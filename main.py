from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from slowapi.middleware import SlowAPIMiddleware

app = FastAPI(title="MESAN Ω API")

# =========================
# FIX SLOWAPI
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
# ENDPOINTS
# =========================

@app.get("/")
def root():
    return {"status": "MESAN Ω activo"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.options("/enterprise")
def options_enterprise():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.post("/enterprise")
def enterprise(data: dict):
    return {"ok": True, "data": data}
