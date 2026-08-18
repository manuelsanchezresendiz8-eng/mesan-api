# routes/mission_control_routes.py -- MESAN Omega Mission Control v2.0
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse

router = APIRouter()
logger = logging.getLogger("mesan.mission_control")

# Serve Mission Control Dashboard HTML
@router.get("/commercial/mission-control", response_class=HTMLResponse)
async def mission_control_dashboard(request: Request):
    """Serve the Mission Control dashboard."""
    try:
        # Try to load the HTML file
        html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mission_control.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Mission Control HTML not found</h1>", status_code=404)
    except Exception as e:
        logger.error("[MissionControl] Error serving dashboard: %s", e)
        return HTMLResponse(content="<h1>Error loading Mission Control</h1>", status_code=500)


# JSON API endpoint for dashboard data
@router.get("/commercial/mission-control/data")
async def mission_control_data(request: Request):
    """Return Mission Control data as JSON."""
    try:
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0.0",
        }
        data["leads"] = _get_leads()
        data["guardian"] = _get_guardian()
        data["pipeline"] = _get_pipeline()
        data["billing"] = _get_billing()
        data["scheduler"] = _get_scheduler()
        data["system"] = _get_system()
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


def _get_leads():
    try:
        import psycopg
        conn = psycopg.connect(os.getenv("DATABASE_URL"), connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM leads")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM leads WHERE estatus IS NULL OR estatus = 'nuevo'")
        nuevos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM leads WHERE created_at::date = CURRENT_DATE")
        hoy = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"total": total, "nuevos": nuevos, "hoy": hoy, "hot": 0, "warm": 0, "cold": nuevos}
    except Exception as e:
        return {"error": str(e)}


def _get_guardian():
    try:
        from core.jarvis.guardian_integration import guardian_integration
        s = guardian_integration.get_state()
        return {
            "health": s.get("health_score", 0),
            "status": s.get("health_status", "--"),
            "alerts": s.get("alerts_count", 0),
            "incidents": s.get("incidents_count", 0),
        }
    except Exception:
        return {"status": "OFFLINE"}


def _get_pipeline():
    try:
        from core.jarvis.commercial.commercial_metrics import commercial_metrics
        m = commercial_metrics.calculate()
        return {
            "mrr": m.get("mrr", 0),
            "arr": m.get("arr", 0),
            "conversion": m.get("conversion_rate", 0),
            "subscriptions": m.get("active_subscriptions", 0),
        }
    except Exception:
        return {"mrr": 0, "arr": 0}


def _get_billing():
    try:
        from core.billing.subscription_engine import subscription_engine
        m = subscription_engine.get_metrics()
        return {
            "status": "OK",
            "mrr": m.get("mrr_mxn", 0),
            "active": m.get("active_subscriptions", 0),
        }
    except Exception:
        return {"status": "UNAVAILABLE"}


def _get_scheduler():
    try:
        from core.jarvis.commercial.commercial_scheduler import commercial_scheduler
        return commercial_scheduler.health_check()
    except Exception:
        return {"status": "NOT_LOADED"}


def _get_system():
    try:
        from core.jarvis.telemetry_engine import telemetry_engine
        m = telemetry_engine.build_metrics()
        return {
            "health": m.get("health", 0),
            "uptime": m.get("uptime_seconds", 0),
            "requests": m.get("total_requests", 0),
            "errors": m.get("total_errors", 0),
            "db": "OK" if m.get("services") else "UNKNOWN",
            "smtp": "CONFIGURED" if os.getenv("SMTP_HOST") else "NOT_CONFIGURED",
            "stripe": "OK" if os.getenv("STRIPE_SECRET_KEY") else "MISSING",
        }
    except Exception:
        return {"status": "ERROR"}
