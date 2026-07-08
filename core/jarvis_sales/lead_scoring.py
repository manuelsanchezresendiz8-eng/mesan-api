# core/jarvis_sales/lead_scoring.py -- MESAN Omega JARVIS Sales v1.0
from __future__ import annotations
import logging
from core.jarvis_sales.models import LeadProfile, LeadScore, LeadPriority
from core.jarvis_sales.sales_rules import sales_rules
logger = logging.getLogger("mesan.sales.scoring")

class LeadScoring:
    def score(self, profile: LeadProfile) -> LeadScore:
        w = sales_rules.weights
        d_tamano      = sales_rules.get_tamano_score(profile.empleados)
        d_sector      = sales_rules.get_sector_score(profile.sector)
        d_riesgo      = sales_rules.get_riesgo_score(profile.nivel_riesgo or "", profile.omega_score)
        d_potencial   = sales_rules.get_potencial_score(profile.impacto_estimado, profile.ingresos_estimados)
        d_interaccion = sales_rules.get_interaccion_score(profile.contactos_previos, profile.dias_sin_contacto)
        d_diagnostico = sales_rules.get_diagnostico_score(profile.diagnostico_hecho)
        breakdown = {
            "tamano_empresa":     d_tamano      * w["tamano_empresa"],
            "sector_priority":    d_sector      * w["sector_priority"],
            "riesgo_detectado":   d_riesgo      * w["riesgo_detectado"],
            "potencial_economico":d_potencial   * w["potencial_economico"],
            "interaccion_previa": d_interaccion * w["interaccion_previa"],
            "diagnostico_hecho":  d_diagnostico * w["diagnostico_hecho"],
        }
        final = max(0.0, min(100.0, sum(breakdown.values())))
        priority = LeadPriority(sales_rules.classify_priority(final))
        confidence = min(100.0, (
            (30.0 if profile.empleados > 0 else 0) +
            (30.0 if profile.diagnostico_hecho else 0) +
            (20.0 if profile.nivel_riesgo else 0) +
            (20.0 if profile.impacto_estimado > 0 else 0)
        ))
        temperature = sales_rules.classify_temperature(final)
        reasons = []
        if d_riesgo >= 75: reasons.append(f"riesgo {profile.nivel_riesgo or 'ALTO'}")
        if d_potencial >= 60: reasons.append(f"impacto ${profile.impacto_estimado:,.0f} MXN")
        if profile.diagnostico_hecho: reasons.append("diagnostico realizado")
        if d_tamano >= 70: reasons.append(f"{profile.empleados} empleados")
        if profile.dias_sin_contacto > 7: reasons.append(f"{profile.dias_sin_contacto} dias sin contacto")
        reason = f"Score {final:.0f}/100: {', '.join(reasons) or 'perfil basico'}"
        logger.info("[Scoring] %s score=%.1f priority=%s", profile.lead_id, final, priority.value)
        return LeadScore(lead_id=profile.lead_id, lead_score=round(final,1),
                         priority=priority, reason=reason, breakdown=breakdown,
                         confidence=round(confidence,1), temperature=temperature)

lead_scoring = LeadScoring()
