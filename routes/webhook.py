import os
import stripe
import logging
from fastapi import APIRouter, Request, HTTPException
from database import SessionLocal
from models import Lead

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):

    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig,
            os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook invalido")

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]
        email = session.get("customer_email")
        lead_id = session.get("metadata", {}).get("lead_id")

        if email:
            try:
                db = SessionLocal()
                lead = db.query(Lead).filter(Lead.email == email).first()
                if lead:
                    lead.estatus = "pagado"
                    db.commit()
                    logging.info(f"Lead actualizado a pagado: {email}")
                db.close()
            except Exception as e:
                logging.error(f"Error actualizando lead: {e}")

    return {"ok": True}
