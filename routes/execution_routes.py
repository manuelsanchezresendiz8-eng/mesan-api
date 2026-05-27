# routes/execution_routes.py -- MESAN Omega Execution Routes v1.8

import os
import time
import logging
import traceback

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field

from core.auth.tenant_context import get_tenant, set_tenant
from core.auth.tenant_model import Tenant
from core.auth.audit_log import AuditLog
from core.billing.billing_engine import BillingEngine

from services.executive_narrative_generator import (
    ExecutiveNarrativeGenerator
)

from services.fiscal_sentinel_engine import (
    FiscalSentinelEngine
)

from services.compliance_verify_engine import (
    ComplianceVerifyEngine
)

router = APIRouter()

logger = logging.getLogger("mesan.execute")

ENV = os.getenv("ENV", "development").lower()

# ============================================================
# PAYLOAD
# ============================================================

class ExecutePayload(BaseModel):

    empresa: str = Field(
        default="EMPRESA",
        max_length=120
    )

    ingresos: float = Field(default=0, ge=0)
    gastos: float = Field(default=0, ge=0)
    nomina: float = Field(default=0, ge=0)

    deuda_mensual: float = Field(default=0, ge=0)

    cartera_vencida: float = Field(default=0, ge=0)

    iva: float = Field(default=0, ge=0)

    isr_retenido: float = Field(default=0, ge=0)

    trabajadores: int = Field(default=0, ge=0)

    trabajadores_sin_imss: int = Field(
        default=0,
        ge=0
    )

    bloqueo_bancario: bool = False

    repse_suspendido: bool = False

    opinion_sat: str = Field(
        default="NO_LOCALIZADA",
        max_length=40
    )

    opinion_imss: str = Field(
        default="NO_LOCALIZADA",
        max_length=40
    )


# ============================================================
# ENDPOINT
# ============================================================

@router.post("/execute")
async def execute(payload: ExecutePayload, request: Request):

    started = time.time()

    trace_id = f"exec-{int(started * 1000)}"

    logger.info(
        f"[EXECUTE] request received trace_id={trace_id}"
    )

    # ========================================================
    # TENANT
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

            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "message": "TENANT_MISSING",
                    "trace_id": trace_id
                }
            )

    try:

        data = payload.model_dump()

        data["tenant_id"] = tenant.tenant_id
        data["trace_id"]  = trace_id

        # ====================================================
        # FISCAL ENGINE
        # ====================================================

        try:

            fiscal = FiscalSentinelEngine().analizar(data)

            fiscal_resultado = fiscal.get(
                "resultado",
                {}
            )

            score = fiscal_resultado.get(
                "score",
                72
            )

            nivel = fiscal_resultado.get(
                "nivel",
                "ALTO"
            )

            flujo = fiscal_resultado.get(
                "flujo_operativo",
                0
            )

            alertas = fiscal_resultado.get(
                "alertas",
                []
            )

            recomendaciones = fiscal_resultado.get(
                "recomendaciones",
                []
            )

        except Exception as e:

            logger.warning(
                f"[EXECUTE] fiscal engine error: {e}"
            )

            logger.warning(
                traceback.format_exc()
            )

            score = 72
            nivel = "ALTO"
            flujo = 0

            alertas = [
                {
                    "tipo": "ENGINE",
                    "nivel": "ALTO",
                    "mensaje": "Fiscal engine temporalmente degradado"
                }
            ]

            recomendaciones = [
                "Ejecutar revisión manual"
            ]

        # ====================================================
        # COMPLIANCE ENGINE
        # ====================================================

        try:

            compliance = (
                ComplianceVerifyEngine().calcular_score(
                    repse_vigente=not payload.repse_suspendido,
                    opinion_sat=payload.opinion_sat,
                    opinion_imss=payload.opinion_imss
                )
            )

        except Exception as e:

            logger.warning(
                f"[EXECUTE] compliance error: {e}"
            )

            logger.warning(
                traceback.format_exc()
            )

            compliance = {
                "score_compliance": 100,
                "nivel": "SEGURO",
                "alertas": []
            }

        # ====================================================
        # DIAS SUPERVIVENCIA
        # ====================================================

        ingresos = max(
            float(data.get("ingresos", 0)),
            1
        )

        if flujo <= 0:

            dias = 18

        elif flujo < ingresos * 0.10:

            dias = 45

        else:

            dias = 90

        # ====================================================
        # DSCR
        # ====================================================

        deuda = float(
            data.get("deuda_mensual", 0)
        )

        if deuda <= 0:

            dscr = flujo

        else:

            dscr = round(
                flujo / deuda,
                2
            )

        # ====================================================
        # RESULTADO
        # ====================================================

        resultado = {

            "nivel": nivel,

            "score": score,

            "dias_supervivencia": dias,

            "flujo_operativo": flujo,

            "dscr": dscr,

            "alertas": alertas,

            "recomendaciones": recomendaciones,

            "compliance": {

                "score": compliance.get(
                    "score_compliance",
                    100
                ),

                "nivel": compliance.get(
                    "nivel",
                    "SEGURO"
                ),

                "alertas": compliance.get(
                    "alertas",
                    []
                )
            },

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
                    "trace_id": trace_id,
                    "score": score,
                    "nivel": nivel
                }
            )

        except Exception as e:

            logger.warning(
                f"[EXECUTE] audit error: {e}"
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
                f"[EXECUTE] billing error: {e}"
            )

            class DummyInvoice:

                amount = 0

                currency = "MXN"

                reason = "billing_disabled"

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

                report = (
                    "Ejecutar contención "
                    "financiera inmediata."
                )

        except Exception as e:

            logger.warning(
                f"[EXECUTE] narrative error: {e}"
            )

            report = (
                "Ejecutar contención "
                "financiera inmediata."
            )

        # ====================================================
        # RESPONSE
        # ====================================================

        latency_ms = round(
            (time.time() - started) * 1000,
            2
        )

        logger.info(
            f"[EXECUTE] completed "
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

    except Exception:

        logger.exception(
            f"[EXECUTE] pipeline failed "
            f"trace_id={trace_id}"
        )

        return JSONResponse(

            status_code=500,

            content={

                "status": "error",

                "message":
                    "EXECUTION_TEMPORARILY_UNAVAILABLE",

                "trace_id": trace_id
            }
        )
