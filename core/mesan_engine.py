class MesanOmegaEngine:
    """
    Motor central MESAN Ω v6
    Prioriza flujo de efectivo sobre cualquier otro riesgo.
    """

    def __init__(self, data: dict):
        self.data = data or {}

    def _get(self, key, default=0):
        return self.data.get(key, default)

    def evaluar_financiero(self):
        ventas = self._get("ventas_mensuales")
        costos = self._get("costos_fijos")
        caja = self._get("caja_disponible")

        deficit = costos - ventas

        if deficit <= 0:
            return {"nivel": "ESTABLE", "deficit": 0, "dias": None}

        deficit_diario = deficit / 30
        dias = int(caja / deficit_diario) if deficit_diario > 0 else None

        if dias is None:
            nivel = "ALTO"
        elif dias < 30:
            nivel = "CRÍTICO"
        elif dias < 60:
            nivel = "ALTO"
        else:
            nivel = "MEDIO"

        return {"nivel": nivel, "deficit": round(deficit, 2), "dias": dias}

    def evaluar_operativo(self):
        horas = self._get("horas_semanales", 40)
        empleados = self._get("empleados", 1)
        nomina = self._get("nomina", 0)

        exceso = max(0, horas - 40)
        costo_hora = (nomina / 30) / 8 if nomina else 0
        sobrecosto = exceso * 4 * empleados * (costo_hora * 2)

        if exceso > 8:
            nivel = "ALTO"
        elif exceso > 4:
            nivel = "MEDIO"
        else:
            nivel = "BAJO"

        return {"nivel": nivel, "sobrecosto": round(sobrecosto, 2)}

    def evaluar_rotacion(self):
        bajas = self._get("bajas")
        salario = self._get("salario_promedio")
        reclutamiento = self._get("costo_reclutamiento")

        impacto = bajas * ((salario * 3.5) + reclutamiento)

        if bajas >= 5:
            nivel = "ALTO"
        elif bajas >= 2:
            nivel = "MEDIO"
        else:
            nivel = "BAJO"

        return {"nivel": nivel, "impacto": round(impacto, 2)}

    def nivel_global(self, niveles):
        prioridad = ["CRÍTICO", "ALTO", "MEDIO", "BAJO", "ESTABLE"]
        return min(niveles, key=lambda x: prioridad.index(x) if x in prioridad else 99)

    def construir_mensaje(self, financiero):
        if financiero["deficit"] > 0:
            dias_txt = f"{financiero['dias']} días" if financiero["dias"] is not None else "periodo indefinido"
            return (
                f"Tu empresa pierde aproximadamente ${financiero['deficit']:,.0f} MXN al mes. "
                f"Con la liquidez actual, tienes cerca de {dias_txt} antes de presión crítica. "
                f"Esto es un problema de flujo, no solo operativo."
            )
        return "Tu operación es sostenible con el flujo actual."

    def ejecutar(self):
        financiero = self.evaluar_financiero()
        operativo = self.evaluar_operativo()
        rotacion = self.evaluar_rotacion()

        nivel = self.nivel_global([
            financiero["nivel"],
            operativo["nivel"],
            rotacion["nivel"]
        ])

        # Override financiero — nunca sale BAJO con pérdidas
        if financiero["nivel"] in ["ALTO", "CRÍTICO"]:
            nivel = financiero["nivel"]

        impacto_total = (
            financiero["deficit"] +
            operativo["sobrecosto"] +
            rotacion["impacto"]
        )

        return {
            "engine": "MESAN Ω v6",
            "nivel_alerta": nivel,
            "impacto_total_mensual": round(impacto_total, 2),
            "financiero": financiero,
            "operativo": operativo,
            "rotacion": rotacion,
            "mensaje": self.construir_mensaje(financiero)
        }
