# ============================================================
# MESAN Omega -- MOTOR AVANZADO DE RIESGO EMPRESARIAL v3.5
# Stress-Test Hardened Edition
# ============================================================

from dataclasses import dataclass
from typing import List, Dict
import re


@dataclass
class ResultadoRiesgo:
    score: int
    nivel: str
    tendencia: str
    confianza: int
    impacto_min: int
    impacto_max: int
    causas: List[str]
    consecuencias: List[str]
    recomendaciones: List[str]
    escenario_30_dias: str
    hallazgo: str
    impacto_operativo: str


class MesanOmegaEngine:

    def __init__(self):

        self.rules = {

            "IMSS": {
                "patterns": [r"\bimss\b", r"sin imss", r"no tienen imss", r"cuotas", r"seguro social"],
                "score": 18,
                "causa": "Posible incumplimiento IMSS",
                "consecuencia": "Contingencias laborales y retroactivos",
                "recomendacion": "Regularizar trabajadores ante IMSS en maximo 72 horas."
            },

            "INFONAVIT": {
                "patterns": [r"\binfonavit\b", r"aportaciones", r"credito vivienda"],
                "score": 16,
                "causa": "Posible incumplimiento Infonavit",
                "consecuencia": "Riesgo de bloqueo o ejecucion administrativa",
                "recomendacion": "Solicitar conciliacion inmediata de adeudos Infonavit."
            },

            "SAT": {
                "patterns": [r"\bsat\b", r"isr", r"iva", r"retenido", r"auditoria fiscal"],
                "score": 20,
                "causa": "Posible riesgo fiscal SAT",
                "consecuencia": "Riesgo de creditos fiscales y multas",
                "recomendacion": "Activar auditoria fiscal preventiva inmediata."
            },

            "REPSE": {
                "patterns": [r"\brepse\b", r"servicios especializados"],
                "score": 22,
                "causa": "Posible incumplimiento REPSE",
                "consecuencia": "Riesgo de cancelacion de contratos",
                "recomendacion": "Iniciar regularizacion REPSE inmediata."
            },

            "SSPC": {
                "patterns": [r"\bsspc\b", r"seguridad privada", r"guardias", r"permiso vencido"],
                "score": 24,
                "causa": "Posible operacion sin permisos SSPC",
                "consecuencia": "Riesgo de clausura operativa",
                "recomendacion": "Priorizar renovacion SSPC urgente."
            },

            "BANCO": {
                "patterns": [r"deuda bancaria", r"credito", r"mora", r"garantias", r"banco"],
                "score": 20,
                "causa": "Presion financiera detectada",
                "consecuencia": "Riesgo de incumplimiento bancario",
                "recomendacion": "Negociar reestructura financiera antes del siguiente vencimiento."
            },

            "NOMINA": {
                "patterns": [r"nomina", r"no alcanza", r"sueldos"],
                "score": 18,
                "causa": "Posible riesgo de incumplimiento en nomina",
                "consecuencia": "Riesgo de conflicto laboral y demandas",
                "recomendacion": "Priorizar flujo para nomina inmediatamente."
            },

            "BLOQUEO": {
                "patterns": [r"bloqueo", r"embargo", r"cuentas congeladas", r"cuentas bloqueadas"],
                "score": 28,
                "causa": "Presion critica sobre liquidez bancaria",
                "consecuencia": "Riesgo de paralizacion operativa inmediata",
                "recomendacion": "Solicitar desbloqueo parcial y acuerdo de pago urgente."
            }
        }

    def analizar(self, texto: str) -> ResultadoRiesgo:

        texto_lower = texto.lower()
        score = 0
        causas = []
        consecuencias = []
        recomendaciones = []

        for regla in self.rules.values():
            detectado = any(re.search(pattern, texto_lower) for pattern in regla["patterns"])
            if detectado:
                score += regla["score"]
                causas.append(regla["causa"])
                consecuencias.append(regla["consecuencia"])
                recomendaciones.append(regla["recomendacion"])

        # Stress test multipliers
        if "sin imss" in texto_lower and "sat" in texto_lower:
            score += 10
        if "bloqueo" in texto_lower and "banco" in texto_lower:
            score += 12
        if "repse" in texto_lower and "sspc" in texto_lower:
            score += 15
        if "huelga" in texto_lower:
            score += 15

        score = min(score, 100)

        if score >= 85:
            nivel = "CRITICO"
            tendencia = "ASCENDENTE"
        elif score >= 60:
            nivel = "ALTO"
            tendencia = "VOLATIL"
        elif score >= 35:
            nivel = "MEDIO"
            tendencia = "ESTABLE"
        else:
            nivel = "BAJO"
            tendencia = "CONTROLADA"

        confianza = min(95, 40 + len(causas) * 8)
        impacto_min = score * 25000
        impacto_max = score * 75000

        recomendaciones_finales = list(dict.fromkeys(recomendaciones))
        if score >= 85:
            recomendaciones_finales.append("Activar comite de crisis ejecutivo con seguimiento diario.")
            recomendaciones_finales.append("Priorizar flujo en nomina, operacion critica e impuestos retenidos.")

        return ResultadoRiesgo(
            score=score, nivel=nivel, tendencia=tendencia, confianza=confianza,
            impacto_min=impacto_min, impacto_max=impacto_max,
            causas=causas, consecuencias=consecuencias,
            recomendaciones=recomendaciones_finales,
            escenario_30_dias="Riesgo critico -- intervencion inmediata requerida." if score >= 85 else "Vigilancia preventiva activa.",
            hallazgo=f"Se detectan {len(causas)} contingencias simultaneas." if causas else "Sin contingencias criticas detectadas.",
            impacto_operativo="Riesgo de interrupcion parcial de operaciones." if score >= 85 else "Operacion bajo monitoreo preventivo."
        )
