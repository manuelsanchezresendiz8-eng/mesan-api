# pro/pagos.py -- MESAN Omega Pagos v3.0.0
# Sin Stripe SDK — llamada directa a API con httpx
import os
import re
import logging
import httpx
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

BASE_URL    = os.getenv("BASE_URL", "https://mesanomega.com")
STRIPE_KEY  = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SEC = os.getenv("STRIPE_WEBHOOK_SECRET", "")


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

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                auth=(STRIPE_KEY, ""),
                data={
                    "payment_method_types[]": "card",
                    "mode": "payment",
                    "line_items[0][price_data][currency]": "mxn",
                    "line_items[0][price_data][product_data][name]": "MESAN CEO Report",
                    "line_items[0][price_data][unit_amount]": str(int(monto * 100)),
                    "line_items[0][quantity]": "1",
                    "success_url": f"{BASE_URL}/success.html",
                    "cancel_url": f"{BASE_URL}/cancel.html",
                    "metadata[cliente_id]": cliente_id,
                    "metadata[indice]": indice,
                }
            )

        result = response.json()

        if response.status_code == 200:
            return {"url": result["url"], "ok": True}
        else:
            msg = result.get("error", {}).get("message", "Stripe error")
            logging.error(f"Stripe error: {msg}")
            raise HTTPException(status_code=500, detail="Stripe session error")

    except HTTPException:
        raise
    except Exception:
        logging.exception("Stripe session error")
        raise HTTPException(status_code=500, detail="Stripe session error")


@router.post("/pro/checkout")
async def crear_checkout(data: dict):
    try:
        nombre  = clean_ascii(data.get("nombre", "Cliente"))
        email   = clean_ascii(data.get("email", ""))
        lead_id = clean_ascii(data.get("lead_id", ""))

        form_data = {
            "payment_method_types[]": "card",
            "mode": "payment",
            "line_items[0][price_data][currency]": "mxn",
            "line_items[0][price_data][product_data][name]": "MESAN Diagnostico Completo",
            "line_items[0][price_data][unit_amount]": "99900",
            "line_items[0][quantity]": "1",
            "success_url": f"{BASE_URL}/success.html",
            "cancel_url": f"{BASE_URL}/cancel.html",
            "metadata[lead_id]": lead_id,
            "metadata[nombre]": nombre,
        }

        if email:
            form_data["customer_email"] = email

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                auth=(STRIPE_KEY, ""),
                data=form_data
            )

        result = response.json()

        if response.status_code == 200:
            return {"url": result["url"], "ok": True}
        else:
            return {"ok": False, "error": "Stripe checkout error"}

    except Exception:
        logging.exception("Stripe checkout error")
        return {"ok": False, "error": "Stripe checkout error"}


@router.post("/pro/webhook-stripe")
async def webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if WEBHOOK_SEC:
        try:
            import stripe
            stripe.api_key = STRIPE_KEY
            event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SEC)
            if event["type"] == "checkout.session.completed":
                session    = event["data"]["object"]
                cliente_id = clean_ascii(session["metadata"].get("cliente_id", ""))
                logging.info(f"Pago completado: {cliente_id}")
        except Exception:
            raise HTTPException(status_code=400, detail="Webhook invalido")

    return {"status": "ok"}
