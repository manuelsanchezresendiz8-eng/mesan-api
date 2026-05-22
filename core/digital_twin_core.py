# core/digital_twin_core.py
# MESAN Omega — Digital Twin Foundation (Enterprise Hardened)

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum


# =========================================================
# ENUMS
# =========================================================

class RiskLevel(str, Enum):
    ESTABLE = "ESTABLE"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class SimulationResult:
    scenario_id: str
    escenario: str
    flujo_resultante: float
    dias_supervivencia: int
    nivel_riesgo: RiskLevel
    descripcion: str
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# =========================================================
# DIGITAL TWIN CORE
# =========================================================

class DigitalTwinCore:

    ENGINE_VERSION = "2.0.0"

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, empresa: Dict[str, Any]):

        self.ingresos = self.safe_float(
            empresa.get("ingresos_mensuales")
        )

        self.nomina = self.safe_float(
            empresa.get("nomina")
        )

        self.gastos = self.safe_float(
            empresa.get("gastos")
        )

        self.deuda = self.safe_float(
            empresa.get("deuda_mensual")
        )

        self.reserva_efectivo = self.safe_float(
            empresa.get("reserva_efectivo", 0)
        )

        # Burn mensual total
        self.burn = self.nomina + self.gastos + self.deuda

    # =====================================================
    # SAFE PARSERS
    # =====================================================

    @staticmethod
    def safe_float(value, default=0.0) -> float:

        try:

            if value in [None, "", "null"]:
                return default

            return float(value)

        except (TypeError, ValueError):
            return default

    # =====================================================
    # RISK CLASSIFICATION
    # =====================================================

    def _clasificar(
        self,
        flujo: float,
        dias: int
    ) -> RiskLevel:

        if dias < 15 or flujo < -500000:
            return RiskLevel.CRITICO

        if dias < 30 or flujo < 0:
            return RiskLevel.ALTO

        if dias < 60:
            return RiskLevel.MEDIO

        return RiskLevel.ESTABLE

    # =====================================================
    # SURVIVAL DAYS
    # =====================================================

    def _dias_supervivencia(
        self,
        ingreso_mensual: float
    ) -> int:

        burn_real = max(self.burn, 1)

        flujo_neto = ingreso_mensual - self.burn

        # Reserva de efectivo incluida
        capacidad_total = max(
            ingreso_mensual + self.reserva_efectivo,
            0
        )

        dias = int((capacidad_total / burn_real) * 30)

        return max(dias, 0)

    # =====================================================
    # RESULT BUILDER
    # =====================================================

    def _result(
        self,
        scenario_id: str,
        escenario: str,
        flujo: float,
        ingreso: float,
        descripcion: str
    ) -> SimulationResult:

        dias = self._dias_supervivencia(ingreso)

        return SimulationResult(
            scenario_id=scenario_id,
            escenario=escenario,
            flujo_resultante=round(flujo, 2),
            dias_supervivencia=dias,
            nivel_riesgo=self._clasificar(flujo, dias),
            descripcion=descripcion
        )

    # =====================================================
    # SCENARIOS
    # =====================================================

    def simulate_perdida_cliente(
        self,
        ingreso_cliente: float
    ) -> SimulationResult:

        ingreso_cliente = max(
            self.safe_float(ingreso_cliente),
            0
        )

        nuevo_ingreso = max(
            self.ingresos - ingreso_cliente,
            0
        )

        flujo = nuevo_ingreso - self.burn

        return self._result(
            scenario_id="DT_001",
            escenario="PERDIDA_CLIENTE",
            flujo=flujo,
            ingreso=nuevo_ingreso,
            descripcion=(
                f"Pérdida de cliente equivalente a "
                f"${ingreso_cliente:,.0f} mensuales."
            )
        )

    # -----------------------------------------------------

    def simulate_embargo(
        self,
        monto: float = 500000
    ) -> SimulationResult:

        monto = max(self.safe_float(monto), 0)

        flujo = (self.ingresos - self.burn) - monto

        return self._result(
            scenario_id="DT_002",
            escenario="EMBARGO_SAT",
            flujo=flujo,
            ingreso=self.ingresos,
            descripcion=(
                f"Embargo SAT simulado por "
                f"${monto:,.0f}."
            )
        )

    # -----------------------------------------------------

    def simulate_huelga(
        self,
        dias_paro: int = 5
    ) -> SimulationResult:

        dias_paro = max(int(dias_paro), 0)

        perdida_diaria = self.ingresos / 30

        perdida_total = perdida_diaria * dias_paro

        nuevo_ingreso = max(
            self.ingresos - perdida_total,
            0
        )

        flujo = nuevo_ingreso - self.burn

        return self._result(
            scenario_id="DT_003",
            escenario="HUELGA_OPERATIVA",
            flujo=flujo,
            ingreso=nuevo_ingreso,
            descripcion=(
                f"Paro operativo de {dias_paro} días "
                f"con pérdida estimada de "
                f"${perdida_total:,.0f}."
            )
        )

    # -----------------------------------------------------

    def simulate_caida_ingresos(
        self,
        porcentaje: float
    ) -> SimulationResult:

        porcentaje = min(
            max(self.safe_float(porcentaje), 0),
            100
        )

        nuevo_ingreso = self.ingresos * (
            1 - (porcentaje / 100)
        )

        flujo = nuevo_ingreso - self.burn

        return self._result(
            scenario_id="DT_004",
            escenario="CAIDA_INGRESOS",
            flujo=flujo,
            ingreso=nuevo_ingreso,
            descripcion=(
                f"Caída de ingresos del "
                f"{porcentaje:.0f}%."
            )
        )

    # -----------------------------------------------------

    def simulate_aumento_nomina(
        self,
        porcentaje: float
    ) -> SimulationResult:

        porcentaje = max(
            self.safe_float(porcentaje),
            0
        )

        nueva_nomina = self.nomina * (
            1 + (porcentaje / 100)
        )

        nuevo_burn = (
            nueva_nomina +
            self.gastos +
            self.deuda
        )

        flujo = self.ingresos - nuevo_burn

        return self._result(
            scenario_id="DT_005",
            escenario="AUMENTO_NOMINA",
            flujo=flujo,
            ingreso=self.ingresos,
            descripcion=(
                f"Aumento de nómina del "
                f"{porcentaje:.0f}% "
                f"(nueva nómina: "
                f"${nueva_nomina:,.0f})."
            )
        )

    # -----------------------------------------------------

    def simulate_bloqueo_bancario(
        self,
        porcentaje_retenido: float = 30
    ) -> SimulationResult:

        porcentaje_retenido = min(
            max(self.safe_float(porcentaje_retenido), 0),
            100
        )

        ingreso_disponible = self.ingresos * (
            1 - porcentaje_retenido / 100
        )

        flujo = ingreso_disponible - self.burn

        return self._result(
            scenario_id="DT_006",
            escenario="BLOQUEO_BANCARIO",
            flujo=flujo,
            ingreso=ingreso_disponible,
            descripcion=(
                f"Bloqueo bancario con "
                f"{porcentaje_retenido:.0f}% "
                f"de ingresos retenidos."
            )
        )

    # =====================================================
    # MASTER EXECUTION
    # =====================================================

    def run_all(
        self,
        cliente_pct: float = 20,
        embargo: float = 500000,
        dias_huelga: int = 5,
        caida_pct: float = 25,
        aumento_nomina: float = 15
    ) -> List[SimulationResult]:

        return [

            self.simulate_perdida_cliente(
                self.ingresos * (
                    cliente_pct / 100
                )
            ),

            self.simulate_embargo(
                embargo
            ),

            self.simulate_huelga(
                dias_huelga
            ),

            self.simulate_caida_ingresos(
                caida_pct
            ),

            self.simulate_aumento_nomina(
                aumento_nomina
            ),

            self.simulate_bloqueo_bancario()

        ]
