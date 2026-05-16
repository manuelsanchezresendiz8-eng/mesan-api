# core/fallback_engine.py — MESAN Ω
# Motor fallback — cuando Claude no responde
# Tono: riesgo estimado, NO afirmaciones definitivas

def generar_analisis_mesan(data):

    empresa   = data.get("empresa", "EMPRESA")
    empleados = data.get("empleados", 0)
    riesgo    = data.get("riesgo", "MEDIO")
    industria = data.get("industria", "GENERAL")
    impacto   = data.get("impacto", 0)
    causas    = data.get("causas", [])
    requerimiento_sat = data.get("requerimiento_sat", False)

    # Score y severidad
    if riesgo == "CRITICO":
        severidad = "CRITICA"
        score = 85
        emoji = "🔴"
    elif riesgo == "ALTO":
        severidad = "ALTA"
        score = 68
        emoji = "🟠"
    elif riesgo == "MEDIO":
        severidad = "MEDIA"
        score = 48
        emoji = "🟡"
    else:
        severidad = "BAJA"
        score = 22
        emoji = "🟢"

    # Rangos de impacto estimado
    imp_min = int(impacto * 0.6) if impacto else 80000
    imp_probable = impacto if impacto else 180000
    imp_critico = int(impacto * 2.0) if impacto else 350000

    # Hallazgo por industria
    hallazgos = {
        "SERVICIOS_APOYO": "Se detectan posibles inconsistencias en registro REPSE y estructura de subcontratacion que podrian generar exposicion ante IMSS/SAT.",
        "LABORAL": "Se identifican posibles irregularidades en formalizacion contractual y registros de seguridad social que podrian derivar en contingencias laborales.",
        "SEGURIDAD": "Se detectan posibles riesgos en permisos operativos y cobertura de seguridad social para el personal activo.",
        "MANUFACTURA": "Se identifican posibles factores de riesgo en estructura laboral y cumplimiento normativo STPS/IMSS.",
        "SALUD": "Se detectan posibles areas de incumplimiento sanitario y laboral que podrian derivar en revision COFEPRIS/IMSS.",
        "GENERAL": "Se detectan posibles inconsistencias entre estructura operativa, formalización contractual y registros regulatorios."
    }

    hallazgo = hallazgos.get(industria, hallazgos["GENERAL"])

    causas_txt = ""
    if causas:
        causas_txt = "\n".join(f"- {c}" for c in causas[:3])

    sat_txt = ""
    if requerimiento_sat:
        sat_txt = "\nSe identifican posibles factores de atencion prioritaria derivados de requerimientos fiscales recientes que podrian incrementar la probabilidad de revision regulatoria."

    return f"""
## MESAN Ω Intelligence Engine

### RESUMEN EJECUTIVO

**Empresa analizada:** {empresa}
**Severidad estimada:** {emoji} {severidad}
**MESAN Ω Risk Score:** {score}/100
**Confianza del analisis:** 74%

---

## 1. RIESGO DETECTADO

{hallazgo}
{sat_txt}

{causas_txt}

La combinacion de estos factores podria representar exposicion laboral, fiscal y administrativa bajo escenarios de revision regulatoria.

---

## 2. POSIBLE IMPACTO OPERATIVO

En escenarios de validacion regulatoria podrian presentarse:
- Requerimientos documentales y revision cruzada IMSS/SAT
- Auditorias administrativas con afectacion operativa temporal
- Exposicion contractual ante clientes con politicas de compliance

---

## 3. EXPOSICION FINANCIERA ESTIMADA

**Escenario conservador:** ${imp_min:,.0f} - ${int(imp_min * 1.5):,.0f} MXN
**Escenario probable:** ${imp_probable:,.0f} - ${int(imp_probable * 1.8):,.0f} MXN
**Escenario critico:** ${imp_critico:,.0f}+ MXN

*Estimacion basada en patrones regulatorios generales. No constituye determinacion legal o fiscal definitiva.*

---

## 4. VENTANA DE ACCION — 30 DIAS

**Fase inmediata (0-72 horas)**
- Validar situacion contractual y registros IMSS
- Consolidar expediente documental
- Evaluar exposicion fiscal actual

**Fase correctiva (7-15 dias)**
- Iniciar proceso de regularizacion administrativa
- Revisar cumplimiento STPS/IMSS/SAT
- Definir estrategia preventiva con asesor especializado

**Fase estabilizacion (15-30 dias)**
- Implementar controles de cumplimiento
- Monitoreo continuo de obligaciones
- Validacion externa con especialista certificado

---

## 5. PROXIMOS PASOS RECOMENDADOS

1. Realizar auditoria laboral-fiscal interna inmediata
2. Revisar integralmente registros IMSS y situacion SAT
3. Formalizar documentacion pendiente de manera preventiva
4. Consultar con asesor legal y fiscal certificado para validar exposicion real
5. Implementar monitoreo continuo — MESAN Ω puede ayudarte

---

## AVISO IMPORTANTE

*Este analisis es referencial y representa una estimacion de riesgo basada en patrones generales e informacion declarada. Los montos y plazos son aproximados. No constituye dictamen legal, fiscal ni resolucion oficial. Se recomienda validar con asesor legal y fiscal certificado antes de tomar decisiones.*
"""
