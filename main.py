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

from database import init_db, SessionLocal
from models import Lead
from limiter import limiter

from routes.evaluar import router as evaluar_router
from routes.verificar import router as verificar_router
from routes.consultar import router as consultar_router
from routes.documentos import router as documentos_router
from routes.pagos_omega import router as pagos_router
from routes.gobierno import router as gobierno_router
from routes.ai_diagnostico import router as ai_router  # ← NUEVO
from pro.auth import auth_router
from pro.diagnostico import diagnostico_router

# =========================================
# CONFIG
# =========================================
VERSION = "2.5.0"
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

try:
    from utils.helpers import normalizar_clasificacion
    logging.info("helpers OK")
except Exception as e:
    logging.error(f"ERROR helpers: {e}")
    def normalizar_clasificacion(v):
        return "MEDIO"

try:
    from core.motor_financiero import evaluar_servicio
    logging.info("motor_financiero OK")
except Exception as e:
    logging.error(f"ERROR motor_financiero: {e}")
    evaluar_servicio = None

try:
    from core.motor_total import motor_total
    logging.info("motor_total OK")
except Exception as e:
    logging.error(f"ERROR motor_total: {e}")
    motor_total = None

try:
    from routes.chat_ai import router as chat_router
    logging.info("chat_ai OK")
except Exception as e:
    logging.error(f"ERROR chat_ai: {e}")
    chat_router = None

# =========================================
# VALIDACION ENV
# =========================================
if not os.environ.get("MESAN_API_KEY"):
    logging.critical("Falta MESAN_API_KEY")
    sys.exit(1)

if not os.environ.get("DATABASE_URL"):
    logging.critical("Falta DATABASE_URL")
    sys.exit(1)

# =========================================
# INIT
# =========================================
try:
    init_db()
    logging.info("DB init OK")
except Exception as e:
    logging.error(f"ERROR init_db: {e}")

app = FastAPI(title="MESAN API", version=VERSION)

# =========================================
# CORS
# =========================================
origins = [
    "https://mesanomega.com",
    "https://www.mesanomega.com",
    "https://manuelsanchezresendiz8-eng.github.io",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*", "api-key", "Authorization", "Content-Type"],
    expose_headers=["*"],
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
app.include_router(consultar_router, prefix="/api")
app.include_router(documentos_router)
app.include_router(pagos_router)
app.include_router(gobierno_router)
app.include_router(ai_router)  # ← NUEVO
app.include_router(auth_router, prefix="/pro")
app.include_router(diagnostico_router, prefix="/pro")

if chat_router:
    app.include_router(chat_router)

# =========================================
# HELPERS
# =========================================
def response(data, status=200):
    return JSONResponse(
        status_code=status,
        content=data,
        headers={"X-MESAN-VERSION": VERSION}
    )

def serialize_lead(l):
    return {
        "id": l.id,
        "nombre": l.nombre,
        "email": l.email,
        "telefono": l.telefono,
        "score": l.score,
        "clasificacion": l.clasificacion,
        "impacto_min": l.impacto_min,
        "impacto_max": l.impacto_max,
        "estatus": l.estatus,
        "fecha": str(l.fecha) if l.fecha else None,
        "giro": getattr(l, "giro", None)
    }

def normalize_input(data: dict) -> dict:
    normalized = dict(data)

    field_map = {
        "situacion_fiscal": "factura",
        "gestion_contable": "contabilidad",
        "registro_imss": "imss",
        "contratos_laborales": "contratos",
        "procesos_documentados": "procesos",
        "ante_inspeccion": "inspeccion",
        "historial_multas": "historial",
    }

    for k, v in field_map.items():
        if k in data and v not in data:
            normalized[v] = data[k]

    raw_nombre = data.get("nombre")
    if raw_nombre:
        normalized["nombre"] = raw_nombre.strip()

    return normalized

# =========================================
# ROOT / HEALTH
# =========================================
@app.get("/")
@app.head("/")
async def root():
    return response({"status": "MESAN-Omega API activa", "version": VERSION})

@app.get("/health")
@app.head("/health")
async def health():
    return response({"status": "ok", "version": VERSION})

# =========================================
# PREFLIGHT CORS
# =========================================
@app.options("/enterprise")
def preflight_enterprise():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://mesanomega.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "api-key, Content-Type, Authorization",
        },
    )

@app.options("/leads")
def preflight_leads():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://mesanomega.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "api-key, Content-Type, Authorization",
        },
    )

# =========================================
# ENDPOINT PRINCIPAL
# =========================================
@app.post("/enterprise")
@limiter.limit("10/minute")
async def enterprise(data: dict, request: Request):

    logging.info(f"DATA RECIBIDA: {data}")

    try:
        if not isinstance(data, dict):
            return JSONResponse(status_code=400, content={"error": "Payload invalido"})

        data = normalize_input(data)

        nombre = (data.get("nombre") or "").strip() or "Sin nombre"
        email = (data.get("email") or "").strip()
        telefono = (data.get("telefono") or "").strip() or "Sin telefono"
        giro = (data.get("giro") or "").strip()

        logging.warning(f"LEAD FINAL -> {nombre} | {email} | {telefono} | {giro}")

        resultado = {}
        if sistema_enterprise:
            try:
                resultado = sistema_enterprise(data) or {}
            except Exception:
                logging.error(f"ERROR motor: {traceback.format_exc()}")
                resultado = {
                    "clasificacion": "MEDIO",
                    "diagnostico": {"score": 0},
                    "impacto": {"impacto_min": 0, "impacto_max": 0},
                    "soluciones": []
                }

        if not email:
            return response({
                "ok": True,
                "modo": "anonimo",
                "resultado": resultado
            })

        lead_id = str(uuid.uuid4())
        lead_data = {
            "id": lead_id,
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "score": resultado.get("diagnostico", {}).get("score") or 0,
            "clasificacion": normalizar_clasificacion(resultado.get("clasificacion")),
            "impacto_min": resultado.get("impacto", {}).get("impacto_min") or 0,
            "impacto_max": resultado.get("impacto", {}).get("impacto_max") or 0,
            "estatus": "nuevo",
            "fecha": datetime.now().isoformat()
        }

        try:
            db = SessionLocal()
            nuevo_lead = Lead(**lead_data)
            db.add(nuevo_lead)
            db.commit()
            db.close()
            logging.info(f"Lead guardado en DB: {email}")
        except Exception:
            logging.error(f"Error guardando lead: {traceback.format_exc()}")

        def procesos_async():
            try:
                if enviar_notificacion_lead:
                    enviar_notificacion_lead(
                        nombre=nombre,
                        email_cliente=email,
                        telefono=telefono,
                        score=lead_data["score"],
                        clasificacion=lead_data["clasificacion"],
                        soluciones=resultado.get("soluciones", [])
                    )
                    logging.info("notificacion enviada OK")

                if generar_diagnostico_pdf and enviar_reporte_pdf:
                    pdf_bytes = generar_diagnostico_pdf(
                        nombre=nombre,
                        email=email,
                        telefono=telefono,
                        score=lead_data["score"],
                        clasificacion=lead_data["clasificacion"],
                        soluciones=resultado.get("soluciones", []),
                        impacto_min=lead_data["impacto_min"],
                        impacto_max=lead_data["impacto_max"]
                    )
                    enviar_reporte_pdf(email, nombre, pdf_bytes)
                    logging.info("PDF enviado OK")

            except Exception:
                logging.error(f"ERROR procesos_async: {traceback.format_exc()}")

        threading.Thread(target=procesos_async, daemon=True).start()

        return response({
            "ok": True,
            "modo": "lead_guardado",
            "resultado": resultado,
            "lead_id": lead_id
        })

    except Exception:
        logging.error(f"ERROR CRITICO /enterprise: {traceback.format_exc()}")
        return response({"error": "Error interno"}, 500)

# =========================================
# PRO DIAGNOSTICO
# =========================================
@app.post("/pro/diagnostico-financiero")
async def pro_diagnostico(data: dict):
    if not evaluar_servicio:
        return response({"error": "Motor financiero no disponible"}, 500)
    try:
        precio = float(data.get("precio_cliente", 0))
        empleados = int(data.get("empleados", 1))
        zona = data.get("zona", "general")
        return response(evaluar_servicio(precio, empleados, zona=zona))
    except Exception:
        logging.error(traceback.format_exc())
        return response({"error": "Error en motor financiero"}, 500)

# =========================================
# LEADS PROTEGIDO
# =========================================
@app.get("/leads")
async def obtener_leads(api_key: str = Header(None, alias="api-key")):
    if not api_key or api_key != os.environ.get("MESAN_API_KEY"):
        return response({"error": "No autorizado"}, 403)
    try:
        db = SessionLocal()
        leads = db.query(Lead).all()
        db.close()
        return response({"leads": [serialize_lead(l) for l in leads]})
    except Exception:
        logging.error(traceback.format_exc())
        return response({"error": "Error obteniendo leads"}, 500)

# =========================================
# LEAD INDIVIDUAL
# =========================================
@app.get("/lead/{lead_id}")
async def obtener_lead(lead_id: str, api_key: str = Header(None, alias="api-key")):
    if not api_key or api_key != os.environ.get("MESAN_API_KEY"):
        return response({"error": "No autorizado"}, 403)
    try:
        db = SessionLocal()
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        db.close()
        if not lead:
            return response({"error": "No encontrado"}, 404)
        return response(serialize_lead(lead))
    except Exception:
        logging.error(traceback.format_exc())
        return response({"error": "Error obteniendo lead"}, 500)

# =========================================
# ACTUALIZAR LEAD
# =========================================
@app.put("/lead/{lead_id}")
async def actualizar_lead(lead_id: str, data: dict):
    try:
        db = SessionLocal()
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            db.close()
            return response({"ok": False})
        lead.estatus = data.get("estatus", lead.estatus)
        db.commit()
        db.close()
        return response({"ok": True})
    except Exception:
        logging.error(traceback.format_exc())
        return response({"error": "Error actualizando lead"}, 500)

# =========================================
# ERROR GLOBAL
# =========================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"ERROR GLOBAL: {traceback.format_exc()}")
    return response({"error": "Error interno"}, 500)
