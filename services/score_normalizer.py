# services/score_normalizer.py -- MESAN Omega v1.0
"""
Score Normalizer Ω

Resuelve la inconsistencia semántica entre engines:

  FiscalSentinelEngine  → score INVERTIDO (0=saludable, 100=crisis)
  Todos los demás       → score DIRECTO   (100=saludable, 0=crisis)

El normalizador expone una interfaz uniforme sin modificar los engines.

Salida estándar por engine:
    {
        "health_score": 0-100,   # siempre: mayor = más saludable
        "risk_score":   0-100,   # siempre: mayor = más riesgo
        "raw_score":    int,     # valor original del engine
        "engine":       str,
        "inverted":     bool     # True solo para FiscalSentinel
    }
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("mesan.score_normalizer")


# ══════════════════════════════════════════════════════════════════════════════
# REGISTRO DE ENGINES Y SU SEMÁNTICA
# ══════════════════════════════════════════════════════════════════════════════

# True  = engine usa semántica INVERTIDA (mayor score = más riesgo)
# False = engine usa semántica DIRECTA   (mayor score = más saludable)
ENGINE_SEMANTICS: dict[str, bool] = {
    "MESAN_FISCAL_SENTINEL":    True,   # score invertido — documentado en auditoría
    "MESAN_COMPLIANCE_VERIFY":  False,
    "MESAN_LABOR_SHIELD":       False,
    "MESAN_CONTRACTUAL_RISK":   False,
    "MESAN_POLICY_AUDIT":       False,
    "MESAN_GOVERNANCE":         False,
    "MESAN_REMEDIATION":        False,
    "MESAN_ENTERPRISE_SURVIVAL":False,
}

# Claves de score por engine (pueden variar entre engines)
ENGINE_SCORE_KEYS: dict[str, str] = {
    "MESAN_FISCAL_SENTINEL":             "fiscal_score",
    "MESAN_COMPLIANCE_VERIFY":           "score_compliance",
    "MESAN_LABOR_SHIELD":                "labor_score",
    "MESAN_CONTRACTUAL_RISK":            "contractual_score",
    "MESAN_POLICY_AUDIT":                "policy_score",
    "MESAN_GOVERNANCE":                  "governance_score",
    "MESAN_REMEDIATION":                 "score",
    "MESAN_ENTERPRISE_SURVIVAL":         "enterprise_survival_index",
    "MESAN_FINANCIAL_INTELLIGENCE":      "financial_score",      # v1.1 oficial
    "MESAN_FINANCIAL_INTELLIGENCE_V2":   "financial_score_v2",   # v2.0 shadow
}


# ══════════════════════════════════════════════════════════════════════════════
# RESULTADO NORMALIZADO
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class NormalizedScore:
    engine:       str
    health_score: int    # mayor = más saludable (0-100)
    risk_score:   int    # mayor = más riesgo    (0-100)
    raw_score:    int    # valor original del engine
    inverted:     bool   # True si el engine usa semántica invertida

    def to_dict(self) -> dict:
        return {
            "engine":       self.engine,
            "health_score": self.health_score,
            "risk_score":   self.risk_score,
            "raw_score":    self.raw_score,
            "inverted":     self.inverted,
        }


# ══════════════════════════════════════════════════════════════════════════════
# SCORE NORMALIZER
# ══════════════════════════════════════════════════════════════════════════════

class ScoreNormalizer:
    """
    Normaliza scores de todos los engines a una semántica uniforme.

    Uso:
        normalizer = ScoreNormalizer()

        # Normalizar un engine individual
        result = normalizer.normalize("MESAN_FISCAL_SENTINEL", raw_score=72)
        # → NormalizedScore(health_score=28, risk_score=72, inverted=True)

        # Normalizar resultado completo de un engine
        result = normalizer.normalize_engine_result(fiscal_result)
        # → NormalizedScore extraído automáticamente

        # Normalizar todos los engines del pipeline
        all_scores = normalizer.normalize_all(engine_results)
    """

    # ── Normalización individual ──────────────────────────────────────────────

    def normalize(self, engine_name: str, raw_score: int) -> NormalizedScore:
        """
        Normaliza un score dado su engine.

        Para engines con semántica invertida (FiscalSentinel):
            health_score = 100 - raw_score
            risk_score   = raw_score

        Para engines con semántica directa:
            health_score = raw_score
            risk_score   = 100 - raw_score
        """
        inverted = ENGINE_SEMANTICS.get(engine_name, False)
        raw      = max(0, min(100, int(raw_score)))

        if inverted:
            health = 100 - raw
            risk   = raw
        else:
            health = raw
            risk   = 100 - raw

        return NormalizedScore(
            engine       = engine_name,
            health_score = health,
            risk_score   = risk,
            raw_score    = raw,
            inverted     = inverted,
        )

    # ── Extracción automática desde resultado del engine ──────────────────────

    def normalize_engine_result(self, engine_result: dict) -> NormalizedScore:
        """
        Extrae el score del resultado de un engine y lo normaliza.
        Fix P0-C2: si engine_status=ERROR, retorna health=50 sin invertir.
        Fix P1-C1: log warning si engine no está registrado.
        """
        engine_name = engine_result.get("engine", "UNKNOWN")

        # Fix P0-C2: engine con error → neutro (50) sin inversión
        # Evita que FiscalSentinel score=0 por fallo retorne health=100
        if engine_result.get("engine_status") == "ERROR":
            logger.warning("[ScoreNormalizer] Engine '%s' en ERROR — usando score neutro 50",
                           engine_name)
            return NormalizedScore(engine=engine_name, health_score=50,
                                   risk_score=50, raw_score=50, inverted=False)

        score_key = ENGINE_SCORE_KEYS.get(engine_name)

        # Fix P1-C1: log cuando engine no está registrado
        if engine_name not in ENGINE_SCORE_KEYS and engine_name != "UNKNOWN":
            logger.warning("[ScoreNormalizer] Engine '%s' no registrado — fallback 50", engine_name)

        # Intentar clave registrada primero, luego fallbacks comunes
        raw_score = None
        if score_key:
            raw_score = engine_result.get(score_key)

        if raw_score is None:
            for fallback in ("score", "fiscal_score", "labor_score",
                             "contractual_score", "policy_score",
                             "governance_score", "enterprise_survival_index"):
                if fallback in engine_result:
                    raw_score = engine_result[fallback]
                    break

        if raw_score is None:
            raw_score = 50  # default neutral si no se encuentra

        return self.normalize(engine_name, int(raw_score))

    # ── Normalización del pipeline completo ───────────────────────────────────

    def normalize_all(self, engine_results: dict) -> dict[str, NormalizedScore]:
        """
        Normaliza todos los resultados del pipeline de engines.

        Args:
            engine_results: { "fiscal": {...}, "compliance": {...}, ... }

        Returns:
            { "fiscal": NormalizedScore, "compliance": NormalizedScore, ... }
        """
        normalized = {}
        for key, result in engine_results.items():
            if isinstance(result, dict) and "engine" in result:
                normalized[key] = self.normalize_engine_result(result)
        return normalized

    # ── Score compuesto del sistema ───────────────────────────────────────────

    def omega_health_score(
        self,
        normalized_scores: dict[str, NormalizedScore],
        weights: Optional[dict[str, float]] = None,
    ) -> int:
        """
        Calcula el Omega Health Score como promedio ponderado
        de los health_scores normalizados.

        Pesos por defecto iguales si no se especifican.
        """
        if not normalized_scores:
            return 0

        default_weights = {k: 1.0 for k in normalized_scores}
        w = weights or default_weights

        total_weight = sum(w.get(k, 1.0) for k in normalized_scores)
        if total_weight == 0:
            return 0

        weighted_sum = sum(
            ns.health_score * w.get(key, 1.0)
            for key, ns in normalized_scores.items()
        )

        return round(weighted_sum / total_weight)

    def snapshot(self, normalized_scores: dict[str, NormalizedScore]) -> dict:
        """Snapshot completo para diagnóstico y War Room."""
        return {
            key: ns.to_dict()
            for key, ns in normalized_scores.items()
        }


# Instancia global
score_normalizer = ScoreNormalizer()
