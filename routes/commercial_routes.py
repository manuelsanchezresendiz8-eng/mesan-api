# routes/commercial_routes.py -- MESAN Omega Commercial Routes v1.0
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.jarvis.commercial.commercial_orchestrator import commercial_orchestrator
from core.jarvis.commercial.lead_scoring import lead_scoring
from core.jarvis.commercial.sales_pipeline import sales_pipeline
from core.jarvis.commercial.commercial_metrics import commercial_metrics
from core.jarvis.commercial.followup_engine import followup_engine
from core.jarvis.commercial.proposal_generator import proposal_generator

router = APIRouter()
logger = logging.getLogger("mesan.commercial.routes")

@router.get("/commercial/dashboard")
async def commercial_dashboard(request: Request):
    try: return commercial_orchestrator.get_dashboard()
    except Exception as e:
        logger.exception("[Commercial] dashboard failed")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/commercial/pipeline")
async def commercial_pipeline(request: Request):
    try: return sales_pipeline.get_pipeline()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/commercial/leads")
async def commercial_leads(request: Request):
    try: return {"leads": sales_pipeline._fetch_leads()[:50]}
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/commercial/hot")
async def commercial_hot(request: Request):
    try: return {"hot_leads": commercial_orchestrator.get_hot_leads()}
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/commercial/metrics")
async def commercial_metrics_endpoint(request: Request):
    try: return commercial_metrics.calculate()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/commercial/forecast")
async def commercial_forecast(request: Request):
    try: return commercial_orchestrator.get_forecast()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/commercial/proposals")
async def commercial_proposals(request: Request):
    try: return {"proposals": proposal_generator.get_proposals()}
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/commercial/followups")
async def commercial_followups(request: Request):
    try: return followup_engine.get_stats()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/commercial/process-lead")
async def commercial_process_lead(request: Request):
    try:
        body = await request.json()
        return commercial_orchestrator.process_lead(body.get("lead", {}), body.get("omega_result"))
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})