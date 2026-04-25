def generar_preguntas(industria: str, texto: str, riesgo: str):

    preguntas = []

    if industria == "SALUD":
        preguntas.append({
            "id": "acta",
            "pregunta": "¿Ya te levantaron acta de inspección o solo fue visita?",
            "tipo": "opcion",
            "opciones": ["Acta levantada", "Solo visita", "No estoy seguro"]
        })
        preguntas.append({
            "id": "aviso",
            "pregunta": "¿Cuentas con aviso de funcionamiento vigente?",
            "tipo": "opcion",
            "opciones": ["Sí", "No", "No sé"]
        })
        preguntas.append({
            "id": "expediente",
            "pregunta": "¿Tienes expediente sanitario documentado y actualizado?",
            "tipo": "opcion",
            "opciones": ["Sí completo", "Parcial", "No"]
        })

    elif industria == "RETAIL":
        preguntas.append({
            "id": "contratos",
            "pregunta": "¿Todos tus empleados tienen contrato firmado?",
            "tipo": "opcion",
            "opciones": ["Sí", "Algunos", "No"]
        })
        preguntas.append({
            "id": "rotacion",
            "pregunta": "¿Tienes alta rotación de personal?",
            "tipo": "opcion",
            "opciones": ["Alta", "Media", "Baja"]
        })

    elif industria == "CONSTRUCCION":
        preguntas.append({
            "id": "imss_obra",
            "pregunta": "¿Tus trabajadores de obra están registrados en IMSS?",
            "tipo": "opcion",
            "opciones": ["Todos", "Algunos", "Ninguno"]
        })
        preguntas.append({
            "id": "repse",
            "pregunta": "¿Tienes REPSE vigente?",
            "tipo": "opcion",
            "opciones": ["Sí vigente", "Vencido", "No tengo"]
        })

    elif industria == "ALIMENTOS":
        preguntas.append({
            "id": "licencia",
            "pregunta": "¿Tienes licencia sanitaria y manejo de alimentos vigente?",
            "tipo": "opcion",
            "opciones": ["Sí", "Vencida", "No"]
        })
        preguntas.append({
            "id": "inspeccion",
            "pregunta": "¿Han tenido inspección sanitaria este año?",
            "tipo": "opcion",
            "opciones": ["Sí sin problemas", "Sí con observaciones", "No"]
        })

    elif industria == "MANUFACTURA":
        preguntas.append({
            "id": "tiempo_paro",
            "pregunta": "¿Cuánto tiempo lleva detenida la producción?",
            "tipo": "opcion",
            "opciones": ["Menos de 24hrs", "1-3 días", "Más de 3 días"]
        })
        preguntas.append({
            "id": "proveedor",
            "pregunta": "¿Tienes proveedor alterno de refacciones?",
            "tipo": "opcion",
            "opciones": ["Sí", "No", "En proceso"]
        })

    else:
        preguntas.append({
            "id": "auditoria",
            "pregunta": "¿Has recibido alguna notificación del SAT o IMSS?",
            "tipo": "opcion",
            "opciones": ["Sí", "No", "No sé"]
        })
        preguntas.append({
            "id": "empleados",
            "pregunta": "¿Cuántos empleados tiene la empresa?",
            "tipo": "opcion",
            "opciones": ["1-5", "6-20", "Más de 20"]
        })

    return preguntas
