from datetime import datetime, timedelta


class GestionPropuestas:

    def __init__(self):
        self.nombre_modulo = "Modulo de Cierre Omega"

    def calcular_fecha_vencimiento(self, fecha_emision: str, dias_habiles: int = 5) -> str:
        fecha_actual = datetime.strptime(fecha_emision, "%Y-%m-%d")
        dias_sumados = 0

        while dias_sumados < dias_habiles:
            fecha_actual += timedelta(days=1)
            if fecha_actual.weekday() < 5:
                dias_sumados += 1

        return fecha_actual.strftime("%Y-%m-%d")

    def dias_por_urgencia(self, indice_omega: float) -> int:
        if indice_omega >= 75:
            return 2
        elif indice_omega >= 50:
            return 4
        else:
            return 7

    def generar_propuesta(self, resultado: dict, fecha_emision: str) -> dict:
        indice = resultado.get("indice_omega", {}).get("indice_omega", 0)
        dinero = resultado.get("impacto", {}).get("impacto_anual_max", 0)

        dias = self.dias_por_urgencia(indice)
        fecha_limite = self.calcular_fecha_vencimiento(fecha_emision, dias_habiles=dias)

        return {
            "indice": indice,
            "dinero_en_riesgo": dinero,
            "fecha_limite": fecha_limite,
            "dias_disponibles": dias,
            "mensaje": self._mensaje_cierre(indice, dinero, fecha_limite)
        }

    def _mensaje_cierre(self, indice: float, dinero: float, fecha_limite: str) -> str:
        if indice >= 75:
            return (
                f"Tu empresa presenta riesgo CRITICO.\n\n"
                f"Perdida estimada anual: ${dinero:,.0f} MXN\n\n"
                f"Esta propuesta expira el {fecha_limite}.\n\n"
                f"Recomendacion: iniciar intervencion inmediata."
            )
        elif indice >= 50:
            return (
                f"Detectamos riesgo operativo relevante.\n\n"
                f"Impacto estimado: ${dinero:,.0f} MXN\n\n"
                f"La propuesta es valida hasta {fecha_limite}."
            )
        return (
            f"Empresa en estado estable.\n\n"
            f"Oportunidad de mejora detectada.\n\n"
            f"Vigencia hasta {fecha_limite}."
        )

    def verificar_estatus_propuesta(self, fecha_emision: str, fecha_firma: str, indice: float) -> dict:
        dias = self.dias_por_urgencia(indice)
        limite = self.calcular_fecha_vencimiento(fecha_emision, dias)

        limite_dt = datetime.strptime(limite, "%Y-%m-%d")
        firma_dt = datetime.strptime(fecha_firma, "%Y-%m-%d")

        if firma_dt <= limite_dt:
            return {
                "estatus": "APROBADA",
                "mensaje": "Espacio operativo reservado correctamente."
            }

        return {
            "estatus": "EXPIRADA",
            "mensaje": f"Propuesta vencida el {limite}. Requiere recalculo de costo."
        }
