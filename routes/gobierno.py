import os
import stripe
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

CODIGO_MAESTRO = os.getenv("CODIGO_MAESTRO")

# =========================
# MODELOS
# =========================
class AuditoriaRequest(BaseModel):
    cliente_id: str
    sector: str
    monto: float = 300.0
    institucion: Optional[str] = "General"
    contrato_id: Optional[str] = "N/A"
    datos_empresa: dict


class NodoOperativo(BaseModel):
    empleado_id: str
    nombre: str
    pago_internet_total: float
    pago_luz_total: float
    contrato_nom037_firmado: bool
    equipo_en_comodato: List[str]
    vpn_activa: bool = True


class EstatusNodo(str, Enum):
    optimo = "OPTIMO"
    alerta = "ALERTA"


# =========================
# MOTOR INSTITUCIONAL
# =========================
class OmegaEngine:

    @staticmethod
    def calcular_imse(datos):
        puntos = 0
        if datos.get("imss_al_dia"): puntos += 40
        if datos.get("sat_cumplimiento"): puntos += 30
        if datos.get("stps_normas"): puntos += 30
        nivel = "BAJO" if puntos >= 80 else "MEDIO" if puntos >= 50 else "ALTO"
        return {"puntos": puntos, "nivel": nivel}

    @staticmethod
    def calcular_reembolso(internet, luz):
        return round((internet + luz) * 0.30, 2)

    @staticmethod
    def generar_score_global(datos):
        imse = OmegaEngine.calcular_imse(datos)
        score = imse["puntos"]
        dinero_perdido = (100 - score) * 1500
        return {
            "score": score,
            "riesgo": imse["nivel"],
            "dinero_perdido_estimado": dinero_perdido
        }


# =========================
# REGISTRO DE EVENTOS
# =========================
eventos = []

def registrar_evento(tipo: str, descripcion: str):
    eventos.append({
        "tipo": tipo,
        "descripcion": descripcion,
        "fecha": datetime.utcnow().isoformat()
    })
    logging.info(f"Evento: {tipo} - {descripcion}")


# =========================
# ENDPOINTS
# =========================
@router.post("/gobierno/diagnostico")
async def diagnostico_gobierno(request: AuditoriaRequest):
    resultado = OmegaEngine.generar_score_global(request.datos_empresa)
    registrar_evento(
        "DIAGNOSTICO",
        f"Sector: {request.sector} | Institucion: {request.institucion}"
    )
    return {
        "status": "ok",
        "cliente": request.cliente_id,
        "sector": request.sector,
        "institucion": request.institucion,
        "contrato_id": request.contrato_id,
        "resultado": resultado,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/gobierno/crear-sesion-pago")
async def crear_sesion_gobierno(request: AuditoriaRequest):
    try:
        monto_centavos = int(request.monto * 100)
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {
                        "name": f"MESAN Omega - {request.sector}",
                        "description": f"{request.institucion} | {request.contrato_id}"
                    },
                    "unit_amount": monto_centavos,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://mesanomega.com/exito",
            cancel_url="https://mesanomega.com",
            metadata={
                "cliente_id": request.cliente_id,
                "sector": request.sector
            }
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/nodo/evaluar")
async def evaluar_nodo(datos: NodoOperativo):
    reembolso = OmegaEngine.calcular_reembolso(
        datos.pago_internet_total,
        datos.pago_luz_total
    )

    alertas = []
    if not datos.contrato_nom037_firmado:
        alertas.append("FALTA NOM-037")
    if not datos.vpn_activa:
        alertas.append("SIN VPN")
    if not datos.equipo_en_comodato:
        alertas.append("SIN EQUIPO EN COMODATO")

    riesgo_total = len(alertas) * 25
    nivel_global = (
        "CRITICO" if riesgo_total >= 50
        else "ALTO" if riesgo_total >= 25
        else "CONTROLADO"
    )

    registrar_evento(
        "NODO_EVALUADO",
        f"Empleado: {datos.nombre} | Nivel: {nivel_global}"
    )

    return {
        "empleado": datos.nombre,
        "empleado_id": datos.empleado_id,
        "estatus": EstatusNodo.optimo if not alertas else EstatusNodo.alerta,
        "reembolso": reembolso,
        "riesgo_global": nivel_global,
        "alertas": alertas
    }


@router.post("/gobierno/panic")
async def boton_panico(codigo_seguridad: str, salario_minimo_vigente: float = 0):
    if codigo_seguridad != CODIGO_MAESTRO:
        raise HTTPException(status_code=403, detail="Codigo incorrecto")

    registrar_evento(
        "PANIC_BUTTON",
        f"Activado con salario {salario_minimo_vigente}"
    )

    return {
        "status": "EMERGENCY",
        "accion": "SISTEMA BLOQUEADO",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/gobierno/eventos")
async def ver_eventos():
    return {"eventos": eventos}
