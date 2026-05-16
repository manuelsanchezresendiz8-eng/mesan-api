# services/executive_report_generator.py
# MESAN Ω — Executive Risk Report Generator v3.0

from datetime import datetime


def generar_reporte(score_data: dict, data: dict) -> str:

    score = score_data.get("score", 0)
    nivel = score_data.get("nivel", "BAJO")
    emoji = score_data.get("emoji", "🟢")
    confianza = score_data.get("confianza", 70)
    tendencia = score_data.get("tendencia", "ESTABLE")
    industria = score_data.get("industria", "GENERAL")
    factores = score_data.get("factores", [])

    ingresos = float(data.get("ingresos", 0))
    egresos = float(data.get("egresos", 0))

    # ─────────────────────────────────────────────
    # PRIORIDAD
    # ─────────────────────────────────────────────

    if score >= 75:
        prioridad = "🔴 Acción inmediata requerida"
    elif score >= 55:
        prioridad = "🟠 Acción recomendada <30 días"
    elif score >= 35:
        prioridad = "🟡 Seguimiento preventivo"
    else:
        prioridad = "🟢 Riesgo controlado"

    # ─────────────────────────────────────────────
    # TENDENCIA VISUAL
    # ─────────────────────────────────────────────

    tendencia_visual = {
        "ASCENDENTE": "📈 ASCENDENTE",
        "ESTABLE": "➡️ ESTABLE",
        "CONTROLADA": "📉 CONTROLADA"
    }

    tendencia_txt = tendencia_visual.get(
        tendencia,
        "➡️ ESTABLE"
    )

    # ─────────────────────────────────────────────
    # TOP RISK DRIVERS
    # ─────────────────────────────────────────────

    top_riesgos = []

    for f in factores[:4]:
        top_riesgos.append(f"• {f['detalle']}")

    if not top_riesgos:
        top_riesgos.append(
            "• No se detectaron factores críticos relevantes"
        )

    drivers = "\n".join(top_riesgos)

    # ─────────────────────────────────────────────
    # IMPACTO ECONÓMICO
    # ─────────────────────────────────────────────

    base = max(50000, int(score * 5500))

    escenario_conservador = int(base * 0.65)
    escenario_probable = int(base)
    escenario_critico = int(base * 1.6)

    # ─────────────────────────────────────────────
    # HALLAZGO PRINCIPAL
    # ─────────────────────────────────────────────

    hallazgo = """
Se detectan posibles señales de presión operativa,
financiera o regulatoria derivadas de las variables
analizadas por el motor MESAN Ω.
"""

    if ingresos > 0 and egresos > ingresos:

        hallazgo = f"""
Se detectan posibles señales de presión financiera
derivadas de un escenario donde los egresos operativos
estimados (${egresos:,.0f}) superan los ingresos
declarados (${ingresos:,.0f}) de forma sostenida.

Bajo ciertos escenarios, esta situación podría generar
afectaciones progresivas sobre liquidez, capacidad
operativa y estabilidad administrativa.
"""

    # ─────────────────────────────────────────────
    # POSIBLE IMPACTO
    # ─────────────────────────────────────────────

    impacto = """
De mantenerse la tendencia actual podrían presentarse:
- presión operativa progresiva,
- observaciones administrativas,
- incremento de exposición financiera,
- y necesidad de acciones correctivas preventivas.
"""

    if nivel in ["ALTO", "CRITICO"]:

        impacto = """
De mantenerse la tendencia actual podrían presentarse:
- restricciones de flujo operativo,
- presión sobre obligaciones recurrentes,
- incremento de exposición financiera,
- y posibles contingencias administrativas o regulatorias.
"""

    # ─────────────────────────────────────────────
    # REPORTE FINAL
    # ─────────────────────────────────────────────

    reporte = f"""
# MESAN Ω Intelligence Engine

## RESUMEN EJECUTIVO

### MESAN Ω Risk Score
{score}/100

### Nivel de Riesgo
{emoji} {nivel}

### Tendencia
{tendencia_txt}

### Confianza del análisis
{confianza}%

### Prioridad de atención
{prioridad}

### Sector Analizado
{industria}

---

# TOP RISK DRIVERS

{drivers}

---

# IMPACTO ECONÓMICO ESTIMADO

## Escenario conservador
${escenario_conservador:,.0f} MXN

## Escenario probable
${escenario_probable:,.0f} MXN

## Escenario crítico
${escenario_critico:,.0f} MXN

### Simulación basada en:
- flujo operativo declarado,
- presión financiera acumulada,
- escenarios de continuidad operativa,
- y patrones de riesgo empresarial.

---

# ANÁLISIS ESTRATÉGICO EJECUTIVO

## 1. HALLAZGO PRINCIPAL

{hallazgo}

---

## 2. POSIBLE IMPACTO OPERATIVO

{impacto}

---

## 3. ESCENARIO PROYECTADO — 30 DÍAS

### Semana 1
- Auditoría operativa preventiva
- Validación documental estratégica
- Identificación de factores críticos

### Semana 2
- Correcciones prioritarias
- Ajustes operativos
- Regularización preventiva

### Semana 3
- Seguimiento financiero/regulatorio
- Validación de cumplimiento
- Optimización administrativa

### Semana 4
- Monitoreo de riesgo residual
- Implementación de controles
- Estabilización operativa

---

## 4. RECOMENDACIONES PRIORITARIAS

1. Ejecutar revisión operativa preventiva.
2. Priorizar variables críticas detectadas.
3. Reducir exposición financiera/regulatoria.
4. Implementar monitoreo continuo MESAN Ω.
5. Activar seguimiento estratégico JARVIS Ω.

---

## DISCLAIMER EJECUTIVO

Este análisis representa una simulación estratégica
generada por MESAN Ω Intelligence Engine basada en
variables declaradas, scoring determinístico y modelos
predictivos de riesgo empresarial.

No constituye auditoría financiera, dictamen legal,
resolución fiscal ni determinación oficial de autoridad.

Generado:
{datetime.now().strftime("%d/%m/%Y %H:%M")}
"""

    return reporte
