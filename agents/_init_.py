# agents/__init__.py -- MESAN Omega Agent Governance Layer v0.1
"""
Agent Governance Layer Ω — Capa Experimental

Principio:
    MESAN Ω supervisa procesos y controles, no personas.
    El sujeto auditado puede ser humano, sistema, IA o workflow.

Estado: EXPERIMENTAL — desacoplado del pipeline principal.

Contratos disponibles:
    AgentEntity       — Entidad operativa auditable
    AgentProtocol     — Protocolo de proceso auditable
    AgentAuditResult  — Resultado estándar de auditoría

Integración futura (v2.x):
    Agent Governance Engine
    ↓
    Governance Engine
    ↓
    Enterprise Survival Index
    ↓
    War Room
    ↓
    Remediation

NO importar desde el pipeline principal hasta fase v2.x.
"""

from agents.agent_entity       import AgentEntity
from agents.agent_protocol     import AgentProtocol
from agents.agent_audit_result import AgentAuditResult

__all__ = [
    "AgentEntity",
    "AgentProtocol",
    "AgentAuditResult",
]
