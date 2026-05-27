# services/fiscal_sentinel_engine.py
# MESAN Omega Fiscal Sentinel Engine v2.1

import logging
import time

from datetime import datetime, timezone

logger = logging.getLogger("mesan.fiscal")


class FiscalSentinelEngine:

    def __init__(self):

        self.version = "2.1"

        self.engine = "MESAN_FISCAL_SENTINEL"

        self.regulatory_version = "SAT_IMSS_2026_01"

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def to_bool(value):

        return str(value).lower() in (
            "1",
            "true",
            "yes",
            "on"
        )

    @staticmethod
    def safe_float(value, default=0.0):

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

        tenant_id = data.get(
            "tenant_id",
            "DEFAULT"
        )

        trace_id = data.get(
            "trace_id",
            "NO_TRACE"
        )

        logger.info(
            f"[FISCAL] analysis started "
            f"tenant={tenant_id} "
            f"trace_id={trace_id}"
        )

        score = 0

        alertas = []

        recomendaciones = []

        # =====================================================
        # NORMALIZATION
        # =====================================================

        ingresos = max(
            self.safe_float(
                data.get("ingresos")
            ),
            0
        )

        gastos = max(
            self.safe_float(
                data.get("gastos")
            ),
            0
        )

        iva = max(
            self.safe_float(
                data.get("iva")
            ),
            0
        )

        isr = max(
            self.safe_float(
                data.get("isr_retenido")
            ),
            0
        )

        deuda = max(
            self.safe_float(
                data.get("deuda_mensual")
            ),
            0
        )

        cartera = max(
            self.safe_float(
                data.get("cartera_vencida")
            ),
            0
        )

        empleados = max(
            self.safe_int(
                data.get("trabajadores")
            ),
            0
        )

        sin_imss = max(
            self.safe_int(
                data.get("trabajadores_sin_imss")
            ),
            0
        )

        repse = self.to_bool(
            data.get("repse_suspendido")
        )

        bloqueo = self.to_bool(
            data.get("bloqueo_bancario")
        )

        # =====================================================
        # CALCULATIONS
        # =====================================================

        flujo = ingresos - gastos - deuda

        exposicion_estimada = round(
            (iva + isr + deuda) * 1.35,
            2
        )

        # =====================================================
        # LIQUIDITY
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
        # SAT PRESSURE
        # =====================================================

        if ingresos > 0 and (
            (iva + isr) > ingresos * 0.25
        ):

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

        if (
            empleados > 0 and
            (sin_imss / empleados) > 0.10
        ):

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
        # BANKING
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
        # COLLECTIONS
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
        # DEBT
        # =====================================================

        if ingresos > 0 and (
            deuda > ingresos * 0.45
        ):

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
        # LEVELS
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

        latency_ms = round(
            (time.time() - started) * 1000,
            2
        )

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

            "engine": self.engine,

            "engine_status": "OK",

            "version": self.version,

            "regulatory_version":
                self.regulatory_version,

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

                "exposicion_estimada":
                    exposicion_estimada,

                "alertas": alertas,

                "recomendaciones":
                    recomendaciones
            }
        }
