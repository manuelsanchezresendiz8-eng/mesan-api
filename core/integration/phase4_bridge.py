# =============================================================================
# MESAN Omega - Phase 4 Integration Bridge v1.0
# JARVIS Executive Briefing (5 motores en cadena)
# =============================================================================
# Bindings FIRMES (codigo completo leido):
#   - core/decision_engine_v3.py (MesanOmegaDecisionEngine.generar_reporte)
#   - core/ceo_engine.py         (ceo_engine(rent, sim, auditoria, repse))
#   - core/executive_actions.py  (ExecutiveActions.generar_recomendaciones)
# Bindings DEFENSIVOS (API resumida; si no pegan, fallback derivado y etiquetado):
#   - core/explainability_engine.py v2.0
#   - core/consistency_engine.py    v2.0
#
# REGLA ABSOLUTA: flag MESAN_P4_JARVIS apagado -> no-op; fail-open total.
# =============================================================================
from __future__ import annotations
import logging, os, time
from typing import Any, Callable, Optional

logger = logging.getLogger("mesan.phase4")
FLAG_JARVIS = "MESAN_P4_JARVIS"


def _flag(n): return os.getenv(n, "false").strip().lower() in ("1", "true", "yes", "on")


def _safe(default: Any = None) -> Callable:
    def wrap(fn):
        def inner(*a, **k):
            try:
                return fn(*a, **k)
            except Exception as exc:  # noqa: BLE001
                logger.warning("phase4_bridge: %s fallo (%s) - no-op", fn.__name__, exc)
                return default
        inner.__name__ = fn.__name__
        return inner
    return wrap


def _f(d, k, default=0.0):
    try:
        return float(d.get(k, default) or default)
    except (TypeError, ValueError):
        return default


class JarvisBridge:
    """Encadena los 5 motores en un Executive Briefing unico."""

    def __init__(self) -> None:
        self._enabled = _flag(FLAG_JARVIS)
        self._decision = self._ceo = self._actions = None
        self._explain = self._consistency = None
        if self._enabled:
            try:
                from core.decision_engine_v3 import MesanOmegaDecisionEngine, EmpresaInput
                from core.ceo_engine import ceo_engine
                from core.executive_actions import ExecutiveActions
                self._decision = MesanOmegaDecisionEngine
                self._empresa_input = EmpresaInput
                self._ceo = ceo_engine
                self._actions = ExecutiveActions
                logger.info("Phase4: decision_v3 + ceo + executive_actions conectados")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Phase4: motores nucleo no disponibles (%s)", exc)
                self._enabled = False
                return
            # Bindings defensivos (opcionales)
            try:
                import core.explainability_engine as _xe
                self._explain = _xe
            except Exception:
                logger.info("Phase4: explainability no importable - fallback derivado")
            try:
                import core.consistency_engine as _ce
                self._consistency = _ce
            except Exception:
                logger.info("Phase4: consistency no importable - fallback derivado")

    @property
    def active(self):
        return self._enabled and self._decision is not None

    # -------------------------------------------------- construccion de insumos
    def _empresa(self, d: dict):
        return self._empresa_input(
            sector=str(d.get("sector", "GENERAL") or "GENERAL").upper(),
            ingresos_mensuales=_f(d, "ingresos"),
            nomina=_f(d, "nomina"),
            gastos_fijos=_f(d, "gastos"),
            pago_deuda_mensual=_f(d, "deuda_mensual"),
            cartera_vencida=_f(d, "cartera_vencida"),
            adeudo_sat=_f(d, "isr_retenido") + _f(d, "iva"),
            adeudo_imss=_f(d, "adeudo_imss"),
            empleados_sin_imss=int(d.get("trabajadores_sin_imss", 0) or 0),
            permisos_vencidos=list(d.get("permisos_vencidos", []) or []),
            incidente_operativo=bool(d.get("incidente_operativo", False)),
            seguro_rc=bool(d.get("seguro_rc", True)),
            cliente_rescision=bool(d.get("cliente_rescision", False)),
            lineas_credito_saturadas=bool(d.get("bloqueo_bancario", False)),
        )

    def _explicacion(self, reporte: dict, empresa) -> dict:
        """Motor real si pega; si no, explicacion derivada del decision engine
        (deterministica, etiquetada como derivada)."""
        if self._explain is not None:
            for name in ("explain", "generar_explicacion", "explicar"):
                fn = getattr(self._explain, name, None)
                if callable(fn):
                    try:
                        return {"fuente": "explainability_engine_v2", "detalle": fn(reporte)}
                    except Exception:  # noqa: BLE001
                        break
        razones = []
        flujo = empresa.ingresos_mensuales - empresa.nomina - empresa.gastos_fijos - empresa.pago_deuda_mensual
        if flujo < 0:
            razones.append(f"Flujo operativo negativo (${flujo:,.0f} MXN/mes) domina el componente de liquidez (30% del score).")
        if empresa.adeudo_sat + empresa.adeudo_imss > 500000:
            razones.append(f"Adeudo fiscal de ${empresa.adeudo_sat + empresa.adeudo_imss:,.0f} MXN activa el componente fiscal (20%).")
        if empresa.empleados_sin_imss > 0:
            razones.append(f"{empresa.empleados_sin_imss} trabajadores sin IMSS elevan el componente laboral (20%).")
        if empresa.cartera_vencida > empresa.ingresos_mensuales:
            razones.append("Cartera vencida supera un mes de ingresos: presion adicional de liquidez.")
        for p in reporte.get("protocolos", []):
            razones.append(f"Protocolo {p.get('titulo')}: {p.get('objetivo')}.")
        return {"fuente": "derivada_decision_engine_v3", "detalle": razones}

    def _consistencia(self, reporte: dict, ceo: dict) -> dict:
        """Motor real si pega; si no, validacion basica etiquetada."""
        if self._consistency is not None:
            try:
                eng = getattr(self._consistency, "ConsistencyEngine", None)
                if eng is not None:
                    inst = eng()
                    fn = getattr(inst, "validate_cross_engine_consistency", None)
                    if callable(fn):
                        return {"fuente": "consistency_engine_v2", "resultado": fn(reporte)}
            except Exception:  # noqa: BLE001
                pass
        # Fallback: coherencia decision <-> ceo
        nivel = reporte.get("nivel", "")
        prio = ceo.get("prioridad", "")
        coherente = not (nivel == "CRITICO" and prio in ("BAJA", "MEDIA")) and \
                    not (nivel == "CONTROLADO" and prio == "URGENTE")
        return {"fuente": "validacion_basica_bridge",
                "coherente": coherente,
                "detalle": f"nivel_decision={nivel} vs prioridad_ceo={prio}"}

    # ------------------------------------------------------------------- API
    @_safe(default=None)
    def briefing(self, data: dict, tenant_id: str = "global",
                 sim: Optional[dict] = None) -> Optional[dict]:
        """Genera el JARVIS Executive Briefing completo. None si flag apagado."""
        if not self.active or not isinstance(data, dict):
            return None
        t0 = time.perf_counter()
        emp = self._empresa(data)

        # 1) Decision Engine v3 - nucleo
        reporte = self._decision(emp).generar_reporte()

        # 2) CEO Engine - decision final
        ingresos = emp.ingresos_mensuales
        utilidad = ingresos - emp.nomina - emp.gastos_fijos - emp.pago_deuda_mensual
        margen = (utilidad / ingresos * 100) if ingresos > 0 else 0
        rent = {"utilidad": utilidad, "margen": margen}
        auditoria = {"nivel": "RIESGO CRITICO" if reporte["nivel"] == "CRITICO" else reporte["nivel"]}
        repse = {"riesgo_repse": "ALTO" if data.get("repse_suspendido") else "BAJO"}
        ceo = self._ceo(rent, sim or {"mejor": "actual"}, auditoria, repse)

        # 3) Executive Actions - recomendaciones por nivel y sector
        recomendaciones = self._actions.generar_recomendaciones(
            reporte["nivel"], emp.sector)

        # 4) Explainability  5) Consistency
        explicacion = self._explicacion(reporte, emp)
        consistencia = self._consistencia(reporte, ceo)

        return {
            "engine": "jarvis_executive_briefing",
            "version": "1.0",
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
            "tenant": tenant_id,
            "fecha": reporte.get("fecha"),
            "decision_ejecutiva": ceo,
            "riesgo": {"score": reporte["score"], "nivel": reporte["nivel"]},
            "protocolos_activados": reporte.get("protocolos", []),
            "prioridades": reporte.get("prioridades", []),
            "escenarios": reporte.get("escenarios", []),
            "recomendaciones": recomendaciones,
            "explicacion": explicacion,
            "consistencia": consistencia,
        }


_jarvis: Optional[JarvisBridge] = None


def get_jarvis() -> JarvisBridge:
    global _jarvis
    if _jarvis is None:
        _jarvis = JarvisBridge()
    return _jarvis
