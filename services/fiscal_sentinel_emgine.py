# services/fiscal_sentinel_engine.py
# MESAN Omega Fiscal Sentinel Engine v2.0

import logging
import time

from datetime import datetime, timezone

logger = logging.getLogger("mesan.fiscal")


class FiscalSentinelEngine:

    def __init__(self):
        self.version = "2.0"
        self.regulatory_version = "SAT_IMSS_2026_01"

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def to_bool(value):
        return str(value).lower() in ("1", "true", "yes", "on")

    @staticmethod
    def safe_float(value, default=0):
        try:
            return float(value)
        except Exception:
            return default

    @staticmethod
    def safe_int(value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    # =========================================================
    # ENGINE
    # =========================================================

    def analizar(self, data: dict):

        started = time.time()

        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id", "NO_TRACE")

        logger.info(
            f"[FISCAL] analysis started "
            f"tenant={tenant_id} trace_id={trace_id}"
        )

        score = 0
        alertas = []
        recomendaciones = []

        # =====================================================
        # INPUT NORMALIZATION
        # =====================================================

        ingresos  = self.safe_float(data.get("ingresos"))
        gastos    = self.safe_float(data.get("gastos"))
        iva       = self.safe_float(data.get("iva"))
        isr       = self.safe_float(data.get("isr_retenido"))
        deuda     = self.safe_float(data.get("deuda_mensual"))
        cartera   = self.safe_float(data.get("cartera_vencida"))

        empleados = self.safe_int(data.get("trabajadores"))
        sin_imss  = self.safe_int(data.get("trabajadores_sin_imss"))

        repse     = self.to_bool(data.get("repse_suspendido"))
        bloqueo   = self.to_bool(data.get("bloqueo_bancario"))

        flujo = ingresos - gastos - deuda

        # =====================================================
        # LIQUIDEZ
        # =====================================================

        if flujo < 0:
            score += 20

            alertas.append({
                "tipo": "LIQUIDEZ",
                "nivel": "CRITICO",
                "mensaje": "Flujo operativo negativo"
            })

            recomendaciones.append(
                "Ejecutar contención inmediata de gasto"
            )

        # =====================================================
        # PRESION FISCAL
        # =====================================================

        if ingresos > 0 and (iva + isr) > ingresos * 0.25:

            score += 15

            alertas.append({
                "tipo": "SAT",
                "nivel": "ALTO",
                "mensaje": "Presión fiscal elevada"
            })

            recomendaciones.append(
                "Reestructurar estrategia fiscal y flujo tributario"
            )

        # =====================================================
        # IMSS
        # =====================================================

        imss_ratio = (
            (sin_imss / empleados)
            if empleados > 0 else 0
        )

        if imss_ratio > 0.10:

            score += 18

            alertas.append({
                "tipo": "IMSS",
                "nivel": "CRITICO",
                "mensaje": "Plantilla laboral fuera de IMSS"
            })

            recomendaciones.append(
                "Regularizar plantilla laboral inmediatamente"
            )

        # =====================================================
        # REPSE
        # =====================================================

        if repse:

            score += 25

            alertas.append({
                "tipo": "REPSE",
                "nivel": "CRITICO",
                "mensaje": "REPSE suspendido"
            })

            recomendaciones.append(
                "Ejecutar recuperación REPSE urgente"
            )

        # =====================================================
        # BLOQUEO BANCARIO
        # =====================================================

        if bloqueo:

            score += 35

            alertas.append({
                "tipo": "BANCARIO",
                "nivel": "CRITICO",
                "mensaje": "Bloqueo bancario detectado"
            })

            recomendaciones.append(
                "Activar protocolo de supervivencia financiera"
            )

        # =====================================================
        # CARTERA VENCIDA
        # =====================================================

        if ingresos > 0 and cartera > ingresos:

            score += 12

            alertas.append({
                "tipo": "COBRANZA",
                "nivel": "ALTO",
                "mensaje": "Cartera vencida superior a ingresos"
            })

            recomendaciones.append(
                "Ejecutar recuperación agresiva de cobranza"
            )

        # =====================================================
        # DEUDA CRITICA
        # =====================================================

        if ingresos > 0 and deuda > ingresos * 0.45:

            score += 15

            alertas.append({
                "tipo": "DEUDA",
                "nivel": "CRITICO",
                "mensaje": "Presión de deuda mensual crítica"
            })

            recomendaciones.append(
                "Renegociar deuda bancaria y proteger liquidez"
            )

        # =====================================================
        # SCORE CAP
        # =====================================================

        score = min(score, 100)

        # =====================================================
        # NIVEL
        # =====================================================

        if score >= 90:
            nivel = "EXTREMO"

        elif score >= 80:
            nivel = "CRITICO"

        elif score >= 60:
            nivel = "ALTO"

        elif score >= 40:
            nivel = "MEDIO"

        else:
            nivel = "BAJO"

        # =====================================================
        # LATENCY
        # =====================================================

        latency_ms = round((time.time() - started) * 1000, 2)

        logger.info(
            f"[FISCAL] analysis completed "
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

            "engine": "MESAN_FISCAL_SENTINEL",

            "engine_status": "OK",

            "version": self.version,

            "regulatory_version": self.regulatory_version,

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "tenant_id": tenant_id,

            "trace_id": trace_id,

            "engine_latency_ms": latency_ms,

            "resultado": {

                "score": score,

                "nivel": nivel,

                "flujo_operativo": flujo,

                "exposicion_estimada": round(
                    (iva + isr + deuda) * 1.35,
                    2
                ),

                "alertas": alertas,

                "recomendaciones": recomendaciones
            }
        }
