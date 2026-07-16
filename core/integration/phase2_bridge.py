# =============================================================================
# MESAN Omega - Phase 2 Integration Bridge v1.0
# Inteligencia Regulatoria Automatica
# =============================================================================
# Bindings REALES verificados contra:
#   - core/regulation_manager.py  v1.1 (load_ruleset, compare_rulesets, env versions)
#
# Fuente de datos: rulesets curados en config/regulations/{regulador}/{version}.json
# Cada regla lleva "aplica_a" (tags) que se cruzan con el perfil del tenant
# derivado de su diagnostico -> alertas PERSONALIZADAS, no genericas.
#
# Deteccion de cambios: si existe MESAN_{REG}_PREVIOUS, el diff entre la version
# activa y la anterior genera alertas de tipo NUEVO/ACTUALIZADO ("cambio la ley").
#
# REGLA ABSOLUTA (igual que Fase 1): nada de esto puede romper el pipeline.
#   - Flag MESAN_P2_REGULATORY apagado por default -> no-op total
#   - Lazy import + fail-open: cualquier fallo degrada a lista vacia
# =============================================================================

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("mesan.phase2")

FLAG_REGULATORY = "MESAN_P2_REGULATORY"

REGULATORS = ("SAT", "IMSS", "REPSE", "LABORAL", "INFONAVIT")

SEVERIDAD_ORDEN = {"CRITICA": 3, "ALTA": 2, "MEDIA": 1, "BAJA": 0}


def _flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in ("1", "true", "yes", "on")


def _safe(default: Any = None) -> Callable:
    """Decorador fail-open: cualquier excepcion se loguea y se traga."""
    def wrap(fn: Callable) -> Callable:
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - aislamiento total
                logger.warning("phase2_bridge: %s fallo (%s) - no-op", fn.__name__, exc)
                return default
        inner.__name__ = fn.__name__
        return inner
    return wrap


def perfil_tenant(data: Optional[dict]) -> List[str]:
    """Deriva las etiquetas de aplicabilidad desde el payload del diagnostico.

    Estas etiquetas cruzan con el campo "aplica_a" de cada regla del ruleset.
    GENERAL aplica siempre.
    """
    tags = ["GENERAL"]
    if not isinstance(data, dict):
        return tags
    def _f(k):
        try:
            return float(data.get(k, 0) or 0)
        except (TypeError, ValueError):
            return 0.0
    if _f("isr_retenido") > 0:
        tags.append("ISR_RETENIDO")
    if _f("iva") > 0:
        tags.append("IVA")
    if _f("nomina") > 0 or int(data.get("trabajadores", 0) or 0) > 0:
        tags.append("NOMINA")
    if int(data.get("trabajadores_sin_imss", 0) or 0) > 0:
        tags.append("SIN_IMSS")
    if data.get("repse_suspendido") or (data.get("repse_vigente") is False):
        tags.append("REPSE")
    if data.get("bloqueo_bancario"):
        tags.append("BLOQUEO")
    return tags


class RegulatoryBridge:
    """Genera alertas regulatorias personalizadas. Nunca lanza excepciones."""

    def __init__(self) -> None:
        self._manager = None
        self._enabled = _flag(FLAG_REGULATORY)
        if self._enabled:
            try:
                # BINDING REAL: RegulationManager v1.1
                from core.regulation_manager import RegulationManager
                self._manager = RegulationManager()
                logger.info("Phase2: RegulationManager v1.1 conectado (%s reguladores)",
                            len(self._manager.get_all_versions()))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Phase2: RegulationManager no disponible (%s)", exc)
                self._enabled = False

    @property
    def active(self) -> bool:
        return self._enabled and self._manager is not None

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _previous_version(regulator: str) -> Optional[str]:
        return os.getenv(f"MESAN_{regulator.upper()}_PREVIOUS") or None

    def _rule_alert(self, regulator: str, version: str, rule_id: str,
                    rule: dict, tipo: str) -> dict:
        return {
            "regulator": regulator,
            "version": version,
            "rule_id": rule_id,
            "tipo": tipo,                      # VIGENTE | NUEVO | ACTUALIZADO
            "titulo": rule.get("titulo", rule_id),
            "severidad": rule.get("severidad", "MEDIA"),
            "resumen": rule.get("resumen", ""),
            "aplica_a": rule.get("aplica_a", ["GENERAL"]),
        }

    # ------------------------------------------------------------------ API
    @_safe(default=[])
    def get_alerts(self, tenant_data: Optional[dict] = None,
                   solo_cambios: bool = False) -> List[dict]:
        """Alertas personalizadas para el perfil del tenant.

        - VIGENTE: regla activa que aplica al perfil (severidad ALTA/CRITICA)
        - NUEVO / ACTUALIZADO: detectadas por diff contra MESAN_{REG}_PREVIOUS
        Orden: cambios primero, luego por severidad.
        """
        if not self.active:
            return []
        tags = set(perfil_tenant(tenant_data))
        alerts: List[dict] = []

        for reg in REGULATORS:
            active_version = self._manager.get_active_ruleset(reg)
            ruleset = self._manager.load_ruleset(reg)
            if not isinstance(ruleset, dict) or "error" in ruleset:
                continue
            rules = ruleset.get("rules", {}) or {}

            # 1) Cambios vs version anterior (si esta configurada)
            cambios_ids: Dict[str, str] = {}
            prev = self._previous_version(reg)
            if prev and prev != active_version:
                diff = self._manager.compare_rulesets(reg, prev, active_version)
                if diff.get("success"):
                    for rid in diff.get("added", []):
                        cambios_ids[rid] = "NUEVO"
                    for rid in diff.get("changed", []):
                        cambios_ids[rid] = "ACTUALIZADO"

            for rule_id, rule in rules.items():
                if not isinstance(rule, dict):
                    continue
                aplica = set(rule.get("aplica_a", ["GENERAL"]))
                if not (aplica & tags):
                    continue  # no aplica a este tenant
                tipo = cambios_ids.get(rule_id)
                if tipo:
                    alerts.append(self._rule_alert(reg, active_version, rule_id, rule, tipo))
                elif not solo_cambios:
                    sev = rule.get("severidad", "MEDIA")
                    if SEVERIDAD_ORDEN.get(sev, 0) >= SEVERIDAD_ORDEN["ALTA"]:
                        alerts.append(self._rule_alert(reg, active_version, rule_id, rule, "VIGENTE"))

        alerts.sort(key=lambda a: (
            0 if a["tipo"] in ("NUEVO", "ACTUALIZADO") else 1,
            -SEVERIDAD_ORDEN.get(a["severidad"], 0),
        ))
        return alerts

    @_safe(default=None)
    def market_summary(self, tenant_data: Optional[dict] = None,
                       sector: str = "") -> Optional[dict]:
        """Bloque para OmegaResponse.market_intelligence -> seccion del PDF.

        presion_regulatoria: derivada del numero de alertas CRITICA/ALTA aplicables.
        cambios_recientes: titulos de alertas NUEVO/ACTUALIZADO.
        """
        if not self.active:
            return None
        alerts = self.get_alerts(tenant_data)
        if alerts is None:
            return None
        criticas = sum(1 for a in alerts if a["severidad"] == "CRITICA")
        altas    = sum(1 for a in alerts if a["severidad"] == "ALTA")
        if criticas >= 2:
            presion = "ALTA"
        elif criticas == 1 or altas >= 2:
            presion = "MEDIA"
        else:
            presion = "BAJA"
        cambios = [f"{a['regulator']}: {a['titulo']}"
                   for a in alerts if a["tipo"] in ("NUEVO", "ACTUALIZADO")][:6]
        out = {
            "presion_regulatoria": presion,
            "alertas_criticas": criticas,
            "alertas_altas": altas,
            "cambios_recientes": cambios,
            "reguladores_monitoreados": list(REGULATORS),
            "versiones_activas": self._manager.get_all_versions(),
        }
        if sector:
            out["sector"] = sector
        return out

    @_safe(default={})
    def health(self) -> dict:
        if not self.active:
            return {"status": "DISABLED"}
        return self._manager.health()


# =============================================================================
# Singleton - un solo import donde se necesite
# =============================================================================
_regulatory: Optional[RegulatoryBridge] = None


def get_regulatory() -> RegulatoryBridge:
    global _regulatory
    if _regulatory is None:
        _regulatory = RegulatoryBridge()
    return _regulatory
