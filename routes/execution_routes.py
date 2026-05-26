# routes/execution_routes.py -- MESAN Omega Execution Routes v1.4
import os
import time
import logging

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.auth.tenant_context import get_tenant, set_tenant
from core.auth.tenant_model import Tenant
from core.auth.audit_log import AuditLog
from core.billing.billing_engine import BillingEngine
from services.executive_narrative_generator import ExecutiveNarrativeGenerator

router = APIRouter()

logger = logging.getLogger("mesan.execute")

# ============================================================
# ENV
# ============================================================

ENV = os.getenv("ENV", "production").lower()

# ============================================================
# PAYLOAD MODEL
# ============================================================

class ExecutePayload(BaseModel):

    empresa: str = Field(default="EMPRESA")

    ingresos: float = Field(default=0, ge=0)
    gastos: float = Field(default=0, ge=0)
    nomina: float = Field(default=0, ge=0)

    deuda_mensual: float = Field(default=0, ge=0)
    cartera_vencida: float = Field(default=0, ge=0)

    trabajadores_sin_imss: int = Field(default=0, ge=0)

    bloqueo_bancario: bool = False
    repse_suspendido: bool = False

# ============================================================
# RISK ENGINE
# ============================================================

def calcular_riesgo(data: dict) -> tuple:

    ingresos = max(float(data.get("ingresos", 0)), 1)

    gastos   = float(data.get("gastos", 0))
    nomina   = float(data.get("nomina", 0))
    deuda    = float(data.get("deuda_mensual", 0))
    cartera  = float(data.get("cartera_vencida", 0))

    sin_imss = int(data.get("trabajadores_sin_imss", 0))

    bloqueo_bancario = bool(data.get("bloqueo_bancario", False))
    repse_suspendido = bool(data.get("repse_suspendido", False))

    score = 72

    # ========================================================
    # FINANCIAL PRESSURE
    # ========================================================

    if deuda > ingresos * 0.35:
        score += 8

    if cartera > ingresos:
        score += 6

    if sin_imss > 10:
        score += 5

    if repse_suspendido:
        score += 10

    if bloqueo_bancario:
        score += 15

    score = min(score, 100)

    # ========================================================
    # RISK LEVEL
    # ========================================================

    if score >= 85:
        nivel = "CRITICO"

    elif score >= 70:
        nivel = "ALTO"

    elif score >= 50:
        nivel = "MEDIO"

    else:
        nivel = "BAJO"

    # ========================================================
    # CASHFLOW
    # ========================================================

    flujo_operativo = ingresos - gastos - deuda - nomina

    if flujo_operativo <= 0:
        dias_supervivencia = 18

    elif flujo_operativo < ingresos * 0.10:
        dias_supervivencia = 45

    else:
        dias_supervivencia = 90

    return (
        score,
        nivel,
        flujo_operativo,
        dias_supervivencia
    )

# ============================================================
# FALLBACK REPORT
# ============================================================

def fallback_report() -> str:

    return (
        "RIESGO OPERATIVO ELEVADO.\n"
        "Ejecutar contención financiera inmediata.\n"
        "Proteger flujo operativo crítico.\n"
        "Renegociar presión bancaria y fiscal.\n"
        "Reducir exposición laboral de alto impacto."
    )

# ============================================================
# EXECUTE ENDPOINT
# ============================================================

@router.post("/execute")
async def execute(payload: ExecutePayload, request: Request):

    started = time.time()

    trace_id = f"exec-{int(started * 1000)}"

    logger.info(
        f"[EXECUTE] request received trace_id={trace_id}"
    )

    # ========================================================
    # TENANT RESOLUTION
    # ========================================================

    tenant = get_tenant()

    if not tenant:

        if ENV != "production":

            set_tenant(
                Tenant(
                    tenant_id="demo",
                    name="DEMO_TENANT",
                    plan="FREE"
                )
            )

            tenant = get_tenant()

        else:

            logger.warning(
                f"[EXECUTE] tenant missing trace_id={trace_id}"
            )

            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "message": "TENANT_MISSING",
                    "trace_id": trace_id
                }
            )

    # ========================================================
    # EXECUTION PIPELINE
    # ========================================================

    try:

        data = payload.model_dump()

        (
            score,
            nivel,
            flujo_operativo,
            dias_supervivencia
        ) = calcular_riesgo(data)

        resultado = {

            "nivel": nivel,

            "score": score,

            "dias_supervivencia": dias_supervivencia,

            "flujo_operativo": flujo_operativo,

            "dscr": round(
                flujo_operativo /
                max(float(data.get("deuda_mensual", 1)), 1),
                2
            ),

            "acciones_hoy": [

                "Bloquear gasto no esencial",

                "Renegociar pasivos bancarios",

                "Proteger flujo operativo crítico"
            ],

            "acciones_72h": [

                "Reestructurar presión financiera",

                "Congelar contrataciones",

                "Ejecutar reducción táctica de gasto"
            ],

            "acciones_7d": [

                "Optimizar capital de trabajo",

                "Auditar contratos críticos",

                "Reducir exposición SAT/IMSS"
            ]
        }

        # ====================================================
        # AUDIT
        # ====================================================

        try:

            AuditLog().log(
                tenant_id=tenant.tenant_id,
                event_type="EXECUTION",
                payload={
                    **resultado,
                    "trace_id": trace_id
                }
            )

        except Exception as e:

            logger.warning(
                f"[EXECUTE] audit error "
                f"trace_id={trace_id}: {e}"
            )

        # ====================================================
        # BILLING
        # ====================================================

        try:

            invoice = BillingEngine().charge(
                tenant_id=tenant.tenant_id,
                operation="EXECUTION_DECISION",
                risk_score=score
            )

        except Exception as e:

            logger.warning(
                f"[EXECUTE] billing error "
                f"trace_id={trace_id}: {e}"
            )

            class DummyInvoice:
                amount   = 0
                currency = "MXN"
                reason   = "billing_disabled"

            invoice = DummyInvoice()

        # ====================================================
        # NARRATIVE
        # ====================================================

        try:

            report = (
                ExecutiveNarrativeGenerator()
                .generar(resultado)
            )

            if not report:
                report = fallback_report()

        except Exception as e:

            logger.warning(
                f"[EXECUTE] narrative error "
                f"trace_id={trace_id}: {e}"
            )

            report = fallback_report()

        # ====================================================
        # RESPONSE
        # ====================================================

        latency_ms = round(
            (time.time() - started) * 1000,
            2
        )

        logger.info(
            f"[EXECUTE] pipeline completed "
            f"trace_id={trace_id} "
            f"latency_ms={latency_ms}"
        )

        return {

            "status": "success",

            "trace_id": trace_id,

            "tenant_id": tenant.tenant_id,

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "latency_ms": latency_ms,

            "result": resultado,

            "invoice": {

                "amount": invoice.amount,

                "currency": invoice.currency,

                "reason": invoice.reason
            },

            "report": report
        }

    except Exception as e:

        logger.exception(
            f"[EXECUTE] pipeline failed "
            f"trace_id={trace_id}"
        )

        return JSONResponse(

            status_code=500,

            content={

                "status": "error",

                "message": "EXECUTION_TEMPORARILY_UNAVAILABLE",

                "trace_id": trace_id
            }
        )
