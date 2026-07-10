from __future__ import annotations
import json, logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger('mesan.market')
MARKET_VERSION = '1.0.0'

class EventSeverity(str, Enum):
    INFO='INFO'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

class EventCategory(str, Enum):
    REGULATORY='REGULATORY'; ECONOMIC='ECONOMIC'; SECTORAL='SECTORAL'; COMPETITIVE='COMPETITIVE'

class EventSource(str, Enum):
    DOF='DOF'; SAT='SAT'; IMSS='IMSS'; REPSE='REPSE'; STPS='STPS'
    BANXICO='BANXICO'; INEGI='INEGI'; INTERNAL='INTERNAL'

@dataclass
class MarketEvent:
    event_id: str; timestamp: str; source: EventSource; category: EventCategory
    severity: EventSeverity; title: str; description: str
    affected_sectors: List[str] = field(default_factory=list)
    action_required: str = ''; url: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self):
        return {'event_id':self.event_id,'timestamp':self.timestamp,'source':self.source.value,
                'category':self.category.value,'severity':self.severity.value,'title':self.title,
                'description':self.description,'affected_sectors':self.affected_sectors,'action_required':self.action_required}

@dataclass
class EconomicIndicator:
    name: str; value: float; unit: str; period: str; trend: str; source: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def to_dict(self):
        return {'name':self.name,'value':self.value,'unit':self.unit,'period':self.period,'trend':self.trend,'source':self.source}

@dataclass
class SectorStatus:
    sector: str; status: str; risk_level: str
    key_events: List[str] = field(default_factory=list); opportunity: str = ''
    def to_dict(self):
        return {'sector':self.sector,'status':self.status,'risk_level':self.risk_level,'key_events':self.key_events,'opportunity':self.opportunity}

@dataclass
class MarketAlert:
    alert_id: str; severity: EventSeverity; title: str; message: str; source: str; action: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def to_dict(self):
        return {'alert_id':self.alert_id,'severity':self.severity.value,'title':self.title,
                'message':self.message,'source':self.source,'action':self.action,'timestamp':self.timestamp}

@dataclass
class MarketReport:
    timestamp: str; version: str; market_score: float; status: str
    events: List[MarketEvent]; alerts: List[MarketAlert]
    indicators: List[EconomicIndicator]; sectors: List[SectorStatus]
    recommendations: List[str]; latency_ms: float = 0.0
    def to_dict(self):
        return {'timestamp':self.timestamp,'version':self.version,'market_score':round(self.market_score,2),
                'status':self.status,'total_events':len(self.events),'total_alerts':len(self.alerts),
                'events':[e.to_dict() for e in self.events],'alerts':[a.to_dict() for a in self.alerts],
                'indicators':[i.to_dict() for i in self.indicators],'sectors':[s.to_dict() for s in self.sectors],
                'recommendations':self.recommendations,'latency_ms':self.latency_ms}
