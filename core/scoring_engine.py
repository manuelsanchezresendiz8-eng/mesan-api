# core/scoring_engine.py — MESAN Ω
# Motor de Scoring Dinámico v2.0
# Arquitectura enterprise determinística
# Riesgo explicable + mitigadores + confianza real

from typing import Dict, List


def calcular_score(data: dict) -> dict:

    # ─────────────────────────────────────────────
    # CONFIGURACIÓN BASE
    # ─────────────────────────────────────────────

    score = 0
    confianza = 50

    factores: List[Dict] = []
    mitigadores: List[str] = []

    riesgo_principal = "OPERATIVO"

    datos_faltantes = 0

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    def agregar_factor(tipo, nivel, puntos, detalle):
        nonlocal score

        score += puntos

        factores.append({
            "tipo": tipo,
            "nivel": nivel,
            "impacto": puntos,
            "detalle": detalle
        })

    def faltante(valor):
        return valor is None or valor == "" or valor == 0

    # ─────────────────────────────────────────────
    # VARIABLES LABORALES
    # ─────────────────────────────────────────────

    empleados = data.get("empleados", data.get("num_empleados"))

    if faltante(empleados):
        datos_faltantes += 1
        empleados = 0

    empleados = int(empleados)

    if empleados > 20:
        agregar_factor(
            "LABORAL",
            "ALTO",
            18,
            "Alto volumen de personal expuesto"
        )
        confianza += 5

    elif empleados > 5:
        agregar_factor(
            "LABORAL",
            "MEDIO",
            10,
            "Plantilla laboral con posible exposición IMSS"
        )
        confianza += 3

    imss = data.get("imss", data.get("registro_imss"))

    if faltante(imss):
        datos_faltantes += 1
        imss = "desconocido"

    if imss == "ninguno":
        agregar_factor(
            "LABORAL",
            "CRITICO",
            22,
            "Ausencia de registro IMSS"
        )
        confianza += 6
        riesgo_principal = "LABORAL"

    elif imss == "parcial":
        agregar_factor(
            "LABORAL",
            "ALTO",
            14,
            "Registro IMSS parcial o inconsistente"
        )

    contratos = data.get(
        "contratos",
        data.get("contratos_laborales")
    )

    if faltante(contratos):
        datos_faltantes += 1
        contratos = "desconocido"

    if contratos == "ninguno":
        agregar_factor(
            "LABORAL",
            "ALTO",
            15,
            "Ausencia de contratos laborales"
        )

    elif contratos == "algunos":
        agregar_factor(
            "LABORAL",
            "MEDIO",
            8,
            "Formalización contractual incompleta"
        )

    # ─────────────────────────────────────────────
    # VARIABLES FISCALES
    # ─────────────────────────────────────────────

    factura = data.get(
        "factura",
        data.get("situacion_fiscal")
    )

    if faltante(factura):
        datos_faltantes += 1
        factura = "desconocido"

    if factura in ["irregular", "sin_facturar"]:
        agregar_factor(
            "FISCAL",
            "ALTO",
            18,
            "Posibles inconsistencias fiscales"
        )

        riesgo_principal = "FISCAL"

    sat_notificacion = data.get(
        "sat_notificacion",
        data.get("inspeccion_sat", False)
    )

    if sat_notificacion:
        agregar_factor(
            "FISCAL",
            "CRITICO",
            20,
            "Requerimiento SAT o inspección activa"
        )

        confianza += 8
        riesgo_principal = "FISCAL"

    historial = data.get(
        "historial",
        data.get("historial_multas")
    )

    if historial == "si":
        agregar_factor(
            "FISCAL",
            "MEDIO",
            10,
            "Historial previo de multas o sanciones"
        )

    # ─────────────────────────────────────────────
    # REPSE
    # ─────────────────────────────────────────────

    repse = data.get(
        "repse",
        data.get("repse_vencido")
    )

    if repse in ["vencido", "sin_registro", True]:
        agregar_factor(
            "REGULATORIO",
            "CRITICO",
            18,
            "REPSE vencido o inexistente"
        )

        confianza += 5
        riesgo_principal = "REGULATORIO"

    # ─────────────────────────────────────────────
    # VARIABLES FINANCIERAS
    # ─────────────────────────────────────────────

    ingresos = float(
        data.get(
            "ingresos",
            data.get("precio_servicio", 0)
        )
    )

    egresos = float(
        data.get(
            "egresos",
            data.get("gastos_fijos", 0)
        )
    )

    if ingresos > 0 and egresos > ingresos:

        deficit_pct = ((egresos - ingresos) / ingresos) * 100

        if deficit_pct > 30:
            agregar_factor(
                "FINANCIERO",
                "CRITICO",
                20,
                "Déficit financiero crítico"
            )

            riesgo_principal = "FINANCIERO"

        else:
            agregar_factor(
                "FINANCIERO",
                "MEDIO",
                10,
                "Flujo operativo negativo"
            )

    # ─────────────────────────────────────────────
    # MITIGADORES
    # ─────────────────────────────────────────────

    if data.get("auditoria_externa"):
        score -= 8
        mitigadores.append(
            "Auditoría externa activa"
        )

    if data.get("compliance"):
        score -= 6
        mitigadores.append(
            "Programa de compliance detectado"
        )

    if data.get("certificaciones"):
        score -= 5
        mitigadores.append(
            "Certificaciones corporativas activas"
        )

    # ─────────────────────────────────────────────
    # SECTOR MULTIPLICADOR
    # ─────────────────────────────────────────────

    industria = data.get(
        "industria",
        data.get("giro", "GENERAL")
    )

    multiplicadores = {
        "SEGURIDAD": 1.20,
        "SALUD": 1.15,
        "MANUFACTURA": 1.10,
        "SERVICIOS_APOYO": 1.12,
        "LABORAL": 1.10,
        "FINANCIERO": 1.08,
        "GENERAL": 1.0
    }

    mult = multiplicadores.get(
        industria.upper(),
        1.0
    )

    score = score * mult

    # ─────────────────────────────────────────────
    # AJUSTES DE CONFIANZA
    # ─────────────────────────────────────────────

    confianza -= (datos_faltantes * 5)

    confianza = max(35, min(92, confianza))

    # ─────────────────────────────────────────────
    # NORMALIZACIÓN SCORE
    # ─────────────────────────────────────────────

    score = int(max(0, min(100, score)))

    # ─────────────────────────────────────────────
    # CLASIFICACIÓN FINAL
    # ─────────────────────────────────────────────

    if score >= 75:
        nivel = "CRITICO"
        emoji = "🔴"

    elif score >= 55:
        nivel = "ALTO"
        emoji = "🟠"

    elif score >= 35:
        nivel = "MEDIO"
        emoji = "🟡"

    else:
        nivel = "BAJO"
        emoji = "🟢"

    # ─────────────────────────────────────────────
    # TENDENCIA
    # ─────────────────────────────────────────────

    if score >= 70:
        tendencia = "ASCENDENTE"

    elif score >= 40:
        tendencia = "ESTABLE"

    else:
        tendencia = "CONTROLADA"

    # ─────────────────────────────────────────────
    # VALIDACIÓN MÍNIMA
    # ─────────────────────────────────────────────

    if datos_faltantes >= 4:
        return {
            "status": "insuficiente",
            "mensaje": "Información insuficiente para generar un diagnóstico confiable.",
            "confianza": confianza
        }

    # ─────────────────────────────────────────────
    # RESPUESTA FINAL
    # ─────────────────────────────────────────────

    return {

        "status": "ok",

        "score": score,

        "nivel": nivel,

        "emoji": emoji,

        "confianza": confianza,

        "tendencia": tendencia,

        "riesgo_principal": riesgo_principal,

        "industria": industria,

        "factores": factores,

        "mitigadores": mitigadores,

        "origen": [
            "Variables declaradas",
            "Simulación operativa",
            "Patrones regulatorios",
            "Scoring determinístico MESAN Ω"
        ]
    }
