# schemas/omega_response.py -- MESAN Omega v1.0
"""
Omega Response Contract Ω

Contrato único de salida para todos los consumidores de MESAN Ω.
Ningún endpoint deberá construir su propia estructura de respuesta.

Todos los consumers leen este contrato:
    - API endpoints
    - War Room UI
    - CRM Enterprise
    - Panel Estratégico
    - Landing Diagnóstico
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════════════
# OMEGA RESPONSE CONTRACT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OmegaResponse:
    """
    Respuesta estándar del pipeline completo MESAN Ω.

    Campos obligatorios:
        tenant_id                 Identificador del tenant
        trace_id                  Trazabilidad de la ejecución
        omega_score               Score global consolidado (0-100, mayor = más saludable)
        enterprise_survival_index ESI-Ω oficial — solo desde EnterpriseSurvivalEngine
        governance_score          Score de gobierno corporativo
        war_room_required         Decisión final del WarRoomEngine
        war_room_priority         Urgencia: INMEDIATA / 24H / 48H / 7_DIAS / MONITOREO
        sales_priority            A+ / HOT / A / B / C desde ExposureAggregator
        total_exposure_mxn        Exposición total consolidada
        executive_summary         Narrativa ejecutiva para CEO/Consejo
    """

    # ── Identidad ─────────────────────────────────────────────────────────────
    tenant_id:   str = "DEFAULT"
    trace_id:    str = "NO_TRACE"

    # ── Score central ─────────────────────────────────────────────────────────
    omega_score:               int   = 0    # promedio ponderado de todos los engines
    enterprise_survival_index: int   = 0    # ESI-Ω oficial — solo EnterpriseSurvivalEngine
    governance_score:          float = 0.0

    # ── War Room ──────────────────────────────────────────────────────────────
    war_room_required: bool         = False
    war_room_score:    int          = 0
    war_room_priority: str          = "MONITOREO"
    war_room_reasons:  List[str]    = field(default_factory=list)

    # ── Comercial ─────────────────────────────────────────────────────────────
    sales_priority:      str   = "C"
    total_exposure_mxn:  float = 0.0

    # ── Horizonte de continuidad ──────────────────────────────────────────────
    continuity_horizon: Dict[str, int] = field(default_factory=lambda: {
        "12_months": 0,
        "24_months": 0,
        "36_months": 0,
    })

    # ── Resultados por engine ─────────────────────────────────────────────────
    engines: Dict[str, Any] = field(default_factory=dict)

    # ── Exposición por dominio ────────────────────────────────────────────────
    exposure_breakdown: Dict[str, float] = field(default_factory=lambda: {
        "fiscal":      0.0,
        "labor":       0.0,
        "contractual": 0.0,
        "policy":      0.0,
    })

    # ── Remediación ───────────────────────────────────────────────────────────
    remediation: Dict[str, Any] = field(default_factory=dict)

    # ── Narrativa ejecutiva ───────────────────────────────────────────────────
    executive_summary: str = ""

    # ── Trazabilidad ──────────────────────────────────────────────────────────
    generated_at:  str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    pipeline_version: str = "1.0"
    score_version:    str = "ESI-OMEGA-3.2"

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            # Identidad
            "tenant_id":   self.tenant_id,
            "trace_id":    self.trace_id,

            # Scores principales
            "omega_score":               self.omega_score,
            "enterprise_survival_index": self.enterprise_survival_index,
            "governance_score":          self.governance_score,

            # War Room
            "war_room_required": self.war_room_required,
            "war_room_score":    self.war_room_score,
            "war_room_priority": self.war_room_priority,
            "war_room_reasons":  self.war_room_reasons,

            # Comercial
            "sales_priority":     self.sales_priority,
            "total_exposure_mxn": round(self.total_exposure_mxn, 2),

            # Horizonte
            "continuity_horizon": self.continuity_horizon,

            # Detalle
            "exposure_breakdown": {
                k: round(v, 2) for k, v in self.exposure_breakdown.items()
            },
            "engines":     self.engines,
            "remediation": self.remediation,

            # Narrativa
            "executive_summary": self.executive_summary,

            # Trazabilidad
            "generated_at":       self.generated_at,
            "pipeline_version":   self.pipeline_version,
            "score_version":      self.score_version,
        }

    @classmethod
    def empty(cls, tenant_id: str = "DEFAULT", trace_id: str = "NO_TRACE") -> "OmegaResponse":
        """Respuesta vacía para errores o inicialización."""
        return cls(tenant_id=tenant_id, trace_id=trace_id)


# ══════════════════════════════════════════════════════════════════════════════
# BUILDER — construye OmegaResponse desde componentes del pipeline
# ══════════════════════════════════════════════════════════════════════════════

class OmegaResponseBuilder:
    """
    Construye OmegaResponse desde los componentes del pipeline.

    Uso:
        builder = OmegaResponseBuilder(tenant_id, trace_id)
        builder.set_scores(omega_score, esi, governance)
        builder.set_war_room(war_room_result)
        builder.set_exposure(exposure_result)
        builder.set_engines(pipeline_results)
        builder.set_remediation(remediation_result)
        builder.set_summary(narrative)
        response = builder.build()
    """

    def __init__(self, tenant_id: str = "DEFAULT", trace_id: str = "NO_TRACE"):
        self._response = OmegaResponse(tenant_id=tenant_id, trace_id=trace_id)

    def set_scores(
        self,
        omega_score:               int,
        enterprise_survival_index: int,
        governance_score:          float,
        continuity_horizon:        Optional[dict] = None,
    ) -> "OmegaResponseBuilder":
        self._response.omega_score               = omega_score
        self._response.enterprise_survival_index = enterprise_survival_index
        self._response.governance_score          = governance_score
        if continuity_horizon:
            self._response.continuity_horizon    = continuity_horizon
        return self

    def set_war_room(self, war_room_result) -> "OmegaResponseBuilder":
        """Acepta WarRoomResult o dict."""
        if hasattr(war_room_result, "to_dict"):
            d = war_room_result.to_dict()
        else:
            d = war_room_result
        self._response.war_room_required = d.get("war_room_required", False)
        self._response.war_room_score    = d.get("war_room_score",    0)
        self._response.war_room_priority = d.get("war_room_priority", "MONITOREO")
        self._response.war_room_reasons  = d.get("war_room_reasons",  [])
        return self

    def set_exposure(self, exposure_result) -> "OmegaResponseBuilder":
        """Acepta ExposureResult o dict."""
        if hasattr(exposure_result, "to_dict"):
            d = exposure_result.to_dict()
        else:
            d = exposure_result
        self._response.total_exposure_mxn  = d.get("total_exposure_mxn", 0.0)
        self._response.sales_priority      = d.get("sales_priority", "C")
        self._response.exposure_breakdown  = {
            "fiscal":      d.get("fiscal",      0.0),
            "labor":       d.get("labor",       0.0),
            "contractual": d.get("contractual", 0.0),
            "policy":      d.get("policy",      0.0),
        }
        return self

    def set_engines(self, pipeline_results: dict) -> "OmegaResponseBuilder":
        """Guarda resultados de engines — solo campos clave, no todo el resultado."""
        summary = {}
        for key, result in pipeline_results.items():
            if not isinstance(result, dict):
                continue
            summary[key] = {
                "engine":      result.get("engine", key),
                "score":       result.get(
                    f"{key}_score",
                    result.get("score",
                    result.get("governance_score",
                    result.get("enterprise_survival_index", 0)))
                ),
                "nivel":       result.get("nivel", ""),
                "exposicion":  result.get("exposicion_estimada_mxn", 0),
                "alertas":     len(result.get("alertas", result.get("riesgos", []))),
            }
        self._response.engines = summary
        return self

    def set_remediation(self, remediation_result: dict) -> "OmegaResponseBuilder":
        if not remediation_result:
            return self
        self._response.remediation = {
            "urgencia":          remediation_result.get("urgencia", ""),
            "war_room_required": remediation_result.get("war_room_required", False),
            "plan_remediacion":  remediation_result.get("plan_remediacion", {}),
            "total_acciones":    remediation_result.get("total_acciones", 0),
            "executive_summary": remediation_result.get("executive_summary", ""),
        }
        return self

    def set_summary(self, summary: str) -> "OmegaResponseBuilder":
        self._response.executive_summary = summary
        return self

    def build(self) -> OmegaResponse:
        return self._response
