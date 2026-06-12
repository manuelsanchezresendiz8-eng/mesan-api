# routes/omega_routes.py -- MESAN Omega v1.1
"""
Omega Evaluate Endpoint Ω

POST /api/v1/omega/evaluate

Puente oficial entre cliente real y OmegaOrchestrator.
Primer endpoint que conecta datos reales con el pipeline completo.

Mantiene compatibilidad con:
    GET /health
    GET /api/v1/warroom/status

v1.1:
    - tenant_id inyectado desde JWT context al pipeline
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from schemas.omega_evaluation_request import OmegaEvaluationRequest
from schemas.omega_response           import OmegaResponse

logger = logging.getLogger("mesan.omega_routes")

router = APIRouter()


@router.post("/omega/evaluate", tags=["Omega"])
async def omega_evaluate(request: Request):
    """
    Evaluación empresarial completa MESAN Ω.

    Recibe datos de empresa → ejecuta pipeline completo → retorna OmegaResponse.

    Body (JSON):
        empresa_nombre*  str
        sector*          str
        empleados        int
        ingresos         float   (mensual)
        nomina           float   (mensual)
        gastos           float   (mensual)
        caja_disponible  float
        deuda_mensual    float
        ... (ver OmegaEvaluationRequest para campos completos)
    """
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={
            "error":     "INVALID_JSON",
            "message":   "El body debe ser JSON válido",
            "trace_id":  trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # ── Construir request desde body ──────────────────────────────────────
    try:
        eval_request = OmegaEvaluationRequest.from_dict({
            **body,
            "trace_id": body.get("trace_id", trace_id),
        })
    except Exception as exc:
        logger.error("[OmegaEvaluate] Error construyendo request: %s", exc)
        return JSONResponse(status_code=400, content={
            "error":     "REQUEST_BUILD_ERROR",
            "message":   str(exc),
            "trace_id":  trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # ── Validar campos obligatorios ───────────────────────────────────────
    errors = eval_request.validate()
    if errors:
        return JSONResponse(status_code=422, content={
            "error":     "VALIDATION_ERROR",
            "messages":  errors,
            "trace_id":  trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # ── Ejecutar pipeline Ω ───────────────────────────────────────────────
    try:
        container    = getattr(request.app.state, "container", None)
        orchestrator = getattr(request.app.state, "orchestrator", None)

        if not orchestrator:
            from services.omega_orchestrator import omega_orchestrator
            orchestrator = omega_orchestrator

        # Obtener circuitos abiertos del ObservabilityBus si está disponible
        open_circuits = 0
        try:
            from core.observability_bus import omega_bus
            open_circuits = omega_bus.traces.active_count()
        except Exception:
            pass

        # ── Fix v1.1: inyectar tenant_id desde JWT context ────────────────
        data = eval_request.to_orchestrator_dict()
        try:
            from core.auth.tenant_context import get_tenant
            tenant = get_tenant()
            if tenant and tenant.tenant_id:
                data["tenant_id"] = tenant.tenant_id
                logger.info("[OmegaEvaluate] tenant=%s trace=%s", tenant.tenant_id, trace_id)
        except Exception:
            pass  # tenant_id permanece como DEFAULT si falla

        result = orchestrator.ejecutar(data, open_circuits=open_circuits)

    except Exception as exc:
        logger.exception("[OmegaEvaluate] Pipeline error trace=%s: %s", trace_id, exc)
        return JSONResponse(status_code=500, content={
            "error":     "PIPELINE_ERROR",
            "message":   "Error en pipeline de evaluación MESAN Ω",
            "trace_id":  trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # ── Respuesta ─────────────────────────────────────────────────────────
    response_data = result.to_dict()
    return JSONResponse(
        status_code = 200,
        content     = response_data,
        headers     = {"X-Trace-Id": trace_id},
    )
