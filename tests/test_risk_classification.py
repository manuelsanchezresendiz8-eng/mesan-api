# tests/test_risk_classification.py -- MESAN Omega v1.0
"""
Suite de pruebas para RiskClassificationService.

Cobertura:
    classify_esi()
    classify_esi_full()
    classify_risk_level()
    classify_days_risk()
    classify_flujo()
    classify_health_score()

Ejecutar:
    python tests/test_risk_classification.py
    python -m pytest tests/test_risk_classification.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.risk_classification import (
    RiskClassificationService,
    risk_classifier,
)

svc = RiskClassificationService()


# ══════════════════════════════════════════════════════════════════════════════
# classify_esi()
# ══════════════════════════════════════════════════════════════════════════════

def test_esi_robusta_limite_inferior():
    assert svc.classify_esi(90) == "ROBUSTA"
    print("  classify_esi(90) → ROBUSTA ✓")

def test_esi_robusta_maximo():
    assert svc.classify_esi(100) == "ROBUSTA"
    print("  classify_esi(100) → ROBUSTA ✓")

def test_esi_estable_limite_inferior():
    assert svc.classify_esi(80) == "ESTABLE"
    print("  classify_esi(80) → ESTABLE ✓")

def test_esi_estable_limite_superior():
    assert svc.classify_esi(89) == "ESTABLE"
    print("  classify_esi(89) → ESTABLE ✓")

def test_esi_vigilancia_limite_inferior():
    assert svc.classify_esi(70) == "VIGILANCIA"
    print("  classify_esi(70) → VIGILANCIA ✓")

def test_esi_vigilancia_limite_superior():
    assert svc.classify_esi(79) == "VIGILANCIA"
    print("  classify_esi(79) → VIGILANCIA ✓")

def test_esi_riesgo_elevado_limite_inferior():
    assert svc.classify_esi(60) == "RIESGO_ELEVADO"
    print("  classify_esi(60) → RIESGO_ELEVADO ✓")

def test_esi_riesgo_elevado_limite_superior():
    assert svc.classify_esi(69) == "RIESGO_ELEVADO"
    print("  classify_esi(69) → RIESGO_ELEVADO ✓")

def test_esi_critica_limite_superior():
    assert svc.classify_esi(59) == "CRITICA"
    print("  classify_esi(59) → CRITICA ✓")

def test_esi_critica_minimo():
    assert svc.classify_esi(0) == "CRITICA"
    print("  classify_esi(0) → CRITICA ✓")

def test_esi_cinco_niveles_completos():
    """Verifica los 5 niveles sin gaps ni solapamientos."""
    mapping = {
        95: "ROBUSTA",
        84: "ESTABLE",
        74: "VIGILANCIA",
        64: "RIESGO_ELEVADO",
        45: "CRITICA",
    }
    for score, expected in mapping.items():
        result = svc.classify_esi(score)
        assert result == expected, f"ESI {score}: esperado {expected}, obtenido {result}"
    print("  5 niveles sin gaps: OK ✓")


# ══════════════════════════════════════════════════════════════════════════════
# classify_esi_full()
# ══════════════════════════════════════════════════════════════════════════════

def test_esi_full_estructura():
    """Verifica que ClassificationResult tiene nivel, etiqueta y color."""
    r = svc.classify_esi_full(84)
    assert hasattr(r, 'nivel')
    assert hasattr(r, 'etiqueta')
    assert hasattr(r, 'color')
    print(f"  classify_esi_full(84): nivel={r.nivel} etiqueta='{r.etiqueta}' color={r.color} ✓")

def test_esi_full_robusta():
    r = svc.classify_esi_full(95)
    assert r.nivel == "ROBUSTA"
    assert r.color == "green"
    print(f"  classify_esi_full(95): ROBUSTA/green ✓")

def test_esi_full_critica():
    r = svc.classify_esi_full(45)
    assert r.nivel == "CRITICA"
    assert r.color == "red"
    print(f"  classify_esi_full(45): CRITICA/red ✓")

def test_esi_full_vigilancia():
    r = svc.classify_esi_full(74)
    assert r.nivel == "VIGILANCIA"
    assert r.color == "yellow"
    print(f"  classify_esi_full(74): VIGILANCIA/yellow ✓")

def test_esi_full_riesgo_elevado():
    r = svc.classify_esi_full(64)
    assert r.nivel == "RIESGO_ELEVADO"
    assert r.color == "orange"
    print(f"  classify_esi_full(64): RIESGO_ELEVADO/orange ✓")

def test_esi_full_inmutable():
    """ClassificationResult es frozen=True — no se puede modificar."""
    r = svc.classify_esi_full(84)
    try:
        r.nivel = "MODIFICADO"
        assert False, "Debería ser inmutable"
    except Exception:
        print("  classify_esi_full() inmutable: OK ✓")


# ══════════════════════════════════════════════════════════════════════════════
# classify_risk_level()
# ══════════════════════════════════════════════════════════════════════════════

def test_risk_level_critico():
    assert svc.classify_risk_level(59) == "CRITICO"
    assert svc.classify_risk_level(0)  == "CRITICO"
    print("  classify_risk_level(<60) → CRITICO ✓")

def test_risk_level_alto():
    assert svc.classify_risk_level(60) == "ALTO"
    assert svc.classify_risk_level(74) == "ALTO"
    print("  classify_risk_level(60-74) → ALTO ✓")

def test_risk_level_medio():
    assert svc.classify_risk_level(75)  == "MEDIO"
    assert svc.classify_risk_level(100) == "MEDIO"
    print("  classify_risk_level(>=75) → MEDIO ✓")

def test_risk_level_limites():
    """Verifica límites exactos sin ambigüedad."""
    assert svc.classify_risk_level(59) == "CRITICO"
    assert svc.classify_risk_level(60) == "ALTO"
    assert svc.classify_risk_level(74) == "ALTO"
    assert svc.classify_risk_level(75) == "MEDIO"
    print("  classify_risk_level() límites exactos ✓")


# ══════════════════════════════════════════════════════════════════════════════
# classify_days_risk()
# ══════════════════════════════════════════════════════════════════════════════

def test_days_critico():
    assert svc.classify_days_risk(0)  == "CRITICO"
    assert svc.classify_days_risk(14) == "CRITICO"
    print("  classify_days_risk(<15) → CRITICO ✓")

def test_days_alto():
    assert svc.classify_days_risk(15) == "ALTO"
    assert svc.classify_days_risk(29) == "ALTO"
    print("  classify_days_risk(15-29) → ALTO ✓")

def test_days_medio():
    assert svc.classify_days_risk(30) == "MEDIO"
    assert svc.classify_days_risk(90) == "MEDIO"
    print("  classify_days_risk(>=30) → MEDIO ✓")

def test_days_limites_exactos():
    assert svc.classify_days_risk(14) == "CRITICO"
    assert svc.classify_days_risk(15) == "ALTO"
    assert svc.classify_days_risk(29) == "ALTO"
    assert svc.classify_days_risk(30) == "MEDIO"
    print("  classify_days_risk() límites exactos ✓")


# ══════════════════════════════════════════════════════════════════════════════
# classify_flujo()
# ══════════════════════════════════════════════════════════════════════════════

def test_flujo_critico_negativo():
    assert svc.classify_flujo(-1)       == "CRITICO"
    assert svc.classify_flujo(-100000)  == "CRITICO"
    print("  classify_flujo(negativo) → CRITICO ✓")

def test_flujo_alto_con_referencia():
    # flujo=5000, referencia=200000 → 5000 < 200000*0.2=40000 → ALTO
    assert svc.classify_flujo(5000, referencia=200000) == "ALTO"
    print("  classify_flujo(estrecho con referencia) → ALTO ✓")

def test_flujo_medio_sin_referencia():
    assert svc.classify_flujo(0)       == "MEDIO"
    assert svc.classify_flujo(100000)  == "MEDIO"
    print("  classify_flujo(>=0, sin referencia) → MEDIO ✓")

def test_flujo_medio_con_referencia_holgada():
    # flujo=100000, referencia=200000 → 100000 >= 200000*0.2=40000 → MEDIO
    assert svc.classify_flujo(100000, referencia=200000) == "MEDIO"
    print("  classify_flujo(holgado con referencia) → MEDIO ✓")

def test_flujo_cero_es_medio():
    """Flujo en cero exacto no es CRITICO — solo negativo lo es."""
    assert svc.classify_flujo(0) == "MEDIO"
    print("  classify_flujo(0) → MEDIO (no CRITICO) ✓")


# ══════════════════════════════════════════════════════════════════════════════
# classify_health_score()
# ══════════════════════════════════════════════════════════════════════════════

def test_health_optimo():
    assert svc.classify_health_score(90)  == "OPTIMO"
    assert svc.classify_health_score(100) == "OPTIMO"
    print("  classify_health_score(>=90) → OPTIMO ✓")

def test_health_saludable():
    assert svc.classify_health_score(75) == "SALUDABLE"
    assert svc.classify_health_score(89) == "SALUDABLE"
    print("  classify_health_score(75-89) → SALUDABLE ✓")

def test_health_degradado():
    assert svc.classify_health_score(50) == "DEGRADADO"
    assert svc.classify_health_score(74) == "DEGRADADO"
    print("  classify_health_score(50-74) → DEGRADADO ✓")

def test_health_critico():
    assert svc.classify_health_score(49) == "CRITICO"
    assert svc.classify_health_score(0)  == "CRITICO"
    print("  classify_health_score(<50) → CRITICO ✓")

def test_health_limites_exactos():
    assert svc.classify_health_score(89) == "SALUDABLE"
    assert svc.classify_health_score(90) == "OPTIMO"
    assert svc.classify_health_score(74) == "DEGRADADO"
    assert svc.classify_health_score(75) == "SALUDABLE"
    assert svc.classify_health_score(49) == "CRITICO"
    assert svc.classify_health_score(50) == "DEGRADADO"
    print("  classify_health_score() límites exactos ✓")


# ══════════════════════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ══════════════════════════════════════════════════════════════════════════════

def test_instancia_global():
    """risk_classifier es la instancia global — mismos resultados que svc."""
    assert risk_classifier.classify_esi(74)          == svc.classify_esi(74)
    assert risk_classifier.classify_risk_level(48)   == svc.classify_risk_level(48)
    assert risk_classifier.classify_days_risk(10)    == svc.classify_days_risk(10)
    assert risk_classifier.classify_health_score(85) == svc.classify_health_score(85)
    print("  risk_classifier global: mismos resultados que instancia local ✓")


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    suites = {
        "classify_esi()": [
            test_esi_robusta_limite_inferior,
            test_esi_robusta_maximo,
            test_esi_estable_limite_inferior,
            test_esi_estable_limite_superior,
            test_esi_vigilancia_limite_inferior,
            test_esi_vigilancia_limite_superior,
            test_esi_riesgo_elevado_limite_inferior,
            test_esi_riesgo_elevado_limite_superior,
            test_esi_critica_limite_superior,
            test_esi_critica_minimo,
            test_esi_cinco_niveles_completos,
        ],
        "classify_esi_full()": [
            test_esi_full_estructura,
            test_esi_full_robusta,
            test_esi_full_critica,
            test_esi_full_vigilancia,
            test_esi_full_riesgo_elevado,
            test_esi_full_inmutable,
        ],
        "classify_risk_level()": [
            test_risk_level_critico,
            test_risk_level_alto,
            test_risk_level_medio,
            test_risk_level_limites,
        ],
        "classify_days_risk()": [
            test_days_critico,
            test_days_alto,
            test_days_medio,
            test_days_limites_exactos,
        ],
        "classify_flujo()": [
            test_flujo_critico_negativo,
            test_flujo_alto_con_referencia,
            test_flujo_medio_sin_referencia,
            test_flujo_medio_con_referencia_holgada,
            test_flujo_cero_es_medio,
        ],
        "classify_health_score()": [
            test_health_optimo,
            test_health_saludable,
            test_health_degradado,
            test_health_critico,
            test_health_limites_exactos,
        ],
        "Instancia global": [
            test_instancia_global,
        ],
    }

    passed = failed = 0
    print("\nMESAN Ω — RiskClassificationService Test Suite\n" + "─" * 50)

    for suite_name, tests in suites.items():
        print(f"\n▸ {suite_name}")
        for test in tests:
            try:
                print(f"  {test.__name__}")
                test()
                passed += 1
            except Exception as e:
                print(f"    ✗ FAILED: {e}")
                failed += 1

    total = passed + failed
    print(f"\n{'─'*50}")
    print(f"Resultado: {passed} passed / {failed} failed / {total} total")
    if failed == 0:
        print("✓ RiskClassificationService listo para producción\n")
    else:
        print("✗ Corregir antes del merge\n")
        sys.exit(1)
