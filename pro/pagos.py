# pro/pagos.py — MESAN Ω v2.5.0

import os
import logging
import stripe
from fastapi import APIRouter

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://mesanomega.com")


@router.post("/pro/checkout")
async def crear_checkout(data: dict):
    try:
        nombre = data.get("nombre", "Cliente")
        email = data.get("email", "")
        lead_id = data.get("lead_id", "")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email or None,
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {"name": "MESAN Omega — Diagnostico Completo"},
                    "unit_amount": 29900,  # $299 MXN en centavos
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{BASE_URL}/success.html?id={lead_id}",
            cancel_url=f"{BASE_URL}/diagnostico.html",
            metadata={
                "lead_id": lead_id,
                "nombre": nombre
            }
        )

        return {"url": session.url, "ok": True}

    except Exception as e:
        logging.error(f"Error Stripe checkout: {e}")
        return {"error": "No se pudo crear la sesion de pago", "ok": False}
