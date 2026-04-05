# =========================
# ROUTERS
# =========================

app.include_router(evaluar_router, prefix="/api")
app.include_router(verificar_router, prefix="/api")

# =========================
# HEALTH
# =========================

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

# =========================
# DIAGNÓSTICO (si existe)
# =========================

if ejecutar_diagnostico:

    @app.post("/diagnostico")
    async def diagnostico(data: dict):
        return ejecutar_diagnostico(data)

# =========================
# FIX CORS (OPTIONS)
# =========================

from fastapi.responses import Response

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
# ENTERPRISE
# =========================

if sistema_enterprise:

    @app.post("/enterprise")
    async def enterprise(data: dict):
        return sistema_enterprise(data)
