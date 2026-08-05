# main.py -- MESAN Omega v3.3.0 Enterprise SaaS Platform
import os
import time
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core.container          import Container
from core.engine_factory     import build_engines
from core.context_middleware import context_middleware
from core.auth.auth_middleware import auth_middleware
from core.auth.basic_auth import verify_crm_credentials

from routes.execution_routes import router as execution_router
from routes.leads_routes     import router as leads_router
from routes.payment_routes   import router as payment_router
from routes.warroom_routes   import router as warroom_router    # FASE 2
from routes.omega_routes     import router as omega_router      # FASE 4
from routes.jarvis_routes    import router as jarvis_router     # JARVIS Omega

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mesan.main")

VERSION    = "3.3.0"
ENV        = os.getenv("ENV", "production")

FEATURE_WAR_ROOM      = os.getenv("FEATURE_WAR_ROOM",      "true").lower()  == "true"
FEATURE_BENCHMARKING  = os.getenv("FEATURE_BENCHMARKING",  "true").lower()  == "true"
FEATURE_PREDICTIVE_AI = os.getenv("FEATURE_PREDICTIVE_AI", "false").lower() == "true"
FEATURE_SELF_HEALING  = os.getenv("FEATURE_SELF_HEALING",  "false").lower() == "true"

FEATURES = {
    "war_room":       FEATURE_WAR_ROOM,
    "benchmarking":   FEATURE_BENCHMARKING,
    "predictive_ai":  FEATURE_PREDICTIVE_AI,
    "self_healing":   FEATURE_SELF_HEALING,
}

CRITICAL_ENGINES = [
    e.strip() for e in
    os.getenv("CRITICAL_ENGINES", "Governance,FiscalSentinel,ComplianceVerify,LaborShield").split(",")
]

def build_engines_safe():
    try:
        engines, degraded = build_engines()
    except Exception as e:
        logger.critical("[ENGINE_FACTORY] Fallo al construir engines: %s", e)
        raise
    logger.info("[STARTUP] Engines cargados: %s", list(engines.keys()))
    if degraded:
        logger.warning("[STARTUP] Engines degradados: %s", list(degraded.keys()))
    for critical in CRITICAL_ENGINES:
        if critical not in engines:
            msg = f"Engine critico no disponible: {critical}"
            logger.critical("[STARTUP_VALIDATION] %s", msg)
            raise RuntimeError(msg)
    return engines, degraded


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_complete = False
    container = Container()
    logger.info("MESAN Omega v%s iniciando (ENV=%s)", VERSION, ENV)
    if ENV != "production":
        logger.warning("[CORS] Modo desarrollo: origenes abiertos (*). Verificar ENV=production en Render.")
    logger.info("Features: %s", FEATURES)

    engines, errors = build_engines_safe()
    from core.engine_factory import get_engine_metadata
    for name, engine in engines.items():
        try:
            meta = get_engine_metadata(name)
        except Exception:
            meta = None
        container.register_engine(name, engine, metadata=meta)
    container.set_degraded(errors)
    app.state.container  = container
    app.state.started_at = time.time()

    try:
        from services.omega_orchestrator import omega_orchestrator
        if not callable(getattr(omega_orchestrator, "ejecutar", None)):
            raise RuntimeError("OmegaOrchestrator invalid interface")
        app.state.orchestrator = omega_orchestrator
        omega_orchestrator.load_engines()
        logger.info("[Orchestrator] Registrado en app.state — engines pre-cargados")
    except Exception as exc:
        logger.exception("[Orchestrator] Failed to load: %s", exc)
        raise RuntimeError("OmegaOrchestrator startup failure") from exc

    app.state.self_healing     = None
    app.state.startup_complete = True
    logger.info("MESAN Omega v%s READY | engines=%s", VERSION, list(engines.keys()))
    yield

    if getattr(app.state, "self_healing", None):
        app.state.self_healing.stop()
    logger.info("SHUTDOWN COMPLETE")


app = FastAPI(
    title="MESAN Omega — Enterprise Risk Intelligence Platform",
    version=VERSION,
    lifespan=lifespan,
    docs_url="/docs" if ENV != "production" else None,
    redoc_url=None,
)


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

app.middleware("http")(auth_middleware)
app.middleware("http")(context_middleware)

@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


allow_origins = (
    ["https://mesanomega.com", "https://www.mesanomega.com"]
    if ENV == "production" else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["X-Trace-Id", "X-Latency-Ms"],
)


@app.get("/crm_enterprise.html")
async def crm_enterprise(_user: str = Depends(verify_crm_credentials)):
    return FileResponse("crm_enterprise.html")


app.include_router(execution_router,              tags=["Diagnostico"])
app.include_router(leads_router,                  tags=["Leads"])
app.include_router(payment_router, prefix="/pro", tags=["Pagos"])
app.include_router(warroom_router, prefix="/api/v1", tags=["War Room"])
app.include_router(omega_router,   prefix="/api/v1", tags=["Omega"])
app.include_router(jarvis_router,                 tags=["JARVIS"])


@app.get("/health", tags=["Sistema"])
def health(request: Request):
    c        = getattr(request.app.state, "container", None)
    engines_loaded = c.engine_count() if c else 0
    degraded       = c.get_degraded() if c else {}
    healing  = getattr(request.app.state, "self_healing", None)
    startup_complete = getattr(request.app.state, "startup_complete", False)
    c_diag = c.diagnostics() if c else {}
    if not startup_complete:
        status = "STARTING"
    elif c_diag.get("unhealthy_engines", 0) > 0:
        status = "UNHEALTHY"
    elif degraded:
        status = "DEGRADED"
    else:
        status = "OK"
    body = {
        "status":           status,
        "version":          VERSION,
        "env":              ENV,
        "uptime_seconds":   round(time.time() - getattr(request.app.state, "started_at", time.time()), 2),
        "engines_loaded":   engines_loaded,
        "engines_degraded": len(degraded),
        "features":         FEATURES,
        "self_healing":     {"enabled": FEATURE_SELF_HEALING, "running": healing is not None},
        "timestamp":        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **({k: v for k, v in c.diagnostics().items()
            if k in ("healthy_engines", "degraded_engines", "unhealthy_engines")}
           if c else {}),
    }
    http_code = 503 if status in ("STARTING", "UNHEALTHY") else 200
    return JSONResponse(status_code=http_code, content=body)


@app.get("/ready", tags=["Sistema"])
def ready(request: Request):
    c       = getattr(request.app.state, "container", None)
    engines = c.list_engines() if c else []
    missing = [e for e in CRITICAL_ENGINES if e not in engines]
    if missing or not c:
        return JSONResponse(status_code=503, content={"status": "NOT_READY", "missing": missing})
    return {"status": "READY", "engines": engines}


@app.get("/engines", tags=["Sistema"])
def engines_status(request: Request):
    c = getattr(request.app.state, "container", None)
    if not c:
        return JSONResponse(status_code=503, content={"status": "STARTING"})
    engine_names = c.list_engines()
    engines_info = {
        name: getattr(c.get_engine(name), "version", "unknown")
        for name in engine_names
    }
    degraded = c.get_degraded()
    return {
        "status":   "DEGRADED" if degraded else "OK",
        "engines":  engines_info,
        "degraded": degraded,
        "total":    len(engine_names),
    }


@app.get("/diagnostics", tags=["Sistema"])
def diagnostics(request: Request):
    c = getattr(request.app.state, "container", None)
    if not c:
        return JSONResponse(status_code=503, content={"status": "STARTING"})
    return {
        "version":        VERSION,
        "env":            ENV,
        **c.diagnostics(),
        "features":       FEATURES,
        "uptime_seconds": round(time.time() - getattr(request.app.state, "started_at", time.time()), 2),
    }


@app.get("/features", tags=["Sistema"])
def features():
    return {"features": FEATURES}


from fastapi import HTTPException
from pydantic import ValidationError as PydanticValidationError

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    trace_id = getattr(request.state, "trace_id", "-")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": exc.detail, "trace_id": trace_id},
        headers=exc.headers,
    )

@app.exception_handler(PydanticValidationError)
async def validation_error_handler(request: Request, exc: PydanticValidationError):
    trace_id = getattr(request.state, "trace_id", "-")
    return JSONResponse(status_code=422, content={
        "error": "VALIDATION_ERROR", "message": "Request validation failed",
        "details": exc.errors(), "trace_id": trace_id,
    })

@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    trace_id = getattr(request.state, "trace_id", "-")
    logger.warning("[%s] KeyError: %s", trace_id, exc)
    return JSONResponse(status_code=404, content={
        "error": "NOT_FOUND", "message": f"Resource not found: {exc}", "trace_id": trace_id,
    })

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    trace_id = getattr(request.state, "trace_id", "-")
    logger.warning("[%s] ValueError: %s", trace_id, exc)
    return JSONResponse(status_code=400, content={
        "error": "INVALID_INPUT", "message": str(exc), "trace_id": trace_id,
    })

@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "-")
    logger.exception("[%s] SYSTEM FAILURE: %s", trace_id, exc)
    return JSONResponse(status_code=500, content={
        "error": "INTERNAL_ERROR", "message": "MESAN internal failure", "trace_id": trace_id,
    })


app.mount("/", StaticFiles(directory=".", html=True), name="static")


_SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://mesan-api.onrender.com https://mesanomega.com; "
        "frame-ancestors 'none';"
    ),
}


class SecurityHeadersMiddleware:
    def __init__(self, asgi_app):
        self.app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                existing = {h[0].lower() for h in headers}
                for name, value in _SECURITY_HEADERS.items():
                    key = name.lower().encode()
                    if key not in existing:
                        headers.append((key, value.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)


app = SecurityHeadersMiddleware(app)