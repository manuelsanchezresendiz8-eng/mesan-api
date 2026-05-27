# services/fiscal_sentinel_engine.py
# MESAN Omega Fiscal Sentinel Engine v2.2
# HARDENED ENTERPRISE VERSION

import logging
import time

from datetime import datetime, timezone

logger = logging.getLogger("mesan.fiscal")


class FiscalSentinelEngine:

    def __init__(self):

        self.version = "2.2"

        self.regulatory_version = "SAT_IMSS_2026_02"

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
    # MAIN ANALYSIS
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

        score = 0

        alertas = []

        recomendaciones = []

        # =====================================================
        # SAFE INPUTS
        # =====================================================

        ingresos = self.safe_float(
            data.get("ingresos")
        )

        gastos = self.safe_float(
            data.get("gastos")
        )

        iva = self.safe_float(
            data.get("iva")
        )

        isr = self.safe_float(
            data.get("isr_retenido")
        )

        deuda = self.safe_float(
            data.get("deuda_mensual")
        )

        cartera = self.safe_float(
            data.get("cartera_vencida")
        )

        empleados = self.safe_int(
            data.get("trabajadores")
        )

        sin_imss = self.safe_int(
            data.get("trabajadores_sin_imss")
        )

        repse = self.to_bool(
            data.get("repse_suspendido")
        )

        bloqueo = self.to_bool(
            data.get("bloqueo_bancario")
        )

        # =====================================================
        # CALCULOS
        # =====================================================

        flujo = ingresos - gastos - deuda

        carga_fiscal = iva + isr

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
        # SAT
        # =====================================================

        if ingresos > 0:

            if carga_fiscal > ingresos * 0.25:

                score += 15

                alertas.append({
                    "tipo": "SAT",
                    "nivel": "ALTO",
                    "mensaje": "Presión fiscal elevada"
                })

                recomendaciones.append(
                    "Reestructurar estrategia fiscal"
                )

        # =====================================================
        # IMSS
        # =====================================================

        if empleados > 0:

            ratio_imss = sin_imss / empleados

            if ratio_imss > 0.10:

                score += 18

                alertas.append({
                    "tipo": "IMSS",
                    "nivel": "CRITICO",
                    "mensaje": "Plantilla fuera de IMSS"
                })

                recomendaciones.append(
                    "Regularizar plantilla laboral"
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
                "Activar protocolo financiero"
            )

        # =====================================================
        # COBRANZA
        # =====================================================

        if ingresos > 0:

            if cartera > ingresos:

                score += 12

                alertas.append({
                    "tipo": "COBRANZA",
                    "nivel": "ALTO",
                    "mensaje": "Cartera vencida crítica"
                })

                recomendaciones.append(
                    "Recuperar cobranza urgente"
                )

        # =====================================================
        # DEUDA
        # =====================================================

        if ingresos > 0:

            if deuda > ingresos * 0.45:

                score += 15

                alertas.append({
                    "tipo": "DEUDA",
                    "nivel": "CRITICO",
                    "mensaje": "Presión bancaria crítica"
                })

                recomendaciones.append(
                    "Renegociar deuda bancaria"
                )

        # =====================================================
        # HARD REGULATORY FLOOR
        # =====================================================

        # REPSE suspendido nunca puede ser BAJO
        if repse:

            score = max(score, 60)

        # Bloqueo bancario nunca puede ser menor a CRITICO
        if bloqueo:

            score = max(score, 85)

        # =====================================================
        # NORMALIZACION SCORE
        # =====================================================

        score = min(score, 100)

        # =====================================================
        # NIVEL FINAL
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
        # METRICAS
        # =====================================================

        latency_ms = round(
            (time.time() - started) * 1000,
            2
        )

        exposicion = round(
            (iva + isr + deuda) * 1.35,
            2
        )

        # =====================================================
        # RESPONSE
        # =====================================================

        return {

            "engine": "MESAN_FISCAL_SENTINEL",

            "engine_status": "OK",

            "version": self.version,

            "regulatory_version":
                self.regulatory_version,

            "timestamp":
                datetime.now(
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
                    exposicion,

                "alertas": alertas,

                "recomendaciones":
                    recomendaciones
            }
        }
