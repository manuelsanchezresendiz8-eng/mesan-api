from __future__ import annotations
import logging, uuid
from datetime import datetime, timezone
from typing import List
from services.market_models import MarketEvent, MarketAlert, EventSeverity

logger = logging.getLogger('mesan.market.rules')

class MarketRules:
    def evaluate(self, events):
        alerts = []
        now = datetime.now(timezone.utc).isoformat()
        for event in events:
            if event.severity in (EventSeverity.CRITICAL, EventSeverity.HIGH):
                alerts.append(MarketAlert(
                    alert_id=str(uuid.uuid4())[:8], severity=event.severity,
                    title=f'[{event.source.value}] {event.title}',
                    message=event.description, source=event.source.value,
                    action=event.action_required or 'Revisar con asesor', timestamp=now))
        logger.info('[MarketRules] %d alertas de %d eventos', len(alerts), len(events))
        return alerts

    def calculate_score(self, events):
        if not events: return 100.0
        deductions = {EventSeverity.CRITICAL:25.0, EventSeverity.HIGH:15.0, EventSeverity.MEDIUM:7.0, EventSeverity.INFO:2.0}
        score = 100.0
        for e in events: score -= deductions.get(e.severity, 0)
        return max(0.0, round(score, 2))

    def classify_status(self, score):
        if score >= 85: return 'ESTABLE'
        if score >= 70: return 'ATENCION'
        if score >= 50: return 'ALERTA'
        return 'CRITICO'

    def generate_recommendations(self, events):
        recs = []
        sources = {e.source.value for e in events}
        severities = {e.severity for e in events}
        if 'REPSE' in sources: recs.append('Revisar estatus REPSE de todos los clientes activos')
        if 'SAT' in sources: recs.append('Verificar cumplimiento CFDI 4.0 con proveedor de facturacion')
        if EventSeverity.HIGH in severities or EventSeverity.CRITICAL in severities:
            recs.append('Atender alertas HIGH/CRITICAL antes del cierre de semana')
        if not recs: recs.append('Sin acciones urgentes — continuar monitoreo regular')
        return recs

market_rules = MarketRules()
