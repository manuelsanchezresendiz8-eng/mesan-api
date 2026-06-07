# services/omega_orchestrator.py -- MESAN Omega v1.5.0

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, Optional

from services.score_normalizer    import score_normalizer
from services.exposure_aggregator import exposure_aggregator, ExposureAggregator
from services.war_room_engine     import war_room_engine, WarRoomEngine
from schemas.omega_response       import OmegaResponse, OmegaResponseBuilder

logger = logging.getLogger("mesan.orchestrator")

ORCHESTRATOR_VERSION = "1.5.0"


class OmegaOrchestrator:

    def __init__(self):
        self._narrative      = None
        self._normalizer     = score_normalizer
        self._exposure       = exposure_aggregator
        self._war_room       = war_room_engine
        self._engines_loaded = False
        self._load_lock      = threading.Lock()   # Fix P0-A2: thread-safe init

    def _load_engines(self):
        if self._engines_loaded:
            return
        with self._load_lock:          # Fix P0-A2: double-checked locking
            if self._engines_loaded:
                return

        from services.compliance_verify_engine          import ComplianceVerifyEngine
        from services.fiscal_sentinel_engine            import FiscalSentinelEngine
        from services.labor_shield_engine               import LaborShieldEngine
        from services.contractual_risk_engine           import ContractualRiskEngine
        from services.policy_audit_engine               import PolicyAuditEngine
        from services.governance_engine                 import GovernanceEngine
        from services.remediation_engine                import RemediationEngine
        from services.continuity_engine                 import ContinuityEngine, Empresa
        from services.financial_intelligence_engine     import FinancialIntelligenceEngine
        from services.financial_intelligence_engine_v2  import FinancialIntelligenceEngineV2

        self._compliance   = ComplianceVerifyEngine()
        self._fiscal       = FiscalSentinelEngine()
        self._labor        = LaborShieldEngine()
        self._contractual  = ContractualRiskEngine()
        self._policy       = PolicyAuditEngine()
        self._governance   = GovernanceEngine()
        self._remediation  = RemediationEngine()
        self._continuity   = ContinuityEngine()
        self._financial    = FinancialIntelligenceEngine()
        self._financial_v2 = FinancialIntelligenceEngineV2(shadow_mode=True)
        self._Empresa      = Empresa

        self._engines_loaded = True

    def ejecutar(self, data: Dict[str, Any], open_circuits: int = 0) -> OmegaResponse:

        start     = time.time()
        self._load_engines()

        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  str(uuid.uuid4()))

        pipeline = self._run_pipeline(data, tenant_id, trace_id)

        # Fix: excluir claves internas del pipeline antes de normalizar
        pipeline_engines = {k: v for k, v in pipeline.items()
                            if not k.startswith("_")}
        normalized  = self._normalizer.normalize_all(pipeline_engines)
        omega_score = self._normalizer.omega_health_score(
            normalized,
            weights={
                "compliance":  0.10,
                "fiscal":      0.15,
                "labor":       0.15,
                "contractual": 0.10,
                "policy":      0.10,
                "governance":  0.20,
                "financial":   0.20,   # Fix P1-A4: financial incluido (suma=1.0)
            },
        )

        # ── Financial shadow drift ────────────────────────────────────────
        v1 = self._extract_financial_score(pipeline.get("financial"))
        v2 = pipeline.get("financial_v2", {}).get("financial_score_v2")

        drift       = None
        drift_pct   = None
        drift_level = "UNKNOWN"
        try:
            if v1 is not None and v2 is not None:
                drift       = round(abs(float(v1) - float(v2)), 2)
                drift_pct   = round((drift / float(v1)) * 100, 2) if float(v1) > 0 else None  # Fix P1-D1
                drift_level = "OK" if drift < 5 else "WARNING" if drift < 15 else "CRITICAL"
        except Exception:
            pass

        model_drift = {
            "v1_score":    v1,
            "v2_score":    v2,
            "drift":       drift,
            "drift_pct":   drift_pct,
            "drift_level": drift_level,
        }

        logger.info("[DRIFT] tenant=%s v1=%s v2=%s drift=%s level=%s",
                    tenant_id, v1, v2, drift, drift_level)

        # ── Exposición + ESI + War Room ───────────────────────────────────
        exposure_result = pipeline.get("_exposure") \
            or self._exposure.aggregate_from_pipeline(pipeline)
        total_exposure  = self._get_exposure_total(exposure_result)
        sales_priority  = ExposureAggregator.classify_sales_priority(total_exposure)

        esi = pipeline.get("survival", {}).get("enterprise_survival_index", 0)

        # Fix P1: WarRoom protegido — si falla, pipeline no cae
        try:
            war_signals = WarRoomEngine.build_signals(
                pipeline, esi, total_exposure, open_circuits,
            )
            war_result = self._war_room.evaluate(war_signals)
        except Exception as e:
            logger.critical("[WarRoom] FAILED — escalamiento conservador aplicado: %s", e)
            from war_room_engine import WarRoomResult, WarRoomSignals
            war_result = WarRoomResult(
                required = True,    # Fix P0-E1: conservador — ante duda, escalar
                score    = 50,
                priority = "48H",
                reasons  = [f"WarRoom evaluation failed — conservative escalation: {str(e)}"],
                signals  = WarRoomSignals(),
            )

        # ── Fix 2: Restaurar continuity_horizon ─────────────────────────────
        horizon = pipeline.get("survival", {}).get("continuity_horizon", {
            "12_months": 0, "24_months": 0, "36_months": 0,
        })

        # ── Fix 1: Restaurar RemediationEngine ───────────────────────────
        remediation_input = {
            "tenant_id":               tenant_id,
            "trace_id":                trace_id,
            "nivel":                   self._esi_to_remediation_nivel(esi),  # Fix P1-F1
            "score":                   omega_score,
            "exposicion_estimada_mxn": total_exposure,
            "critical_findings_count": war_signals.critical_findings_count,
            "war_room_required":       war_result.required,
            "alertas":                 self._collect_alerts(pipeline),
        }
        try:
            remediation_result = self._remediation.generar_plan(remediation_input)
        except Exception as e:
            logger.error("[Orchestrator] Remediation failed: %s", e)
            remediation_result = {}

        # ── Fix 3: Restaurar ExecutiveNarrativeGenerator ──────────────────
        narrative = self._generate_narrative(
            omega_score    = omega_score,
            esi            = esi,
            governance     = float(pipeline.get("governance", {}).get("governance_score", 0)),
            war_room       = war_result.required,
            exposure       = total_exposure,
            sales_priority = sales_priority,
        )

        # Fix P2: dual contract seguro — sin dict() sobre objetos arbitrarios
        if hasattr(exposure_result, "to_dict"):
            exposure_dict = exposure_result.to_dict()
        elif isinstance(exposure_result, dict):
            exposure_dict = exposure_result.copy()
        else:
            logger.warning("[Orchestrator] ExposureResult tipo inesperado: %s", type(exposure_result))
            exposure_dict = {"total_exposure_mxn": total_exposure,
                             "fiscal": 0, "labor": 0, "contractual": 0, "policy": 0}
        exposure_dict["sales_priority"] = sales_priority

        response = (
            OmegaResponseBuilder(tenant_id=tenant_id, trace_id=trace_id)
            .set_scores(omega_score, esi,
                        float(pipeline.get("governance", {}).get("governance_score", 0)),
                        horizon)
            .set_war_room(war_result)
            .set_exposure(exposure_dict)
            .set_engines(pipeline)
            .set_remediation(remediation_result)
            .set_summary(narrative)
            .set_model_drift(model_drift)
            .build()
        )

        return response

    def _run_pipeline(self, data: dict, tenant_id: str, trace_id: str) -> dict:
        ctx     = {**data, "tenant_id": tenant_id, "trace_id": trace_id}
        results = {}

        # ── FASE A: Compliance primero ────────────────────────────────────
        try:
            results["compliance"] = self._compliance.calcular_score(
                ctx.get("repse_vigente", True),
                ctx.get("opinion_sat",   "POSITIVA"),
                ctx.get("opinion_imss",  "POSITIVA"),
                tenant_id, trace_id,
            )
        except Exception as e:
            results["compliance"] = {"engine": "compliance", "error": str(e)}

        # ── FASE A: Paralelo ──────────────────────────────────────────────
        parallel = {
            "financial":    self._financial.analizar,
            "financial_v2": self._financial_v2.analizar,
            "fiscal":       self._fiscal.analizar,
            "labor":        self._labor.analizar,
            "contractual":  self._contractual.analizar,
            "policy":       self._policy.auditar,
        }

        with ThreadPoolExecutor(max_workers=len(parallel)) as ex:
            futures = {ex.submit(fn, ctx): name for name, fn in parallel.items()}
            try:
                for f in as_completed(futures, timeout=15):  # Fix P0-A1: timeout 15s
                    name = futures[f]
                    try:
                        results[name] = f.result()
                    except Exception as e:
                        results[name] = {"engine": name, "error": str(e)}
            except FuturesTimeoutError:
                logger.error("[Orchestrator] Pipeline timeout — engines lentos: %s",
                             [n for fut, n in futures.items() if not fut.done()])
                for fut, name in futures.items():
                    if not fut.done():
                        results[name] = {"engine": name, "error": "timeout"}

        # ── FASE B: Exposure → Governance → ESI ──────────────────────────
        results["_exposure"] = self._exposure.aggregate_from_pipeline(results)

        governance_input = {
            **ctx,
            "score_fiscal":      self._extract_score(results.get("fiscal")),
            "score_compliance":  self._extract_score(results.get("compliance")),
            "score_laboral":     self._extract_score(results.get("labor")),
            "score_contractual": self._extract_score(results.get("contractual")),
            "score_financiero":  self._extract_score(results.get("financial")),
            "exposicion_total":  self._get_exposure_total(results["_exposure"]),
        }
        try:
            results["governance"] = self._governance.calcular(governance_input)
        except Exception as e:
            results["governance"] = {"engine": "governance", "error": str(e)}

        empresa = self._build_empresa(ctx)
        if empresa:
            try:
                results["survival"] = self._continuity.calcular_esi(empresa)
            except Exception as e:
                results["survival"] = {"enterprise_survival_index": 0, "error": str(e)}
        else:
            results["survival"] = {"enterprise_survival_index": 0, "error": "build_empresa_failed"}

        return results

    def _get_exposure_total(self, exposure) -> float:
        """Fix 2: contrato dual — ExposureResult.total o dict total_exposure_mxn."""
        if hasattr(exposure, "total"):
            return exposure.total
        if isinstance(exposure, dict):
            return exposure.get("total_exposure_mxn", 0.0)
        return 0.0

    def _extract_financial_score(self, r: Optional[dict]) -> Optional[float]:
        """Fix: or-chain falla si score=0. Usar búsqueda por key explícita."""
        if not r:
            return None
        for key in ("financial_score", "score", "financial_score_v1"):
            if key in r:
                return r[key]
        return None

    def _extract_score(self, result: Optional[dict]) -> float:
        if not result:
            return 100.0
        ns = self._normalizer.normalize_engine_result(result)
        return float(ns.health_score)

    def _esi_to_remediation_nivel(self, esi: int) -> str:
        """Fix P1-F1: usar ESI (escala estándar) en lugar de governance.nivel."""
        if esi >= 80: return "BAJO"
        if esi >= 70: return "MEDIO"
        if esi >= 60: return "ALTO"
        if esi >= 40: return "CRITICO"
        return "EXTREMO"

    def _generate_narrative(self, omega_score, esi, governance, war_room, exposure, sales_priority) -> str:
        clasificacion = (
            "ROBUSTA"       if esi >= 90 else
            "ESTABLE"       if esi >= 80 else
            "VIGILANCIA"    if esi >= 70 else
            "RIESGO ELEVADO" if esi >= 60 else
            "CRÍTICA"
        )
        urgencia = "intervención inmediata" if war_room else "monitoreo preventivo"
        return (
            f"MESAN Ω detectó un Enterprise Survival Index de {esi}/100 "
            f"({clasificacion}) con un Governance Score de {governance:.0f}/100. "
            f"La exposición financiera consolidada asciende a ${exposure:,.0f} MXN. "
            f"El sistema recomienda {urgencia}. "
            f"Prioridad comercial: {sales_priority}."
        )

    def _collect_alerts(self, pipeline: dict) -> list:
        alerts = []
        for result in pipeline.values():
            if not isinstance(result, dict):
                continue
            for key in ("alertas", "riesgos"):
                items = result.get(key, [])
                if isinstance(items, list):
                    alerts.extend(items)
        return alerts

    def _build_empresa(self, data: dict):
        try:
            return self._Empresa(
                nombre                = data.get("empresa_nombre", "Empresa"),
                ingresos_mensuales    = float(data.get("ingresos",            0)),
                nomina_mensual        = float(data.get("nomina",              0)),
                empleados             = int(data.get("empleados",             0)),
                empleados_criticos    = int(data.get("empleados_criticos",    0)),
                caja_disponible       = float(data.get("caja_disponible",     0)),
                deuda_mensual         = float(data.get("deuda_mensual",       0)),
                demandas_laborales    = int(data.get("demandas_laborales",    0)),
                trabajadores_sin_imss = int(data.get("trabajadores_sin_imss", 0)),
                rotacion_anual        = float(data.get("rotacion_anual",      0)),
                severance_estimado    = float(data.get("severance_estimado",  0)),
                riesgo_sat            = str(data.get("opinion_sat",    "POSITIVO")),
                riesgo_imss           = str(data.get("opinion_imss",   "POSITIVO")),
                repse_suspendido      = not bool(data.get("repse_vigente", True)),
            )
        except Exception as e:
            logger.warning("[Orchestrator] build_empresa failed: %s", e)
            return None


omega_orchestrator = OmegaOrchestrator()
