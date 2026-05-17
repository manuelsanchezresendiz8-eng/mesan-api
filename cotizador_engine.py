# routes/enterprise_audit.py — MESAN Ω
# Endpoints Shield y USMCA — imports corregidos

from fastapi import APIRouter
from pydantic import BaseModel
from core.omega_shield import OmegaShield
from core.usmca_engine import OmegaUSMCATrace

router = APIRouter(prefix="/api/v1/enterprise", tags=["Enterprise Audit"])

shield = OmegaShield()
trace  = OmegaUSMCATrace()

class ShieldRequest(BaseModel):
    rfc_proveedor:    str
    total_facturado:  float
    nomina_pagada:    float
    gastos_logistica: float

class USMCARequest(BaseModel):
    no_originarios:    float
    originarios:       float
    horas_hombre:      int
    gastos_indirectos: float
    sector:            str = "default"

@router.post("/shield/verify")
def verificar_blindaje(data: ShieldRequest):
    resultado_efos = shield.evaluar_proveedor_efos(data.rfc_proveedor)
    resultado_coherencia = shield.auditar_coherencia_operativa(
        total_facturado_mes=data.total_facturado,
        nomina_pagada_mes=data.nomina_pagada,
        gastos_logistica_mes=data.gastos_logistica
    )
    return {"efos": resultado_efos, "materialidad": resultado_coherencia}

@router.post("/usmca/validate")
def validar_origen_exportacion(data: USMCARequest):
    return trace.calcular_vcr_costo_neto(
        costo_materiales_no_originarios=data.no_originarios,
        costo_materiales_originarios=data.originarios,
        horas_hombre_directas=data.horas_hombre,
        gastos_indirectos_fabricacion=data.gastos_indirectos,
        sector=data.sector
    )
