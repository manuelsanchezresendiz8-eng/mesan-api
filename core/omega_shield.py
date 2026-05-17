# core/omega_shield.py — MESAN Ω
import os
import json

class OmegaShield:
    def __init__(self, efo_list_path=None):
        self.efo_list_path = efo_list_path
        self.blacklist_rfcs = self._load_blacklist()

    def _load_blacklist(self):
        if self.efo_list_path and os.path.exists(self.efo_list_path):
            with open(self.efo_list_path, 'r') as f:
                return json.load(f)
        return ["XAXX010101000", "FACT123456AAA"]

    def evaluar_proveedor_efos(self, rfc_proveedor: str) -> dict:
        if rfc_proveedor in self.blacklist_rfcs:
            return {
                "status": "CRITICAL_RISK",
                "codigo_alerta": "EFO_DETECTED",
                "mensaje": f"RFC {rfc_proveedor} identificado en lista negra SAT (Art. 69-B). Se recomienda revision inmediata."
            }
        return {"status": "CLEAN", "mensaje": "Proveedor sin registros negativos en EFOS."}

    def auditar_coherencia_operativa(
        self,
        total_facturado_mes: float,
        nomina_pagada_mes: float,
        gastos_logistica_mes: float
    ) -> dict:
        if total_facturado_mes > 0:
            proporcion_laboral = nomina_pagada_mes / total_facturado_mes
            proporcion_logistica = gastos_logistica_mes / total_facturado_mes
        else:
            proporcion_laboral = 1.0
            proporcion_logistica = 1.0

        riesgo_materialidad = "BAJO"
        indicadores = []

        if proporcion_laboral < 0.10 and total_facturado_mes > 50000:
            riesgo_materialidad = "ALTO"
            indicadores.append("NOMINA_INSUFICIENTE_PARA_EL_VOLUMEN_DE_VENTA")

        if proporcion_logistica < 0.02 and total_facturado_mes > 50000:
            riesgo_materialidad = "ALTO"
            indicadores.append("GASTOS_OPERATIVOS_ANORMALMENTE_BAJOS")

        return {
            "analisis_materialidad": {
                "nivel_riesgo_auditoria": riesgo_materialidad,
                "alertas_detectadas": indicadores,
                "metricas": {
                    "ratio_laboral": round(proporcion_laboral * 100, 2),
                    "ratio_logistico": round(proporcion_logistica * 100, 2)
                }
            },
            "status": "COMPLETADO"
        }
