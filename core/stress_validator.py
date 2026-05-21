# ============================================================
# MESAN Omega -- STRESS TEST & VALIDATION LAYER v1.0
# ============================================================

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class Hallazgo:
    tipo: str
    severidad: str
    mensaje: str
    campo: str
    recomendacion: str


@dataclass
class ResultadoStress:
    score_integridad: int
    estado: str
    hallazgos: List[Hallazgo] = field(default_factory=list)
    inconsistencias: List[str] = field(default_factory=list)
    alertas_criticas: List[str] = field(default_factory=list)
    recomendaciones: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MesanStressValidator:

    def __init__(self):
        self.limites = {"MAX_SCORE": 100, "MIN_SCORE": 0, "MAX_SURVIVAL_DAYS": 365, "MIN_CONFIDENCE": 35}

    def _safe(self, value):
        try:
            return 0 if value is None else float(value)
        except:
            return 0

    def validar(self, data: Dict[str, Any]) -> ResultadoStress:

        hallazgos = []; inconsistencias = []; alertas = []; recomendaciones = []
        integridad = 100

        ingresos     = self._safe(data.get("ingresos"))
        nomina       = self._safe(data.get("nomina"))
        gastos       = self._safe(data.get("gastos"))
        deuda        = self._safe(data.get("deuda_mensual"))
        iva          = self._safe(data.get("iva"))
        isr          = self._safe(data.get("isr_retenido"))
        trabajadores = self._safe(data.get("trabajadores"))
        sin_imss     = self._safe(data.get("trabajadores_sin_imss"))
        impacto      = self._safe(data.get("impacto_estimado"))

        if ingresos < 0:
            integridad -= 20
            hallazgos.append(Hallazgo("FINANCIERO", "CRITICO", "Ingresos negativos detectados.", "ingresos", "Validar origen del dato."))

        if nomina > ingresos * 3 and ingresos > 0:
            integridad -= 10
            inconsistencias.append("Nomina desproporcionada respecto a ingresos.")

        if deuda > ingresos * 5 and ingresos > 0:
            integridad -= 15
            alertas.append("Deuda mensual extremadamente elevada.")

        if sin_imss > trabajadores and trabajadores > 0:
            integridad -= 25
            hallazgos.append(Hallazgo("LABORAL", "CRITICO", "Trabajadores sin IMSS exceden plantilla.", "trabajadores_sin_imss", "Corregir captura de empleados."))

        if trabajadores == 0 and nomina > 0:
            integridad -= 15
            inconsistencias.append("Existe nomina sin trabajadores registrados.")

        if iva > ingresos * 2 and ingresos > 0:
            integridad -= 10
            alertas.append("IVA superior a ingresos declarados.")

        if isr > ingresos and ingresos > 0:
            integridad -= 10
            alertas.append("ISR retenido excede ingresos mensuales.")

        burn_rate = nomina + gastos + deuda
        flujo = ingresos - burn_rate

        if burn_rate <= 0:
            integridad -= 20
            hallazgos.append(Hallazgo("OPERATIVO", "ALTO", "Burn rate invalido o igual a cero.", "burn_rate", "Validar gastos y deuda."))

        if data.get("reglas_duplicadas"):
            integridad -= 12
            inconsistencias.append("Se detectaron reglas duplicadas.")

        if data.get("multiples_scores"):
            integridad -= 15
            inconsistencias.append("Existen multiples motores alterando score final.")

        if data.get("override_manual"):
            integridad -= 18
            alertas.append("Override manual detectado en resultados.")

        if data.get("vacaciones_pagadas") and data.get("calculo_vacaciones_incluido"):
            integridad -= 25
            hallazgos.append(Hallazgo("LEGAL", "CRITICO", "El sistema incluyo vacaciones ya pagadas dentro del finiquito.", "vacaciones", "Excluir vacaciones y prima vacacional si ya fueron liquidadas."))

        if flujo > 0 and data.get("nivel_riesgo") == "CRITICO":
            integridad -= 10
            inconsistencias.append("Flujo positivo con riesgo critico declarado.")

        if flujo < 0 and data.get("nivel_riesgo") == "BAJO":
            integridad -= 20
            inconsistencias.append("Flujo negativo incompatible con riesgo bajo.")

        if ingresos > 0 and impacto > ingresos * 100:
            integridad -= 10
            alertas.append("Impacto estimado posiblemente exagerado.")

        if data.get("zona_salario") is None:
            recomendaciones.append("Solicitar zona salarial antes de calcular finiquitos.")
        if data.get("tipo_contrato") is None:
            recomendaciones.append("Solicitar tipo de contrato antes de calcular liquidaciones.")
        if data.get("vacaciones_pagadas") is None:
            recomendaciones.append("Confirmar si vacaciones y prima vacacional ya fueron cubiertas.")

        integridad = max(0, min(100, integridad))

        if integridad >= 90:   estado = "ESTABLE"
        elif integridad >= 75: estado = "OBSERVACION"
        elif integridad >= 55: estado = "RIESGO"
        else:                  estado = "CRITICO"

        if integridad < 80:
            recomendaciones.append("Activar auditoria interna de reglas.")
        if len(inconsistencias) >= 3:
            recomendaciones.append("Separar motor financiero, fiscal y laboral.")
        if len(alertas) >= 2:
            recomendaciones.append("Ejecutar pruebas de estres antes de produccion.")

        return ResultadoStress(score_integridad=integridad, estado=estado, hallazgos=hallazgos, inconsistencias=inconsistencias, alertas_criticas=alertas, recomendaciones=recomendaciones)
