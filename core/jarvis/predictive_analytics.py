# core/jarvis/predictive_analytics.py -- MESAN Omega Predictive Analytics v1.0
"""
Motor predictivo de Guardian. Calcula tendencias, probabilidades de falla
y tiempo estimado antes de incidentes.
"""
import logging
import time
from collections import deque
from datetime import datetime, timezone
logger = logging.getLogger("mesan.guardian.predictive")

class PredictiveEngine:
    def __init__(self):
        self.version = "1.0.0"
        self._health_history = deque(maxlen=100)
        self._service_failures = {}
        self._last_analysis = None
        logger.info("[Predictive] v%s iniciado", self.version)

    def record(self, health_score, services):
        self._health_history.append({"timestamp": time.time(), "health": health_score})
        for svc in services:
            name = svc.get("service", "unknown")
            if name not in self._service_failures:
                self._service_failures[name] = deque(maxlen=50)
            if svc.get("status") not in ("OK", "STARTING"):
                self._service_failures[name].append(time.time())

    def analyze(self):
        trend = self._calc_trend()
        risk_svc = self._highest_risk_service()
        prob = self._failure_probability()
        eta = self._estimate_eta(trend)
        risk_level = "CRITICAL" if prob > 0.8 else "HIGH" if prob > 0.5 else "MEDIUM" if prob > 0.3 else "LOW"
        self._last_analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.version,
            "risk": risk_level,
            "probability": round(prob, 2),
            "next_failure": risk_svc,
            "eta_minutes": eta,
            "trend": trend,
            "health_samples": len(self._health_history),
            "monitored_services": list(self._service_failures.keys()),
        }
        return self._last_analysis

    def _calc_trend(self):
        samples = list(self._health_history)
        if len(samples) < 3:
            return "STABLE"
        recent = [s["health"] for s in samples[-5:]]
        older = [s["health"] for s in samples[-10:-5]] if len(samples) >= 10 else [s["health"] for s in samples[:len(samples)//2]]
        avg_recent = sum(recent) / len(recent) if recent else 0
        avg_older = sum(older) / len(older) if older else avg_recent
        diff = avg_recent - avg_older
        if diff < -10:
            return "DECLINING"
        if diff > 5:
            return "IMPROVING"
        return "STABLE"

    def _highest_risk_service(self):
        if not self._service_failures:
            return "None"
        worst = max(self._service_failures.items(), key=lambda x: len(x[1]))
        return worst[0] if len(worst[1]) > 0 else "None"

    def _failure_probability(self):
        samples = list(self._health_history)
        if len(samples) < 5:
            return 0.1
        recent = [s["health"] for s in samples[-10:]]
        below_threshold = sum(1 for h in recent if h < 70)
        return round(min(below_threshold / len(recent), 1.0), 2)

    def _estimate_eta(self, trend):
        if trend == "DECLINING":
            samples = list(self._health_history)
            if len(samples) >= 2:
                recent = [s["health"] for s in samples[-5:]]
                rate = (recent[0] - recent[-1]) / max(len(recent), 1)
                if rate > 0:
                    current = recent[-1]
                    minutes_to_critical = max(int((current - 50) / rate * 0.5), 1)
                    return minutes_to_critical
            return 30
        if trend == "STABLE":
            return 120
        return 480

    def get_last(self):
        if not self._last_analysis:
            return self.analyze()
        return self._last_analysis

predictive_engine = PredictiveEngine()