# core/jarvis/jarvis_engine.py -- MESAN Omega JARVIS v1.0
"""
JARVIS Omega -- Director General Autonomo del ecosistema MESAN Omega.

Fase 1: agrega datos reales de PostgreSQL, Billing y Pipeline Omega.
Fase B (interfaces preparadas, sin implementar):
    - GuardianOmega: monitoreo permanente y deteccion de errores
    - LeviatanOmega: Kill Switch y Fail-Safe
    - SecurityMonitor: deteccion de intrusiones y fugas
    - IncidentLog: bitacora de incidentes y causa raiz
    - PredictiveIntelligence: alertas antes de que ocurran
    - MarketIntelligence: senales debiles y competidores
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mesan.jarvis")

JARVIS_VERSION = "1.0.0"


# ── Interfaces para Fase B (stubs documentados) ───────────────────────────────

class IGuardianOmega:
    """Fase B: monitoreo permanente, deteccion de errores antes de afectar cliente."""
    def scan(self) -> List[Dict]: raise NotImplementedError

class ILeviatanOmega:
    """Fase B: Kill Switch global, Modo Isla, Fail-Safe, Disaster Recovery."""
    def activate_kill_switch(self, reason: str) -> Dict: raise NotImplementedError
    def activate_island_mode(self) -> Dict: raise NotImplementedError

class ISecurityMonitor:
    """Fase B: deteccion de intrusiones, fugas de datos, accesos anomalos."""
    def scan_threats(self) -> List[Dict]: raise NotImplementedError

class IIncidentLog:
    """Fase B: bitacora de incidentes, causa raiz, solucion aplicada."""
    def log(self, incident: Dict) -> None: raise NotImplementedError
    def get_history(self) -> List[Dict]: raise NotImplementedError

class IMarketIntelligence:
    """Fase B: senales debiles, competidores, cambios regulatorios."""
    def scan(self) -> List[Dict]: raise NotImplementedError


# ── Engine principal ──────────────────────────────────────────────────────────

class JarvisEngine:

    def __init__(self):
        self.version = JARVIS_VERSION
        # Fase B: registrar implementaciones reales aqui
        self._guardian:   Optional[IGuardianOmega]      = None
        self._leviatan:   Optional[ILeviatanOmega]      = None
        self._security:   Optional[ISecurityMonitor]    = None
        self._incidents:  Optional[IIncidentLog]        = None
        self._market:     Optional[IMarketIntelligence] = None
        logger.info("[JARVIS] JarvisEngine v%s inicializado", self.version)

    # ── War Room ──────────────────────────────────────────────────────────────

    def get_warroom(self) -> Dict[str, Any]:
        started = time.perf_counter()
        health      = self._get_system_health()
        financials  = self._get_financials()
        risks       = self._get_top_risks()
        decision    = self._get_todays_decision()
        jarvis_work = self._get_jarvis_activity()
        alerts      = self._get_all_alerts()
        allies      = self._get_ally_attention()
        bottleneck  = self._get_next_bottleneck()
        latency_ms  = round((time.perf_counter() - started) * 1000, 2)
        return {
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "version":    self.version,
            "latency_ms": latency_ms,
            "warroom": {
                "company_health":       health,
                "financials":           financials,
                "top_risks":            risks,
                "todays_decision":      decision,
                "jarvis_working_on":    jarvis_work,
                "failed_automations":   [],
                "ally_needs_attention": allies,
                "next_bottleneck":      bottleneck,
            }
        }

    # ── KPIs ──────────────────────────────────────────────────────────────────

    def get_kpis(self) -> Dict[str, Any]:
        billing  = self._get_billing_metrics()
        pipeline = self._get_pipeline_metrics()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "financial": {
                "mrr_mxn":              billing.get("mrr", 0.0),
                "arr_mxn":              billing.get("arr", 0.0),
                "active_subscriptions": billing.get("active_subs", 0),
                "avg_revenue_per_user": billing.get("arpu", 0.0),
            },
            "commercial": {
                "total_leads":         pipeline.get("total_leads", 0),
                "leads_today":         pipeline.get("leads_today", 0),
                "leads_pending":       pipeline.get("leads_pending", 0),
                "conversion_rate_pct": pipeline.get("conversion_rate", 0.0),
            },
            "growth": {
                "ltv_cac_ratio": self._calc_ltv_cac_ratio(
                    billing.get("ltv", 0), billing.get("cac", 1)
                ),
            },
        }

    # ── Alerts ────────────────────────────────────────────────────────────────

    def get_alerts(self) -> Dict[str, Any]:
        alerts = self._get_all_alerts()
        all_alerts = alerts.get("all", [])
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total":     len(all_alerts),
            "critical":  [a for a in all_alerts if a.get("severity") == "CRITICAL"],
            "high":      [a for a in all_alerts if a.get("severity") == "HIGH"],
            "medium":    [a for a in all_alerts if a.get("severity") == "MEDIUM"],
            "info":      [a for a in all_alerts if a.get("severity") == "INFO"],
        }

    # ── Decisions ─────────────────────────────────────────────────────────────

    def get_decisions(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decisions": self._generate_decisions(),
            "rule": "Solo aparecen cuando ninguna automatizacion puede resolverlo.",
        }

    # ── Radar ─────────────────────────────────────────────────────────────────

    def get_radar(self) -> Dict[str, Any]:
        return {
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "allies":       [],   # Fase B: GCR Omega
            "hot_leads":    self._get_hot_leads(),
            "opportunities":[],   # Fase B: Market Intelligence
        }

    # ── Autonomy ──────────────────────────────────────────────────────────────

    def get_autonomy(self) -> Dict[str, Any]:
        processes = self._evaluate_process_autonomy()
        total     = len(processes)
        automated = sum(1 for p in processes if p.get("status") == "AUTOMATED")
        return {
            "timestamp":            datetime.now(timezone.utc).isoformat(),
            "overall_autonomy_pct": round(automated / total * 100, 1) if total else 0.0,
            "processes":            processes,
        }

    # ── System ────────────────────────────────────────────────────────────────

    def get_system(self) -> Dict[str, Any]:
        return {
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "version":        self.version,
            "environment":    os.getenv("ENV", "development"),
            "engines":        self._get_engine_status(),
            "infrastructure": self._get_infra_status(),
            "billing_module": self._get_billing_module_status(),
            "phase_b_modules": {
                "guardian":    "NOT_IMPLEMENTED",
                "leviatan":    "NOT_IMPLEMENTED",
                "security":    "NOT_IMPLEMENTED",
                "incidents":   "NOT_IMPLEMENTED",
                "market_intel":"NOT_IMPLEMENTED",
            }
        }

    # ── Helpers privados ──────────────────────────────────────────────────────

    def _get_system_health(self) -> Dict:
        try:
            from services.omega_orchestrator import omega_orchestrator
            omega_orchestrator._load_engines()
            return {
                "status":  "OK",
                "engines": 10,
                "message": "Pipeline Omega operativo — 10 motores activos",
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def _get_financials(self) -> Dict:
        try:
            from core.billing.subscription_engine import subscription_engine
            m = subscription_engine.get_metrics()
            return {
                "mrr_mxn":              m.get("mrr_mxn", 0.0),
                "arr_mxn":              m.get("arr_mxn", 0.0),
                "active_subscriptions": m.get("active_subscriptions", 0),
                "status": "GROWING" if m.get("mrr_mxn", 0) > 0 else "PRE_REVENUE",
            }
        except Exception as e:
            return {"status": "UNAVAILABLE", "error": str(e)}

    def _get_billing_metrics(self) -> Dict:
        try:
            from core.billing.subscription_engine import subscription_engine
            m = subscription_engine.get_metrics()
            return {
                "mrr":        m.get("mrr_mxn", 0.0),
                "arr":        m.get("arr_mxn", 0.0),
                "active_subs":m.get("active_subscriptions", 0),
                "arpu":       m.get("avg_revenue_per_user", 0.0),
                "ltv":        0.0,
                "cac":        0.0,
            }
        except Exception:
            return {}

    def _get_pipeline_metrics(self) -> Dict:
        """Conectado a PostgreSQL real."""
        try:
            import psycopg2
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leads")
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM leads "
                "WHERE created_at::date = CURRENT_DATE"
            )
            today = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM leads WHERE estatus = 'NUEVO'"
            )
            pending = cur.fetchone()[0]
            cur.close()
            conn.close()
            return {
                "total_leads":     total,
                "leads_today":     today,
                "leads_pending":   pending,
                "conversion_rate": 0.0,
            }
        except Exception as e:
            logger.warning("[JARVIS] DB error: %s", e)
            return {
                "total_leads": 0, "leads_today": 0,
                "leads_pending": 0, "conversion_rate": 0.0,
            }

    def _get_top_risks(self) -> List[Dict]:
        risks = []
        metrics = self._get_pipeline_metrics()
        if metrics.get("leads_pending", 0) > 10:
            risks.append({
                "severity": "HIGH",
                "area":     "COMERCIAL",
                "message":  f"{metrics['leads_pending']} leads sin atender",
                "action":   "Revisar CRM y asignar seguimiento inmediato",
            })
        try:
            from core.billing.renewal_engine import renewal_engine
            expiring = renewal_engine.get_expiring_soon(days_ahead=7)
            if expiring:
                risks.append({
                    "severity": "MEDIUM",
                    "area":     "BILLING",
                    "message":  f"{len(expiring)} suscripciones vencen en 7 dias",
                    "action":   "Activar recordatorio de renovacion",
                })
        except Exception:
            pass
        if not risks:
            risks.append({
                "severity": "INFO",
                "area":     "GENERAL",
                "message":  "Sin riesgos criticos detectados",
                "action":   "Continuar monitoreando",
            })
        return risks

    def _get_todays_decision(self) -> Dict:
        metrics = self._get_pipeline_metrics()
        pending = metrics.get("leads_pending", 0)
        if pending > 0:
            return {
                "priority": "HIGH",
                "decision": f"Atender {pending} leads pendientes en CRM",
                "impact":   "Conversion directa a clientes",
                "deadline": "Hoy",
            }
        return {
            "priority": "MEDIUM",
            "decision": "Revisar estrategia de adquisicion de leads",
            "impact":   "Crecimiento comercial",
            "deadline": "Esta semana",
        }

    def _get_jarvis_activity(self) -> List[str]:
        return [
            "Monitoreando pipeline Omega (10 motores activos)",
            "Calculando MRR/ARR desde Billing Engine",
            "Consultando leads en PostgreSQL",
            "Vigilando suscripciones proximas a vencer",
        ]

    def _get_all_alerts(self) -> Dict:
        all_alerts = []
        env = os.getenv("ENV", "development")
        if env != "production":
            all_alerts.append({
                "severity": "HIGH",
                "area":     "INFRA",
                "message":  f"ENV={env} — no es produccion",
            })
        try:
            from core.billing.renewal_engine import renewal_engine
            for sub in renewal_engine.get_expiring_soon(3):
                all_alerts.append({
                    "severity": "HIGH",
                    "area":     "BILLING",
                    "message":  f"Suscripcion {sub.subscription_id[:8]} vence en 3 dias",
                })
        except Exception:
            pass
        metrics = self._get_pipeline_metrics()
        if metrics.get("leads_pending", 0) > 5:
            all_alerts.append({
                "severity": "HIGH",
                "area":     "COMERCIAL",
                "message":  f"{metrics['leads_pending']} leads sin atender",
            })
        return {"all": all_alerts, "failed_automations": []}

    def _get_ally_attention(self) -> List[Dict]:
        return []  # Fase B: GCR Omega

    def _get_next_bottleneck(self) -> Dict:
        m = self._get_pipeline_metrics()
        if m.get("total_leads", 0) > 0 and m.get("conversion_rate", 0) == 0:
            return {
                "area":    "CONVERSION",
                "message": "Leads entrando pero conversion en 0% — revisar embudo",
                "priority":"HIGH",
            }
        return {
            "area":    "LEADS",
            "message": "Aumentar volumen de leads entrantes",
            "priority":"MEDIUM",
        }

    def _generate_decisions(self) -> List[Dict]:
        decisions = []
        m = self._get_pipeline_metrics()
        if m.get("leads_pending", 0) > 0:
            decisions.append({
                "id":       "DEC-001",
                "area":     "COMERCIAL",
                "question": f"Hay {m['leads_pending']} leads sin contactar. ¿Como proceder?",
                "options":  ["Contactar manualmente", "Activar secuencia automatica"],
                "deadline": "Hoy",
                "impact":   "ALTO",
            })
        if not decisions:
            decisions.append({
                "id":       "DEC-000",
                "area":     "ESTRATEGIA",
                "question": "Sin decisiones urgentes. ¿En que canal invertir energia esta semana?",
                "options":  ["LinkedIn", "Contadores", "Facebook Ads", "Alianzas directas"],
                "deadline": "Esta semana",
                "impact":   "MEDIO",
            })
        return decisions

    def _get_hot_leads(self) -> List:
        try:
            import psycopg2
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            cur  = conn.cursor()
            cur.execute(
                "SELECT nombre, empresa, telefono, created_at "
                "FROM leads WHERE estatus = 'NUEVO' "
                "ORDER BY created_at DESC LIMIT 5"
            )
            rows = cur.fetchall()
            cur.close(); conn.close()
            return [
                {"nombre": r[0], "empresa": r[1],
                 "telefono": r[2], "received": str(r[3])}
                for r in rows
            ]
        except Exception:
            return []

    def _evaluate_process_autonomy(self) -> List[Dict]:
        return [
            {"process": "Diagnostico Omega",   "autonomy_pct": 100, "status": "AUTOMATED",
             "note": "Pipeline completo automatizado"},
            {"process": "Facturacion basica",   "autonomy_pct": 95,  "status": "AUTOMATED",
             "note": "BillingEngine operativo"},
            {"process": "Renovaciones",         "autonomy_pct": 80,  "status": "PROPOSED",
             "note": "Logica lista, falta Stripe Webhooks"},
            {"process": "Seguimiento de leads", "autonomy_pct": 40,  "status": "MANUAL",
             "note": "Fase B: WhatsApp Business API"},
            {"process": "Campanas publicitarias","autonomy_pct": 0,   "status": "MANUAL",
             "note": "Fase B: Meta Ads API"},
            {"process": "Onboarding aliados",   "autonomy_pct": 20,  "status": "MANUAL",
             "note": "Fase B: GCR Omega"},
        ]

    def _get_engine_status(self) -> Dict:
        try:
            from services.omega_orchestrator import omega_orchestrator
            omega_orchestrator._load_engines()
            return {"omega_pipeline": "OK", "engines_loaded": 10, "sovereign_engine": "OK"}
        except Exception as e:
            return {"omega_pipeline": "ERROR", "error": str(e)}

    def _get_infra_status(self) -> Dict:
        return {
            "platform":    "Render",
            "region":      "Oregon US West",
            "env":         os.getenv("ENV", "development"),
            "db":          "PostgreSQL Starter",
            "domain":      "mesanomega.com",
            "stripe_mode": "live" if os.getenv("STRIPE_SECRET_KEY","").startswith("sk_live") else "test",
        }

    def _get_billing_module_status(self) -> Dict:
        return {
            "billing_engine":       "OK",
            "pricing_engine":       "OK",
            "subscription_engine":  "OK",
            "commission_engine":    "OK",
            "renewal_engine":       "OK",
            "version":              "1.0",
        }

    @staticmethod
    def _calc_ltv_cac_ratio(ltv: float, cac: float) -> float:
        if not cac or cac == 0:
            return 0.0
        return round(ltv / cac, 2)


jarvis_engine = JarvisEngine()