# schemas/omega_response.py -- MESAN Omega v1.1
"""
Omega Response Contract Ω

CHANGELOG v1.1 — Motor Omega #10 (Sovereign Continuity Engine):
    - Agregado campo opcional digital_sovereignty (Optional[Dict])
    - Agregado set_sovereignty() en OmegaResponseBuilder
    - Compatibilidad total hacia atras: si es None no aparece en to_dict()
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class OmegaResponse:

    tenant_id:   str = "DEFAULT"
    trace_id:    str = "NO_TRACE"

    omega_score:               int   = 0
    enterprise_survival_index: int   = 0
    governance_score:          float = 0.0

    war_room_required: bool         = False
    war_room_score:    int          = 0
    war_room_priority: str          = "MONITOREO"
    war_room_reasons:  List[str]    = field(default_factory=list)

    sales_priority:      str   = "C"
    total_exposure_mxn:  float = 0.0

    continuity_horizon: Dict[str, int] = field(default_factory=lambda: {
        "12_months": 0,
        "24_months": 0,
        "36_months": 0,
    })

    engines: Dict[str, Any] = field(default_factory=dict)

    exposure_breakdown: Dict[str, float] = field(default_factory=lambda: {
        "fiscal":      0.0,
        "labor":       0.0,
        "contractual": 0.0,
        "policy":      0.0,
    })

    remediation: Dict[str, Any] = field(default_factory=dict)

    executive_summary: str = ""

    model_drift: Dict[str, Any] = field(default_factory=dict)

    engine_latency_ms: Dict[str, float] = field(default_factory=dict)

    # Motor Omega #10 — opcional, None si no se ejecuto
    digital_sovereignty: Optional[Dict[str, Any]] = None

    generated_at:  str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    pipeline_version: str = "1.1"
    score_version:    str = "ESI-OMEGA-3.2"

    def to_dict(self) -> dict:
        d = {
            "tenant_id":   self.tenant_id,
            "trace_id":    self.trace_id,
            "omega_score":               self.omega_score,
            "enterprise_survival_index": self.enterprise_survival_index,
            "governance_score":          self.governance_score,
            "war_room_required": self.war_room_required,
            "war_room_score":    self.war_room_score,
            "war_room_priority": self.war_room_priority,
            "war_room_reasons":  self.war_room_reasons,
            "sales_priority":     self.sales_priority,
            "total_exposure_mxn": round(self.total_exposure_mxn, 2),
            "continuity_horizon": self.continuity_horizon,
            "exposure_breakdown": {
                k: round(v, 2) for k, v in self.exposure_breakdown.items()
            },
            "engines":     self.engines,
            "remediation": self.remediation,
            "executive_summary": self.executive_summary,
            "model_drift":       self.model_drift,
            "engine_latency_ms": self.engine_latency_ms,
            "generated_at":     self.generated_at,
            "pipeline_version": self.pipeline_version,
            "score_version":    self.score_version,
        }
        if self.digital_sovereignty is not None:
            d["digital_sovereignty"] = self.digital_sovereignty
        return d

    @classmethod
    def empty(cls, tenant_id: str = "DEFAULT", trace_id: str = "NO_TRACE") -> "OmegaResponse":
        return cls(tenant_id=tenant_id, trace_id=trace_id)


class OmegaResponseBuilder:

    def __init__(self, tenant_id: str = "DEFAULT", trace_id: str = "NO_TRACE"):
        self._response = OmegaResponse(tenant_id=tenant_id, trace_id=trace_id)

    def set_scores(self, omega_score, enterprise_survival_index, governance_score,
                   continuity_horizon=None):
        self._response.omega_score               = omega_score
        self._response.enterprise_survival_index = enterprise_survival_index
        self._response.governance_score          = governance_score
        if continuity_horizon:
            self._response.continuity_horizon    = continuity_horizon
        return self

    def set_war_room(self, war_room_result):
        if hasattr(war_room_result, "to_dict"):
            d = war_room_result.to_dict()
        else:
            d = war_room_result
        self._response.war_room_required = d.get("war_room_required", False)
        self._response.war_room_score    = d.get("war_room_score",    0)
        self._response.war_room_priority = d.get("war_room_priority", "MONITOREO")
        self._response.war_room_reasons  = d.get("war_room_reasons",  [])
        return self

    def set_exposure(self, exposure_result):
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

    def set_engines(self, pipeline_results: dict):
        summary = {}
        for key, result in pipeline_results.items():
            if not isinstance(result, dict):
                continue
            summary[key] = {
                "engine":     result.get("engine", key),
                "score":      result.get(
                    f"{key}_score",
                    result.get("score",
                    result.get("governance_score",
                    result.get("enterprise_survival_index", 0)))
                ),
                "nivel":      result.get("nivel", ""),
                "exposicion": result.get("exposicion_estimada_mxn", 0),
                "alertas":    len(result.get("alertas", result.get("riesgos", []))),
            }
        self._response.engines = summary
        return self

    def set_remediation(self, remediation_result: dict):
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

    def set_summary(self, summary: str):
        self._response.executive_summary = summary
        return self

    def set_model_drift(self, model_drift: dict):
        self._response.model_drift = model_drift or {}
        return self

    def set_sovereignty(self, sovereignty_result: Optional[Dict[str, Any]]):
        """Motor Omega #10 — None si no disponible."""
        if sovereignty_result:
            self._response.digital_sovereignty = sovereignty_result
        return self

    def build(self) -> OmegaResponse:
        return self._response
