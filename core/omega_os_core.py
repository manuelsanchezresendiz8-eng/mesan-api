from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class ValidationError(Exception):
    pass

@dataclass
class Evidence:
    factor: str
    source: str
    formula: str
    value: Any
    legal_reference: Optional[str] = None

@dataclass
class Explainability:
    factor: str
    weight: int
    impact: float
    explanation: str
    evidence: List[Evidence] = field(default_factory=list)

@dataclass
class Alert:
    type: str
    severity: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class KPI:
    name: str
    value: str
    status: str

@dataclass
class Risk:
    id: str
    category: str
    severity: int
    title: str
    impact: float
    probability: float
    collapse_window_days: int
    action: str
    explainability: List[Explainability] = field(default_factory=list)

@dataclass
class Scenario:
    name: str
    probability: str
    operational_impact: str
    survival_days: int
    projected_loss: float
    narrative: str

@dataclass
class ExecutiveDecision:
    title: str
    priority: str
    owner: str
    deadline_hours: int
    action: str

@dataclass
class CompanyInput:
    company_id: str
    company_name: str
    sector: str
    ingresos: float
    nomina: float
    gastos: float
    deuda_mensual: float
    cartera_vencida: float = 0
    iva_pendiente: float = 0
    isr_retenido: float = 0
    trabajadores: int = 0
    trabajadores_sin_imss: int = 0
    bloqueo_bancario: bool = False
    repse_suspendido: bool = False
    sspc_vencido: bool = False
    vacaciones_pagadas: bool = False
    vacaciones_adeudadas: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class MesanResult:
    score: int
    level: str
    trend: str
    confidence: int
    survival_days: int
    kpis: List[KPI]
    alerts: List[Alert]
    risks: List[Risk]
    scenarios: List[Scenario]
    executive_decisions: List[ExecutiveDecision]
    operational_cascades: List[str]
    explainability: List[Explainability]
    audit_log: List[Dict]
    ceo_summary: str
    cfo_summary: str
    legal_summary: str
    operational_summary: str

class ValidationEngine:
    @staticmethod
    def validate(company: CompanyInput):
        if company.ingresos < 0: raise ValidationError("Ingresos invalidos.")
        if company.nomina < 0: raise ValidationError("Nomina invalida.")
        if company.gastos < 0: raise ValidationError("Gastos invalidos.")
        if company.deuda_mensual < 0: raise ValidationError("Deuda invalida.")
        if company.vacaciones_pagadas and company.vacaciones_adeudadas:
            raise ValidationError("Conflicto: vacaciones marcadas como pagadas y adeudadas.")
        if company.trabajadores_sin_imss > company.trabajadores:
            raise ValidationError("Trabajadores sin IMSS no puede exceder trabajadores totales.")

class AuditEngine:
    @staticmethod
    def log(event: str, detail: Dict):
        return {"event_id": str(uuid.uuid4()), "event": event, "detail": detail, "timestamp": datetime.now().isoformat()}

class MesanOmegaOS:

    def __init__(self):
        self.audit_log = []

    def analyze(self, company: CompanyInput) -> MesanResult:
        ValidationEngine.validate(company)
        risks=[]; alerts=[]; scenarios=[]; kpis=[]; decisions=[]; cascades=[]; explain=[]
        score = 0

        flujo = company.ingresos - company.nomina - company.gastos - company.deuda_mensual
        burn  = company.nomina + company.gastos + company.deuda_mensual
        survival = int((company.ingresos / burn) * 30) if burn > 0 else 365
        dscr = round(company.ingresos / company.deuda_mensual, 2) if company.deuda_mensual > 0 else 99

        kpis.append(KPI("Flujo Operativo", f"${flujo:,.0f}", "CRITICO" if flujo < 0 else "ESTABLE"))
        kpis.append(KPI("DSCR", str(dscr), "CRITICO" if dscr < 1.2 else "ESTABLE"))
        kpis.append(KPI("Dias Supervivencia", str(survival), "CRITICO" if survival < 30 else "ESTABLE"))

        if flujo < 0:
            imp = abs(flujo) * 12
            score += 30
            ex = Explainability("Flujo Negativo", 30, imp, "Deficit estructural.", [Evidence("Flujo", "Estado financiero", "ingresos-nomina-gastos-deuda", flujo)])
            risks.append(Risk(str(uuid.uuid4()), "FINANCIERO", 35, "Deficit operativo", imp, 0.91, survival, "Reestructura inmediata.", [ex]))
            explain.append(ex)
            alerts.append(Alert("LIQUIDEZ", "CRITICA", "Flujo operativo negativo detectado."))
            cascades.append("Flujo negativo -> Presion nomina -> Riesgo laboral -> Riesgo fiscal")

        if company.isr_retenido > 0:
            imp = company.isr_retenido * 2.2
            score += 35
            ex = Explainability("ISR retenido", 35, imp, "ISR con riesgo SAT.", [Evidence("ISR", "Contabilidad", "ISR x 2.2", company.isr_retenido, "CFF Art. 108")])
            risks.append(Risk(str(uuid.uuid4()), "FISCAL", 40, "ISR retenido", imp, 0.95, 45, "Negociar SAT inmediatamente.", [ex]))
            explain.append(ex)

        if company.trabajadores_sin_imss > 0:
            imp = company.trabajadores_sin_imss * 15000
            score += 25
            ex = Explainability("Sin IMSS", 25, imp, "Exposicion laboral IMSS.", [Evidence("IMSS", "RH", "trabajadores x 15000", company.trabajadores_sin_imss)])
            risks.append(Risk(str(uuid.uuid4()), "LABORAL", 30, "Trabajadores sin IMSS", imp, 0.84, 60, "Regularizacion inmediata IMSS.", [ex]))
            explain.append(ex)
            cascades.append("Sin IMSS -> Inspeccion -> Retroactivos -> Multas")

        if company.bloqueo_bancario:
            score += 35
            alerts.append(Alert("BANCARIO", "CRITICA", "Bloqueo bancario activo."))
            cascades.append("Bloqueo bancario -> Paralizacion operativa -> Riesgo nomina")

        score = min(score, 100)
        if score >= 85:   level = "CRITICO"; trend = "ASCENDENTE"
        elif score >= 65: level = "ALTO";    trend = "VOLATIL"
        elif score >= 40: level = "MEDIO";   trend = "ESTABLE"
        else:             level = "BAJO";    trend = "CONTROLADO"

        missing = sum(1 for x in [company.ingresos, company.nomina, company.gastos, company.deuda_mensual] if x <= 0)
        confidence = max(40, 95 - missing * 15)

        scenarios.append(Scenario("CONSERVADOR", "ALTA", "CONTROLABLE", survival, score*15000, "Estabilizacion posible."))
        scenarios.append(Scenario("PROBABLE", "MEDIA", "ELEVADO", max(survival-15,1), score*35000, "Persisten presiones fiscales."))
        if score >= 85:
            scenarios.append(Scenario("COLAPSO", "ALTA", "SEVERO", max(survival-30,1), score*75000, "Riesgo incumplimiento multiple."))

        decisions.append(ExecutiveDecision("Proteger flujo", "INMEDIATA", "CFO", 24, "Suspender gastos no esenciales."))
        if company.isr_retenido > 0:
            decisions.append(ExecutiveDecision("Negociacion SAT", "24H", "CFO + LEGAL", 24, "Preparar convenio de pago."))
        if company.trabajadores_sin_imss > 0:
            decisions.append(ExecutiveDecision("Regularizacion IMSS", "72H", "OPERATIVO", 72, "Alta inmediata trabajadores."))

        self.audit_log.append(AuditEngine.log("ANALYSIS", {"company": company.company_name, "score": score, "level": level}))

        return MesanResult(
            score=score, level=level, trend=trend, confidence=confidence, survival_days=survival,
            kpis=kpis, alerts=alerts, risks=risks, scenarios=scenarios, executive_decisions=decisions,
            operational_cascades=cascades, explainability=explain, audit_log=self.audit_log,
            ceo_summary=f"MESAN Omega detecta escenario {level} con score {score}% y {survival} dias de estabilidad.",
            cfo_summary=f"Flujo: ${flujo:,.0f} MXN. DSCR: {dscr}.",
            legal_summary="Existen riesgos fiscales y laborales con posible escalamiento regulatorio.",
            operational_summary="La continuidad depende de flujo, cobranza y cumplimiento."
        )
