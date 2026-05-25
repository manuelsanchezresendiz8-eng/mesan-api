# ============================================
# MESAN Ω — main.py v2.5.0
# Enterprise Survival OS LATAM
# ============================================

print("MESAN MAIN.PY v2.5.0 LOADED")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.execution_routes import router as execution_router

# ============================================
# APP
# ============================================

app = FastAPI(
    title="MESAN Omega",
    version="2.5.0"
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
# MIDDLEWARE
# ============================================

from core.auth.auth_middleware import auth_middleware
app.middleware("http")(auth_middleware)

# ============================================
# ROUTERS
# ============================================

app.include_router(execution_router)

# ============================================
# HEALTH
# ============================================

@app.get("/")
async def root():
    return {"system": "MESAN Omega", "status": "online", "version": "2.5.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.5.0"}

@app.get("/ready")
async def ready():
    return {"ready": True}

# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup_event():
    print("MESAN Ω ENTERPRISE ONLINE")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
