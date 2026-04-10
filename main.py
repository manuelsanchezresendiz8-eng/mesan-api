import os
import sys
import uuid
import logging
from datetime import datetime

from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from pydantic import BaseModel, Field

from database import init_db
from limiter import limiter
from routes.evaluar import router as evaluar_router
from routes.verificar import router as verificar_router

# =========================
# CONFIG LOGGING
# =========================
logging.basicConfig(level=logging.INFO)

# =========================
# VALIDAR VARIABLES
# =========================
REQUIRED_VARS = ["MESAN_API_KEY"]
missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
if missing:
    logging.critical(f"Faltan variables de entorno: {missing}")
    sys.exit(1)

# =========================
# IMPORTS CRITICOS
# =========================
try:
    from core.mesan_core import ejecutar_diagnostico
    logging.info("DEBUG: core.mesan_core cargado OK")
except Exception as e:
    logging.critical(f"Error core.mesan_core: {e}")
    raise

try:
    from enterprise.enterprise_engine import sistema_enterprise
    logging.info("DEBUG: enterprise_engine cargado OK")
except Exception as e:
    logging.critical(f"Error enterprise_engine: {e}")
    raise

try:
    from utils.email_sender import enviar_notificacion_lead
    logging.info("DEBUG: email_sender cargado OK")
except Exception as e:
    logging.error(f"Email sender no disponible: {e}")
    enviar_notificacion_lead = None

# =========================
# INIT APP
# =========================
init_db()

app = FastAPI(title="MESAN API", version="2.1.0")

# =========================
# CORS SEGURO
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mesanomega.com",
        "https://www.mesanomega.com",
        "https://manuelsanchezresendiz8-eng.github.io"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================
# RATE LIMIT
# =========================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# =========================
# ROUTERS
# =========================
app.include_router(evaluar_router, prefix="/api")
app.include_router(verificar_router, prefix="/api")

# =========================
# BASE DE LEADS EN MEMORIA
# (temporal hasta implementar PostgreSQL)
# =========================
leads_db = []

# =========================
# MODELOS
# =========================
class LeadInput(BaseModel):
    nombre: str = Field(default="")
    email: str = Field(default="")
    telefono: str = Field(default="")
    score: int = Field(default=0)
    clasificacion: str = Field(default="")
    estatus: str = Field(default="nuevo")

# =========================
# PREFLIGHT CORS
# =========================
@app.options("/enterprise")
def preflight_enterprise():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# =========================
# RAIZ — evita 404 y shutdown de Render
# =========================
@app.get("/")
async def root():
    return {"status": "MESAN-Ω API activa", "version": "2.1.0"}

# =========================
# HEALTH
# =========================
@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.1.0"}

# =========================
# DIAGNOSTICO
# =========================
@app.post("/diagnostico")
@limiter.limit("20/minute")
async def diagnostico(request: Request, data: dict):
    try:
        return ejecutar_diagnostico(data)
    except Exception as e:
        logging.error(f"Error diagnostico: {e}")
        return JSONResponse(status_code=500, content={"error": "Error en diagnostico"})

# =========================
# ENTERPRISE
# =========================
@app.post("/enterprise")
@limiter.limit("10/minute")
async def enterprise(request: Request, data: dict):
    try:
        resultado = sistema_enterprise(data)

        score = resultado.get("diagnostico", {}).get("score", 0)
        clasificacion = resultado.get("clasificacion", "")
        soluciones = resultado.get("soluciones", [])
        impacto = resultado.get("impacto", {})

        nombre = data.get("nombre", "")
        email = data.get("email", "")
        telefono = data.get("telefono", "")

        if nombre or email or telefono:
            lead = {
                "id": str(uuid.uuid4()),
                "nombre": nombre,
                "email": email,
                "telefono": telefono,
                "score": score,
                "clasificacion": clasificacion,
                "soluciones": soluciones,
                "impacto_min": impacto.get("impacto_min", 0),
                "impacto_max": impacto.get("impacto_max", 0),
                "estatus": "nuevo",
                "fecha": datetime.now().isoformat()
            }
            leads_db.append(lead)

            if enviar_notificacion_lead and email:
                try:
                    enviar_notificacion_lead(
                        nombre=nombre,
                        email_cliente=email,
                        telefono=telefono,
                        score=score,
                        clasificacion=clasificacion,
                        soluciones=soluciones
                    )
                except Exception as e:
                    logging.error(f"Error email: {e}")

        return resultado

    except Exception as e:
        logging.error(f"Error enterprise: {e}")
        return JSONResponse(status_code=500, content={"error": "Error interno"})

# =========================
# GUARDAR LEAD
# =========================
@app.post("/lead")
@limiter.limit("20/minute")
async def guardar_lead(request: Request, data: dict):
    try:
        lead = {
            "id": str(uuid.uuid4()),
            "nombre": data.get("nombre", ""),
            "email": data.get("email", ""),
            "telefono": data.get("telefono", ""),
            "score": data.get("score", 0),
            "clasificacion": data.get("clasificacion", ""),
            "estatus": "nuevo",
            "fecha": datetime.now().isoformat()
        }
        leads_db.append(lead)
        return {"ok": True, "id": lead["id"]}
    except Exception as e:
        logging.error(f"Error guardando lead: {e}")
        return JSONResponse(status_code=500, content={"error": "Error guardando lead"})

# =========================
# VER LEADS (PROTEGIDO)
# =========================
@app.get("/leads")
async def obtener_leads(api_key: str = Header(None)):
    if api_key != os.environ.get("MESAN_API_KEY"):
        return JSONResponse(status_code=403, content={"error": "No autorizado"})
    return {"leads": leads_db}

# =========================
# ACTUALIZAR LEAD
# =========================
@app.put("/lead/{lead_id}")
async def actualizar_lead(lead_id: str, data: dict):
    for lead in leads_db:
        if lead["id"] == lead_id:
            lead["estatus"] = data.get("estatus", lead["estatus"])
            return {"ok": True, "lead": lead}
    return {"ok": False}

# =========================
# ERROR GLOBAL
# =========================
@app.exception_handler(Exception)
async def global_exception(request: Request, exc: Exception):
    logging.error(f"Error global: {exc}")
    return JSONResponse(status_code=500, content={"error": "Error interno"})
