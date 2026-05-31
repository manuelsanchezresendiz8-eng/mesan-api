# services/remediation_engine.py -- MESAN Omega Remediation Engine v2.0
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger("mesan.remediation")


class RemediationEngine:

    def __init__(self):
        self.version = "2.0"
        self.engine  = "MESAN_REMEDIATION"

    def generar_plan(self, data: dict) -> dict:
        started   = time.time()
        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  "NO_TRACE")

        nivel      = str(data.get("nivel", "MEDIO")).upper()
        alertas    = data.get("alertas", [])
        try:    score = int(data.get("score", 50))
        except: score = 50
        try:    exposicion = float(data.get("exposicion_estimada_mxn", 0))
        except: exposicion = 0.0

        acciones_inmediatas = []
        acciones_30_dias    = []
        acciones_60_dias    = []
        acciones_90_dias    = []

        if any("SAT" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Solicitar opinion de cumplimiento SAT actualizada")
            acciones_30_dias.append("Regularizar declaraciones fiscales pendientes")
            acciones_60_dias.append("Implementar estrategia fiscal preventiva")

        if any("IMSS" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Regularizar afiliaciones IMSS")
            acciones_30_dias.append("Auditar nomina vs plantilla IMSS")
            acciones_60_dias.append("Implementar controles permanentes IMSS")

        if any("REPSE" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Iniciar renovacion REPSE")
            acciones_30_dias.append("Revisar contratos de subcontratacion")

        if any("LIQUIDEZ" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Contencion inmediata de gasto")
            acciones_30_dias.append("Renegociar pasivos financieros")
            acciones_60_dias.append("Plan de recuperacion de cartera")

        if any("BANCARIO" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Activar protocolo de supervivencia financiera")

        if nivel in ("CRITICO", "EXTREMO"):
            acciones_inmediatas.extend(["Activar War Room Ejecutivo","Congelar gastos no esenciales","Comite diario de riesgos"])
            acciones_30_dias.append("Reestructura financiera de emergencia")
            acciones_60_dias.append("Negociacion con acreedores estrategicos")
            acciones_90_dias.append("Plan de continuidad operativa")
        elif nivel == "ALTO":
            acciones_30_dias.append("Reducir burn rate operativo")
            acciones_60_dias.append("Blindaje fiscal y laboral preventivo")
            acciones_90_dias.append("Optimizacion de capital de trabajo")
        else:
            acciones_60_dias.append("Monitoreo preventivo mensual")
            acciones_90_dias.append("Auditoria interna de cumplimiento")

        acciones_inmediatas = list(dict.fromkeys(acciones_inmediatas))
        acciones_30_dias    = list(dict.fromkeys(acciones_30_dias))
        acciones_60_dias    = list(dict.fromkeys(acciones_60_dias))
        acciones_90_dias    = list(dict.fromkeys(acciones_90_dias))

        costo_estimado   = max(25000, round(exposicion*0.05, 2))
        ahorro_potencial = round(exposicion*0.70, 2)
        roi_estimado     = round(ahorro_potencial/max(costo_estimado,1), 2)

        if nivel in ("CRITICO", "EXTREMO"): urgencia = "INMEDIATA";  probabilidad_exito = 70
        elif nivel == "ALTO":               urgencia = "7_DIAS";     probabilidad_exito = 80
        elif nivel == "MEDIO":              urgencia = "30_DIAS";    probabilidad_exito = 90
        else:                               urgencia = "90_DIAS";    probabilidad_exito = 95

        survival_score_post = min(100, score+25)
        war_room_required   = nivel in ("CRITICO","EXTREMO") or exposicion >= 500000

        if survival_score_post >= 85:   semaforo = "VERDE"
        elif survival_score_post >= 70: semaforo = "AMARILLO"
        elif survival_score_post >= 50: semaforo = "NARANJA"
        else:                           semaforo = "ROJO"

        if exposicion >= 1000000:   sales_priority = "A+"
        elif exposicion >= 500000:  sales_priority = "A"
        elif exposicion >= 250000:  sales_priority = "B"
        else:                       sales_priority = "C"

        executive_summary = (
            f"Se detecto una exposicion estimada de ${exposicion:,.0f} MXN. "
            f"El plan propuesto contempla {len(acciones_inmediatas)} acciones inmediatas "
            f"y una recuperacion potencial de ${ahorro_potencial:,.0f} MXN."
        )

        recovery_ratio = round(ahorro_potencial/max(exposicion, 1), 2)
        latency_ms = round((time.time()-started)*1000, 2)

        logger.info(f"[REMEDIATION] tenant={tenant_id} nivel={nivel} acciones={len(acciones_inmediatas)}")

        return {
            "engine": self.engine, "engine_status": "OK", "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id, "trace_id": trace_id,
            "nivel_riesgo": nivel, "urgencia": urgencia,
            "war_room_required": war_room_required,
            "costo_estimado_mxn": costo_estimado,
            "ahorro_potencial_mxn": ahorro_potencial,
            "roi_estimado": roi_estimado,
            "probabilidad_exito": probabilidad_exito,
            "enterprise_survival_score_post": survival_score_post,
            "semaforo": semaforo,
            "executive_summary": executive_summary,
            "sales_priority": sales_priority,
            "recovery_ratio": recovery_ratio,
            "plan_remediacion": {
                "acciones_inmediatas": acciones_inmediatas,
                "acciones_30_dias":    acciones_30_dias,
                "acciones_60_dias":    acciones_60_dias,
                "acciones_90_dias":    acciones_90_dias
            },
            "total_acciones": len(acciones_inmediatas)+len(acciones_30_dias)+len(acciones_60_dias)+len(acciones_90_dias),
            "engine_latency_ms": latency_ms
        }
