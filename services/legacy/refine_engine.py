# services/refine_engine.py — MESAN Ω
# Motor de Refinamiento Conversacional

from datetime import datetime

def generar_refinamiento(data: dict) -> dict:
    industria = data.get("industria", "GENERAL")
    riesgo    = data.get("riesgo", "MEDIO")
    impacto   = int(data.get("impacto", 0))
    impacto_min = int(data.get("impacto_min", impacto))
    impacto_max = int(data.get("impacto_max", impacto * 2))

    preguntas  = []
    escenarios = []
    acciones   = []
    prioridad  = "MEDIA"

    if industria == "FINANCIERO":
        preguntas = [
            {"id": "cobranza", "tipo": "radio", "pregunta": "Cuantos dias promedio tienen vencidas tus cuentas por cobrar?", "opciones": ["0-30 dias", "30-60 dias", "60-90 dias", "Mas de 90 dias"]},
            {"id": "nomina",   "tipo": "radio", "pregunta": "La nomina ya presenta retrasos?", "opciones": ["No", "Retrasos menores", "Si, ya hay adeudos"]},
            {"id": "credito",  "tipo": "radio", "pregunta": "El banco ya notifico posible revision o cancelacion de lineas?", "opciones": ["No", "Revision preventiva", "Si"]}
        ]
        escenarios = [
            {"titulo": "Escenario Estable",    "descripcion": "Recuperacion parcial de cobranza y estabilizacion operativa.", "impacto_estimado": f"${impacto_min:,} - ${int(impacto_min*1.5):,} MXN"},
            {"titulo": "Escenario Presionado", "descripcion": "Atrasos progresivos en flujo y obligaciones prioritarias.",    "impacto_estimado": f"${int(impacto_min*1.5):,} - ${impacto_max:,} MXN"},
            {"titulo": "Escenario Critico",    "descripcion": "Incumplimiento bancario + contingencia laboral/fiscal.",        "impacto_estimado": f"${impacto_max:,} - ${int(impacto_max*2.5):,} MXN"}
        ]
        acciones  = ["Priorizar flujo para nomina y SAT", "Negociar prorroga bancaria inmediata", "Reducir gastos no esenciales 20% en 14 dias", "Activar cobranza intensiva en cuentas principales"]
        prioridad = "CRITICA" if riesgo == "CRITICO" else "ALTA"

    elif industria == "SEGURIDAD":
        preguntas = [
            {"id": "sspc",      "tipo": "radio", "pregunta": "El permiso SSPC sigue vigente?",                          "opciones": ["Si", "Por vencer", "Vencido"]},
            {"id": "imss",      "tipo": "radio", "pregunta": "Todos los elementos tienen IMSS activo?",                 "opciones": ["Si", "Parcial", "No"]},
            {"id": "seguro_rc", "tipo": "radio", "pregunta": "La empresa tiene seguro de responsabilidad civil vigente?", "opciones": ["Si", "No"]}
        ]
        escenarios = [
            {"titulo": "Escenario Operativo",    "descripcion": "Regularizacion SSPC e IMSS sin afectacion contractual.", "impacto_estimado": "$300,000 - $700,000 MXN"},
            {"titulo": "Escenario Contractual",  "descripcion": "Rescision parcial de clientes y multas regulatorias.",   "impacto_estimado": "$1,000,000 - $2,500,000 MXN"},
            {"titulo": "Escenario Critico",      "descripcion": "Suspension operativa + litigio civil + sanciones SAT.",  "impacto_estimado": "$3,000,000 - $10,000,000 MXN"}
        ]
        acciones  = ["Iniciar renovacion SSPC inmediata", "Regularizar IMSS prioritario", "Contratar seguro RC urgente", "Blindar contratos corporativos"]
        prioridad = "CRITICA"

    elif industria == "LABORAL":
        preguntas = [
            {"id": "huelga",   "tipo": "radio", "pregunta": "Existe emplazamiento formal a huelga?",     "opciones": ["No", "En negociacion", "Si"]},
            {"id": "sindicato","tipo": "radio", "pregunta": "El sindicato ya notifico fecha limite?",     "opciones": ["No", "Si"]}
        ]
        escenarios = [
            {"titulo": "Escenario Negociado", "descripcion": "Acuerdo preventivo sin paro operativo.",           "impacto_estimado": "$500,000 - $1,500,000 MXN"},
            {"titulo": "Escenario de Paro",   "descripcion": "Suspension parcial de operaciones.",               "impacto_estimado": "$2,000,000 - $6,000,000 MXN"},
            {"titulo": "Escenario Critico",   "descripcion": "Huelga prolongada + penalizaciones contractuales.", "impacto_estimado": "$8,000,000 - $20,000,000 MXN"}
        ]
        acciones  = ["Activar mesa de negociacion inmediata", "Revisar contratos colectivos", "Preparar contingencia operativa", "Blindar clientes estrategicos"]
        prioridad = "CRITICA"

    elif industria == "MANUFACTURA":
        preguntas = [
            {"id": "produccion", "tipo": "radio", "pregunta": "La produccion ya fue afectada?", "opciones": ["No", "Parcialmente", "Parada total"]},
            {"id": "cliente",    "tipo": "radio", "pregunta": "El cliente principal ya notifico penalizacion?", "opciones": ["No", "Advertencia", "Si"]}
        ]
        escenarios = [
            {"titulo": "Escenario Contenido",  "descripcion": "Negociacion sindical rapida sin paro.",          "impacto_estimado": "$800,000 - $2,000,000 MXN"},
            {"titulo": "Escenario Extendido",  "descripcion": "Paro parcial + penalizacion contractual.",        "impacto_estimado": "$3,000,000 - $8,000,000 MXN"},
            {"titulo": "Escenario Catastrofico","descripcion": "Paro total + perdida de cliente estrategico.",   "impacto_estimado": "$10,000,000 - $25,000,000 MXN"}
        ]
        acciones  = ["Activar protocolo de contingencia con cliente", "Negociar acuerdo sindical en 48 horas", "Documentar posicion legal inmediatamente", "Preparar plan de produccion alternativo"]
        prioridad = "CRITICA"

    else:
        preguntas = [
            {"id": "operacion", "tipo": "radio", "pregunta": "La operacion ya presenta afectaciones visibles?", "opciones": ["No", "Parcial", "Critica"]}
        ]
        escenarios = [
            {"titulo": "Escenario Preventivo", "descripcion": "Correccion temprana y estabilizacion.", "impacto_estimado": "$50,000 - $300,000 MXN"}
        ]
        acciones  = ["Auditoria preventiva inmediata", "Regularizacion documental prioritaria", "Monitoreo operativo continuo"]
        prioridad = "MEDIA"

    return {
        "preguntas_refinamiento":  preguntas,
        "escenarios":              escenarios,
        "acciones_prioritarias":   acciones,
        "prioridad_operativa":     prioridad,
        "cta": {
            "titulo":    "Refinar Diagnostico",
            "subtitulo": "Podemos proyectar escenarios reales de riesgo y estabilizacion.",
            "boton":     "CONTINUAR ANALISIS ESTRATEGICO"
        },
        "fecha": datetime.now().strftime("%d/%m/%Y")
    }
