# routes/whatsapp.py
# MESAN Omega — WhatsApp Cloud API Motor v31
# ===========================================
# Flujo:
# Mensaje entra → procesar_mensaje() → respuesta automática
# Pago Stripe → enviar diagnóstico completo → scoring → asignar humano
#
# Variables de entorno requeridas:
# WA_TOKEN = Token permanente Meta (nunca expira)
# WA_PHONE_ID = ID del número en Meta Business
# WA_VERIFY = Token de verificación webhook (ej: "mesan_verify_2025")

import os
import json
import requests
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Lead

router = APIRouter()

# ─── CONFIG ─────────────────────────────────────────────────────────
WA_TOKEN = os.getenv("WA_TOKEN", "TU_TOKEN_META_PERMANENTE")
WA_PHONE_ID = os.getenv("WA_PHONE_ID", "TU_PHONE_ID")
WA_VERIFY = os.getenv("WA_VERIFY", "mesan_verify_2025")
WA_API = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages"
DOMINIO = os.getenv("DOMINIO", "https://mesanomega.com")

# Sesiones en memoria (reemplazar con Redis en producción)
sesiones: dict = {}


# ─── ENVÍO ──────────────────────────────────────────────────────────

def enviar(numero: str, mensaje: str):
    """Envía mensaje de texto por WhatsApp Cloud API."""
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensaje}
    }
    try:
        r = requests.post(WA_API, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[WA ERROR] {e}")


def enviar_botones(numero: str, cuerpo: str, botones: list[dict]):
    """
    Envía mensaje con botones interactivos (máx 3).
    botones = [{"id": "btn_1", "title": "Ver diagnóstico"}]
    """
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": cuerpo},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in botones[:3]
                ]
            }
        }
    }
    try:
        r = requests.post(WA_API, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        # Fallback a texto si botones no disponibles
        enviar(numero, cuerpo + "\n\n" + "\n".join(f"• {b['title']}" for b in botones))


# ─── WEBHOOK VERIFY (GET) ────────────────────────────────────────────

@router.get("/webhook/whatsapp")
async def verificar_webhook(request: Request):
    """
    Meta llama este endpoint para verificar el webhook.
    Devuelve hub.challenge si el verify_token es correcto.
    """
    params = request.query_params
    if params.get("hub.verify_token") == WA_VERIFY:
        return int(params.get("hub.challenge", 0))
    return {"error": "token inválido"}


# ─── WEBHOOK RECEIVE (POST) ──────────────────────────────────────────

@router.post("/webhook/whatsapp")
async def recibir_mensaje(request: Request, db: Session = Depends(get_db)):
    """
    Recibe mensajes entrantes de WhatsApp.
    Meta envía JSON con la estructura entry[].changes[].value.messages[].
    """
    data = await request.json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]["value"]
        msgs = changes.get("messages")

        if not msgs:
            return {"status": "ok"} # notificación de estado, no mensaje

        msg = msgs[0]
        numero = msg["from"]

        # Tipo de mensaje
        if msg["type"] == "text":
            texto = msg["text"]["body"].strip()
            procesar_mensaje(numero, texto, db)

        elif msg["type"] == "interactive":
            # Respuesta a botón
            btn_id = msg["interactive"]["button_reply"]["id"]
            procesar_boton(numero, btn_id, db)

    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")

    return {"status": "ok"}


# ─── MOTOR DE CONVERSACIÓN ───────────────────────────────────────────

def procesar_mensaje(numero: str, texto: str, db: Session):
    """Procesa mensajes de texto libre según estado de sesión."""

    texto_lower = texto.lower()
    estado = sesiones.get(numero, {}).get("estado", "nuevo")

    # ── SALUDO / ENTRADA ──────────────────────────────────
    if any(w in texto_lower for w in ["hola", "diagnostico", "diagnóstico", "inicio", "start", "menu", "menú"]):
        sesiones[numero] = {"estado": "menu"}
        enviar_botones(numero,
            "🔍 *MESAN Ω — Inteligencia de Riesgo Empresarial*\n\n"
            "Detectamos fugas económicas en empresas.\n"
            "¿Qué quieres hacer?",
            [
                {"id": "btn_diagnostico", "title": "⚡ Ver diagnóstico"},
                {"id": "btn_consultor", "title": "👤 Hablar con consultor"},
                {"id": "btn_productos", "title": "💼 Ver servicios"}
            ]
        )
        return

    # ── FALLBACK: redirigir a menú ────────────────────────
    if estado == "nuevo":
        sesiones[numero] = {"estado": "menu"}
        enviar(numero,
            "Hola 👋 Soy MESAN Ω.\n\n"
            f"Inicia tu diagnóstico gratuito aquí:\n"
            f"{DOMINIO}\n\n"
            "O escribe *hola* para ver opciones."
        )
        return

    # ── DESPUÉS DE VER DIAGNÓSTICO ────────────────────────
    if estado == "diagnostico_visto":
        if any(w in texto_lower for w in ["pagar", "pago", "comprar", "desbloquear", "si", "sí", "quiero"]):
            sesiones[numero]["estado"] = "pago_enviado"
            nivel = sesiones[numero].get("nivel", "ALTO")
            impacto = sesiones[numero].get("impacto", "—")
            enviar(numero,
                f"✅ Perfecto.\n\n"
                f"Tu diagnóstico ({nivel} · ${impacto} MXN en riesgo) se desbloquea al completar el pago:\n\n"
                f"👉 {DOMINIO}?pago=wa&n={numero}\n\n"
                f"Precio: *$299 MXN* · Pago único · Acceso inmediato."
            )
            return

    # ── CONFIRMACIÓN DE PAGO ──────────────────────────────
    if "pagué" in texto_lower or "ya pagué" in texto_lower or "pague" in texto_lower:
        enviar(numero,
            "⏳ Verificando tu pago...\n"
            "En unos segundos recibirás el diagnóstico completo."
        )
        return

    # ── DEFAULT ───────────────────────────────────────────
    enviar(numero,
        "Escribe *hola* para ver el menú principal."
    )


def procesar_boton(numero: str, btn_id: str, db: Session):
    """Procesa respuestas de botones interactivos."""

    # ── BTN: DIAGNÓSTICO ──────────────────────────────────
    if btn_id == "btn_diagnostico":
        # Aquí puedes conectar con el motor v31 real
        nivel = "ALTO"
        impacto = "180,000 - 540,000"

        sesiones[numero] = {
            "estado": "diagnostico_visto",
            "nivel": nivel,
            "impacto": impacto
        }

        # Guardar lead en CRM
        lead = Lead(
            empresa="",
            sector="WhatsApp",
            nivel=nivel,
            impacto=impacto,
            texto="Lead WhatsApp - diagnóstico solicitado",
            pagado=False
        )
        db.add(lead)
        db.commit()

        enviar_botones(numero,
            f"⚠️ *RIESGO DETECTADO: {nivel}*\n\n"
            f"Impacto estimado: *${impacto} MXN*\n\n"
            f"🔒 Diagnóstico completo bloqueado.\n"
            f"Incluye: causa raíz · estrategia · plan de acción.",
            [
                {"id": "btn_pagar", "title": "🔓 Desbloquear $299"},
                {"id": "btn_consultor", "title": "👤 Hablar consultor"},
            ]
        )
        return

    # ── BTN: PAGAR ────────────────────────────────────────
    if btn_id == "btn_pagar":
        sesiones[numero] = {**sesiones.get(numero, {}), "estado": "pago_enviado"}
        nivel = sesiones.get(numero, {}).get("nivel", "ALTO")
        impacto = sesiones.get(numero, {}).get("impacto", "—")

        enviar(numero,
            f"💳 *Desbloquear Diagnóstico MESAN Ω*\n\n"
            f"Nivel: {nivel}\n"
            f"Impacto: ${impacto} MXN\n\n"
            f"Precio: *$299 MXN* · Pago único\n\n"
            f"👉 {DOMINIO}/pago?n={numero}\n\n"
            f"Al completar el pago recibirás el diagnóstico completo aquí mismo."
        )
        return

    # ── BTN: CONSULTOR ────────────────────────────────────
    if btn_id == "btn_consultor":
        sesiones[numero] = {**sesiones.get(numero, {}), "estado": "humano"}
        asignar_humano(numero, db)
        enviar(numero,
            "👤 *Conectando con especialista...*\n\n"
            "El Lic. Manuel Sánchez revisará tu caso.\n"
            "Te contactamos en los próximos 30 minutos en horario hábil."
        )
        return

    # ── BTN: PRODUCTOS ────────────────────────────────────
    if btn_id == "btn_productos":
        enviar(numero,
            "💼 *Servicios MESAN Omega*\n\n"
            "1️⃣ *Diagnóstico IA* — $299 MXN\n"
            " Análisis de riesgo + causa raíz\n\n"
            "2️⃣ *Plan de Acción* — $499 MXN\n"
            " Estrategia concreta + pasos\n\n"
            "3️⃣ *Monitoreo Mensual* — $970 MXN/mes\n"
            " Vigilancia continua de riesgos\n\n"
            "4️⃣ *Intervención Senior* — desde $2,999 MXN\n"
            " Consultoría directa Lic. Sánchez\n\n"
            f"Diagnóstico gratuito: {DOMINIO}\n"
            "O responde el número del servicio que te interesa."
        )
        return


# ─── SCORING AUTOMÁTICO ──────────────────────────────────────────────

def evaluar_lead_scoring(numero: str, nivel: str, impacto_str: str, db: Session):
    """
    Scoring automático post-pago.
    Si el impacto es alto → notifica y asigna humano.
    """

    # Extraer número mínimo del rango "180,000 - 540,000"
    try:
        impacto_min = int(impacto_str.split("-")[0].replace(",", "").strip())
    except (ValueError, IndexError):
        impacto_min = 0

    if nivel == "CRITICO" or impacto_min >= 200_000:
        enviar(numero,
            "⚠️ *ALERTA: Caso de alta prioridad*\n\n"
            "Tu situación requiere intervención especializada.\n\n"
            "El Lic. Manuel Sánchez revisará tu caso personalmente.\n"
            "Te contactamos en breve."
        )
        asignar_humano(numero, db, nivel=nivel, prioridad="ALTA")

    elif impacto_min >= 100_000:
        enviar(numero,
            "📋 *Recomendación MESAN*\n\n"
            "Tu caso tiene riesgo significativo.\n"
            "Considera el *Plan de Acción ($499)* para resolverlo.\n\n"
            f"👉 {DOMINIO}/plan"
        )


def asignar_humano(numero: str, db: Session, nivel: str = "ALTO", prioridad: str = "NORMAL"):
    """
    Registra lead para seguimiento humano.
    Actualiza CRM y puede disparar notificación interna.
    """
    # Actualizar lead en DB si existe
    lead = db.query(Lead).filter(Lead.sector == "WhatsApp").order_by(Lead.id.desc()).first()
    if lead:
        lead.nivel = nivel
        db.commit()

    # Notificación interna (opcional: enviar a Slack / email)
    print(f"[CRM] Lead asignado: {numero} | Nivel: {nivel} | Prioridad: {prioridad}")


# ─── ENVÍO POST-PAGO (llamado desde webhook Stripe) ──────────────────

def enviar_diagnostico_completo(
    numero: str,
    nivel: str,
    area: str,
    impacto: str,
    causa: str,
    detalle: str,
    plan: str,
    db: Session
):
    """
    Se llama desde el webhook de Stripe cuando el pago se completa.
    Envía el diagnóstico completo por WhatsApp.
    """

    # Parsear plan a lista de pasos
    pasos = []
    for line in (plan or "").strip().split("\n"):
        line = line.strip().lstrip("0123456789.-) ")
        if line:
            pasos.append(line)

    plan_texto = "\n".join(f"{i+1}. {p}" for i, p in enumerate(pasos[:5]))

    enviar(numero,
        f"✅ *DIAGNÓSTICO COMPLETO DESBLOQUEADO*\n\n"
        f"Nivel: *{nivel}*\n"
        f"Área: {area}\n"
        f"Impacto: *${impacto} MXN*\n\n"
        f"🔍 *Causa raíz:*\n{causa}\n\n"
        f"📋 *Detalle:*\n{detalle}\n\n"
        f"🚀 *Plan de acción:*\n{plan_texto}\n\n"
        f"Lic. Manuel Sánchez · MESAN Omega\n"
        f"¿Quieres apoyo para implementarlo? Responde *sí*."
    )

    # Scoring automático
    evaluar_lead_scoring(numero, nivel, impacto, db)
