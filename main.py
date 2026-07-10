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
# from core.self_healing_engine import SelfHealingEngine        # FASE 2 — pendiente

from routes.execution_routes import router as execution_router
from routes.leads_routes     import router as leads_router
from routes.payment_routes   import router as payment_router
from routes.warroom_routes   import router as warroom_router    # FASE 2
from routes.omega_routes     import router as omega_router      # FASE 4
from routes.jarvis_routes    import router as jarvis_router     # JARVIS Omega
from routes.guardian_routes  import router as guardian_router   # Guardian Omega
from routes.jarvis_sales_routes import router as jarvis_sales_router  # JARVIS Sales
from routes.market_routes import router as market_router  # Market Intelligence

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mesan.main")

# ── Config ────────────────────────────────────────────────────────────────────
VERSION    = "3.3.0"
ENV        = os.getenv("ENV", "production")

# ── Feature Flags ─────────────────────────────────────────────────────────────
FEATURE_WAR_ROOM      = os.getenv("FEATURE_WAR_ROOM",      "true").lower()  == "true"
FEATURE_BENCHMARKING  = os.getenv("FEATURE_BENCHMARKING",  "true").lower()  == "true"
FEATURE_PREDICTIVE_AI = os.getenv("FEATURE_PREDICTIVE_AI", "false").lower() == "true"
FEATURE_SELF_HEALING  = os.getenv("FEATURE_SELF_HEALING",  "false").lower() == "true"   # FASE 2 — false hasta implementación real

FEATURES = {
    "war_room":       FEATURE_WAR_ROOM,
    "benchmarking":   FEATURE_BENCHMARKING,
    "predictive_ai":  FEATURE_PREDICTIVE_AI,
    "self_healing":   FEATURE_SELF_HEALING,
}

# ── Engines críticos requeridos para startup ──────────────────────────────────
CRITICAL_ENGINES = [
    e.strip() for e in
    os.getenv("CRITICAL_ENGINES", "Governance,FiscalSentinel,ComplianceVerify,LaborShield").split(",")
]

# ── Engine Factory ────────────────────────────────────────────────────────────
def build_engines_safe():
    try:
        engines, degraded = build_engines()  # P0: recibe tuple con degraded
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


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_complete = False  # obs-2: inicializar explícito
    container = Container()              # Fix 1: instancia local — sin contaminación entre procesos/tests
    logger.info("MESAN Ω v%s iniciando (ENV=%s)", VERSION, ENV)
    if ENV != "production":
        logger.warning("[CORS] Modo desarrollo: orígenes abiertos (*). Verificar ENV=production en Render.")
    logger.info("Features: %s", FEATURES)

    # Engines
    engines, errors = build_engines_safe()
    from core.engine_factory import get_engine_metadata  # importado una vez, fuera del loop
    for name, engine in engines.items():
        try:
            meta = get_engine_metadata(name)
        except Exception:
            meta = None
        container.register_engine(name, engine, metadata=meta)
    # P0-2: usar métodos explícitos — sin atributos dinámicos
    container.set_degraded(errors)
    app.state.container  = container
    app.state.started_at = time.time()

    # ── FASE 4 — OmegaOrchestrator en app.state (P0: blindado) ──────────────
    try:
        from services.omega_orchestrator import omega_orchestrator
        if not callable(getattr(omega_orchestrator, "ejecutar", None)):
            raise RuntimeError("OmegaOrchestrator invalid interface — missing callable ejecutar()")
        app.state.orchestrator = omega_orchestrator
        omega_orchestrator.load_engines()   # Fix 3: API pública — warm-up sin acoplamiento interno
        logger.info("[Orchestrator] Registrado en app.state — engines pre-cargados")
    except Exception as exc:
        logger.exception("[Orchestrator] Failed to load: %s", exc)
        raise RuntimeError("OmegaOrchestrator startup failure") from exc

    # ── FASE 2 — Self Healing Audit Mode ──────────────────────────────────────
    # TODO P1-5: activar Self-Healing real cuando FEATURE_SELF_HEALING=true
    # Requiere: implementar SelfHealingEngine con circuit_breaker integration
    # TODO P1-4: conectar circuit_breaker al campo circuit_state de Container
    app.state.self_healing = None  # FASE 2 pendiente
    # ─────────────────────────────────────────────────────────────────────────

    from core.jarvis.guardian_setup import setup_guardian
    setup_guardian()
    app.state.startup_complete = True  # P0-3: flag para health endpoint
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


# ── Middleware — orden de registro inverso al de ejecución ───────────────────
# Ejecución deseada: trace → context → auth → latency
# Registro FastAPI (inverso): latency primero, trace último

# 4. Latency (ejecuta último — mide tiempo total incluyendo auth)
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

# 3. Auth (ejecuta después de context, necesita trace_id)
app.middleware("http")(auth_middleware)

# 2. Context (ejecuta después de trace)
app.middleware("http")(context_middleware)

# 1. Trace ID (ejecuta primero — establece trace_id para todos los demás)
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


# ── CORS ──────────────────────────────────────────────────────────────────────
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


# ── CRM Enterprise — PROTEGIDA (Basic Auth) ───────────────────────────────────
# Debe registrarse ANTES del StaticFiles mount para que FastAPI le dé
# prioridad sobre el archivo estático del mismo nombre.
#
# ADVERTENCIA: si se elimina Depends(verify_crm_credentials), la ruta
# quedará pública sin que auth_middleware lo detecte (está exenta de JWT
# por diseño en core/auth/auth_middleware.py).
@app.get("/crm_enterprise.html")
async def crm_enterprise(_user: str = Depends(verify_crm_credentials)):
    """
    Sirve el panel CRM enterprise.
    PROTEGIDA: requiere Basic Auth (CRM_BASIC_USER / CRM_BASIC_PASSWORD).
    Exenta de JWT en auth_middleware.py — NO eliminar Depends(verify_crm_credentials).
    """
    return FileResponse("crm_enterprise.html")


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(execution_router,              tags=["Diagnóstico"])
app.include_router(leads_router,   tags=["Leads"])
app.include_router(payment_router, prefix="/pro",        tags=["Pagos"])
app.include_router(warroom_router, prefix="/api/v1",     tags=["War Room"])   # FASE 2
app.include_router(omega_router,   prefix="/api/v1",     tags=["Omega"])      # FASE 4
app.include_router(jarvis_router,                         tags=["JARVIS"])
app.include_router(guardian_router,                       tags=["Guardian"])
app.include_router(jarvis_sales_router,                   tags=["JARVIS Sales"])
app.include_router(market_router,                         tags=["Market Intelligence"])


# ── Health ────────────────────────────────────────────────────────────────────
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
        "status":              status,
        "version":             VERSION,
        "env":                 ENV,
        "uptime_seconds":      round(time.time() - getattr(request.app.state, "started_at", time.time()), 2),
        "engines_loaded":      engines_loaded,
        "engines_degraded":    len(degraded),
        "features":            FEATURES,
        "self_healing":        {"enabled": FEATURE_SELF_HEALING, "running": healing is not None},  # FASE 2
        "timestamp":           time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **({k: v for k, v in c.diagnostics().items()
            if k in ("healthy_engines", "degraded_engines", "unhealthy_engines")}
           if c else {}),
    }
    http_code = 503 if status in ("STARTING", "UNHEALTHY") else 200
    return JSONResponse(status_code=http_code, content=body)


# ── Readiness ─────────────────────────────────────────────────────────────────
@app.get("/ready", tags=["Sistema"])
def ready(request: Request):
    c       = getattr(request.app.state, "container", None)
    engines = c.list_engines() if c else []
    missing = [e for e in CRITICAL_ENGINES if e not in engines]

    if missing or not c:
        return JSONResponse(status_code=503, content={
            "status":  "NOT_READY",
            "missing": missing,
        })

    return {"status": "READY", "engines": engines}


# ── Engines ───────────────────────────────────────────────────────────────────
@app.get("/engines", tags=["Sistema"])
def engines_status(request: Request):
    c = getattr(request.app.state, "container", None)
    if not c:
        return JSONResponse(status_code=503, content={
            "status":  "STARTING",
            "message": "Container not ready — startup in progress",
        })
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


# ── Diagnostics ───────────────────────────────────────────────────────────────
@app.get("/diagnostics", tags=["Sistema"])
def diagnostics(request: Request):
    """Observabilidad operativa completa — para soporte y monitoreo comercial."""
    c = getattr(request.app.state, "container", None)
    if not c:
        return JSONResponse(status_code=503, content={"status": "STARTING"})
    return {
        "version":    VERSION,
        "env":        ENV,
        **c.diagnostics(),
        "features":   FEATURES,
        "uptime_seconds": round(
            time.time() - getattr(request.app.state, "started_at", time.time()), 2
        ),
    }


# ── Features ──────────────────────────────────────────────────────────────────
@app.get("/features", tags=["Sistema"])
def features():
    return {"features": FEATURES}


# ── Error Handler ─────────────────────────────────────────────────────────────
from fastapi import HTTPException
from pydantic import ValidationError as PydanticValidationError

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    trace_id = getattr(request.state, "trace_id", "-")
    # IMPORTANTE: se preservan exc.headers. Sin esto, las respuestas 401
    # generadas por HTTPBasic() (FastAPI) o por verify_crm_credentials()
    # pierden el header WWW-Authenticate: Basic, y el navegador nunca
    # muestra el prompt nativo de usuario/contraseña para Basic Auth.
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error":    "HTTP_ERROR",
            "message":  exc.detail,
            "trace_id": trace_id,
        },
        headers=exc.headers,
    )

@app.exception_handler(PydanticValidationError)
async def validation_error_handler(request: Request, exc: PydanticValidationError):
    trace_id = getattr(request.state, "trace_id", "-")
    return JSONResponse(status_code=422, content={
        "error":    "VALIDATION_ERROR",
        "message":  "Request validation failed",
        "details":  exc.errors(),
        "trace_id": trace_id,
    })

@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    trace_id = getattr(request.state, "trace_id", "-")
    logger.warning("[%s] KeyError: %s", trace_id, exc)
    return JSONResponse(status_code=404, content={
        "error":    "NOT_FOUND",
        "message":  f"Resource not found: {exc}",
        "trace_id": trace_id,
    })

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    trace_id = getattr(request.state, "trace_id", "-")
    logger.warning("[%s] ValueError: %s", trace_id, exc)
    return JSONResponse(status_code=400, content={
        "error":    "INVALID_INPUT",
        "message":  str(exc),
        "trace_id": trace_id,
    })

@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "-")
    logger.exception("[%s] SYSTEM FAILURE: %s", trace_id, exc)
    return JSONResponse(status_code=500, content={
        "error":    "INTERNAL_ERROR",
        "message":  "MESAN internal failure",
        "trace_id": trace_id,
    })


# ── Static Files — debe ir AL FINAL, después de todas las rutas ──────────────
# Sirve index.html, styles.css, páginas legales, etc.
# /crm_enterprise.html está protegida arriba y FastAPI le da prioridad
# sobre este mount por estar registrada antes.
# Los security headers los agrega SecurityHeadersMiddleware (ASGI puro) abajo,
# que intercepta http.response.start y cubre TODAS las respuestas incluyendo
# StaticFiles, FileResponse, StreamingResponse y errores.
app.mount("/", StaticFiles(directory=".", html=True), name="static")


# ── Security Headers — Middleware ASGI puro ───────────────────────────────────
# Debe envolverse DESPUÉS de app.mount() para que cubra también StaticFiles.
# BaseHTTPMiddleware (los @app.middleware("http")) no cubre StaticFiles porque
# Starlette los sirve directamente sin pasar por el middleware stack HTTP.
# Un middleware ASGI puro sí los cubre porque intercepta a nivel de protocolo
# ASGI (http.response.start / http.response.body), antes de que la respuesta
# salga del servidor.
#
# Cubre: API, CRM, landing, páginas legales, assets estáticos, errores 4xx/5xx.
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
    """Middleware ASGI puro que agrega security headers a TODAS las respuestas.

    A diferencia de BaseHTTPMiddleware, opera a nivel de protocolo ASGI
    interceptando el mensaje http.response.start — por eso funciona para
    StaticFiles, FileResponse, StreamingResponse y cualquier otra respuesta
    que Starlette/FastAPI genere, incluyendo errores.
    """

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


# Envolver la app completa con el middleware ASGI puro.
# Esto debe ir AL FINAL — después de app.mount() — para que cubra
# también las rutas montadas por StaticFiles.
app = SecurityHeadersMiddleware(app)
