# ============================================================
# MESAN Omega -- ENTERPRISE OPERATING RISK PLATFORM v5.1
# Multi-Layer Predictive Corporate Intelligence Engine
# ============================================================

from dataclasses import dataclass, field, asdict
from typing import List, Dict
from datetime import datetime


# ============================================================
# DATA MODELS
# ============================================================

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
    dias_supervivencia: int
    impacto: str
    probabilidad: str
    accion_clave: str


@dataclass
class Empresa:
    empresa_id: str
    nombre: str
    sector: str

    ingresos: float
    caja: float = 0

    nomina: float = 0
    gastos: float = 0
    deuda_mensual: float = 0

    cartera_vencida: float = 0

    iva: float = 0
    isr_retenido: float = 0

    trabajadores: int = 0
    trabajadores_sin_imss: int = 0

    repse_suspendido: bool = False
    sspc_vencido: bool = False
    bloqueo_bancario: bool = False

    fecha: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResultadoEnterprise:

    score: int
    health_index: int

    nivel: str
    tendencia: str
    confianza: int

    dias_supervivencia: int

    kpis: List[KPI]
    alertas: List[Alerta]
    riesgos: List[Riesgo]

    cascadas: List[str]
    timeline: List[str]

    escenarios: List[Escenario]

    acciones_hoy: List[str]
    acciones_72h: List[str]
    acciones_7d: List[str]

    prioridades: List[str]

    preguntas_refinamiento: List[str]

    heatmap: Dict[str, int]

    resumen_ceo: str
    resumen_cfo: str
    resumen_legal: str
    resumen_operativo: str


# ============================================================
# ENGINE
# ============================================================

class MesanOmegaEnterprise:

    def __init__(self):
        self.historial = []

    def analizar(self, empresa: Empresa):

        riesgos = []
        alertas = []
        cascadas = []
        escenarios = []
        kpis = []

        acciones_hoy = []
        acciones_72h = []
        acciones_7d = []

        prioridades = []

        timeline = []

        heatmap = {
            "financiero": 0,
            "laboral": 0,
            "fiscal": 0,
            "operativo": 0,
            "regulatorio": 0
        }

        score = 0

        # ====================================================
        # CORE FINANCIALS
        # ====================================================

        burn_rate = (
            empresa.nomina +
            empresa.gastos +
            empresa.deuda_mensual
        )

        flujo_operativo = (
            empresa.ingresos -
            burn_rate
        )

        capital_trabajo = flujo_operativo

        caja = empresa.caja if empresa.caja > 0 else empresa.ingresos

        if burn_rate > 0:
            dias_supervivencia = int((caja / burn_rate) * 30)
        else:
            dias_supervivencia = 365

        dias_supervivencia = max(dias_supervivencia, 1)

        dscr = (
            round(
                empresa.ingresos / empresa.deuda_mensual,
                2
            )
            if empresa.deuda_mensual > 0
            else 99
        )

        # ====================================================
        # KPI ENGINE
        # ====================================================

        kpis.append(
            KPI(
                "Flujo Operativo",
                f"${flujo_operativo:,.0f}",
                "CRITICO" if flujo_operativo < 0 else "ESTABLE"
            )
        )

        kpis.append(
            KPI(
                "DSCR",
                str(dscr),
                "CRITICO" if dscr < 1.2 else "ESTABLE"
            )
        )

        kpis.append(
            KPI(
                "Capital de Trabajo",
                f"${capital_trabajo:,.0f}",
                "CRITICO" if capital_trabajo < 0 else "ESTABLE"
            )
        )

        kpis.append(
            KPI(
                "Dias Supervivencia",
                str(dias_supervivencia),
                "CRITICO" if dias_supervivencia < 30 else "ESTABLE"
            )
        )

        # ====================================================
        # FINANCIAL RISK
        # ====================================================

        if flujo_operativo < 0:

            score += 30
            heatmap["financiero"] += 30

            riesgos.append(
                Riesgo(
                    "FINANCIERO",
                    "Deficit operativo estructural",
                    35,
                    abs(flujo_operativo) * 12,
                    "Reestructura inmediata"
                )
            )

            alertas.append(
                Alerta(
                    "LIQUIDEZ",
                    "CRITICA",
                    "Flujo operativo negativo"
                )
            )

            cascadas.append(
                "Deficit operativo -> deterioro liquidez"
            )

        # ====================================================
        # DSCR
        # ====================================================

        if dscr < 1:

            score += 15
            heatmap["financiero"] += 15

            riesgos.append(
                Riesgo(
                    "FINANCIERO",
                    "Cobertura financiera insuficiente",
                    20,
                    empresa.deuda_mensual * 6,
                    "Renegociacion bancaria inmediata"
                )
            )

            cascadas.append(
                "DSCR menor a 1 -> incapacidad cobertura deuda"
            )

        # ====================================================
        # CARTERA
        # ====================================================

        if empresa.cartera_vencida > empresa.ingresos:

            score += 20
            heatmap["operativo"] += 20

            riesgos.append(
                Riesgo(
                    "COBRANZA",
                    "Cartera vencida critica",
                    25,
                    empresa.cartera_vencida,
                    "Cobranza agresiva"
                )
            )

            cascadas.append(
                "Cartera vencida -> falta de flujo -> riesgo nomina"
            )

        # ====================================================
        # ISR
        # ====================================================

        if empresa.isr_retenido > 0:

            score += 35
            heatmap["fiscal"] += 35

            riesgos.append(
                Riesgo(
                    "FISCAL",
                    "ISR retenido pendiente",
                    35,
                    empresa.isr_retenido * 2,
                    "Negociacion SAT urgente"
                )
            )

            alertas.append(
                Alerta(
                    "SAT",
                    "CRITICA",
                    "ISR retenido detectado"
                )
            )

            prioridades.append(
                "Convenio SAT"
            )

        # ====================================================
        # IVA
        # ====================================================

        if empresa.iva > 0:

            score += 15
            heatmap["fiscal"] += 15

            riesgos.append(
                Riesgo(
                    "FISCAL",
                    "Adeudo IVA",
                    18,
                    empresa.iva,
                    "Regularizacion fiscal"
                )
            )

        # ====================================================
        # IMSS
        # ====================================================

        if empresa.trabajadores_sin_imss > 0:

            score += 25
            heatmap["laboral"] += 25

            riesgos.append(
                Riesgo(
                    "LABORAL",
                    "Trabajadores sin IMSS",
                    30,
                    empresa.trabajadores_sin_imss * 15000,
                    "Alta inmediata IMSS"
                )
            )

            cascadas.append(
                "Sin IMSS -> inspeccion -> retroactivos -> multas"
            )

            prioridades.append(
                "Regularizacion IMSS"
            )

        # ====================================================
        # SSPC
        # ====================================================

        if empresa.sspc_vencido:

            score += 30
            heatmap["regulatorio"] += 30

            riesgos.append(
                Riesgo(
                    "REGULATORIO",
                    "Permiso SSPC vencido",
                    35,
                    950000,
                    "Renovacion SSPC"
                )
            )

            alertas.append(
                Alerta(
                    "REGULATORIA",
                    "ALTA",
                    "Permiso SSPC vencido"
                )
            )

        # ====================================================
        # REPSE
        # ====================================================

        if empresa.repse_suspendido:

            score += 20
            heatmap["regulatorio"] += 20

            riesgos.append(
                Riesgo(
                    "REGULATORIO",
                    "REPSE suspendido",
                    25,
                    450000,
                    "Regularizacion REPSE"
                )
            )

            alertas.append(
                Alerta(
                    "REGULATORIA",
                    "ALTA",
                    "REPSE suspendido"
                )
            )

        # ====================================================
        # BLOQUEO BANCARIO
        # ====================================================

        if empresa.bloqueo_bancario:

            score += 35
            heatmap["financiero"] += 35

            riesgos.append(
                Riesgo(
                    "BANCARIO",
                    "Bloqueo bancario activo",
                    40,
                    1200000,
                    "Desbloqueo legal inmediato"
                )
            )

            alertas.append(
                Alerta(
                    "BANCARIA",
                    "CRITICA",
                    "Bloqueo bancario activo"
                )
            )

            cascadas.append(
                "Bloqueo bancario -> paralizacion operativa"
            )

            prioridades.append(
                "Desbloqueo bancario"
            )

        # ====================================================
        # COLLISION ENGINE
        # ====================================================

        factores_criticos = 0

        if flujo_operativo < 0:
            factores_criticos += 1

        if empresa.cartera_vencida > empresa.ingresos:
            factores_criticos += 1

        if empresa.isr_retenido > 0:
            factores_criticos += 1

        if empresa.trabajadores_sin_imss > 0:
            factores_criticos += 1

        if empresa.bloqueo_bancario:
            factores_criticos += 1

        if factores_criticos >= 4:

            score += 20

            cascadas.append(
                "Colision critica -> insolvencia operativa progresiva"
            )

            alertas.append(
                Alerta(
                    "COLISION",
                    "CRITICA",
                    "Multiples presiones simultaneas detectadas"
                )
            )

        # ====================================================
        # SCORE LIMIT
        # ====================================================

        score = min(score, 100)

        health_index = max(0, 100 - score)

        # ====================================================
        # LEVEL ENGINE
        # ====================================================

        if score >= 85:
            nivel = "CRITICO"
            tendencia = "ASCENDENTE"

        elif score >= 65:
            nivel = "ALTO"
            tendencia = "VOLATIL"

        elif score >= 40:
            nivel = "MEDIO"
            tendencia = "ESTABLE"

        else:
            nivel = "BAJO"
            tendencia = "CONTROLADA"

        # ====================================================
        # CONFIDENCE
        # ====================================================

        campos = [
            empresa.ingresos,
            empresa.nomina,
            empresa.gastos,
            empresa.deuda_mensual
        ]

        faltantes = sum(1 for x in campos if x <= 0)

        confianza = max(
            35,
            95 - (faltantes * 15)
        )

        # ====================================================
        # TIMELINE
        # ====================================================

        timeline = [
            "24H -> Riesgo liquidez",
            "72H -> Presion bancaria",
            "7D -> Riesgo operativo",
            "30D -> Riesgo continuidad"
        ]

        # ====================================================
        # ESCENARIOS
        # ====================================================

        escenarios.append(
            Escenario(
                "Conservador",
                dias_supervivencia,
                "Controlable",
                "Alta",
                "Contencion preventiva"
            )
        )

        escenarios.append(
            Escenario(
                "Probable",
                max(dias_supervivencia - 10, 1),
                "Elevado",
                "Media",
                "Reestructura parcial"
            )
        )

        if score >= 85:

            escenarios.append(
                Escenario(
                    "Critico",
                    max(dias_supervivencia - 20, 1),
                    "Severo",
                    "Alta",
                    "Intervencion inmediata"
                )
            )

        # ====================================================
        # ACTIONS
        # ====================================================

        acciones_hoy = [
            "Priorizar nomina e impuestos retenidos.",
            "Suspender gastos no esenciales.",
            "Activar comite de crisis ejecutivo."
        ]

        acciones_72h = [
            "Negociar SAT y bancos.",
            "Regularizar trabajadores IMSS.",
            "Implementar cobranza intensiva."
        ]

        acciones_7d = [
            "Reestructurar costos fijos.",
            "Renegociar contratos criticos.",
            "Separar cuentas operativas."
        ]

        # ====================================================
        # REFINEMENT QUESTIONS
        # ====================================================

        preguntas = []

        if empresa.isr_retenido > 0:

            preguntas.extend([
                "Ya existe requerimiento formal SAT?",
                "Cuantos meses acumulados existen?"
            ])

        if empresa.cartera_vencida > 0:

            preguntas.extend([
                "Los clientes firmaron reconocimiento de adeudo?",
                "Cual es el aging promedio de cartera?"
            ])

        if empresa.trabajadores_sin_imss > 0:

            preguntas.extend([
                "Existen accidentes laborales recientes?",
                "Hay inspecciones programadas?"
            ])

        # ====================================================
        # EXECUTIVE SUMMARIES
        # ====================================================

        resumen_ceo = (
            f"MESAN Omega detecta escenario {nivel} "
            f"con score {score}%. "
            f"La organizacion presenta "
            f"{dias_supervivencia} dias aproximados "
            f"de estabilidad financiera."
        )

        resumen_cfo = (
            f"Flujo operativo: ${flujo_operativo:,.0f} MXN. "
            f"DSCR: {dscr}. "
            f"Capital de trabajo: "
            f"${capital_trabajo:,.0f} MXN."
        )

        resumen_legal = (
            "Se identifican riesgos fiscales, "
            "laborales y regulatorios "
            "con potencial escalamiento."
        )

        resumen_operativo = (
            "La continuidad operativa depende "
            "de estabilizacion de flujo, "
            "cobranza y cumplimiento regulatorio."
        )

        # ====================================================
        # HISTORIAL
        # ====================================================

        self.historial.append({
            "empresa_id": empresa.empresa_id,
            "fecha": datetime.now().isoformat(),
            "score": score,
            "nivel": nivel
        })

        if len(self.historial) > 5000:
            self.historial.pop(0)

        # ====================================================
        # RETURN
        # ====================================================

        return ResultadoEnterprise(
            score=score,
            health_index=health_index,

            nivel=nivel,
            tendencia=tendencia,
            confianza=confianza,

            dias_supervivencia=dias_supervivencia,

            kpis=kpis,
            alertas=alertas,
            riesgos=riesgos,

            cascadas=cascadas,
            timeline=timeline,

            escenarios=escenarios,

            acciones_hoy=acciones_hoy,
            acciones_72h=acciones_72h,
            acciones_7d=acciones_7d,

            prioridades=prioridades,

            preguntas_refinamiento=preguntas,

            heatmap=heatmap,

            resumen_ceo=resumen_ceo,
            resumen_cfo=resumen_cfo,
            resumen_legal=resumen_legal,
            resumen_operativo=resumen_operativo
        )
