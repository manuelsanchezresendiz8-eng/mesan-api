# routes/pro.py
# MESAN Omega — Motor v31 Backend Completo
# ==========================================
# Endpoints:
#   POST /pro/diagnostico      → genera diagnóstico + guarda en DB
#   POST /crear-sesion-omega   → crea sesión Stripe
#   POST /webhook              → marca pagado en DB
#   GET  /verificar-pago/{id}  → devuelve diagnóstico completo si pagado
#   POST /guardar-lead         → CRM: guarda lead en tabla leads

import os
import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import Diagnostico, Lead

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxx")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")
DOMINIO = os.getenv("DOMINIO", "https://mesanomega.com")


# ─────────────────────────────────────────
#  SCHEMAS
# ─────────────────────────────────────────

class InputIA(BaseModel):
    texto: str
    sector: Optional[str] = "GENERAL"
    empresa: Optional[str] = ""

class SesionInput(BaseModel):
    diagnostico_id: int
    monto: Optional[int] = 299
    telefono: Optional[str] = None

class LeadInput(BaseModel):
    texto: Optional[str] = ""
    sector: Optional[str] = ""
    empresa: Optional[str] = ""
    nivel: Optional[str] = ""
    impacto: Optional[str] = ""


# ─────────────────────────────────────────
#  MOTOR DE ANÁLISIS v31
#  (conecta aquí tu IA real / Claude API)
# ─────────────────────────────────────────

def motor_analisis(texto: str, sector: str) -> dict:
    """
    Motor de análisis sectorial MESAN v31.
    Reglas base — reemplaza con llamada a Claude/OpenAI para IA real.
    """

    texto_lower = texto.lower()

    # ── REGLAS CRÍTICAS ──────────────────────────────────
    if "huelga" in texto_lower:
        return {
            "nivel": "CRITICO",
            "area": "LABORAL / SINDICAL",
            "impacto": "2,000,000 - 5,000,000",
            "causa": "Proceso de huelga activo o amenaza sindical confirmada.",
            "detalle": (
                "Huelga detectada: el impacto incluye paro de operaciones, demanda ante JLCA "
                "estimada en $800K+, carga social acumulada y daño reputacional. "
                "Multiplicador de impacto: ×1.8 por escalamiento procesal."
            ),
            "impacto_detalle": (
                "Pérdida operativa diaria + costos legales JLCA + indemnizaciones potenciales. "
                "Rango: $2M–$5M MXN dependiendo de duración del conflicto."
            ),
            "plan": "1. Contactar mediador laboral inmediato\n2. Revisar convenio colectivo\n3. Activar protocolo de conciliación STPS\n4. Documentar posición legal\n5. Suspender decisiones unilaterales",
            "prioridad": "ALTA"
        }

    if "repse" in texto_lower and ("vencid" in texto_lower or "expirad" in texto_lower or "caducad" in texto_lower):
        return {
            "nivel": "CRITICO",
            "area": "SERVICIOS DE APOYO / REPSE",
            "impacto": "560,000 - 1,400,000",
            "causa": "REPSE vencido: los contratos de subcontratación son ilegales hasta renovación.",
            "detalle": (
                "El artículo 15-D LFT establece responsabilidad solidaria del beneficiario. "
                "IMSS puede iniciar auditoría retroactiva. "
                "SAT no permite deducción de pagos a prestadores sin REPSE vigente."
            ),
            "impacto_detalle": "Multas SAT + cuotas IMSS no deducibles + riesgo de nulidad contractual. Rango: $560K–$1.4M MXN.",
            "plan": "1. Suspender pagos a proveedor hasta regularización\n2. Iniciar trámite renovación REPSE (STPS)\n3. Notificar al cliente del riesgo\n4. Revisar contratos para cláusula de garantía",
            "prioridad": "ALTA"
        }

    if "sspc" in texto_lower or ("seguridad" in texto_lower and "registro" in texto_lower):
        return {
            "nivel": "CRITICO",
            "area": "SEGURIDAD PRIVADA / SSPC",
            "impacto": "780,000 - 1,950,000",
            "causa": "Ausencia o vencimiento de registro SSPC para empresa de seguridad privada.",
            "detalle": (
                "La LGSP exige registro federal vigente. Operar sin él constituye infracción grave "
                "con multa de hasta 5,000 UMA + suspensión de operaciones."
            ),
            "impacto_detalle": "Multas administrativas + suspensión + pérdida de contratos activos. Rango: $780K–$1.95M MXN.",
            "plan": "1. Verificar vigencia registro SSPC\n2. Iniciar trámite renovación inmediata\n3. Revisar pólizas de seguro de responsabilidad\n4. Notificar a clientes sobre contingencia",
            "prioridad": "ALTA"
        }

    # ── REGLAS POR SECTOR ────────────────────────────────
    if sector == "LABORAL" or "outsourcing" in texto_lower or "subcontrat" in texto_lower:
        nivel = "ALTO"
        impacto = "180,000 - 540,000"
        causa = "Riesgo en estructura de subcontratación o relación laboral indirecta."
        detalle = "Reforma outsourcing 2021 (D.O.F. 23/04/21): todos los contratos deben ser de servicios especializados con REPSE vigente. Responsabilidad solidaria activa."
        plan = "1. Auditar contratos de subcontratación\n2. Verificar REPSE de todos los proveedores\n3. Regularizar relaciones laborales directas\n4. Implementar control documental mensual"

    elif sector == "FISCAL" or "sat" in texto_lower or "fiscal" in texto_lower:
        nivel = "ALTO"
        impacto = "200,000 - 800,000"
        causa = "Inconsistencias fiscales detectadas. Riesgo de auditoría SAT o ajuste de crédito fiscal."
        detalle = "El SAT intensificó revisiones a empresas con deducción de servicios de terceros. CFDI inconsistentes pueden derivar en créditos fiscales rechazados."
        plan = "1. Auditoría interna de CFDI últimos 5 años\n2. Validar deducciones de servicios especializados\n3. Preparar expediente de respuesta ante posible requerimiento\n4. Contratar asesor fiscal preventivo"

    elif sector == "CALL_CENTER" or "call center" in texto_lower:
        nivel = "MEDIO"
        impacto = "80,000 - 200,000"
        causa = "Sector con riesgo moderado en cumplimiento laboral y rotación de personal."
        detalle = "Alta rotación genera riesgo en liquidaciones, IMSS y Infonavit. Verificar contratos por proyecto vs. relación indefinida."
        plan = "1. Revisar clasificación de contratos\n2. Auditar pagos IMSS/Infonavit\n3. Implementar política de retención\n4. Verificar NOM-035 cumplimiento"

    elif sector in ("FINANCIERO",) or "sofom" in texto_lower or "fintech" in texto_lower:
        nivel = "ALTO"
        impacto = "250,000 - 600,000"
        causa = "Riesgo regulatorio en entidad financiera. Posible incumplimiento CNBV o Condusef."
        detalle = "Entidades financieras no bancarias sujetas a supervisión CNBV. Incumplimientos en reporte regulatorio o LFPIORPI pueden derivar en multas graves."
        plan = "1. Auditoría de reporte regulatorio\n2. Verificar cumplimiento LFPIORPI\n3. Actualizar políticas AML/KYC\n4. Revisar convenios Condusef"

    else:
        # General
        nivel = "MEDIO"
        impacto = "100,000 - 350,000"
        causa = "Riesgos operativos y de cumplimiento detectados en el análisis inicial."
        detalle = "El análisis identifica áreas de mejora en cumplimiento laboral, fiscal y operativo. Se requiere revisión detallada para cuantificar impacto exacto."
        plan = "1. Diagnóstico completo de áreas de riesgo\n2. Priorizar cumplimiento fiscal y laboral\n3. Implementar controles internos\n4. Establecer monitoreo mensual"

    return {
        "nivel": nivel,
        "area": sector.replace("_", " "),
        "impacto": impacto,
        "causa": causa,
        "detalle": detalle,
        "impacto_detalle": f"Pérdida estimada: ${impacto} MXN. Incluye multas, ajustes y costos legales.",
        "plan": plan,
        "prioridad": "ALTA" if nivel in ("CRITICO", "ALTO") else "MEDIA"
    }


# ─────────────────────────────────────────
#  ENDPOINT: GENERAR DIAGNÓSTICO (GANCHO)
# ─────────────────────────────────────────

@router.post("/pro/diagnostico")
def generar_diagnostico(data: InputIA, db: Session = Depends(get_db)):
    """
    Genera diagnóstico con motor v31.
    Guarda en DB. Devuelve solo nivel/área/impacto (gancho).
    Detalle completo solo disponible después de pago.
    """

    resultado = motor_analisis(data.texto, data.sector or "GENERAL")

    nuevo = Diagnostico(
        nivel           = resultado["nivel"],
        area            = resultado["area"],
        impacto         = resultado["impacto"],
        causa           = resultado["causa"],
        detalle         = resultado["detalle"],
        impacto_detalle = resultado["impacto_detalle"],
        plan            = resultado["plan"],
        sector          = data.sector or "GENERAL",
        empresa         = data.empresa or "",
        pagado          = False
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Respuesta pública (gancho): solo nivel/área/impacto
    return {
        "id":      nuevo.id,
        "nivel":   nuevo.nivel,
        "area":    nuevo.area,
        "impacto": nuevo.impacto,
        "prioridad": resultado["prioridad"]
    }


# ─────────────────────────────────────────
#  ENDPOINT: STRIPE CHECKOUT SESSION
# ─────────────────────────────────────────

@router.post("/crear-sesion-omega")
def crear_sesion(data: SesionInput):
    """
    Crea sesión de pago Stripe para diagnóstico.
    Redirige a success.html?id={diagnostico_id} al completar.
    """

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {
                        "name": "Diagnóstico Completo MESAN Ω",
                        "description": "Acceso inmediato: causa raíz, estrategia, plan de acción."
                    },
                    "unit_amount": (data.monto or 299) * 100  # centavos
                },
                "quantity": 1
            }],
            mode="payment",
            metadata={"telefono": data.telefono or ""},   # ← WhatsApp post-pago
            success_url=f"{DOMINIO}/success.html?id={data.diagnostico_id}",
            cancel_url=f"{DOMINIO}/"
        )
        return {"url": session.url}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────
#  ENDPOINT: WEBHOOK STRIPE (marcar pagado)
# ─────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe llama este endpoint cuando el pago se completa.
    1. Extrae diagnostico_id → marca pagado=True en DB
    2. Si hay teléfono en metadata → envía diagnóstico por WhatsApp
    3. Scoring automático → asigna humano si impacto alto
    """
    from routes.whatsapp import enviar_diagnostico_completo

    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Webhook inválido")

    if event["type"] == "checkout.session.completed":
        session     = event["data"]["object"]
        success_url = session.get("success_url", "")
        metadata    = session.get("metadata", {})
        telefono    = metadata.get("telefono")  # número WA si viene de landing móvil

        # ── Extraer diagnostico_id ────────────────────────
        try:
            diag_id = int(success_url.split("id=")[-1].split("&")[0])
        except (ValueError, IndexError):
            return {"status": "ok", "warning": "Sin diagnostico_id"}

        diag = db.query(Diagnostico).filter(Diagnostico.id == diag_id).first()
        if not diag:
            return {"status": "ok", "warning": "Diagnóstico no encontrado"}

        # ── Marcar pagado ─────────────────────────────────
        diag.pagado = True
        db.commit()

        # ── Actualizar lead CRM si existe ─────────────────
        if telefono:
            lead = db.query(Lead).filter(Lead.sector == "WhatsApp").order_by(Lead.id.desc()).first()
            if lead:
                lead.pagado = True
                db.commit()

        # ── Enviar diagnóstico por WhatsApp si hay teléfono ──
        if telefono:
            enviar_diagnostico_completo(
                numero   = telefono,
                nivel    = diag.nivel,
                area     = diag.area,
                impacto  = diag.impacto,
                causa    = diag.causa    or "",
                detalle  = diag.detalle  or "",
                plan     = diag.plan     or "",
                db       = db
            )

    return {"status": "ok"}


# ─────────────────────────────────────────
#  ENDPOINT: VERIFICAR PAGO → UNLOCK
# ─────────────────────────────────────────

@router.get("/verificar-pago/{id}")
def verificar_pago(id: int, db: Session = Depends(get_db)):
    """
    success.html llama esto para verificar pago y obtener diagnóstico completo.
    Si pagado=True → devuelve todo el diagnóstico.
    Si pagado=False → devuelve pagado:false.
    """

    diag = db.query(Diagnostico).filter(Diagnostico.id == id).first()

    if not diag:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")

    if not diag.pagado:
        return {"pagado": False}

    # Parsear plan en pasos estructurados
    plan_pasos = []
    if diag.plan:
        for line in diag.plan.strip().split("\n"):
            line = line.strip()
            if line:
                plan_pasos.append({
                    "titulo": line.lstrip("0123456789.-) "),
                    "detalle": ""
                })

    return {
        "pagado":          True,
        "nivel":           diag.nivel,
        "area":            diag.area,
        "impacto":         diag.impacto,
        "causa":           diag.causa,
        "detalle":         diag.detalle,
        "impacto_detalle": diag.impacto_detalle,
        "plan":            diag.plan,
        "plan_pasos":      plan_pasos,
        "sector":          diag.sector,
        "empresa":         diag.empresa
    }


# ─────────────────────────────────────────
#  ENDPOINT: UPLOAD DOCUMENTO (PDF / IMAGEN)
# ─────────────────────────────────────────

from fastapi import UploadFile, File
import io

@router.post("/extract-text")
async def upload_documento(file: UploadFile = File(...)):
    """
    Recibe PDF o imagen. Extrae texto y lo devuelve para pre-llenar el form.
    Soporta: PDF (pdfplumber), JPG/PNG (pytesseract OCR).
    pip install pdfplumber pytesseract Pillow
    """
    contenido = await file.read()
    texto = ""

    try:
        if file.content_type == "application/pdf" or file.filename.endswith(".pdf"):
            import pdfplumber
            with pdfplumber.open(io.BytesIO(contenido)) as pdf:
                paginas = pdf.pages[:3]  # solo primeras 3 páginas
                texto = "\n".join(p.extract_text() or "" for p in paginas)

        elif file.content_type in ("image/jpeg","image/jpg","image/png"):
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(io.BytesIO(contenido))
                texto = pytesseract.image_to_string(img, lang="spa")
            except ImportError:
                texto = ""  # OCR no disponible, continúa sin texto

    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        texto = ""

    # Limpiar texto
    texto = texto.strip()[:1000]  # máx 1000 chars para el form

    # Análisis rápido del documento si hay texto
    analisis = {}
    if texto:
        analisis = motor_analisis(texto, "GENERAL")

    return {
        "texto":   texto,
        "nivel":   analisis.get("nivel", ""),
        "area":    analisis.get("area", ""),
        "impacto": analisis.get("impacto", ""),
        "ok":      True
    }


# ─────────────────────────────────────────
#  ENDPOINT: VERIFICAR PAGO POR SESSION_ID
# ─────────────────────────────────────────

@router.get("/verificar-pago-session")
def verificar_por_session(session_id: str, db: Session = Depends(get_db)):
    """
    Alternativa a verificar por ID cuando Stripe redirige con ?session_id=
    Busca el diagnóstico asociado a esa sesión de Stripe.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        success_url = session.get("success_url", "")

        diag_id = int(success_url.split("id=")[-1].split("&")[0])
        diag    = db.query(Diagnostico).filter(Diagnostico.id == diag_id).first()

        if diag and diag.pagado:
            return {"pagado": True, "diagnostico_id": diag.id}

    except Exception as e:
        print(f"[SESSION VERIFY] {e}")

    return {"pagado": False}


@router.post("/guardar-lead")
def guardar_lead(data: LeadInput, db: Session = Depends(get_db)):
    """
    Lead scoring automático: guarda leads ALTO/CRÍTICO en DB.
    Campos CRM: nombre, empresa, sector, riesgo, pérdida, pagó, fecha.
    """

    lead = Lead(
        empresa = data.empresa or "",
        sector  = data.sector  or "",
        nivel   = data.nivel   or "",
        impacto = data.impacto or "",
        texto   = data.texto   or "",
        pagado  = False
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return {"status": "ok", "id": lead.id}
