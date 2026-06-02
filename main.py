# main.py -- MESAN Omega v3.0.4 Distributed Intelligence Platform
import os
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.container import Container
from core.engine_factory import build_engines
from core.context_middleware import context_middleware
from core.auth.auth_middleware import auth_middleware

from routes.execution_routes import router as execution_router
from routes.leads_routes import router as leads_router
from routes.payment_routes import router as payment_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mesan.main")

VERSION = "3.0.4"
ENV = os.getenv("ENV", "production")

container = Container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    engines = build_engines()
    for name, engine in engines.items():
        container.register_engine(name, engine)
    container.engines = engines
    app.state.container = container
    logger.info("MESAN Ω v%s READY | engines=%s", VERSION, list(engines.keys()))
    yield
    logger.info("SHUTDOWN COMPLETE")


app = FastAPI(
    title="MESAN Ω — Distributed Intelligence Platform",
    version=VERSION,
    lifespan=lifespan
)

app.middleware("http")(context_middleware)
app.middleware("http")(auth_middleware)

@app.middleware("http")
async def latency_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Latency-Ms"] = str(round((time.time() - start) * 1000, 2))
    return response

allow_origins = (
    ["https://mesanomega.com", "https://www.mesanomega.com"]
    if ENV == "production" else ["*"]
)

app.add_middleware(CORSMiddleware, allow_origins=allow_origins, allow_methods=["*"], allow_headers=["*"])

app.include_router(execution_router, tags=["Diagnóstico"])
app.include_router(leads_router, prefix="/api/leads", tags=["Leads"])
app.include_router(payment_router, prefix="/pro", tags=["Pagos"])

@app.get("/health")
def health():
    return {"status": "OK", "version": VERSION, "env": ENV}

@app.get("/engines")
def engines(request: Request):
    c = request.app.state.container
    engines = getattr(c, "engines", None) or {}
    return {"engines": {name: getattr(engine, "version", "unknown") for name, engine in engines.items()}}

@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    logger.exception("SYSTEM FAILURE")
    return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR", "message": "MESAN internal failure"})
