# ============================================
# MESAN Ω — main.py v2.5.1
# ============================================

print("MESAN MAIN.PY v2.5.1 LOADED")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ============================================
# APP
# ============================================

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
# IMPORT ROUTERS
# ============================================

try:
    from routes.execution_routes import router as execution_router

    app.include_router(execution_router)

    print("EXECUTION ROUTER LOADED")

except Exception as e:
    print("ROUTER LOAD ERROR:", str(e))

# ============================================
# ROOT
# ============================================

@app.get("/")
async def root():
    return {
        "system": "MESAN Omega",
        "status": "online",
        "version": "2.5.1"
    }

# ============================================
# HEALTH
# ============================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.5.1"
    }

# ============================================
# READY
# ============================================

@app.get("/ready")
async def ready():
    return {"ready": True}

# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup_event():
    print("MESAN Ω ENTERPRISE ONLINE")

# ============================================
# LOCAL RUN
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
