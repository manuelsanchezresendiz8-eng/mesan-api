# MESAN Ω — Motor Financiero Nacional v4

from core.control_decision import evaluar_decision
from core.precio_inteligente import calcular_precio_cierre

SALARIO_MIN_FRONTERA = 13409.80
SALARIO_MIN_GENERAL = 7467.00


def salario_por_zona(zona: str) -> float:
    return SALARIO_MIN_FRONTERA if zona == "frontera" else SALARIO_MIN_GENERAL


def calcular_costo_empleado(salario: float) -> float:
    return round(salario * 1.63, 2)


def calcular_reserva(utilidad: float, porcentaje: float = 0.10) -> float:
    return round(utilidad * porcentaje, 2) if utilidad > 0 else 0


def evaluar_servicio(precio_cliente: float, empleados: int, salario=None, zona="general"):

    salario_base = salario if salario else salario_por_zona(zona)

    costo_unitario = calcular_costo_empleado(salario_base)
    costo_total = round(costo_unitario * empleados, 2)

    utilidad = round(precio_cliente - costo_total, 2)
    margen = round((utilidad / precio_cliente) * 100, 2) if precio_cliente else 0

    reserva = calcular_reserva(utilidad)
    precios = calcular_precio_cierre(costo_total)

    if utilidad < 0:
        clasificacion = "CRITICO"
        mensaje = "Operación en pérdida"
    elif margen < 10:
        clasificacion = "ALTO"
        mensaje = "Margen insuficiente"
    elif margen < 20:
        clasificacion = "MEDIO"
        mensaje = "Margen vulnerable"
    else:
        clasificacion = "BAJO"
        mensaje = "Operación rentable"

    decision = evaluar_decision({
        "utilidad": utilidad,
        "margen": margen,
        "precio_minimo": precios["precio_minimo"]
    })

    return {
        "clasificacion": clasificacion,
        "mensaje": mensaje,
        "decision": decision,
        "precios": precios,
        "financiero": {
            "ingreso": precio_cliente,
            "costo_total": costo_total,
            "utilidad": utilidad,
            "margen": margen,
            "reserva": reserva,
            "salario": salario_base,
            "zona": zona
        }
    }
