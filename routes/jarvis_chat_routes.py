# routes/jarvis_chat_routes.py -- MESAN Omega JARVIS Chat v1.0
import os
import logging
import psycopg
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger("mesan.jarvis_chat")


def _get_conn():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return None
    return psycopg.connect(url)


def _ensure_table():
    """Crea la tabla jarvis_leads si no existe."""
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
                email VARCHAR(255),
                telefono VARCHAR(50),
                dias VARCHAR(255),
                horario VARCHAR(255),
                respuestas TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error("[JARVIS] Error creando tabla: %s", e)


# Crear tabla al importar el modulo
_ensure_table()


@router.post("/api/chat/jarvis/lead")
async def jarvis_lead(request: Request):
    """Guarda lead del chatbot JARVIS en la base de datos."""
    try:
        body = await request.json()
        nombre = body.get("nombre", "")
        empresa = body.get("empresa", "")
        email = body.get("email", "")
        telefono = body.get("telefono", "")
        dias = body.get("dias", "")
        horario = body.get("horario", "")
        respuestas = ",".join(body.get("respuestas", []))

        logger.info("[JARVIS] Nuevo lead: %s | %s | %s", nombre, empresa, email)

        conn = _get_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO jarvis_leads
                       (nombre, empresa, email, telefono, dias, horario, respuestas)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (nombre, empresa, email, telefono, dias, horario, respuestas),
                )
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                logger.error("[JARVIS] Error guardando lead: %s", e)
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "error": str(e)},
                )

        lead_id = "jarvis_{}".format(
            datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        )
        return {
            "status": "success",
            "message": "Lead guardado",
            "lead_id": lead_id,
        }

    except Exception as e:
        logger.error("[JARVIS] Error: %s", e)
        return JSONResponse(
            status_code=500, content={"status": "error", "error": str(e)}
        )
