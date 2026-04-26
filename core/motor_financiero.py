# =============================================
# FUNCIÓN LEGACY — requerida por panel_pro
# =============================================
def evaluar_servicio(precio_cliente, empleados, zona="general"):
    smg = 278.80 if zona == "frontera" else 248.93
    salario_base = smg * 30
    imss = salario_base * 0.2497
    infonavit = salario_base * 0.05
    costo_empleado = salario_base + imss + infonavit
    costo_total = costo_empleado * empleados
    utilidad = precio_cliente - costo_total
    margen = round((utilidad / precio_cliente * 100), 2) if precio_cliente else 0
    reserva = round(costo_total * 0.08, 2)

    if margen > 30:
        clasificacion = "RENTABLE"
        decision = {"decision": "ACEPTAR", "mensaje": "Margen saludable — operación viable"}
    elif margen > 10:
        clasificacion = "AJUSTADO"
        decision = {"decision": "REVISAR", "mensaje": "Margen bajo — evaluar optimización"}
    else:
        clasificacion = "EN RIESGO"
        decision = {"decision": "RECHAZAR", "mensaje": "Margen insuficiente — pérdida probable"}

    precio_minimo = round(costo_total * 1.05, 2)
    precio_cierre = round(costo_total * 1.15, 2)
    precio_objetivo = round(costo_total * 1.35, 2)

    return {
        "clasificacion": clasificacion,
        "decision": decision,
        "financiero": {
            "ingreso": precio_cliente,
            "costo_total": round(costo_total, 2),
            "utilidad": round(utilidad, 2),
            "margen": margen,
            "reserva": reserva,
            "salario": round(salario_base, 2)
        },
        "precios": {
            "precio_minimo": precio_minimo,
            "precio_cierre": precio_cierre,
            "precio_objetivo": precio_objetivo
        }
    }


# =============================================
# MOTOR FINANCIERO PRINCIPAL
# =============================================
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
