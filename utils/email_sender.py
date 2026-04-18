import os
import json
import urllib.request

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO", "contacto@mesanomega.com")

def _send_email(to: str, subject: str, html: str):
    if not RESEND_API_KEY:
        print("RESEND_API_KEY no configurado")
        return False
    try:
        payload = json.dumps({
            "from": "MESAN Omega <contacto@mesanomega.com>",
            "to": [to],
            "subject": subject,
            "html": html
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
            print(f"Email enviado OK → {to} | status: {res.status}")
            return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False


def enviar_notificacion_lead(nombre, email_cliente, telefono, score, clasificacion, soluciones):
    soluciones_html = "".join(
        f"<li>{s if isinstance(s, str) else s.get('area','') + ' - ' + s.get('accion','')}</li>"
        for s in soluciones
    )
    color = "#ff3b5c" if clasificacion == "ALTO" else "#ffaa00" if clasificacion == "MEDIO" else "#00e5a0"

    html = f"""
    <html><body style="background:#02060a;color:#e2e8f0;font-family:Arial;padding:30px;">
    <div style="max-width:600px;margin:auto;background:#0a1118;padding:30px;border:1px solid rgba(0,243,255,0.15);">
        <h2 style="color:#00f3ff;font-family:monospace;letter-spacing:3px;">MESAN Omega</h2>
        <p style="color:#64748b;font-size:0.8rem;">NUEVO LEAD CAPTURADO</p>
        <hr style="border-color:rgba(0,243,255,0.1);">
        <p><b>Nombre:</b> {nombre}</p>
        <p><b>Email:</b> {email_cliente}</p>
        <p><b>Telefono:</b> {telefono}</p>
        <hr style="border-color:rgba(0,243,255,0.1);">
        <p><b>Score:</b> <span style="font-size:1.5rem;color:#00f3ff;">{score}</span></p>
        <p><b>Clasificacion:</b> <span style="color:{color};font-weight:700;">{clasificacion}</span></p>
        <p><b>Soluciones:</b></p>
        <ul>{soluciones_html}</ul>
        <hr style="border-color:rgba(0,243,255,0.1);">
        <p style="color:#64748b;font-size:0.75rem;">MESAN Omega | mesanomega.com</p>
    </div></body></html>
    """
    _send_email(
        to=EMAIL_DESTINO,
        subject=f"Nuevo Lead MESAN Omega — {clasificacion} | Score {score}",
        html=html
    )


def enviar_reporte_pdf(email_cliente, nombre, pdf_bytes):
    html = f"""
    <html><body style="font-family:Arial;padding:30px;">
    <h2>Hola {nombre},</h2>
    <p>Gracias por usar MESAN Omega. Tu reporte de diagnostico ha sido generado.</p>
    <p>Nuestro equipo revisara tu caso y te contactara en breve.</p>
    <br>
    <p>Equipo MESAN Omega<br>
    <a href="https://mesanomega.com">mesanomega.com</a></p>
    </body></html>
    """
    _send_email(
        to=email_cliente,
        subject="Tu Reporte de Diagnostico MESAN Omega",
        html=html
    )
