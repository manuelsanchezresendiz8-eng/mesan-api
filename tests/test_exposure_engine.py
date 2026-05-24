# tests/test_exposure_engine.py -- MESAN Omega Exposure Engine Tests v1.2

from core.exposure_engine import ExposureEngine

engine = ExposureEngine()


def test_imss_basico():

    r = engine.analizar({
        "trabajadores_sin_imss": 14,
        "salario_diario_promedio": 350,
        "meses_omision": 3
    })

    assert r.exposicion_probable > 0
    assert r.nivel_riesgo in ["CRITICO", "ALTO", "MEDIO", "BAJO"]
    assert len(r.items) > 0


def test_sat_basico():

    r = engine.analizar({
        "isr_retenido": 410000,
        "iva": 620000
    })

    assert r.exposicion_probable > 0
    assert r.nivel_riesgo in ["CRITICO", "ALTO", "MEDIO", "BAJO"]


def test_caso_logistico_completo():

    r = engine.analizar({
        "trabajadores_sin_imss": 14,
        "salario_diario_promedio": 400,
        "meses_omision": 3,
        "isr_retenido": 410000,
        "iva": 620000,
        "trabajadores": 62
    })

    assert r.score_ponderado > 0
    assert len(r.regulatory_versions) > 0
    assert len(r.cascadas) > 0
    assert r.exposicion_max >= r.exposicion_min


def test_input_invalido():

    r = engine.analizar({})

    assert r.score_ponderado == 0
    assert r.exposicion_probable == 0


def test_explainability():

    r = engine.analizar({
        "trabajadores_sin_imss": 5,
        "salario_diario_promedio": 300
    })

    for item in r.items:
        assert item.formula != ""
        assert item.version_regulatoria != ""
        assert item.explicacion != ""
