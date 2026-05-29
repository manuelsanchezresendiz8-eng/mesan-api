# services/continuity_engine.py -- MESAN Omega Continuity Engine v2.0 CLEAN

from dataclasses import dataclass


@dataclass
class Empresa:
    nombre: str
    ingresos_mensuales: float
    nomina_mensual: float
    empleados: int
    empleados_criticos: int
    caja_disponible: float
    deuda_mensual: float
    demandas_laborales: int
    trabajadores_sin_imss: int
    rotacion_anual: float
    severance_estimado: float
    riesgo_sat: str
    riesgo_imss: str
    repse_suspendido: bool


class ContinuityEngine:

    def calcular_dscr(self, ingresos, deuda):
        if deuda <= 0:
            return 10.0
        return round(ingresos / deuda, 2)

    def calcular_burn_rate(self, ingresos, gastos):
        if ingresos <= 0:
            return 100.0
        return round((gastos / ingresos) * 100, 2)

    def calcular_severance_pressure(self, caja, severance):
        if caja <= 0:
            return 100.0
        return round((severance / caja) * 100, 2)

    def calcular_workforce_risk(self, empleados, sin_imss, rotacion):
        if empleados <= 0:
            return 100.0

        score = (
            ((sin_imss / empleados) * 50) +
            ((rotacion / 100) * 50)
        )

        return round(min(score, 100), 2)

    def clasificar(self, score):

        if score >= 80:
            return "ESTABLE"

        if score >= 60:
            return "PRESION_OPERATIVA"

        if score >= 40:
            return "RIESGO_ALTO"

        return "RIESGO_CRITICO"

    def generar_recomendacion(self, score):

        if score >= 80:
            return "Mantener monitoreo preventivo."

        if score >= 60:
            return "Optimizar liquidez y reducir exposicion laboral."

        if score >= 40:
            return "Implementar War Room financiero inmediato."

        return "Activar protocolo de supervivencia empresarial."

    def calcular_continuity_score(self, empresa: Empresa):

        dscr = self.calcular_dscr(
            empresa.ingresos_mensuales,
            empresa.deuda_mensual
        )

        burn_rate = self.calcular_burn_rate(
            empresa.ingresos_mensuales,
            empresa.nomina_mensual + empresa.deuda_mensual
        )

        severance_pressure = self.calcular_severance_pressure(
            empresa.caja_disponible,
            empresa.severance_estimado
        )

        workforce_risk = self.calcular_workforce_risk(
            empresa.empleados,
            empresa.trabajadores_sin_imss,
            empresa.rotacion_anual
        )

        score = 100

        # DSCR
        if dscr < 1:
            score -= 30
        elif dscr < 1.5:
            score -= 15

        # Burn Rate
        if burn_rate > 80:
            score -= 20
        elif burn_rate > 60:
            score -= 10

        # Severance Pressure
        if severance_pressure > 70:
            score -= 20
        elif severance_pressure > 40:
            score -= 10

        # Workforce Risk
        if workforce_risk > 70:
            score -= 20
        elif workforce_risk > 40:
            score -= 10

        # SAT
        if empresa.riesgo_sat.upper() == "NEGATIVO":
            score -= 15

        # IMSS
        if empresa.riesgo_imss.upper() == "NEGATIVO":
            score -= 15

        # REPSE
        if empresa.repse_suspendido:
            score -= 20

        score = max(score, 0)

        nivel = self.clasificar(score)

        return {
            "empresa": empresa.nombre,
            "continuity_score": score,
            "nivel": nivel,
            "metricas": {
                "dscr": dscr,
                "burn_rate": burn_rate,
                "severance_pressure": severance_pressure,
                "workforce_risk": workforce_risk
            },
            "recomendacion": self.generar_recomendacion(score)
        }


class SeveranceEngine:

    def calcular_liquidacion(
        self,
        salario_mensual,
        antiguedad_anios,
        vacaciones_pendientes=0
    ):

        salario_diario = salario_mensual / 30

        indemnizacion_90 = salario_diario * 90

        prima_antiguedad = (
            salario_diario *
            12 *
            antiguedad_anios
        )

        vacaciones = salario_diario * vacaciones_pendientes

        total = (
            indemnizacion_90 +
            prima_antiguedad +
            vacaciones
        )

        return {
            "indemnizacion_90_dias": round(indemnizacion_90, 2),
            "prima_antiguedad": round(prima_antiguedad, 2),
            "vacaciones": round(vacaciones, 2),
            "total_estimado": round(total, 2)
        }


class WarRoomEngine:

    def generar_plan_306090(self, nivel):

        planes = {

            "ESTABLE": {
                "30_dias": "Optimizacion preventiva",
                "60_dias": "Automatizacion financiera",
                "90_dias": "Escalamiento operativo"
            },

            "PRESION_OPERATIVA": {
                "30_dias": "Reducir burn rate",
                "60_dias": "Reestructuracion parcial",
                "90_dias": "Blindaje fiscal"
            },

            "RIESGO_ALTO": {
                "30_dias": "Contencion de flujo",
                "60_dias": "Reestructura laboral",
                "90_dias": "Proteccion de activos"
            },

            "RIESGO_CRITICO": {
                "30_dias": "Supervivencia inmediata",
                "60_dias": "Negociacion bancaria",
                "90_dias": "Continuidad critica"
            }
        }

        return planes.get(
            nivel,
            planes["RIESGO_CRITICO"]
        )
