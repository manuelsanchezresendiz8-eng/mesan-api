# pro/pagos.py -- MESAN Omega Pagos v2.7.0
import os
import re
import logging
import stripe
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://mesanomega.com")

# Fix: forzar User-Agent ASCII puro
stripe.default_http_client = stripe.HTTPXClient()


def clean_ascii(value):
    if value is None:
        return ""
    return re.sub(r"[^\x00-\x7F]+", "", str(value)).strip()


@router.post("/pro/crear-sesion")
async def crear_sesion_pago(data: dict):
    try:
        monto      = max(299, int(data.get("monto", 799)))
        cliente_id = clean_ascii(data.get("cliente_id", "tenant_1"))
        indice     = clean_ascii(data.get("indice", 0))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {"name": "MESAN CEO Report"},
                    "unit_amount": int(monto * 100),
                },
                "quantity": 1,
            }],
            success_url=f"{BASE_URL}/success.html",
            cancel_url=f"{BASE_URL}/cancel.html",
            metadata={"cliente_id": cliente_id, "indice": indice}
        )

        return {"url": session.url, "ok": True}

    except Exception:
        logging.exception("Stripe session error")
        raise HTTPException(status_code=500, detail="Stripe session error")


@router.post("/pro/webhook-stripe")
async def webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header,
            os.getenv("STRIPE_WEBHOOK_SECRET", "")
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook invalido")

    if event["type"] == "checkout.session.completed":
        session    = event["data"]["object"]
        cliente_id = clean_ascii(session["metadata"].get("cliente_id", ""))
        logging.info(f"Pago completado: {cliente_id}")

    return {"status": "ok"}


@router.post("/pro/checkout")
async def crear_checkout(data: dict):
    try:
        nombre  = clean_ascii(data.get("nombre", "Cliente"))
        email   = clean_ascii(data.get("email", ""))
        lead_id = clean_ascii(data.get("lead_id", ""))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email or None,
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {"name": "MESAN Diagnostico Completo"},
                    "unit_amount": 29900,
                },
                "quantity": 1,
            }],
            success_url=f"{BASE_URL}/success.html",
            cancel_url=f"{BASE_URL}/cancel.html",
            metadata={"lead_id": lead_id, "nombre": nombre}
        )

        return {"url": session.url, "ok": True}

    except Exception:
        logging.exception("Stripe checkout error")
        return {"ok": False, "error": "Stripe checkout error"}
