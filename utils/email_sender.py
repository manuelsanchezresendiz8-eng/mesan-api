import os
import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.titan.email")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO", "")

def enviar_notificacion_lead(nombre, email_cliente, telefono, score, clasificacion, soluciones):
    if not SMTP_USER or not SMTP_PASS:
        logging.warning("SMTP no configurado")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Nuevo Lead MESAN-Omega — {clasificacion} | Score {score}"
        msg["From"] = SMTP_USER
        msg["To"] = EMAIL_DESTINO

        soluciones_html = "".join(
            f"<li>{s if isinstance(s, str) else s.get('area','') + ' - ' + s.get('accion','')}</li>"
            for s in soluciones
        )

        color = "#ff3b5c" if clasificacion == "ALTO" else "#ffaa00" if clasificacion == "MEDIO" else "#00e5a0"

        html = f"""
        <html><body style="background:#02060a;color:#e2e8f0;font-family:Arial;padding:30px;">
        <div style="max-width:600px;margin:auto;background:#0a1118;padding:30px;border:1px solid rgba(0,243,255,0.15);">
            <h2 style="color:#00f3ff;font-family:monospace;letter-spacing:3px;">MESAN-Ω</h2>
            <p style="color:#64748b;font-size:0.8rem;">NUEVO LEAD CAPTURADO</p>
            <hr style="border-color:rgba(0,243,255,0.1);">
            <p><b>Nombre:</b> {nombre}</p>
            <p><b>Email:</b> {email_cliente}</p>
            <p><b>Teléfono:</b> {telefono}</p>
            <hr style="border-color:rgba(0,243,255,0.1);">
            <p><b>Score:</b> <span style="font-size:1.5rem;color:#00f3ff;">{score}</span></p>
            <p><b>Clasificación:</b> <span style="color:{color};font-weight:700;">{clasificacion}</span></p>
            <p><b>Soluciones:</b></p>
            <ul>{soluciones_html}</ul>
            <hr style="border-color:rgba(0,243,255,0.1);">
            <p style="color:#64748b;font-size:0.75rem;">MESAN-Ω | mesanomega.com</p>
        </div></body></html>
        """
        msg.attach(MIMEText(html, "html"))
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, EMAIL_DESTINO, msg.as_string())
        logging.info(f"Notificacion enviada OK → {EMAIL_DESTINO}")
    except Exception as e:
        logging.error(f"Error notificacion: {e}")

def enviar_reporte_pdf(email_cliente, nombre, pdf_bytes):
    if not SMTP_USER or not SMTP_PASS:
        logging.warning("SMTP no configurado")
        return
    try:
        msg = MIMEMultipart()
        msg["Subject"] = "Tu Reporte de Diagnostico MESAN-Omega"
        msg["From"] = SMTP_USER
        msg["To"] = email_cliente

        cuerpo = MIMEText(
            f"Hola {nombre},\n\n"
            "Adjunto encontraras tu reporte de diagnostico MESAN-Omega.\n\n"
            "Este analisis identifica riesgos y oportunidades en tu operacion.\n\n"
            "Equipo MESAN-Omega\nhttps://mesanomega.com",
            "plain"
        )
        msg.attach(cuerpo)

        adjunto = MIMEApplication(pdf_bytes, Name="Diagnostico_MESAN_Omega.pdf")
        adjunto['Content-Disposition'] = 'attachment; filename="Diagnostico_MESAN_Omega.pdf"'
        msg.attach(adjunto)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, email_cliente, msg.as_string())
        logging.info(f"PDF enviado OK → {email_cliente}")
    except Exception as e:
        logging.error(f"Error enviando PDF: {e}")
