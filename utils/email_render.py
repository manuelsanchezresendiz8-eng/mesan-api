import smtplib
from email.message import EmailMessage
import os

EMAIL_USER = os.getenv("EMAIL_USER", "contacto@mesanomega.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
EMAIL_SMTP = os.getenv("EMAIL_SMTP", "smtp.godaddy.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))

def enviar_notificacion_lead(nombre, email_cliente, telefono, score, clasificacion, soluciones):
    if not EMAIL_PASS:
        print("EMAIL_PASS no configurado")
        return

    # Email al cliente
    msg_cliente = EmailMessage()
    msg_cliente["Subject"] = "Tu Diagnostico MESAN-Omega"
    msg_cliente["From"] = EMAIL_USER
    msg_cliente["To"] = email_cliente

    problemas = "\n".join([f"- {s['area']}: {s['accion']}" for s in soluciones])

    msg_cliente.set_content(f"""
Hola {nombre},

Tu diagnostico MESAN-Omega ha sido generado.

Score de Riesgo: {score}
Clasificacion: {clasificacion}

Areas de atencion detectadas:
{problemas}

Un asesor se pondra en contacto contigo en menos de 1 hora.

MESAN-Omega
contacto@mesanomega.com
""")

    # Email a Manuel (admin)
    msg_admin = EmailMessage()
    msg_admin["Subject"] = f"NUEVO LEAD - {clasificacion} - {nombre}"
    msg_admin["From"] = EMAIL_USER
    msg_admin["To"] = EMAIL_USER

    msg_admin.set_content(f"""
NUEVO LEAD MESAN-OMEGA

Empresa: {nombre}
Telefono: {telefono}
Email: {email_cliente}

Score: {score}
Clasificacion: {clasificacion}

Problemas detectados:
{problemas}

Entra al CRM para ver el detalle completo.
""")

    try:
        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg_cliente)
            server.send_message(msg_admin)
        print(f"Emails enviados para lead: {nombre}")
    except Exception as e:
        print(f"Error enviando email: {e}")
