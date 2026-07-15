# utils/pdf_generator.py -- MESAN Omega PDF Generator v2.3
"""
Genera el reporte PDF del diagnostico Omega directamente desde OmegaResponse.
Sin logica de negocio -- solo serializa lo que ya calculo el pipeline.

v2.3: rediseno comercial:
      - Caja RIESGO TOTAL en primera pagina (score + nivel + ESI + exposicion grande
        + mensaje de urgencia con dias del predictivo)
      - Impacto potencial estimado en MXN (suma de riesgos predictivos)
      - Seccion ENTORNO EMPRESARIAL (datos reales si vienen; monitoreo activo si no)
      - Seccion PRIORIDAD COMERCIAL (sales_priority del pipeline + tendencia predictiva)
      - Placeholder JARVIS Executive Briefing (upsell Premium)
      - Soberania Digital: sin nodos ya no muestra "0", muestra pitch de Guardian Enterprise
v2.2: fix fpdf2 multi_cells consecutivos (_mc resetea X) + DSI tolerante a None
v2.1: seccion ANALISIS PREDICTIVO + fix precedencia en acciones
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
        predictive   = getattr(omega_response, "predictive", None)
        sales_prio   = getattr(omega_response, "sales_priority", "") or ""
        war_priority = getattr(omega_response, "war_room_priority", "") or ""
        market       = getattr(omega_response, "market_intelligence", None)
    elif resultado is not None:
        score        = resultado.get("omega_score", resultado.get("score", 0)) or 0
        esi          = resultado.get("esi", 0) or 0
        nivel        = resultado.get("nivel", _score_to_nivel(score))
        exposure     = resultado.get("exposure_mxn", 0) or 0
        remediation  = resultado.get("remediation", {}) or {}
        sovereignty  = resultado.get("digital_sovereignty", {}) or {}
        summary      = resultado.get("report", "") or ""
        predictive   = resultado.get("predictive", None)
        sales_prio   = resultado.get("sales_priority", "") or ""
        war_priority = resultado.get("war_room_priority", "") or ""
        market       = resultado.get("market_intelligence", None)
    else:
        raise ValueError("Se requiere omega_response o resultado")

    # Acciones (FIX v2.1: parentesis explicitos)
    plan          = remediation.get("plan_remediacion", {})
    acciones_hoy  = plan.get("acciones_inmediatas") or (resultado.get("acciones_hoy", []) if resultado else [])
    acciones_72h  = plan.get("acciones_30_dias")    or (resultado.get("acciones_72h", []) if resultado else [])
    acciones_7d   = plan.get("acciones_60_dias")    or (resultado.get("acciones_7d", [])  if resultado else [])

    # Bloque predictivo (Phase 1) -- {version, result: {...}}
    pred_res = None
    pred_version = "4.1"
    if isinstance(predictive, dict):
        pred_version = predictive.get("version", "4.1")
        pred_res = predictive.get("result") if isinstance(predictive.get("result"), dict) else None

    pred_dias    = (pred_res or {}).get("dias_supervivencia") if pred_res else None
    pred_riesgos = (pred_res or {}).get("riesgos", []) or []
    impacto_total = sum(
        (r.get("impacto_estimado", 0) or 0)
        for r in pred_riesgos if isinstance(r, dict)
    )

    fecha = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    # -- Construir PDF --------------------------------------------------------
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Colores
    AZUL    = (26, 58, 92)
    AZUL_M  = (46, 109, 164)
    GRIS    = (85, 85, 85)
    GRIS_C  = (130, 130, 130)
    BLANCO  = (255, 255, 255)
    ROJO    = (200, 50, 50)
    VERDE   = (34, 139, 34)
    AMARILLO= (180, 130, 0)

    def color_nivel(n):
        if n in ("BAJO",):     return VERDE
        if n in ("MEDIO",):    return AMARILLO
        return ROJO

    # -- Header ----------------------------------------------------------------
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

    # -- Datos de la empresa ----------------------------------------------------
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 8, empresa, ln=True)
    if nombre_contacto:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GRIS)
        pdf.cell(0, 6, f"Contacto: {nombre_contacto}", ln=True)
    pdf.ln(4)

    # -- Caja RIESGO TOTAL (v2.3: lo primero que ve el cliente) -------------------
    box_y = pdf.get_y()
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, box_y, 190, 46, "F")

    pdf.set_xy(14, box_y + 3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 7, "RIESGO TOTAL", ln=True)

    pdf.set_xy(14, box_y + 11)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*color_nivel(nivel))
    pdf.cell(34, 11, f"{score:.0f}", ln=False)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 11, f"/ 100    Nivel: {nivel}    ESI: {esi:.0f}/100", ln=True)

    pdf.set_xy(14, box_y + 23)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(58, 8, "Exposicion estimada:", ln=False)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*ROJO)
    pdf.cell(0, 8, f"${exposure:,.0f} MXN", ln=True)

    pdf.set_xy(14, box_y + 33)
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.set_text_color(*GRIS)
    if pred_dias:
        urg_txt = (f"Si no se actua, la empresa tiene alta probabilidad de incrementar "
                   f"su exposicion durante los proximos {pred_dias} dias.")
    else:
        urg_txt = ("Si no se actua, la empresa tiene alta probabilidad de incrementar "
                   "su exposicion en el corto plazo.")
    pdf.multi_cell(182, 5, urg_txt)
    pdf.set_y(box_y + 46 + 5)

    # -- Secciones ------------------------------------------------------------------
    def seccion(titulo):
        pdf.set_x(pdf.l_margin)
        pdf.set_fill_color(*AZUL_M)
        pdf.set_text_color(*BLANCO)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"  {titulo}", ln=True, fill=True)
        pdf.set_text_color(*GRIS)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)

    def _mc(txt, h=6):
        """multi_cell seguro: fpdf2 deja X en el margen derecho tras cada
        multi_cell; sin este reset, el siguiente truena por falta de ancho."""
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, h, txt)

    # -- Resumen ejecutivo -------------------------------------------------------
    if summary:
        seccion("RESUMEN EJECUTIVO")
        clean = summary.replace("**", "").replace("##", "").replace("#", "")
        for line in clean.split("\n"):
            line = line.strip()
            if line:
                _mc(line)
        pdf.ln(4)

    # -- Analisis Predictivo (Phase 1 -- Predictive Defense v4.1) -------------------
    if pred_res:
        p_score  = pred_res.get("score", 0) or 0
        p_nivel  = pred_res.get("nivel", "") or ""
        p_dias   = pred_res.get("dias_supervivencia", 0) or 0
        p_conf   = pred_res.get("confianza", 0) or 0
        p_cascadas = pred_res.get("cascadas", []) or []
        p_resumen  = pred_res.get("resumen_ejecutivo", "") or ""

        seccion(f"ANALISIS PREDICTIVO -- DEFENSA ANTICIPADA (v{pred_version})")

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*color_nivel(p_nivel))
        pdf.cell(0, 7, f"  Riesgo predictivo: {p_score}/100 ({p_nivel})", ln=True)

        # v2.3: el director piensa en dinero -- impacto potencial en MXN
        if impacto_total > 0:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*GRIS)
            pdf.cell(56, 7, "  Impacto potencial estimado:", ln=False)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*ROJO)
            pdf.cell(0, 7, f"${impacto_total:,.0f} MXN", ln=True)

        pdf.set_text_color(*GRIS)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"  Dias de estabilidad financiera estimados: {p_dias}   |   Confianza del modelo: {p_conf}%", ln=True)
        pdf.ln(2)

        if pred_riesgos:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "  Riesgos detectados antes de que ocurran:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for r in pred_riesgos[:5]:
                if not isinstance(r, dict):
                    continue
                nombre  = r.get("nombre", "")
                cat     = r.get("categoria", "")
                impacto = r.get("impacto_estimado", 0) or 0
                accion  = r.get("accion_critica", "")
                _mc(f"  > {nombre} [{cat}]  ~${impacto:,.0f} MXN  ->  {accion}")
            pdf.ln(2)

        if p_cascadas:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "  Cascadas de colapso identificadas:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for c in p_cascadas[:4]:
                _mc(f"  > {c}")
            pdf.ln(2)

        if p_resumen:
            pdf.set_font("Helvetica", "I", 10)
            _mc(f"  {p_resumen}")
            pdf.set_font("Helvetica", "", 10)
        pdf.ln(3)

    # -- Entorno Empresarial (v2.3) ----------------------------------------------
    # Renderiza datos reales de Market Intelligence si vienen en la respuesta.
    # Sin datos, muestra el monitoreo activo (sin inventar scores).
    seccion("ENTORNO EMPRESARIAL -- MARKET INTELLIGENCE")
    if isinstance(market, dict) and market:
        m_score  = market.get("market_score")
        m_sector = market.get("sector", "") or ""
        m_presion= market.get("presion_regulatoria", "") or ""
        m_cambios= market.get("cambios_recientes", []) or []
        if isinstance(m_score, (int, float)):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, f"  Market Score: {m_score:.0f}/100", ln=True)
            pdf.set_font("Helvetica", "", 10)
        if m_sector:
            pdf.cell(0, 6, f"  Sector: {m_sector}", ln=True)
        if m_presion:
            pdf.cell(0, 6, f"  Nivel de presion regulatoria: {m_presion}", ln=True)
        if m_cambios:
            pdf.cell(0, 6, "  Cambios regulatorios recientes:", ln=True)
            for c in m_cambios[:6]:
                _mc(f"  > {c}")
    else:
        _mc("  MESAN monitorea de forma continua el entorno regulatorio que afecta "
            "a su empresa: REPSE, UMA, CFDI, SAT, IMSS y STPS.")
        _mc("  Las alertas regulatorias personalizadas por sector se incluyen en el "
            "monitoreo activo de su cuenta.")
    pdf.ln(3)

    # -- Prioridad Comercial (v2.3) -------------------------------------------------
    if sales_prio or pred_res:
        seccion("PRIORIDAD DE ATENCION")
        if sales_prio:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, f"  Clasificacion: {sales_prio}", ln=True)
            pdf.set_font("Helvetica", "", 10)
        if pred_res:
            tendencia = pred_res.get("tendencia", "") or ""
            p_score   = pred_res.get("score", 0) or 0
            deterioro = "Alta" if (p_score >= 65 or tendencia == "ASCENDENTE") else \
                        "Media" if p_score >= 40 else "Baja"
            pdf.cell(0, 6, f"  Probabilidad de deterioro: {deterioro}" +
                     (f"   |   Tendencia: {tendencia}" if tendencia else ""), ln=True)
        if war_priority and war_priority not in ("MONITOREO", "NONE"):
            pdf.cell(0, 6, f"  Urgencia: intervencion en ventana {war_priority}.", ln=True)
        elif pred_dias and pred_dias <= 45:
            pdf.cell(0, 6, f"  Urgencia: intervencion en menos de {min(pred_dias, 30)} dias.", ln=True)
        else:
            pdf.cell(0, 6, "  Urgencia: monitoreo preventivo con seguimiento mensual.", ln=True)
        pdf.ln(3)

    # -- Acciones ---------------------------------------------------------------------
    if acciones_hoy:
        seccion("ACCIONES INMEDIATAS (HOY)")
        for a in acciones_hoy[:5]:
            _mc(f"  > {a}")
        pdf.ln(3)

    if acciones_72h:
        seccion("PROXIMAS 72 HORAS")
        for a in acciones_72h[:5]:
            _mc(f"  > {a}")
        pdf.ln(3)

    if acciones_7d:
        seccion("ESTRATEGIA SEMANA 1")
        for a in acciones_7d[:5]:
            _mc(f"  > {a}")
        pdf.ln(3)

    # -- JARVIS Executive Briefing (v2.3: placeholder Premium) --------------------------
    seccion("JARVIS EXECUTIVE BRIEFING")
    pdf.set_font("Helvetica", "I", 10)
    _mc("  Briefing ejecutivo diario con decisiones priorizadas, responsables y plazos.")
    _mc("  Disponible para clientes MESAN Premium.")
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(3)

    # -- Soberania / Infraestructura Digital (v2.3) ---------------------------------------
    dsi_raw = sovereignty.get("index") if isinstance(sovereignty, dict) else None
    if isinstance(dsi_raw, (int, float)) and dsi_raw > 0:
        dlevel = sovereignty.get("level", "") or ""
        rec    = sovereignty.get("recommendation", "") or ""
        seccion("SOBERANIA DIGITAL (Motor Omega #10)")
        pdf.cell(0, 6, f"  Indice DSI: {float(dsi_raw):.1f}/100   Nivel: {dlevel}", ln=True)
        if rec:
            _mc(f"  {rec}")
        pdf.ln(3)
    else:
        # Sin nodos registrados: no mostrar un 0 que confunde -- mostrar el siguiente paso
        seccion("INFRAESTRUCTURA DIGITAL")
        _mc("  Pendiente de evaluacion.")
        _mc("  Este indicador estara disponible al activar MESAN Guardian Omega Enterprise.")
        pdf.ln(3)

    # -- Footer -----------------------------------------------------------------------------
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