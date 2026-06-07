# services/crisis_simulation_layer.py -- MESAN Omega v1.0
"""
Crisis Simulation Layer Ω

Conecta ContinuityEngine con los escenarios de crisis definidos en crisis_scenarios.py.
Recalcula el ESI-Ω bajo condiciones de estrés sin modificar la empresa original.

Cada simulación:
    1. Clona datos de empresa (deepcopy)
    2. Aplica shock del escenario
    3. Ejecuta ContinuityEngine.calcular_esi()
    4. Retorna ESI, clasificación y delta vs. base

NO modifica la empresa original.
NO usa IA, ML ni modelos probabilísticos.
Determinístico y auditable.

Uso:
    from services.crisis_simulation_layer import CrisisSimulationLayer
    from services.continuity_engine import ContinuityEngine, Empresa

    engine = ContinuityEngine()
    empresa = Empresa(...)
    resultado_base = engine.calcular_esi(empresa)
    esi_base = resultado_base["esi"]

    sim = CrisisSimulationLayer(engine)
    escenarios = sim.simular_todos(empresa, esi_base)
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Optional

from services.continuity_engine import ContinuityEngine, Empresa
from core.crisis_scenarios import (
    PANDEMIA, PERDIDA_CLIENTE, AUDITORIA_SAT, DEMANDA_LABORAL,
    CrisisScenario,
)


# ══════════════════════════════════════════════════════════════════════════════
# RESULTADO DE ESCENARIO
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CrisisScenarioResult:
    """Resultado de simular un escenario de crisis."""
    escenario:     str
    esi_base:      int
    esi_escenario: int
    delta:         int    # negativo = deterioro
    clasificacion: str
    riesgo:        str    # CRITICO | ALTO | MEDIO

    def to_dict(self) -> dict:
        return {
            "esi_base":      self.esi_base,
            "esi_escenario": self.esi_escenario,
            "delta":         self.delta,
            "clasificacion": self.clasificacion,
            "riesgo":        self.riesgo,
        }


# ══════════════════════════════════════════════════════════════════════════════
# CRISIS SIMULATION LAYER
# ══════════════════════════════════════════════════════════════════════════════

class CrisisSimulationLayer:
    """
    Capa de simulación de crisis para MESAN Ω.

    Recalcula ESI-Ω bajo escenarios de estrés.
    La empresa original nunca es modificada.
    """

    def __init__(self, engine: Optional[ContinuityEngine] = None):
        self._engine = engine or ContinuityEngine()

    # ── Utilidades internas ───────────────────────────────────────────────────

    def _recalcular_esi(self, empresa: Empresa) -> int:
        return self._engine.calcular_esi(empresa)["esi"]

    def _clasificar_riesgo(self, esi: int) -> str:
        if esi < 60:
            return "CRITICO"
        if esi < 75:
            return "ALTO"
        return "MEDIO"

    def _build_result(
        self,
        escenario:     str,
        esi_base:      int,
        empresa_mod:   Empresa,
    ) -> CrisisScenarioResult:
        esi_nuevo = self._recalcular_esi(empresa_mod)
        return CrisisScenarioResult(
            escenario     = escenario,
            esi_base      = esi_base,
            esi_escenario = esi_nuevo,
            delta         = esi_nuevo - esi_base,
            clasificacion = self._engine.clasificar(esi_nuevo),
            riesgo        = self._clasificar_riesgo(esi_nuevo),
        )

    # ── Escenario A — Pandemia ────────────────────────────────────────────────

    def simulate_pandemia(
        self,
        empresa:           Empresa,
        esi_base:          int,
        cashflow_drop_pct: Optional[float] = None,
    ) -> CrisisScenarioResult:
        """
        Simula caída de ingresos por disrupción operativa o sanitaria.
        Default: 40% de caída (PANDEMIA.factor_riesgo).
        """
        factor = cashflow_drop_pct if cashflow_drop_pct is not None else PANDEMIA.factor_riesgo
        mod = deepcopy(empresa)
        mod.ingresos_mensuales *= (1 - factor)
        return self._build_result("pandemia", esi_base, mod)

    # ── Escenario B — Pérdida de cliente principal ────────────────────────────

    def simulate_perdida_cliente(
        self,
        empresa:          Empresa,
        esi_base:         int,
        client_loss_pct:  Optional[float] = None,
    ) -> CrisisScenarioResult:
        """
        Simula pérdida del cliente principal.
        Default: 25% de reducción en ingresos (PERDIDA_CLIENTE.factor_riesgo).
        """
        factor = client_loss_pct if client_loss_pct is not None else PERDIDA_CLIENTE.factor_riesgo
        mod = deepcopy(empresa)
        mod.ingresos_mensuales *= (1 - factor)
        return self._build_result("perdida_cliente", esi_base, mod)

    # ── Escenario C — Auditoría SAT ───────────────────────────────────────────

    def simulate_auditoria_sat(
        self,
        empresa:         Empresa,
        esi_base:        int,
        multa_estimada:  Optional[float] = None,
    ) -> CrisisScenarioResult:
        """
        Simula auditoría SAT con multa sobre caja disponible.
        Default: 30% de ingresos mensuales (AUDITORIA_SAT.factor_riesgo).
        """
        multa = multa_estimada if multa_estimada is not None \
            else empresa.ingresos_mensuales * AUDITORIA_SAT.factor_riesgo
        mod = deepcopy(empresa)
        mod.riesgo_sat        = "NEGATIVO"
        mod.caja_disponible   = max(0, mod.caja_disponible - multa)
        return self._build_result("auditoria_sat", esi_base, mod)

    # ── Escenario D — Demanda laboral ─────────────────────────────────────────

    def simulate_demanda_laboral(
        self,
        empresa:              Empresa,
        esi_base:             int,
        severance_multiplier: Optional[float] = None,
    ) -> CrisisScenarioResult:
        """
        Simula demanda laboral colectiva que multiplica el severance estimado.
        Default: 2x (DEMANDA_LABORAL.factor_riesgo).
        """
        mult = severance_multiplier if severance_multiplier is not None \
            else DEMANDA_LABORAL.factor_riesgo
        mod = deepcopy(empresa)
        mod.severance_estimado *= mult
        mod.demandas_laborales += 1
        return self._build_result("demanda_laboral", esi_base, mod)

    # ── Simular todos ─────────────────────────────────────────────────────────

    def simular_todos(
        self,
        empresa:  Empresa,
        esi_base: int,
    ) -> Dict[str, dict]:
        """
        Ejecuta los 4 escenarios estándar y retorna resultados consolidados.

        Retorna:
            {
                "pandemia":        { esi_base, esi_escenario, delta, clasificacion, riesgo },
                "perdida_cliente": { ... },
                "auditoria_sat":   { ... },
                "demanda_laboral": { ... },
            }
        """
        return {
            "pandemia":        self.simulate_pandemia(empresa, esi_base).to_dict(),
            "perdida_cliente": self.simulate_perdida_cliente(empresa, esi_base).to_dict(),
            "auditoria_sat":   self.simulate_auditoria_sat(empresa, esi_base).to_dict(),
            "demanda_laboral": self.simulate_demanda_laboral(empresa, esi_base).to_dict(),
        }
