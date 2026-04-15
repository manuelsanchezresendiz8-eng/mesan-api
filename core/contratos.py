from datetime import date

def evaluar_tacita_reconduccion(fecha_vencimiento, prestacion_continua, oposicion_formal, monto_original):
    """
    Dictamen de MESAN Ω sobre la vigencia automática de términos.
    Basado en el principio de Tácita Reconducción (Código Civil).
    """
    hoy = date.today()

    if hoy > fecha_vencimiento and prestacion_continua and not oposicion_formal:
        return {
            "estatus": "ACTIVO_POR_RECONDUCCION",
            "monto_aplicable": monto_original,
            "alerta": "El contrato venció pero los términos anteriores siguen vigentes por ley.",
            "accion_requerida": "Continuar facturando monto original hasta aviso formal de 30 días."
        }

    return {"estatus": "REVISIÓN_REQUERIDA", "monto_aplicable": None}
