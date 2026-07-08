# routes/execution_routes.py -- MESAN Omega Execution Routes v2.4
"""
v2.4: invoice extendido con todos los campos del Omega Billing Engine.
"""

import os
import time
import logging

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.auth.tenant_context import get_tenant, set_tenant
from core.auth.tenant_model   import Tenant
from core.auth.audit_log      import AuditLog
from core.billing.billing_engine import BillingEngine
from core.rate_limiter        import rate_limit_check

from services.executive_narrative_generator import ExecutiveNarrativeGenerator
from services.omega_orchestrator            import omega_orchestrator

router = APIRouter()
logger = logging.getLogger("mesan.execute")


class ExecutePayload(BaseModel):
    empresa:               str   = Field(default="EMPRESA", max_length=120)
    ingresos:              float = Field(default=0, ge=0)
    gastos:                float = Field(default=0, ge=0)
    nomina:                float = Field(default=0, ge=0)
    deuda_mensual:         float = Field(default=0, ge=0)
    cartera_vencida:       float = Field(default=0, ge=0)
    iva:                   float = Field(default=0, ge=0)
    isr_retenido:          float = Field(default=0, ge=0)
    trabajadores:          int   = Field(default=0, ge=0)
    trabajadores_sin_imss: int   = Field(default=0, ge=0)
    bloqueo_bancario:      bool  = False
    repse_suspendido:      bool  = False
    opinion_sat:           str   = Field(default="NO_LOCALIZADA", max_length=40)
    opinion_imss:          str   = Field(default="NO_LOCALIZADA", max_length=40)


def _invoice_to_dict(invoice) -> dict:
    """
    Serializa el Invoice a dict completo para la respuesta.
    Soporta tanto Invoice (Omega Billing v3) como DummyInvoice (fallback).
    """
    def _val(obj):
        return obj.value if hasattr(obj, "value") else obj

    return {
        "invoice_id":        getattr(invoice, "invoice_id",        None),
        "tenant_id":         getattr(invoice, "tenant_id",         None),
        "plan":              _val(getattr(invoice, "plan",          "ANONYMOUS")),
        "billing_cycle":     _val(getattr(invoice, "billing_cycle", "MONTHLY")),
        "customer_type":     _val(getattr(invoice, "customer_type", "ANONYMOUS")),
        "amount":            invoice.amount,
        "subtotal":          getattr(invoice, "subtotal",           invoice.amount),
        "discount_pct":      getattr(invoice, "discount_pct",       0.0),
        "discount_amount":   getattr(invoice, "discount_amount",    0.0),
        "currency":          _val(getattr(invoice, "currency",      "MXN")),
        "reason":            invoice.reason,
        "payment_status":    _val(getattr(invoice, "payment_status","PENDING")),
        "payment_url":       getattr(invoice, "payment_url",        None),
        "affiliate_id":      getattr(invoice, "affiliate_id",       None),
        "commission_pct":    getattr(invoice, "commission_pct",     0.0),
        "commission_amount": getattr(invoice, "commission_amount",  0.0),
        "ive_score":         getattr(invoice, "ive_score",          0.0),
        "pricing_version":   getattr(invoice, "pricing_version",    ""),
        "timestamp":         getattr(invoice, "timestamp",          None),
    }


@router.post("/execute")
async def execute(payload: ExecutePayload, request: Request):

    started  = time.time()
    trace_id = f"exec-{int(started * 1000)}"
    logger.info("[EXECUTE] request received trace_id=%s", trace_id)

    rate_limit_check(request, key="execute_diagnostico", max_requests=3, window_seconds=300)

    tenant = get_tenant()
    if not tenant:
        set_tenant(Tenant(
            tenant_id="public_diagnostic",
            name="PUBLIC_DIAGNOSTIC",
            plan="ANONYMOUS",
        ))
        tenant = get_tenant()

    try:
        data = {
            "tenant_id":              tenant.tenant_id,
            "trace_id":               trace_id,
            "empresa_nombre":         payload.empresa,
            "ingresos":               payload.ingresos,
            "gastos":                 payload.gastos,
            "nomina":                 payload.nomina,
            "deuda_mensual":          payload.deuda_mensual,
            "cartera_vencida":        payload.cartera_vencida,
            "iva":                    payload.iva,
            "isr_retenido":           payload.isr_retenido,
            "empleados":              payload.trabajadores,
            "trabajadores":           payload.trabajadores,
            "trabajadores_sin_imss":  payload.trabajadores_sin_imss,
            "repse_vigente":          not payload.repse_suspendido,
            "repse_suspendido":       payload.repse_suspendido,
            "bloqueo_bancario":       payload.bloqueo_bancario,
            "opinion_sat":            payload.opinion_sat,
            "opinion_imss":           payload.opinion_imss,
            "caja_disponible":        0.0,
            "empleados_criticos":     0,
            "demandas_laborales":     0,
            "rotacion_anual":         0.0,
            "severance_estimado":     0.0,
        }

        logger.info("[EXECUTE] invoking OmegaOrchestrator trace_id=%s", trace_id)
        omega_response = omega_orchestrator.ejecutar(data)

        omega_score = getattr(omega_response, "omega_score",               None)
        esi         = getattr(omega_response, "enterprise_survival_index", None)
        war_room    = getattr(omega_response, "war_room_required",         False)
        exposure    = getattr(omega_response, "total_exposure_mxn",        0.0)
        engine_data = getattr(omega_response, "engines",                   {})
        remediation = getattr(omega_response, "remediation",               {})
        summary     = getattr(omega_response, "executive_summary",         "")
        model_drift = getattr(omega_response, "model_drift",               {})
        digital_sovereignty = getattr(omega_response, "digital_sovereignty", None)

        engine_errors = {
            name: res.get("error")
            for name, res in (engine_data or {}).items()
            if isinstance(res, dict) and "error" in res
        }
        if engine_errors:
            logger.error("[EXECUTE] engine_errors trace_id=%s errors=%s", trace_id, engine_errors)

        if omega_score is None:
            logger.error("[EXECUTE] omega_score is None trace_id=%s", trace_id)
            return JSONResponse(status_code=500, content={
                "status":        "error",
                "message":       "OMEGA_PIPELINE_FAILURE",
                "trace_id":      trace_id,
                "engine_errors": engine_errors,
            })

        if omega_score >= 80:   nivel = "BAJO"
        elif omega_score >= 65: nivel = "MEDIO"
        elif omega_score >= 50: nivel = "ALTO"
        elif omega_score >= 35: nivel = "CRITICO"
        else:                   nivel = "EXTREMO"

        fiscal_data = engine_data.get("fiscal", {})
        fiscal_res  = fiscal_data.get("resultado", fiscal_data)
        flujo = fiscal_res.get(
            "flujo_operativo",
            payload.ingresos - payload.gastos - payload.deuda_mensual
        )

        if esi is None:     dias = 30
        elif esi >= 90:     dias = 180
        elif esi >= 80:     dias = 120
        elif esi >= 70:     dias = 90
        elif esi >= 60:     dias = 60
        elif esi >= 45:     dias = 30
        else:               dias = 15

        deuda = payload.deuda_mensual
        if deuda <= 0:
            dscr = None
        elif flujo is not None:
            dscr = round(flujo / deuda, 2)
        else:
            dscr = None

        plan = remediation.get("plan_remediacion", {})
        acciones_hoy = plan.get("acciones_inmediatas") or remediation.get("acciones_inmediatas") or []
        acciones_72h = plan.get("acciones_30_dias")    or remediation.get("acciones_30_dias")    or []
        acciones_7d  = plan.get("acciones_60_dias")    or remediation.get("acciones_60_dias")    or []

        remediation_available = bool(acciones_hoy or acciones_72h or acciones_7d)
        if not remediation_available:
            logger.warning("[EXECUTE] RemediationEngine no devolvio acciones trace_id=%s", trace_id)

        resultado = {
            "nivel":                 nivel,
            "score":                 round(omega_score, 1),
            "omega_score":           round(omega_score, 1),
            "esi":                   esi,
            "dias_supervivencia":    dias,
            "flujo_operativo":       flujo,
            "dscr":                  dscr,
            "war_room_required":     war_room,
            "exposure_mxn":          exposure,
            "alertas":               fiscal_res.get("alertas", []),
            "recomendaciones":       fiscal_res.get("recomendaciones", []),
            "compliance":            engine_data.get("compliance", {}),
            "acciones_hoy":          acciones_hoy,
            "acciones_72h":          acciones_72h,
            "acciones_7d":           acciones_7d,
            "remediation_available": remediation_available,
            "model_drift":           model_drift,
            "digital_sovereignty":   digital_sovereignty,
            "engine_errors":         engine_errors if engine_errors else None,
        }

        try:
            AuditLog().log(
                tenant_id=tenant.tenant_id,
                event_type="EXECUTION",
                payload={"trace_id": trace_id, "score": omega_score, "nivel": nivel},
            )
        except Exception as e:
            logger.warning("[EXECUTE] audit error: %s", e)

        try:
            invoice = BillingEngine().charge(
                tenant_id=tenant.tenant_id,
                operation="EXECUTION_DECISION",
                risk_score=omega_score,
            )
        except Exception as e:
            logger.warning("[EXECUTE] billing error: %s", e)
            class DummyInvoice:
                invoice_id = None
                tenant_id  = tenant.tenant_id
                amount     = 0
                currency   = "MXN"
                reason     = "billing_disabled"
            invoice = DummyInvoice()

        try:
            report = ExecutiveNarrativeGenerator().generar(resultado)
            if not report:
                report = summary or "Sin narrativa disponible."
        except Exception as e:
            logger.warning("[EXECUTE] narrative error: %s", e)
            report = summary or "Sin narrativa disponible."

        latency_ms = round((time.time() - started) * 1000, 2)
        logger.info(
            "[EXECUTE] completed trace_id=%s latency_ms=%s score=%s nivel=%s",
            trace_id, latency_ms, omega_score, nivel,
        )

        return {
            "status":     "success",
            "trace_id":   trace_id,
            "tenant_id":  tenant.tenant_id,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency_ms,
            "result":     resultado,
            "invoice":    _invoice_to_dict(invoice),
            "report":     report,
        }

    except Exception:
        logger.exception("[EXECUTE] pipeline failed trace_id=%s", trace_id)
        return JSONResponse(status_code=500, content={
            "status":   "error",
            "message":  "EXECUTION_TEMPORARILY_UNAVAILABLE",
            "trace_id": trace_id,
        })

@router.post('/execute/pdf')
async def execute_pdf(payload: ExecutePayload, request: Request):
    from utils.pdf_generator import generar_pdf_omega
    from fastapi.responses import Response
    started = time.time()
    trace_id = f'pdf-{int(started * 1000)}'
    omega_response = omega_orchestrator.ejecutar({
        'tenant_id': 'public_diagnostic', 'trace_id': trace_id,
        'empresa_nombre': payload.empresa, 'ingresos': payload.ingresos,
        'gastos': payload.gastos, 'nomina': payload.nomina,
        'deuda_mensual': payload.deuda_mensual, 'cartera_vencida': payload.cartera_vencida,
        'iva': payload.iva, 'isr_retenido': payload.isr_retenido,
        'empleados': payload.trabajadores, 'trabajadores': payload.trabajadores,
        'trabajadores_sin_imss': payload.trabajadores_sin_imss,
        'repse_vigente': not payload.repse_suspendido, 'opinion_sat': payload.opinion_sat,
        'opinion_imss': payload.opinion_imss, 'caja_disponible': 0.0,
        'empleados_criticos': 0, 'demandas_laborales': 0, 'rotacion_anual': 0.0, 'severance_estimado': 0.0
    })
    pdf_bytes = generar_pdf_omega(omega_response=omega_response, empresa=payload.empresa)
    return Response(content=pdf_bytes, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename=diagnostico_mesan_{trace_id}.pdf'})
