# tests/test_sprint2_integration.py -- MESAN Omega Sprint 2 Integration Tests
"""
Suite de pruebas para:
- digital_twin_enterprise.py v2.1
- crisis_scenarios.py v1.0
- crisis_simulation_layer.py v1.0
- continuity_engine.py v3.2 (calcular_esi, build_warroom_payload, alias legacy)

Ejecutar:
    python tests/test_sprint2_integration.py
    python -m pytest tests/test_sprint2_integration.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from digital_twin_enterprise import EnterpriseTwin, simulador_empresarial
from crisis_scenarios import (
    PANDEMIA, PERDIDA_CLIENTE, AUDITORIA_SAT, DEMANDA_LABORAL,
    ESCENARIOS, get_escenario,
)
from crisis_simulation_layer import CrisisSimulationLayer
from continuity_engine import ContinuityEngine, Empresa


# ── Fixtures ──────────────────────────────────────────────────────────────────

def empresa_base() -> Empresa:
    return Empresa(
        nombre                = "Empresa Test",
        ingresos_mensuales    = 500000,
        nomina_mensual        = 200000,
        empleados             = 50,
        empleados_criticos    = 10,
        caja_disponible       = 300000,
        deuda_mensual         = 100000,
        demandas_laborales    = 0,
        trabajadores_sin_imss = 2,
        rotacion_anual        = 15.0,
        severance_estimado    = 50000,
        riesgo_sat            = "POSITIVO",
        riesgo_imss           = "POSITIVO",
        repse_suspendido      = False,
    )

def twin_base() -> EnterpriseTwin:
    return EnterpriseTwin({
        "empresa_id":    "TEST-001",
        "ingresos":      500000,
        "nomina":        200000,
        "gastos":        50000,
        "deuda_mensual": 100000,
    })


# ══════════════════════════════════════════════════════════════════════════════
# DIGITAL TWIN — PRIORIDAD 1
# ══════════════════════════════════════════════════════════════════════════════

def test_digital_twin_import():
    """Módulo importa sin SyntaxError."""
    from digital_twin_enterprise import EnterpriseTwin
    assert EnterpriseTwin is not None
    print("  EnterpriseTwin import: OK ✓")

def test_snapshot():
    twin = twin_base()
    s = twin.snapshot()
    assert s["empresa_id"] == "TEST-001"
    assert s["ingresos"]   == 500000
    assert "timestamp" in s
    print(f"  snapshot(): empresa_id={s['empresa_id']}, ts={s['timestamp'][:10]} ✓")

def test_simulate_cashflow_drop():
    twin = twin_base()
    r = twin.simulate_cashflow_drop(40)
    assert r["new_income"] == 300000.0
    assert r["stress_level"] == 40
    assert r["dias_supervivencia"] >= 0
    assert r["riesgo"] in ("CRITICO", "ALTO", "MEDIO")
    print(f"  simulate_cashflow_drop(40%): new_income={r['new_income']} dias={r['dias_supervivencia']} riesgo={r['riesgo']} ✓")

def test_simulate_embargo():
    twin = twin_base()
    r = twin.simulate_embargo(500000)
    assert "flujo_post_embargo" in r
    assert r["riesgo"] in ("CRITICO", "ALTO")
    print(f"  simulate_embargo(500k): flujo_post={r['flujo_post_embargo']} riesgo={r['riesgo']} ✓")

def test_simulate_perdida_cliente():
    twin = twin_base()
    r = twin.simulate_perdida_cliente(125000)
    assert r["new_income"] == 375000.0
    assert r["riesgo"] in ("CRITICO", "ALTO")
    print(f"  simulate_perdida_cliente(125k): new_income={r['new_income']} dias={r['dias_supervivencia']} ✓")

def test_simulate_nomina_aumento():
    """Bug fix v2.1 — método que estaba truncado."""
    twin = twin_base()
    r = twin.simulate_nomina_aumento(20)
    assert r["nomina_anterior"] == 200000
    assert r["nueva_nomina"]    == 240000.0
    assert r["incremento"]      == 40000.0
    assert "flujo_resultante"   in r
    assert r["riesgo"] in ("CRITICO", "ALTO", "MEDIO")
    print(f"  simulate_nomina_aumento(20%): nueva={r['nueva_nomina']} flujo={r['flujo_resultante']} riesgo={r['riesgo']} ✓")

def test_empresa_original_no_modificada():
    """Verificar que snapshot no muta datos internos."""
    twin = twin_base()
    before = twin.empresa.copy()
    twin.snapshot()
    twin.simulate_cashflow_drop(40)
    twin.simulate_embargo(100000)
    assert twin.empresa == before
    print("  Empresa original no modificada por simulaciones ✓")


# ══════════════════════════════════════════════════════════════════════════════
# CRISIS SCENARIOS — PRIORIDAD 4
# ══════════════════════════════════════════════════════════════════════════════

def test_escenarios_inmutables():
    assert PANDEMIA.factor_riesgo        == 0.40
    assert PERDIDA_CLIENTE.factor_riesgo == 0.25
    assert AUDITORIA_SAT.factor_riesgo   == 0.30
    assert DEMANDA_LABORAL.factor_riesgo == 2.0
    print("  Escenarios inmutables: factores correctos ✓")

def test_catalogo_completo():
    assert "pandemia"        in ESCENARIOS
    assert "perdida_cliente" in ESCENARIOS
    assert "auditoria_sat"   in ESCENARIOS
    assert "demanda_laboral" in ESCENARIOS
    print("  Catálogo: 4 escenarios registrados ✓")

def test_get_escenario():
    e = get_escenario("PANDEMIA")
    assert e.nombre == "PANDEMIA"
    print("  get_escenario() case-insensitive ✓")

def test_get_escenario_invalido():
    try:
        get_escenario("NO_EXISTE")
        assert False, "Debería lanzar KeyError"
    except KeyError:
        print("  get_escenario() KeyError para escenario inválido ✓")


# ══════════════════════════════════════════════════════════════════════════════
# CRISIS SIMULATION LAYER — PRIORIDAD 2
# ══════════════════════════════════════════════════════════════════════════════

def test_simulate_pandemia():
    engine = ContinuityEngine()
    emp    = empresa_base()
    esi_base = engine.calcular_esi(emp)["esi"]
    sim    = CrisisSimulationLayer(engine)
    r      = sim.simulate_pandemia(emp, esi_base)
    assert r.esi_escenario < esi_base, "Pandemia debe degradar ESI"
    assert r.delta < 0
    assert r.clasificacion in ("ROBUSTA","ESTABLE","VIGILANCIA","RIESGO_ELEVADO","CRITICA")
    print(f"  simulate_pandemia: base={esi_base} → {r.esi_escenario} (delta={r.delta}) {r.clasificacion} ✓")

def test_simulate_perdida_cliente():
    engine = ContinuityEngine()
    emp    = empresa_base()
    esi_base = engine.calcular_esi(emp)["esi"]
    sim    = CrisisSimulationLayer(engine)
    r      = sim.simulate_perdida_cliente(emp, esi_base)
    assert r.esi_escenario <= esi_base
    print(f"  simulate_perdida_cliente: base={esi_base} → {r.esi_escenario} (delta={r.delta}) ✓")

def test_simulate_auditoria_sat():
    engine = ContinuityEngine()
    emp    = empresa_base()
    esi_base = engine.calcular_esi(emp)["esi"]
    sim    = CrisisSimulationLayer(engine)
    r      = sim.simulate_auditoria_sat(emp, esi_base)
    assert r.esi_escenario <= esi_base
    print(f"  simulate_auditoria_sat: base={esi_base} → {r.esi_escenario} (delta={r.delta}) ✓")

def test_simulate_demanda_laboral():
    engine = ContinuityEngine()
    emp    = empresa_base()
    esi_base = engine.calcular_esi(emp)["esi"]
    sim    = CrisisSimulationLayer(engine)
    r      = sim.simulate_demanda_laboral(emp, esi_base)
    assert r.esi_escenario <= esi_base
    print(f"  simulate_demanda_laboral: base={esi_base} → {r.esi_escenario} (delta={r.delta}) ✓")

def test_empresa_no_mutada_en_simulacion():
    """deepcopy garantiza que la empresa original no cambia."""
    engine   = ContinuityEngine()
    emp      = empresa_base()
    original_ingresos  = emp.ingresos_mensuales
    original_caja      = emp.caja_disponible
    original_severance = emp.severance_estimado
    esi_base = engine.calcular_esi(emp)["esi"]
    sim = CrisisSimulationLayer(engine)
    sim.simular_todos(emp, esi_base)
    assert emp.ingresos_mensuales  == original_ingresos
    assert emp.caja_disponible     == original_caja
    assert emp.severance_estimado  == original_severance
    print("  Empresa original no mutada por CrisisSimulationLayer ✓")

def test_simular_todos():
    engine   = ContinuityEngine()
    emp      = empresa_base()
    esi_base = engine.calcular_esi(emp)["esi"]
    sim      = CrisisSimulationLayer(engine)
    todos    = sim.simular_todos(emp, esi_base)
    assert set(todos.keys()) == {"pandemia","perdida_cliente","auditoria_sat","demanda_laboral"}
    for nombre, r in todos.items():
        assert "esi_base"      in r
        assert "esi_escenario" in r
        assert "delta"         in r
        assert "clasificacion" in r
        assert "riesgo"        in r
    print(f"  simular_todos(): 4 escenarios OK ✓")
    for nombre, r in todos.items():
        print(f"    {nombre}: {esi_base} → {r['esi_escenario']} (Δ{r['delta']}) [{r['clasificacion']}]")


# ══════════════════════════════════════════════════════════════════════════════
# CONTINUITY ENGINE v3.2 — PRIORIDADES 3 + 5
# ══════════════════════════════════════════════════════════════════════════════

def test_calcular_esi_es_api_principal():
    engine = ContinuityEngine()
    emp    = empresa_base()
    r      = engine.calcular_esi(emp)
    assert "enterprise_survival_index" in r
    assert "esi"                       in r
    assert "continuity_score"          in r
    assert "risk_breakdown"            in r
    assert "drivers"                   in r
    assert "continuity_horizon"        in r
    assert "score_version"             in r
    assert "generated_at"              in r
    print(f"  calcular_esi() API completa: ESI={r['esi']} {r['clasificacion']} ✓")

def test_alias_legacy():
    """calcular_continuity_score() debe retornar exactamente lo mismo que calcular_esi()."""
    engine = ContinuityEngine()
    emp    = empresa_base()
    r1     = engine.calcular_esi(emp)
    r2     = engine.calcular_continuity_score(emp)
    # generated_at puede diferir por microsegundos
    assert r1["esi"] == r2["esi"]
    assert r1["clasificacion"] == r2["clasificacion"]
    assert r1["risk_breakdown"] == r2["risk_breakdown"]
    print("  calcular_continuity_score() alias legacy: compatible ✓")

def test_build_warroom_payload():
    engine  = ContinuityEngine()
    emp     = empresa_base()
    payload = engine.build_warroom_payload(emp)
    assert "esi"                in payload
    assert "clasificacion"      in payload
    assert "continuity_horizon" in payload
    assert "risk_breakdown"     in payload
    assert "drivers"            in payload
    assert "plan_306090"        in payload
    assert "score_version"      in payload
    assert "generated_at"       in payload
    # plan_306090 debe tener 30/60/90 días
    assert "30_dias" in payload["plan_306090"]
    assert "60_dias" in payload["plan_306090"]
    assert "90_dias" in payload["plan_306090"]
    print(f"  build_warroom_payload(): ESI={payload['esi']} plan_306090 ✓")
    print(f"    horizon: {payload['continuity_horizon']}")
    print(f"    breakdown: {payload['risk_breakdown']}")


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        # Digital Twin
        test_digital_twin_import,
        test_snapshot,
        test_simulate_cashflow_drop,
        test_simulate_embargo,
        test_simulate_perdida_cliente,
        test_simulate_nomina_aumento,
        test_empresa_original_no_modificada,
        # Crisis Scenarios
        test_escenarios_inmutables,
        test_catalogo_completo,
        test_get_escenario,
        test_get_escenario_invalido,
        # Crisis Simulation Layer
        test_simulate_pandemia,
        test_simulate_perdida_cliente,
        test_simulate_auditoria_sat,
        test_simulate_demanda_laboral,
        test_empresa_no_mutada_en_simulacion,
        test_simular_todos,
        # Continuity Engine v3.2
        test_calcular_esi_es_api_principal,
        test_alias_legacy,
        test_build_warroom_payload,
    ]

    passed = failed = 0
    print("\nMESAN Ω — Sprint 2 Integration Tests\n" + "─" * 50)

    for test in tests:
        section = {
            test_digital_twin_import: "\n▸ DIGITAL TWIN",
            test_escenarios_inmutables: "\n▸ CRISIS SCENARIOS",
            test_simulate_pandemia: "\n▸ CRISIS SIMULATION LAYER",
            test_calcular_esi_es_api_principal: "\n▸ CONTINUITY ENGINE v3.2",
        }
        if test in section:
            print(section[test])
        try:
            print(f"  {test.__name__}")
            test()
            passed += 1
        except Exception as e:
            print(f"    ✗ FAILED: {e}")
            failed += 1

    print(f"\n{'─'*50}")
    print(f"Resultado: {passed} passed / {failed} failed / {len(tests)} total")
    if failed == 0:
        print("✓ Sprint 2 listo para integración\n")
    else:
        print("✗ Corregir antes de continuar\n")
        sys.exit(1)
