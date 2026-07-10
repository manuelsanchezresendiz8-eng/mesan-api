import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.market_intelligence_engine import market_engine

router = APIRouter()
logger = logging.getLogger('mesan.market.routes')

@router.get('/market/health')
async def market_health():
    return market_engine.health()

@router.get('/market/dashboard')
async def market_dashboard():
    try:
        return market_engine.get_dashboard()
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/market/events')
async def market_events():
    try:
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'events':market_engine.get_events()}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/market/alerts')
async def market_alerts():
    try:
        report = market_engine.run()
        alerts = [a.to_dict() for a in report.alerts]
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'total':len(alerts),'alerts':alerts}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/market/regulatory')
async def market_regulatory():
    try:
        from services.regulatory_monitor import regulatory_monitor
        events = regulatory_monitor.scan()
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'total':len(events),'events':[e.to_dict() for e in events]}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/market/economic')
async def market_economic():
    try:
        from services.economic_monitor import economic_monitor
        indicators = economic_monitor.scan()
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'indicators':[i.to_dict() for i in indicators]}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/market/sectors')
async def market_sectors():
    try:
        from services.sector_monitor import sector_monitor
        sectors = sector_monitor.scan()
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'sectors':[s.to_dict() for s in sectors]}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})

@router.get('/market/recommendations')
async def market_recommendations():
    try:
        report = market_engine.run()
        return {'timestamp':datetime.now(timezone.utc).isoformat(),'market_score':report.market_score,'recommendations':report.recommendations}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':str(e)})
