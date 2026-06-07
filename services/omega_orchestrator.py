# services/omega_orchestrator.py -- MESAN Omega v1.2
"""
Omega Orchestrator Ω

Convierte múltiples engines independientes en una única evaluación empresarial.

Pipeline v1.1:
    FASE A (paralelo):
    ↓ ComplianceVerifyEngine  [secuencial — alimenta validaciones]
    ↓ FiscalSentinelEngine    [paralelo]
    ↓ LaborShieldEngine       [paralelo]
    ↓ ContractualRiskEngine   [paralelo]
    ↓ PolicyAuditEngine       [paralelo]

    FASE B (secuencial):
    ↓ ExposureAggregator      [consolida exposición]
    ↓ GovernanceEngine        [recibe exposición real]
    ↓ ContinuityEngine        [ESI-Ω oficial — única fuente]
    ↓ WarRoomEngine           [decisión central]
    ↓ RemediationEngine
    ↓ ExecutiveNarrativeGenerator
    OUTPUT → OmegaResponse

Ningún endpoint debe consumir engines directamente.
Todo pasa por el Orchestrator.
"""

import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.score_normalizer    import score_normalizer
from services.exposure_aggregator import exposure_aggregator, ExposureAggregator
from services.war_room_engine     import war_room_engine, WarRoomEngine
from schemas.omega_response       import OmegaResponse, OmegaResponseBuilder

logger = logging.getLogger("mesan.orchestrator")

ORCHESTRATOR_VERSION = "1.2"


# ══════════════════════════════════════════════════════════════════════════════
# NARRATIVE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class ExecutiveNarrativeGenerator:
    """
    Genera narrativa ejecutiva consolidada para CEO y Consejo.
    Basada en el resultado completo del pipeline — no en un solo engine.
    """

    def generate(
        self,
        omega_score:    int,
        esi:            int,
        governance:     float,
        war_room:       bool,
        exposure:       float,
        sales_priority: str,
        tenant_id:      str = "DEFAULT",
    ) -> str:
        clasificacion = self._classify(esi)
        urgencia      = "intervención inmediata" if war_room else "monitoreo preventivo"

        return (
            f"MESAN Ω detectó un Enterprise Survival Index de {esi}/100 "
            f"({clasificacion}) con un Governance Score de {governance:.0f}/100. "
            f"La exposición financiera consolidada asciende a ${exposure:,.0f} MXN. "
            f"El sistema recomienda {urgencia}. "
            f"Prioridad comercial: {sales_priority}."
        )

    @staticmethod
    def _classify(esi: int) -> str:
        if esi >= 90: return "ROBUSTA"
        if esi >= 80: return "ESTABLE"
        if esi >= 70: return "VIGILANCIA"
        if esi >= 60: return "RIESGO ELEVADO"
        return "CRÍTICA"


# ══════════════════════════════════════════════════════════════════════════════
# OMEGA ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

class OmegaOrchestrator:
    """
    Orquestador central de MESAN Ω.

    Ejecuta el pipeline completo y retorna OmegaResponse.

    Uso:
        orchestrator = OmegaOrchestrator()
        response = orchestrator.ejecutar(data)
        print(response.to_dict())
    """

    def __init__(self):
        self._narrative  = ExecutiveNarrativeGenerator()
        self._normalizer = score_normalizer
        self._exposure   = exposure_aggregator
        self._war_room   = war_room_engine

        # Engines — lazy import para evitar circularidades
        self._engines_loaded = False

    def _load_engines(self):
        if self._engines_loaded:
            return
        from services.compliance_verify_engine  import ComplianceVerifyEngine
        from services.fiscal_sentinel_engine    import FiscalSentinelEngine
        from services.labor_shield_engine       import LaborShieldEngine
        from services.contractual_risk_engine   import ContractualRiskEngine
        from services.policy_audit_engine       import PolicyAuditEngine
        from services.governance_engine         import GovernanceEngine
        from services.remediation_engine        import RemediationEngine
        from services.continuity_engine         import ContinuityEngine, Empresa

        self._compliance  = ComplianceVerifyEngine()
        self._fiscal      = FiscalSentinelEngine()
        self._labor       = LaborShieldEngine()
        self._contractual = ContractualRiskEngine()
        self._policy      = PolicyAuditEngine()
        self._governance  = GovernanceEngine()
        self._remediation = RemediationEngine()
        self._continuity  = ContinuityEngine()
        self._Empresa     = Empresa

        self._engines_loaded = True

    # ── Pipeline principal ────────────────────────────────────────────────────

    def ejecutar(
        self,
        data:          Dict[str, Any],
        open_circuits: int = 0,
    ) -> OmegaResponse:
        """
        Ejecuta el pipeline completo de evaluación empresarial.

        Args:
            data:          Datos de la empresa (dict con todos los campos)
            open_circuits: Circuitos abiertos del ObservabilityBus (opcional)

        Returns:
            OmegaResponse con evaluación consolidada
        """
        started   = time.time()
        self._load_engines()

        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  str(uuid.uuid4()))

        logger.info("[Orchestrator] Iniciando pipeline tenant=%s trace=%s",
                    tenant_id, trace_id[:8])

        # ── Paso 1: Ejecutar engines individuales ─────────────────────────
        pipeline = self._run_pipeline(data, tenant_id, trace_id)

        # ── Paso 2: Normalizar scores ─────────────────────────────────────
        normalized = self._normalizer.normalize_all(pipeline)
        omega_score = self._normalizer.omega_health_score(
            normalized,
            weights={
                "compliance":  0.15,
                "fiscal":      0.20,
                "labor":       0.20,
                "contractual": 0.15,
                "policy":      0.10,
                "governance":  0.20,
            }
        )

        # ── Paso 3: Exposición consolidada (reutiliza cálculo de _run_pipeline) ──
        # Fix P1: evita doble ejecución del aggregator
        exposure_result = pipeline.pop("_exposure", None)             or self._exposure.aggregate_from_pipeline(pipeline)
        sales_priority  = ExposureAggregator.classify_sales_priority(
            exposure_result.total
        )

        # ── Paso 4: ESI-Ω oficial ─────────────────────────────────────────
        esi_result   = pipeline.get("survival", {})
        esi          = esi_result.get("enterprise_survival_index", 0)
        horizon      = esi_result.get("continuity_horizon", {
            "12_months": 0, "24_months": 0, "36_months": 0
        })
        governance_score = float(
            pipeline.get("governance", {}).get("governance_score", 0)
        )

        # ── Paso 5: War Room ──────────────────────────────────────────────
        war_signals  = WarRoomEngine.build_signals(
            pipeline_results          = pipeline,
            enterprise_survival_index = esi,
            total_exposure_mxn        = exposure_result.total,
            open_circuits             = open_circuits,
        )
        war_result = self._war_room.evaluate(war_signals)

        # ── Paso 6: Remediación ───────────────────────────────────────────
        remediation_input = {
            "tenant_id":              tenant_id,
            "trace_id":               trace_id,
            "nivel":                  pipeline.get("governance", {}).get("nivel", "MEDIO"),
            "score":                  omega_score,
            "exposicion_estimada_mxn": exposure_result.total,
            "critical_findings_count": war_signals.critical_findings_count,
            "war_room_required":       war_result.required,
            "alertas": self._collect_alerts(pipeline),
        }
        remediation_result = self._remediation.generar_plan(remediation_input)

        # ── Paso 7: Narrativa ejecutiva ───────────────────────────────────
        narrative = self._narrative.generate(
            omega_score    = omega_score,
            esi            = esi,
            governance     = governance_score,
            war_room       = war_result.required,
            exposure       = exposure_result.total,
            sales_priority = sales_priority,
            tenant_id      = tenant_id,
        )

        # ── Paso 8: Construir respuesta ───────────────────────────────────
        latency_ms = round((time.time() - started) * 1000, 2)
        logger.info(
            "[Orchestrator] Pipeline completado tenant=%s esi=%s omega=%s latency=%sms",
            tenant_id, esi, omega_score, latency_ms,
        )

        exposure_dict = exposure_result.to_dict()
        exposure_dict["sales_priority"] = sales_priority

        response = (
            OmegaResponseBuilder(tenant_id=tenant_id, trace_id=trace_id)
            .set_scores(omega_score, esi, governance_score, horizon)
            .set_war_room(war_result)
            .set_exposure(exposure_dict)
            .set_engines(pipeline)
            .set_remediation(remediation_result)
            .set_summary(narrative)
            .build()
        )

        return response

    # ── Ejecución del pipeline de engines ─────────────────────────────────────

    def _run_pipeline(
        self,
        data:      dict,
        tenant_id: str,
        trace_id:  str,
    ) -> dict:
        """
        Pipeline v1.1 — dos fases.

        FASE A — Paralelo:
            Compliance (secuencial, primero) + Fiscal/Labor/Contractual/Policy (paralelo)

        FASE B — Secuencial:
            ExposureAggregator → Governance (con exposición real) → ContinuityEngine (ESI oficial)
        """
        ctx     = {**data, "tenant_id": tenant_id, "trace_id": trace_id}
        results = {}

        # ── FASE A.1 — Compliance primero (alimenta validaciones) ─────────
        results["compliance"] = self._safe_run(
            "compliance", self._compliance.calcular_score,
            ctx.get("repse_vigente", True),
            ctx.get("opinion_sat",  "POSITIVA"),
            ctx.get("opinion_imss", "POSITIVA"),
            tenant_id, trace_id,
        )

        # ── FASE A.2 — Paralelo: Fiscal, Labor, Contractual, Policy ───────
        parallel_tasks = {
            "fiscal":      (self._fiscal.analizar,      ctx),
            "labor":       (self._labor.analizar,        ctx),
            "contractual": (self._contractual.analizar,  ctx),
            "policy":      (self._policy.auditar,        ctx),
        }

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._safe_run, name, fn, arg): name
                for name, (fn, arg) in parallel_tasks.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as exc:
                    logger.error("[Orchestrator] Futuro '%s' falló: %s", name, exc)
                    results[name] = {"engine": name, "engine_status": "ERROR", "error": str(exc)}

        # ── FASE B.1 — Exposición consolidada (Corrección #2) ─────────────
        # ExposureAggregator ANTES de Governance para que reciba exposición real
        partial_exposure = self._exposure.aggregate_from_pipeline(results)
        results["_exposure"] = partial_exposure   # guardado para reutilizar en ejecutar()

        # ── FASE B.2 — Governance con exposición real ──────────────────────
        governance_input = {
            **ctx,
            "score_fiscal":      self._extract_score(results.get("fiscal"),      "fiscal"),
            "score_compliance":  self._extract_score(results.get("compliance"),  "compliance"),
            "score_laboral":     self._extract_score(results.get("labor"),       "labor"),
            "score_contractual": self._extract_score(results.get("contractual"), "contractual"),
            "score_financiero":  100,   # TODO Sprint 4: Financial Intelligence Engine
            "exposicion_total":  partial_exposure.total,   # ← exposición real (Corrección #2)
        }
        results["governance"] = self._safe_run(
            "governance", self._governance.calcular, governance_input
        )

        # ── FASE B.3 — ESI-Ω oficial desde ContinuityEngine ───────────────
        # Única fuente de enterprise_survival_index (Corrección #1)
        empresa = self._build_empresa(ctx)
        if empresa:
            results["survival"] = self._safe_run(
                "survival",
                self._continuity.calcular_esi,
                empresa,
            )
        else:
            results["survival"] = {"enterprise_survival_index": 0, "esi": 0, "engine_status": "ERROR", "error": "No se pudo construir Empresa para ContinuityEngine"}

        return results

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _safe_run(self, name: str, fn, *args, **kwargs) -> dict:
        """Ejecuta un engine capturando excepciones sin detener el pipeline."""
        try:
            return fn(*args, **kwargs) or {}
        except Exception as exc:
            logger.error("[Orchestrator] Engine '%s' falló: %s", name, exc)
            return {"engine": name, "engine_status": "ERROR", "error": str(exc)}

    def _extract_score(self, result: Optional[dict], engine_key: str) -> float:
        """Extrae health_score normalizado de un resultado de engine."""
        if not result:
            return 100.0
        normalized = self._normalizer.normalize_engine_result(result)
        return float(normalized.health_score)

    def _build_empresa(self, data: dict):
        """Construye Empresa para ContinuityEngine desde el input del Orchestrator."""
        try:
            return self._Empresa(
                nombre                = data.get("empresa_nombre", "Empresa"),
                ingresos_mensuales    = float(data.get("ingresos",           0)),
                nomina_mensual        = float(data.get("nomina",             0)),
                empleados             = int(data.get("empleados",            0)),
                empleados_criticos    = int(data.get("empleados_criticos",   0)),
                caja_disponible       = float(data.get("caja_disponible",    0)),
                deuda_mensual         = float(data.get("deuda_mensual",      0)),
                demandas_laborales    = int(data.get("demandas_laborales",   0)),
                trabajadores_sin_imss = int(data.get("trabajadores_sin_imss",0)),
                rotacion_anual        = float(data.get("rotacion_anual",     0)),
                severance_estimado    = float(data.get("severance_estimado", 0)),
                riesgo_sat            = str(data.get("opinion_sat",   "POSITIVO")),
                riesgo_imss           = str(data.get("opinion_imss",  "POSITIVO")),
                repse_suspendido      = not bool(data.get("repse_vigente", True)),
            )
        except Exception as exc:
            logger.warning("[Orchestrator] No se pudo construir Empresa: %s", exc)
            return None

    def _collect_alerts(self, pipeline: dict) -> list:
        """Colecta alertas de todos los engines para el RemediationEngine."""
        alerts = []
        for result in pipeline.values():
            if not isinstance(result, dict):
                continue
            engine_alerts = result.get("alertas", result.get("riesgos", []))
            if isinstance(engine_alerts, list):
                alerts.extend(engine_alerts)
        return alerts


# Instancia global
omega_orchestrator = OmegaOrchestrator()
