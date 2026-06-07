# schemas/omega_evaluation_request.py -- MESAN Omega v1.1
"""
OmegaEvaluationRequest — Contrato oficial de entrada al pipeline MESAN Ω.

Define todos los campos requeridos por el OmegaOrchestrator.
Separa la ruta de evaluación técnica de la ruta de captación comercial.

    /api/leads          → captación CRM (nombre, empresa, sector, empleados)
    /api/v1/omega/evaluate → evaluación técnica (este contrato)
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Catálogo de opiniones válidas ─────────────────────────────────────────────
VALID_OPINIONS = {"POSITIVA", "NEGATIVA", "CON_OBSERVACIONES"}


def _parse_bool(value, default: bool = True) -> bool:
    """
    Corrección 2: convierte strings a bool correctamente.
    bool("false") == True en Python — este helper lo resuelve.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "1", "yes", "si", "sí", "on"):
            return True
        if v in ("false", "0", "no", "off"):
            return False
    return default


def _parse_opinion(value: str, default: str = "POSITIVA") -> str:
    """
    Corrección 3: normaliza y valida opiniones SAT/IMSS.
    Solo acepta valores del catálogo VALID_OPINIONS.
    """
    normalized = str(value).strip().upper()
    if normalized in VALID_OPINIONS:
        return normalized
    return default


@dataclass
class OmegaEvaluationRequest:
    """
    Contrato oficial de entrada para POST /api/v1/omega/evaluate.
    Versión 1.1 — validación fuerte, bool parsing, catálogo de opiniones.

    Campos financieros obligatorios (deben ser > 0 o >= 0 según el campo):
        empresa_nombre, sector, empleados, ingresos, nomina,
        gastos, caja_disponible, deuda_mensual.
    """

    # ── Identidad ─────────────────────────────────────────────────────────────
    empresa_nombre: str
    sector:         str
    tenant_id:      str          = "DEFAULT"
    trace_id:       Optional[str] = None
    schema_version: str          = "1.1"   # Corrección 4: versionamiento del contrato

    # ── Financieros (obligatorios) ────────────────────────────────────────────
    ingresos:        float = 0.0   # debe ser > 0 en validación
    nomina:          float = 0.0
    gastos:          float = 0.0
    caja_disponible: float = 0.0
    deuda_mensual:   float = 0.0

    # ── Operativos ────────────────────────────────────────────────────────────
    empleados:             int   = 0
    empleados_criticos:    int   = 0
    trabajadores_sin_imss: int   = 0
    demandas_laborales:    int   = 0
    rotacion_anual:        float = 0.0
    severance_estimado:    float = 0.0

    # ── Regulatorio ───────────────────────────────────────────────────────────
    repse_vigente:  bool = True
    opinion_sat:    str  = "POSITIVA"
    opinion_imss:   str  = "POSITIVA"

    # ── Contractual ───────────────────────────────────────────────────────────
    contratos_vencidos:        int  = 0
    proveedores_sin_contrato:  int  = 0
    litigios_activos:          int  = 0

    # ── Políticas ─────────────────────────────────────────────────────────────
    nom_035:            bool = False
    reglamento_interno: bool = False
    cumplimiento_stps:  bool = False
    plan_capacitacion:  bool = False

    def to_orchestrator_dict(self) -> dict:
        """Convierte al formato que espera OmegaOrchestrator.ejecutar()."""
        import uuid
        return {
            "tenant_id":              self.tenant_id,
            "trace_id":               self.trace_id or str(uuid.uuid4()),
            "empresa_nombre":         self.empresa_nombre,
            "sector":                 self.sector,
            "ingresos":               self.ingresos,
            "nomina":                 self.nomina,
            "gastos":                 self.gastos,
            "caja_disponible":        self.caja_disponible,
            "deuda_mensual":          self.deuda_mensual,
            "empleados":              self.empleados,
            "empleados_criticos":     self.empleados_criticos,
            "trabajadores_sin_imss":  self.trabajadores_sin_imss,
            "demandas_laborales":     self.demandas_laborales,
            "rotacion_anual":         self.rotacion_anual,
            "severance_estimado":     self.severance_estimado,
            "repse_vigente":          self.repse_vigente,
            "opinion_sat":            self.opinion_sat,
            "opinion_imss":           self.opinion_imss,
            "contratos_vencidos":     self.contratos_vencidos,
            "proveedores_sin_contrato": self.proveedores_sin_contrato,
            "litigios_activos":       self.litigios_activos,
            "nom_035":                self.nom_035,
            "reglamento_interno":     self.reglamento_interno,
            "cumplimiento_stps":      self.cumplimiento_stps,
            "plan_capacitacion":      self.plan_capacitacion,
            "schema_version":         self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OmegaEvaluationRequest":
        """Construye desde dict — para uso en el endpoint FastAPI."""
        return cls(
            empresa_nombre         = str(data.get("empresa_nombre", data.get("empresa", ""))),
            sector                 = str(data.get("sector", "")),
            tenant_id              = str(data.get("tenant_id", "DEFAULT")),
            trace_id               = data.get("trace_id"),
            ingresos               = float(data.get("ingresos", 0)),
            nomina                 = float(data.get("nomina", 0)),
            gastos                 = float(data.get("gastos", 0)),
            caja_disponible        = float(data.get("caja_disponible", 0)),
            deuda_mensual          = float(data.get("deuda_mensual", 0)),
            empleados              = int(data.get("empleados", 0)),
            empleados_criticos     = int(data.get("empleados_criticos", 0)),
            trabajadores_sin_imss  = int(data.get("trabajadores_sin_imss", 0)),
            demandas_laborales     = int(data.get("demandas_laborales", 0)),
            rotacion_anual         = float(data.get("rotacion_anual", 0)),
            severance_estimado     = float(data.get("severance_estimado", 0)),
            repse_vigente          = _parse_bool(data.get("repse_vigente", True), default=True),
            opinion_sat            = _parse_opinion(data.get("opinion_sat", "POSITIVA")),
            opinion_imss           = _parse_opinion(data.get("opinion_imss", "POSITIVA")),
            contratos_vencidos     = int(data.get("contratos_vencidos", 0)),
            proveedores_sin_contrato = int(data.get("proveedores_sin_contrato", 0)),
            litigios_activos       = int(data.get("litigios_activos", 0)),
            nom_035                = _parse_bool(data.get("nom_035", False), default=False),
            reglamento_interno     = _parse_bool(data.get("reglamento_interno", False), default=False),
            cumplimiento_stps      = _parse_bool(data.get("cumplimiento_stps", False), default=False),
            plan_capacitacion      = _parse_bool(data.get("plan_capacitacion", False), default=False),
        )

    def validate(self) -> list[str]:
        """
        Corrección 1: validación fuerte de campos obligatorios.
        Retorna lista de errores — vacía si todo es válido.
        """
        errors = []

        # Identidad
        if not self.empresa_nombre.strip():
            errors.append("empresa_nombre es obligatorio")
        if not self.sector.strip():
            errors.append("sector es obligatorio")

        # Financieros obligatorios
        if self.ingresos <= 0:
            errors.append("ingresos debe ser mayor a 0")
        if self.empleados <= 0:
            errors.append("empleados debe ser mayor a 0")

        # Financieros no negativos
        if self.nomina < 0:
            errors.append("nomina no puede ser negativo")
        if self.gastos < 0:
            errors.append("gastos no puede ser negativo")
        if self.caja_disponible < 0:
            errors.append("caja_disponible no puede ser negativo")
        if self.deuda_mensual < 0:
            errors.append("deuda_mensual no puede ser negativo")

        # Opiniones (catálogo)
        if self.opinion_sat not in VALID_OPINIONS:
            errors.append(f"opinion_sat inválida: {self.opinion_sat}. Válidas: {VALID_OPINIONS}")
        if self.opinion_imss not in VALID_OPINIONS:
            errors.append(f"opinion_imss inválida: {self.opinion_imss}. Válidas: {VALID_OPINIONS}")

        # Schema version
        if self.schema_version not in ("1.0", "1.1"):
            errors.append(f"schema_version no soportada: {self.schema_version}")

        return errors
