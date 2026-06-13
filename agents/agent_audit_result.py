# agents/agent_audit_result.py -- MESAN Omega Agent Governance Layer v0.1
"""
AgentAuditResult — Resultado Estándar de Auditoría de Entidad Ω

Contrato de salida para cualquier auditoría de entidad operativa.
Agnóstico al tipo de entidad: humano, sistema, IA o workflow.

Principio:
    Lo que importa es cumplimiento, riesgo, trazabilidad e impacto económico.
    No importa si el ejecutor fue una persona, un ERP, un bot o una IA.

FASE: Contrato base — NO conectado al pipeline principal.
Integración futura: Agent Governance Engine → Governance Engine → ESI → War Room
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

RiskLevel      = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ExecutionQuality = Literal["EXCELLENT", "GOOD", "ACCEPTABLE", "POOR", "FAILED"]


@dataclass
class AgentAuditResult:
    """
    Resultado estándar de auditoría para una entidad operativa.

    Campos:
        audit_id            Identificador único de la auditoría
        entity_id           Entidad auditada
        protocol_id         Protocolo ejecutado
        compliance_score    Score de cumplimiento (0-100, mayor = más cumplimiento)
        execution_quality   Calidad de ejecución: EXCELLENT / GOOD / ACCEPTABLE / POOR / FAILED
        anomalies           Lista de anomalías detectadas
        risk_level          Nivel de riesgo resultante
        recommendations     Recomendaciones de mejora
        evidence_generated  Evidencias generadas por la entidad
        execution_ms        Tiempo real de ejecución en ms
        economic_impact_mxn Impacto económico estimado en MXN
        trace_id            Trazabilidad del proceso auditado
        generated_at        Timestamp del resultado
        metadata            Información adicional
    """

    audit_id:            str              = field(default_factory=lambda: str(uuid4()))
    entity_id:           str              = ""
    protocol_id:         str              = ""
    compliance_score:    int              = 0      # 0-100
    execution_quality:   ExecutionQuality = "ACCEPTABLE"
    anomalies:           List[str]        = field(default_factory=list)
    risk_level:          RiskLevel        = "LOW"
    recommendations:     List[str]        = field(default_factory=list)
    evidence_generated:  List[str]        = field(default_factory=list)
    execution_ms:        int              = 0
    economic_impact_mxn: float            = 0.0
    trace_id:            str              = ""
    generated_at:        str              = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata:            Dict[str, Any]   = field(default_factory=dict)

    def is_compliant(self) -> bool:
        """Entidad cumple si score >= 70 y sin anomalías críticas."""
        return self.compliance_score >= 70 and self.risk_level not in ("HIGH", "CRITICAL")

    def to_dict(self) -> dict:
        return {
            "audit_id":            self.audit_id,
            "entity_id":           self.entity_id,
            "protocol_id":         self.protocol_id,
            "compliance_score":    self.compliance_score,
            "execution_quality":   self.execution_quality,
            "anomalies":           self.anomalies,
            "risk_level":          self.risk_level,
            "recommendations":     self.recommendations,
            "evidence_generated":  self.evidence_generated,
            "execution_ms":        self.execution_ms,
            "economic_impact_mxn": round(self.economic_impact_mxn, 2),
            "trace_id":            self.trace_id,
            "generated_at":        self.generated_at,
            "is_compliant":        self.is_compliant(),
            "metadata":            self.metadata,
        }
