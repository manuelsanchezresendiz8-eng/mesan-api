import logging
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse

router = APIRouter()
logger = logging.getLogger("mesan.guardian.routes")
GUARDIAN_BASE = Path(__file__).resolve().parent.parent

@router.get("/guardian/dashboard")
async def guardian_dashboard(request: Request):
    return FileResponse(GUARDIAN_BASE / "guardian_dashboard.html")

@router.get("/guardian/status")
async def guardian_status(request: Request):
    try:
        from core.jarvis.guardian_engine import guardian_engine
        report = guardian_engine.execute()
        result = {"timestamp": datetime.now(timezone.utc).isoformat(), "overall_score": report.overall_score, "status": report.status}
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/health")
async def guardian_health(request: Request):
    try:
        from core.jarvis.guardian_engine import guardian_engine
        r = guardian_engine.execute()
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "overall_score": r.overall_score, "status": r.status}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/incidents")
async def guardian_incidents(request: Request):
    try:
        from core.jarvis.guardian_engine import guardian_engine
        r = guardian_engine.execute()
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "total": len(r.incidents), "incidents": r.incidents, "alerts": r.alerts}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/telemetry")
async def guardian_telemetry(request: Request):
    try:
        from core.jarvis.telemetry_engine import telemetry_engine
        return telemetry_engine.build_metrics()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/self-healing")
async def guardian_self_healing(request: Request):
    try:
        from core.jarvis.self_healing_engine import self_healing_engine
        self_healing_engine.analyze()
        return self_healing_engine.generate_report()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/orchestrator")
async def guardian_orchestrator(request: Request):
    try:
        from core.jarvis.autonomous_orchestrator import autonomous_orchestrator
        return autonomous_orchestrator.evaluate()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/dashboard/state")
async def guardian_dashboard_state(request: Request):
    try:
        from core.jarvis.guardian_integration import guardian_integration
        return guardian_integration.get_state()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/events")
async def guardian_events(request: Request):
    try:
        from core.jarvis.event_bus import event_bus
        return event_bus.get_queue()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/scheduler")
async def guardian_scheduler_status(request: Request):
    try:
        from core.jarvis.guardian_scheduler import guardian_scheduler
        return guardian_scheduler.health_check()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/predictive-analytics")
async def guardian_predictive_analytics(request: Request):
    try:
        from core.jarvis.predictive_analytics import predictive_engine
        return predictive_engine.analyze()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/executive-report")
async def guardian_executive_report(request: Request):
    try:
        from core.jarvis.executive_reporting import executive_reporter
        return executive_reporter.generate()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/notifications")
async def guardian_notifications(request: Request):
    try:
        from core.jarvis.notification_center import notification_center
        return notification_center.get_status()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/advisor")
async def guardian_advisor_endpoint(request: Request):
    try:
        from core.jarvis.guardian_ai_advisor import guardian_advisor
        q = request.query_params.get("q", "estado general")
        return guardian_advisor.ask(q)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/control-plane")
async def guardian_control_plane(request: Request):
    try:
        from core.jarvis.control_plane import control_plane
        return control_plane.get_state()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/security")
async def guardian_security(request: Request):
    try:
        from core.jarvis.guardian_engine import guardian_engine
        r = guardian_engine.execute()
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "services": [], "alerts": [a for a in r.alerts if a.get("severity") in ("CRITICAL","HIGH")]}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/predictive")
async def guardian_predictive(request: Request):
    try:
        from core.jarvis.guardian_engine import guardian_engine
        r = guardian_engine.execute()
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "overall_score": r.overall_score, "status": r.status, "signals": r.alerts}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/guardian/orchestrator/report")
async def guardian_orchestrator_report(request: Request):
    try:
        from core.jarvis.autonomous_orchestrator import autonomous_orchestrator
        return autonomous_orchestrator.build_report()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/guardian/scheduler/start")
async def guardian_scheduler_start(request: Request):
    try:
        from core.jarvis.guardian_scheduler import guardian_scheduler
        return guardian_scheduler.start()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/guardian/scheduler/stop")
async def guardian_scheduler_stop(request: Request):
    try:
        from core.jarvis.guardian_scheduler import guardian_scheduler
        return guardian_scheduler.stop()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/guardian/advisor")
async def guardian_advisor_post(request: Request):
    try:
        from core.jarvis.guardian_ai_advisor import guardian_advisor
        body = await request.json()
        return guardian_advisor.ask(body.get("question", "estado general"))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})