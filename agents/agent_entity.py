# agents/agent_entity.py -- MESAN Omega Agent Governance Layer v0.1
"""
AgentEntity — Entidad Operativa Auditable Ω

Representa cualquier sujeto capaz de ejecutar un proceso auditado por MESAN Ω.

Principio:
    MESAN Ω supervisa procesos y controles, no personas.
    El sujeto puede ser humano, sistema, IA o workflow.

FASE: Contrato base — NO conectado al pipeline principal.
Integración futura: Agent Governance Engine → Governance Engine → ESI → War Room
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import uuid4

EntityType = Literal[
    "HUMAN",
    "SYSTEM",
    "AI_AGENT",
    "MULTI_AGENT",
    "EXTERNAL_SERVICE",
]

CriticalityLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass
class AgentEntity:
    """
    Entidad Operativa Auditable.

    Representa cualquier sujeto que ejecuta procesos dentro del
    ecosistema supervisado por MESAN Ω.

    Campos:
        entity_id       Identificador único de la entidad
        entity_type     Tipo: HUMAN / SYSTEM / AI_AGENT / MULTI_AGENT / EXTERNAL_SERVICE
        entity_name     Nombre descriptivo
        owner           Responsable de la entidad (tenant_id o área)
        criticality     Nivel de criticidad operativa
        permissions     Lista de permisos o scopes autorizados
        execution_scope Procesos o módulos que puede ejecutar
        active          Estado operativo actual
        created_at      Timestamp de registro
        metadata        Información adicional opcional
    """

    entity_id:       str           = field(default_factory=lambda: str(uuid4()))
    entity_type:     EntityType    = "HUMAN"
    entity_name:     str           = ""
    owner:           str           = "DEFAULT"
    criticality:     CriticalityLevel = "MEDIUM"
    permissions:     List[str]     = field(default_factory=list)
    execution_scope: List[str]     = field(default_factory=list)
    active:          bool          = True
    created_at:      str           = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata:        dict          = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entity_id":       self.entity_id,
            "entity_type":     self.entity_type,
            "entity_name":     self.entity_name,
            "owner":           self.owner,
            "criticality":     self.criticality,
            "permissions":     self.permissions,
            "execution_scope": self.execution_scope,
            "active":          self.active,
            "created_at":      self.created_at,
            "metadata":        self.metadata,
        }
