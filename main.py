import os
import sys
import uuid
import logging
import traceback
from datetime import datetime

from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from database import init_db
from limiter import limiter

from routes.evaluar import router as evaluar_router
from routes.verificar import router as verificar_router

# =========================================
# LOGGING
# =========================================
logging.basicConfig(level=logging.INFO)

# =========================================
# IMPORTS SEGUROS
# =========================================
try:
    from enterprise.enterprise_engine import sistema_enterprise
    logging.info("DEBUG: enterprise_engine OK")
except Exception as e:
    logging.critical(f"ERROR enterprise_engine: {e}")
    sistema_enterprise = None

try:
    from utils.email_sender import enviar_notificacion_lead
    logging.info("DEBUG: email_sender OK")
except Exception as e:
    logging.error(f"ERROR email_sender: {e}")
    enviar_notificacion_lead = None

# =========================================
# VALIDACIÓN DE VARIABLES
# =========================================
_VARS_REQUERIDAS = ["MESAN_API_KEY"]
_faltantes = [v for v in _VARS_REQUERIDAS if not os.environ.get(v)]
if _faltantes:
    logging.critical(f"ERROR: Variables faltantes: {', '.join(_faltantes)}")
    sys.exit(1)

# =========================================
# INIT
# =========================================
init_db()

app = FastAPI(title="MESAN API", version="2.1.0")

# CORS
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

# Rate limit con IP real
limiter.key_func = get_remote_address
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(evaluar_router, prefix="/api")
app.include_router(verificar_router, prefix="/api")

# =========================================
# STORAGE TEMP
# =========================================
leads_db = []
logging.warning("Leads almacenados en memoria (no persistente)")

# =========================================
# PREFLIGHT CORS
# =========================================
@app.options("/enterprise")
def preflight_enterprise():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://mesanomega.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# =========================================
# RAIZ — evita shutdown de Render
# =========================================
@app.get("/")
@app.head("/")
async def root():
    return JSONResponse(
        content={"status": "MESAN-Ω API activa", "version": "2.1.0"},
        headers={"X-MESAN-VERSION": "2.1.0"}
    )

# =========================================
# HEALTH CHECK
# =========================================
@app.get("/health")
@app.head("/health")
async def health():
    return JSONResponse(
        content={"status": "ok", "version": "2.1.0"},
        headers={"X-MESAN-VERSION": "2.1.0"}
    )

# =========================================
# ENDPOINT PRINCIPAL
# =========================================
if sistema_enterprise:

    @app.post("/enterprise")
    @limiter.limit("10/minute")
    async def enterprise(data: dict, request: Request):

        if not isinstance(data, dict):
            return JSONResponse(status_code=400, content={"error": "Formato inválido"})

        try:
            resultado = sistema_enterprise(data)
        except Exception as e:
            logging.error(traceback.format_exc())
            return JSONResponse(status_code=500, content={"error": f"Error en motor: {str(e)}"})

        nombre = data.get("nombre", "")
        email = data.get("email", "")
        telefono = data.get("telefono", "")

        # MODO ANÓNIMO
        if not email:
            return JSONResponse(
                content={"ok": True, "modo": "anonimo", "resultado": resultado},
                headers={"X-MESAN-VERSION": "2.1.0"}
            )

        # CREAR LEAD
        lead = {
            "id": str(uuid.uuid4()),
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "score": resultado.get("diagnostico", {}).get("score"),
            "clasificacion": resultado.get("clasificacion"),
            "impacto_min": resultado.get("impacto", {}).get("impacto_min"),
            "impacto_max": resultado.get("impacto", {}).get("impacto_max"),
            "simulador": resultado.get("simulador"),
            "estatus": "nuevo",
            "fecha": datetime.now().isoformat()
        }
        leads_db.append(lead)

        # EMAIL
        if enviar_notificacion_lead:
            try:
                enviar_notificacion_lead(
                    nombre=nombre,
                    email_cliente=email,
                    telefono=telefono,
                    score=lead["score"],
                    clasificacion=lead["clasificacion"],
                    soluciones=resultado.get("soluciones", [])
                )
            except Exception as e:
                logging.error(f"Error email: {e}")

        return JSONResponse(
            content={
                "ok": True,
                "modo": "lead_guardado",
                "resultado": resultado,
                "lead_id": lead["id"]
            },
            headers={"X-MESAN-VERSION": "2.1.0"}
        )

# =========================================
# LEADS (PROTEGIDO)
# =========================================
@app.get("/leads")
async def obtener_leads(api_key: str = Header(None)):
    if not api_key or api_key != os.environ.get("MESAN_API_KEY"):
        return JSONResponse(status_code=403, content={"error": "No autorizado"})
    return JSONResponse(
        content={"leads": leads_db},
        headers={"X-MESAN-VERSION": "2.1.0"}
    )

# =========================================
# ACTUALIZAR LEAD
# =========================================
@app.put("/lead/{lead_id}")
async def actualizar_lead(lead_id: str, data: dict):
    for lead in leads_db:
        if lead["id"] == lead_id:
            lead["estatus"] = data.get("estatus", lead["estatus"])
            return JSONResponse(
                content={"ok": True, "lead": lead},
                headers={"X-MESAN-VERSION": "2.1.0"}
            )
    return JSONResponse(content={"ok": False})

# =========================================
# ERROR GLOBAL
# =========================================
@app.exception_handler(Exception)
async def global_exception(request: Request, exc: Exception):
    logging.error(traceback.format_exc())
    return JSONResponse(status_code=500, content={"error": "Error interno"})
