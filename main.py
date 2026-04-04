import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from database import init_db
from limiter import limiter
from routes.evaluar import router as evaluar_router
from routes.verificar import router as verificar_router

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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

_origins_raw = os.environ.get("MESAN_ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(evaluar_router, prefix="/api")
app.include_router(verifican_router, prefix="/api")

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


