# =============================================================================
# MESAN Omega - Phase 3 Integration Bridge v1.0
# Digital Twin Empresarial (simulador de escenarios)
# =============================================================================
# Bindings REALES verificados contra:
#   - core/digital_twin_enterprise.py v3.0 (EnterpriseTwin + 4 primitivas)
#   - core/risk_classification.py v1.0 (via el propio Twin)
#
# Escenarios del roadmap compuestos desde las primitivas:
#   base, caida_ventas_10/20/30, incremento_costos, auditoria_sat,
#   demanda_laboral, perdida_cliente_principal, y personalizados.
#
# REGLA ABSOLUTA: flag MESAN_P3_TWIN apagado -> no-op; fail-open total.
# =============================================================================

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, List, Optional

logger = logging.getLogger("mesan.phase3")

FLAG_TWIN = "MESAN_P3_TWIN"

ESCENARIOS_ESTANDAR = [
    "caida_ventas_10", "caida_ventas_20", "caida_ventas_30",
    "incremento_costos_15", "auditoria_sat", "demanda_laboral",
    "perdida_cliente_principal",
]


def _flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in ("1", "true", "yes", "on")


def _safe(default: Any = None) -> Callable:
    def wrap(fn: Callable) -> Callable:
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                logger.warning("phase3_bridge: %s fallo (%s) - no-op", fn.__name__, exc)
                return default
        inner.__name__ = fn.__name__
        return inner
    return wrap


def _f(data: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(data.get(key, default) or default)
    except (TypeError, ValueError):
        return default


class TwinBridge:
    """Simula escenarios sobre el gemelo digital. Nunca lanza excepciones."""

    def __init__(self) -> None:
        self._twin_cls = None
        self._enabled = _flag(FLAG_TWIN)
        if self._enabled:
            try:
                # BINDING REAL: EnterpriseTwin v3.0
                from core.digital_twin_enterprise import EnterpriseTwin
                self._twin_cls = EnterpriseTwin
                logger.info("Phase3: EnterpriseTwin v3.0 conectado")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Phase3: EnterpriseTwin no disponible (%s)", exc)
                self._enabled = False

    @property
    def active(self) -> bool:
        return self._enabled and self._twin_cls is not None

    # ------------------------------------------------------------- escenarios
    def _run_escenario(self, twin, nombre: str, data: dict) -> Optional[dict]:
        """Ejecuta un escenario nombrado componiendo las primitivas del Twin."""
        n = nombre.strip().lower()

        if n.startswith("caida_ventas_"):
            try:
                pct = float(n.rsplit("_", 1)[1])
            except (ValueError, IndexError):
                pct = 20.0
            r = twin.simulate_cashflow_drop(pct)
            desc = f"Caida de ventas del {pct:.0f}%"

        elif n.startswith("incremento_costos"):
            try:
                pct = float(n.rsplit("_", 1)[1])
            except (ValueError, IndexError):
                pct = 15.0
            r = twin.simulate_nomina_aumento(pct)
            desc = f"Incremento de costos operativos del {pct:.0f}%"

        elif n == "auditoria_sat":
            # Impacto: credito fiscal estimado = 2x ISR retenido (criterio del
            # predictive v4.1) o monto default del Twin
            isr = _f(data, "isr_retenido")
            monto = isr * 2 if isr > 0 else 500_000.0
            r = twin.simulate_embargo(monto)
            desc = f"Auditoria SAT con credito fiscal estimado de ${monto:,.0f} MXN"
            r["monto_simulado"] = monto

        elif n == "demanda_laboral":
            # Impacto: severance estimado del payload, o 3 meses de nomina
            # prorrateados a un despido colectivo parcial (25% de la nomina)
            monto = _f(data, "severance_estimado")
            if monto <= 0:
                monto = _f(data, "nomina") * 0.25 * 3
            if monto <= 0:
                monto = 350_000.0
            r = twin.simulate_embargo(monto)
            desc = f"Demanda laboral con pasivo estimado de ${monto:,.0f} MXN"
            r["monto_simulado"] = monto

        elif n == "perdida_cliente_principal":
            # Concentracion del payload o 30% de ingresos por default
            pct_cliente = _f(data, "concentracion_cliente_pct", 30.0)
            ingreso_cli = _f(data, "ingreso_cliente_principal")
            if ingreso_cli <= 0:
                ingreso_cli = _f(data, "ingresos") * pct_cliente / 100.0
            r = twin.simulate_perdida_cliente(ingreso_cli)
            desc = f"Perdida del cliente principal (${ingreso_cli:,.0f} MXN/mes)"
            r["ingreso_cliente_simulado"] = ingreso_cli

        else:
            return None

        return {
            "escenario": n,
            "descripcion": desc,
            "riesgo": r.get("riesgo", "MEDIO"),
            "dias_supervivencia": r.get("dias_supervivencia"),
            "resultado": r,
        }

    # ------------------------------------------------------------------- API
    @_safe(default=None)
    def simulate(self, data: dict, escenarios: Optional[List[str]] = None,
                 tenant_id: str = "global") -> Optional[dict]:
        """Corre los escenarios (estandar o solicitados) sobre el gemelo.

        data: mismo payload financiero del diagnostico (ingresos, nomina,
        gastos, deuda_mensual + opcionales isr_retenido, severance_estimado,
        ingreso_cliente_principal, concentracion_cliente_pct).
        """
        if not self.active or not isinstance(data, dict):
            return None
        t0 = time.perf_counter()
        twin = self._twin_cls({
            "empresa_id": tenant_id,
            "ingresos": _f(data, "ingresos"),
            "nomina": _f(data, "nomina"),
            "gastos": _f(data, "gastos"),
            "deuda_mensual": _f(data, "deuda_mensual"),
        })

        # Linea base: situacion actual sin estres
        base_drop = twin.simulate_cashflow_drop(0)
        base = {
            "escenario": "base",
            "descripcion": "Situacion actual sin estres",
            "riesgo": base_drop.get("riesgo", "MEDIO"),
            "dias_supervivencia": base_drop.get("dias_supervivencia"),
            "resultado": base_drop,
        }

        pedidos = [e for e in (escenarios or ESCENARIOS_ESTANDAR)
                   if isinstance(e, str)][:12]
        resultados = [base]
        no_reconocidos = []
        for nombre in pedidos:
            res = self._run_escenario(twin, nombre, data)
            if res is None:
                no_reconocidos.append(nombre)
            else:
                resultados.append(res)

        peor = min((r for r in resultados[1:]
                    if r.get("dias_supervivencia") is not None),
                   key=lambda r: r["dias_supervivencia"], default=None)
        criticos = [r["escenario"] for r in resultados if r["riesgo"] == "CRITICO"]

        return {
            "engine": "digital_twin",
            "version": "3.0",
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
            "tenant": tenant_id,
            "snapshot": twin.snapshot(),
            "escenarios": resultados,
            "escenarios_no_reconocidos": no_reconocidos,
            "resumen": {
                "total_escenarios": len(resultados),
                "escenarios_criticos": criticos,
                "peor_escenario": (
                    {"escenario": peor["escenario"],
                     "dias_supervivencia": peor["dias_supervivencia"],
                     "riesgo": peor["riesgo"]} if peor else None),
            },
        }


# =============================================================================
_twin: Optional[TwinBridge] = None


def get_twin() -> TwinBridge:
    global _twin
    if _twin is None:
        _twin = TwinBridge()
    return _twin
