# core/exposure_engine.py
# MESAN Omega — Exposure Engine v2.0
# Enterprise Hardened | Deterministic | Auditable

from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import importlib
import uuid


# ============================================================
# GLOBAL CONFIG
# ============================================================

ENGINE_VERSION = "2.0.0"

REGULATION_MAP = {
    "IMSS": "regulations.imss_2026_01",
    "SAT": None,
    "INFONAVIT": None,
}


# ============================================================
# ENUMS
# ============================================================

class RiskLevel(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ExposureItem:
    item_id: str
    concepto: str
    formula: str
    valor_input: float
    resultado: float
    version_regulatoria: str
    explicacion: str
    categoria: str
    riesgo: RiskLevel
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


@dataclass
class ExposureResult:
    score_ponderado: float
    nivel_riesgo: RiskLevel

    exposicion_min: float
    exposicion_probable: float
    exposicion_max: float

    items: List[ExposureItem] = field(
        default_factory=list
    )

    cascadas: List[str] = field(
        default_factory=list
    )

    regulatory_versions: Dict[str, str] = field(
        default_factory=dict
    )

    trace_id: str = ""

    engine_version: str = ENGINE_VERSION

    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ============================================================
# ENGINE
# ============================================================

class ExposureEngine:

    VERSION = ENGINE_VERSION

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        regulation: str = "IMSS_2026_01"
    ):

        self.reg_version = regulation

        try:

            self.imss = importlib.import_module(
                "regulations.imss_2026_01"
            )

        except ModuleNotFoundError:

            self.imss = None

    # ========================================================
    # SAFE PARSERS
    # ========================================================

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

    # ========================================================
    # RISK LEVEL
    # ========================================================

    def _risk(self, score: float) -> RiskLevel:

        if score >= 75:
            return RiskLevel.CRITICO

        if score >= 50:
            return RiskLevel.ALTO

        if score >= 25:
            return RiskLevel.MEDIO

        return RiskLevel.BAJO

    # ========================================================
    # ITEM FACTORY
    # ========================================================

    def _item(
        self,
        concepto: str,
        formula: str,
        valor_input: float,
        resultado: float,
        version_regulatoria: str,
        explicacion: str,
        categoria: str,
        riesgo: RiskLevel
    ) -> ExposureItem:

        return ExposureItem(

            item_id=str(uuid.uuid4()),

            concepto=concepto,

            formula=formula,

            valor_input=round(
                self.safe_float(valor_input),
                2
            ),

            resultado=round(
                self.safe_float(resultado),
                2
            ),

            version_regulatoria=version_regulatoria,

            explicacion=explicacion,

            categoria=categoria,

            riesgo=riesgo

        )

    # ========================================================
    # IMSS
    # ========================================================

    def calcular_imss(
        self,
        trabajadores_sin_alta: int,
        salario_diario: float,
        meses_omision: int = 1
    ) -> ExposureItem:

        trabajadores_sin_alta = max(
            self.safe_int(trabajadores_sin_alta),
            0
        )

        salario_diario = max(
            self.safe_float(salario_diario),
            0
        )

        meses_omision = max(
            self.safe_int(meses_omision),
            1
        )

        if not self.imss:

            return self._item(

                concepto="Contingencia IMSS",

                formula="N/A",

                valor_input=0,

                resultado=0,

                version_regulatoria="N/A",

                explicacion="Regulación IMSS no cargada.",

                categoria="IMSS",

                riesgo=RiskLevel.MEDIO

            )

        sbc = salario_diario * 30

        cuota = getattr(
            self.imss,
            "CUOTA_TOTAL_PATRONAL",
            0.30
        )

        base = (
            trabajadores_sin_alta *
            sbc *
            cuota *
            meses_omision
        )

        multa_data = self.imss.calcular_multa(
            "omision_alta"
        )

        multa_min = (
            multa_data["min_mxn"] *
            trabajadores_sin_alta
        )

        multa_max = (
            multa_data["max_mxn"] *
            trabajadores_sin_alta
        )

        recargos = (
            base *
            getattr(
                self.imss,
                "RECARGOS_MENSUALES",
                0.01
            ) *
            meses_omision
        )

        total = (
            base +
            multa_min +
            recargos
        )

        riesgo = self._risk(
            min(total / 100000, 100)
        )

        return self._item(

            concepto="Contingencia IMSS",

            formula=(
                f"trabajadores({trabajadores_sin_alta}) "
                f"x SBC({sbc:.0f}) "
                f"x cuota({cuota:.4f}) "
                f"x meses({meses_omision}) "
                f"+ multas + recargos"
            ),

            valor_input=trabajadores_sin_alta,

            resultado=total,

            version_regulatoria=getattr(
                self.imss,
                "VERSION",
                "IMSS_UNKNOWN"
            ),

            explicacion=(
                f"{trabajadores_sin_alta} "
                f"trabajadores sin alta generan "
                f"cuotas omitidas "
                f"de ${base:,.0f}, "
                f"multas "
                f"${multa_min:,.0f}-"
                f"${multa_max:,.0f} "
                f"y recargos "
                f"${recargos:,.0f}."
            ),

            categoria="IMSS",

            riesgo=riesgo

        )

    # ========================================================
    # INFONAVIT
    # ========================================================

    def calcular_infonavit(
        self,
        trabajadores: int,
        salario_diario: float,
        meses: int = 1
    ) -> ExposureItem:

        trabajadores = max(
            self.safe_int(trabajadores),
            0
        )

        salario_diario = max(
            self.safe_float(salario_diario),
            0
        )

        meses = max(
            self.safe_int(meses),
            1
        )

        aportacion = (
            getattr(
                self.imss,
                "CUOTAS_PATRONALES",
                {}
            ).get(
                "infonavit_aportacion_patronal",
                0.05
            )
            if self.imss
            else 0.05
        )

        sbc = salario_diario * 30

        base = (
            trabajadores *
            sbc *
            aportacion *
            meses
        )

        multa = (
            trabajadores *
            350 *
            (
                getattr(
                    self.imss,
                    "UMA_DIARIA",
                    108.57
                )
                if self.imss
                else 108.57
            )
        )

        riesgo = self._risk(
            min(base / 50000, 100)
        )

        return self._item(

            concepto="Exposición INFONAVIT",

            formula=(
                f"trabajadores({trabajadores}) "
                f"x SBC({sbc:.0f}) "
                f"x {aportacion:.2%} "
                f"x meses({meses})"
            ),

            valor_input=trabajadores,

            resultado=base,

            version_regulatoria=self.reg_version,

            explicacion=(
                f"Aportaciones INFONAVIT "
                f"omitidas: ${base:,.0f}. "
                f"Multa máxima estimada: "
                f"${multa:,.0f}."
            ),

            categoria="INFONAVIT",

            riesgo=riesgo

        )

    # ========================================================
    # SAT
    # ========================================================

    def calcular_sat(
        self,
        isr_retenido: float,
        iva_pendiente: float,
        meses_mora: int = 1
    ) -> ExposureItem:

        isr_retenido = max(
            self.safe_float(isr_retenido),
            0
        )

        iva_pendiente = max(
            self.safe_float(iva_pendiente),
            0
        )

        meses_mora = max(
            self.safe_int(meses_mora),
            1
        )

        recargo_mensual = 0.006

        total_fiscal = (
            isr_retenido +
            iva_pendiente
        )

        recargos = (
            total_fiscal *
            recargo_mensual *
            meses_mora
        )

        multa_base = total_fiscal * 0.55

        total = (
            total_fiscal +
            recargos +
            multa_base
        )

        riesgo = self._risk(
            min(total / 100000, 100)
        )

        return self._item(

            concepto="Riesgo SAT",

            formula=(
                f"(ISR {isr_retenido:,.0f} "
                f"+ IVA {iva_pendiente:,.0f}) "
                f"x (1 + recargos + multa 55%)"
            ),

            valor_input=total_fiscal,

            resultado=total,

            version_regulatoria="SAT_2026_05",

            explicacion=(
                f"Adeudo fiscal "
                f"${total_fiscal:,.0f}, "
                f"recargos "
                f"${recargos:,.0f}, "
                f"multa estimada "
                f"${multa_base:,.0f}. "
                f"Exposición total "
                f"${total:,.0f}."
            ),

            categoria="SAT",

            riesgo=riesgo

        )

    # ========================================================
    # MAIN ENGINE
    # ========================================================

    def analizar(
        self,
        data: Dict[str, Any],
        trace_id: str = ""
    ) -> ExposureResult:

        if not trace_id:

            trace_id = str(uuid.uuid4())

        items = []

        cascadas = []

        trabajadores_sin_imss = self.safe_int(
            data.get("trabajadores_sin_imss")
        )

        salario_diario = self.safe_float(
            data.get(
                "salario_diario_promedio",
                350
            )
        )

        meses_omision = self.safe_int(
            data.get(
                "meses_omision",
                1
            )
        )

        isr = self.safe_float(
            data.get("isr_retenido")
        )

        iva = self.safe_float(
            data.get("iva")
        )

        trabajadores = self.safe_int(
            data.get(
                "trabajadores",
                trabajadores_sin_imss
            )
        )

        # ====================================================
        # IMSS
        # ====================================================

        if trabajadores_sin_imss > 0:

            item = self.calcular_imss(
                trabajadores_sin_imss,
                salario_diario,
                meses_omision
            )

            items.append(item)

            cascadas.append(
                "IMSS omitido -> inspección -> "
                "cuotas retroactivas -> "
                "multas -> embargo"
            )

        # ====================================================
        # INFONAVIT
        # ====================================================

        if trabajadores_sin_imss > 0:

            item2 = self.calcular_infonavit(
                trabajadores_sin_imss,
                salario_diario,
                meses_omision
            )

            items.append(item2)

        # ====================================================
        # SAT
        # ====================================================

        if isr > 0 or iva > 0:

            item3 = self.calcular_sat(
                isr,
                iva,
                meses_omision
            )

            items.append(item3)

            cascadas.append(
                "ISR/IVA pendiente -> "
                "requerimiento SAT -> "
                "embargo -> "
                "bloqueo bancario"
            )

        # ====================================================
        # TOTALS
        # ====================================================

        total = sum(

            self.safe_float(i.resultado)

            for i in items

        )

        exposicion_min = round(
            total * 0.60,
            2
        )

        exposicion_probable = round(
            total,
            2
        )

        exposicion_max = round(
            total * 1.80,
            2
        )

        # ====================================================
        # WEIGHTED SCORE
        # ====================================================

        score = 0

        if trabajadores_sin_imss > 0:

            score += min(
                trabajadores_sin_imss * 2,
                35
            )

        if isr > 0:
            score += 30

        if iva > 0:
            score += 15

        score = min(score, 100)

        nivel = self._risk(score)

        # ====================================================
        # RETURN
        # ====================================================

        return ExposureResult(

            score_ponderado=score,

            nivel_riesgo=nivel,

            exposicion_min=exposicion_min,

            exposicion_probable=exposicion_probable,

            exposicion_max=exposicion_max,

            items=items,

            cascadas=cascadas,

            regulatory_versions={

                "IMSS":
                getattr(
                    self.imss,
                    "VERSION",
                    "N/A"
                ),

                "SAT":
                "SAT_2026_05",

                "INFONAVIT":
                self.reg_version

            },

            trace_id=trace_id,

            engine_version=self.VERSION

        )
