# services/continuity_engine.py -- MESAN Omega Continuity Engine v3.2
"""
Continuity Engine v3.2 — Sprint 1 Final

Cambios v3.2:
- Key Person Risk corregido: mide dependencia operacional real (ratio críticos/no-críticos)
- Demandas laborales proporcionales al tamaño de empresa (litigation_ratio)
- risk_breakdown por dominio: financiero, laboral, regulatorio, operativo
- score_version: trazabilidad y auditoría histórica
- generated_at: timestamp UTC en cada resultado
- calcular_esi() como método oficial; calcular_continuity_score() delega a él

Cambios v3.1:
- Demandas laborales incorporadas al ESI-Ω
- Key Person Risk básico
- Drivers explicativos
- Trend reservado para Sprint posterior

Cambios v3.0:
- continuity_score evoluciona a enterprise_survival_index (ESI-Ω)
- Clasificación alineada: ROBUSTA/ESTABLE/VIGILANCIA/RIESGO_ELEVADO/CRITICA
- Continuity Horizon determinístico 12/24/36 meses
- Recomendaciones War Room
- founder_dependency y revenue_concentration preparadas en dataclass
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


# ══════════════════════════════════════════════════════════════════════════════
# DATACLASS EMPRESA
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Empresa:
    nombre:                  str
    ingresos_mensuales:      float
    nomina_mensual:          float
    empleados:               int
    empleados_criticos:      int
    caja_disponible:         float
    deuda_mensual:           float
    demandas_laborales:      int
    trabajadores_sin_imss:   int
    rotacion_anual:          float
    severance_estimado:      float
    riesgo_sat:              str
    riesgo_imss:             str
    repse_suspendido:        bool

    # Variables estratégicas futuras (Sprint 3) — opcionales, sin efecto aún
    founder_dependency:      Optional[float] = None  # 0-100: 0=totalmente dependiente
    revenue_concentration:   Optional[float] = None  # % del cliente principal (0-100)


# ══════════════════════════════════════════════════════════════════════════════
# CONTINUITY ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class ContinuityEngine:
    """
    Motor principal del Enterprise Survival Index Ω (ESI-Ω).

    Calcula el índice de sostenibilidad empresarial basado en
    factores financieros, laborales y regulatorios reales.

    Salida principal: enterprise_survival_index (ESI-Ω)
    Compatibilidad: continuity_score (alias temporal)
    """

    # ── Métricas base ─────────────────────────────────────────────────────────

    def calcular_dscr(self, ingresos: float, deuda: float) -> float:
        """Debt Service Coverage Ratio — capacidad de cubrir deuda con ingresos."""
        if deuda <= 0:
            return 10.0
        return round(ingresos / deuda, 2)

    def calcular_burn_rate(self, ingresos: float, gastos: float) -> float:
        """Porcentaje de ingresos consumido por gastos operativos."""
        if ingresos <= 0:
            return 100.0
        return round((gastos / ingresos) * 100, 2)

    def calcular_severance_pressure(self, caja: float, severance: float) -> float:
        """Presión de liquidación sobre caja disponible."""
        if caja <= 0:
            return 100.0
        return round((severance / caja) * 100, 2)

    def calcular_workforce_risk(
        self,
        empleados: int,
        sin_imss:  int,
        rotacion:  float,
    ) -> float:
        """Riesgo laboral combinado: exposición IMSS + rotación."""
        if empleados <= 0:
            return 100.0
        score = (
            ((sin_imss / empleados) * 50) +
            ((rotacion / 100) * 50)
        )
        return round(min(score, 100), 2)

    def calcular_key_person_risk(
        self,
        empleados:          int,
        empleados_criticos: int,
    ) -> float:
        """
        Key Person Risk v3.2 — mide dependencia operacional real.

        Usa ratio críticos / no-críticos en lugar de críticos / total.
        Esto evita penalizar empresas pequeñas altamente especializadas.

        Ejemplos:
            5 empleados, 3 críticos → ratio = 3/2 = 1.5 → riesgo alto
            50 empleados, 3 críticos → ratio = 3/47 = 0.06 → riesgo bajo
            100 empleados, 50 críticos → ratio = 50/50 = 1.0 → riesgo elevado
        """
        no_criticos = max(1, empleados - empleados_criticos)
        ratio = empleados_criticos / no_criticos
        return round(min(ratio, 3.0), 4)   # cap en 3.0 para normalizar

    def calcular_litigation_ratio(
        self,
        demandas:  int,
        empleados: int,
    ) -> float:
        """
        Litigation Ratio — demandas proporcionales al tamaño de empresa.

        1 demanda en empresa de 5 empleados es más grave que
        1 demanda en empresa de 500 empleados.
        """
        if empleados <= 0:
            return 1.0
        return round(demandas / empleados, 4)

    # ── Clasificación ESI-Ω (estándar MESAN Ω) ───────────────────────────────

    def clasificar(self, esi: int) -> str:
        """
        Clasificación estándar MESAN Ω.
        Alineada con EnterpriseSurvivalEngine y ObservabilityBus.

        90-100 → ROBUSTA
        80-89  → ESTABLE
        70-79  → VIGILANCIA
        60-69  → RIESGO_ELEVADO
        0-59   → CRITICA
        """
        if esi >= 90:
            return "ROBUSTA"
        if esi >= 80:
            return "ESTABLE"
        if esi >= 70:
            return "VIGILANCIA"
        if esi >= 60:
            return "RIESGO_ELEVADO"
        return "CRITICA"

    # ── Recomendaciones War Room ──────────────────────────────────────────────

    def generar_recomendacion(self, clasificacion: str) -> str:
        """
        Recomendaciones ejecutivas orientadas a acción inmediata.
        Lenguaje War Room — no genérico.
        """
        recomendaciones = {
            "ROBUSTA":        "Escalar crecimiento sin aumentar exposición.",
            "ESTABLE":        "Proteger liquidez y fortalecer resiliencia.",
            "VIGILANCIA":     "Reducir concentración de riesgo operativo.",
            "RIESGO_ELEVADO": "Ejecutar contención financiera inmediata.",
            "CRITICA":        "Activar protocolo de supervivencia empresarial.",
        }
        return recomendaciones.get(clasificacion, "Activar protocolo de supervivencia empresarial.")

    # ── Continuity Horizon ────────────────────────────────────────────────────

    def calcular_horizon(self, esi: int) -> dict:
        """
        Proyección determinística del ESI-Ω a 12, 24 y 36 meses.

        12m = min(100, ESI + 10) — ventana de reacción disponible
        24m = ESI                — condiciones actuales sin cambios
        36m = max(0, ESI - 10)  — erosión natural sin intervención
        """
        return {
            "12_months": min(100, esi + 10),
            "24_months": esi,
            "36_months": max(0,   esi - 10),
        }

    # ── Cálculo principal ESI-Ω ───────────────────────────────────────────────

    def calcular_esi(self, empresa: Empresa) -> dict:
        """
        API oficial v3.2 — Enterprise Survival Index Ω.
        Contiene toda la lógica de cálculo.
        calcular_continuity_score() es alias legacy que delega aquí.

        La respuesta incluye:
            enterprise_survival_index  ← nombre principal
            esi                        ← alias corto
            continuity_score           ← alias de compatibilidad temporal
        """
        # ── Métricas base ──────────────────────────────────────────────────
        dscr = self.calcular_dscr(
            empresa.ingresos_mensuales,
            empresa.deuda_mensual,
        )
        burn_rate = self.calcular_burn_rate(
            empresa.ingresos_mensuales,
            empresa.nomina_mensual + empresa.deuda_mensual,
        )
        severance_pressure = self.calcular_severance_pressure(
            empresa.caja_disponible,
            empresa.severance_estimado,
        )
        workforce_risk = self.calcular_workforce_risk(
            empresa.empleados,
            empresa.trabajadores_sin_imss,
            empresa.rotacion_anual,
        )
        key_person_risk   = self.calcular_key_person_risk(
            empresa.empleados,
            empresa.empleados_criticos,
        )
        litigation_ratio  = self.calcular_litigation_ratio(
            empresa.demandas_laborales,
            empresa.empleados,
        )

        # ── Score base con risk_breakdown por dominio ───────────────────────
        score   = 100
        drivers: List[str] = []

        # Contadores por dominio para risk_breakdown
        penalizacion_financiero  = 0
        penalizacion_laboral     = 0
        penalizacion_regulatorio = 0
        penalizacion_operativo   = 0

        # ── DOMINIO FINANCIERO ─────────────────────────────────────────────
        if dscr < 1.0:
            p = 30; score -= p; penalizacion_financiero += p
            drivers.append("DSCR menor a 1.0 — flujo insuficiente para cubrir deuda")
        elif dscr < 1.5:
            p = 15; score -= p; penalizacion_financiero += p
            drivers.append("DSCR menor a 1.5")

        if burn_rate > 80:
            p = 20; score -= p; penalizacion_financiero += p
            drivers.append("Burn Rate superior a 80%")
        elif burn_rate > 60:
            p = 10; score -= p; penalizacion_financiero += p
            drivers.append("Burn Rate superior a 60%")

        if severance_pressure > 70:
            p = 20; score -= p; penalizacion_financiero += p
            drivers.append("Presión de severance crítica sobre caja (>70%)")
        elif severance_pressure > 40:
            p = 10; score -= p; penalizacion_financiero += p
            drivers.append("Presión de severance elevada sobre caja (>40%)")

        # ── DOMINIO LABORAL ────────────────────────────────────────────────
        if workforce_risk > 70:
            p = 20; score -= p; penalizacion_laboral += p
            drivers.append("Riesgo laboral crítico — alta exposición IMSS y rotación")
        elif workforce_risk > 40:
            p = 10; score -= p; penalizacion_laboral += p
            drivers.append("Riesgo laboral elevado")

        # Demandas proporcionales al tamaño (litigation_ratio)
        if litigation_ratio >= 0.20:
            p = 20; score -= p; penalizacion_laboral += p
            drivers.append(f"Litigiosidad crítica ({litigation_ratio:.1%} de empleados demandantes)")
        elif litigation_ratio >= 0.10:
            p = 10; score -= p; penalizacion_laboral += p
            drivers.append(f"Litigiosidad elevada ({litigation_ratio:.1%})")
        elif litigation_ratio >= 0.05:
            p = 5; score -= p; penalizacion_laboral += p
            drivers.append("Demandas laborales activas")

        # Key Person Risk — ratio críticos/no-críticos
        if key_person_risk >= 1.0:
            p = 10; score -= p; penalizacion_laboral += p
            drivers.append(f"Alta dependencia de personal crítico (ratio {key_person_risk:.2f})")
        elif key_person_risk >= 0.5:
            p = 5; score -= p; penalizacion_laboral += p
            drivers.append(f"Dependencia moderada de personal crítico (ratio {key_person_risk:.2f})")

        # ── DOMINIO REGULATORIO ────────────────────────────────────────────
        if empresa.riesgo_sat.upper() == "NEGATIVO":
            p = 15; score -= p; penalizacion_regulatorio += p
            drivers.append("Riesgo SAT negativo")

        if empresa.riesgo_imss.upper() == "NEGATIVO":
            p = 15; score -= p; penalizacion_regulatorio += p
            drivers.append("Riesgo IMSS negativo")

        if empresa.repse_suspendido:
            p = 20; score -= p; penalizacion_regulatorio += p
            drivers.append("REPSE suspendido")

        # ── DOMINIO OPERATIVO ──────────────────────────────────────────────
        # (reservado para Sprint 2 — crisis simulation layer)
        # Por ahora sin penalizaciones operativas adicionales

        # ── Variables estratégicas futuras (Sprint 3) ──────────────────────
        # founder_dependency y revenue_concentration preparadas en Empresa
        # pero sin efecto en el score hasta Sprint 3.
        # No eliminar estos comentarios — marcan el punto de integración.
        #
        # if empresa.founder_dependency is not None and empresa.founder_dependency < 30:
        #     score -= 15
        # elif empresa.founder_dependency is not None and empresa.founder_dependency < 60:
        #     score -= 7
        #
        # if empresa.revenue_concentration is not None and empresa.revenue_concentration > 70:
        #     score -= 20
        # elif empresa.revenue_concentration is not None and empresa.revenue_concentration > 50:
        #     score -= 10
        # elif empresa.revenue_concentration is not None and empresa.revenue_concentration > 30:
        #     score -= 5

        esi           = max(score, 0)
        clasificacion = self.clasificar(esi)

        # TODO Sprint Futuro:
        # trend = "improving" | "stable" | "deteriorating"
        # basado en histórico ESI por empresa (requiere persistence layer)
        # Punto de integración: agregar "trend": calcular_trend(empresa.nombre, esi)

        return {
            # ── Trazabilidad ───────────────────────────────────────────────
            "score_version": "ESI-OMEGA-3.2",
            "generated_at":  datetime.now(timezone.utc).isoformat(),

            # ── Índice principal ───────────────────────────────────────────
            "empresa":                   empresa.nombre,
            "enterprise_survival_index": esi,
            "esi":                       esi,
            "continuity_score":          esi,          # alias de compatibilidad
            "clasificacion":             clasificacion,
            "nivel":                     clasificacion, # alias de compatibilidad

            # ── Drivers explicativos ───────────────────────────────────────
            "drivers": drivers,

            # ── Risk Breakdown por dominio ─────────────────────────────────
            "risk_breakdown": {
                "financiero":  penalizacion_financiero,
                "laboral":     penalizacion_laboral,
                "regulatorio": penalizacion_regulatorio,
                "operativo":   penalizacion_operativo,
            },

            # ── Proyección temporal ────────────────────────────────────────
            "continuity_horizon": self.calcular_horizon(esi),

            # ── Métricas detalladas ────────────────────────────────────────
            "metricas": {
                "dscr":               dscr,
                "burn_rate":          burn_rate,
                "severance_pressure": severance_pressure,
                "workforce_risk":     workforce_risk,
                "key_person_risk":    key_person_risk,
                "litigation_ratio":   litigation_ratio,
            },

            # ── Recomendación ejecutiva ────────────────────────────────────
            "recomendacion": self.generar_recomendacion(clasificacion),
        }


    def calcular_continuity_score(self, empresa: Empresa) -> dict:
        """
        Alias legacy de calcular_esi().
        Mantiene compatibilidad con consumidores anteriores a v3.2.
        No contiene lógica propia — delega completamente a calcular_esi().
        """
        return self.calcular_esi(empresa)

    def build_warroom_payload(self, empresa: Empresa) -> dict:
        """
        Helper de integración para War Room Ω.
        Construye el payload completo listo para /api/v1/warroom/status.

        Incluye:
            esi + clasificacion + continuity_horizon + risk_breakdown
            + drivers + plan_306090

        Uso:
            payload = engine.build_warroom_payload(empresa)
            response["continuity"] = payload
        """
        result = self.calcular_esi(empresa)
        esi    = result["esi"]
        nivel  = result["clasificacion"]

        return {
            "esi":                esi,
            "clasificacion":      nivel,
            "continuity_horizon": result["continuity_horizon"],
            "risk_breakdown":     result["risk_breakdown"],
            "drivers":            result["drivers"],
            "plan_306090":        WarRoomEngine().generar_plan_306090(nivel),
            "score_version":      result["score_version"],
            "generated_at":       result["generated_at"],
        }


# ══════════════════════════════════════════════════════════════════════════════
# SEVERANCE ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class SeveranceEngine:
    """Cálculo de liquidación individual. Sin cambios en v3.0."""

    def calcular_liquidacion(
        self,
        salario_mensual:      float,
        antiguedad_anios:     float,
        vacaciones_pendientes: float = 0,
    ) -> dict:

        salario_diario    = salario_mensual / 30
        indemnizacion_90  = salario_diario * 90
        prima_antiguedad  = salario_diario * 12 * antiguedad_anios
        vacaciones        = salario_diario * vacaciones_pendientes
        total             = indemnizacion_90 + prima_antiguedad + vacaciones

        return {
            "indemnizacion_90_dias": round(indemnizacion_90, 2),
            "prima_antiguedad":      round(prima_antiguedad, 2),
            "vacaciones":            round(vacaciones, 2),
            "total_estimado":        round(total, 2),
        }


# ══════════════════════════════════════════════════════════════════════════════
# WAR ROOM ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class WarRoomEngine:
    """
    Planes de acción 30/60/90 días alineados con clasificación v3.0.
    """

    def generar_plan_306090(self, clasificacion: str) -> dict:
        """
        Genera plan de acción ejecutivo según clasificación ESI-Ω.
        Acepta tanto clasificación v3 (ROBUSTA/ESTABLE/VIGILANCIA/RIESGO_ELEVADO/CRITICA)
        como clasificación legacy para compatibilidad.
        """
        planes = {
            "ROBUSTA": {
                "30_dias": "Auditoría de eficiencia operativa",
                "60_dias": "Expansión controlada de capacidad",
                "90_dias": "Blindaje ante ciclos adversos futuros",
            },
            "ESTABLE": {
                "30_dias": "Optimización de liquidez",
                "60_dias": "Automatización financiera",
                "90_dias": "Escalamiento operativo",
            },
            "VIGILANCIA": {
                "30_dias": "Reducir burn rate",
                "60_dias": "Reestructuración parcial",
                "90_dias": "Blindaje fiscal",
            },
            "RIESGO_ELEVADO": {
                "30_dias": "Contención de flujo",
                "60_dias": "Reestructura laboral",
                "90_dias": "Protección de activos",
            },
            "CRITICA": {
                "30_dias": "Supervivencia inmediata",
                "60_dias": "Negociación bancaria",
                "90_dias": "Continuidad crítica",
            },
            # ── Aliases legacy para compatibilidad ────────────────────────
            "PRESION_OPERATIVA": {
                "30_dias": "Reducir burn rate",
                "60_dias": "Reestructuración parcial",
                "90_dias": "Blindaje fiscal",
            },
            "RIESGO_ALTO": {
                "30_dias": "Contención de flujo",
                "60_dias": "Reestructura laboral",
                "90_dias": "Protección de activos",
            },
            "RIESGO_CRITICO": {
                "30_dias": "Supervivencia inmediata",
                "60_dias": "Negociación bancaria",
                "90_dias": "Continuidad crítica",
            },
        }

        return planes.get(clasificacion, planes["CRITICA"])
