def generar_argumento_reconduccion(id_contrato, monto_anterior):
    """
    Genera el bloque legal para la defensa del precio actual.
    """
    dictamen = f"""
    DICTAMEN DE VIGENCIA CONTRACTUAL - MESAN Ω
    -----------------------------------------
    Estatus: Prórroga por Tácita Reconducción.
    Fundamento: Continuidad operativa sin oposición formal previa al vencimiento.
    Monto Exigible: ${monto_anterior:,.2f}
    Nota: Cualquier ajuste requiere notificación previa de 30 días naturales.
    """
    return dictamen
