# services/sovereign_continuity_engine.py -- MESAN Omega Motor #10
# Sovereign Continuity Engine (SCE Ω) v1.1
"""
Motor Ω #10 — Sovereign Continuity Engine

Calcula el Digital Sovereignty Index (DSI) de la infraestructura
de una organizacion y entrega recomendaciones al OmegaOrchestrator.

FASE 1 — MODO OBSERVACION:
    - NO migra agentes.
    - NO modifica infraestructura.
    - NO toma decisiones automaticas.
    - Unicamente calcula DSI y entrega recomendaciones.

CHANGELOG v1.1:
    P1 — Thread safety: RLock sobre _nodes y _policies. Todas las
         operaciones de lectura/escritura usan snapshots bajo lock para
         evitar RuntimeError por modificacion concurrente del dict.
    P2 — trust_score eliminado del dataclass (era decorativo). La
         decision se documenta abajo en la seccion "trust_score".
    P3 — DSI modular: DimensionMetric + registro de dimensiones.
         Agregar una dimension nueva = registrar un DimensionMetric,
         sin tocar el algoritmo principal.
    P4 — policy.replicas: si hay menos nodos elegibles que replicas
         requeridas, se emite advertencia explicita en warnings.

trust_score — DECISION DE DISENO:
    Se elimina de SovereignNode porque no tenia funcion matematica
    definida en el DSI. Mantenerlo como campo decorativo viola el
    principio de que cada campo del modelo debe influir en el resultado.
    En Fase 2, si se define una formula clara para incorporar la
    confianza del proveedor (ej. certificaciones ISO 27001, SOC2),
    se reintroducira como una DimensionMetric registrada.

Correlacion geopolitical_risk + regulatory_risk — NOTA DE DISENO:
    Ambas dimensiones tienden a correlacionar (paises inestables
    suelen tener alta incertidumbre regulatoria). Esta correlacion
    es intencional: la soberania digital tiene dos vectores de riesgo
    diferenciados — el riesgo de corte por conflicto/sancion
    (geopolitical) y el riesgo de cumplimiento normativo (regulatory).
    Aunque correlacionan, son accionables por caminos distintos:
    el primero se mitiga con diversificacion geografica, el segundo
    con certificaciones y contratos regulatorios. La suma de pesos
    (0.25 + 0.20 = 0.45) refleja que la dimension pais/regulacion es
    el factor dominante en soberania digital — decision deliberada.

Dependencias externas: ninguna.
Efectos secundarios: ninguno.
Compatible con pipeline existente: si.
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("mesan.sovereign")

SCE_VERSION        = "1.1"
DSI_SCHEMA_VERSION = "1.1.0"   # version del algoritmo DSI para comparacion historica

# ── Tabla de pesos centralizada ───────────────────────────────────────────────
# Todos los pesos del DSI en un solo lugar.
# La suma debe ser exactamente 1.0.
# Nota: trust_score fue eliminado (ver docstring del modulo).
# NOTA DE DISENO — separacion deliberada de geopolitical_risk y regulatory_risk:
# Aunque ambas dimensiones tienden a correlacionar (paises inestables suelen
# tener alta incertidumbre regulatoria), representan vectores de riesgo
# ESTRATEGICAMENTE DISTINTOS:
#   geopolitical_risk  → riesgo de corte por conflicto, sancion o embargo.
#                        Mitigacion: diversificacion geografica de nodos.
#   regulatory_risk    → riesgo de incumplimiento normativo (GDPR, LFPDPPP,
#                        NIS2, etc.). Mitigacion: certificaciones y contratos.
# La suma de pesos (0.25 + 0.20 = 0.45) refleja que la dimension
# pais/regulacion es el factor dominante en soberania digital. Decision
# deliberada — no es doble contabilizacion sino reconocimiento de que ambos
# riesgos requieren acciones distintas y son accionables por separado.
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


# ── DimensionMetric — extensibilidad modular ──────────────────────────────────

@dataclass
class DimensionMetric:
    """
    Define una dimension del DSI de forma modular.

    name:      nombre de la dimension (debe coincidir con DSI_WEIGHTS)
    extractor: funcion que recibe un SovereignNode y retorna float [0,1]
               donde 1.0 = optimo (sin riesgo / maxima disponibilidad)
               y 0.0 = peor caso.
    weight:    peso de esta dimension en el DSI (suma global debe ser 1.0)
    """
    name:      str
    extractor: Callable[["SovereignNode"], float]
    weight:    float


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class SovereignNode:
    """Representa un nodo de infraestructura (cloud, edge, on_prem)."""
    node_id:             str
    provider:            str
    country:             str
    region:              str
    node_type:           str      # cloud | edge | on_prem
    latency_ms:          float
    availability:        float    # 0.0 - 1.0
    cyber_risk:          float    # 0.0 - 1.0 (1 = riesgo maximo)
    geopolitical_risk:   float    # 0.0 - 1.0
    regulatory_risk:     float    # 0.0 - 1.0
    provider_dependency: float    # 0.0 - 1.0
    status:              str = "ACTIVE"

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
    """Define las reglas de soberania que debe cumplir la infraestructura."""
    allowed_countries:       List[str]
    forbidden_providers:     List[str]
    max_geopolitical_risk:   float
    max_provider_dependency: float
    minimum_availability:    float
    replicas:                int = 1   # minimo de nodos elegibles requeridos


@dataclass
class SovereignAssessment:
    """Resultado de la evaluacion de soberania."""
    digital_sovereignty_index: float
    recommendation:            str
    selected_node:             Optional[str]
    warnings:                  List[str] = field(default_factory=list)
    level:                     str = "MODERADO"
    dimension_scores:          Dict[str, float] = field(default_factory=dict)
    policy_violations:         List[str] = field(default_factory=list)
    # P2: contribucion de cada dimension al DSI (positiva o negativa vs baseline 50)
    # Permite al ExecutiveNarrativeGenerator explicar al CEO el origen del score.
    # Ejemplo: {"geopolitical_risk": -18.5, "availability": +12.0}
    dimension_contribution:    Dict[str, float] = field(default_factory=dict)
    # P1: version del schema DSI para comparacion historica entre diagnosticos
    dsi_schema:                str = DSI_SCHEMA_VERSION

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


# ── Engine ────────────────────────────────────────────────────────────────────

class SovereignContinuityEngine:
    """
    Motor Ω #10 — Sovereign Continuity Engine (SCE Ω) v1.1

    Cambios v1.1 vs v1.0:
        - RLock en _nodes y _policies (thread safety)
        - DSI modular via DimensionMetric
        - trust_score eliminado
        - policy.replicas validado con advertencia explicita
    """

    def __init__(self):
        self.version    = SCE_VERSION
        self._lock      = threading.RLock()   # P1: RLock reentrante
        self._nodes:    Dict[str, SovereignNode]   = {}
        self._policies: Dict[str, SovereignPolicy] = {}
        self._dimensions: List[DimensionMetric]    = self._build_default_dimensions()
        logger.info("[SCE] SovereignContinuityEngine v%s inicializado", self.version)

    # ── Registro de dimensiones (P3 — extensibilidad) ─────────────────────────

    def _build_default_dimensions(self) -> List[DimensionMetric]:
        """
        Dimensiones por defecto del DSI.
        Para agregar una nueva dimension: crear un DimensionMetric y
        llamar a register_dimension() — sin tocar este metodo ni el
        algoritmo de calculo.
        """
        return [
            DimensionMetric(
                name="geopolitical_risk",
                extractor=lambda n: 1.0 - n.geopolitical_risk,
                weight=DSI_WEIGHTS["geopolitical_risk"],
            ),
            DimensionMetric(
                name="regulatory_risk",
                extractor=lambda n: 1.0 - n.regulatory_risk,
                weight=DSI_WEIGHTS["regulatory_risk"],
            ),
            DimensionMetric(
                name="availability",
                extractor=lambda n: n.availability,
                weight=DSI_WEIGHTS["availability"],
            ),
            DimensionMetric(
                name="provider_dependency",
                extractor=lambda n: 1.0 - n.provider_dependency,
                weight=DSI_WEIGHTS["provider_dependency"],
            ),
            DimensionMetric(
                name="cyber_risk",
                extractor=lambda n: 1.0 - n.cyber_risk,
                weight=DSI_WEIGHTS["cyber_risk"],
            ),
            DimensionMetric(
                name="latency",
                extractor=lambda n: self._normalize_latency(n.latency_ms) / 100.0,
                weight=DSI_WEIGHTS["latency"],
            ),
        ]

    def register_dimension(self, metric: DimensionMetric) -> None:
        """
        Registra una nueva dimension de riesgo sin modificar el algoritmo.

        ADVERTENCIA: agregar una dimension sin ajustar los pesos del resto
        puede hacer que la suma de pesos supere 1.0 y el DSI quede fuera
        de rango. Siempre recalibrar DSI_WEIGHTS despues de agregar.
        """
        with self._lock:
            self._dimensions.append(metric)
        logger.info("[SCE] Dimension registrada: %s (weight=%.3f)", metric.name, metric.weight)

    # ── API publica ───────────────────────────────────────────────────────────

    def register_node(self, node: SovereignNode) -> None:
        """Registra un nodo. Thread-safe."""
        errors = node.validate()
        if errors:
            logger.warning("[SCE] Nodo %s errores de validacion: %s", node.node_id, errors)
        with self._lock:
            self._nodes[node.node_id] = node
        logger.info("[SCE] Nodo registrado: %s (%s/%s)", node.node_id, node.provider, node.country)

    def register_policy(self, policy_id: str, policy: SovereignPolicy) -> None:
        """Registra una politica. Thread-safe."""
        with self._lock:
            self._policies[policy_id] = policy
        logger.info("[SCE] Politica registrada: %s (replicas=%d)", policy_id, policy.replicas)

    def evaluate(self, ctx: Dict[str, Any]) -> SovereignAssessment:
        """
        Punto de entrada principal — llamado por OmegaOrchestrator.
        Thread-safe: toma snapshot de nodos/politicas bajo lock.
        """
        started  = time.perf_counter()
        trace_id = ctx.get("trace_id", str(uuid.uuid4()))

        # P1: snapshot bajo lock — evita RuntimeError por modificacion concurrente
        with self._lock:
            nodes_snapshot    = dict(self._nodes)
            policies_snapshot = dict(self._policies)
            dims_snapshot     = list(self._dimensions)

        logger.info("[SCE] evaluate | tenant=%s trace=%s nodes=%d",
                    ctx.get("tenant_id", "?"), trace_id, len(nodes_snapshot))

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

        # Calcular DSI para cada nodo activo
        scored: List[Tuple[SovereignNode, float, Dict, List, Dict]] = []
        for node in active_nodes:
            dsi, dims, violations, contribution = self.calculate_digital_sovereignty_index(
                node, policy, dims_snapshot
            )
            scored.append((node, dsi, dims, violations, contribution))

        # Ordenar por DSI desc — sort de Python es estable (desempate por orden de insercion)
        scored.sort(key=lambda x: x[1], reverse=True)
        best_node, best_dsi, best_dims, best_violations, best_contribution = scored[0]

        # DSI global = promedio de todos los nodos activos
        global_dsi = sum(s[1] for s in scored) / len(scored)

        level    = self._classify_dsi(global_dsi)
        warnings = self._collect_warnings(scored, policy)

        # P4: validar replicas
        if policy and policy.replicas > 1:
            eligible = [
                (n, dsi, dims, v, c) for n, dsi, dims, v, c in scored
                if not v   # nodos sin violaciones de politica
            ]
            if len(eligible) < policy.replicas:
                warnings.append(
                    f"Replicas insuficientes: se requieren {policy.replicas} nodos "
                    f"elegibles pero solo hay {len(eligible)} sin violaciones de politica."
                )

        recommendation = self.recommend(global_dsi, best_node, warnings)

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info("[SCE] DSI=%.1f best=%s level=%s ms=%s",
                    global_dsi, best_node.node_id, level, latency_ms)

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

    def calculate_digital_sovereignty_index(
        self,
        node: SovereignNode,
        policy: Optional[SovereignPolicy] = None,
        dimensions: Optional[List[DimensionMetric]] = None,
    ) -> Tuple[float, Dict[str, float], List[str], Dict[str, float]]:
        """
        Calcula el DSI (0-100) de un nodo usando las dimensiones registradas.

        El algoritmo principal es inmutable — agregar dimensiones se hace
        registrando nuevos DimensionMetric, no editando este metodo.

        Retorna: (dsi, dimension_scores, policy_violations)
        """
        dims = dimensions if dimensions is not None else self._dimensions

        # Calcular score normalizado [0, 100] por dimension
        dim_scores: Dict[str, float] = {}
        for metric in dims:
            try:
                raw = metric.extractor(node)
                # clamp [0, 1] antes de escalar
                raw = max(0.0, min(1.0, raw))
                dim_scores[metric.name] = raw * 100.0
            except Exception as e:
                logger.warning("[SCE] Error en dimension %s nodo %s: %s",
                               metric.name, node.node_id, e)
                dim_scores[metric.name] = 0.0

        # DSI ponderado
        total_weight = sum(m.weight for m in dims)
        if total_weight == 0:
            return 0.0, dim_scores, [], {}   # contribution vacio si total_weight==0

        dsi = sum(
            (dim_scores.get(m.name, 0.0) * m.weight)
            for m in dims
        ) / total_weight * 1.0   # normalizar si pesos no suman 1.0

        # Re-escalar si total_weight != 1.0 (cuando se agregan dims sin recalibrar)
        dsi = max(0.0, min(100.0, dsi))

        # P2: contribucion de cada dimension = score_dimension * weight - baseline_contribution
        # baseline = 50.0 * weight (equivale a DSI=50 en esa dimension)
        # Positivo = la dimension mejora el DSI respecto al baseline.
        # Negativo = la dimension penaliza el DSI respecto al baseline.
        baseline = 50.0
        contribution: Dict[str, float] = {
            m.name: (dim_scores.get(m.name, 0.0) - baseline) * m.weight
            for m in dims
        }

        violations = []
        if policy:
            violations = self._check_policy_violations(node, policy)

        return dsi, dim_scores, violations, contribution

    def recommend(
        self,
        dsi: float,
        best_node: Optional[SovereignNode],
        warnings: List[str],
    ) -> str:
        level     = self._classify_dsi(dsi)
        node_info = f" (nodo recomendado: {best_node.node_id})" if best_node else ""

        messages = {
            "SOBERANO":   (f"Soberania digital optima (DSI={dsi:.1f}){node_info}. "
                           "Mantener politicas y monitoreo preventivo."),
            "ROBUSTO":    (f"Soberania digital robusta (DSI={dsi:.1f}){node_info}. "
                           "Revisar dependencias de proveedores y diversificar regiones."),
            "MODERADO":   (f"Soberania digital moderada (DSI={dsi:.1f}){node_info}. "
                           "Reducir concentracion en proveedores y mejorar redundancia geografica."),
            "VULNERABLE": (f"Infraestructura vulnerable (DSI={dsi:.1f}){node_info}. "
                           "Riesgo de corte operativo por factores externos. "
                           "Priorizar diversificacion."),
            "CRITICO":    (f"Soberania digital critica (DSI={dsi:.1f}). "
                           "Alta dependencia con riesgo geopolitico elevado. "
                           "Activar plan de contingencia."),
        }
        return messages.get(level, messages["CRITICO"])

    def health(self) -> Dict[str, Any]:
        """Thread-safe health check."""
        with self._lock:
            n_nodes    = len(self._nodes)
            n_active   = sum(1 for n in self._nodes.values() if n.is_active())
            n_policies = len(self._policies)
            n_dims     = len(self._dimensions)
        return {
            "engine":      "SOVEREIGN_CONTINUITY_ENGINE",
            "version":     self.version,
            "status":      "OK",
            "nodes":       n_nodes,
            "active_nodes":n_active,
            "policies":    n_policies,
            "dimensions":  n_dims,
            "dsi_weights": DSI_WEIGHTS,
        }

    # ── Helpers privados ──────────────────────────────────────────────────────
