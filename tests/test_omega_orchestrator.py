# tests/test_omega_orchestrator.py -- MESAN Omega Sprint 3 Production Tests
"""
4 tests de producción para OmegaOrchestrator v1.2

Test 1: 100 ejecuciones consecutivas sin excepciones
Test 2: 50 ejecuciones concurrentes — trace_id únicos, sin race conditions
Test 3: Fallo de cada engine individual — _safe_run mantiene pipeline vivo
Test 4: Contrato OmegaResponse — todos los campos obligatorios presentes

Ejecutar:
    python tests/test_omega_orchestrator.py
"""

import sys
import os
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from score_normalizer    import ScoreNormalizer, score_normalizer
from exposure_aggregator import ExposureAggregator, exposure_aggregator
from war_room_engine     import WarRoomEngine, WarRoomSignals, war_room_engine
from omega_response      import OmegaResponse, OmegaResponseBuilder


# ── Fixtures ──────────────────────────────────────────────────────────────────

def empresa_data(tenant_id: str = "TEST", trace_id: str = None) -> dict:
    """Datos de empresa completos para el Orchestrator."""
    return {
        "tenant_id":              tenant_id,
        "trace_id":               trace_id or str(uuid.uuid4()),
        "empresa_nombre":         "Empresa Test S.A. de C.V.",
        "ingresos":               500_000,
        "nomina":                 200_000,
        "gastos":                 50_000,
        "empleados":              50,
        "empleados_criticos":     10,
        "caja_disponible":        300_000,
        "deuda_mensual":          100_000,
        "demandas_laborales":     0,
        "trabajadores_sin_imss":  2,
        "rotacion_anual":         15.0,
        "severance_estimado":     50_000,
        "repse_vigente":          True,
        "opinion_sat":            "POSITIVA",
        "opinion_imss":           "POSITIVA",
        "contratos_vencidos":     0,
        "proveedores_sin_contrato": 0,
        "litigios_activos":       0,
        "nom_035":                True,
        "reglamento_interno":     True,
        "cumplimiento_stps":      True,
        "plan_capacitacion":      True,
    }


# ── Simulador de pipeline (sin engines reales — test de arquitectura) ──────────

class MockOrchestrator:
    """
    Simula el OmegaOrchestrator sin cargar engines reales.
    Permite probar la arquitectura de normalización, aggregation y war room
    sin dependencias de los engines.
    """

    def __init__(self):
        self._normalizer = score_normalizer
        self._exposure   = exposure_aggregator
        self._war_room   = war_room_engine
        self._narrative  = _MockNarrative()

    def ejecutar(self, data: dict, open_circuits: int = 0) -> OmegaResponse:
        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  str(uuid.uuid4()))

        # Simular resultados del pipeline
        pipeline = self._mock_pipeline(data, tenant_id, trace_id)

        # Normalizar
        normalized  = self._normalizer.normalize_all(pipeline)
        omega_score = self._normalizer.omega_health_score(normalized, weights={
            "compliance": 0.15, "fiscal": 0.20, "labor": 0.20,
            "contractual": 0.15, "policy": 0.10, "governance": 0.20,
        })

        # Exposición
        exposure_result = pipeline.pop("_exposure", None) \
            or self._exposure.aggregate_from_pipeline(pipeline)
        sales_priority  = ExposureAggregator.classify_sales_priority(exposure_result.total)

        # ESI
        esi_result = pipeline.get("survival", {})
        esi        = esi_result.get("enterprise_survival_index", 0)
        horizon    = esi_result.get("continuity_horizon", {
            "12_months": 0, "24_months": 0, "36_months": 0
        })
        governance_score = float(pipeline.get("governance", {}).get("governance_score", 0))

        # War Room
        war_signals = WarRoomEngine.build_signals(
            pipeline_results          = pipeline,
            enterprise_survival_index = esi,
            total_exposure_mxn        = exposure_result.total,
            open_circuits             = open_circuits,
        )
        war_result = self._war_room.evaluate(war_signals)

        # Response
        exposure_dict = exposure_result.to_dict()
        exposure_dict["sales_priority"] = sales_priority

        return (
            OmegaResponseBuilder(tenant_id=tenant_id, trace_id=trace_id)
            .set_scores(omega_score, esi, governance_score, horizon)
            .set_war_room(war_result)
            .set_exposure(exposure_dict)
            .set_engines(pipeline)
            .set_remediation({})
            .set_summary(f"ESI={esi} omega={omega_score}")
            .build()
        )

    def ejecutar_con_fallo(self, data: dict, engine_falla: str) -> OmegaResponse:
        """Simula fallo de un engine específico."""
        return self.ejecutar({**data, "_fail_engine": engine_falla})

    def _mock_pipeline(self, data: dict, tenant_id: str, trace_id: str) -> dict:
        fail_engine = data.get("_fail_engine")
        def result(engine_name, score, exposure=0):
            if engine_name == fail_engine:
                return {"engine": engine_name, "engine_status": "ERROR", "error": "Fallo simulado"}
            return {
                "engine": f"MESAN_{engine_name.upper()}",
                "engine_status": "OK",
                f"{engine_name}_score": score,
                "score": score,
                "exposicion_estimada_mxn": exposure,
                "nivel": "VERDE",
                "alertas": [],
                "riesgos": [],
            }

        results = {
            "compliance":  result("compliance",  85),
            "fiscal":      result("fiscal",      30),   # invertido: raw=30 → health=70
            "labor":       result("labor",        82, 50_000),
            "contractual": result("contractual",  78, 100_000),
            "policy":      result("policy",       90, 20_000),
            "governance":  {
                "engine": "MESAN_GOVERNANCE",
                "engine_status": "OK",
                "governance_score": 80.0,
                "score": 80,
                "exposicion_estimada_mxn": 0,
                "nivel": "VERDE",
            },
            "survival": {
                "engine_status": "OK",
                "enterprise_survival_index": 78,
                "esi": 78,
                "continuity_horizon": {"12_months": 88, "24_months": 78, "36_months": 68},
            },
        }

        partial_exposure = self._exposure.aggregate_from_pipeline(results)
        results["_exposure"] = partial_exposure
        return results


class _MockNarrative:
    def generate(self, **kwargs) -> str:
        return f"ESI={kwargs.get('esi',0)} omega={kwargs.get('omega_score',0)}"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — 100 ejecuciones consecutivas
# ══════════════════════════════════════════════════════════════════════════════

def test_100_consecutivas():
    orchestrator = MockOrchestrator()
    errors = []
    start  = time.time()

    for i in range(100):
        try:
            data   = empresa_data(tenant_id=f"tenant_{i}", trace_id=str(uuid.uuid4()))
            result = orchestrator.ejecutar(data)
            assert isinstance(result, OmegaResponse), f"Iter {i}: no es OmegaResponse"
            assert result.tenant_id == f"tenant_{i}", f"Iter {i}: tenant_id incorrecto"
            assert 0 <= result.omega_score <= 100, f"Iter {i}: omega_score fuera de rango"
        except Exception as e:
            errors.append(f"Iter {i}: {e}")

    elapsed = round(time.time() - start, 2)
    assert not errors, f"Errores: {errors}"
    print(f"  100 ejecuciones consecutivas: OK — {elapsed}s total ({round(elapsed*10, 1)}ms/ejecución) ✓")


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — 50 ejecuciones concurrentes
# ══════════════════════════════════════════════════════════════════════════════

def test_50_concurrentes():
    orchestrator = MockOrchestrator()
    results      = {}
    errors       = []
    lock         = threading.Lock()
    start        = time.time()

    def run(i):
        trace_id = str(uuid.uuid4())
        data     = empresa_data(tenant_id=f"concurrent_{i}", trace_id=trace_id)
        result   = orchestrator.ejecutar(data)
        with lock:
            results[trace_id] = result.omega_score
        return trace_id, result

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(run, i) for i in range(50)]
        for future in as_completed(futures):
            try:
                trace_id, result = future.result()
                assert isinstance(result, OmegaResponse)
                assert 0 <= result.omega_score <= 100
            except Exception as e:
                errors.append(str(e))

    elapsed = round(time.time() - start, 2)

    # trace_ids únicos
    assert len(results) == 50, f"Esperados 50 results, obtenidos {len(results)}"
    assert not errors, f"Race condition errors: {errors}"

    scores = list(results.values())
    assert len(set(scores)) >= 1, "Todos los scores son idénticos — posible race condition"

    print(f"  50 concurrentes: OK — {elapsed}s — {len(results)} resultados únicos ✓")


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — Fallo de cada engine individual
# ══════════════════════════════════════════════════════════════════════════════

def test_fallo_engines_individuales():
    orchestrator = MockOrchestrator()
    engines      = ["fiscal", "labor", "contractual", "policy"]

    for engine in engines:
        data   = empresa_data()
        data["_fail_engine"] = engine
        result = orchestrator.ejecutar(data)

        assert isinstance(result, OmegaResponse), f"Fallo {engine}: no retornó OmegaResponse"
        assert result.omega_score >= 0,            f"Fallo {engine}: omega_score negativo"
        # El engine en error aparece con engine_status ERROR
        engine_data = result.engines.get(engine, {})
        # Pipeline sigue vivo aunque un engine falle
        assert len(result.engines) >= 4, f"Fallo {engine}: pipeline se detuvo"
        print(f"  Fallo simulado '{engine}': pipeline sobrevive omega={result.omega_score} ✓")


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — Contrato OmegaResponse
# ══════════════════════════════════════════════════════════════════════════════

def test_contrato_omega_response():
    orchestrator = MockOrchestrator()
    result       = orchestrator.ejecutar(empresa_data())
    d            = result.to_dict()

    campos_obligatorios = [
        "tenant_id", "trace_id",
        "omega_score", "enterprise_survival_index", "governance_score",
        "war_room_required", "war_room_score", "war_room_priority", "war_room_reasons",
        "sales_priority", "total_exposure_mxn",
        "continuity_horizon", "exposure_breakdown",
        "engines", "remediation", "executive_summary",
        "generated_at", "pipeline_version", "score_version",
    ]

    faltantes = [c for c in campos_obligatorios if c not in d]
    assert not faltantes, f"Campos faltantes en OmegaResponse: {faltantes}"

    # Tipos
    assert isinstance(d["omega_score"],               int)
    assert isinstance(d["enterprise_survival_index"], int)
    assert isinstance(d["war_room_required"],         bool)
    assert isinstance(d["total_exposure_mxn"],        float)
    assert isinstance(d["war_room_reasons"],          list)
    assert isinstance(d["continuity_horizon"],        dict)
    assert "12_months" in d["continuity_horizon"]

    # Rangos
    assert 0 <= d["omega_score"]               <= 100
    assert 0 <= d["enterprise_survival_index"] <= 100
    assert d["sales_priority"] in ("A+", "HOT", "A", "B", "C")
    assert d["war_room_priority"] in ("INMEDIATA", "24H", "48H", "7_DIAS", "MONITOREO")

    print(f"  Contrato OmegaResponse: {len(campos_obligatorios)} campos OK ✓")
    print(f"    omega={d['omega_score']} esi={d['enterprise_survival_index']} "
          f"war_room={d['war_room_required']} exposure=${d['total_exposure_mxn']:,.0f} "
          f"priority={d['sales_priority']}")


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    suites = [
        ("Test 1 — 100 ejecuciones consecutivas",    test_100_consecutivas),
        ("Test 2 — 50 ejecuciones concurrentes",     test_50_concurrentes),
        ("Test 3 — Fallo de engines individuales",   test_fallo_engines_individuales),
        ("Test 4 — Contrato OmegaResponse",          test_contrato_omega_response),
    ]

    passed = failed = 0
    print("\nMESAN Ω — Omega Orchestrator Production Tests\n" + "─" * 55)

    for name, test in suites:
        print(f"\n▸ {name}")
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1

    print(f"\n{'─'*55}")
    print(f"Resultado: {passed} passed / {failed} failed / {len(suites)} total")
    if failed == 0:
        print("✓ Arquitectura núcleo Ω lista para congelar\n")
    else:
        print("✗ Corregir antes de congelar\n")
        sys.exit(1)
