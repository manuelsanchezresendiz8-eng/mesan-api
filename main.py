# ============================================
# MESAN Ω — main.py v2.5.1
# Enterprise Survival OS LATAM
# ============================================

print("MESAN MAIN.PY v2.5.1 LOADED")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MESAN Omega",
    version="2.5.1"
)

# ============================================
# CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# AUTH MIDDLEWARE
# ============================================

from core.auth.auth_middleware import auth_middleware

app.middleware("http")(auth_middleware)

# ============================================
# DEBUG IMPORTS
# ============================================

try:
    import routes.execution_routes
    print("execution_routes OK")

except Exception as e:
    import traceback

    print("execution_routes ERROR:")
    print(traceback.format_exc())

try:
    import services.fiscal_sentinel_engine
    print("fiscal_sentinel_engine OK")

except Exception as e:
    import traceback

    print("fiscal_sentinel_engine ERROR:")
    print(traceback.format_exc())

try:
    import services.compliance_verify_engine
    print("compliance_verify_engine OK")

except Exception as e:
    import traceback

    print("compliance_verify_engine ERROR:")
    print(traceback.format_exc())

try:
    import core.billing.billing_engine
    print("billing_engine OK")

except Exception as e:
    import traceback

    print("billing_engine ERROR:")
    print(traceback.format_exc())

# ============================================
# ROUTER LOAD
# ============================================

try:

    from routes.execution_routes import router as execution_router

    app.include_router(execution_router)

    print("EXECUTION ROUTER LOADED")

except Exception as e:

    import traceback

    print("ROUTER LOAD ERROR:", str(e))

    print(
        "ROUTER TRACEBACK:\n",
        traceback.format_exc()
    )

# ============================================
# HEALTH
# ============================================

@app.get("/")
async def root():
    return {
        "system": "MESAN Omega",
        "status": "online",
        "version": "2.5.1"
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.5.1"
    }

@app.get("/ready")
async def ready():
    return {
        "ready": True
    }

# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup_event():
    print("MESAN Ω ENTERPRISE ONLINE")

# ============================================
# LOCAL DEV
# ============================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
