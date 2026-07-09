import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.jarvis_sales.lead_engine import lead_engine

router = APIRouter()
logger = logging.getLogger('mesan.jarvis.sales.routes')

@router.get('/jarvis-sales/health')
async def health():
    return {'status':'OK','version':lead_engine.version,'timestamp':datetime.now(timezone.utc).isoformat()}

@router.get('/jarvis-sales/leads')
async def leads():
    try:
        decisions = lead_engine.load_and_rank_from_db()
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'total':len(decisions),'leads':[d.to_dict() for d in decisions]}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/jarvis-sales/priorities')
async def priorities():
    try:
        decisions = lead_engine.load_and_rank_from_db()
        summary = lead_engine.summary(decisions)
        hot  = [d.to_dict() for d in decisions if d.temperature.value == 'HOT']
        warm = [d.to_dict() for d in decisions if d.temperature.value == 'WARM']
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'summary':summary,'hot':hot,'warm':warm}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/jarvis-sales/dashboard')
async def dashboard():
    try:
        decisions = lead_engine.load_and_rank_from_db()
        summary = lead_engine.summary(decisions)
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'summary':summary,'top_5_leads':[d.to_dict() for d in decisions[:5]]}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/jarvis-sales/score/{lead_id}')
async def score(lead_id: str):
    try:
        decisions = lead_engine.load_and_rank_from_db()
        match = next((d for d in decisions if d.lead_id == lead_id), None)
        if not match:
            return JSONResponse(status_code=404, content={'error':f'Lead {lead_id} no encontrado'})
        return match.score.to_dict()
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/jarvis-sales/recommendation/{lead_id}')
async def recommendation(lead_id: str):
    try:
        decisions = lead_engine.load_and_rank_from_db()
        match = next((d for d in decisions if d.lead_id == lead_id), None)
        if not match:
            return JSONResponse(status_code=404, content={'error':f'Lead {lead_id} no encontrado'})
        return match.recommendation.to_dict()
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.post('/jarvis-sales/recalculate')
async def recalculate():
    try:
        decisions = lead_engine.load_and_rank_from_db()
        summary = lead_engine.summary(decisions)
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'recalculated':len(decisions),'summary':summary}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})
