# tests/test_explainability_engine.py -- MESAN Omega v1.3

from core.explainability_engine import ExplainabilityEngine
from core.validators import InputValidator
from core.contradiction_engine_v2 import ContradictionEngineV2
from core.exposure_engine import ExposureEngine

engine = ExplainabilityEngine()
validator = InputValidator()
ce = ContradictionEngineV2()
exposure = ExposureEngine()

DATA = {
    "ingresos": 1800000,
    "nomina": 740000,
    "gastos": 550000,
    "deuda_mensual": 320000,
    "isr_retenido": 410000,
    "iva": 620000,
    "trabajadores": 62,
    "trabajadores_sin_imss": 14,
    "salario_diario_promedio": 400,
    "meses_omision": 3,
    "repse_activo": True
}


def test_score_explanation():

    r = engine.build_explanation(
        score=85,
        confidence=0.82
    )

    assert r.score_original == 85
    assert r.trace_id != ""
    assert r.engine_version != ""


def test_full_explanation():

    vr = validator.validate(DATA)
    cr = ce.detect(DATA)
    exp = exposure.analizar(DATA)

    r = engine.build_explanation(
        score=87,
        confidence=0.82,
        exposure_result=exp,
        contradiction_result=cr,
        validation_result=vr
    )

    assert r.contradictions_detected >= 0
    assert 0 <= r.confidence_final <= 1
    assert len(r.explanation_tree) > 0
    assert r.summary != ""


def test_empty_input():

    r = engine.build_explanation(score=0)

    assert r.score_original == 0
    assert r.summary != ""


def test_deterministic():

    r1 = engine.build_explanation(
        score=75,
        confidence=0.80
    )

    r2 = engine.build_explanation(
        score=75,
        confidence=0.80
    )

    assert r1.score_original == r2.score_original
    assert r1.confidence_final == r2.confidence_final


def test_explanation_tree_integrity():

    exp = exposure.analizar(DATA)

    r = engine.build_explanation(
        score=80,
        exposure_result=exp
    )

    for node in r.explanation_tree:
        assert node.categoria != ""
        assert node.fuente != ""
