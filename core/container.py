# core/container.py -- MESAN Omega Service Container v2.2
"""
MESAN Ω Production Service Container
- Service Registry
- Dependency Injection
- Tenant Configuration Manager
- Engine Lifecycle Manager
- Health Monitoring
- Observability

v2.1:
- set_health() valida engine existente antes de actualizar
- _health extendido con error_count, restart_count, circuit_state (Self-Healing ready)
- diagnostics() incluye conteos healthy/degraded/unhealthy
- TODO: migración de tenants a Redis/PostgreSQL documentada
"""

import logging
import time
from collections import defaultdict
from threading import RLock
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mesan.container")


class Container:
    """
    MESAN Ω Production Service Container v2.2

    Thread-safe, multi-tenant, observable.
    Compatible con FastAPI lifespan y MESAN Ω Self-Healing Control Plane.
    """

    def __init__(self):
        self._engines:  Dict[str, Any]            = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._health:   Dict[str, Dict[str, Any]] = {}
        self._tenants:  Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = RLock()
        logger.info("[Container] Initialized — MESAN Ω Service Container v2.2")

    # ── ENGINE REGISTRY ───────────────────────────────────────────────────────

    def register_engine(
        self,
        name: str,
        engine: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registra un engine. Lanza ValueError si nombre vacío o duplicado."""
        if not name:
            raise ValueError("Engine name cannot be empty")

        with self._lock:
            if name in self._engines:
                raise ValueError(f"Engine '{name}' is already registered")

            self._engines[name] = engine
            self._metadata[name] = metadata or {
                "version": getattr(engine, "version", "unknown"),
                "owner":   "MESAN Ω",
                "enabled": True,
            }
            # v2.1: campos extendidos para Self-Healing Fase 2
            self._health[name] = {
                "status":        "healthy",
                "last_check":    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "latency_ms":    0,
                "error_count":   0,      # incrementar en cada fallo del engine
                "restart_count": 0,      # incrementar en cada reinicio por Self-Healing
                "circuit_state": "CLOSED",  # CLOSED | OPEN | HALF_OPEN
            }

        logger.info("[Container] Engine registered: %s | version=%s",
                    name, self._metadata[name].get("version"))

    def get_engine(self, name: str) -> Any:
        """Retorna engine por nombre. Lanza KeyError si no existe."""
        with self._lock:
            engine = self._engines.get(name)

        if engine is None:
            raise KeyError(f"Engine '{name}' not found in registry")

        return engine

    def has_engine(self, name: str) -> bool:
        with self._lock:
            return name in self._engines

    def unregister_engine(self, name: str) -> None:
        with self._lock:
            self._engines.pop(name, None)
            self._metadata.pop(name, None)
            self._health.pop(name, None)
        logger.info("[Container] Engine unregistered: %s", name)

    def list_engines(self) -> List[str]:
        with self._lock:
            return list(self._engines.keys())

    def engine_count(self) -> int:
        with self._lock:
            return len(self._engines)

    # ── ENGINE METADATA ───────────────────────────────────────────────────────

    def get_engine_metadata(self, name: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._metadata.get(name, {}))

    def update_engine_metadata(
        self,
        name: str,
        updates: Dict[str, Any]
    ) -> None:
        with self._lock:
            if name not in self._engines:
                raise KeyError(f"Engine '{name}' not found")
            self._metadata[name].update(updates)
        logger.info("[Container] Metadata updated: %s | %s", name, updates)

    # ── HEALTH MONITORING ─────────────────────────────────────────────────────

    def set_health(
        self,
        name: str,
        status: str,
        latency_ms: float = 0,
    ) -> None:
        """
        status: 'healthy' | 'degraded' | 'unhealthy'

        v2.1: valida que el engine exista antes de actualizar.
        Evita estados fantasma y métricas inconsistentes.
        """
        with self._lock:
            # Fix v2.1: no permitir health para engines no registrados
            if name not in self._engines:
                raise KeyError(f"Engine '{name}' not found — cannot set health for unregistered engine")

            current = self._health.get(name, {})
            self._health[name] = {
                "status":        status,
                "last_check":    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "latency_ms":    latency_ms,
                # Preservar contadores acumulativos
                "error_count":   current.get("error_count",   0),
                "restart_count": current.get("restart_count", 0),
                "circuit_state": current.get("circuit_state", "CLOSED"),
            }

    def get_health(self, name: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._health.get(name, {"status": "unknown"}))

    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {k: dict(v) for k, v in self._health.items()}

    def increment_error_count(self, name: str) -> None:
        """Incrementa error_count del engine. Para uso en Self-Healing Fase 2."""
        with self._lock:
            if name in self._health:
                self._health[name]["error_count"] += 1

    def increment_restart_count(self, name: str) -> None:
        """Incrementa restart_count del engine. Para uso en Self-Healing Fase 2."""
        with self._lock:
            if name in self._health:
                self._health[name]["restart_count"] += 1

    # ── TENANT CONFIGURATION ──────────────────────────────────────────────────

    def register_tenant_config(
        self,
        tenant_id: str,
        key: str,
        value: Any
    ) -> None:
        if not tenant_id:
            raise ValueError("tenant_id cannot be empty")
        if not key:
            raise ValueError("config key cannot be empty")

        with self._lock:
            self._tenants[tenant_id][key] = value
        logger.debug("[Container] Tenant config set: %s.%s", tenant_id, key)

    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._tenants.get(tenant_id, {}))

    def get_tenant_value(
        self,
        tenant_id: str,
        key: str,
        default: Optional[Any] = None
    ) -> Any:
        with self._lock:
            return self._tenants.get(tenant_id, {}).get(key, default)

    def delete_tenant(self, tenant_id: str) -> None:
        with self._lock:
            self._tenants.pop(tenant_id, None)
        logger.info("[Container] Tenant deleted: %s", tenant_id)

    def tenant_count(self) -> int:
        with self._lock:
            return len(self._tenants)

    # ── DIAGNOSTICS ───────────────────────────────────────────────────────────

    def diagnostics(self) -> Dict[str, Any]:
        """
        v2.1: extendido con conteos por estado de salud.
        Contrato backward compatible — solo se agregan campos nuevos.

        TODO: migrar self._tenants a Redis/PostgreSQL cuando el número de
        tenants supere capacidad razonable de almacenamiento en memoria.
        Umbral sugerido: >1000 tenants activos simultáneos.
        """
        with self._lock:
            health_summary = {k: v["status"] for k, v in self._health.items()}
            statuses = list(health_summary.values())

            return {
                # Campos originales — sin cambios
                "engines":        list(self._engines.keys()),
                "engine_count":   len(self._engines),
                "tenant_count":   len(self._tenants),
                "health_summary": health_summary,
                # Campos nuevos v2.1
                "healthy_engines":   statuses.count("healthy"),
                "degraded_engines":  statuses.count("degraded"),
                "unhealthy_engines": statuses.count("unhealthy"),
            }
