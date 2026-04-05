from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI(title="MESAN Ω API")

# =========================
# CORS
# =========================

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
    return {"status": "ok", "version": "2.0.0"}

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
