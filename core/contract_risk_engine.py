# ============================================================
# MESAN Omega -- CONTRACT RISK ENGINE v4.0
# Contract Intelligence + Legal Exposure Mapping
# ============================================================

from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime


@dataclass
class FundamentoCalculo:
    descripcion: str
    formula: str
    resultado: float
    detalles: Dict = field(default_factory=dict)


@dataclass
class EscenarioLegal:
    nombre: str
    probabilidad: str
    exposicion: float
    descripcion: str


@dataclass
class ResultadoContractual:
    ok: bool
    nivel_riesgo: str
    confianza_legal: str
    exposicion_min: float
    exposicion_probable: float
    exposicion_max: float
    fundamentos: List[FundamentoCalculo]
    escenarios: List[EscenarioLegal]
    acciones_24h: List[str]
    acciones_72h: List[str]
    acciones_semana1: List[str]
    observaciones: List[str]
    resumen_ejecutivo: str
    disclaimer: str
    fecha_generacion: str


class ContractRiskEngine:

    def analizar(self, data: Dict):

        fundamentos = []; escenarios = []; observaciones = []

        mensualidad          = float(data.get("mensualidad", 0))
        meses_restantes      = int(data.get("meses_restantes", 0))
        penalizacion_pct     = float(data.get("penalizacion_pct", 0))
        costos_legales       = float(data.get("costos_legales", 85000))
        contrato_firmado     = data.get("contrato_firmado", False)
        clausula_penalizacion = data.get("clausula_penalizacion", False)
        evidencia_servicio   = data.get("evidencia_servicio", False)
        cancelacion_escrita  = data.get("cancelacion_escrita", False)

        if mensualidad <= 0:
            return ResultadoContractual(
                ok=False, nivel_riesgo="INDETERMINADO", confianza_legal="BAJA",
                exposicion_min=0, exposicion_probable=0, exposicion_max=0,
                fundamentos=[], escenarios=[], acciones_24h=[], acciones_72h=[], acciones_semana1=[],
                observaciones=["No existe mensualidad valida para calcular exposicion contractual."],
                resumen_ejecutivo="No fue posible generar estimacion contractual.",
                disclaimer="Estimacion automatizada preventiva.",
                fecha_generacion=datetime.now().isoformat()
            )

        contrato_restante = mensualidad * meses_restantes
        fundamentos.append(FundamentoCalculo("Monto pendiente del contrato no ejecutado.", "mensualidad * meses_restantes", round(contrato_restante, 2), {"mensualidad": mensualidad, "meses_restantes": meses_restantes}))

        penalizacion = 0
        if clausula_penalizacion:
            penalizacion = contrato_restante * penalizacion_pct
            fundamentos.append(FundamentoCalculo("Penalizacion segun clausula contractual.", "saldo_restante * porcentaje", round(penalizacion, 2), {"saldo_restante": contrato_restante, "porcentaje": penalizacion_pct}))
        else:
            observaciones.append("No existe clausula de penalizacion confirmada documentalmente.")

        fundamentos.append(FundamentoCalculo("Estimacion preventiva de costos legales.", "estimacion parametrica", round(costos_legales, 2), {"metodologia": "estimacion preventiva"}))

        exposicion_total = contrato_restante + penalizacion + costos_legales
        fundamentos.append(FundamentoCalculo("Exposicion contractual total estimada.", "contrato_restante + penalizacion + costos_legales", round(exposicion_total, 2)))

        score_confianza = sum([contrato_firmado*35, clausula_penalizacion*25, evidencia_servicio*20, cancelacion_escrita*20])
        confianza_legal = "ALTA" if score_confianza >= 80 else "MEDIA" if score_confianza >= 50 else "BAJA"

        if exposicion_total >= 2000000: nivel_riesgo = "CRITICO"
        elif exposicion_total >= 750000: nivel_riesgo = "ALTO"
        elif exposicion_total >= 250000: nivel_riesgo = "MEDIO"
        else: nivel_riesgo = "BAJO"

        escenarios = [
            EscenarioLegal("Conservador", "ALTA", round(costos_legales, 2), "Negociacion temprana sin litigio prolongado."),
            EscenarioLegal("Probable", "MEDIA", round(contrato_restante * 0.50, 2), "Acuerdo parcial o negociacion contractual."),
            EscenarioLegal("Critico", "MEDIA", round(exposicion_total, 2), "Litigio mercantil con reclamacion integral.")
        ]

        observaciones += [
            "La procedencia de indemnizacion dependera de clausulas reales y evidencia documental.",
            "La cancelacion unilateral no implica automaticamente responsabilidad exigible.",
            "La determinacion final dependera de negociacion, convenio o resolucion judicial."
        ]

        return ResultadoContractual(
            ok=True, nivel_riesgo=nivel_riesgo, confianza_legal=confianza_legal,
            exposicion_min=round(costos_legales, 2),
            exposicion_probable=round(contrato_restante * 0.50, 2),
            exposicion_max=round(exposicion_total, 2),
            fundamentos=fundamentos, escenarios=escenarios,
            acciones_24h=["Enviar notificacion formal de desacuerdo contractual.", "Resguardar contrato, anexos y comunicaciones.", "Documentar evidencia de cumplimiento del servicio."],
            acciones_72h=["Solicitar revision legal mercantil especializada.", "Calcular exposicion contractual real conforme a clausulas."],
            acciones_semana1=["Intentar negociacion estructurada antes de litigio.", "Evaluar convenio economico o ajuste de alcance contractual."],
            observaciones=observaciones,
            resumen_ejecutivo=f"MESAN Omega detecta escenario {nivel_riesgo} con exposicion estimada de ${exposicion_total:,.0f} MXN. Confianza legal: {confianza_legal}.",
            disclaimer="Analisis preventivo automatizado por MESAN Omega. No constituye dictamen legal definitivo.",
            fecha_generacion=datetime.now().isoformat()
        )
