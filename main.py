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
from routes.verificar import router as verificar_routerfrom core.mesan_core import ejecutar_diagnostico
from enterprise.enterprise_engine import sistema_enterprise


_VARS_REQUERIDAS = ["MESAN_API_KEY"]
_faltantes = [v for v in _VARS_REQUERIDAS if not os.environ.get(v)]
if _faltantes:
    print(f"ERROR: Variables faltantes: {', '.join(_faltantes)}")
    sys.exit(1)

init_db()
ES_PRODUCCION = os.environ.get("MESAN_ENV") == "production"

app = FastAPI(
    title="MESAN API",
    version="2.0.0",
    docs_url=None if ES_PRODUCCION else "/docs",
    redoc_url=None
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

_origins_raw = os.environ.get("MESAN_ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"]
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.exception_handler(Exception)
async def error_global(request: Request, exc: Exception):
    if not ES_PRODUCCION:
        return JSONResponse(status_code=500,
            content={"error": "Error interno", "detalle": str(exc)})
    return JSONResponse(status_code=500,
        content={"error": "Error interno del servidor"})

app.include_router(evaluar_router, prefix="/api")
app.include_router(verificar_router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}  
    @app.post("/diagnostico")
def diagnostico(data: dict):
    return ejecutar_diagnostico(data)

@app.post("/enterprise")
def enterprise(data: dict):
    return sistema_enterprise(data)

@app.get("/health")
def health():
    return {"status": "ok"}

