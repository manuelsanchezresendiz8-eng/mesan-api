class MotorFinanciero:

    def __init__(self, data):
        self.data = data
        self.nomina = data.get("nomina", 0)
        self.empleados = data.get("empleados", 1)
        self.costo_hora_base = ((self.nomina / 30) / 8) if self.nomina else 0

    def calcular_nearshoring(self):
        horas = self.data.get("horas_semanales", 40)
        exceso = max(0, horas - 40)
        horas_extra_mes = exceso * 4 * self.empleados
        sobrecosto = horas_extra_mes * (self.costo_hora_base * 2)
        if exceso > 8:
            riesgo = "CRÍTICO"
            impacto_score = 25
        elif exceso > 4:
            riesgo = "ALTO"
            impacto_score = 15
        else:
            riesgo = "MEDIO"
            impacto_score = 5
        return {
            "horas_extra_mes": horas_extra_mes,
            "sobrecosto": round(sobrecosto, 2),
            "riesgo": riesgo,
            "impacto_score": impacto_score
        }

    def calcular_rotacion(self):
        bajas = self.data.get("bajas", 0)
        salario = self.data.get("salario_promedio", 0)
        reclutamiento = self.data.get("costo_reclutamiento", 0)
        impacto = bajas * (salario * 3.5 + reclutamiento)
        return {
            "bajas": bajas,
            "impacto_mensual": round(impacto, 2),
            "impacto_anual": round(impacto * 12, 2),
            "riesgo": "ALTO" if bajas > 3 else "MEDIO",
            "impacto_score": 20 if impacto > 50000 else 10
        }

    def ejecutar(self):
        near = self.calcular_nearshoring()
        rot = self.calcular_rotacion()
        score = 100
        score -= near["impacto_score"]
        score -= rot["impacto_score"]
        impacto_total = near["sobrecosto"] + rot["impacto_mensual"]
        return {
            "engine": "MESAN Ω v4",
            "score": max(round(score, 2), 0),
            "impacto_total_mensual": round(impacto_total, 2),
            "nearshoring": near,
            "rotacion": rot
        }
