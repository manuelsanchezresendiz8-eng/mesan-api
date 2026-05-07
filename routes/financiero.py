# routes/financiero.py
# MESAN Omega — Endpoint Análisis Financiero
# ============================================
# POST /analisis-financiero → gancho (nivel + impacto, bloqueado)
# GET /unlock-financiero/{id} → unlock post-pago (causa + estrategia + plan)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Diagnostico
from core.motor_financiero_avanzado import analizar_finanzas

router = APIRouter()


# ─── SCHEMA ──────────────────────────────────────────────────────────

class InputFinanciero(BaseModel):
    ingresos: float
    egresos: float
    activos: float
    pasivos: float
    obligaciones: float
    empresa: str = ""
    sector: str = "FINANCIERO"


# ─── ENDPOINT: ANÁLISIS (GANCHO) ─────────────────────────────────────

@router.post("/analisis-financiero")
def analisis_financiero(data: InputFinanciero, db: Session = Depends(get_db)):
    """
    Corre el motor financiero v31.
    Devuelve solo nivel + liquidez + impacto (gancho).
    Causa raíz, estrategia y plan → bloqueados hasta pago.
    """

    resultado = analizar_finanzas(data.dict())

    # Guardar en DB para unlock posterior
    diag = Diagnostico(
        nivel = resultado["nivel"],
        area = "FINANCIERO / FLUJO",
        impacto = resultado["impacto"],
        causa = resultado["_causa_raiz"],
        detalle = f"Liquidez: {resultado['liquidez']} | Flujo ajustado: ${resultado['flujo_ajustado']:,.0f} | Deuda ratio: {resultado['deuda_ratio']}",
        impacto_detalle = f"Impacto estimado: ${resultado['impacto']} MXN",
        plan = "\n".join(resultado["_plan_accion"]),
        sector = data.sector,
        empresa = data.empresa,
        pagado = False
    )
    db.add(diag)
    db.commit()
    db.refresh(diag)

    # 🔒 GANCHO — solo nivel/liquidez/impacto
    return {
        "id": diag.id,
        "nivel": resultado["nivel"],
        "liquidez": resultado["liquidez"],
        "impacto": resultado["impacto"],
        "flujo": resultado["flujo"],
        "mensaje": "Diagnóstico financiero completo bloqueado",
        "unlock": False
    }


# ─── ENDPOINT: UNLOCK POST-PAGO ──────────────────────────────────────

@router.get("/unlock-financiero/{id}")
def unlock_financiero(id: int, db: Session = Depends(get_db)):
    """
    Devuelve diagnóstico financiero completo si el pago fue confirmado.
    Se activa después del webhook Stripe → pagado=True en DB.
    """

    diag = db.query(Diagnostico).filter(Diagnostico.id == id).first()

    if not diag:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")

    if not diag.pagado:
        return {"error": "No autorizado", "pagado": False}

    # Reconstruir estrategia y plan desde DB
    from core.motor_financiero_avanzado import analizar_finanzas
    # Plan guardado como texto, convertir a lista
    plan_lista = [l.strip().lstrip("0123456789.-) ") for l in (diag.plan or "").split("\n") if l.strip()]

    return {
        "pagado": True,
        "nivel": diag.nivel,
        "area": diag.area,
        "impacto": diag.impacto,
        "causa_raiz": diag.causa,
        "detalle": diag.detalle,
        "estrategia": [
            "Reestructura de pasivos a 90 días",
            "Optimización de carga operativa",
            "Reducción de gasto no crítico",
            "Negociación con acreedores"
        ] if diag.nivel == "CRITICO" else [
            "Revisión de flujo operativo",
            "Diferimiento de obligaciones no urgentes",
            "Incremento de liquidez a corto plazo"
        ],
        "plan_accion": plan_lista
    }
