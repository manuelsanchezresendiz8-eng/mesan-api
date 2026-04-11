import os
import sys
import uuid
import logging
import traceback
import threading
from datetime import datetime

from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from database import init_db
from limiter import limiter

from routes.evaluar import router as evaluar_router
from routes.verificar import router as verificar_router

# =========================================
# CONFIG
# =========================================
VERSION = "2.2.0"

logging.basicConfig(level=logging.INFO)

# =========================================
# IMPORTS SEGUROS
# =========================================
try:
    from enterprise.enterprise_engine import sistema_enterprise
    logging.info("enterprise_engine OK")
except Exception as e:
    logging.critical(f"ERROR enterprise_engine: {e}")
    sistema_enterprise = None

try:
    from utils.email_sender import enviar_notificacion_lead, enviar_reporte_pdf
    logging.info("email_sender OK")
except Exception as e:
    logging.error(f"ERROR email_sender: {e}")
    enviar_notificacion_lead = None
    enviar_reporte_pdf = None

try:
    from utils.pdf_generator import generar_diagnostico_pdf
    logging.info("pdf_generator OK")
except Exception as e:
    logging.error(f"ERROR pdf_generator: {e}")
    generar_diagnostico_pdf = None

# =========================================
# VALIDACIÓN ENV
# =========================================
if not os.environ.get("MESAN_API_KEY"):
    logging.critical("Falta MESAN_API_KEY")
    sys.exit(1)

# =========================================
# INIT
# =========================================
init_db()

app = FastAPI(title="MESAN API", version=VERSION)

# =========================================
# CORS
# =========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # evitar errores en GitHub Pages / dominio
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================================
# RATE LIMIT
# =========================================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# =========================================
# ROUTERS
# =========================================
app.include_router(evaluar_router, prefix="/api")
app.include_router(verificar_router, prefix="/api")

# =========================================
# STORAGE TEMP
# =========================================
leads_db = []
logging.warning("Leads en memoria (no persistente)")

# =========================================
# HELPERS
# =========================================
def response(data, status=200):
    return JSONResponse(
        status_code=status,
        content=data,
        headers={"X-MESAN-VERSION": VERSION}
    )

# =========================================
# ROOT / HEALTH
# =========================================
@app.get("/")
@app.head("/")
async def root():
    return response({"status": "MESAN-Ω API activa", "version": VERSION})

@app.get("/health")
@app.head("/health")
async def health():
    return response({"status": "ok", "version": VERSION})

# =========================================
# PREFLIGHT
# =========================================
@app.options("/enterprise")
def preflight():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# =========================================
# ENDPOINT PRINCIPAL
# =========================================
if sistema_enterprise:

    @app.post("/enterprise")
    @limiter.limit("10/minute")
    async def enterprise(data: dict, request: Request):

        # VALIDACIÓN BÁSICA
        if not isinstance(data, dict):
            return response({"error": "Formato inválido"}, 400)

        # EJECUCIÓN MOTOR
        try:
            resultado = sistema_enterprise(data)
        except Exception:
            logging.error(traceback.format_exc())
            return response({"error": "Error en motor"}, 500)

        if not isinstance(resultado, dict):
            return response({"error": "Resultado inválido"}, 500)

        nombre = data.get("nombre", "")
        email = data.get("email", "")
        telefono = data.get("telefono", "")

        # =========================================
        # MODO ANÓNIMO
        # =========================================
        if not email:
            return response({
                "ok": True,
                "modo": "anonimo",
                "resultado": resultado
            })

        # =========================================
        # CREAR LEAD
        # =========================================
        lead = {
            "id": str(uuid.uuid4()),
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "score": resultado.get("diagnostico", {}).get("score"),
            "clasificacion": resultado.get("clasificacion"),
            "impacto_min": resultado.get("impacto", {}).get("impacto_min"),
            "impacto_max": resultado.get("impacto", {}).get("impacto_max"),
            "simulador": resultado.get("simulador"),
            "estatus": "nuevo",
            "fecha": datetime.now().isoformat(),
            "pdf": False
        }

        leads_db.append(lead)

        # =========================================
        # EMAIL + PDF ASYNC
        # =========================================
        def procesos_async():
            try:
                # Notificación
                if enviar_notificacion_lead:
                    enviar_notificacion_lead(
                        nombre=nombre,
                        email_cliente=email,
                        telefono=telefono,
                        score=lead["score"],
                        clasificacion=lead["clasificacion"],
                        soluciones=resultado.get("soluciones", [])
                    )

                # PDF
                if generar_diagnostico_pdf and enviar_reporte_pdf:
                    pdf_bytes = generar_diagnostico_pdf(
                        nombre=nombre,
                        email=email,
                        telefono=telefono,
                        score=lead["score"],
                        clasificacion=lead["clasificacion"],
                        soluciones=resultado.get("soluciones", []),
                        impacto_min=lead.get("impacto_min") or 0,
                        impacto_max=lead.get("impacto_max") or 0
                    )
                    lead["pdf"] = True
                    enviar_reporte_pdf(email, nombre, pdf_bytes)

            except Exception:
                logging.error(traceback.format_exc())

        threading.Thread(target=procesos_async).start()

        # =========================================
        # RESPUESTA
        # =========================================
        return response({
            "ok": True,
            "modo": "lead_guardado",
            "resultado": resultado,
            "lead_id": lead["id"],
            "pdf_enviado": lead["pdf"]
        })

# =========================================
# LEADS PROTEGIDO
# =========================================
@app.get("/leads")
async def obtener_leads(api_key: str = Header(None, alias="api-key")):
    if api_key != os.environ.get("MESAN_API_KEY"):
        return response({"error": "No autorizado"}, 403)
    return response({"leads": leads_db})

# =========================================
# ACTUALIZAR LEAD
# =========================================
@app.put("/lead/{lead_id}")
async def actualizar_lead(lead_id: str, data: dict):
    for lead in leads_db:
        if lead["id"] == lead_id:
            lead["estatus"] = data.get("estatus", lead["estatus"])
            return response({"ok": True, "lead": lead})
    return response({"ok": False})

# =========================================
# ERROR GLOBAL
# =========================================
@app.exception_handler(Exception)
async def global_exception(request: Request, exc: Exception):
    logging.error(traceback.format_exc())
    return response({"error": "Error interno"}, 500)
