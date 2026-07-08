# core/jarvis_sales/models.py -- MESAN Omega JARVIS Sales v1.1
from __future__ import annotations
import json, logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger("mesan.jarvis.sales")
JARVIS_SALES_VERSION = "1.0.0"

class LeadPriority(str, Enum):
    HIGH = "HIGH"; MEDIUM = "MEDIUM"; LOW = "LOW"

class LeadTemperature(str, Enum):
    HOT = "HOT"; WARM = "WARM"; COLD = "COLD"

class NextAction(str, Enum):
    CALL_TODAY = "CALL_TODAY"
    SEND_PROPOSAL = "SEND_PROPOSAL"
    SCHEDULE_MEETING = "SCHEDULE_MEETING"
    FOLLOW_UP_7D = "FOLLOW_UP_7D"
    FOLLOW_UP_30D = "FOLLOW_UP_30D"
    DISCARD = "DISCARD"

class Sector(str, Enum):
    MANUFACTURA = "MANUFACTURA"; COMERCIO = "COMERCIO"; SERVICIOS = "SERVICIOS"
    CONSTRUCCION = "CONSTRUCCION"; TRANSPORTE = "TRANSPORTE"; SALUD = "SALUD"
    EDUCACION = "EDUCACION"; TECNOLOGIA = "TECNOLOGIA"; AGROPECUARIO = "AGROPECUARIO"
    OTRO = "OTRO"

@dataclass
class LeadProfile:
    lead_id: str
    nombre: str
    empresa: str
    telefono: str = ""
    email: str = ""
    sector: str = "OTRO"
    empleados: int = 0
    ingresos_estimados: float = 0.0
    estatus: str = "nuevo"
    clasificacion: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    omega_score: Optional[float] = None
    nivel_riesgo: Optional[str] = None
    impacto_estimado: float = 0.0
    diagnostico_hecho: bool = False
    contactos_previos: int = 0
    dias_sin_contacto: int = 0
    whatsapp: str = ""
    origen: str = ""
    fuente_detalle: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"lead_id": self.lead_id, "nombre": self.nombre, "empresa": self.empresa,
                "sector": self.sector, "empleados": self.empleados, "estatus": self.estatus,
                "clasificacion": self.clasificacion, "omega_score": self.omega_score,
                "nivel_riesgo": self.nivel_riesgo, "impacto_estimado": self.impacto_estimado,
                "diagnostico_hecho": self.diagnostico_hecho, "dias_sin_contacto": self.dias_sin_contacto}

    def to_json(self): return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data):
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})

@dataclass
class LeadScore:
    lead_id: str
    lead_score: float
    priority: LeadPriority
    reason: str
    breakdown: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    temperature: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return {"lead_id": self.lead_id, "lead_score": round(self.lead_score, 1),
                "priority": self.priority.value, "reason": self.reason,
                "breakdown": {k: round(v,1) for k,v in self.breakdown.items()},
                "confidence": round(self.confidence, 1), "temperature": self.temperature,
                "timestamp": self.timestamp}

    def to_json(self): return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data):
        d = dict(data)
        if "priority" in d: d["priority"] = LeadPriority(d["priority"])
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in valid})

@dataclass
class LeadRecommendation:
    lead_id: str
    action: NextAction
    reason: str
    urgency: str
    script: str = ""
    estimated_close_probability: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return {"lead_id": self.lead_id, "action": self.action.value,
                "reason": self.reason, "urgency": self.urgency, "script": self.script,
                "estimated_close_probability": round(self.estimated_close_probability, 1),
                "timestamp": self.timestamp}

    def to_json(self): return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data):
        d = dict(data)
        if "action" in d: d["action"] = NextAction(d["action"])
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in valid})

@dataclass
class SalesDecision:
    lead_id: str
    profile: LeadProfile
    score: LeadScore
    temperature: LeadTemperature
    recommendation: LeadRecommendation
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return {"lead_id": self.lead_id, "timestamp": self.timestamp,
                "score": self.score.to_dict(), "temperature": self.temperature.value,
                "recommendation": self.recommendation.to_dict(),
                "profile_summary": self.profile.to_dict()}

    def to_json(self): return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data):
        profile = LeadProfile.from_dict(data.get("profile_summary", {}))
        score = LeadScore.from_dict(data.get("score", {}))
        recommendation = LeadRecommendation.from_dict(data.get("recommendation", {}))
        temperature = LeadTemperature(data.get("temperature", "COLD"))
        return cls(lead_id=data.get("lead_id",""), profile=profile, score=score,
                   temperature=temperature, recommendation=recommendation,
                   timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()))
