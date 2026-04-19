import os
import urllib.parse
import logging

def safe_get(d, key, default=0):
    return d.get(key) if isinstance(d, dict) else default

def limpiar_telefono(tel):
    import re
    tel = re.sub(r"\D", "", tel or "")
    if not tel.startswith("52"):
        tel = "52" + tel
    return tel

def mensaje_venta(nombre, ceo, rent, sim):
    fuga = safe_get(rent, "fuga_oculta", 0)
    actual = safe_get(sim, "actual", 0)
    mejor = safe_get(sim, "mejor", "actual")
    decision = safe_get(ceo, "decision", "ANALISIS")
    prioridad = safe_get(ceo, "prioridad", "MEDIA")

    return (
        f"Hola {nombre},\n\n"
        f"MESAN Omega detecto lo siguiente:\n\n"
        f"Estado: {decision}\n"
        f"Prioridad: {prioridad}\n\n"
        f"Perdida estimada mensual: ${fuga} MXN\n"
        f"Utilidad actual: ${actual} MXN\n"
        f"Mejor estrategia: {mejor}\n\n"
        f"Podemos corregir esto en dias.\n"
        f"Agenda tu llamada: https://wa.me/526861629643"
    )

def generar_link_whatsapp(tel, msg):
    tel = limpiar_telefono(tel)
    return f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"

def generar_link_pago(precio: float) -> str:
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {
                        "name": "MESAN Omega Diagnostico Completo"
                    },
                    "unit_amount": int(precio * 100)
                },
                "quantity": 1
            }],
            success_url="https://mesanomega.com/gracias",
            cancel_url="https://mesanomega.com"
        )
        return session.url

    except Exception as e:
        logging.error(f"Stripe error: {e}")
        return None
