# main.py -- MESAN Omega v2.7.0 Production Entry Point
import os
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Core ──────────────────────────────────────────────────────────────────────
from core.auth.auth_middleware import auth_middleware

# ── Routers ───────────────────────────────────────────────────────────────────
from routes.execution_routes import router as execution_router
from routes.leads_routes      import router as leads_router
from routes.payment_routes    import router as payment_router

# ── Engines (import verifica disponibilidad al arranque) ──────────────────────
from services.fiscal_sentinel_engine       import FiscalSentinelEngine
from services.compliance_verify_engine     import ComplianceVerifyEngine
from services.labor_shield_engine          import LaborShieldEngine
from services.contractual_risk_engine      import ContractualRiskEngine
from services.policy_audit_engine          import PolicyAuditEngine
from services.governance_engine            import GovernanceEngine
from services.continuity_engine            import ContinuityEngine
from services.remediation_engine           import RemediationEngine
from services.executive_narrative_generator import ExecutiveNarrativeGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mesan.main")

ENV     = os.getenv("ENV", "production").lower()
VERSION = "2.7.0"

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MESAN Ω v%s arrancando — ENV=%s", VERSION, ENV)
    logger.info("Engines cargados: FiscalSentinel, ComplianceVerify, LaborShield, "
                "ContractualRisk, PolicyAudit, Governance, Continuity, Remediation, Narrative")
    yield
    logger.info("MESAN Ω apagando")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MESAN Ω — Risk Intelligence API",
    description="Sistema de Inteligencia de Riesgos Empresariales para México y LATAM",
    version=VERSION,
    lifespan=lifespan,
    docs_url="/docs" if ENV != "production" else None,
    redoc_url=None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://mesanomega.com,https://www.mesanomega.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + ["*"] if ENV == "development" else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Auth middleware ───────────────────────────────────────────────────────────
app.middleware("http")(auth_middleware)

# ── Latency logger ────────────────────────────────────────────────────────────
@app.middleware("http")
async def latency_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = round((time.time() - start) * 1000, 2)
    response.headers["X-Latency-Ms"] = str(ms)
    logger.info("%s %s → %s  %.0fms", request.method, request.url.path, response.status_code, ms)
    return response

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(execution_router,   tags=["Diagnóstico"])
app.include_router(leads_router,       prefix="/api/leads", tags=["Leads"])
app.include_router(payment_router,     prefix="/pro",       tags=["Pagos"])

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
def health():
    return {
        "status":  "OK",
        "system":  "MESAN Ω",
        "version": VERSION,
        "env":     ENV,
        "engines": [
            "FiscalSentinel", "ComplianceVerify", "LaborShield",
            "ContractualRisk", "PolicyAudit", "Governance",
            "Continuity", "Remediation", "Narrative"
        ]
    }

# ── Engine status ─────────────────────────────────────────────────────────────
@app.get("/engines", tags=["Sistema"])
def engines_status():
    engines = {
        "FiscalSentinelEngine":        FiscalSentinelEngine().version,
        "ComplianceVerifyEngine":      ComplianceVerifyEngine().version,
        "LaborShieldEngine":           LaborShieldEngine().version,
        "ContractualRiskEngine":       ContractualRiskEngine().version,
        "PolicyAuditEngine":           PolicyAuditEngine().version,
        "GovernanceEngine":            GovernanceEngine().version,
        "ContinuityEngine":            ContinuityEngine().version,
        "RemediationEngine":           RemediationEngine().version,
        "ExecutiveNarrativeGenerator": ExecutiveNarrativeGenerator().version,
    }
    return {"status": "OK", "engines": engines, "total": len(engines)}

# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s | path=%s", exc, request.url.path)
    return JSONResponse(status_code=500, content={
        "error":   "INTERNAL_ERROR",
        "message": "Error interno del sistema MESAN Ω",
        "path":    request.url.path,
    })
