# core/crisis_scenarios.py -- MESAN Omega v1.0
"""
Crisis Scenarios Ω — Catálogo centralizado de escenarios de estrés empresarial.

Evita valores hardcodeados dispersos en múltiples módulos.
Cada escenario define nombre, descripción, factor de riesgo y tipo de shock.

Uso:
    from core.crisis_scenarios import PANDEMIA, PERDIDA_CLIENTE, ESCENARIOS

    factor = PANDEMIA.factor_riesgo   # 0.40
    desc   = PANDEMIA.descripcion
"""

from dataclasses import dataclass
from typing import Dict


# ══════════════════════════════════════════════════════════════════════════════
# MODELO DE ESCENARIO
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CrisisScenario:
    """
    Definición inmutable de un escenario de crisis.

    Campos:
        nombre          : Identificador del escenario
        descripcion     : Descripción ejecutiva del escenario
        factor_riesgo   : Magnitud del shock (interpretación depende del tipo)
        tipo            : Tipo de variable afectada por el shock
    """
    nombre:        str
    descripcion:   str
    factor_riesgo: float
    tipo:          str   # CASHFLOW_DROP | INGRESO_REDUCCION | CAJA_REDUCCION | SEVERANCE_MULTIPLICADOR


# ══════════════════════════════════════════════════════════════════════════════
# ESCENARIOS ESTÁNDAR
# ══════════════════════════════════════════════════════════════════════════════

PANDEMIA = CrisisScenario(
    nombre        = "PANDEMIA",
    descripcion   = "Caída de ingresos del 40% por disrupción operativa o sanitaria.",
    factor_riesgo = 0.40,    # ingresos *= (1 - 0.40) → ingresos *= 0.60
    tipo          = "CASHFLOW_DROP",
)

PERDIDA_CLIENTE = CrisisScenario(
    nombre        = "PERDIDA_CLIENTE",
    descripcion   = "Pérdida del cliente principal, representando 25% de los ingresos.",
    factor_riesgo = 0.25,    # ingresos *= (1 - 0.25) → ingresos *= 0.75
    tipo          = "CASHFLOW_DROP",
)

AUDITORIA_SAT = CrisisScenario(
    nombre        = "AUDITORIA_SAT",
    descripcion   = "Auditoría SAT con multa estimada equivalente al 30% de ingresos mensuales.",
    factor_riesgo = 0.30,    # caja -= ingresos_mensuales * 0.30
    tipo          = "CAJA_REDUCCION",
)

DEMANDA_LABORAL = CrisisScenario(
    nombre        = "DEMANDA_LABORAL",
    descripcion   = "Demanda laboral colectiva que duplica la estimación de severance.",
    factor_riesgo = 2.0,     # severance_estimado *= 2.0
    tipo          = "SEVERANCE_MULTIPLICADOR",
)


# ══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO COMPLETO
# ══════════════════════════════════════════════════════════════════════════════

ESCENARIOS: Dict[str, CrisisScenario] = {
    "pandemia":        PANDEMIA,
    "perdida_cliente": PERDIDA_CLIENTE,
    "auditoria_sat":   AUDITORIA_SAT,
    "demanda_laboral": DEMANDA_LABORAL,
}


def get_escenario(nombre: str) -> CrisisScenario:
    """
    Retorna escenario por nombre (case-insensitive).
    Lanza KeyError si no existe.
    """
    key = nombre.lower()
    if key not in ESCENARIOS:
        raise KeyError(
            f"Escenario '{nombre}' no existe. "
            f"Disponibles: {list(ESCENARIOS.keys())}"
        )
    return ESCENARIOS[key]
