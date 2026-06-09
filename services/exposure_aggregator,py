# services/exposure_aggregator.py -- MESAN Omega v1.0
"""
Exposure Aggregator Ω

Consolida la exposición financiera calculada individualmente
por cada engine en un total único y verificable.

Elimina el patrón actual donde 4 engines calculan
exposición con metodologías propias sin sumar el total.

Alimenta:
    - GovernanceEngine    (exposicion_total input)
    - EnterpriseSurvivalEngine
    - WarRoomEngine
    - RemediationEngine
    - OmegaOrchestrator   (sales_priority basada en total real)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


# ══════════════════════════════════════════════════════════════════════════════
# RESULTADO DE EXPOSICIÓN
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ExposureResult:
    """Exposición financiera consolidada de todos los engines."""

    # Por dominio
    fiscal:      float = 0.0
    labor:       float = 0.0
    contractual: float = 0.0
    policy:      float = 0.0

    # Campos adicionales opcionales para futuros engines
    extra: Dict[str, float] = field(default_factory=dict)

    @property
    def total(self) -> float:
        """Total consolidado incluyendo dominios extra."""
        base = self.fiscal + self.labor + self.contractual + self.policy
        return base + sum(self.extra.values())

    @property
    def total_rounded(self) -> float:
        return round(self.total, 2)

    def dominant_domain(self) -> str:
        """Dominio con mayor exposición."""
        domains = {
            "fiscal":      self.fiscal,
            "labor":       self.labor,
            "contractual": self.contractual,
            "policy":      self.policy,
        }
        domains.update(self.extra)
        return max(domains, key=domains.get)

    def to_dict(self) -> dict:
        return {
            "fiscal":            round(self.fiscal,      2),
            "labor":             round(self.labor,       2),
            "contractual":       round(self.contractual, 2),
            "policy":            round(self.policy,      2),
            "extra":             {k: round(v, 2) for k, v in self.extra.items()},
            "total_exposure_mxn": self.total_rounded,
            "dominant_domain":   self.dominant_domain(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# EXPOSURE AGGREGATOR
# ══════════════════════════════════════════════════════════════════════════════

class ExposureAggregator:
    """
    Consolida exposición financiera de todos los engines del pipeline.

    Uso:
        agg = ExposureAggregator()

        exposure = agg.aggregate(
            fiscal_result      = fiscal_result,
            labor_result       = labor_result,
            contractual_result = contractual_result,
            policy_result      = policy_result,
        )

        print(exposure.total_rounded)       # 1_600_000.0
        print(exposure.dominant_domain())   # "contractual"
        print(exposure.to_dict())
    """

    # ── Extracción de exposición por engine ───────────────────────────────────

    @staticmethod
    def _extract(result: Optional[dict], key: str = "exposicion_estimada_mxn") -> float:
        """Extrae exposición de un resultado de engine de forma segura."""
        if not result or not isinstance(result, dict):
            return 0.0
        value = result.get(key, 0)
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0

    # ── Agregación principal ──────────────────────────────────────────────────

    def aggregate(
        self,
        fiscal_result:      Optional[dict] = None,
        labor_result:       Optional[dict] = None,
        contractual_result: Optional[dict] = None,
        policy_result:      Optional[dict] = None,
        extra:              Optional[Dict[str, float]] = None,
    ) -> ExposureResult:
        """
        Consolida exposición de los 4 dominios principales.

        Cada engine usa su propia clave de exposición:
            FiscalSentinel  → calculada como (iva + isr + deuda) * 1.35
            LaborShield     → "exposicion_estimada_mxn"
            ContractualRisk → "exposicion_estimada_mxn"
            PolicyAudit     → "exposicion_estimada_mxn"
        """
        return ExposureResult(
            fiscal      = self._extract_fiscal(fiscal_result),
            labor       = self._extract(labor_result),
            contractual = self._extract(contractual_result),
            policy      = self._extract(policy_result),
            extra       = extra or {},
        )

    def _extract_fiscal(self, result: Optional[dict]) -> float:
        """
        FiscalSentinel no usa 'exposicion_estimada_mxn' como clave directa.
        La calcula internamente como (iva + isr + deuda) * 1.35.
        Intentamos extraerla del resultado o recalcularla.
        """
        if not result:
            return 0.0
        # Intentar clave directa si se agregó en versiones futuras
        direct = result.get("exposicion_estimada_mxn")
        if direct is not None:
            try:
                return max(0.0, float(direct))
            except (TypeError, ValueError):
                pass
        # Recalcular desde métricas si están disponibles
        try:
            iva   = float(result.get("iva",            0))
            isr   = float(result.get("isr_retenido",   0))
            deuda = float(result.get("deuda_mensual",  0))
            return max(0.0, round((iva + isr + deuda) * 1.35, 2))
        except (TypeError, ValueError):
            return 0.0

    # ── Desde resultados del Orchestrator ────────────────────────────────────

    def aggregate_from_pipeline(self, pipeline_results: dict) -> ExposureResult:
        """
        Consolida exposición desde el dict completo del pipeline.

        Args:
            pipeline_results: {
                "fiscal":      {...},
                "labor":       {...},
                "contractual": {...},
                "policy":      {...},
            }
        """
        return self.aggregate(
            fiscal_result      = pipeline_results.get("fiscal"),
            labor_result       = pipeline_results.get("labor"),
            contractual_result = pipeline_results.get("contractual"),
            policy_result      = pipeline_results.get("policy"),
        )

    # ── Sales Priority desde exposición total ────────────────────────────────

    @staticmethod
    def classify_sales_priority(total_exposure: float) -> str:
        """
        Clasifica la prioridad comercial basada en exposición total consolidada.
        Fuente única para sales_priority en el Orchestrator.

        A+  → ≥ $2,000,000 MXN
        HOT → ≥ $1,000,000 MXN
        A   → ≥ $500,000 MXN
        B   → ≥ $250,000 MXN
        C   → < $250,000 MXN
        """
        if total_exposure >= 2_000_000: return "A+"
        if total_exposure >= 1_000_000: return "HOT"
        if total_exposure >= 500_000:   return "A"
        if total_exposure >= 250_000:   return "B"
        return "C"


# Instancia global
exposure_aggregator = ExposureAggregator()
