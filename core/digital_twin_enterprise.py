# core/digital_twin_enterprise.py -- MESAN Omega Digital Twin v3.0
"""
Digital Twin Enterprise v3.0

Cambios v3.0:
- EnterpriseTwinData migrado a @dataclass (consistencia con Empresa de continuity_engine)
- Clasificaciones de riesgo delegadas a RiskClassificationService
  (elimina lógica duplicada de CRITICO/ALTO/MEDIO)
- EnterpriseTwin mantiene API pública idéntica — compatibilidad total
- simulador_empresarial() sin cambios

Compatibilidad:
    EnterpriseTwin(dict) sigue funcionando — constructor acepta dict o dataclass
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from core.risk_classification import risk_classifier as _risk


# ══════════════════════════════════════════════════════════════════════════════
# DATACLASS — DATOS DE EMPRESA PARA DIGITAL TWIN
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EnterpriseTwinData:
    """
    Modelo de datos tipado para EnterpriseTwin.
    Consistente con Empresa de continuity_engine.py.

    Todos los campos tienen default=0 para compatibilidad con
    construcción desde dict parcial.
    """
    empresa_id:   str   = "unknown"
    ingresos:     float = 0.0
    nomina:       float = 0.0
    gastos:       float = 0.0
    deuda_mensual: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "EnterpriseTwinData":
        """Construye EnterpriseTwinData desde un dict arbitrario."""
        return cls(
            empresa_id    = str(data.get("empresa_id", "unknown")),
            ingresos      = float(data.get("ingresos", 0)),
            nomina        = float(data.get("nomina", 0)),
            gastos        = float(data.get("gastos", 0)),
            deuda_mensual = float(data.get("deuda_mensual", 0)),
        )

    def to_dict(self) -> dict:
        return {
            "empresa_id":    self.empresa_id,
            "ingresos":      self.ingresos,
            "nomina":        self.nomina,
            "gastos":        self.gastos,
            "deuda_mensual": self.deuda_mensual,
        }

    @property
    def burn_total(self) -> float:
        """Gasto operativo total mensual."""
        return self.nomina + self.gastos + self.deuda_mensual


# ══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE TWIN
# ══════════════════════════════════════════════════════════════════════════════

class EnterpriseTwin:
    """
    Digital Twin empresarial de MESAN Ω.

    Acepta dict (compatibilidad legacy) o EnterpriseTwinData.

    API pública idéntica a v2.1:
        snapshot()
        simulate_cashflow_drop(percentage)
        simulate_embargo(monto)
        simulate_perdida_cliente(ingreso_cliente)
        simulate_nomina_aumento(percentage)
    """

    def __init__(self, empresa):
        if isinstance(empresa, dict):
            self._data = EnterpriseTwinData.from_dict(empresa)
        elif isinstance(empresa, EnterpriseTwinData):
            self._data = empresa
        else:
            raise TypeError(
                f"EnterpriseTwin espera dict o EnterpriseTwinData, recibió {type(empresa)}"
            )

        # Mantener self.empresa como dict para compatibilidad con código existente
        self.empresa = self._data.to_dict()

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        return {
            **self._data.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Simulación: Caída de flujo ────────────────────────────────────────────

    def simulate_cashflow_drop(self, percentage: float) -> dict:
        """
        Simula caída porcentual de ingresos.
        Clasifica riesgo por días de supervivencia.
        """
        new_income = self._data.ingresos * (1 - percentage / 100)
        burn       = self._data.burn_total
        dias       = int((new_income / burn) * 30) if burn > 0 else 0

        return {
            "new_income":         round(new_income, 2),
            "stress_level":       percentage,
            "dias_supervivencia": dias,
            "riesgo":             _risk.classify_days_risk(dias),
        }

    # ── Simulación: Embargo ───────────────────────────────────────────────────

    def simulate_embargo(self, monto: float = 500_000) -> dict:
        """Simula impacto de embargo sobre flujo operativo."""
        flujo      = self._data.ingresos - self._data.burn_total
        flujo_post = flujo - monto

        return {
            "flujo_post_embargo": round(flujo_post, 2),
            "riesgo":             _risk.classify_flujo(flujo_post),
        }

    # ── Simulación: Pérdida de cliente ────────────────────────────────────────

    def simulate_perdida_cliente(self, ingreso_cliente: float) -> dict:
        """Simula pérdida de un cliente con ingreso conocido."""
        new_income = self._data.ingresos - ingreso_cliente
        burn       = self._data.burn_total
        dias       = int((new_income / burn) * 30) if burn > 0 and new_income > 0 else 0

        return {
            "new_income":         round(new_income, 2),
            "dias_supervivencia": dias,
            "riesgo":             _risk.classify_days_risk(dias),
        }

    # ── Simulación: Aumento de nómina ─────────────────────────────────────────

    def simulate_nomina_aumento(self, percentage: float) -> dict:
        """Simula aumento porcentual de nómina y su impacto en flujo."""
        nueva_nomina = self._data.nomina * (1 + percentage / 100)
        flujo        = (
            self._data.ingresos
            - nueva_nomina
            - self._data.gastos
            - self._data.deuda_mensual
        )

        return {
            "nomina_anterior":  round(self._data.nomina, 2),
            "nueva_nomina":     round(nueva_nomina, 2),
            "incremento":       round(nueva_nomina - self._data.nomina, 2),
            "flujo_resultante": round(flujo, 2),
            "riesgo":           _risk.classify_flujo(flujo, self._data.nomina),
        }


# ══════════════════════════════════════════════════════════════════════════════
# SIMULADOR EMPRESARIAL (función standalone — sin cambios)
# ══════════════════════════════════════════════════════════════════════════════

def simulador_empresarial(datos: dict) -> dict:
    """
    MESAN Omega — Simulador financiero empresarial.
    3 escenarios + mejor decisión. Sin cambios respecto a v2.
    """
    precio    = float(datos.get("precio_servicio", 0))
    empleados = int(datos.get("num_empleados", 1))
    salario   = float(datos.get("salario_promedio", 300))

    costo   = salario * empleados * 30
    actual  = precio - costo
    subir   = (precio * 1.2) - costo
    reducir = precio - (salario * max(1, int(empleados * 0.85)) * 30)

    escenarios = {
        "actual":           actual,
        "subir_precio":     subir,
        "reducir_personal": reducir,
    }

    return {
        "actual":           round(actual, 2),
        "subir_precio":     round(subir, 2),
        "reducir_personal": round(reducir, 2),
        "mejor":            max(escenarios, key=escenarios.get),
    }
