# services/executive_narrative_generator.py -- MESAN Omega v1.1
from datetime import datetime
from typing import Dict, Any, List

class ExecutiveNarrativeGenerator:

    def __init__(self): pass

    def _safe(self, value, default):
        return default if value is None else value

    def generar(self, resultado_engine: Dict[str, Any]) -> str:
        riesgo = self._safe(resultado_engine.get("nivel"), "MEDIO")
        score  = self._safe(resultado_engine.get("score"), 50)
        dias   = self._safe(resultado_engine.get("dias_supervivencia"), 30)
        flujo  = self._safe(resultado_engine.get("flujo_operativo"), 0)
        dscr   = self._safe(resultado_engine.get("dscr"), 1.0)

        acciones_hoy = resultado_engine.get("acciones_hoy") or []
        acciones_72h = resultado_engine.get("acciones_72h") or []
        acciones_7d  = resultado_engine.get("acciones_7d") or []

        resumen = (
            "## 7. DECISION CEO\n\n"
            f"La organizacion presenta un escenario {riesgo} con score operativo de {score}% "
            f"y ventana de supervivencia financiera de {dias} dias.\n\n"
            f"Flujo operativo estimado: ${flujo:,.0f} MXN | DSCR: {dscr}\n\n"
            "Prioridad absoluta: estabilizar liquidez, proteger operacion critica y bloquear escalamiento fiscal/laboral.\n"
        )

        plan_30 = (
            "### Plan de Accion 30 Dias\n\n"
            "**S1** Reestructuracion urgente de deuda bancaria\n"
            "**S2** Recorte de gastos no esenciales\n"
            "**S3** Negociacion con acreedores y flujo prioritario\n"
            "**S4** Estabilizacion de caja y control operativo\n"
        )

        pilares = (
            "### Modulos de Valor MESAN Omega\n\n"
            "**Blindaje Fiscal** -- Proteccion ante SAT, IMSS e INFONAVIT\n"
            "**Blindaje Laboral** -- Cumplimiento REPSE, STPS y contratos\n"
            "**Inteligencia** -- Modelado predictivo de flujos\n"
            "**Soberania** -- Infraestructura privada y control de activos\n"
        )

        def fmt(lst: List[str]) -> str:
            return "\n".join(f"- {x}" for x in lst[:4]) if lst else "- Sin acciones definidas"

        footer = (
            "\n---\n\n"
            "### Acciones Prioridad Inmediata\n"
            f"{fmt(acciones_hoy)}\n\n"
            "### Acciones Proximas 72H\n"
            f"{fmt(acciones_72h)}\n\n"
            "### Estrategia Semana 1\n"
            f"{fmt(acciones_7d)}\n\n"
            "---\n"
            f"MESAN OMEGA (c) {datetime.now().year}\n"
        )

        return resumen + plan_30 + pilares + footer
