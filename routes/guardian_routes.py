# routes/guardian_routes.py -- MESAN Omega Guardian Routes v2.0
"""
Endpoints de Guardian Omega v2.
Toda la logica vive en core/jarvis/guardian_engine.py.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.jarvis.guardian_engine import guardian_engine

router = APIRouter()
logger = logging.getLogger("mesan.guardian.routes")


def _serialize(obj):
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialize(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


@router.get("/guardian/status")
async def guardian_status(request: Request):
    """Estado completo del sistema."""
    try:
        return _serialize(guardian_engine.execute())
    except Exception as e:
        logger.exception("[GUARDIAN] status failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/health")
async def guardian_health(request: Request):
    """Health Score del sistema."""
    try:
        report = guardian_engine.execute()
        return {
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "overall_score": report.overall_score,
            "status":        report.status,
            "services":      [_serialize(s) for s in report.services],
        }
    except Exception as e:
        logger.exception("[GUARDIAN] health failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/incidents")
async def guardian_incidents(request: Request):
    """Incidentes activos."""
    try:
        report = guardian_engine.execute()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total":     len(report.incidents),
            "incidents": report.incidents,
            "alerts":    report.alerts,
        }
    except Exception as e:
        logger.exception("[GUARDIAN] incidents failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/security")
async def guardian_security(request: Request):
    """Reporte de seguridad."""
    try:
        report = guardian_engine.execute()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services":  [_serialize(s) for s in report.services
                         if "security" in s.service.lower() or "env" in s.service.lower()],
            "alerts":    [a for a in report.alerts if a.get("severity") in ("CRITICAL","HIGH")],
        }
    except Exception as e:
        logger.exception("[GUARDIAN] security failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/predictive")
async def guardian_predictive(request: Request):
    """Senales predictivas."""
    try:
        report = guardian_engine.execute()
        return {
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "overall_score": report.overall_score,
            "status":        report.status,
            "signals":       report.alerts,
        }
    except Exception as e:
        logger.exception("[GUARDIAN] predictive failed")
        return JSONResponse(status_code=500, content={"error": str(e)})