# pro/pagos.py -- MESAN Omega Pagos v1.2
import stripe
import os
import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@router.post("/pro/crear-sesion")
async def crear_sesion_pago(data: dict):
    try:
        monto  = max(299, int(data.get("monto", 799)))
        cliente_id = str(data.get("cliente_id", "tenant_1"))
        indice = str(data.get("indice", 0))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {
                        "name": "MESAN CEO Report"
                    },
                    "unit_amount": int(monto * 100),
                },
                "quantity": 1,
            }],
            success_url="https://mesanomega.com/demo_enterprise.html?pago=exitoso",
            cancel_url="https://mesanomega.com/demo_enterprise.html?pago=cancelado",
            metadata={
                "cliente_id": cliente_id,
                "indice": indice
            }
        )

        return {"url": session.url}

    except Exception as e:
        logging.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=500, detail="Stripe session error")


@router.post("/pro/webhook-stripe")
async def webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            os.getenv("STRIPE_WEBHOOK_SECRET", "")
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook invalido")

    if event["type"] == "checkout.session.completed":
        session    = event["data"]["object"]
        cliente_id = session["metadata"].get("cliente_id")
        logging.info(f"Pago completado: {cliente_id}")
        activar_cliente(cliente_id)

    return {"status": "ok"}


def activar_cliente(cliente_id: str):
    try:
        from database import SessionLocal
        from models import Lead
        db   = SessionLocal()
        lead = db.query(Lead).filter(Lead.id == cliente_id).first()
        if lead:
            lead.estatus = "pagado"
            db.commit()
            logging.info(f"Lead {cliente_id} marcado como pagado")
        db.close()
    except Exception as e:
        logging.error(f"Error activando cliente: {str(e)}")


def puede_ver_pdf(lead: dict) -> bool:
    if not lead.get("pagado"):
        return False
    expiracion = lead.get("fecha_expiracion")
    if expiracion and expiracion < datetime.utcnow():
        return False
    return True
