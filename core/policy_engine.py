# core/policy_engine.py
# MESAN Omega — Policy Engine v2.0
# Enterprise Governance / Compliance / Automation Layer

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import ast
import uuid


# ============================================================
# ENUMS
# ============================================================

class PolicySeverity(str, Enum):

    BAJO = "BAJO"

    MEDIO = "MEDIO"

    ALTO = "ALTO"

    CRITICO = "CRITICO"


class PolicyActionType(str, Enum):

    ALERT = "ALERT"

    ACTION = "ACTION"

    BLOCK = "BLOCK"

    EMERGENCY = "EMERGENCY"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class PolicyRule:

    rule_id: str

    nombre: str

    condicion: str

    accion: str

    prioridad: int

    severidad: PolicySeverity = (
        PolicySeverity.MEDIO
    )

    action_type: PolicyActionType = (
        PolicyActionType.ACTION
    )

    activa: bool = True

    version: str = "2.0"

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class TriggeredPolicy:

    rule_id: str

    nombre: str

    accion: str

    severidad: str

    action_type: str

    descripcion: str

    timestamp: str


@dataclass
class PolicyResult:

    trace_id: str

    rules_evaluated: int

    rules_triggered: int

    actions: List[str]

    alerts: List[str]

    blocked_operations: List[str]

    emergency_protocols: List[str]

    triggered_policies: List[
        TriggeredPolicy
    ] = field(default_factory=list)

    system_risk: str = "BAJO"

    engine_version: str = "2.0.0"

    timestamp: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )


# ============================================================
# SAFE CONDITION EVALUATOR
# ============================================================

class SafeEvaluator(ast.NodeVisitor):

    ALLOWED_NODES = (

        ast.Expression,

        ast.BoolOp,

        ast.Compare,

        ast.Name,

        ast.Load,

        ast.Constant,

        ast.And,

        ast.Or,

        ast.Gt,

        ast.GtE,

        ast.Lt,

        ast.LtE,

        ast.Eq,

        ast.NotEq,

        ast.UnaryOp,

        ast.Not,

        ast.USub,

        ast.BinOp,

        ast.Add,

        ast.Sub,

        ast.Mult,

        ast.Div,

        ast.Mod

    )

    def visit(self, node):

        if not isinstance(
            node,
            self.ALLOWED_NODES
        ):

            raise ValueError(
                f"Operación no permitida: "
                f"{type(node).__name__}"
            )

        return super().visit(node)

    @staticmethod
    def evaluate(
        expression: str,
        context: dict
    ) -> bool:

        tree = ast.parse(
            expression,
            mode="eval"
        )

        SafeEvaluator().visit(tree)

        compiled = compile(
            tree,
            "<policy>",
            "eval"
        )

        return bool(eval(
            compiled,
            {"__builtins__": {}},
            context
        ))


# ============================================================
# DEFAULT POLICIES
# ============================================================

DEFAULT_POLICIES = [

    PolicyRule(

        rule_id="P001",

        nombre="Score Crítico CEO",

        condicion="score >= 85",

        accion="ALERT_CEO",

        prioridad=1,

        severidad=PolicySeverity.CRITICO,

        action_type=PolicyActionType.ALERT

    ),

    PolicyRule(

        rule_id="P002",

        nombre="IMSS Crítico",

        condicion="trabajadores_sin_imss > 10",

        accion="FREEZE_EXPANSION",

        prioridad=2,

        severidad=PolicySeverity.ALTO,

        action_type=PolicyActionType.BLOCK

    ),

    PolicyRule(

        rule_id="P003",

        nombre="Liquidez Crítica",

        condicion="dias_supervivencia < 15",

        accion="ACTIVATE_SURVIVAL_PROTOCOL",

        prioridad=1,

        severidad=PolicySeverity.CRITICO,

        action_type=PolicyActionType.EMERGENCY

    ),

    PolicyRule(

        rule_id="P004",

        nombre="ISR Alto",

        condicion="isr_retenido > 500000",

        accion="ALERT_LEGAL_TEAM",

        prioridad=2,

        severidad=PolicySeverity.ALTO,

        action_type=PolicyActionType.ALERT

    ),

    PolicyRule(

        rule_id="P005",

        nombre="Bloqueo Bancario",

        condicion="bloqueo_bancario == True",

        accion="EMERGENCY_PROTOCOL",

        prioridad=1,

        severidad=PolicySeverity.CRITICO,

        action_type=PolicyActionType.EMERGENCY

    )

]


# ============================================================
# POLICY ENGINE
# ============================================================

class PolicyEngine:

    VERSION = "2.0.0"

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self):

        self._rules: List[
            PolicyRule
        ] = list(DEFAULT_POLICIES)

    # ========================================================
    # RULE MANAGEMENT
    # ========================================================

    def register_rule(
        self,
        rule: PolicyRule
    ):

        self._rules.append(rule)

    def activate(
        self,
        rule_id: str
    ):

        for rule in self._rules:

            if rule.rule_id == rule_id:

                rule.activa = True

    def deactivate(
        self,
        rule_id: str
    ):

        for rule in self._rules:

            if rule.rule_id == rule_id:

                rule.activa = False

    def remove_rule(
        self,
        rule_id: str
    ):

        self._rules = [

            r for r in self._rules

            if r.rule_id != rule_id

        ]

    # ========================================================
    # SYSTEM RISK
    # ========================================================

    def _calculate_system_risk(
        self,
        triggered: List[TriggeredPolicy]
    ) -> str:

        if any(
            p.severidad == "CRITICO"
            for p in triggered
        ):

            return "CRITICO"

        if any(
            p.severidad == "ALTO"
            for p in triggered
        ):

            return "ALTO"

        if any(
            p.severidad == "MEDIO"
            for p in triggered
        ):

            return "MEDIO"

        return "BAJO"

    # ========================================================
    # EVALUATE POLICIES
    # ========================================================

    def evaluate(
        self,
        data: dict
    ) -> PolicyResult:

        trace_id = str(uuid.uuid4())

        actions = []

        alerts = []

        blocked = []

        emergency = []

        triggered_count = 0

        triggered_policies = []

        active_rules = sorted(

            [
                r for r in self._rules
                if r.activa
            ],

            key=lambda r: (
                r.prioridad,
                r.rule_id
            )

        )

        # ----------------------------------------------------
        # EVALUATE
        # ----------------------------------------------------

        for rule in active_rules:

            try:

                matched = SafeEvaluator.evaluate(

                    rule.condicion,
                    data

                )

                if not matched:

                    continue

                triggered_count += 1

                description = (

                    f"[{rule.rule_id}] "
                    f"{rule.nombre} -> "
                    f"{rule.accion}"

                )

                triggered_policies.append(

                    TriggeredPolicy(

                        rule_id=rule.rule_id,

                        nombre=rule.nombre,

                        accion=rule.accion,

                        severidad=rule.severidad.value,

                        action_type=rule.action_type.value,

                        descripcion=description,

                        timestamp=datetime.utcnow().isoformat()

                    )

                )

                # ALERTS
                if (
                    rule.action_type ==
                    PolicyActionType.ALERT
                ):

                    alerts.append(
                        description
                    )

                # ACTIONS
                elif (
                    rule.action_type ==
                    PolicyActionType.ACTION
                ):

                    actions.append(
                        description
                    )

                # BLOCKS
                elif (
                    rule.action_type ==
                    PolicyActionType.BLOCK
                ):

                    blocked.append(
                        description
                    )

                # EMERGENCY
                elif (
                    rule.action_type ==
                    PolicyActionType.EMERGENCY
                ):

                    emergency.append(
                        description
                    )

            except Exception as e:

                alerts.append(

                    f"[POLICY_ERROR] "
                    f"{rule.rule_id}: "
                    f"{str(e)}"

                )

        # ----------------------------------------------------
        # SYSTEM RISK
        # ----------------------------------------------------

        system_risk = self._calculate_system_risk(
            triggered_policies
        )

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return PolicyResult(

            trace_id=trace_id,

            rules_evaluated=len(
                active_rules
            ),

            rules_triggered=(
                triggered_count
            ),

            actions=actions,

            alerts=alerts,

            blocked_operations=blocked,

            emergency_protocols=emergency,

            triggered_policies=(
                triggered_policies
            ),

            system_risk=system_risk,

            engine_version=self.VERSION

        )

    # ========================================================
    # EXPORT POLICIES
    # ========================================================

    def export_rules(self) -> List[dict]:

        return [

            {

                "rule_id":
                r.rule_id,

                "nombre":
                r.nombre,

                "condicion":
                r.condicion,

                "accion":
                r.accion,

                "prioridad":
                r.prioridad,

                "activa":
                r.activa,

                "version":
                r.version,

                "severidad":
                r.severidad.value,

                "action_type":
                r.action_type.value

            }

            for r in self._rules

        ]
