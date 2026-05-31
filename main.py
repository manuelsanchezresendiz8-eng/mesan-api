main.py — MESAN Ω v2.6.2

# ============================================
# MESAN Ω — main.py v2.6.2
# Enterprise Survival OS LATAM
# ============================================

print("MESAN MAIN.PY v2.6.2 LOADED")

import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MESAN Omega",
    version="2.6.2",
    docs_url="/docs",
    redoc_url="/redoc"
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
# AUTH
# ============================================

try:
    from core.auth.auth_middleware import auth_middleware

    app.middleware("http")(auth_middleware)

    print("✓ AUTH MIDDLEWARE LOADED")

except Exception as e:

    print("✗ AUTH MIDDLEWARE ERROR:", str(e))
    print(traceback.format_exc())

# ============================================
# EXECUTION ENGINE
# ============================================

try:
    from routes.execution_routes import router as execution_router

    app.include_router(execution_router)

    print("✓ EXECUTION ROUTER LOADED")

except Exception as e:

    print("✗ EXECUTION ROUTER ERROR:", str(e))
    print(traceback.format_exc())

# ============================================
# PAYMENTS
# ============================================

try:
    from pro.pagos import router as payment_router

    app.include_router(payment_router)

    print("✓ PAYMENT ROUTER LOADED")

except Exception as e:

    print("✗ PAYMENT ROUTER ERROR:", str(e))
    print(traceback.format_exc())

# ============================================
# LEADS
# ============================================

try:
    from routes.leads_routes import router as leads_router

    app.include_router(
        leads_router,
        prefix="/api",
        tags=["Leads"]
    )

    print("✓ LEADS ROUTER LOADED")

except Exception as e:

    print("✗ LEADS ROUTER ERROR:", str(e))
    print(traceback.format_exc())

# ============================================
# UPLOADS
# ============================================

try:
    from routes.upload_routes import router as upload_router

    app.include_router(upload_router)

    print("✓ UPLOAD ROUTER LOADED")

except Exception as e:

    print("✗ UPLOAD ROUTER ERROR:", str(e))
    print(traceback.format_exc())

# ============================================
# ROOT
# ============================================

@app.get("/")
async def root():

    return {
        "system": "MESAN Omega",
        "status": "online",
        "version": "2.6.2",
        "platform": "Enterprise Survival OS LATAM"
    }

# ============================================
# HEALTH
# ============================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "system": "MESAN Omega",
        "version": "2.6.2"
    }

# ============================================
# READY
# ============================================

@app.get("/ready")
async def ready():

    return {
        "ready": True
    }

# ============================================
# INFO
# ============================================

@app.get("/info")
async def info():

    return {
        "name": "MESAN Omega",
        "platform": "Enterprise Survival OS LATAM",
        "version": "2.6.2"
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
