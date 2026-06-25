# routes/execution_routes.py -- MESAN Omega Execution Routes v2.0
"""
v2.0 — CAMBIO CRÍTICO:
    /execute ahora usa OmegaOrchestrator completo (9 motores) en lugar
    de instanciar FiscalSentinelEngine y ComplianceVerifyEngine directamente.

    Compatibilidad con landing actual mantenida — todos los campos del
    ExecutePayload siguen siendo los mismos. Los campos que el Orchestrator
    requiere y que la landing no envía usan defaults seguros (0/False/None).

    Fallbacks explícitos — cualquier fallo de motor queda en logs con
    nivel ERROR y el response incluye engine_errors visible al operador.
    Ningún score ficticio se presenta como diagnóstico real.

DIFF vs v1.8:
    - ELIMINADO: FiscalSentinelEngine() instanciado directamente
    - ELIMINADO: ComplianceVerifyEngine() instanciado directamente
    - ELIMINADO: score=72, nivel="ALTO" hardcodeados como fallback silencioso
    - ELIMINADO: acciones_hoy/72h/7d hardcodeadas
    - AGREGADO:  from services.omega_orchestrator import omega_orchestrator
    - AGREGADO:  data mapping completo hacia el Orchestrator
    - AGREGADO:  engine_errors en el response (trazabilidad de fallos)
    - AGREGADO:  dias_supervivencia calculado desde ESI real (no 18/45/90 fijos)
    - AGREGADO:  dscr corregido cuando deuda == 0
    - AGREGADO:  acciones desde RemediationEngine via Orchestrator
"""

import os
import time
import logging
import traceback

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.auth.tenant_context import get_tenant, set_tenant
from core.auth.tenant_model   import Tenant
from core.auth.audit_log      import AuditLog
from core.billing.billing_engine import BillingEngine

from services.executive_narrative_generator import ExecutiveNarrativeGenerator
from services.omega_orchestrator            import omega_orchestrator
from core.rate_limiter                      import rate_limit_check

router = APIRouter()
logger = logging.getLogger("mesan.execute")
ENV    = os.getenv("ENV", "development").lower()


# ── Payload ───────────────────────────────────────────────────────────────────
# Mantiene compatibilidad total con el formulario de la landing actual.
# Campos nuevos que el Orchestrator necesita se resuelven con defaults seguros.

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


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/execute")
async def execute(payload: ExecutePayload, request: Request):

    started  = time.time()
    trace_id = f"exec-{int(started * 1000)}"

    logger.info("[EXECUTE] request received trace_id=%s", trace_id)

    # Rate limiting: 3 diagnosticos/IP cada 5 minutos.
    # Mas estricto que /api/leads (5/60s) porque cada ejecucion
    # consume recursos significativos del Orchestrator (9 motores).
    rate_limit_check(request, key="execute_diagnostico", max_requests=3, window_seconds=300)

    # ── Tenant ────────────────────────────────────────────────────────────────
    tenant = get_tenant()

    if not tenant:
        if ENV != "production":
            set_tenant(Tenant(tenant_id="demo", name="DEMO_TENANT", plan="FREE"))
            tenant = get_tenant()
        else:
            return JSONResponse(status_code=401, content={
                "status":   "error",
                "message":  "TENANT_MISSING",
                "trace_id": trace_id,
            })

    try:
        # ── Mapeo de payload → Orchestrator ──────────────────────────────────
        # Los campos que la landing no envía usan defaults seguros documentados.
        data = {
            # Identidad
            "tenant_id":    tenant.tenant_id,
            "trace_id":     trace_id,
            "empresa_nombre": payload.empresa,

            # Financieros — enviados por la landing
            "ingresos":         payload.ingresos,
            "gastos":           payload.gastos,
            "nomina":           payload.nomina,
            "deuda_mensual":    payload.deuda_mensual,
            "cartera_vencida":  payload.cartera_vencida,
            "iva":              payload.iva,
            "isr_retenido":     payload.isr_retenido,

            # Laborales — enviados por la landing
            "empleados":              payload.trabajadores,
            "trabajadores":           payload.trabajadores,         # alias fiscal
            "trabajadores_sin_imss":  payload.trabajadores_sin_imss,

            # Regulatorios — enviados por la landing
            "repse_vigente":     not payload.repse_suspendido,
            "repse_suspendido":  payload.repse_suspendido,
            "bloqueo_bancario":  payload.bloqueo_bancario,
            "opinion_sat":       payload.opinion_sat,
            "opinion_imss":      payload.opinion_imss,

            # Campos requeridos por ContinuityEngine — defaults seguros
            # (no disponibles en landing v1; se ampliarán en Fase 2 del form)
            "caja_disponible":       0.0,    # TODO Fase 2: agregar al formulario
            "empleados_criticos":    0,      # TODO Fase 2
            "demandas_laborales":    0,      # TODO Fase 2
            "rotacion_anual":        0.0,    # TODO Fase 2
            "severance_estimado":    0.0,    # TODO Fase 2
        }

        # ── OmegaOrchestrator — 9 motores ─────────────────────────────────
        logger.info("[EXECUTE] invoking OmegaOrchestrator trace_id=%s", trace_id)

        omega_response = omega_orchestrator.ejecutar(data)

        # ── Extraer resultados del OmegaResponse ──────────────────────────
        # OmegaResponse es un objeto con atributos; extraemos lo necesario
        # con getattr(..., default) para no romper si el schema cambia.

        omega_score = getattr(omega_response, "omega_score",        None)
        esi         = getattr(omega_response, "enterprise_survival_index", None)
        war_room    = getattr(omega_response, "war_room_required",  False)
        exposure    = getattr(omega_response, "total_exposure_mxn", 0.0)
        engine_data = getattr(omega_response, "engines",            {})
        remediation = getattr(omega_response, "remediation",        {})
        summary     = getattr(omega_response, "executive_summary",        "")
        model_drift = getattr(omega_response, "model_drift",        {})

        # Detectar motores que fallaron (trazabilidad explícita)
        engine_errors = {
            name: res.get("error")
            for name, res in (engine_data or {}).items()
            if isinstance(res, dict) and "error" in res
        }
        if engine_errors:
            logger.error(
                "[EXECUTE] engine_errors trace_id=%s errors=%s",
                trace_id, engine_errors,
            )

        # ── Score y nivel desde Orchestrator ──────────────────────────────
        # Si omega_score es None (fallo total del pipeline), devolvemos error
        # explícito — nunca un score ficticio.
        if omega_score is None:
            logger.error(
                "[EXECUTE] omega_score is None — pipeline failure trace_id=%s",
                trace_id,
            )
            return JSONResponse(status_code=500, content={
                "status":        "error",
                "message":       "OMEGA_PIPELINE_FAILURE",
                "trace_id":      trace_id,
                "engine_errors": engine_errors,
            })

        # Nivel desde omega_score (escala de salud: 100 = perfecto, 0 = crítico)
        if omega_score >= 80:   nivel = "BAJO"
        elif omega_score >= 65: nivel = "MEDIO"
        elif omega_score >= 50: nivel = "ALTO"
        elif omega_score >= 35: nivel = "CRITICO"
        else:                   nivel = "EXTREMO"

        # ── Flujo operativo desde FiscalSentinel ──────────────────────────
        fiscal_data  = engine_data.get("fiscal", {})
        fiscal_res   = fiscal_data.get("resultado", fiscal_data)
        flujo        = fiscal_res.get("flujo_operativo", payload.ingresos - payload.gastos - payload.deuda_mensual)

        # ── Días de supervivencia desde ESI real ──────────────────────────
        # ESI es Enterprise Survival Index 0-100.
        # En lugar de 3 buckets fijos (18/45/90), lo derivamos del ESI real.
        if esi is None:
            dias = 30   # default conservador si ESI no disponible
        elif esi >= 90: dias = 180
        elif esi >= 80: dias = 120
        elif esi >= 70: dias = 90
        elif esi >= 60: dias = 60
        elif esi >= 45: dias = 30
        else:           dias = 15

        # ── DSCR corregido ────────────────────────────────────────────────
        # Cuando deuda == 0: DSCR es técnicamente ∞ (sin presión de deuda).
        # Se representa como None para que el frontend lo muestre como "N/A".
        deuda = payload.deuda_mensual
        if deuda <= 0:
            dscr = None   # sin deuda = sin ratio de cobertura aplicable
        elif flujo is not None:
            dscr = round(flujo / deuda, 2)
        else:
            dscr = None

        # ── Acciones desde RemediationEngine (via Orchestrator) ───────────
        # Si el RemediationEngine devolvió acciones, las usamos.
        # Si no, el response lo indica explícitamente — sin hardcode.
        acciones_hoy = (
            remediation.get("acciones_inmediatas") or
            remediation.get("acciones_hoy")        or
            []
        )
        acciones_72h = (
            remediation.get("acciones_30_dias") or
            remediation.get("acciones_72h")     or
            []
        )
        acciones_7d = (
            remediation.get("acciones_60_dias") or
            remediation.get("acciones_7d")      or
            []
        )

        remediation_available = bool(acciones_hoy or acciones_72h or acciones_7d)
        if not remediation_available:
            logger.warning(
                "[EXECUTE] RemediationEngine did not return actions trace_id=%s "
                "remediation=%s", trace_id, remediation,
            )

        # ── Compliance desde Orchestrator ─────────────────────────────────
        compliance_data = engine_data.get("compliance", {})

        # ── Resultado consolidado ─────────────────────────────────────────
        resultado = {
            "nivel":              nivel,
            "score":              round(omega_score, 1),
            "omega_score":        round(omega_score, 1),
            "esi":                esi,
            "dias_supervivencia": dias,
            "flujo_operativo":    flujo,
            "dscr":               dscr,
            "war_room_required":  war_room,
            "exposure_mxn":       exposure,
            "alertas":            fiscal_res.get("alertas", []),
            "recomendaciones":    fiscal_res.get("recomendaciones", []),
            "compliance":         compliance_data,
            "acciones_hoy":       acciones_hoy,
            "acciones_72h":       acciones_72h,
            "acciones_7d":        acciones_7d,
            "remediation_available": remediation_available,
            "model_drift":        model_drift,
            "engine_errors":      engine_errors if engine_errors else None,
        }

        # ── Audit ─────────────────────────────────────────────────────────
        try:
            AuditLog().log(
                tenant_id=tenant.tenant_id,
                event_type="EXECUTION",
                payload={"trace_id": trace_id, "score": omega_score, "nivel": nivel},
            )
        except Exception as e:
            logger.warning("[EXECUTE] audit error: %s", e)

        # ── Billing ───────────────────────────────────────────────────────
        try:
            invoice = BillingEngine().charge(
                tenant_id=tenant.tenant_id,
                operation="EXECUTION_DECISION",
                risk_score=omega_score,
            )
        except Exception as e:
            logger.warning("[EXECUTE] billing error: %s", e)
            class DummyInvoice:
                amount   = 0
                currency = "MXN"
                reason   = "billing_disabled"
            invoice = DummyInvoice()

        # ── Narrative CEO IA ──────────────────────────────────────────────
        # ExecutiveNarrativeGenerator usa el resultado consolidado que ya
        # incluye acciones reales del RemediationEngine.
        try:
            report = ExecutiveNarrativeGenerator().generar(resultado)
            if not report:
                report = summary or "Sin narrativa disponible."
        except Exception as e:
            logger.warning("[EXECUTE] narrative error: %s", e)
            report = summary or "Sin narrativa disponible."

        # ── Response ──────────────────────────────────────────────────────
        latency_ms = round((time.time() - started) * 1000, 2)

        logger.info(
            "[EXECUTE] completed trace_id=%s latency_ms=%s score=%s nivel=%s",
            trace_id, latency_ms, omega_score, nivel,
        )

        return {
            "status":    "success",
            "trace_id":  trace_id,
            "tenant_id": tenant.tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency_ms,
            "result":    resultado,
            "invoice": {
                "amount":   invoice.amount,
                "currency": invoice.currency,
                "reason":   invoice.reason,
            },
            "report": report,
        }

    except Exception:
        logger.exception("[EXECUTE] pipeline failed trace_id=%s", trace_id)
        return JSONResponse(status_code=500, content={
            "status":   "error",
            "message":  "EXECUTION_TEMPORARILY_UNAVAILABLE",
            "trace_id": trace_id,
        })
