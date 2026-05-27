# services/compliance_verify_engine.py
# MESAN Omega Compliance Verify Engine v2.0

import logging
import time

from datetime import datetime, timezone

logger = logging.getLogger("mesan.compliance")


class ComplianceVerifyEngine:

    def __init__(self):

        self.version = "2.0"
        self.engine  = "MESAN_COMPLIANCE_VERIFY"
        self.regulatory_version = "SAT_IMSS_REPSE_2026_01"

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def to_bool(value):
        return str(value).lower() in (
            "1", "true", "yes", "on"
        )

    @staticmethod
    def normalize_text(value, default="NO_LOCALIZADA"):

        if value is None:
            return default

        return str(value).strip().upper()

    # =========================================================
    # REPSE
    # =========================================================

    def validar_repse(self, repse_status: bool) -> dict:

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        if repse_status:

            return {
                "status": "VIGENTE",
                "riesgo": "BAJO",
                "accion": "Proveedor habilitado para operación",
                "timestamp": timestamp
            }

        return {
            "status": "SUSPENDIDO",
            "riesgo": "CRITICO",
            "accion": "Bloquear contratación inmediatamente",
            "timestamp": timestamp
        }

    # =========================================================
    # SAT
    # =========================================================

    def validar_sat(self, opinion_sat: str) -> dict:

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        opinion = self.normalize_text(opinion_sat)

        if opinion == "POSITIVA":

            return {
                "status": "POSITIVA",
                "riesgo": "BAJO",
                "accion": "Sin exposición fiscal inmediata",
                "timestamp": timestamp
            }

        if opinion == "NEGATIVA":

            return {
                "status": "NEGATIVA",
                "riesgo": "ALTO",
                "accion": "Suspender pagos y solicitar regularización",
                "timestamp": timestamp
            }

        return {
            "status": "NO_LOCALIZADA",
            "riesgo": "MEDIO",
            "accion": "Solicitar documentación fiscal actualizada",
            "timestamp": timestamp
        }

    # =========================================================
    # IMSS
    # =========================================================

    def validar_imss(self, opinion_imss: str) -> dict:

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        opinion = self.normalize_text(opinion_imss)

        if opinion == "POSITIVA":

            return {
                "status": "POSITIVA",
                "riesgo": "BAJO",
                "accion": "Sin contingencia laboral inmediata",
                "timestamp": timestamp
            }

        if opinion == "NEGATIVA":

            return {
                "status": "NEGATIVA",
                "riesgo": "ALTO",
                "accion": "Riesgo solidario IMSS detectado",
                "timestamp": timestamp
            }

        return {
            "status": "NO_LOCALIZADA",
            "riesgo": "MEDIO",
            "accion": "Validar cumplimiento patronal",
            "timestamp": timestamp
        }

    # =========================================================
    # SCORE
    # =========================================================

    def calcular_score(
        self,
        repse_vigente: bool,
        opinion_sat: str,
        opinion_imss: str,
        tenant_id: str = "DEFAULT",
        trace_id: str = "NO_TRACE"
    ) -> dict:

        started = time.time()

        logger.info(
            f"[COMPLIANCE] analysis started "
            f"tenant={tenant_id} "
            f"trace_id={trace_id}"
        )

        score = 100
        alertas = []
        recomendaciones = []

        # =====================================================
        # NORMALIZATION
        # =====================================================

        repse_vigente = self.to_bool(repse_vigente)

        # =====================================================
        # VALIDATIONS
        # =====================================================

        repse = self.validar_repse(repse_vigente)
        sat   = self.validar_sat(opinion_sat)
        imss  = self.validar_imss(opinion_imss)

        # =====================================================
        # REPSE
        # =====================================================

        if repse["riesgo"] == "CRITICO":

            score -= 40

            alertas.append(
                "REPSE suspendido"
            )

            recomendaciones.append(
                "Bloquear contratación inmediatamente"
            )

        # =====================================================
        # SAT
        # =====================================================

        if sat["riesgo"] == "ALTO":

            score -= 30

            alertas.append(
                "Opinión SAT negativa"
            )

            recomendaciones.append(
                "Suspender pagos y exigir regularización fiscal"
            )

        # =====================================================
        # IMSS
        # =====================================================

        if imss["riesgo"] == "ALTO":

            score -= 30

            alertas.append(
                "Opinión IMSS negativa"
            )

            recomendaciones.append(
                "Bloquear relación operativa hasta regularización"
            )

        # =====================================================
        # SCORE FLOOR
        # =====================================================

        score = max(score, 0)

        # =====================================================
        # LEVELS
        # =====================================================

        if score >= 90:

            nivel = "SEGURO"

        elif score >= 70:

            nivel = "PRECAUCION"

        elif score >= 40:

            nivel = "ALTO_RIESGO"

        else:

            nivel = "CRITICO"

        # =====================================================
        # LATENCY
        # =====================================================

        latency_ms = round(
            (time.time() - started) * 1000,
            2
        )

        logger.info(
            f"[COMPLIANCE] analysis completed "
            f"tenant={tenant_id} "
            f"trace_id={trace_id} "
            f"score={score} "
            f"nivel={nivel} "
            f"latency_ms={latency_ms}"
        )

        # =====================================================
        # RESPONSE
        # =====================================================

        return {

            "engine": self.engine,

            "engine_status": "OK",

            "version": self.version,

            "regulatory_version":
                self.regulatory_version,

            "tenant_id": tenant_id,

            "trace_id": trace_id,

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "engine_latency_ms": latency_ms,

            "score_compliance": score,

            "nivel": nivel,

            "repse": repse,

            "sat": sat,

            "imss": imss,

            "alertas": alertas,

            "recomendaciones": recomendaciones
        }
