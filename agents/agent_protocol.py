# agents/agent_protocol.py -- MESAN Omega Agent Governance Layer v0.1
"""
AgentProtocol — Protocolo de Proceso Auditable Ω

Define qué proceso ejecuta una entidad, qué reglas debe cumplir,
qué evidencia debe generar y qué riesgos produce.

FASE: Contrato base — NO conectado al pipeline principal.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import uuid4

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass
class AgentProtocol:
    """
    Protocolo de ejecución auditable para una entidad operativa.

    Define el contrato entre la entidad y el sistema de auditoría:
        - Qué proceso ejecuta
        - Qué reglas debe cumplir
        - Qué evidencia debe generar
        - Qué riesgos produce si falla

    Campos:
        protocol_id         Identificador único del protocolo
        protocol_name       Nombre descriptivo del proceso
        entity_id           Entidad responsable de ejecutar
        rules               Lista de reglas de cumplimiento
        required_evidence   Evidencias mínimas que debe generar
        risk_on_failure     Nivel de riesgo si el protocolo falla
        max_execution_ms    Tiempo máximo de ejecución permitido
        active              Estado del protocolo
        version             Versión del protocolo
        created_at          Timestamp de creación
    """

    protocol_id:        str        = field(default_factory=lambda: str(uuid4()))
    protocol_name:      str        = ""
    entity_id:          str        = ""
    rules:              List[str]  = field(default_factory=list)
    required_evidence:  List[str]  = field(default_factory=list)
    risk_on_failure:    RiskLevel  = "MEDIUM"
    max_execution_ms:   int        = 30000   # 30 segundos por defecto
    active:             bool       = True
    version:            str        = "1.0"
    created_at:         str        = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "protocol_id":       self.protocol_id,
            "protocol_name":     self.protocol_name,
            "entity_id":         self.entity_id,
            "rules":             self.rules,
            "required_evidence": self.required_evidence,
            "risk_on_failure":   self.risk_on_failure,
            "max_execution_ms":  self.max_execution_ms,
            "active":            self.active,
            "version":           self.version,
            "created_at":        self.created_at,
        }
