import smtplib
from email.message import EmailMessage
import os

EMAIL_USER = os.getenv("EMAIL_USER", "manuel@mesanomega.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
EMAIL_SMTP = os.getenv("EMAIL_SMTP", "smtpout.secureserver.net")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))

def enviar_notificacion_lead(nombre, email_cliente, telefono, score, clasificacion, soluciones):
    if not EMAIL_PASS:
        print("EMAIL_PASS no configurado")
        return

    problemas = "\n".join([f"- {s['area']}: {s['accion']}" for s in soluciones])

    msg_cliente = EmailMessage()
    msg_cliente["Subject"] = "Tu Diagnostico MESAN-Omega"
    msg_cliente["From"] = EMAIL_USER
    msg_cliente["To"] = email_cliente
    msg_cliente.set_content(f"""
Hola {nombre},

Tu diagnostico MESAN-Omega ha sido generado.

Score: {score}
Clasificacion: {clasificacion}

Areas detectadas:
{problemas}

Un asesor te contactara en menos de 1 hora.

MESAN-Omega opera como un sistema de deteccion temprana de riesgos.
Por cumplimiento normativo, la ejecucion del plan de accion debe ser
supervisada por su equipo de asesoria legal o contable.

mesanomega.com
""")

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

Problemas:
{problemas}
""")

    try:
        with smtplib.SMTP_SSL(EMAIL_SMTP, EMAIL_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg_cliente)
            server.send_message(msg_admin)
        print(f"Emails enviados: {nombre}")
    except Exception as e:
        print(f"Error email: {e}")
