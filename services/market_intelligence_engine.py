from __future__ import annotations
import logging, time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from services.market_models import MarketEvent, MarketAlert, EconomicIndicator, SectorStatus, MarketReport, MARKET_VERSION
from services.regulatory_monitor import regulatory_monitor
from services.economic_monitor import economic_monitor
from services.sector_monitor import sector_monitor
from services.market_rules import market_rules

logger = logging.getLogger('mesan.market')

class MarketIntelligenceEngine:
    def __init__(self):
        self.version = MARKET_VERSION
        self._monitors = []
        self._last_report = None
        self.register_monitor(regulatory_monitor)
        self.register_monitor(economic_monitor)
        self.register_monitor(sector_monitor)
        logger.info('[MarketEngine] v%s inicializado con %d monitores', self.version, len(self._monitors))

    def register_monitor(self, monitor):
        self._monitors.append(monitor)

    def run(self):
        started = time.perf_counter()
        events = []; indicators = []; sectors = []
        for monitor in self._monitors:
            try:
                result = monitor.check()
                if not result: continue
                first = result[0]
                if hasattr(first, 'source') and hasattr(first, 'category'): events.extend(result)
                elif hasattr(first, 'value') and hasattr(first, 'unit'): indicators.extend(result)
                elif hasattr(first, 'risk_level'): sectors.extend(result)
            except Exception as e:
                logger.error('[MarketEngine] Monitor %s fallo: %s', monitor.__class__.__name__, e)
        alerts = market_rules.evaluate(events)
        score = market_rules.calculate_score(events)
        status = market_rules.classify_status(score)
        recs = market_rules.generate_recommendations(events)
        latency = round((time.perf_counter() - started) * 1000, 2)
        report = MarketReport(timestamp=datetime.now(timezone.utc).isoformat(), version=self.version,
            market_score=score, status=status, events=events, alerts=alerts,
            indicators=indicators, sectors=sectors, recommendations=recs, latency_ms=latency)
        self._last_report = report
        logger.info('[MarketEngine] score=%.1f status=%s events=%d alerts=%d', score, status, len(events), len(alerts))
        return report

    def health(self):
        return {'status':'OK','version':self.version,'monitors':len(self._monitors),'timestamp':datetime.now(timezone.utc).isoformat()}

    def get_alerts(self):
        return [(self._last_report or self.run()).alerts]

    def get_indicators(self):
        return [i.to_dict() for i in (self._last_report or self.run()).indicators]

    def get_events(self):
        return [e.to_dict() for e in (self._last_report or self.run()).events]

    def get_dashboard(self):
        r = self.run()
        return {'timestamp':r.timestamp,'market_score':r.market_score,'status':r.status,
                'total_events':len(r.events),'total_alerts':len(r.alerts),
                'critical_alerts':sum(1 for a in r.alerts if a.severity.value=='CRITICAL'),
                'high_alerts':sum(1 for a in r.alerts if a.severity.value=='HIGH'),
                'indicators':[i.to_dict() for i in r.indicators],
                'sectors':[s.to_dict() for s in r.sectors],
                'top_alerts':[a.to_dict() for a in r.alerts[:3]],
                'recommendations':r.recommendations,'latency_ms':r.latency_ms}

    def notify_guardian(self, alert): pass
    def notify_jarvis(self, event): pass
    def notify_sales(self, opportunity): pass

market_engine = MarketIntelligenceEngine()
