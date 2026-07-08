# core/jarvis_sales/sales_rules.py -- MESAN Omega JARVIS Sales v1.0
from __future__ import annotations
import logging
from typing import Dict
logger = logging.getLogger("mesan.sales.rules")

RULES_CONFIG = {
    "score_weights": {"tamano_empresa":0.20,"sector_priority":0.15,"riesgo_detectado":0.25,
                      "potencial_economico":0.20,"interaccion_previa":0.10,"diagnostico_hecho":0.10},
    "tamano_scores": {"micro":(1,10,30.0),"pequena":(11,50,70.0),"mediana":(51,200,100.0),"grande":(201,99999,85.0)},
    "sector_scores": {"MANUFACTURA":90.0,"CONSTRUCCION":85.0,"TRANSPORTE":85.0,"COMERCIO":75.0,
                      "SERVICIOS":70.0,"SALUD":65.0,"AGROPECUARIO":60.0,"TECNOLOGIA":60.0,
                      "EDUCACION":50.0,"OTRO":40.0},
    "temperature_thresholds": {"HOT":75.0,"WARM":45.0},
    "priority_thresholds": {"HIGH":70.0,"MEDIUM":40.0},
    "max_days_without_contact": 7,
    "min_impact_hot": 100000,
}

class SalesRules:
    def __init__(self, config=None):
        self._cfg = config or RULES_CONFIG
        logger.info("[SalesRules] inicializado v1.0")

    def get_tamano_score(self, empleados):
        for _, (mn, mx, score) in self._cfg["tamano_scores"].items():
            if mn <= empleados <= mx: return score
        return 30.0

    def get_sector_score(self, sector):
        return self._cfg["sector_scores"].get(sector.upper(), 40.0)

    def get_riesgo_score(self, nivel_riesgo, omega_score=None):
        if nivel_riesgo:
            m = {"EXTREMO":100.0,"CRITICO":90.0,"ALTO":75.0,"MEDIO":55.0,"BAJO":30.0}
            return m.get(nivel_riesgo.upper(), 50.0)
        if omega_score is not None: return max(0.0, 100.0 - omega_score)
        return 50.0

    def get_potencial_score(self, impacto, ingresos=0):
        ref = max(impacto, ingresos * 0.1)
        if ref >= 500000: return 100.0
        if ref >= 200000: return 80.0
        if ref >= 100000: return 60.0
        if ref >= 50000:  return 40.0
        return 20.0

    def get_interaccion_score(self, contactos, dias_sin):
        base = min(contactos * 20.0, 80.0)
        max_d = self._cfg["max_days_without_contact"]
        if dias_sin > max_d * 2: base *= 0.5
        elif dias_sin > max_d: base *= 0.75
        return min(base, 100.0)

    def get_diagnostico_score(self, diagnostico_hecho):
        return 100.0 if diagnostico_hecho else 0.0

    def classify_temperature(self, score):
        t = self._cfg["temperature_thresholds"]
        if score >= t["HOT"]: return "HOT"
        if score >= t["WARM"]: return "WARM"
        return "COLD"

    def classify_priority(self, score):
        p = self._cfg["priority_thresholds"]
        if score >= p["HIGH"]: return "HIGH"
        if score >= p["MEDIUM"]: return "MEDIUM"
        return "LOW"

    @property
    def weights(self): return self._cfg["score_weights"]

sales_rules = SalesRules()
