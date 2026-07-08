# utils/pdf_generator.py -- MESAN Omega PDF Generator v2.0
"""
Genera el reporte PDF del diagnostico Omega directamente desde OmegaResponse.
Sin logica de negocio — solo serializa lo que ya calculo el pipeline.

v2.0: conectado a OmegaResponse (10 motores + SCE + Billing)
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("mesan.pdf")


def generar_pdf_omega(
    omega_response=None,
    resultado: Optional[Dict[str, Any]] = None,
    empresa: str = "Empresa",
    nombre_contacto: str = "",
) -> bytes:
    """
    Genera el PDF del diagnostico Omega.

    Acepta:
        - omega_response: OmegaResponse completo del pipeline
        - resultado: dict del endpoint /execute (compatibilidad)
        - empresa: nombre de la empresa
        - nombre_contacto: nombre del contacto

    Retorna bytes del PDF listo para enviar o guardar.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise RuntimeError("fpdf2 no instalado. Agregar fpdf2==2.7.9 a requirements.txt")

    # Extraer datos del OmegaResponse o del dict resultado
    if omega_response is not None:
        score        = getattr(omega_response, "omega_score", 0) or 0
        esi          = getattr(omega_response, "enterprise_survival_index", 0) or 0
        nivel        = _score_to_nivel(score)
        exposure     = getattr(omega_response, "total_exposure_mxn", 0) or 0
        remediation  = getattr(omega_response, "remediation", {}) or {}
        sovereignty  = getattr(omega_response, "digital_sovereignty", {}) or {}
        summary      = getattr(omega_response, "executive_summary", "") or ""
    elif resultado is not None:
        score        = resultado.get("omega_score", resultado.get("score", 0)) or 0
        esi          = resultado.get("esi", 0) or 0
        nivel        = resultado.get("nivel", _score_to_nivel(score))
        exposure     = resultado.get("exposure_mxn", 0) or 0
        remediation  = resultado.get("remediation", {}) or {}
        sovereignty  = resultado.get("digital_sovereignty", {}) or {}
        summary      = resultado.get("report", "") or ""
    else:
        raise ValueError("Se requiere omega_response o resultado")

    # Acciones
    plan          = remediation.get("plan_remediacion", {})
    acciones_hoy  = plan.get("acciones_inmediatas") or resultado.get("acciones_hoy", []) if resultado else []
    acciones_72h  = plan.get("acciones_30_dias")    or resultado.get("acciones_72h", []) if resultado else []
    acciones_7d   = plan.get("acciones_60_dias")    or resultado.get("acciones_7d", [])  if resultado else []

    fecha = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    # ── Construir PDF ─────────────────────────────────────────────────────────
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Colores
    AZUL    = (26, 58, 92)
    AZUL_M  = (46, 109, 164)
    GRIS    = (85, 85, 85)
    BLANCO  = (255, 255, 255)
    ROJO    = (200, 50, 50)
    VERDE   = (34, 139, 34)
    AMARILLO= (180, 130, 0)

    def color_nivel(n):
        if n in ("BAJO",):     return VERDE
        if n in ("MEDIO",):    return AMARILLO
        return ROJO

    # ── Header ────────────────────────────────────────────────────────────────
    pdf.set_fill_color(*AZUL)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(*BLANCO)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(10, 6)
    pdf.cell(0, 10, "MESAN  Diagnostico Estrategico", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(10)
    pdf.cell(0, 6, f"Generado: {fecha}", ln=True)

    pdf.set_text_color(*GRIS)
    pdf.ln(8)

    # ── Datos de la empresa ───────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 8, empresa, ln=True)
    if nombre_contacto:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GRIS)
        pdf.cell(0, 6, f"Contacto: {nombre_contacto}", ln=True)
    pdf.ln(4)

    # ── Score principal ───────────────────────────────────────────────────────
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 190, 28, "F")
    pdf.set_xy(12, pdf.get_y() + 3)

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*color_nivel(nivel))
    pdf.cell(40, 12, f"{score:.0f}", ln=False)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 12, f"/ 100   Nivel de Riesgo: {nivel}   ESI: {esi:.0f}/100", ln=True)

    pdf.set_xy(12, pdf.get_y())
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Exposicion economica estimada: ${exposure:,.0f} MXN", ln=True)
    pdf.ln(6)

    # ── Linea divisoria ───────────────────────────────────────────────────────
    def seccion(titulo):
        pdf.set_fill_color(*AZUL_M)
        pdf.set_text_color(*BLANCO)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"  {titulo}", ln=True, fill=True)
        pdf.set_text_color(*GRIS)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)

    # ── Resumen ejecutivo ─────────────────────────────────────────────────────
    if summary:
        seccion("RESUMEN EJECUTIVO")
        # Limpiar markdown
        clean = summary.replace("**", "").replace("##", "").replace("#", "")
        for line in clean.split("\n"):
            line = line.strip()
            if line:
                pdf.multi_cell(0, 6, line)
        pdf.ln(4)

    # ── Acciones ──────────────────────────────────────────────────────────────
    if acciones_hoy:
        seccion("ACCIONES INMEDIATAS (HOY)")
        for a in acciones_hoy[:5]:
            pdf.multi_cell(0, 6, f"  > {a}")
        pdf.ln(3)

    if acciones_72h:
        seccion("PROXIMAS 72 HORAS")
        for a in acciones_72h[:5]:
            pdf.multi_cell(0, 6, f"  > {a}")
        pdf.ln(3)

    if acciones_7d:
        seccion("ESTRATEGIA SEMANA 1")
        for a in acciones_7d[:5]:
            pdf.multi_cell(0, 6, f"  > {a}")
        pdf.ln(3)

    # ── Soberania digital ─────────────────────────────────────────────────────
    if sovereignty:
        dsi   = sovereignty.get("index", 0)
        dlevel= sovereignty.get("level", "")
        rec   = sovereignty.get("recommendation", "")
        seccion("SOBERANIA DIGITAL (Motor Omega #10)")
        pdf.cell(0, 6, f"  Indice DSI: {dsi:.1f}/100   Nivel: {dlevel}", ln=True)
        if rec:
            pdf.multi_cell(0, 6, f"  {rec}")
        pdf.ln(3)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_fill_color(*AZUL)
    pdf.set_text_color(*BLANCO)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(0, 275)
    pdf.cell(0, 12, "  MESAN Omega  |  mesanomega.com  |  Diagnostico confidencial", fill=True)

    return bytes(pdf.output())


def _score_to_nivel(score: float) -> str:
    if score >= 80: return "BAJO"
    if score >= 65: return "MEDIO"
    if score >= 50: return "ALTO"
    if score >= 35: return "CRITICO"
    return "EXTREMO"

    
