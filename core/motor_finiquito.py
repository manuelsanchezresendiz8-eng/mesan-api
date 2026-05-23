# core/motor_finiquito.py -- MESAN Omega Settlement Engine v2.0
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from datetime import datetime
import logging, sys, os
sys.path.insert(0, '/mnt/user-data/outputs/omega')

logger = logging.getLogger("mesan.finiquito")

def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class RuleEngineDeducciones:
    VERSION = "2.0.0"
    def __init__(self, deductions_config: Optional[Dict[str,Any]] = None):
        self.reglas = {k: Decimal(str(v)) for k,v in (deductions_config or {
            "obra":Decimal("0.00"),"falta":Decimal("0.10"),
            "renuncia":Decimal("0.00"),"abandono":Decimal("0.15"),"despido":Decimal("0.00")
        }).items()}
    def obtener_factor(self, tipo_baja: str) -> Decimal:
        return Decimal(str(self.reglas.get(tipo_baja, "0.00")))

class MotorCalculoFiniquito:
    VERSION = "2.0.0"

    def __init__(self, salario_diario, tenant_id: str = "DEFAULT", regulator: str = "LABORAL"):
        self.salario    = money(salario_diario)
        self.tenant_id  = tenant_id
        self.regulator  = regulator
        self.ruleset_version = "lft_2026_02"
        # Defaults — se sobreescriben si RegulationManager carga JSON
        self.aguinaldo_dias  = Decimal("15")
        self.prima_vacacional= Decimal("0.25")
        self.factor_isr      = Decimal("0.10")
        self.factor_imss     = Decimal("0.03")
        self.tipos_baja      = ["renuncia","abandono","obra","despido","falta"]
        self.rules           = RuleEngineDeducciones()
        # Intentar cargar desde RegulationManager
        try:
            from core.regulation_manager import RegulationManager
            regs = RegulationManager()
            self.ruleset_version = regs.get_active_ruleset(regulator)
            ruleset = regs.load_ruleset(regulator, self.ruleset_version)
            if "rules" in ruleset:
                r = ruleset["rules"]
                self.aguinaldo_dias   = Decimal(str(r.get("aguinaldo_dias",15)))
                self.prima_vacacional = Decimal(str(r.get("prima_vacacional",0.25)))
                self.factor_isr       = Decimal(str(r.get("isr_factor",0.10)))
                self.factor_imss      = Decimal(str(r.get("imss_factor",0.03)))
                self.tipos_baja       = r.get("tipos_baja", self.tipos_baja)
            if "deducciones" in ruleset:
                self.rules = RuleEngineDeducciones(ruleset["deducciones"])
        except Exception:
            pass  # Fallback a defaults

    def calcular_proporcional(self, dias_laborados, base_anual_dias) -> Decimal:
        return money((Decimal(str(base_anual_dias))/Decimal("365")) * Decimal(str(dias_laborados)) * self.salario)

    def calcular_isr(self, total_bruto) -> Decimal:
        return money(money(total_bruto) * self.factor_isr)

    def calcular_imss(self, total_bruto) -> Decimal:
        return money(money(total_bruto) * self.factor_imss)

    def aplicar_reglas_deduccion(self, tipo_baja, total_bruto) -> Decimal:
        return money(money(total_bruto) * self.rules.obtener_factor(tipo_baja))

    def calcular_finiquito(self, tipo_baja, dias_devengados, dias_laborados,
                           vacaciones_pendientes=0, bonos_pendientes=0) -> dict:
        if tipo_baja not in self.tipos_baja:
            raise ValueError(f"Tipo de baja invalido: {tipo_baja}")

        salario_pendiente = money(Decimal(str(dias_devengados)) * self.salario)
        aguinaldo         = self.calcular_proporcional(dias_laborados, self.aguinaldo_dias)
        vacaciones        = money(Decimal(str(vacaciones_pendientes)) * self.salario)
        bonos             = money(bonos_pendientes)
        total_bruto       = money(salario_pendiente + aguinaldo + vacaciones + bonos)
        isr               = self.calcular_isr(total_bruto)
        imss              = self.calcular_imss(total_bruto)
        deduccion_extra   = self.aplicar_reglas_deduccion(tipo_baja, total_bruto)
        total_deducciones = money(isr + imss + deduccion_extra)
        total_neto        = money(total_bruto - total_deducciones)

        logger.info(f"[FINIQUITO] tenant={self.tenant_id} tipo={tipo_baja} neto={total_neto}")

        return {"tenant_id":self.tenant_id,"timestamp":datetime.utcnow().isoformat(),
                "regulatory_version":self.ruleset_version,"tipo_baja":tipo_baja,
                "salario_pendiente":float(salario_pendiente),"aguinaldo":float(aguinaldo),
                "vacaciones":float(vacaciones),"bonos":float(bonos),
                "total_bruto":float(total_bruto),"isr":float(isr),"imss":float(imss),
                "deduccion_extra":float(deduccion_extra),"total_deducciones":float(total_deducciones),
                "total_neto":float(total_neto),
                "audit":{"engine_version":self.VERSION,"ruleset_version":self.ruleset_version}}
