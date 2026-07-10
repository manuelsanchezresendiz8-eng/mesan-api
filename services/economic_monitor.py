from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import List
from services.market_models import EconomicIndicator

logger = logging.getLogger('mesan.market.economic')

class EconomicMonitor:
    def scan(self):
        now = datetime.now(timezone.utc).isoformat()
        return [
            EconomicIndicator(name='Inflacion anual', value=3.93, unit='%', period='Mayo 2026', trend='DOWN', source='INEGI', timestamp=now),
            EconomicIndicator(name='Tipo de cambio USD/MXN', value=17.45, unit='MXN', period='Julio 2026', trend='STABLE', source='Banxico', timestamp=now),
            EconomicIndicator(name='Salario minimo diario', value=278.80, unit='MXN', period='2026', trend='UP', source='CONASAMI', timestamp=now),
            EconomicIndicator(name='UMA diaria', value=108.57, unit='MXN', period='2026', trend='UP', source='INEGI', timestamp=now),
            EconomicIndicator(name='Tasa objetivo Banxico', value=9.0, unit='%', period='Julio 2026', trend='DOWN', source='Banxico', timestamp=now),
        ]
    def check(self): return self.scan()

economic_monitor = EconomicMonitor()
