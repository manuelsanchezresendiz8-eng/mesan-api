# routes/webhook.py

import os
import json
import logging
import stripe

from fastapi import APIRouter, Request, HTTPException
from datetime import datetime

router = APIRouter()

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

try:
    from database import SessionLocal
    from models import Lead
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False
    logging.warning("DB no disponible en webhook")


@router.post("/webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not WEBHOOK_SECRET:
        logging.error("STRIPE_WEBHOOK_SECRET no configurado")
        raise HTTPException(status_code=500, detail="Webhook no configurado")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        logging.error("Firma Stripe invalida")
        raise HTTPException(status_code=400, detail="Firma invalida")
    except Exception as e:
        logging.error(f"Error webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # PAGO COMPLETADO
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        cliente_id = session.get("metadata", {}).get("cliente_id")
        email = session.get("customer_email", "")

        logging.info(f"Pago completado: {cliente_id} | {email}")

        if DB_AVAILABLE and cliente_id:
            try:
                db = SessionLocal()
                lead = db.query(Lead).filter(
                    Lead.id == cliente_id
                ).first()

                if lead:
                    lead.estatus = "pagado"
                    lead.fecha_pago = datetime.utcnow()
                    db.commit()
                    logging.info(f"Lead actualizado a pagado: {cliente_id}")

                db.close()
            except Exception as e:
                logging.error(f"Error actualizando lead: {e}")

    # PAGO FALLIDO
    elif event["type"] == "payment_intent.payment_failed":
        logging.warning(f"Pago fallido: {event['data']['object'].get('id')}")

    # SUSCRIPCION CANCELADA
    elif event["type"] == "customer.subscription.deleted":
        logging.info(f"Suscripcion cancelada: {event['data']['object'].get('id')}")

    return {"status": "ok", "type": event["type"]}


@router.get("/webhook/test")
async def webhook_test():
    return {
        "status": "ok",
        "webhook_secret": "configurado" if WEBHOOK_SECRET else "FALTA",
        "db": "disponible" if DB_AVAILABLE else "no disponible"
    }

# v2 — actualizado
