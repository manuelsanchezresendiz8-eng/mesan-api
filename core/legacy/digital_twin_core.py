# core/digital_twin_enterprise.py -- MESAN Omega Enterprise Digital Twin v2.1
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
import copy

@dataclass
class TwinScenarioResult:
    scenario: str; timestamp: str; riesgo: str
    ingresos: float; flujo_operativo: float; burn_rate: float; dias_supervivencia: int
    variables: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""

class EnterpriseTwin:
    VERSION = "2.1.0"

    def __init__(self, empresa: dict):
        self.empresa = copy.deepcopy(empresa)

    def snapshot(self) -> dict:
        return {"empresa_id": self.empresa.get("empresa_id"), "tenant_id": self.empresa.get("tenant_id"),
                "ingresos": float(self.empresa.get("ingresos",0)), "nomina": float(self.empresa.get("nomina",0)),
                "gastos": float(self.empresa.get("gastos",0)), "deuda_mensual": float(self.empresa.get("deuda_mensual",0)),
                "timestamp": datetime.utcnow().isoformat(), "version": self.VERSION}

    def simulate_cashflow_drop(self, percentage: float) -> TwinScenarioResult:
        ingresos = self._safe_float(self.empresa.get("ingresos",0))
        new_income = max(ingresos - ingresos*(percentage/100), 0)
        burn = self._calculate_burn(); flujo = new_income - burn
        dias = self._calculate_survival_days(new_income, burn)
        return TwinScenarioResult("CASHFLOW_DROP", datetime.utcnow().isoformat(), self._risk_level(dias,flujo),
                                  round(new_income,2), round(flujo,2), round(burn,2), dias,
                                  {"drop_percentage":percentage,"income_reduction":round(ingresos*(percentage/100),2)},
                                  f"Cashflow reduction {percentage}% → {dias} survival days.")

    def simulate_embargo(self, monto: float = 500000) -> TwinScenarioResult:
        ingresos = self._safe_float(self.empresa.get("ingresos",0))
        burn = self._calculate_burn(); flujo = ingresos - burn - monto
        dias = self._calculate_survival_days(ingresos - monto, burn)
        return TwinScenarioResult("EMBARGO", datetime.utcnow().isoformat(), self._risk_level(dias,flujo),
                                  ingresos, round(flujo,2), round(burn,2), dias,
                                  {"embargo_amount":monto}, f"Embargo ${monto:,.0f} → {dias} survival days.")

    def simulate_perdida_cliente(self, ingreso_cliente: float) -> TwinScenarioResult:
        ingresos = self._safe_float(self.empresa.get("ingresos",0))
        new_income = max(ingresos - ingreso_cliente, 0)
        burn = self._calculate_burn(); flujo = new_income - burn
        dias = self._calculate_survival_days(new_income, burn)
        return TwinScenarioResult("CLIENT_LOSS", datetime.utcnow().isoformat(), self._risk_level(dias,flujo),
                                  round(new_income,2), round(flujo,2), round(burn,2), dias,
                                  {"lost_client_income":ingreso_cliente}, f"Client loss ${ingreso_cliente:,.0f} → {dias} days.")

    def simulate_nomina_aumento(self, percentage: float) -> TwinScenarioResult:
        ingresos = self._safe_float(self.empresa.get("ingresos",0))
        nueva_nomina = self._safe_float(self.empresa.get("nomina",0)) * (1+percentage/100)
        burn = nueva_nomina + self._safe_float(self.empresa.get("gastos",0)) + self._safe_float(self.empresa.get("deuda_mensual",0))
        flujo = ingresos - burn; dias = self._calculate_survival_days(ingresos, burn)
        return TwinScenarioResult("PAYROLL_INCREASE", datetime.utcnow().isoformat(), self._risk_level(dias,flujo),
                                  ingresos, round(flujo,2), round(burn,2), dias,
                                  {"increase_percentage":percentage,"new_payroll":round(nueva_nomina,2)},
                                  f"Payroll +{percentage}% → {dias} survival days.")

    def run_all(self) -> List[TwinScenarioResult]:
        return [self.simulate_cashflow_drop(20), self.simulate_cashflow_drop(40),
                self.simulate_embargo(500000), self.simulate_perdida_cliente(300000), self.simulate_nomina_aumento(15)]

    def _calculate_burn(self) -> float:
        return sum(self._safe_float(self.empresa.get(k,0)) for k in ["nomina","gastos","deuda_mensual"])

    def _calculate_survival_days(self, ingresos, burn) -> int:
        if burn <= 0: return 365
        if ingresos <= 0: return 0
        return max(int((ingresos/burn)*30), 0)

    def _risk_level(self, dias, flujo) -> str:
        if flujo < 0 or dias < 15: return "CRITICO"
        if dias < 30: return "ALTO"
        if dias < 60: return "MEDIO"
        return "BAJO"

    def _safe_float(self, value) -> float:
        try: return float(value)
        except: return 0.0
