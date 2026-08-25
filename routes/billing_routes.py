# routes/billing_routes.py -- MESAN Omega Billing v1.0
import os,logging
from datetime import datetime,timezone
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse,RedirectResponse
router=APIRouter()
logger=logging.getLogger("mesan.billing")

@router.post("/billing/checkout")
async def create_checkout(request:Request):
    try:
        import stripe
        stripe.api_key=os.getenv("STRIPE_SECRET_KEY","")
        if not stripe.api_key:return JSONResponse(status_code=500,content={"error":"STRIPE_NOT_CONFIGURED"})
        body=await request.json()
        empresa=body.get("empresa","")
        correo=body.get("correo","")
        score=body.get("score",0)
        nivel=body.get("nivel","")
        session=stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price_data":{"currency":"mxn","product_data":{"name":"Diagnostico Ejecutivo MESAN Omega","description":"Evaluacion completa de riesgo empresarial con PDF CEO"},"unit_amount":29900},"quantity":1}],
            mode="payment",
            success_url=os.getenv("DOMINIO","https://mesanomega.com")+"/diagnostico-exitoso?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.getenv("DOMINIO","https://mesanomega.com")+"/#diagnostico",
            customer_email=correo,
            metadata={"empresa":empresa,"score":str(score),"nivel":nivel}
        )
        return{"url":session.url,"session_id":session.id}
    except Exception as e:
        logger.error("[BILLING] %s",e)
        return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/billing/status")
async def billing_status(request:Request):
    configured=bool(os.getenv("STRIPE_SECRET_KEY"))
    return{"status":"CONFIGURED" if configured else "NOT_CONFIGURED"}

@router.get("/diagnostico-exitoso")
async def diagnostico_exitoso(request:Request):
    session_id=request.query_params.get("session_id","")
    html="<html><head><meta charset='utf-8'><title>Pago Exitoso</title></head><body style='background:#060B18;color:#E2E8F0;font-family:Inter,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;'><div style='text-align:center;max-width:500px;padding:40px;'><div style='font-size:64px;margin-bottom:24px;'>✅</div><h1 style='color:#00E5A0;margin-bottom:16px;'>Pago Recibido</h1><p style='font-size:18px;margin-bottom:24px;'>Tu Diagnostico Ejecutivo MESAN Omega esta siendo procesado.</p><p style='color:#64748B;'>Recibiras tu reporte PDF en las proximas 24 horas al correo registrado.</p><a href='/' style='display:inline-block;margin-top:32px;padding:12px 24px;background:linear-gradient(135deg,#00E5A0,#00C98D);color:#060B18;font-weight:700;border-radius:8px;text-decoration:none;'>Volver al inicio</a></div></body></html>"
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)