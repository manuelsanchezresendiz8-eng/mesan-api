# routes/jarvis_chat_routes.py -- MESAN Omega JARVIS Chat v2.0
# Lead capture + SMTP confirmation + fallback endpoint
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import psycopg
except ImportError:
    psycopg = None

from datetime import datetime, timezone
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger("mesan.jarvis_chat")


def _get_conn():
    url = os.getenv("DATABASE_URL", "")
    if not url or not psycopg:
        return None
    try:
        return psycopg.connect(url)
    except Exception as e:
        logger.error("[JARVIS] DB connection error: %s", e)
        return None


def _ensure_table():
    conn = _get_conn()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_leads (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255),
                empresa VARCHAR(255),
                sector VARCHAR(100),
                tamano VARCHAR(50),
                email VARCHAR(255),
                telefono VARCHAR(50),
                dias VARCHAR(255),
                horario VARCHAR(255),
                preocupacion VARCHAR(100),
                producto_interes VARCHAR(100) DEFAULT 'diagnostico_entrada',
                respuestas TEXT,
                fuente VARCHAR(50) DEFAULT 'jarvis_chat',
                smtp_status VARCHAR(20) DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("[JARVIS] Tabla jarvis_leads verificada")
    except Exception as e:
        logger.error("[JARVIS] Error creando tabla: %s", e)


_ensure_table()


def _save_lead(data):
    """Guarda lead en PostgreSQL. Retorna True si exitoso."""
    conn = _get_conn()
    if not conn:
        logger.warning("[JARVIS] No hay conexion a DB, lead no guardado")
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO jarvis_leads
               (nombre, empresa, sector, tamano, email, telefono,
                dias, horario, preocupacion, producto_interes,
                respuestas, fuente)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                data.get("nombre", ""),
                data.get("empresa", ""),
                data.get("sector", ""),
                data.get("tamano", ""),
                data.get("email", ""),
                data.get("telefono", ""),
                data.get("dias", ""),
                data.get("horario", ""),
                data.get("preocupacion", ""),
                data.get("producto_interes", "diagnostico_entrada"),
                ",".join(data.get("respuestas", [])),
                data.get("fuente", "jarvis_chat"),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("[JARVIS] Lead guardado: %s | %s | %s",
                     data.get("nombre"), data.get("empresa"), data.get("email"))
        return True
    except Exception as e:
        logger.error("[JARVIS] Error guardando lead: %s", e)
        try:
            conn.close()
        except Exception:
            pass
        return False


def _send_confirmation_email(data):
    """Intenta enviar email de confirmacion. Retorna status string."""
    host = os.getenv("SMTP_HOST", os.getenv("EMAIL_SMTP", ""))
    port = int(os.getenv("SMTP_PORT", os.getenv("EMAIL_PORT", "587")))
    user = os.getenv("SMTP_USER", os.getenv("EMAIL_DESTINO", ""))
    pwd = os.getenv("SMTP_PASS", os.getenv("EMAIL_PASS", ""))
    to_email = data.get("email", "")

    if not all([host, user, pwd, to_email]):
        logger.warning("[JARVIS] SMTP no configurado o email vacio")
        return "NOT_CONFIGURED"

    nombre = data.get("nombre", "")
    producto = data.get("producto_interes", "diagnostico_entrada")

    if producto == "diagnostico_ejecutivo":
        subject = "MESAN Omega - Diagnostico Ejecutivo Agendado"
        body_title = "Diagnostico Ejecutivo Omega"
        body_desc = "Nuestro equipo te contactara para confirmar fecha y enviarte la liga de pago."
    elif producto == "membresia":
        subject = "MESAN Omega - Interes en Membresia Registrado"
        body_title = "MESAN Omega Monitor"
        body_desc = "Te contactaremos para activar tu membresia y programar el diagnostico inicial."
    else:
        subject = "MESAN Omega - Diagnostico Agendado"
        body_title = "Diagnostico MESAN Omega"
        body_desc = "Tu diagnostico ha sido agendado. Te enviaremos los siguientes pasos pronto."

    html = """
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0D1425;color:#E2E8F0;padding:40px;border-radius:12px;">
        <div style="text-align:center;margin-bottom:24px;">
            <span style="font-size:32px;font-weight:900;color:#00E5A0;">MESAN Omega</span>
        </div>
        <h2 style="color:#00E5A0;margin-bottom:16px;">{title}</h2>
        <p>Hola {nombre},</p>
        <p>{desc}</p>
        <div style="background:#111B33;border:1px solid #1E3055;border-radius:8px;padding:20px;margin:24px 0;">
            <p style="margin:0;"><strong>Nombre:</strong> {nombre}</p>
            <p style="margin:8px 0 0;"><strong>Empresa:</strong> {empresa}</p>
            <p style="margin:8px 0 0;"><strong>Telefono:</strong> {telefono}</p>
            <p style="margin:8px 0 0;"><strong>Disponibilidad:</strong> {dias} - {horario}</p>
        </div>
        <p>Si tienes alguna pregunta, responde a este correo.</p>
        <p style="color:#64748B;font-size:12px;margin-top:32px;">Equipo MESAN Omega | mesanomega.com</p>
    </div>
    """.format(
        title=body_title,
        nombre=nombre,
        desc=body_desc,
        empresa=data.get("empresa", ""),
        telefono=data.get("telefono", ""),
        dias=data.get("dias", ""),
        horario=data.get("horario", ""),
    )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, pwd)
            server.sendmail(user, [to_email, user], msg.as_string())

        logger.info("[JARVIS] Email enviado a %s", to_email)
        return "SENT"
    except Exception as e:
        logger.error("[JARVIS] Error enviando email: %s", e)
        return "FAILED"


def _update_smtp_status(email, status):
    """Actualiza smtp_status del lead mas reciente con ese email."""
    conn = _get_conn()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE jarvis_leads SET smtp_status = %s
               WHERE email = %s
               ORDER BY created_at DESC LIMIT 1""",
            (status, email),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error("[JARVIS] Error actualizando smtp_status: %s", e)


# ==============================================================
# ENDPOINT PRINCIPAL
# ==============================================================
@router.post("/api/chat/jarvis/lead")
async def jarvis_lead(request: Request):
    """Guarda lead y envia confirmacion por email."""
    try:
        body = await request.json()
        logger.info("[JARVIS] === NUEVO LEAD === %s | %s | %s | producto: %s",
                     body.get("nombre"), body.get("empresa"),
                     body.get("email"), body.get("producto_interes"))

        # 1. Guardar en DB (prioritario, nunca perder el lead)
        db_saved = _save_lead(body)

        # 2. Intentar enviar email (si falla, el lead ya esta guardado)
        smtp_status = _send_confirmation_email(body)

        # 3. Actualizar status de email en DB
        if db_saved and body.get("email"):
            _update_smtp_status(body.get("email"), smtp_status)

        lead_id = "jarvis_{}".format(
            datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        )

        return {
            "status": "success",
            "message": "Lead guardado",
            "lead_id": lead_id,
            "db_saved": db_saved,
            "smtp_status": smtp_status,
        }

    except Exception as e:
        logger.error("[JARVIS] Error en endpoint: %s", e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)},
        )


# ==============================================================
# ENDPOINT FALLBACK (GET) — por si el POST falla en el frontend
# ==============================================================
@router.get("/api/chat/jarvis/lead-fallback")
async def jarvis_lead_fallback(
    nombre: str = Query(""),
    empresa: str = Query(""),
    email: str = Query(""),
    telefono: str = Query(""),
    producto: str = Query("diagnostico_entrada"),
):
    """Fallback GET para guardar lead si el POST falla."""
    try:
        data = {
            "nombre": nombre,
            "empresa": empresa,
            "email": email,
            "telefono": telefono,
            "producto_interes": producto,
            "fuente": "jarvis_fallback",
            "sector": "",
            "tamano": "",
            "dias": "",
            "horario": "",
            "preocupacion": "",
            "respuestas": [],
        }
        logger.info("[JARVIS] FALLBACK lead: %s | %s | %s", nombre, empresa, email)
        db_saved = _save_lead(data)
        return {"status": "success", "db_saved": db_saved, "via": "fallback"}
    except Exception as e:
        logger.error("[JARVIS] Fallback error: %s", e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)},
        )
