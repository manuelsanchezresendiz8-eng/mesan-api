# routes/guardian_routes.py -- MESAN Omega Guardian Routes v2.0
"""
Endpoints de Guardian Omega v2.
Toda la logica vive en core/jarvis/guardian_engine.py.
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse

from core.jarvis.guardian_engine import guardian_engine
from core.jarvis.telemetry_engine import telemetry_engine
from core.jarvis.self_healing_engine import self_healing_engine
from core.jarvis.autonomous_orchestrator import autonomous_orchestrator
from core.jarvis.guardian_integration import guardian_integration
from core.jarvis.guardian_scheduler import guardian_scheduler
from core.jarvis.predictive_analytics import predictive_engine
from core.jarvis.executive_reporting import executive_reporter
from core.jarvis.notification_center import notification_center
from core.jarvis.guardian_ai_advisor import guardian_advisor
from core.jarvis.control_plane import control_plane
from core.jarvis.event_bus import event_bus

GUARDIAN_BASE = Path(__file__).resolve().parent.parent

router = APIRouter()
logger = logging.getLogger("mesan.guardian.routes")


@router.get("/guardian/dashboard")
async def guardian_dashboard():
    """Dashboard visual Guardian Omega."""
    return FileResponse(GUARDIAN_BASE / "guardian_dashboard.html")


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


@router.get("/guardian/telemetry")
async def guardian_telemetry(request: Request):
    """Metricas de telemetria en tiempo real."""
    try:
        return telemetry_engine.build_metrics()
    except Exception as e:
        logger.exception("[GUARDIAN] telemetry failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/self-healing")
async def guardian_self_healing(request: Request):
    """Motor de auto-recuperacion."""
    try:
        self_healing_engine.analyze()
        return self_healing_engine.generate_report()
    except Exception as e:
        logger.exception("[GUARDIAN] self-healing failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/orchestrator")
async def guardian_orchestrator(request: Request):
    """Orquestador autonomo."""
    try:
        return autonomous_orchestrator.evaluate()
    except Exception as e:
        logger.exception("[GUARDIAN] orchestrator failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/orchestrator/report")
async def guardian_orchestrator_report(request: Request):
    """Reporte ejecutivo del orquestador."""
    try:
        return autonomous_orchestrator.build_report()
    except Exception as e:
        logger.exception("[GUARDIAN] orchestrator report failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/dashboard/state")
async def guardian_dashboard_state(request: Request):
    """Estado consolidado - una sola llamada."""
    try:
        return guardian_integration.get_state()
    except Exception as e:
        logger.exception("[GUARDIAN] dashboard state failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/events")
async def guardian_events(request: Request):
    """Bus de eventos."""
    try:
        return event_bus.get_queue()
    except Exception as e:
        logger.exception("[GUARDIAN] events failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/scheduler")
async def guardian_scheduler_status(request: Request):
    try: return guardian_scheduler.health_check()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/predictive-analytics")
async def guardian_predictive_analytics(request: Request):
    try: return predictive_engine.analyze()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/executive-report")
async def guardian_executive_report(request: Request):
    try: return executive_reporter.generate()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/notifications")
async def guardian_notifications(request: Request):
    try: return notification_center.get_status()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/advisor")
async def guardian_advisor_endpoint(request: Request):
    q = request.query_params.get("q", "estado general")
    try: return guardian_advisor.ask(q)
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/guardian/control-plane")
async def guardian_control_plane(request: Request):
    try: return control_plane.get_state()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})


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