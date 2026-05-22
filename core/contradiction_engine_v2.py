# core/contradiction_engine_v2.py
# MESAN Omega — Contradiction Engine v2 (Enterprise Hardened)

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime


# =========================================================
# ENUMS
# =========================================================

class Severity(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class Contradiction:
    rule_id: str
    tipo: str
    descripcion: str
    severidad: Severity
    confidence_penalty: int
    explicacion: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ContradictionResult:
    tiene_contradicciones: bool
    contradicciones: List[Contradiction] = field(default_factory=list)
    confidence_penalty_total: int = 0
    engine_version: str = "2.0.0"


# =========================================================
# ENGINE
# =========================================================

class ContradictionEngineV2:

    ENGINE_VERSION = "2.0.0"

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

    @staticmethod
    def safe_int(value, default=0) -> int:
        try:
            if value in [None, "", "null"]:
                return default
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def safe_bool(value, default=False) -> bool:

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            value = value.strip().lower()

            if value in ["true", "1", "si", "sí", "yes"]:
                return True

            if value in ["false", "0", "no"]:
                return False

        return default

    # =====================================================
    # MAIN DETECTION
    # =====================================================

    def detect(self, data: Dict[str, Any]) -> ContradictionResult:

        contradicciones: List[Contradiction] = []

        # =================================================
        # NORMALIZED INPUTS
        # =================================================

        ingresos = self.safe_float(data.get("ingresos_mensuales"))

        nomina = self.safe_float(data.get("nomina"))
        gastos = self.safe_float(data.get("gastos"))
        deuda_mensual = self.safe_float(data.get("deuda_mensual"))

        flujo = self.safe_float(
            data.get(
                "flujo_operativo",
                ingresos - nomina - gastos - deuda_mensual
            )
        )

        dias = self.safe_int(data.get("dias_supervivencia"), 999)

        # SCORE:
        # 0 = muy malo
        # 100 = excelente
        score = self.safe_int(data.get("score"))

        sin_imss = self.safe_int(data.get("trabajadores_sin_imss"))

        isr = self.safe_float(data.get("isr_retenido"))

        repse = self.safe_bool(data.get("repse_activo"))

        cartera = self.safe_float(data.get("cartera_vencida"))

        vacaciones_pagadas = self.safe_bool(
            data.get("vacaciones_pagadas")
        )

        vacaciones_adeudadas = self.safe_bool(
            data.get("vacaciones_adeudadas")
        )

        # =================================================
        # INTERNAL ADD METHOD
        # =================================================

        def add(
            rule_id: str,
            tipo: str,
            desc: str,
            sev: Severity,
            penalty: int,
            expl: str
        ):

            contradicciones.append(
                Contradiction(
                    rule_id=rule_id,
                    tipo=tipo,
                    descripcion=desc,
                    severidad=sev,
                    confidence_penalty=penalty,
                    explicacion=expl
                )
            )

        # =================================================
        # RULES
        # =================================================

        # -------------------------------------------------
