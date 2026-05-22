# core/validators.py -- MESAN Omega Input Validation Layer
from dataclasses import dataclass, field
from typing import List

@dataclass
class ValidationResult:
    valid: bool
    errors: List[dict] = field(default_factory=list)
    warnings: List[dict] = field(default_factory=list)
    confidence_penalty: int = 0

class InputValidator:

    MAX_TRABAJADORES  = 100000
    MAX_SALARIO_DIARIO = 50000
    MAX_MESES_OMISION  = 120
    MAX_MONTO_FISCAL   = 500_000_000

    def validate(self, data: dict) -> ValidationResult:
        errors = []; warnings = []; penalty = 0

        def err(campo, msg, code):
            errors.append({"campo": campo, "mensaje": msg, "code": code})

        def warn(campo, msg):
            warnings.append({"campo": campo, "mensaje": msg})
            return 5

        # Tipos
        for campo in ["ingresos","nomina","gastos","deuda_mensual","isr_retenido","iva","cartera_vencida"]:
            val = data.get(campo)
            if val is not None:
                try:
                    float(val)
                except (TypeError, ValueError):
                    err(campo, f"{campo} debe ser numerico.", "TIPO_INVALIDO")

        # Negativos criticos
        for campo in ["ingresos","nomina","gastos","deuda_mensual","isr_retenido","iva","cartera_vencida"]:
            val = data.get(campo, 0)
            try:
                if float(val) < 0:
                    err(campo, f"{campo} no puede ser negativo.", "NEGATIVO")
            except: pass

        # Trabajadores
        sin_imss    = data.get("trabajadores_sin_imss", 0)
        trabajadores = data.get("trabajadores", 0)
        try:
            sin_imss    = int(sin_imss)
            trabajadores = int(trabajadores)
            if sin_imss < 0:
                err("trabajadores_sin_imss", "No puede ser negativo.", "NEGATIVO")
            if sin_imss > trabajadores and trabajadores > 0:
                err("trabajadores_sin_imss", "Sin IMSS supera total de trabajadores.", "INCONSISTENTE")
            if trabajadores > self.MAX_TRABAJADORES:
                penalty += warn("trabajadores", f"Valor inusualmente alto: {trabajadores}")
        except: pass

        # Salario
        sal = data.get("salario_diario_promedio", 350)
        try:
            sal = float(sal)
            if sal < 278.80:
                penalty += warn("salario_diario_promedio", f"Salario ${sal} por debajo del minimo legal $278.80.")
            if sal > self.MAX_SALARIO_DIARIO:
                penalty += warn("salario_diario_promedio", f"Salario ${sal} inusualmente alto.")
        except: pass

        # Meses
        meses = data.get("meses_omision", 1)
        try:
            meses = int(meses)
            if meses < 1:
                err("meses_omision", "Meses de omision debe ser >= 1.", "FUERA_RANGO")
            if meses > self.MAX_MESES_OMISION:
                penalty += warn("meses_omision", f"{meses} meses de omision es inusual.")
        except: pass

        # Montos fiscales
        for campo in ["isr_retenido","iva"]:
            val = data.get(campo, 0)
            try:
                if float(val) > self.MAX_MONTO_FISCAL:
                    penalty += warn(campo, f"{campo} supera limite de validacion.")
            except: pass

        # Inconsistencias financieras
        ingresos = data.get("ingresos", 0)
        isr      = data.get("isr_retenido", 0)
        try:
            if float(isr) > float(ingresos) * 2 and float(ingresos) > 0:
                penalty += warn("isr_retenido", "ISR supera 2x ingresos — revisar.")
        except: pass

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            confidence_penalty=min(penalty, 40)
        )
