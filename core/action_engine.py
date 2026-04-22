# core/action_engine.py

def generar_plan_accion(data: dict, riesgo: int, imse: int) -> list:
    acciones = []

    salario_real = data.get("salario_real", 0)
    salario_declarado = data.get("salario_declarado", 0)
    empleados_reales = data.get("empleados_reales", 0)
    empleados_imss = data.get("empleados_imss", 0)
    diferencias_cfdi = data.get("diferencias_cfdi", False)

    if salario_real > 0 and salario_declarado < salario_real:
        acciones.append({
            "problema": "Subregistro salarial detectado",
            "impacto": "Riesgo de multa y recalculo de cuotas IMSS",
            "accion": "Ajustar SBC al salario real",
            "prioridad": "ALTA",
            "tiempo": "Inmediato"
        })

    if empleados_reales > empleados_imss:
        acciones.append({
            "problema": "Empleados no registrados en IMSS",
            "impacto": "Multa y riesgo penal laboral",
            "accion": "Regularizar plantilla faltante",
            "prioridad": "ALTA",
            "tiempo": "1-7 dias"
        })

    if diferencias_cfdi:
        acciones.append({
            "problema": "Diferencias entre CFDI y nomina",
            "impacto": "Inconsistencia fiscal detectable por SAT",
            "accion": "Conciliar CFDI con dispersion real",
            "prioridad": "MEDIA",
            "tiempo": "7-15 dias"
        })

    if imse < 60:
        acciones.append({
            "problema": "Baja madurez de seguridad empresarial",
            "impacto": "Alta exposicion a inspecciones",
            "accion": "Revision integral de cumplimiento REPSE",
            "prioridad": "MEDIA",
            "tiempo": "15-30 dias"
        })

    if riesgo > 80:
        acciones.append({
            "problema": "Riesgo critico detectado",
            "impacto": "Alta probabilidad de auditoria IMSS/SAT",
            "accion": "Auditoria inmediata y estrategia de regularizacion",
            "prioridad": "URGENTE",
            "tiempo": "Inmediato"
        })

    return acciones


def generar_recomendacion(nivel: str) -> dict:
    if nivel in ["ALTO", "CRITICO"]:
        return {
            "accion": "Regularizacion inmediata IMSS + auditoria fiscal",
            "ticket": 25000,
            "urgencia": "INMEDIATA"
        }
    elif nivel == "MEDIO":
        return {
            "accion": "Optimizacion fiscal y laboral",
            "ticket": 12000,
            "urgencia": "30 DIAS"
        }
    return {
        "accion": "Monitoreo preventivo",
        "ticket": 3000,
        "urgencia": "60 DIAS"
    }

# v2 — actualizado
   
            
