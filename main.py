from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from slowapi.middleware import SlowAPIMiddleware

# (si los usas, si no existen puedes comentarlos)
# from database import init_db
# from limiter import limiter
# from routes.evaluar import router as evaluar_router
# from routes.verificar import router as verificar_router

# =========================
# APP
# =========================

app = FastAPI(title="MESAN Ω API")

# =========================
# FIX SLOWAPI (NO BLOQUEAR OPTIONS)
# =========================

class CustomSlowAPIMiddleware(SlowAPIMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        return await super().dispatch(request, call_next)

# =========================
# MIDDLEWARES
# =========================

app.add_middleware(CustomSlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ENDPOINTS BASE
# =========================

@app.get("/")
def root():
    return {"status": "MESAN Ω activo"}

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

# =========================
# FIX CORS (PRE-FLIGHT)
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
# ENDPOINT ENTERPRISE
# =========================

@app.post("/enterprise")
def enterprise(data: dict):
    return {
        "mensaje": "MESAN Ω funcionando",
        "data_recibida": data
    }
