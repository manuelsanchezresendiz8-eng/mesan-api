# schemas/omega_evaluation_request.py -- MESAN Omega v1.0
"""
OmegaEvaluationRequest -- Contrato de entrada al pipeline tecnico interno.

Usado por routes/omega_routes.py (POST /api/v1/omega/evaluate).
Distinto del flujo publico simplificado de la landing (execution_routes.py).

Campos documentados en omega_routes.py:
    empresa_nombre*  str
    sector*          str
    empleados        int
    ingresos         float   (mensual)
    nomina           float   (mensual)
    gastos           float   (mensual)
    caja_disponible  float
    deuda_mensual    float

Campos adicionales requeridos por OmegaOrchestrator._build_empresa():
    empleados_criticos, demandas_laborales, trabajadores_sin_imss,
    rotacion_anual, severance_estimado, opinion_sat, opinion_imss,
    repse_vigente, cartera_vencida, iva, isr_retenido,
    bloqueo_bancario, trabajadores
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OmegaEvaluationRequest:

    # Identidad
    trace_id:   str = ""
    tenant_id:  str = "DEFAULT"

    # Campos obligatorios
    empresa_nombre: str = ""
    sector:         str = ""

    # Financieros
    empleados:          int   = 0
    ingresos:           float = 0.0
    nomina:              float = 0.0
    gastos:              float = 0.0
    caja_disponible:     float = 0.0
    deuda_mensual:       float = 0.0
    cartera_vencida:     float = 0.0
    iva:                 float = 0.0
    isr_retenido:        float = 0.0

    # Laborales
    empleados_criticos:    int = 0
    demandas_laborales:    int = 0
    trabajadores_sin_imss: int = 0
    trabajadores:          int = 0
    rotacion_anual:        float = 0.0
    severance_estimado:    float = 0.0

    # Regulatorios
    opinion_sat:       str  = "NO_LOCALIZADA"
    opinion_imss:      str  = "NO_LOCALIZADA"
    repse_vigente:     bool = True
    bloqueo_bancario:  bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OmegaEvaluationRequest":
        """Construye el request desde un dict, ignorando claves desconocidas."""
        valid_fields = {f for f in cls.__dataclass_fields__.keys()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def validate(self) -> List[str]:
        """Valida campos obligatorios. Retorna lista de errores (vacia si OK)."""
        errors = []
        if not self.empresa_nombre or not self.empresa_nombre.strip():
            errors.append("empresa_nombre es obligatorio")
        if not self.sector or not self.sector.strip():
            errors.append("sector es obligatorio")
        if self.empleados < 0:
            errors.append("empleados no puede ser negativo")
        if self.ingresos < 0:
            errors.append("ingresos no puede ser negativo")
        return errors

    def to_orchestrator_data(self) -> Dict[str, Any]:
        """Convierte al formato que espera OmegaOrchestrator.ejecutar()."""
        return {
            "tenant_id":              self.tenant_id,
            "trace_id":               self.trace_id,
            "empresa_nombre":         self.empresa_nombre,
            "ingresos":               self.ingresos,
            "gastos":                 self.gastos,
            "nomina":                 self.nomina,
            "deuda_mensual":          self.deuda_mensual,
            "cartera_vencida":        self.cartera_vencida,
            "iva":                    self.iva,
            "isr_retenido":           self.isr_retenido,
            "empleados":              self.empleados,
            "trabajadores":           self.trabajadores or self.empleados,
            "trabajadores_sin_imss":  self.trabajadores_sin_imss,
            "empleados_criticos":     self.empleados_criticos,
            "demandas_laborales":     self.demandas_laborales,
            "rotacion_anual":         self.rotacion_anual,
            "severance_estimado":     self.severance_estimado,
            "caja_disponible":        self.caja_disponible,
            "repse_vigente":          self.repse_vigente,
            "repse_suspendido":       not self.repse_vigente,
            "bloqueo_bancario":       self.bloqueo_bancario,
            "opinion_sat":            self.opinion_sat,
            "opinion_imss":           self.opinion_imss,
        }