# =========================================================
# MESAN Omega -- ENTERPRISE DECISION ENGINE v3
# =========================================================

from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class EmpresaInput:
    sector: str
    ingresos_mensuales: float
    nomina: float
    gastos_fijos: float
    deuda_bancaria: float = 0
    pago_deuda_mensual: float = 0
    cartera_vencida: float = 0
    adeudo_sat: float = 0
    adeudo_imss: float = 0
    empleados_sin_imss: int = 0
    permisos_vencidos: List[str] = field(default_factory=list)
    incidente_operativo: bool = False
    seguro_rc: bool = True
    cliente_rescision: bool = False
    lineas_credito_saturadas: bool = False


class MesanOmegaDecisionEngine:

    def __init__(self, empresa: EmpresaInput):
        self.e = empresa
        self.protocolos = []
        self.acciones_criticas = []

    def calcular_riesgo(self):
        flujo = self.e.ingresos_mensuales - self.e.nomina - self.e.gastos_fijos - self.e.pago_deuda_mensual
        rl = 0; rf = 0; rlab = 0; rreg = 0; rop = 0

        if flujo < 0: rl += 40
        if self.e.cartera_vencida > self.e.ingresos_mensuales: rl += 25
        if self.e.lineas_credito_saturadas: rl += 20

        total_fiscal = self.e.adeudo_sat + self.e.adeudo_imss
        if total_fiscal > 500000: rf += 25
        if total_fiscal > 1000000: rf += 40

        if self.e.empleados_sin_imss > 0:
            rlab += min(self.e.empleados_sin_imss * 1.5, 30)

        if len(self.e.permisos_vencidos) > 0:
            rreg += len(self.e.permisos_vencidos) * 15

        if self.e.incidente_operativo: rop += 20
        if not self.e.seguro_rc: rop += 20
        if self.e.cliente_rescision: rop += 20

        score = rl*0.30 + rf*0.20 + rlab*0.20 + rreg*0.15 + rop*0.15
        return round(min(score, 100), 1)

    def nivel_riesgo(self, score):
        if score >= 85: return "CRITICO"
        elif score >= 65: return "ALTO"
        elif score >= 40: return "MEDIO"
        return "CONTROLADO"

    def activar_protocolos(self):
        flujo = self.e.ingresos_mensuales - self.e.nomina - self.e.gastos_fijos - self.e.pago_deuda_mensual
        if flujo < 0:
            self.protocolos.append({"titulo": "LIQUIDITY DEFENSE MODE", "objetivo": "Preservar operacion minima viable 45 dias"})
        if self.e.adeudo_sat > 300000:
            self.protocolos.append({"titulo": "FISCAL CONTAINMENT MODE", "objetivo": "Reducir exposicion SAT y evitar ejecucion bancaria"})
        if len(self.e.permisos_vencidos) > 0:
            self.protocolos.append({"titulo": "COMPLIANCE BREACH MODE", "objetivo": "Regularizar permisos criticos"})
        if self.e.empleados_sin_imss > 0:
            self.protocolos.append({"titulo": "LABOR SHIELD PROTOCOL", "objetivo": "Reducir contingencia laboral y retroactivos"})

    def generar_prioridades(self):
        flujo = self.e.ingresos_mensuales - self.e.nomina - self.e.gastos_fijos - self.e.pago_deuda_mensual
        if flujo < 0:
            self.acciones_criticas.append({"prioridad": 1, "titulo": "PRESERVAR NOMINA", "detalle": "Evitar ruptura operativa y contingencia laboral."})
            self.acciones_criticas.append({"prioridad": 2, "titulo": "NEGOCIAR CON ACREEDORES", "detalle": "Extender ventanas de pago antes de mora formal."})
        if self.e.cartera_vencida > 0:
            self.acciones_criticas.append({"prioridad": 3, "titulo": "RECUPERACION DE FLUJO", "detalle": "Activar cobranza intensiva urgente."})
        if self.e.adeudo_sat > 0:
            self.acciones_criticas.append({"prioridad": 4, "titulo": "CONTENCION FISCAL", "detalle": "Negociar convenio SAT antes de acciones coercitivas."})

    def generar_escenarios(self):
        escenarios = []
        if self.e.cartera_vencida > 0:
            escenarios.append("SI clientes NO pagan en 15 dias -> riesgo operativo sube +18%")
        if self.e.lineas_credito_saturadas:
            escenarios.append("SI banco congela lineas -> continuidad operativa cae bajo 40%")
        if self.e.empleados_sin_imss > 0:
            escenarios.append("SI ocurre accidente laboral -> contingencia IMSS se acelera")
        return escenarios

    def generar_reporte(self):
        score = self.calcular_riesgo()
        nivel = self.nivel_riesgo(score)
        self.activar_protocolos()
        self.generar_prioridades()
        return {
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "score": score,
            "nivel": nivel,
            "protocolos": self.protocolos,
            "prioridades": self.acciones_criticas,
            "escenarios": self.generar_escenarios()
        }
