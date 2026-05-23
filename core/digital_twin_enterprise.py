# core/digital_twin_enterprise.py -- MESAN Omega Digital Twin v2
from datetime import datetime

class EnterpriseTwin:

    def __init__(self, empresa: dict):
        self.empresa = empresa

    def snapshot(self) -> dict:
        return {
            "empresa_id": self.empresa.get("empresa_id"),
            "ingresos":   self.empresa.get("ingresos", 0),
            "nomina":     self.empresa.get("nomina", 0),
            "gastos":     self.empresa.get("gastos", 0),
            "deuda":      self.empresa.get("deuda_mensual", 0),
            "timestamp":  datetime.utcnow().isoformat()
        }

    def simulate_cashflow_drop(self, percentage: float) -> dict:
        ingresos = self.empresa.get("ingresos", 0)
        reduction = ingresos * (percentage / 100)
        new_income = ingresos - reduction
        burn = self.empresa.get("nomina",0) + self.empresa.get("gastos",0) + self.empresa.get("deuda_mensual",0)
        dias = int((new_income / burn) * 30) if burn > 0 else 0
        return {"new_income": new_income, "stress_level": percentage, "dias_supervivencia": dias, "riesgo": "CRITICO" if dias < 15 else "ALTO" if dias < 30 else "MEDIO"}

    def simulate_embargo(self, monto: float = 500000) -> dict:
        flujo = self.empresa.get("ingresos",0) - self.empresa.get("nomina",0) - self.empresa.get("gastos",0) - self.empresa.get("deuda_mensual",0)
        return {"flujo_post_embargo": flujo - monto, "riesgo": "CRITICO" if flujo - monto < 0 else "ALTO"}

    def simulate_perdida_cliente(self, ingreso_cliente: float) -> dict:
        new_income = self.empresa.get("ingresos",0) - ingreso_cliente
        burn = self.empresa.get("nomina",0) + self.empresa.get("gastos",0) + self.empresa.get("deuda_mensual",0)
        dias = int((new_income / burn) * 30) if burn > 0 and new_income > 0 else 0
        return {"new_income": new_income, "dias_supervivencia": dias, "riesgo": "CRITICO" if dias < 15 else "ALTO"}

    def simulate_nomina_aumento(self, percentage: float) -> dict:
        nomina_actual = self.empresa.get("nomina", 0)
        nueva_nomina = nomina_actual * (1 + percentage/100)
        flujo = self.empresa.get("ingresos",0) - nueva_nomina - self.empresa.get("gastos",0) - self.empresa.get("deuda_mensual",0)
        return {"nueva_nomina": nueva_nomina, "flujo_resultante": flujo, "riesgo": "CRITICO" if flujo < 0 else "MEDIO"}
