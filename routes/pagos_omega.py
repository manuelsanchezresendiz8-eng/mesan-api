import stripe
import os
import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@router.post("/crear-sesion-omega")
async def crear_sesion_pago(data: dict):
    try:
        monto = data.get("monto", 299)
        cliente_id = data.get("cliente_id", "anonimo")
        indice = data.get("indice", 0)

        monto = max(299, int(monto))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {
                        "name": "Intervencion MESAN Omega",
                        "description": f"Nivel de riesgo: {indice}"
                    },
                    "unit_amount": int(monto * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://mesanomega.com/exito",
            cancel_url="https://mesanomega.com",
            metadata={
                "cliente_id": str(cliente_id),
                "indice": str(indice)
            }
        )

        return {"url": session.url}

    except Exception as e:
        logging.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook-stripe")
async def webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook invalido")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        cliente_id = session["metadata"].get("cliente_id")
        logging.info(f"Pago completado: {cliente_id}")
        activar_cliente(cliente_id)

    return {"status": "ok"}


def activar_cliente(cliente_id: str):
    try:
        from database import SessionLocal
        from models import Lead
        db = SessionLocal()
        lead = db.query(Lead).filter(Lead.id == cliente_id).first()
        if lead:
            lead.estatus = "pagado"
            db.commit()
            logging.info(f"Lead {cliente_id} marcado como pagado")
        db.close()
    except Exception as e:
        logging.error(f"Error activando cliente: {e}")


def puede_ver_pdf(lead: dict) -> bool:
    if not lead.get("pagado"):
        return False
    expiracion = lead.get("fecha_expiracion")
    if expiracion and expiracion < datetime.utcnow():
        return False
    return True
