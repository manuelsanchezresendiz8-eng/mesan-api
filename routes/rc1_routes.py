# routes/rc1_routes.py -- MESAN Omega RC1 Routes
import logging
from fastapi import APIRouter,Request,Depends
from fastapi.responses import JSONResponse
from core.auth.basic_auth import verify_crm_credentials
from core.customer.customer_portal import customer_portal
from core.jarvis.backup_manager import backup_manager
from core.jarvis.audit_trail import audit_trail
from core.demo.demo_mode import demo_mode
from core.offline.sovereign_mode import sovereign_mode
from core.offline.sync_manager import sync_manager
from core.hardening import hardening
from core.jarvis.iot_hub import iot_hub
router=APIRouter()
logger=logging.getLogger("mesan.rc1")

@router.get("/customer")
async def customer_dashboard(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return customer_portal.get_dashboard()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/guardian/backups")
async def guardian_backups(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return backup_manager.get_status()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.post("/guardian/backups/create")
async def guardian_backup_create(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return backup_manager.create_backup()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/guardian/audit")
async def guardian_audit(request:Request,_u:str=Depends(verify_crm_credentials)):
    module=request.query_params.get("module")
    try:return{"entries":audit_trail.query(module=module),"stats":audit_trail.get_stats()}
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/demo")
async def demo_dashboard(request:Request):
    try:return demo_mode.get_dashboard()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/demo/diagnostico")
async def demo_diagnostico(request:Request):
    try:return demo_mode.get_diagnostico()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/demo/guardian")
async def demo_guardian(request:Request):
    try:return demo_mode.get_guardian()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/system/mode")
async def system_mode(request:Request):
    try:return sovereign_mode.get_status()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/system/hardening")
async def system_hardening(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return hardening.full_check()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.post("/system/cleanup")
async def system_cleanup(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return hardening.cleanup_logs()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.post("/guardian/iot/report")
async def iot_report(request:Request):
    try:
        body=await request.json()
        return iot_hub.report(body.get("device_id",""),body.get("device_type",""),body.get("metrics",{}),body.get("location",""))
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/guardian/iot/devices")
async def iot_devices(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return iot_hub.get_devices()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/guardian/iot/events")
async def iot_events(request:Request,_u:str=Depends(verify_crm_credentials)):
    try:return iot_hub.get_events()
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})