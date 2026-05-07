# routes/mesan.py
# MESAN Omega — Endpoint Unificado + Planes de Monetización
# ===========================================================
# POST /mesan-index → análisis unificado (gancho)
# GET /planes → catálogo de planes
# POST /crear-sesion-plan → Stripe para cualquier plan

import os
import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from models import Diagnostico
from core.motor_financiero_avanzado import analizar_finanzas
from core.mesan_index import calcular_mesan_index

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxx")
DOMINIO = os.getenv("DOMINIO", "https://mesanomega.com")


# ─── SCHEMAS ─────────────────────────────────────────────────────────

class InputMesan(BaseModel):
    ingresos: float
    egresos: float
    activos: float
    pasivos: float
    obligaciones: float
    laboral: str = "MEDIO"
    fiscal: str = "MEDIO"
    operativo: str = "MEDIO"
    empresa: Optional[str] = ""
    sector: Optional[str] = "GENERAL"

class SesionPlan(BaseModel):
    plan_id: str # diagnostico | profesional | enterprise | intervencion
    diagnostico_id: Optional[int] = None
    telefono: Optional[str] = None


# ─── PLANES ──────────────────────────────────────────────────────────

PLANES = {
    "diagnostico": {
        "nombre": "Diagnóstico IA",
        "precio": 299,
        "descripcion": "1 análisis completo. Causa raíz + estrategia + plan de acción.",
        "features": ["1 diagnóstico completo", "Causa raíz identificada", "Plan de acción", "Contacto especialista"],
        "recurrente": False
    },
    "profesional": {
        "nombre": "Monitoreo Profesional",
        "precio": 970,
        "descripcion": "Monitoreo mensual continuo. MESAN Index + alertas automáticas.",
        "features": ["MESAN Index mensual", "Alertas de riesgo", "Diagnósticos ilimitados", "Reporte ejecutivo"],
        "recurrente": True,
        "intervalo": "month"
    },
    "enterprise": {
        "nombre": "Enterprise",
        "precio": 2999,
        "descripcion": "Multiempresa. Dashboard ejecutivo. Consultor dedicado.",
        "features": ["Hasta 5 empresas", "Dashboard en tiempo real", "Consultor senior dedicado", "Reportes personalizados", "WhatsApp directo"],
        "recurrente": True,
        "intervalo": "month"
    },
    "intervencion": {
        "nombre": "Intervención Senior",
        "precio": 9999,
        "descripcion": "Consultoría directa Lic. Sánchez. Casos críticos.",
        "features": ["Sesiones ilimitadas", "Intervención presencial", "Plan de rescate ejecutivo", "Seguimiento 90 días"],
        "recurrente": False
    }
}


# ─── ENDPOINT: MESAN INDEX (CORE) ────────────────────────────────────

@router.post("/mesan-index")
def mesan_index(data: InputMesan, db: Session = Depends(get_db)):
    """
    Motor unificado: Financiero + Laboral + Fiscal + Operativo.
    Devuelve MESAN Index 0-100 + nivel + impacto (gancho).
    Detalle completo bloqueado hasta pago.
    """

    # Motor financiero
    fin = analizar_finanzas(data.dict())

    # MESAN Index unificado
    idx = calcular_mesan_index({
        "liquidez": fin["liquidez"],
        "flujo": fin["flujo_ajustado"],
        "laboral": data.laboral,
        "fiscal": data.fiscal,
        "operativo": data.operativo
    })

    # Guardar en DB
    diag = Diagnostico(
        nivel = idx["nivel"],
        area = idx["area_critica"],
        impacto = idx["impacto"],
        causa = fin["_causa_raiz"],
        detalle = (
            f"MESAN Index: {idx['index']}/100 | "
            f"Liquidez: {fin['liquidez']} | "
            f"Flujo ajustado: ${fin['flujo_ajustado']:,.0f} | "
            f"Área crítica: {idx['area_critica']}"
        ),
        impacto_detalle = f"Impacto estimado: ${idx['impacto']} MXN",
        plan = "\n".join(fin["_plan_accion"]),
        sector = data.sector or "GENERAL",
        empresa = data.empresa or "",
        pagado = False
    )
    db.add(diag)
    db.commit()
    db.refresh(diag)

    # 🔒 GANCHO — index + nivel + impacto + área crítica
    return {
        "id": diag.id,
        "index": idx["index"],
        "nivel": idx["nivel"],
        "impacto": idx["impacto"],
        "area_critica":idx["area_critica"],
        "desglose": idx["desglose"], # desglose por área visible (engancha)
        "unlock": False,
        "mensaje": "Diagnóstico completo bloqueado"
    }


# ─── ENDPOINT: CATÁLOGO DE PLANES ────────────────────────────────────

@router.get("/planes")
def obtener_planes():
    """Devuelve catálogo de planes con precios y features."""
    return {"planes": PLANES}


# ─── ENDPOINT: CREAR SESIÓN STRIPE POR PLAN ──────────────────────────

@router.post("/crear-sesion-plan")
def crear_sesion_plan(data: SesionPlan):
    """
    Crea sesión Stripe para cualquier plan.
    Soporta pago único y suscripción mensual.
    """

    plan = PLANES.get(data.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Plan no válido")

    diag_id = data.diagnostico_id or 0
    metadata = {
        "plan_id": data.plan_id,
        "diagnostico_id": str(diag_id),
        "telefono": data.telefono or ""
    }

    try:
        if plan.get("recurrente"):
            # Suscripción mensual
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "mxn",
                        "product_data": {"name": f"MESAN Ω — {plan['nombre']}", "description": plan["descripcion"]},
                        "unit_amount": plan["precio"] * 100,
                        "recurring": {"interval": plan.get("intervalo", "month")}
                    },
                    "quantity": 1
                }],
                mode="subscription",
                metadata=metadata,
                success_url=f"{DOMINIO}/success.html?id={diag_id}&plan={data.plan_id}",
                cancel_url=f"{DOMINIO}/"
            )
        else:
            # Pago único
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "mxn",
                        "product_data": {"name": f"MESAN Ω — {plan['nombre']}", "description": plan["descripcion"]},
                        "unit_amount": plan["precio"] * 100
                    },
                    "quantity": 1
                }],
                mode="payment",
                metadata=metadata,
                success_url=f"{DOMINIO}/success.html?id={diag_id}&plan={data.plan_id}",
                cancel_url=f"{DOMINIO}/"
            )

        return {"url": session.url, "plan": data.plan_id, "precio": plan["precio"]}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
