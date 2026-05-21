# ============================================================
# MESAN Omega -- ENTERPRISE RESILIENCE CORE v6.0
# ============================================================

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import traceback
import logging
import statistics

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def safe_float(value, default=0.0):
    try:
        return default if value is None else float(value)
    except: return default

def safe_int(value, default=0):
    try:
        return default if value is None else int(value)
    except: return default

def safe_div(a, b, default=0):
    try:
        return default if b == 0 else a / b
    except: return default


@dataclass
class Alerta:
    tipo: str
    severidad: str
    mensaje: str

@dataclass
class KPI:
    nombre: str
    valor: str
    estado: str

@dataclass
class Riesgo:
    categoria: str
    descripcion: str
    severidad: int
    impacto: float
    accion: str

@dataclass
class Escenario:
    nombre: str
    probabilidad: str
    impacto: str
    dias_supervivencia: int
    descripcion: str

@dataclass
class Decision:
    prioridad: str
    accion: str
    responsable: str
    plazo_horas: int

@dataclass
class EmpresaInput:
    nombre: str
    sector: str = "GENERAL"
    ingresos: float = 0
    nomina: float = 0
    gastos: float = 0
    deuda_mensual: float = 0
    cartera_vencida: float = 0
    iva: float = 0
    isr_retenido: float = 0
    trabajadores: int = 0
    trabajadores_sin_imss: int = 0
    bloqueo_bancario: bool = False
    repse_suspendido: bool = False
    sspc_vencido: bool = False
    vacaciones_pagadas: bool = True
    prima_vacacional_pagada: bool = True
    salario_diario: Optional[float] = None
    zona_fronteriza: bool = False

@dataclass
class ResultadoMotor:
    empresa_id: str
    score: int
    nivel: str
    tendencia: str
    confianza: int
    flujo_operativo: float
    burn_rate: float
    dias_supervivencia: int
    kpis: List[KPI] = field(default_factory=list)
    alertas: List[Alerta] = field(default_factory=list)
    riesgos: List[Riesgo] = field(default_factory=list)
    escenarios: List[Escenario] = field(default_factory=list)
    decisiones: List[Decision] = field(default_factory=list)
    cascadas: List[str] = field(default_factory=list)
    resumen_ceo: str = ""
    resumen_cfo: str = ""
    resumen_legal: str = ""
    resumen_operativo: str = ""
    stress_errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MesanOmegaResilienceCore:

    VERSION = "6.0"

    def __init__(self):
        self.historial = []
        self.umbrales = {"CRITICO": 85, "ALTO": 65, "MEDIO": 40}

    def validar_input(self, empresa: EmpresaInput):
        errores = []
        if empresa.ingresos < 0: errores.append("Ingresos negativos.")
        if empresa.nomina < 0: errores.append("Nomina negativa.")
        if empresa.gastos < 0: errores.append("Gastos negativos.")
        if empresa.trabajadores_sin_imss > empresa.trabajadores: errores.append("Trabajadores sin IMSS mayores al total.")
        return errores

    def analizar(self, empresa: EmpresaInput) -> ResultadoMotor:

        empresa_id = str(uuid.uuid4())[:8]
        errores = self.validar_input(empresa)
        if errores:
            raise ValueError(f"Errores de validacion: {errores}")

        riesgos=[]; alertas=[]; escenarios=[]; decisiones=[]; cascadas=[]; kpis=[]
        score = 0

        ingresos = safe_float(empresa.ingresos)
        nomina   = safe_float(empresa.nomina)
        gastos   = safe_float(empresa.gastos)
        deuda    = safe_float(empresa.deuda_mensual)

        burn_rate       = nomina + gastos + deuda
        flujo_operativo = ingresos - burn_rate
        dias_supervivencia = int(safe_div(max(ingresos,1), max(burn_rate,1), 1) * 30)
        dscr = round(safe_div(ingresos, deuda, 99), 2)

        kpis.append(KPI("Flujo Operativo", f"${flujo_operativo:,.0f}", "CRITICO" if flujo_operativo < 0 else "ESTABLE"))
        kpis.append(KPI("DSCR", str(dscr), "CRITICO" if dscr < 1.2 else "ESTABLE"))
        kpis.append(KPI("Dias Supervivencia", str(dias_supervivencia), "CRITICO" if dias_supervivencia < 30 else "ESTABLE"))

        if flujo_operativo < 0:
            riesgos.append(Riesgo("FINANCIERO", "Deficit operativo estructural", 35, abs(flujo_operativo)*12, "Reestructura inmediata"))
            decisiones.append(Decision("INMEDIATA", "Suspender gastos no esenciales y proteger nomina.", "CFO", 24))
            alertas.append(Alerta("LIQUIDEZ", "CRITICA", "Flujo operativo negativo detectado."))
            cascadas.append("Flujo negativo -> tension nomina -> riesgo laboral -> riesgo SAT")
            score += 30

        if empresa.isr_retenido > 0:
            riesgos.append(Riesgo("FISCAL", "ISR retenido pendiente", 35, empresa.isr_retenido*2, "Negociacion inmediata SAT"))
            decisiones.append(Decision("INMEDIATA", "Negociar convenio SAT antes de requerimiento.", "CFO + LEGAL", 24))
            cascadas.append("ISR retenido -> requerimiento SAT -> embargo -> bloqueo bancario")
            score += 35

        if empresa.iva > 0:
            riesgos.append(Riesgo("FISCAL", "IVA pendiente", 18, empresa.iva, "Regularizacion fiscal preventiva"))
            score += 15

        if empresa.trabajadores_sin_imss > 0:
            riesgos.append(Riesgo("LABORAL", "Trabajadores sin IMSS", 30, empresa.trabajadores_sin_imss*15000, "Alta inmediata IMSS"))
            decisiones.append(Decision("72H", "Regularizar trabajadores IMSS.", "OPERATIVO", 72))
            cascadas.append("Sin IMSS -> inspeccion -> multas -> demanda laboral")
            score += 25

        if empresa.cartera_vencida > ingresos:
            riesgos.append(Riesgo("COBRANZA", "Cartera vencida critica", 25, empresa.cartera_vencida, "Cobranza agresiva"))
            decisiones.append(Decision("72H", "Negociar pagos anticipados con clientes.", "CFO", 48))
            cascadas.append("Cartera vencida -> iliquidez -> incumplimiento operativo")
            score += 20

        if empresa.bloqueo_bancario:
            riesgos.append(Riesgo("BANCARIO", "Bloqueo bancario activo", 40, 1200000, "Desbloqueo legal urgente"))
            decisiones.append(Decision("INMEDIATA", "Abrir canal bancario alterno y negociar desbloqueo.", "CEO + LEGAL", 12))
            cascadas.append("Bloqueo bancario -> paralizacion operativa -> crisis total")
            score += 35

        if empresa.sspc_vencido:
            riesgos.append(Riesgo("REGULATORIO", "Permiso SSPC vencido", 35, 950000, "Renovacion urgente"))
            score += 22

        if empresa.repse_suspendido:
            riesgos.append(Riesgo("REGULATORIO", "REPSE suspendido", 25, 450000, "Regularizacion inmediata"))
            score += 18

        score = min(score, 100)

        if score >= self.umbrales["CRITICO"]:   nivel = "CRITICO"; tendencia = "ASCENDENTE"
        elif score >= self.umbrales["ALTO"]:    nivel = "ALTO";    tendencia = "VOLATIL"
        elif score >= self.umbrales["MEDIO"]:   nivel = "MEDIO";   tendencia = "ESTABLE"
        else:                                   nivel = "BAJO";    tendencia = "CONTROLADA"

        faltantes = sum(1 for x in [ingresos, nomina, gastos, deuda] if x <= 0)
        confianza = max(35, 95 - faltantes * 12)

        escenarios.append(Escenario("Conservador", "Alta", "Controlable", dias_supervivencia, "Estabilizacion preventiva viable."))
        escenarios.append(Escenario("Probable", "Media", "Elevado", max(dias_supervivencia-10,1), "Persisten riesgos fiscales y laborales."))
        if score >= 85:
            escenarios.append(Escenario("Critico", "Alta", "Severo", max(dias_supervivencia-20,1), "Riesgo real de colapso operativo."))

        resultado = ResultadoMotor(
            empresa_id=empresa_id, score=score, nivel=nivel, tendencia=tendencia, confianza=confianza,
            flujo_operativo=flujo_operativo, burn_rate=burn_rate, dias_supervivencia=dias_supervivencia,
            kpis=kpis, alertas=alertas, riesgos=riesgos, escenarios=escenarios, decisiones=decisiones, cascadas=cascadas,
            resumen_ceo=f"MESAN Omega detecta escenario {nivel} con score {score}% y aproximadamente {dias_supervivencia} dias de estabilidad.",
            resumen_cfo=f"Flujo operativo: ${flujo_operativo:,.0f} MXN | Burn rate: ${burn_rate:,.0f} MXN | DSCR: {dscr}",
            resumen_legal="Existen contingencias fiscales, laborales y regulatorias con potencial escalamiento.",
            resumen_operativo="La continuidad depende de flujo, cobranza y estabilizacion financiera inmediata."
        )

        self.historial.append(asdict(resultado))
        logging.info(f"[MESAN] {empresa.nombre} | Nivel={nivel} | Score={score}")
        return resultado

    def stress_test(self):
        resultados = []; errores = []
        casos = [
            EmpresaInput("Empresa Liquidez", ingresos=500000, nomina=600000, gastos=120000, deuda_mensual=90000, isr_retenido=250000, trabajadores=20, trabajadores_sin_imss=5),
            EmpresaInput("Empresa Bloqueada", ingresos=1500000, nomina=800000, gastos=250000, deuda_mensual=200000, bloqueo_bancario=True, cartera_vencida=2500000),
            EmpresaInput("Empresa Sana", ingresos=3000000, nomina=900000, gastos=600000, deuda_mensual=150000)
        ]
        for e in casos:
            try:
                r = self.analizar(e)
                resultados.append({"empresa": e.nombre, "score": r.score, "nivel": r.nivel})
            except Exception as ex:
                errores.append({"empresa": e.nombre, "error": str(ex)})
        return {"ok": True, "version": self.VERSION, "tests": resultados, "errores": errores}
