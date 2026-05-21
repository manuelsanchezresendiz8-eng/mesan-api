from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid, json

RULES = {
    "ISR_RETENIDO":   {"weight": 35, "category": "FISCAL",      "severity": 95, "collapse_days": 45, "message": "ISR retenido pendiente.",      "action": "Negociar convenio SAT."},
    "IVA_PENDIENTE":  {"weight": 15, "category": "FISCAL",      "severity": 65, "collapse_days": 90, "message": "IVA pendiente.",               "action": "Regularizacion IVA."},
    "FLUJO_NEGATIVO": {"weight": 30, "category": "FINANCIERO",  "severity": 90, "collapse_days": 30, "message": "Flujo operativo negativo.",    "action": "Reestructura inmediata."},
    "CARTERA_CRITICA":{"weight": 20, "category": "LIQUIDEZ",    "severity": 75, "collapse_days": 35, "message": "Cartera vencida critica.",     "action": "Cobranza intensiva."},
    "SIN_IMSS":       {"weight": 25, "category": "LABORAL",     "severity": 80, "collapse_days": 20, "message": "Trabajadores sin IMSS.",       "action": "Alta inmediata IMSS."},
    "BLOQUEO_BANCARIO":{"weight":35, "category": "CRITICO",     "severity": 99, "collapse_days": 7,  "message": "Bloqueo bancario activo.",     "action": "Desbloqueo legal urgente."},
}

@dataclass
class KPI:
    nombre: str; valor: str; estado: str

@dataclass
class Riesgo:
    codigo: str; categoria: str; descripcion: str; severidad: int; impacto: float; accion: str; dias_colapso: int

@dataclass
class Escenario:
    nombre: str; probabilidad: str; impacto: str; dias_supervivencia: int; descripcion: str

@dataclass
class Explainability:
    factor: str; formula: str; input_value: float; output: float

@dataclass
class Empresa:
    empresa_id: str; nombre: str; sector: str
    ingresos: float; nomina: float; gastos: float; deuda_mensual: float
    cartera_vencida: float; iva: float; isr_retenido: float
    trabajadores: int; trabajadores_sin_imss: int
    bloqueo_bancario: bool = False
    fecha: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ResultadoEnterprise:
    score: int; nivel: str; tendencia: str; confianza: int; dias_supervivencia: int
    kpis: List[KPI]; riesgos: List[Riesgo]; escenarios: List[Escenario]
    explainability: List[Explainability]; cascadas: List[str]
    acciones_24h: List[str]; acciones_72h: List[str]; acciones_7d: List[str]
    resumen_ceo: str; resumen_cfo: str; resumen_legal: str
    audit_id: str; timestamp: str

class MesanOmegaEnterpriseV6:
    VERSION = "6.0"

    def __init__(self):
        self.audit_log = []; self.history = []

    def weighted_score(self, fin, fis, lab, ope):
        return min(round(fin*0.35 + fis*0.30 + lab*0.20 + ope*0.15), 100)

    def analizar(self, empresa: Empresa):
        riesgos=[]; kpis=[]; escenarios=[]; explain=[]; cascadas=[]
        fin=0; fis=0; lab=0; ope=0

        flujo = empresa.ingresos - empresa.nomina - empresa.gastos - empresa.deuda_mensual
        burn  = empresa.nomina + empresa.gastos + empresa.deuda_mensual
        dias  = int((empresa.ingresos / burn) * 30) if burn > 0 else 365
        dscr  = round(empresa.ingresos / empresa.deuda_mensual, 2) if empresa.deuda_mensual > 0 else 99

        kpis.append(KPI("Flujo Operativo", f"${flujo:,.0f}", "CRITICO" if flujo < 0 else "ESTABLE"))
        kpis.append(KPI("DSCR", str(dscr), "CRITICO" if dscr < 1.2 else "ESTABLE"))

        if flujo < 0:
            imp = abs(flujo) * 12; fin += RULES["FLUJO_NEGATIVO"]["weight"]
            riesgos.append(Riesgo("FLUJO_NEGATIVO", "FINANCIERO", RULES["FLUJO_NEGATIVO"]["message"], 90, imp, RULES["FLUJO_NEGATIVO"]["action"], 30))
            explain.append(Explainability("FLUJO_NEGATIVO", "abs(flujo)*12", flujo, imp))
            cascadas.append("Flujo negativo -> presion nomina -> riesgo laboral")

        if empresa.isr_retenido > 0:
            imp = empresa.isr_retenido * 2.2; fis += RULES["ISR_RETENIDO"]["weight"]
            riesgos.append(Riesgo("ISR_RETENIDO", "FISCAL", RULES["ISR_RETENIDO"]["message"], 95, imp, RULES["ISR_RETENIDO"]["action"], 45))
            explain.append(Explainability("ISR_RETENIDO", "isr*2.2", empresa.isr_retenido, imp))
            cascadas.append("ISR retenido -> requerimiento SAT -> embargo")

        if empresa.iva > 0:
            fis += RULES["IVA_PENDIENTE"]["weight"]
            riesgos.append(Riesgo("IVA_PENDIENTE", "FISCAL", RULES["IVA_PENDIENTE"]["message"], 65, empresa.iva, RULES["IVA_PENDIENTE"]["action"], 90))

        if empresa.cartera_vencida > empresa.ingresos:
            fin += RULES["CARTERA_CRITICA"]["weight"]
            riesgos.append(Riesgo("CARTERA_CRITICA", "LIQUIDEZ", RULES["CARTERA_CRITICA"]["message"], 75, empresa.cartera_vencida, RULES["CARTERA_CRITICA"]["action"], 35))
            cascadas.append("Cartera vencida -> falta de flujo -> riesgo operativo")

        if empresa.trabajadores_sin_imss > 0:
            imp = empresa.trabajadores_sin_imss * 15000; lab += RULES["SIN_IMSS"]["weight"]
            riesgos.append(Riesgo("SIN_IMSS", "LABORAL", RULES["SIN_IMSS"]["message"], 80, imp, RULES["SIN_IMSS"]["action"], 20))
            cascadas.append("Sin IMSS -> inspeccion -> multas")

        if empresa.bloqueo_bancario:
            ope += RULES["BLOQUEO_BANCARIO"]["weight"]
            riesgos.append(Riesgo("BLOQUEO_BANCARIO", "CRITICO", RULES["BLOQUEO_BANCARIO"]["message"], 99, 1200000, RULES["BLOQUEO_BANCARIO"]["action"], 7))
            cascadas.append("Bloqueo bancario -> paralizacion")

        score = self.weighted_score(fin, fis, lab, ope)
        if score >= 85:   nivel = "CRITICO"; tendencia = "ASCENDENTE"
        elif score >= 65: nivel = "ALTO";    tendencia = "VOLATIL"
        elif score >= 40: nivel = "MEDIO";   tendencia = "ESTABLE"
        else:             nivel = "BAJO";    tendencia = "CONTROLADA"

        campos_validos = sum(1 for x in [empresa.ingresos, empresa.nomina, empresa.gastos, empresa.deuda_mensual, empresa.iva, empresa.isr_retenido] if x is not None)
        confianza = round(max(35, (campos_validos / 6) * 100))

        escenarios.append(Escenario("Conservador", "Alta", "Controlable", dias, "Contencion preventiva."))
        escenarios.append(Escenario("Probable", "Media", "Elevado", max(dias-10,1), "Persistencia de presiones."))
        if score >= 85:
            escenarios.append(Escenario("Critico", "Alta", "Severo", max(dias-20,1), "Riesgo incumplimiento multiple."))

        audit_id = str(uuid.uuid4())
        self.audit_log.append({"audit_id": audit_id, "empresa_id": empresa.empresa_id, "score": score, "version": self.VERSION, "timestamp": datetime.now().isoformat()})
        self.history.append({"empresa_id": empresa.empresa_id, "score": score, "nivel": nivel, "fecha": datetime.now().isoformat()})

        return ResultadoEnterprise(
            score=score, nivel=nivel, tendencia=tendencia, confianza=confianza, dias_supervivencia=dias,
            kpis=kpis, riesgos=riesgos, escenarios=escenarios, explainability=explain, cascadas=cascadas,
            acciones_24h=["Priorizar nomina y flujo critico.", "Suspender gastos no esenciales.", "Activar comite de crisis."],
            acciones_72h=["Negociar SAT y bancos.", "Regularizar IMSS.", "Acelerar cobranza."],
            acciones_7d=["Reestructurar costos fijos.", "Revisar contratos criticos."],
            resumen_ceo=f"MESAN Omega detecta escenario {nivel} con score {score}%.",
            resumen_cfo=f"Flujo operativo: ${flujo:,.0f} MXN.",
            resumen_legal="Existen riesgos potenciales fiscales, laborales y operativos.",
            audit_id=audit_id, timestamp=datetime.now().isoformat()
        )
