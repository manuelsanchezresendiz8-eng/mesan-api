# routes/jarvis_routes.py -- MESAN Omega JARVIS Routes v1.0
"""
Endpoints del War Room JARVIS Omega.
Toda la logica vive en core/jarvis/jarvis_engine.py.
Este archivo solo enruta y serializa.
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.jarvis.jarvis_engine import jarvis_engine

router = APIRouter()
logger = logging.getLogger("mesan.jarvis.routes")


@router.get("/jarvis/warroom")
async def warroom(request: Request):
    """War Room completo — las 8 preguntas en menos de 60 segundos."""
    try:
        return jarvis_engine.get_warroom()
    except Exception as e:
        logger.exception("[JARVIS] warroom failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/jarvis/kpis")
async def kpis(request: Request):
    """KPIs financieros y comerciales en tiempo real."""
    try:
        return jarvis_engine.get_kpis()
    except Exception as e:
        logger.exception("[JARVIS] kpis failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/jarvis/alerts")
async def alerts(request: Request):
    """Alertas priorizadas por urgencia e impacto."""
    try:
        return jarvis_engine.get_alerts()
    except Exception as e:
        logger.exception("[JARVIS] alerts failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/jarvis/decisions")
async def decisions(request: Request):
    """Decisiones que requieren atencion humana hoy."""
    try:
        return jarvis_engine.get_decisions()
    except Exception as e:
        logger.exception("[JARVIS] decisions failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/jarvis/radar")
async def radar(request: Request):
    """Aliados, leads calientes y oportunidades detectadas."""
    try:
        return jarvis_engine.get_radar()
    except Exception as e:
        logger.exception("[JARVIS] radar failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/jarvis/autonomy")
async def autonomy(request: Request):
    """Nivel de autonomia del sistema segun reglas 80/95/100."""
    try:
        return jarvis_engine.get_autonomy()
    except Exception as e:
        logger.exception("[JARVIS] autonomy failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/jarvis/system")
async def system_status(request: Request):
    """Estado tecnico de infraestructura y motores."""
    try:
        return jarvis_engine.get_system()
    except Exception as e:
        logger.exception("[JARVIS] system failed")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get('/jarvis/dashboard')
async def jarvis_dashboard():
    from fastapi.responses import FileResponse
    return FileResponse('static/jarvis_warroom.html')
