# core/preguntas.py

def generar_preguntas(industria, texto, riesgo):
    t = texto.lower()

    # LABORAL - huelga/sindicato
    if any(p in t for p in ["sindicato", "huelga", "paro", "demanda laboral", "jlca", "emplazamiento"]):
        return [
            {"pregunta": "El sindicato ya inicio paro o huelga?", "name": "huelga", "opciones": ["Si", "No", "En negociacion"]},
            {"pregunta": "Existe demanda formal ante la JLCA?", "name": "demanda", "opciones": ["Si", "No", "No se"]}
        ]

    # LABORAL - accidente
    if any(p in t for p in ["accidente", "incapacidad", "herido", "lesion", "obra determinada"]):
        return [
            {"pregunta": "El trabajador tiene IMSS activo?", "name": "imss_activo", "opciones": ["Si", "No", "No se"]},
            {"pregunta": "Ya hay demanda laboral presentada?", "name": "demanda", "opciones": ["Si", "No", "En proceso"]}
        ]

    # SEGURIDAD
    if industria == "SEGURIDAD":
        return [
            {"pregunta": "Tienes permiso federal SSPC vigente?", "name": "sspc", "opciones": ["Si", "No", "En tramite"]},
            {"pregunta": "Los guardias tienen CUIP actualizado?", "name": "cuip", "opciones": ["Si", "No", "Parcial"]}
        ]

    # SERVICIOS_APOYO
    if industria == "SERVICIOS_APOYO":
        return [
            {"pregunta": "Tu REPSE esta vigente?", "name": "repse", "opciones": ["Si", "No", "Vencido"]},
            {"pregunta": "Todos los trabajadores estan dados de alta en IMSS?", "name": "imss", "opciones": ["Si", "No", "Parcial"]}
        ]

    # SALUD
    if industria == "SALUD":
        return [
            {"pregunta": "Ya te levantaron acta de inspeccion?", "name": "acta", "opciones": ["Acta levantada", "Solo visita", "No estoy seguro"]},
            {"pregunta": "Cuentas con aviso de funcionamiento vigente?", "name": "aviso", "opciones": ["Si", "No", "No se"]},
            {"pregunta": "Tienes expediente sanitario documentado?", "name": "expediente", "opciones": ["Si completo", "Parcial", "No"]}
        ]

    # MANUFACTURA
    if industria == "MANUFACTURA":
        return [
            {"pregunta": "Cuanto tiempo lleva detenida la produccion?", "name": "dias_paro", "opciones": ["Menos de 24hrs", "1-3 dias", "Mas de 3 dias"]},
            {"pregunta": "Tienes proveedor alterno de refacciones?", "name": "proveedor", "opciones": ["Si", "No", "En proceso"]}
        ]

    # FISCAL - SAT/IMSS
    if any(p in t for p in ["sat", "imss", "auditoria", "embargo"]):
        return [
            {"pregunta": "Recibiste notificacion formal del SAT o IMSS?", "name": "acta", "opciones": ["Si", "No", "No se"]},
            {"pregunta": "Cuantos empleados tiene la empresa?", "name": "empleados", "opciones": ["1-5", "6-20", "Mas de 20"]}
        ]

    # DEFAULT
    return [
        {"pregunta": "Has recibido alguna notificacion del SAT o IMSS?", "name": "acta", "opciones": ["Si", "No", "No se"]},
        {"pregunta": "Cuantos empleados tiene la empresa?", "name": "empleados", "opciones": ["1-5", "6-20", "Mas de 20"]}
    ]
