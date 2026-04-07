import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from database import init_db
from limiter import limiter
from routes.evaluar import router as evaluar_router
from routes.verificar import router as verificar_router
from datetime import datetime

try:
    from core.mesan_core import ejecutar_diagnostico
    print("DEBUG: core.mesan_core cargado OK")
except Exception as e:
    print(f"ERROR core.mesan_core: {e}")
    ejecutar_diagnostico = None

try:
    from enterprise.enterprise_engine import sistema_enterprise
    print("DEBUG: enterprise_engine cargado OK")
except Exception as e:
    print(f"ERROR enterprise_engine: {e}")
    sistema_enterprise = None

_VARS_REQUERIDAS = ["MESAN_API_KEY"]
_faltantes = [v for v in _VARS_REQUERIDAS if not os.environ.get(v)]
if _faltantes:
    print(f"ERROR: Variables faltantes: {', '.join(_faltantes)}")
    sys.exit(1)

init_db()
ES_PRODUCCION = os.environ.get("MESAN_ENV") == "production"

app = FastAPI(title="MESAN API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(evaluar_router, prefix="/api")
app.include_router(verificar_router, prefix="/api")

leads_db = []
lead_id_counter = 1

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

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

if ejecutar_diagnostico:
    @app.post("/diagnostico")
    async def diagnostico(data: dict):
        return ejecutar_diagnostico(data)

if sistema_enterprise:
    @app.post("/enterprise")
    async def enterprise(data: dict):
        return sistema_enterprise(data)

@app.post("/lead")
async def guardar_lead(data: dict):
    global lead_id_counter
    lead = {
        "id": lead_id_counter,
        "nombre": data.get("nombre"),
        "email": data.get("email"),
        "telefono": data.get("telefono"),
        "score": data.get("score"),
        "clasificacion": data.get("clasificacion"),
        "estatus": "nuevo",
        "fecha": datetime.now().isoformat()
    }
    leads_db.append(lead)
    lead_id_counter += 1
    print("NUEVO LEAD:", lead)
    return {"ok": True}

@app.get("/leads")
async def obtener_leads():
    return {"leads": leads_db}

@app.put("/lead/{lead_id}")
async def actualizar_lead(lead_id: int, data: dict):
    for lead in leads_db:
        if lead["id"] == lead_id:
            lead["estatus"] = data.get("estatus", lead["estatus"])
            return {"ok": True, "lead": lead}
    return {"ok": False}
