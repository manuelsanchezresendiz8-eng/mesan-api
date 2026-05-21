# pro/pagos.py
import os
import stripe
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/pro", tags=["Pagos"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET")
SUCCESS_URL     = os.getenv("STRIPE_SUCCESS_URL", "https://mesanomega.com/success.html")
CANCEL_URL      = os.getenv("STRIPE_CANCEL_URL",  "https://mesanomega.com")
PRICE_ID        = os.getenv("STRIPE_PRICE_ID",    "price_mesan_pro")


@router.post("/crear-sesion")
async def crear_sesion(data: dict):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": PRICE_ID, "quantity": 1}],
            mode="payment",
            success_url=SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=CANCEL_URL,
            metadata={
                "email":    data.get("email", ""),
                "nombre":   data.get("nombre", ""),
                "telefono": data.get("telefono", "")
            }
        )
        return {"ok": True, "url": session.url, "session_id": session.id}
    except Exception as e:
        logging.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook-stripe")
async def webhook_stripe(request: Request):
    payload   = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma invalida")

    if event["type"] == "checkout.session.completed":
        session  = event["data"]["object"]
        metadata = session.get("metadata", {})
        email    = metadata.get("email")
        logging.info(f"Pago completado: {email} | {session['id']}")
        # Aqui activar acceso PRO en base de datos

    return JSONResponse({"ok": True})
  
