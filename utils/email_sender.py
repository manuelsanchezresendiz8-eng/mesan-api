import os
import ssl
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================
# CONFIG SMTP
# =========================================
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.titan.email")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO", "")


# =========================================
# FUNCIÓN PRINCIPAL
# =========================================
def enviar_notificacion_lead(
    nombre: str,
    email_cliente: str,
    telefono: str,
    score: int,
    clasificacion: str,
    soluciones: list
):
    if not SMTP_USER or not SMTP_PASS:
        logging.warning("Email no configurado — faltan credenciales SMTP")
        return

    try:
        # =========================================
        # CONSTRUIR MENSAJE
        # =========================================
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 Nuevo Lead MESAN-Ω — {clasificacion} | Score {score}"
        msg["From"] = SMTP_USER
        msg["To"] = EMAIL_DESTINO

        soluciones_html = "".join(
            f"<li style='padding:4px 0;'>{s}</li>"
            for s in soluciones
        )

        color_clasificacion = (
            "#ff3b5c" if clasificacion == "ALTO" else
            "#ffaa00" if clasificacion == "MEDIO" else
            "#00e5a0"
        )

        html = f"""
        <html>
        <body style="background:#02060a;color:#e2e8f0;font-family:Arial,sans-serif;padding:30px;">
            <div style="max-width:600px;margin:auto;background:#0a1118;padding:30px;border:1px solid rgba(0,243,255,0.15);">

                <h2 style="font-family:monospace;letter-spacing:3px;color:#00f3ff;">MESAN-Ω</h2>
                <p style="color:#64748b;font-size:0.8rem;letter-spacing:2px;">NUEVO LEAD CAPTURADO</p>

                <hr style="border-color:rgba(0,243,255,0.1);margin:20px 0;">

                <p><b>Nombre:</b> {nombre}</p>
                <p><b>Email:</b> {email_cliente}</p>
                <p><b>Teléfono:</b> {telefono}</p>

                <hr style="border-color:rgba(0,243,255,0.1);margin:20px 0;">

                <p><b>Score:</b> <span style="font-size:1.5rem;font-weight:700;color:#00f3ff;">{score}</span></p>
                <p><b>Clasificación:</b> <span style="color:{color_clasificacion};font-weight:700;">{clasificacion}</span></p>

                <p><b>Soluciones detectadas:</b></p>
                <ul style="padding-left:20px;color:#e2e8f0;">
                    {soluciones_html}
                </ul>

                <hr style="border-color:rgba(0,243,255,0.1);margin:20px 0;">

                <p style="color:#64748b;font-size:0.75rem;">MESAN-Ω | mesanomega.com | Mexicali, B.C.</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        # =========================================
        # ENVIAR SSL/TLS Puerto 465
        # =========================================
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, EMAIL_DESTINO, msg.as_string())

        logging.info(f"Email enviado OK → {EMAIL_DESTINO}")

    except Exception as e:
        logging.error(f"Error enviando email: {e}")
        raise
