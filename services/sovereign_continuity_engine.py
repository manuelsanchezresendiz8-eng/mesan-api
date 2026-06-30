# services/sovereign_continuity_engine.py -- MESAN Omega Motor #10
# Sovereign Continuity Engine (SCE Omega) v1.1

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("mesan.sovereign")

SCE_VERSION        = "1.1"
DSI_SCHEMA_VERSION = "1.1.0"

DSI_WEIGHTS: Dict[str, float] = {
    "geopolitical_risk":    0.25,
    "regulatory_risk":      0.20,
    "availability":         0.20,
    "provider_dependency":  0.15,
    "cyber_risk":           0.15,
    "latency":              0.05,
}

assert abs(sum(DSI_WEIGHTS.values()) - 1.0) < 1e-9, \
    f"DSI_WEIGHTS no suma 1.0: {sum(DSI_WEIGHTS.values())}"

DSI_THRESHOLDS = {
    "SOBERANO":  90.0,
    "ROBUSTO":   75.0,
    "MODERADO":  60.0,
    "VULNERABLE":40.0,
    "CRITICO":    0.0,
}

MAX_LATENCY_MS = 500.0


@dataclass
class DimensionMetric:
    name:      str
    extractor: Callable[["SovereignNode"], float]
    weight:    float


@dataclass
class SovereignNode:
    node_id:             str
    provider:            str
    country:              str
    region:              str
    node_type:            str
    latency_ms:           float
    availability:         float
    cyber_risk:           float
    geopolitical_risk:    float
    regulatory_risk:      float
    provider_dependency:  float
    status:               str = "ACTIVE"

    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def validate(self) -> List[str]:
        errors = []
        for fname, val in [
            ("availability",        self.availability),
            ("cyber_risk",          self.cyber_risk),
            ("geopolitical_risk",   self.geopolitical_risk),
            ("regulatory_risk",     self.regulatory_risk),
            ("provider_dependency", self.provider_dependency),
        ]:
            if not (0.0 <= val <= 1.0):
                errors.append(f"{fname}={val} fuera de rango [0,1]")
        if self.latency_ms < 0:
            errors.append(f"latency_ms={self.latency_ms} no puede ser negativo")
        return errors


@dataclass
class SovereignPolicy:
    allowed_countries:        List[str]
    forbidden_providers:      List[str]
    max_geopolitical_risk:    float
    max_provider_dependency:  float
    minimum_availability:     float
    replicas:                 int = 1


@dataclass
class SovereignAssessment:
    digital_sovereignty_index: float
    recommendation:            str
    selected_node:              Optional[str]
    warnings:                   List[str] = field(default_factory=list)
    level:                      str = "MODERADO"
    dimension_scores:           Dict[str, float] = field(default_factory=dict)
    policy_violations:          List[str] = field(default_factory=list)
    dimension_contribution:     Dict[str, float] = field(default_factory=dict)
    dsi_schema:                 str = "1.1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index":                  round(self.digital_sovereignty_index, 2),
            "level":                  self.level,
            "recommendation":         self.recommendation,
            "selected_node":          self.selected_node,
            "warnings":               list(self.warnings),
            "dimension_scores":       {k: round(v, 2) for k, v in self.dimension_scores.items()},
            "policy_violations":      list(self.policy_violations),
            "dimension_contribution": {k: round(v, 2) for k, v in self.dimension_contribution.items()},
            "dsi_schema":             self.dsi_schema,
        }


class SovereignContinuityEngine:

    def __init__(self):
        self.version    = SCE_VERSION
        self._lock      = threading.RLock()
        self._nodes:    Dict[str, SovereignNode]   = {}
        self._policies: Dict[str, SovereignPolicy] = {}
        self._dimensions: List[DimensionMetric]    = self._build_default_dimensions()
        logger.info("[SCE] SovereignContinuityEngine v%s inicializado", self.version)

    def _build_default_dimensions(self) -> List[DimensionMetric]:
        return [
            DimensionMetric("geopolitical_risk",   lambda n: 1.0 - n.geopolitical_risk,   DSI_WEIGHTS["geopolitical_risk"]),
            DimensionMetric("regulatory_risk",     lambda n: 1.0 - n.regulatory_risk,     DSI_WEIGHTS["regulatory_risk"]),
            DimensionMetric("availability",        lambda n: n.availability,              DSI_WEIGHTS["availability"]),
            DimensionMetric("provider_dependency", lambda n: 1.0 - n.provider_dependency, DSI_WEIGHTS["provider_dependency"]),
            DimensionMetric("cyber_risk",          lambda n: 1.0 - n.cyber_risk,          DSI_WEIGHTS["cyber_risk"]),
            DimensionMetric("latency",             lambda n: self._normalize_latency(n.latency_ms) / 100.0, DSI_WEIGHTS["latency"]),
        ]

    def register_dimension(self, metric: DimensionMetric) -> None:
        with self._lock:
            self._dimensions.append(metric)
        logger.info("[SCE] Dimension registrada: %s", metric.name)

    def register_node(self, node: SovereignNode) -> None:
        errors = node.validate()
        if errors:
            logger.warning("[SCE] Nodo %s errores: %s", node.node_id, errors)
        with self._lock:
            self._nodes[node.node_id] = node
        logger.info("[SCE] Nodo registrado: %s", node.node_id)

    def register_policy(self, policy_id: str, policy: SovereignPolicy) -> None:
        with self._lock:
            self._policies[policy_id] = policy
        logger.info("[SCE] Politica registrada: %s", policy_id)

    def evaluate(self, ctx: Dict[str, Any]) -> SovereignAssessment:
        started  = time.perf_counter()
        trace_id = ctx.get("trace_id", str(uuid.uuid4()))

        with self._lock:
            nodes_snapshot    = dict(self._nodes)
            policies_snapshot = dict(self._policies)
            dims_snapshot     = list(self._dimensions)

        logger.info("[SCE] evaluate | tenant=%s nodes=%d", ctx.get("tenant_id", "?"), len(nodes_snapshot))

        if not nodes_snapshot:
            return self._no_nodes_assessment()

        policy_id = ctx.get("policy_id", "default")
        policy    = policies_snapshot.get(policy_id)

        active_nodes = [n for n in nodes_snapshot.values() if n.is_active()]
        if not active_nodes:
            return SovereignAssessment(
                digital_sovereignty_index=0.0,
                recommendation="No hay nodos activos disponibles.",
                selected_node=None,
                warnings=["Todos los nodos registrados estan inactivos."],
                level="CRITICO",
                dimension_contribution={},
                dsi_schema=DSI_SCHEMA_VERSION,
            )

        scored: List[Tuple[SovereignNode, float, Dict, List, Dict]] = []
        for node in active_nodes:
            dsi, dims, violations, contribution = self.calculate_digital_sovereignty_index(node, policy, dims_snapshot)
            scored.append((node, dsi, dims, violations, contribution))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_node, best_dsi, best_dims, best_violations, best_contribution = scored[0]

        global_dsi = sum(s[1] for s in scored) / len(scored)
        level      = self._classify_dsi(global_dsi)
        warnings   = self._collect_warnings(scored, policy)

        if policy and policy.replicas > 1:
            eligible = [(n, dsi, dims, v, c) for n, dsi, dims, v, c in scored if not v]
            if len(eligible) < policy.replicas:
                warnings.append(
                    f"Replicas insuficientes: se requieren {policy.replicas} nodos elegibles "
                    f"pero solo hay {len(eligible)} sin violaciones de politica."
                )

        recommendation = self.recommend(global_dsi, best_node, warnings)

        return SovereignAssessment(
            digital_sovereignty_index=round(global_dsi, 2),
            recommendation=recommendation,
            selected_node=best_node.node_id,
            warnings=warnings,
            level=level,
            dimension_scores=best_dims,
            policy_violations=best_violations,
            dimension_contribution=best_contribution,
            dsi_schema=DSI_SCHEMA_VERSION,
        )

    def calculate_digital_sovereignty_index(self, node, policy=None, dimensions=None):
        dims = dimensions if dimensions is not None else self._dimensions

        dim_scores: Dict[str, float] = {}
        for metric in dims:
            try:
                raw = metric.extractor(node)
                raw = max(0.0, min(1.0, raw))
                dim_scores[metric.name] = raw * 100.0
            except Exception as e:
                logger.warning("[SCE] Error dimension %s: %s", metric.name, e)
                dim_scores[metric.name] = 0.0

        total_weight = sum(m.weight for m in dims)
        if total_weight == 0:
            return 0.0, dim_scores, [], {}

        dsi = sum(dim_scores.get(m.name, 0.0) * m.weight for m in dims) / total_weight
        dsi = max(0.0, min(100.0, dsi))

        baseline = 50.0
        contribution: Dict[str, float] = {
            m.name: (dim_scores.get(m.name, 0.0) - baseline) * m.weight for m in dims
        }

        violations = []
        if policy:
            violations = self._check_policy_violations(node, policy)

        return dsi, dim_scores, violations, contribution

    def recommend(self, dsi, best_node, warnings):
        level     = self._classify_dsi(dsi)
        node_info = f" (nodo recomendado: {best_node.node_id})" if best_node else ""
        messages = {
            "SOBERANO":   f"Soberania digital optima (DSI={dsi:.1f}){node_info}.",
            "ROBUSTO":    f"Soberania digital robusta (DSI={dsi:.1f}){node_info}.",
            "MODERADO":   f"Soberania digital moderada (DSI={dsi:.1f}){node_info}.",
            "VULNERABLE": f"Infraestructura vulnerable (DSI={dsi:.1f}){node_info}.",
            "CRITICO":    f"Soberania digital critica (DSI={dsi:.1f}).",
        }
        return messages.get(level, messages["CRITICO"])

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "engine":       "SOVEREIGN_CONTINUITY_ENGINE",
                "version":      self.version,
                "status":       "OK",
                "nodes":        len(self._nodes),
                "active_nodes": sum(1 for n in self._nodes.values() if n.is_active()),
                "policies":     len(self._policies),
                "dimensions":   len(self._dimensions),
                "dsi_weights":  DSI_WEIGHTS,
            }

    @staticmethod
    def _normalize_latency(latency_ms: float) -> float:
        if latency_ms <= 0:
            return 100.0
        if latency_ms >= MAX_LATENCY_MS:
            return 0.0
        return (1.0 - latency_ms / MAX_LATENCY_MS) * 100.0

    @staticmethod
    def _classify_dsi(dsi: float) -> str:
        for level, threshold in DSI_THRESHOLDS.items():
            if dsi >= threshold:
                return level
        return "CRITICO"

    @staticmethod
    def _check_policy_violations(node, policy):
        violations = []
        if policy.allowed_countries and node.country not in policy.allowed_countries:
            violations.append(f"Pais '{node.country}' no permitido.")
        if node.provider in policy.forbidden_providers:
            violations.append(f"Proveedor '{node.provider}' prohibido.")
        if node.geopolitical_risk > policy.max_geopolitical_risk:
            violations.append(f"Riesgo geopolitico {node.geopolitical_risk:.2f} excede maximo.")
        if node.provider_dependency > policy.max_provider_dependency:
            violations.append(f"Dependencia {node.provider_dependency:.2f} excede maximo.")
        if node.availability < policy.minimum_availability:
            violations.append(f"Disponibilidad {node.availability:.3f} insuficiente.")
        return violations

    @staticmethod
    def _collect_warnings(scored, policy):
        warnings = []
        for node, dsi, dims, violations, _contribution in scored:
            warnings.extend(violations)
            if dsi < 40.0:
                warnings.append(f"Nodo '{node.node_id}' DSI critico ({dsi:.1f}).")
            if node.geopolitical_risk > 0.7:
                warnings.append(f"Nodo '{node.node_id}' riesgo geopolitico alto.")
        return list(dict.fromkeys(warnings))

    @staticmethod
    def _no_nodes_assessment() -> SovereignAssessment:
        return SovereignAssessment(
            digital_sovereignty_index=0.0,
            recommendation="No hay nodos registrados.",
            selected_node=None,
            warnings=["Sin nodos registrados."],
            level="CRITICO",
            dimension_contribution={},
            dsi_schema=DSI_SCHEMA_VERSION,
        )


sovereign_continuity_engine = SovereignContinuityEngine()