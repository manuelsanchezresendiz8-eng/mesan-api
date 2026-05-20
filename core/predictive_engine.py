# ============================================================
# MESAN Omega -- PREDICTIVE DEFENSE ENGINE v4.1
# Survival Intelligence + Cascade Analysis
# ============================================================

from dataclasses import dataclass, field
from typing import List, Dict


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class RiesgoDetectado:
    nombre: str
    severidad: int
    categoria: str
    impacto_estimado: int
    accion_critica: str


@dataclass
class Escenario:
    nombre: str
    probabilidad: str
    impacto: str
    dias_supervivencia: int
    descripcion: str


@dataclass
class ResultadoMesan:
    score: int
    nivel: str
    tendencia: str
    confianza: int
    dias_supervivencia: int

    riesgos: List[RiesgoDetectado] = field(default_factory=list)
    cascadas: List[str] = field(default_factory=list)
    escenarios: List[Escenario] = field(default_factory=list)

    acciones_hoy: List[str] = field(default_factory=list)
    acciones_72h: List[str] = field(default_factory=list)
    acciones_7d: List[str] = field(default_factory=list)

    resumen_ejecutivo: str = ""


# ============================================================
# ENGINE
# ============================================================

class MesanOmegaPredictiveEngine:

    def __init__(self):

        self.pesos = {
            "ISR_RETENIDO": 35,
            "NOMINA": 35,
            "IMSS": 30,
            "SSPC": 30,
            "REPSE": 25,
            "BLOQUEO": 35,
            "SAT": 25,
            "BANCO": 20,
            "CARTERA": 20,
            "HUELGA": 35,
            "RC": 15
        }

    # ========================================================
    # ANALISIS PRINCIPAL
    # ========================================================

    def analizar(self, data: Dict):

        score = 0
        riesgos = []
        cascadas = []

        ingresos = float(data.get("ingresos", 0) or 0)
        nomina = float(data.get("nomina", 0) or 0)
        gastos = float(data.get("gastos", 0) or 0)
        deuda = float(data.get("deuda_mensual", 0) or 0)

        cartera = float(data.get("cartera_vencida", 0) or 0)
        isr = float(data.get("isr_retenido", 0) or 0)
        iva = float(data.get("iva", 0) or 0)

        caja = float(data.get("caja", ingresos) or ingresos)

        sin_imss = int(data.get("sin_imss", 0) or 0)

        bloqueo_bancario = data.get("bloqueo_bancario", False)
        sspc_vencido = data.get("sspc_vencido", False)

        # ====================================================
        # METRICAS FINANCIERAS
        # ====================================================

        burn_rate = nomina + gastos + deuda

        flujo_libre = ingresos - burn_rate

        if deuda > 0:
            dscr = ingresos / deuda
        else:
            dscr = 10

        # ====================================================
        # DIAS SUPERVIVENCIA
        # ====================================================

        if burn_rate <= 0:
            dias_supervivencia = 120
        else:
            dias_supervivencia = int((caja / burn_rate) * 30)

        dias_supervivencia = max(dias_supervivencia, 1)

        # ====================================================
        # RIESGO FLUJO
        # ====================================================

        if flujo_libre < 0:

            impacto = abs(int(flujo_libre * 12))

            riesgos.append(
                RiesgoDetectado(
                    nombre="Presion critica de flujo",
                    severidad=35,
                    categoria="FINANCIERO",
                    impacto_estimado=impacto,
                    accion_critica="Reestructura inmediata"
                )
            )

            score += 35

        # ====================================================
        # DSCR
        # ====================================================

        if dscr < 1:

            score += 15

            cascadas.append(
                "DSCR menor a 1 -> incapacidad de cobertura financiera"
            )

        # ====================================================
        # ISR
        # ====================================================

        if isr > 0:

            riesgos.append(
                RiesgoDetectado(
                    nombre="ISR retenido pendiente",
                    severidad=35,
                    categoria="FISCAL",
                    impacto_estimado=int(isr * 2),
                    accion_critica="Negociar SAT inmediatamente"
                )
            )

            score += 35

        # ====================================================
        # IVA
        # ====================================================

        if iva > 0:

            riesgos.append(
                RiesgoDetectado(
                    nombre="Adeudo IVA",
                    severidad=18,
                    categoria="FISCAL",
                    impacto_estimado=int(iva),
                    accion_critica="Plan de regularizacion"
                )
            )

            score += 18

        # ====================================================
        # CARTERA
        # ====================================================

        if cartera > ingresos:

            riesgos.append(
                RiesgoDetectado(
                    nombre="Cartera vencida critica",
                    severidad=25,
                    categoria="LIQUIDEZ",
                    impacto_estimado=int(cartera),
                    accion_critica="Cobranza agresiva"
                )
            )

            score += 25

            cascadas.append(
                "Cartera vencida -> falta de flujo -> presion nomina -> riesgo laboral"
            )

        # ====================================================
        # IMSS
        # ====================================================

        if sin_imss > 0:

            riesgos.append(
                RiesgoDetectado(
                    nombre="Trabajadores sin IMSS",
                    severidad=30,
                    categoria="LABORAL",
                    impacto_estimado=sin_imss * 15000,
                    accion_critica="Alta inmediata IMSS"
                )
            )

            score += 30

            cascadas.append(
                "Sin IMSS -> inspeccion -> retroactivos -> multas"
            )

        # ====================================================
        # SSPC
        # ====================================================

        if sspc_vencido:

            riesgos.append(
                RiesgoDetectado(
                    nombre="Permiso SSPC vencido",
                    severidad=30,
                    categoria="REGULATORIO",
                    impacto_estimado=750000,
                    accion_critica="Renovacion urgente SSPC"
                )
            )

            score += 30

        # ====================================================
        # BLOQUEO BANCARIO
        # ====================================================

        if bloqueo_bancario:

            riesgos.append(
                RiesgoDetectado(
                    nombre="Bloqueo bancario",
                    severidad=35,
                    categoria="CRITICO",
                    impacto_estimado=1200000,
                    accion_critica="Desbloqueo legal inmediato"
                )
            )

            score += 35

            cascadas.append(
                "Bloqueo bancario -> paralizacion operativa -> incumplimiento en cadena"
            )

        # ====================================================
        # COLISIONES CRITICAS
        # ====================================================

        factores_criticos = 0

        if isr > 0:
            factores_criticos += 1

        if cartera > ingresos:
            factores_criticos += 1

        if sin_imss > 0:
            factores_criticos += 1

        if bloqueo_bancario:
            factores_criticos += 1

        if flujo_libre < 0:
            factores_criticos += 1

        if factores_criticos >= 4:

            score += 20

            cascadas.append(
                "Colision critica detectada -> insolvencia operativa progresiva"
            )

        # ====================================================
        # ENGINE DE COLAPSO EN CADENA
        # ====================================================

        if bloqueo_bancario and isr > 0 and sin_imss > 0:

            cascadas.append(
                "Embargo SAT -> bloqueo bancario -> incumplimiento nomina -> demanda laboral -> perdida operativa"
            )

            score += 10

        if cartera > ingresos and flujo_libre < 0:

            cascadas.append(
                "Cartera vencida -> agotamiento caja -> uso credito -> presion bancaria"
            )

            score += 8

        if dscr < 1 and bloqueo_bancario:

            cascadas.append(
                "Incapacidad cobertura financiera -> riesgo ejecucion garantias"
            )

            score += 10

        # ====================================================
        # NORMALIZACION SCORE
        # ====================================================

        score = min(score, 100)

        # ====================================================
        # CLASIFICACION
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
        # CONFIANZA
        # ====================================================

        campos = [ingresos, nomina, gastos, deuda]

        faltantes = sum(1 for x in campos if x <= 0)

        confianza = max(35, 95 - (faltantes * 15))

        # ====================================================
        # ESCENARIOS
        # ====================================================

        escenarios = [

            Escenario(
                nombre="Conservador",
                probabilidad="Alta",
                impacto="Controlable",
                dias_supervivencia=dias_supervivencia,
                descripcion="Estabilizacion con acciones preventivas."
            ),

            Escenario(
                nombre="Probable",
                probabilidad="Media",
                impacto="Elevado",
                dias_supervivencia=max(dias_supervivencia - 10, 1),
                descripcion="Presiones operativas y fiscales persistentes."
            )
        ]

        if score >= 85:

            escenarios.append(

                Escenario(
                    nombre="Critico",
                    probabilidad="Alta",
                    impacto="Severo",
                    dias_supervivencia=max(dias_supervivencia - 20, 1),
                    descripcion="Riesgo real de incumplimiento multiple."
                )
            )

        # ====================================================
        # ACCIONES
        # ====================================================

        acciones_hoy = [
            "Priorizar flujo para nomina, impuestos retenidos y operacion critica."
        ]

        if cartera > 0:

            acciones_hoy.append(
                "Activar cobranza intensiva y contacto directo con clientes morosos."
            )

        if bloqueo_bancario:

            acciones_hoy.append(
                "Solicitar desbloqueo parcial bancario con estrategia legal."
            )

        if sin_imss > 0:

            acciones_hoy.append(
                "Regularizar trabajadores IMSS antes de inspeccion o incidente laboral."
            )

        acciones_72h = [
            "Negociar prorrogas bancarias antes de vencimientos.",
            "Activar auditoria fiscal preventiva.",
            "Reestructurar flujo operativo prioritario."
        ]

        acciones_7d = [
            "Reducir costos fijos no esenciales.",
            "Implementar comite ejecutivo de crisis.",
            "Reestructurar pasivos financieros."
        ]

        # ====================================================
        # RESUMEN
        # ====================================================

        resumen = (
            f"MESAN Omega detecta escenario {nivel} "
            f"con score {score}%. "
            f"Aproximadamente {dias_supervivencia} dias "
            f"de estabilidad financiera. "
            f"Flujo operativo estimado: "
            f"${flujo_libre:,.0f} MXN."
        )

        # ====================================================
        # RESULTADO
        # ====================================================

        return ResultadoMesan(
            score=score,
            nivel=nivel,
            tendencia=tendencia,
            confianza=confianza,
            dias_supervivencia=dias_supervivencia,

            riesgos=riesgos,
            cascadas=cascadas,
            escenarios=escenarios,

            acciones_hoy=acciones_hoy,
            acciones_72h=acciones_72h,
            acciones_7d=acciones_7d,

            resumen_ejecutivo=resumen
        )
      
