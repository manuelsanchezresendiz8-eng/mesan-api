# core/jarvis/incident_engine.py -- MESAN Omega Incident Engine v1.1
"""
Incident Engine -- Motor oficial de incidentes de Guardian Omega.

v1.1:
    - Deduplicacion: evita incidentes duplicados por servicio+severidad
    - correlation_id: relaciona multiples eventos del mismo problema
    - Source enum: GUARDIAN, HEALTH_MONITOR, SECURITY_MONITOR, etc.
    - Persistencia preparada: _save(), _load(), _delete() (Fase 2: PostgreSQL)
    - stats() mejorado: MTTR, MTBF, Incident Rate, Critical Rate
    - _escalate_old_incidents(): escala severidad por tiempo abierto

API publica sin cambios. Compatible con GuardianEngine existente.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mesan.incidents")


# ── Enums ─────────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    INFO     = "INFO"
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class Status(str, Enum):
    OPEN          = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED     = "MITIGATED"
    RESOLVED      = "RESOLVED"
    CLOSED        = "CLOSED"


class Source(str, Enum):
    GUARDIAN             = "GUARDIAN"
    HEALTH_MONITOR       = "HEALTH_MONITOR"
    SECURITY_MONITOR     = "SECURITY_MONITOR"
    PREDICTIVE_MONITOR   = "PREDICTIVE_MONITOR"
    MARKET_INTELLIGENCE  = "MARKET_INTELLIGENCE"
    MANUAL               = "MANUAL"


# Tiempo maximo abierto por severidad antes de escalar (minutos)
ESCALATION_THRESHOLDS: Dict[str, int] = {
    Severity.LOW.value:    120,   # 2 horas
    Severity.MEDIUM.value:  60,   # 1 hora
    Severity.HIGH.value:    30,   # 30 minutos
}

SEVERITY_ORDER = [
    Severity.INFO, Severity.LOW, Severity.MEDIUM,
    Severity.HIGH, Severity.CRITICAL
]


# ── Modelos ───────────────────────────────────────────────────────────────────

@dataclass
class TimelineEntry:
    """Entrada de la bitacora de un incidente."""
    timestamp: str
    note:      str
    author:    str = "JARVIS"

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "note": self.note, "author": self.author}


@dataclass
class Incident:
    """
    Modelo de incidente de Guardian Omega.
    ID formato: INC-YYYYMMDD-NNNNNN
    """
    id:             str
    created_at:     str
    service:        str
    severity:       Severity
    status:         Status
    title:          str
    description:    str
    source:         str                  = Source.GUARDIAN.value
    metadata:       Dict[str, Any]       = field(default_factory=dict)
    timeline:       List[TimelineEntry]  = field(default_factory=list)
    resolved_at:    Optional[str]        = None
    closed_at:      Optional[str]        = None
    correlation_id: Optional[str]        = None   # v1.1: relaciona eventos del mismo problema

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":             self.id,
            "created_at":     self.created_at,
            "service":        self.service,
            "severity":       self.severity.value,
            "status":         self.status.value,
            "title":          self.title,
            "description":    self.description,
            "source":         self.source,
            "metadata":       self.metadata,
            "timeline":       [e.to_dict() for e in self.timeline],
            "resolved_at":    self.resolved_at,
            "closed_at":      self.closed_at,
            "correlation_id": self.correlation_id,
        }


# ── Engine ────────────────────────────────────────────────────────────────────

class IncidentEngine:
    """
    Motor de incidentes de Guardian Omega.

    API publica estable — preparada para migracion a PostgreSQL
    sin modificar llamadas existentes en GuardianEngine.
    """

    _counters: Dict[str, int] = {}

    def __init__(self):
        self._incidents: Dict[str, Incident] = {}
        logger.info("[IncidentEngine] v1.1 inicializado")

    # ── ID y timestamps ───────────────────────────────────────────────────────

    def _generate_id(self) -> str:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        IncidentEngine._counters[today] = IncidentEngine._counters.get(today, 0) + 1
        return f"INC-{today}-{str(IncidentEngine._counters[today]).zfill(6)}"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Persistencia (Fase 1: memoria / Fase 2: PostgreSQL) ───────────────────

    def _save(self, incident: Incident) -> None:
        """
        Fase 1: guarda en memoria.
        Fase 2: INSERT/UPDATE en tabla incidents de PostgreSQL.
        """
        self._incidents[incident.id] = incident

    def _load(self, incident_id: str) -> Optional[Incident]:
        """
        Fase 1: lee de memoria.
        Fase 2: SELECT FROM incidents WHERE id = %s.
        """
        return self._incidents.get(incident_id)

    def _delete(self, incident_id: str) -> None:
        """
        Fase 1: elimina de memoria.
        Fase 2: DELETE FROM incidents WHERE id = %s.
        """
        self._incidents.pop(incident_id, None)

    # ── Deduplicacion ─────────────────────────────────────────────────────────

    def _find_duplicate(self, service: str, severity: Severity) -> Optional[Incident]:
        """Busca incidente abierto existente para el mismo servicio y severidad."""
        open_statuses = {Status.OPEN, Status.INVESTIGATING, Status.MITIGATED}
        for inc in self._incidents.values():
            if (inc.service == service and
                inc.severity == severity and
                inc.status in open_statuses):
                return inc
        return None

    # ── API publica ───────────────────────────────────────────────────────────

    def create(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo incidente o actualiza uno existente si ya hay uno abierto
        para el mismo servicio y severidad (deduplicacion).

        Contrato con GuardianEngine:
            alert = {"service": str, "severity": str, "message": str}
        """
        severity_str = alert.get("severity", "MEDIUM").upper()
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.MEDIUM

        service     = alert.get("service", "UNKNOWN")
        description = alert.get("message", "Sin descripcion")

        # Deduplicacion: si ya existe uno abierto, agregar al timeline
        existing = self._find_duplicate(service, severity)
        if existing:
            existing.timeline.append(TimelineEntry(
                timestamp=self._now(),
                note=f"Evento repetido: {description}",
            ))
            self._save(existing)
            logger.info(
                "[INCIDENT] Duplicado ignorado, timeline actualizado: %s | %s",
                existing.id, description[:60],
            )
            return existing.to_dict()

        # Crear nuevo incidente
        source_str = alert.get("source", Source.GUARDIAN.value)
        try:
            Source(source_str)
        except ValueError:
            source_str = Source.GUARDIAN.value

        incident_id    = self._generate_id()
        correlation_id = alert.get("correlation_id", None)
        title          = f"[{severity.value}] {service}: {description[:60]}"

        incident = Incident(
            id=             incident_id,
            created_at=     self._now(),
            service=        service,
            severity=       severity,
            status=         Status.OPEN,
            title=          title,
            description=    description,
            source=         source_str,
            metadata=       {k: v for k, v in alert.items()
                            if k not in ("service", "severity", "message", "source", "correlation_id")},
            timeline=       [TimelineEntry(
                timestamp=self._now(),
                note=f"Incidente creado por Guardian Omega. {description}",
            )],
            correlation_id= correlation_id,
        )

        self._save(incident)
        logger.warning(
            "[INCIDENT] %s | %s | %s | %s",
            incident_id, severity.value, service, description[:80],
        )
        return incident.to_dict()

    def resolve(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Marca un incidente como RESOLVED."""
        incident = self._load(incident_id)
        if not incident:
            logger.warning("[INCIDENT] resolve: no encontrado: %s", incident_id)
            return None
        if incident.status in (Status.RESOLVED, Status.CLOSED):
            return incident.to_dict()
        incident.status      = Status.RESOLVED
        incident.resolved_at = self._now()
        incident.timeline.append(TimelineEntry(timestamp=self._now(), note="RESOLVED."))
        self._save(incident)
        logger.info("[INCIDENT] %s RESOLVED", incident_id)
        return incident.to_dict()

    def close(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Marca un incidente como CLOSED."""
        incident = self._load(incident_id)
        if not incident:
            logger.warning("[INCIDENT] close: no encontrado: %s", incident_id)
            return None
        incident.status    = Status.CLOSED
        incident.closed_at = self._now()
        incident.timeline.append(TimelineEntry(timestamp=self._now(), note="CLOSED."))
        self._save(incident)
        logger.info("[INCIDENT] %s CLOSED", incident_id)
        return incident.to_dict()

    def update(self, incident_id: str, note: str, author: str = "JARVIS") -> Optional[Dict[str, Any]]:
        """Agrega una entrada a la timeline."""
        incident = self._load(incident_id)
        if not incident:
            logger.warning("[INCIDENT] update: no encontrado: %s", incident_id)
            return None
        incident.timeline.append(TimelineEntry(timestamp=self._now(), note=note, author=author))
        self._save(incident)
        logger.info("[INCIDENT] %s updated: %s", incident_id, note[:60])
        return incident.to_dict()

    def acknowledge(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Cambia status a INVESTIGATING."""
        incident = self._load(incident_id)
        if not incident or incident.status != Status.OPEN:
            return None
        incident.status = Status.INVESTIGATING
        incident.timeline.append(TimelineEntry(timestamp=self._now(), note="En investigacion."))
        self._save(incident)
        return incident.to_dict()

    def list_open(self) -> List[Dict[str, Any]]:
        """Retorna todos los incidentes abiertos."""
        open_statuses = {Status.OPEN, Status.INVESTIGATING, Status.MITIGATED}
        return [i.to_dict() for i in self._incidents.values() if i.status in open_statuses]

    def get(self, incident_id: str) -> Optional[Dict[str, Any]]:
        incident = self._load(incident_id)
        return incident.to_dict() if incident else None

    def list_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        try:
            sev = Severity(severity.upper())
        except ValueError:
            return []
        return [i.to_dict() for i in self._incidents.values()
                if i.severity == sev and i.status == Status.OPEN]

    def has_open(self, service: str, severity: str) -> bool:
        try:
            sev = Severity(severity.upper())
        except ValueError:
            return False
        return self._find_duplicate(service, sev) is not None

    def stats(self) -> Dict[str, Any]:
        """
        Estadisticas del motor de incidentes.

        Incluye: MTTR, MTBF, Incident Rate, Critical Rate.
        """
        all_inc     = list(self._incidents.values())
        open_inc    = [i for i in all_inc if i.status in
                      (Status.OPEN, Status.INVESTIGATING, Status.MITIGATED)]
        resolved    = [i for i in all_inc if i.status in (Status.RESOLVED, Status.CLOSED)]
        critical    = [i for i in open_inc if i.severity == Severity.CRITICAL]

        # MTTR (Mean Time To Resolve) en minutos
        mttr = 0.0
        resolution_times = []
        for i in resolved:
            if i.resolved_at:
                try:
                    delta = (datetime.fromisoformat(i.resolved_at) -
                             datetime.fromisoformat(i.created_at)).total_seconds() / 60
                    resolution_times.append(delta)
                except Exception:
                    pass
        if resolution_times:
            mttr = round(sum(resolution_times) / len(resolution_times), 1)

        # MTBF (Mean Time Between Failures) en minutos
        mtbf = 0.0
        if len(all_inc) >= 2:
            sorted_inc = sorted(all_inc, key=lambda x: x.created_at)
            gaps = []
            for i in range(1, len(sorted_inc)):
                try:
                    gap = (datetime.fromisoformat(sorted_inc[i].created_at) -
                           datetime.fromisoformat(sorted_inc[i-1].created_at)).total_seconds() / 60
                    gaps.append(gap)
                except Exception:
                    pass
            if gaps:
                mtbf = round(sum(gaps) / len(gaps), 1)

        # Incident Rate (incidentes por hora en las ultimas 24h)
        incident_rate = 0.0
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            recent = [i for i in all_inc
                     if datetime.fromisoformat(i.created_at) >= cutoff]
            incident_rate = round(len(recent) / 24, 2)
        except Exception:
            pass

        # Critical Rate (% de incidentes criticos sobre total abiertos)
        critical_rate = 0.0
        if open_inc:
            critical_rate = round(len(critical) / len(open_inc) * 100, 1)

        return {
            "total":                         len(all_inc),
            "abiertos":                      len(open_inc),
            "criticos":                      len(critical),
            "resueltos":                     len(resolved),
            "tiempo_promedio_resolucion_min": mttr,
            "mttr_min":                      mttr,
            "mtbf_min":                      mtbf,
            "incident_rate_per_hour":        incident_rate,
            "critical_rate_pct":             critical_rate,
        }

    # ── Escalamiento automatico ───────────────────────────────────────────────

    def _escalate_old_incidents(self) -> List[str]:
        """
        Escala severidad de incidentes que llevan demasiado tiempo abiertos.

        Reglas:
            LOW    -> MEDIUM  si abierto > 120 min
            MEDIUM -> HIGH    si abierto >  60 min
            HIGH   -> CRITICAL si abierto >  30 min

        Retorna lista de IDs escalados.
        Llamar desde un scheduler periodico (Fase B: APScheduler o cron).
        """
        escalated = []
        now = datetime.now(timezone.utc)
        open_statuses = {Status.OPEN, Status.INVESTIGATING}

        for incident in self._incidents.values():
            if incident.status not in open_statuses:
                continue
            if incident.severity == Severity.CRITICAL:
                continue

            threshold_min = ESCALATION_THRESHOLDS.get(incident.severity.value)
            if not threshold_min:
                continue

            try:
                age_min = (now - datetime.fromisoformat(incident.created_at)).total_seconds() / 60
            except Exception:
                continue

            if age_min >= threshold_min:
                old_sev = incident.severity
                idx     = SEVERITY_ORDER.index(old_sev)
                if idx < len(SEVERITY_ORDER) - 1:
                    incident.severity = SEVERITY_ORDER[idx + 1]
                    incident.timeline.append(TimelineEntry(
                        timestamp=self._now(),
                        note=f"Escalado automaticamente: {old_sev.value} -> {incident.severity.value} "
                             f"(abierto {age_min:.0f} min, umbral {threshold_min} min)",
                    ))
                    self._save(incident)
                    escalated.append(incident.id)
                    logger.warning(
                        "[INCIDENT] %s escalado %s -> %s (%.0f min abierto)",
                        incident.id, old_sev.value, incident.severity.value, age_min,
                    )

        return escalated


# Singleton
incident_engine = IncidentEngine()