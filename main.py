# main.py -- MESAN Omega v3.2.0 Enterprise SaaS Platform
import os
import time
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.container          import Container
from core.engine_factory     import build_engines
from core.context_middleware import context_middleware
from core.auth.auth_middleware import auth_middleware
from core.observability_bus  import omega_bus
from core.circuit_breaker    import circuit_registry
# from core.self_healing_engine import SelfHealingEngine        # FASE 2 — pendiente

from routes.execution_routes import router as execution_router
from routes.leads_routes     import router as leads_router
from routes.payment_routes   import router as payment_router
from routes.warroom_routes   import router as warroom_router    # FASE 2
from routes.omega_routes     import router as omega_router      # FASE 4

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mesan.main")

# ── Config ────────────────────────────────────────────────────────────────────
VERSION    = "3.3.0"
ENV        = os.getenv("ENV", "production")
START_TIME = time.time()

# ── Feature Flags ─────────────────────────────────────────────────────────────
FEATURE_WAR_ROOM      = os.getenv("FEATURE_WAR_ROOM",      "true").lower()  == "true"
FEATURE_BENCHMARKING  = os.getenv("FEATURE_BENCHMARKING",  "true").lower()  == "true"
FEATURE_PREDICTIVE_AI = os.getenv("FEATURE_PREDICTIVE_AI", "false").lower() == "true"
FEATURE_SELF_HEALING  = os.getenv("FEATURE_SELF_HEALING",  "true").lower()  == "true"   # FASE 2

FEATURES = {
    "war_room":       FEATURE_WAR_ROOM,
    "benchmarking":   FEATURE_BENCHMARKING,
    "predictive_ai":  FEATURE_PREDICTIVE_AI,
    "self_healing":   FEATURE_SELF_HEALING,
}

# ── Engines críticos requeridos para startup ──────────────────────────────────
CRITICAL_ENGINES = os.getenv(
    "CRITICAL_ENGINES",
    "Governance,FiscalSentinel,ComplianceVerify,LaborShield"
).split(",")

# ── Container ─────────────────────────────────────────────────────────────────
container = Container()


# ── Engine Factory ────────────────────────────────────────────────────────────
def build_engines_safe():
    try:
        engines = build_engines()
    except Exception as e:
        logger.critical("[ENGINE_FACTORY] Fallo al construir engines: %s", e)
        raise

    for critical in CRITICAL_ENGINES:
        if critical not in engines:
            msg = f"Engine critico no disponible: {critical}"
            logger.critical("[STARTUP_VALIDATION] %s", msg)
            raise RuntimeError(msg)

    return engines, {}


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MESAN Ω v%s iniciando (ENV=%s)", VERSION, ENV)
    logger.info("Features: %s", FEATURES)

    # Engines
    engines, errors = build_engines_safe()
    for name, engine in engines.items():
        container.register_engine(name, engine)
    container.engines  = engines
    container.degraded = errors
    app.state.container  = container
    app.state.started_at = time.time()

    # ── FASE 4 — OmegaOrchestrator en app.state ──────────────────────────────
    from services.omega_orchestrator import omega_orchestrator
    app.state.orchestrator = omega_orchestrator
    logger.info("[Orchestrator] Registrado en app.state")

    # ── FASE 2 — Self Healing Audit Mode ──────────────────────────────────────
    app.state.self_healing = None  # FASE 2 pendiente
    # ─────────────────────────────────────────────────────────────────────────

    logger.info("MESAN Ω v%s READY | engines=%s", VERSION, list(engines.keys()))
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    if getattr(app.state, "self_healing", None):
        app.state.self_healing.stop()
        logger.info("[SelfHealing] Detenido")

    logger.info("SHUTDOWN COMPLETE")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MESAN Ω — Enterprise Risk Intelligence Platform",
    version=VERSION,
    lifespan=lifespan,
    docs_url="/docs" if ENV != "production" else None,
    redoc_url=None,
)


# ── Middleware: Trace ID ──────────────────────────────────────────────────────
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


# ── Middleware: Context y Auth ────────────────────────────────────────────────
app.middleware("http")(context_middleware)
app.middleware("http")(auth_middleware)


# ── Middleware: Latency ───────────────────────────────────────────────────────
@app.middleware("http")
async def latency_middleware(request: Request, call_next):
    start    = time.time()
    response = await call_next(request)
    latency  = round((time.time() - start) * 1000, 2)
    response.headers["X-Latency-Ms"] = str(latency)
    logger.info("[%s] %s %s → %s (%sms)",
        getattr(request.state, "trace_id", "-"),
        request.method, request.url.path,
        response.status_code, latency)
    return response


# ── CORS ──────────────────────────────────────────────────────────────────────
allow_origins = (
    ["https://mesanomega.com", "https://www.mesanomega.com"]
    if ENV == "production" else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-Id", "X-Latency-Ms"],
)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(execution_router,              tags=["Diagnóstico"])
app.include_router(leads_router,   prefix="/api/leads",  tags=["Leads"])
app.include_router(payment_router, prefix="/pro",        tags=["Pagos"])
app.include_router(warroom_router, prefix="/api/v1",     tags=["War Room"])   # FASE 2
app.include_router(omega_router,   prefix="/api/v1",     tags=["Omega"])      # FASE 4


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
def health(request: Request):
    c        = getattr(request.app.state, "container", None)
    engines  = getattr(c, "engines",  {}) or {}
    degraded = getattr(c, "degraded", {}) or {}
    healing  = getattr(request.app.state, "self_healing", None)

    return {
        "status":              "DEGRADED" if degraded else "OK",
        "version":             VERSION,
        "env":                 ENV,
        "uptime_seconds":      round(time.time() - request.app.state.started_at, 2),
        "engines_loaded":      len(engines),
        "engines_degraded":    len(degraded),
        "features":            FEATURES,
        "self_healing":        healing.status() if healing else None,   # FASE 2
        "timestamp":           time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ── Readiness ─────────────────────────────────────────────────────────────────
@app.get("/ready", tags=["Sistema"])
def ready(request: Request):
    c       = getattr(request.app.state, "container", None)
    engines = getattr(c, "engines", {}) or {}
    missing = [e for e in CRITICAL_ENGINES if e not in engines]

    if missing or not c:
        return JSONResponse(status_code=503, content={
            "status":  "NOT_READY",
            "missing": missing,
        })

    return {"status": "READY", "engines": list(engines.keys())}


# ── Engines ───────────────────────────────────────────────────────────────────
@app.get("/engines", tags=["Sistema"])
def engines_status(request: Request):
    c        = request.app.state.container
    engines  = getattr(c, "engines",  {}) or {}
    degraded = getattr(c, "degraded", {}) or {}

    return {
        "status":   "DEGRADED" if degraded else "OK",
        "engines":  {name: getattr(e, "version", "unknown") for name, e in engines.items()},
        "degraded": degraded,
        "total":    len(engines),
    }


# ── Features ──────────────────────────────────────────────────────────────────
@app.get("/features", tags=["Sistema"])
def features():
    return {"features": FEATURES}


# ── Error Handler ─────────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "-")
    logger.exception("[%s] SYSTEM FAILURE: %s", trace_id, exc)
    return JSONResponse(status_code=500, content={
        "error":    "INTERNAL_ERROR",
        "message":  "MESAN internal failure",
        "trace_id": trace_id,
    })
