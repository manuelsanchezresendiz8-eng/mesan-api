# services/policy_audit_engine.py -- MESAN Omega Policy Audit Engine v2.0 CLEAN
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger("mesan.policy")


class PolicyAuditEngine:
    """
    Motor de auditoría de políticas laborales y cumplimiento legal MESAN Ω.
    Versión: 2.0 CLEAN
    """

    def __init__(self):
        self.version = "2.0"
        self.engine = "MESAN_POLICY_AUDIT"

    def auditar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()

        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id = data.get("trace_id", "NO_TRACE")

        empleados = int(data.get("empleados", 0))

        score = 100
        riesgos: List[dict] = []
        recomendaciones: List[str] = []
        exposicion = 0

        # =========================
        # CATEGORIZACIÓN EMPRESA
        # =========================
        if empleados <= 10:
            categoria = "MICRO"
        elif empleados <= 50:
            categoria = "PYME"
        elif empleados <= 250:
            categoria = "MEDIANA"
        else:
            categoria = "CORPORATIVO"

        # =========================
        # REGLAS DE CUMPLIMIENTO
        # =========================

        if not data.get("nom_035", False):
            impacto = 20 if empleados > 50 else 10
            score -= impacto
            exposicion += 50000
            riesgos.append({
                "riesgo": "NOM-035",
                "severidad": "ALTA",
                "impacto": "MULTAS_STPS"
            })
            recomendaciones.append(
                "Implementar política de prevención de riesgos psicosociales NOM-035"
            )

        if not data.get("reglamento_interno", False):
            score -= 15
            exposicion += 25000
            riesgos.append({
                "riesgo": "REGLAMENTO_INTERNO",
                "severidad": "MEDIA",
                "impacto": "RIESGO_LABORAL"
            })
            recomendaciones.append(
                "Actualizar reglamento interno de trabajo"
            )

        if data.get("empleados_remotos", 0) > 0 and not data.get("politica_teletrabajo", False):
            score -= 15
            exposicion += 30000
            riesgos.append({
                "riesgo": "TELETRABAJO",
                "severidad": "MEDIA",
                "impacto": "CONTINGENCIA_LABORAL"
            })
            recomendaciones.append(
                "Implementar política de teletrabajo conforme a LFT"
            )

        if not data.get("clausula_confidencialidad", False):
            score -= 10
            exposicion += 15000
            riesgos.append({
                "riesgo": "CONFIDENCIALIDAD",
                "severidad": "MEDIA",
                "impacto": "RIESGO_LEGAL"
            })
            recomendaciones.append(
                "Agregar cláusulas de confidencialidad a contratos"
            )

        if not data.get("cumplimiento_stps", False):
            score -= 20
            exposicion += 100000
            riesgos.append({
                "riesgo": "STPS",
                "severidad": "CRITICA",
                "impacto": "MULTAS_Y_SUSPENSIONES"
            })
            recomendaciones.append(
                "Regularizar cumplimiento ante STPS"
            )

        if not data.get("plan_capacitacion", False):
            score -= 10
            exposicion += 20000
            riesgos.append({
                "riesgo": "CAPACITACION",
                "severidad": "MEDIA",
                "impacto": "OBSERVACIONES_STPS"
            })
            recomendaciones.append(
                "Registrar plan de capacitación ante STPS"
            )

        # =========================
        # NORMALIZACIÓN SCORE
        # =========================
        score = max(score, 0)

        if score >= 80:
            nivel = "VERDE"
            prioridad = "BAJA"
        elif score >= 60:
            nivel = "AMARILLO"
            prioridad = "MEDIA"
        elif score >= 40:
            nivel = "NARANJA"
            prioridad = "ALTA"
        else:
            nivel = "ROJO"
            prioridad = "CRITICA"

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # =========================
        # RESPONSE FINAL
        # =========================
        return {
            "engine": self.engine,
            "engine_status": "OK",
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "trace_id": trace_id,
            "categoria_empresa": categoria,
            "policy_score": score,
            "nivel": nivel,
            "prioridad": prioridad,
            "riesgos_detectados": len(riesgos),
            "exposicion_estimada_mxn": exposicion,
            "riesgos": riesgos,
            "recomendaciones": recomendaciones,
            "engine_latency_ms": latency_ms
        }
