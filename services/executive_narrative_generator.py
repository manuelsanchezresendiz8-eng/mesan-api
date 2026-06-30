# services/executive_narrative_generator.py -- MESAN Omega v1.2
"""
CHANGELOG v1.2 -- Motor Omega #10 (Sovereign Continuity Engine):
    - Agregado _generar_explicacion_dsi() que convierte
      dimension_contribution en narrativa ejecutiva para CEO.
    - generar() ahora incluye seccion de Soberania Digital si
      digital_sovereignty esta presente en el resultado.
    - Compatibilidad total hacia atras: si digital_sovereignty
      no existe, el reporte es identico a v1.1.
"""

from datetime import datetime
from typing import Any, Dict, List


class ExecutiveNarrativeGenerator:

    def __init__(self): pass

    def _safe(self, value, default):
        return default if value is None else value

    def _generar_explicacion_dsi(self, resultado: Dict[str, Any]) -> str:
        """
        Convierte dimension_contribution del Motor Omega #10 en
        narrativa ejecutiva comprensible para un CEO.
        """
        digital      = resultado.get("digital_sovereignty") or {}
        contribution = digital.get("dimension_contribution") or {}
        dsi_index    = digital.get("index")
        dsi_level    = digital.get("level", "")
        recommendation = digital.get("recommendation", "")

        if not contribution or dsi_index is None:
            return ""

        dim_labels = {
            "geopolitical_risk":   "el riesgo geopolitico del pais donde opera la infraestructura",
            "regulatory_risk":     "la incertidumbre regulatoria del entorno normativo",
            "availability":        "la disponibilidad operativa de la infraestructura",
            "provider_dependency": "la dependencia de proveedores tecnologicos externos",
            "cyber_risk":          "la exposicion al riesgo cibernetico",
            "latency":             "la latencia de los sistemas criticos",
        }

        positivos = sorted(
            [(k, v) for k, v in contribution.items() if v > 0],
            key=lambda x: x[1], reverse=True,
        )
        negativos = sorted(
            [(k, v) for k, v in contribution.items() if v < 0],
            key=lambda x: x[1],
        )

        lineas = [
            f"### Soberania Digital -- DSI: {dsi_index:.1f}/100 ({dsi_level})\n"
        ]

        if negativos:
            lineas.append("**Factores que reducen la soberania digital:**")
            for dim, val in negativos[:2]:
                label = dim_labels.get(dim, dim)
                lineas.append(
                    f"- {label.capitalize()} redujo el indice en {abs(val):.1f} puntos."
                )

        if positivos:
            lineas.append("\n**Factores que fortalecen la soberania digital:**")
            for dim, val in positivos[:2]:
                label = dim_labels.get(dim, dim)
                lineas.append(
                    f"- {label.capitalize()} aporto +{val:.1f} puntos al indice."
                )

        if recommendation:
            lineas.append(f"\n**Recomendacion:** {recommendation}")

        warnings = digital.get("warnings", [])
        if warnings:
            lineas.append("\n**Alertas de soberania:**")
            for w in warnings[:3]:
                lineas.append(f"- {w}")

        return "\n".join(lineas) + "\n"

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
            "Prioridad absoluta: estabilizar liquidez, proteger operacion critica "
            "y bloquear escalamiento fiscal/laboral.\n"
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

        dsi_section = self._generar_explicacion_dsi(resultado_engine)

        if dsi_section:
            return resumen + plan_30 + pilares + dsi_section + footer
        return resumen + plan_30 + pilares + footer