# ============================================================
# MESAN Omega -- ANTI-COLLAPSE ENGINE v6.0
# Predictive Corporate Survival Intelligence
# ============================================================

from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime
import uuid


@dataclass
class Riesgo:
    id: str
    categoria: str
    titulo: str
    severidad: int
    probabilidad: float
    impacto_estimado: float
    descripcion: str
    recomendacion: str
    fundamento: str


@dataclass
class Accion:
    prioridad: str
    plazo: str
    accion: str
    objetivo: str
    impacto_esperado: str
    responsable: str


@dataclass
class Escenario:
    nombre: str
    probabilidad: str
    impacto: str
    dias_supervivencia: int
    descripcion: str


@dataclass
class ResultadoMesan:
    empresa_id: str
    fecha: str
    score_global: int
    nivel_riesgo: str
    tendencia: str
    confianza_modelo: int
    flujo_operativo: float
    burn_rate: float
    dias_supervivencia: int
    dscr: float
    riesgos: List[Riesgo]
    acciones: List[Accion]
    escenarios: List[Escenario]
    alertas_criticas: List[str]
    cascadas_detectadas: List[str]
    resumen_ceo: str
    disclaimer: str


class MesanOmegaV6:

    def __init__(self):
        self.version = "6.0"
        self.pesos = {
            "FLUJO_NEGATIVO": 25, "ISR_RETENIDO": 30, "IVA": 10,
            "SIN_IMSS": 20, "CARTERA_CRITICA": 18, "BLOQUEO_BANCARIO": 35,
            "REPSE": 15, "SSPC": 18
        }

    def _nivel_riesgo(self, score):
        if score >= 85: return "CRITICO"
        if score >= 65: return "ALTO"
        if score >= 40: return "MEDIO"
        return "CONTROLADO"

    def _tendencia(self, score):
        if score >= 80: return "ASCENDENTE"
        if score >= 50: return "VOLATIL"
        return "ESTABLE"

    def analizar(self, data: Dict):
        riesgos = []; acciones = []; escenarios = []; alertas = []; cascadas = []
        score = 0

        ingresos = float(data.get("ingresos", 0))
        nomina   = float(data.get("nomina", 0))
        gastos   = float(data.get("gastos", 0))
        deuda    = float(data.get("deuda_mensual", 0))
        iva      = float(data.get("iva", 0))
        isr      = float(data.get("isr_retenido", 0))
        cartera  = float(data.get("cartera_vencida", 0))
        sin_imss = int(data.get("sin_imss", 0))
        bloqueo  = bool(data.get("bloqueo_bancario", False))
        repse    = bool(data.get("repse_suspendido", False))
        sspc     = bool(data.get("sspc_vencido", False))

        burn_rate = nomina + gastos + deuda
        flujo_operativo = ingresos - burn_rate
        dscr = round(ingresos / deuda, 2) if deuda > 0 else 99
        dias_supervivencia = int((ingresos / burn_rate) * 30) if burn_rate > 0 else 365

        if flujo_operativo < 0:
            score += self.pesos["FLUJO_NEGATIVO"]
            riesgos.append(Riesgo(id=str(uuid.uuid4()), categoria="FINANCIERO", titulo="Presion de liquidez", severidad=88, probabilidad=0.92, impacto_estimado=abs(flujo_operativo)*12, descripcion="El flujo operativo negativo sugiere presion estructural de liquidez.", recomendacion="Reducir gasto operativo y acelerar cobranza.", fundamento="Flujo operativo mensual negativo."))
            acciones.append(Accion(prioridad="INMEDIATA", plazo="24H", accion="Suspender gastos no esenciales y priorizar nomina.", objetivo="Reducir salida de efectivo.", impacto_esperado="Estabilizacion parcial de caja.", responsable="CFO"))
            cascadas.append("Flujo negativo -> tension de caja -> riesgo de nomina")

        if isr > 0:
            score += self.pesos["ISR_RETENIDO"]
            riesgos.append(Riesgo(id=str(uuid.uuid4()), categoria="FISCAL", titulo="ISR retenido pendiente", severidad=95, probabilidad=0.90, impacto_estimado=isr*2, descripcion="Se detecta ISR retenido pendiente de regularizacion.", recomendacion="Evaluar convenio preventivo con SAT.", fundamento="ISR retenido reportado por usuario."))
            alertas.append("Posible escalamiento fiscal si existe requerimiento previo.")

        if iva > 0:
            score += self.pesos["IVA"]

        if sin_imss > 0:
            score += self.pesos["SIN_IMSS"]
            riesgos.append(Riesgo(id=str(uuid.uuid4()), categoria="LABORAL", titulo="Trabajadores sin IMSS", severidad=82, probabilidad=0.78, impacto_estimado=sin_imss*15000, descripcion="Existen trabajadores sin alta activa IMSS.", recomendacion="Regularizar altas y validar movimientos afiliatorios.", fundamento="Cantidad de trabajadores sin IMSS reportada."))
            cascadas.append("Sin IMSS -> inspeccion -> cuotas retroactivas")

        if cartera > ingresos and cartera > 0:
            score += self.pesos["CARTERA_CRITICA"]
            cascadas.append("Cartera vencida -> menor liquidez -> presion operativa")

        if bloqueo:
            score += self.pesos["BLOQUEO_BANCARIO"]
            alertas.append("Bloqueo bancario detectado.")
            cascadas.append("Bloqueo bancario -> paralizacion operativa")

        if repse: score += self.pesos["REPSE"]
        if sspc:  score += self.pesos["SSPC"]

        score = min(score, 100)
        nivel    = self._nivel_riesgo(score)
        tendencia = self._tendencia(score)
        faltantes = sum(1 for x in [ingresos, nomina, gastos, deuda] if x <= 0)
        confianza = max(40, 95 - faltantes * 15)

        escenarios.append(Escenario("Conservador", "Alta", "Moderado", dias_supervivencia, "Estabilizacion parcial con acciones preventivas."))
        escenarios.append(Escenario("Probable", "Media", "Elevado", max(dias_supervivencia-10,1), "Persistencia de presion financiera y fiscal."))
        if score >= 85:
            escenarios.append(Escenario("Critico", "Alta", "Severo", max(dias_supervivencia-20,1), "Posible disrupcion operativa multiple."))

        return ResultadoMesan(
            empresa_id=data.get("empresa_id", str(uuid.uuid4())),
            fecha=datetime.now().isoformat(),
            score_global=score, nivel_riesgo=nivel, tendencia=tendencia, confianza_modelo=confianza,
            flujo_operativo=flujo_operativo, burn_rate=burn_rate, dias_supervivencia=dias_supervivencia, dscr=dscr,
            riesgos=riesgos, acciones=acciones, escenarios=escenarios,
            alertas_criticas=alertas, cascadas_detectadas=cascadas,
            resumen_ceo=f"MESAN Omega detecta escenario {nivel} con score {score}%. Aproximadamente {dias_supervivencia} dias de estabilidad operativa.",
            disclaimer="Analisis preventivo automatizado por MESAN Omega Intelligence Engine. No constituye dictamen legal, fiscal ni financiero."
        )
