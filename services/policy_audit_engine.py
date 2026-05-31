# services/policy_audit_engine.py -- MESAN Omega Policy Audit Engine v2.0

import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger("mesan.policy")


class PolicyAuditEngine:

    def __init__(self):
        self.version = "2.0"
        self.engine = "MESAN_POLICY_AUDIT"

    def auditar(self, data: dict) -> dict:

        started = time.time()

        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id = data.get("trace_id", "NO_TRACE")

        empleados = int(data.get("empleados", 0))

        score = 100
        riesgos = []
        recomendaciones = []
        exposicion = 0

        # Clasificación empresa
        if empleados <= 10:
            categoria = "MICRO"
        elif empleados <= 50:
            categoria = "PYME"
        elif empleados <= 250:
            categoria = "MEDIANA"
        else:
            categoria = "CORPORATIVO"

        # ==========================
        # NOM-035
        # ==========================

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

        # ==========================
        # Reglamento interno
        # ==========================

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

        # ==========================
        # Teletrabajo
        # ==========================

        if (
            data.get("empleados_remotos", 0) > 0
            and not data.get("politica_teletrabajo", False)
        ):

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

        # ==========================
        # Confidencialidad
        # ==========================

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

        # ==========================
        # STPS
        # ==========================

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

        # ==========================
        # Capacitación
        # ==========================

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

        score = max(score, 0)

        # ==========================
        # Semáforo MESAN Ω
        # ==========================

        if score >= 80:
            nivel = "VERDE"
            prioridad = "BAJA"

        elif score >=
