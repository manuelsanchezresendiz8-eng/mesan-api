# routes/commercial_routes.py -- MESAN Omega Commercial Routes v1.0
import logging
from fastapi import APIRouter,Request,Depends
from fastapi.responses import JSONResponse,FileResponse
from pathlib import Path
from core.auth.basic_auth import verify_crm_credentials
from core.jarvis.commercial.commercial_orchestrator import commercial_orchestrator
from core.jarvis.commercial.lead_scoring import lead_scoring
from core.jarvis.commercial.sales_pipeline import sales_pipeline
from core.jarvis.commercial.commercial_metrics import commercial_metrics
from core.jarvis.commercial.followup_engine import followup_engine
from core.jarvis.commercial.proposal_generator import proposal_generator
from core.jarvis.commercial.commercial_auto import commercial_auto
from core.jarvis.commercial.commercial_scheduler import commercial_scheduler
from core.jarvis.commercial.marketing_engine import marketing_engine
from core.jarvis.commercial.commercial_strategy_engine import strategy_engine
from core.jarvis.commercial.commercial_learning import commercial_learning
COMM_BASE=Path(__file__).resolve().parent.parent
router=APIRouter()
logger=logging.getLogger("mesan.commercial.routes")

@router.get("/commercial/dashboard")
async def comm_dashboard_visual(request:Request,_u:str=Depends(verify_crm_credentials)):
    return FileResponse(COMM_BASE/"commercial_dashboard.html")

@router.get("/commercial/dashboard/data")
async def comm_dashboard_data(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return commercial_orchestrator.get_dashboard()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/pipeline")
async def comm_pipeline(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return sales_pipeline.get_pipeline()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/leads")
async def comm_leads(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return{"leads":sales_pipeline._fetch_leads()[:50]}
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/hot")
async def comm_hot(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return{"hot_leads":commercial_orchestrator.get_hot_leads()}
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/metrics")
async def comm_metrics(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return commercial_metrics.calculate()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/forecast")
async def comm_forecast(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return commercial_orchestrator.get_forecast()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/proposals")
async def comm_proposals(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return{"proposals":proposal_generator.get_proposals()}
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/followups")
async def comm_followups(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return followup_engine.get_stats()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/auto/status")
async def comm_auto(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return commercial_auto.get_status()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/scheduler")
async def comm_scheduler(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return commercial_scheduler.health_check()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/marketing")
async def comm_marketing(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return marketing_engine.get_stats()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/marketing/queue")
async def comm_mkt_queue(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return marketing_engine.get_queue()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/marketing/templates")
async def comm_mkt_templates(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return marketing_engine.get_templates()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.post("/commercial/marketing/generate")
async def comm_mkt_generate(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return marketing_engine.generate_daily_content()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/strategy")
async def comm_strategy(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return strategy_engine.get_latest()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/brief")
async def comm_brief(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return commercial_auto.generate_brief()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/commercial/learning")
async def comm_learning(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return commercial_learning.get_insights()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.post("/commercial/process-lead")
async def comm_process(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:
        body=await request.json()
        return commercial_orchestrator.process_lead(body.get("lead",{}),body.get("omega_result"))
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})