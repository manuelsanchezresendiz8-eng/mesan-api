# routes/smtp_routes.py -- MESAN Omega SMTP v1.0
import os,logging,smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime,timezone
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
router=APIRouter()
logger=logging.getLogger("mesan.smtp")

def _send(to,subject,html):
    host=os.getenv("EMAIL_SMTP","");port=int(os.getenv("EMAIL_PORT","587"));user=os.getenv("EMAIL_DESTINO","");pwd=os.getenv("EMAIL_PASS","")
    if not all([host,user,pwd]):return{"status":"NOT_CONFIGURED"}
    try:
        msg=MIMEMultipart("alternative");msg["Subject"]=subject;msg["From"]=user;msg["To"]=to
        msg.attach(MIMEText(html,"html"))
        with smtplib.SMTP(host,port) as s:
            s.starttls();s.login(user,pwd);s.sendmail(user,to,msg.as_string())
        return{"status":"SENT","to":to,"subject":subject}
    except Exception as e:
        logger.error("[SMTP] %s",e);return{"status":"ERROR","error":str(e)}

@router.post("/smtp/send")
async def smtp_send(request:Request):
    try:
        body=await request.json()
        return _send(body.get("to",""),body.get("subject","MESAN Omega"),body.get("html",""))
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.post("/smtp/welcome")
async def smtp_welcome(request:Request):
    try:
        body=await request.json()
        to=body.get("to","");nombre=body.get("nombre","")
        html="<h2>Bienvenido a MESAN Omega, {}</h2><p>Su diagnostico ejecutivo esta siendo procesado. Recibira los resultados en breve.</p><p>Equipo MESAN Omega</p>".format(nombre)
        return _send(to,"Bienvenido a MESAN Omega",html)
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.post("/smtp/proposal")
async def smtp_proposal(request:Request):
    try:
        body=await request.json()
        to=body.get("to","");empresa=body.get("empresa","");score=body.get("score",0);nivel=body.get("nivel","")
        html="<h2>Propuesta Ejecutiva - {}</h2><p>Score Omega: <strong>{}</strong></p><p>Nivel: <strong>{}</strong></p><p>Solicite una revision ejecutiva con nuestro equipo.</p><p>Equipo MESAN Omega</p>".format(empresa,score,nivel)
        return _send(to,"Propuesta Ejecutiva MESAN Omega - {}".format(empresa),html)
    except Exception as e:return JSONResponse(status_code=500,content={"error":str(e)})

@router.get("/smtp/status")
async def smtp_status(request:Request):
    configured=bool(os.getenv("EMAIL_SMTP")) and bool(os.getenv("EMAIL_PASS"))
    return{"status":"CONFIGURED" if configured else "NOT_CONFIGURED"}