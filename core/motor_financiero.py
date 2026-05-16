# core/motor_financiero.py — MESAN Ω v2.5.0
# SMG 2026 actualizados — NO modificar sin verificar DOF

# =============================================
# SMG 2026 OFICIALES
# =============================================
SMG_FRONTERA = 447.00   # Zona Libre Frontera Norte
SMG_INTERIOR = 278.80   # Interior de la República

FACTOR_CARGA = 1.45     # IMSS + INFONAVIT + vacaciones + aguinaldo
IVA_FRONTERA = 0.08
IVA_INTERIOR = 0.16
MARGEN_MINIMO = 0.30


# =============================================
# FUNCIÓN LEGACY — requerida por panel_pro
# NO modificar firma — rompe panel_pro.html
# =============================================
def evaluar_servicio(precio_cliente, empleados, zona="general"):
    smg = SMG_FRONTERA if zona == "frontera" else SMG_INTERIOR
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
        decision = {"decision": "ACEPTAR", "mensaje": "Margen saludable — operacion viable"}
    elif margen > 10:
        clasificacion = "AJUSTADO"
        decision = {"decision": "REVISAR", "mensaje": "Margen bajo — evaluar optimizacion"}
    else:
        clasificacion = "EN RIESGO"
        decision = {"decision": "RECHAZAR", "mensaje": "Margen insuficiente — perdida probable"}

    precio_minimo  = round(costo_total * 1.05, 2)
    precio_cierre  = round(costo_total * 1.15, 2)
    precio_objetivo = round(costo_total * 1.35, 2)

    return {
        "clasificacion": clasificacion,
        "decision": decision,
        "financiero": {
            "ingreso":     precio_cliente,
            "costo_total": round(costo_total, 2),
            "utilidad":    round(utilidad, 2),
            "margen":      margen,
            "reserva":     reserva,
            "salario":     round(salario_base, 2)
        },
        "precios": {
            "precio_minimo":   precio_minimo,
            "precio_cierre":   precio_cierre,
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
            riesgo = "CRITICO"
            impacto_score = 25
        elif exceso > 4:
            riesgo = "ALTO"
            impacto_score = 15
        else:
            riesgo = "MEDIO"
            impacto_score = 5
        return {
            "horas_extra_mes": horas_extra_mes,
            "sobrecosto":      round(sobrecosto, 2),
            "riesgo":          riesgo,
            "impacto_score":   impacto_score
        }

    def calcular_rotacion(self):
        bajas        = self.data.get("bajas", 0)
        salario      = self.data.get("salario_promedio", 0)
        reclutamiento = self.data.get("costo_reclutamiento", 0)
        impacto      = bajas * (salario * 3.5 + reclutamiento)
        return {
            "bajas":            bajas,
            "impacto_mensual":  round(impacto, 2),
            "impacto_anual":    round(impacto * 12, 2),
            "riesgo":           "ALTO" if bajas > 3 else "MEDIO",
            "impacto_score":    20 if impacto > 50000 else 10
        }

    def ejecutar(self):
        near = self.calcular_nearshoring()
        rot  = self.calcular_rotacion()
        score = 100
        score -= near["impacto_score"]
        score -= rot["impacto_score"]
        impacto_total = near["sobrecosto"] + rot["impacto_mensual"]
        return {
            "engine":                "MESAN Omega v4",
            "score":                 max(round(score, 2), 0),
            "impacto_total_mensual": round(impacto_total, 2),
            "nearshoring":           near,
            "rotacion":              rot
        }


# =============================================
# CALCULAR RENTABILIDAD — usado por /enterprise
# =============================================
def calcular_rentabilidad(ingreso: float, elementos: int, zona: str = "frontera") -> dict:
    smg          = SMG_FRONTERA if zona == "frontera" else SMG_INTERIOR
    salario_mes  = smg * 30
    costo_elem   = salario_mes * FACTOR_CARGA
    costo_total  = costo_elem * elementos
    utilidad     = ingreso - costo_total
    margen_real  = round((utilidad / ingreso * 100), 2) if ingreso else 0

    if margen_real < 15:
        clasificacion = "RIESGO"
        recomendacion = "Precio por debajo del umbral — renegociar contrato"
    elif margen_real < 25:
        clasificacion = "AJUSTADO"
        recomendacion = "Margen aceptable — monitorear costos"
    else:
        clasificacion = "SALUDABLE"
        recomendacion = "Operacion rentable"

    return {
        "ingreso":          ingreso,
        "costo_total":      round(costo_total, 2),
        "utilidad":         round(utilidad, 2),
        "margen_real":      margen_real,
        "clasificacion":    clasificacion,
        "recomendacion":    recomendacion,
        "precio_minimo":    round(costo_total / 0.95, 2),
        "precio_cierre":    round(costo_total / 0.875, 2),
        "precio_objetivo":  round(costo_total / 0.80, 2)
    }


# =============================================
# CALCULAR PROPUESTA — cotización por elementos
# =============================================
def calcular_propuesta(zona: str, elementos: int, dias_semana: int = 6) -> dict:
    from datetime import datetime
    DIAS_MES     = (dias_semana / 7) * 30.4
    smg          = SMG_FRONTERA if zona == "frontera" else SMG_INTERIOR
    iva          = IVA_FRONTERA if zona == "frontera" else IVA_INTERIOR
    nomina       = smg * DIAS_MES * FACTOR_CARGA
    precio_sin_iva = nomina / (1 - MARGEN_MINIMO)
    precio_con_iva = precio_sin_iva * (1 + iva)
    total        = precio_con_iva * elementos

    return {
        "elementos":         elementos,
        "precio_unitario":   round(precio_con_iva, 2),
        "total_mensual":     round(total, 2),
        "costo_operativo":   round(nomina * elementos, 2),
        "utilidad_estimada": round(total - nomina * elementos, 2),
        "zona":              zona,
        "dias_semana":       dias_semana
    }


# =============================================
# RUNWAY — meses de caja disponibles
# =============================================
def calcular_runway(caja: float, gasto_mensual: float) -> dict:
    if gasto_mensual <= 0:
        return {"runway_meses": 0, "estado": "SIN DATOS"}
    runway = caja / gasto_mensual
    if runway < 2:
        estado = "CRITICO"
    elif runway < 4:
        estado = "ALERTA"
    elif runway < 6:
        estado = "PRECAUCION"
    else:
        estado = "ESTABLE"
    return {
        "caja":           caja,
        "gasto_mensual":  gasto_mensual,
        "runway_meses":   round(runway, 1),
        "estado":         estado
    }
