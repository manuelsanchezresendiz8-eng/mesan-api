# ============================================================
# MESAN Omega -- FINIQUITO ENGINE v3.0
# Labor Risk + Settlement Intelligence
# ============================================================

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime


@dataclass
class Escenario:
    nombre: str
    monto: float
    descripcion: str


@dataclass
class ResultadoFiniquito:
    ok: bool
    salario_diario: float
    vacaciones: float
    prima_vacacional: float
    aguinaldo_proporcional: float
    total_finiquito: float
    escenarios: List[Escenario]
    observaciones: List[str]
    confianza_modelo: str
    riesgo_laboral: str
    fecha_calculo: str
    disclaimer: str


class FiniquitoEngine:

    def __init__(self):
        self.salario_minimo_general  = 278.80
        self.salario_minimo_frontera = 419.88

    def calcular(self, data: Dict):

        observaciones = []

        salario_diario          = float(data.get("salario_diario", 0))
        zona_fronteriza         = data.get("zona_fronteriza", False)
        vacaciones_pagadas      = data.get("vacaciones_pagadas", False)
        prima_pagada            = data.get("prima_vacacional_pagada", False)
        contrato_obra           = data.get("contrato_obra_determinada", False)
        contrato_documentado    = data.get("contrato_documentado", False)
        acta_terminacion        = data.get("acta_terminacion_obra", False)
        meses_2026              = float(data.get("meses_trabajados_2026", 5))
        aguinaldo_dias          = int(data.get("aguinaldo_dias", 15))
        dias_vacaciones         = int(data.get("dias_vacaciones_pendientes", 0))
        trabajadores            = int(data.get("trabajadores", 1))

        if salario_diario <= 0:
            return ResultadoFiniquito(
                ok=False, salario_diario=0, vacaciones=0, prima_vacacional=0,
                aguinaldo_proporcional=0, total_finiquito=0, escenarios=[],
                observaciones=["No existe salario diario valido. El sistema no debe asumir salario minimo sin soporte documental."],
                confianza_modelo="BAJA", riesgo_laboral="INDETERMINADO",
                fecha_calculo=datetime.now().isoformat(),
                disclaimer="Calculo preventivo automatizado."
            )

        vacaciones = 0 if vacaciones_pagadas else dias_vacaciones * salario_diario
        if vacaciones_pagadas:
            observaciones.append("Vacaciones previamente pagadas; no se integran nuevamente.")

        prima_vacacional = 0 if prima_pagada else vacaciones * 0.25
        if prima_pagada:
            observaciones.append("Prima vacacional previamente cubierta.")

        aguinaldo_proporcional = aguinaldo_dias * (meses_2026 / 12) * salario_diario
        total_finiquito = vacaciones + prima_vacacional + aguinaldo_proporcional

        escenarios = [
            Escenario("Conservador", round(total_finiquito * trabajadores, 2), "Firma voluntaria sin conflicto."),
            Escenario("Probable",    round(total_finiquito * trabajadores * 1.25, 2), "Negociacion con gratificacion adicional."),
            Escenario("Critico",     round(total_finiquito * trabajadores * 2.50, 2), "Demanda laboral con costos legales.")
        ]

        riesgo_laboral = "MEDIO"
        if not contrato_documentado:
            riesgo_laboral = "ALTO"
            observaciones.append("No existe soporte documental suficiente del contrato laboral.")
        if contrato_obra and not acta_terminacion:
            riesgo_laboral = "ALTO"
            observaciones.append("No existe acta formal de terminacion de obra determinada.")
        if contrato_obra:
            observaciones.append("La procedencia de indemnizacion depende de la validez documental.")

        observaciones.append("El calculo depende del salario diario real acreditable.")
        if zona_fronteriza:
            observaciones.append("Zona fronteriza detectada. Validar salario real contra tablas regionales.")

        return ResultadoFiniquito(
            ok=True,
            salario_diario=round(salario_diario, 2),
            vacaciones=round(vacaciones, 2),
            prima_vacacional=round(prima_vacacional, 2),
            aguinaldo_proporcional=round(aguinaldo_proporcional, 2),
            total_finiquito=round(total_finiquito, 2),
            escenarios=escenarios,
            observaciones=observaciones,
            confianza_modelo="ALTA",
            riesgo_laboral=riesgo_laboral,
            fecha_calculo=datetime.now().isoformat(),
            disclaimer="Estimacion preventiva automatizada por MESAN Omega. No constituye dictamen laboral definitivo."
        )
