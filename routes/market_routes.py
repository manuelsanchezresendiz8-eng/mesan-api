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

@router.get('/market/regulatory/alerts/{tenant_id}')
async def market_regulatory_alerts(
    tenant_id: str,
    isr_retenido: float = 0,
    iva: float = 0,
    nomina: float = 0,
    trabajadores: int = 0,
    trabajadores_sin_imss: int = 0,
    repse_suspendido: bool = False,
    bloqueo_bancario: bool = False,
    sector: str = '',
    solo_cambios: bool = False,
):
    """Phase 2 -- Alertas regulatorias PERSONALIZADAS por perfil del tenant.

    El perfil se pasa por query params (mismos campos que /execute); las reglas
    de los rulesets curados (config/regulations) se cruzan con ese perfil.
    Con MESAN_{REG}_PREVIOUS configurado, incluye alertas NUEVO/ACTUALIZADO.
    Flag MESAN_P2_REGULATORY apagado -> respuesta vacia con enabled=false.
    """
    try:
        from core.integration.phase2_bridge import get_regulatory
        bridge = get_regulatory()
        perfil = {
            'tenant_id': tenant_id,
            'isr_retenido': isr_retenido,
            'iva': iva,
            'nomina': nomina,
            'trabajadores': trabajadores,
            'trabajadores_sin_imss': trabajadores_sin_imss,
            'repse_suspendido': repse_suspendido,
            'bloqueo_bancario': bloqueo_bancario,
        }
        alerts = bridge.get_alerts(perfil, solo_cambios=solo_cambios) or []
        summary = bridge.market_summary(perfil, sector=sector) if bridge.active else None
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tenant_id': tenant_id,
            'enabled': bridge.active,
            'total': len(alerts),
            'cambios': sum(1 for a in alerts if a.get('tipo') in ('NUEVO', 'ACTUALIZADO')),
            'alerts': alerts,
            'summary': summary,
        }
    except Exception as e:
        logger.exception('[MARKET] regulatory alerts failed tenant=%s', tenant_id)
        return JSONResponse(status_code=500, content={'error': str(e)})

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