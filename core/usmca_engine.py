# core/usmca_engine.py — MESAN Ω
# Motor T-MEC con VCR dinamico por sector

RULES_BY_SECTOR = {
    "automotriz":   0.75,
    "textil":       0.65,
    "industrial":   0.60,
    "manufactura":  0.70,
    "servicios":    0.55,
    "logistica":    0.60,
    "electronica":  0.65,
    "default":      0.60
}

class OmegaUSMCATrace:
    def __init__(self):
        self.sueldo_base = 13410

    def calcular_vcr_costo_neto(
        self,
        costo_materiales_no_originarios: float,
        costo_materiales_originarios: float,
        horas_hombre_directas: int,
        gastos_indirectos_fabricacion: float,
        sector: str = "default"
    ) -> dict:
        costo_laboral_por_hora = self.sueldo_base / 160
        costo_mano_obra = costo_laboral_por_hora * horas_hombre_directas

        costo_neto = (
            costo_materiales_no_originarios +
            costo_materiales_originarios +
            costo_mano_obra +
            gastos_indirectos_fabricacion
        )

        if costo_neto == 0:
            return {"status": "ERROR", "motivo": "Costo neto igual a cero."}

        vcr_requerido = RULES_BY_SECTOR.get(sector.lower(), RULES_BY_SECTOR["default"])
        vcr_obtenido = (costo_neto - costo_materiales_no_originarios) / costo_neto
        cumple = vcr_obtenido >= vcr_requerido

        return {
            "analisis_origen": {
                "sector": sector,
                "mercado_objetivo": "NORTE_AMERICA_US_CA",
                "costo_neto_calculado": round(costo_neto, 2),
                "vcr_porcentual": round(vcr_obtenido * 100, 2),
                "vcr_requerido": round(vcr_requerido * 100, 2),
                "cumplimiento_origen": cumple
            },
            "aduana": {
                "status_arancel": "EXENTO_TMEC" if cumple else "RIESGO_ARANCELARIO",
                "accion_requerida": "EMITIR_CERTIFICADO_ORIGEN" if cumple else "REDUZCA_INSUMOS_EXTRANJEROS"
            }
        }
