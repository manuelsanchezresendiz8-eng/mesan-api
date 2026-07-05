# core/jarvis/jarvis_ask.py -- MESAN Omega JARVIS Ask v1.0
import logging, os, json, urllib.request
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger("mesan.jarvis.ask")
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MAX_TOKENS = 1024

class JarvisAsk:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

    def ask(self, question: str) -> Dict[str, Any]:
        if not question or not question.strip():
            return {"error": "Pregunta vacia", "answer": None}
        context = self._gather_context()
        prompt  = self._build_prompt(question, context)
        try:
            answer = self._call_claude(prompt)
        except Exception as e:
            logger.error("[JARVIS ASK] Claude error: %s", e)
            answer = self._fallback_answer(question, context)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question":  question,
            "answer":    answer,
            "context_used": {
                "total_leads":   context.get("total_leads", 0),
                "leads_pending": context.get("leads_pending", 0),
                "mrr_mxn":       context.get("mrr_mxn", 0),
                "alerts":        len(context.get("alerts", [])),
                "health_score":  context.get("health_score", 0),
            }
        }

    def _gather_context(self) -> Dict[str, Any]:
        context = {}
        try:
            import psycopg
            conn = psycopg.connect(os.getenv("DATABASE_URL", ""))
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leads")
            context["total_leads"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM leads WHERE estatus = 'nuevo'")
            context["leads_pending"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM leads WHERE estatus = 'cerrado'")
            context["leads_closed"] = cur.fetchone()[0]
            cur.execute("SELECT nombre, telefono, fecha FROM leads WHERE estatus = 'nuevo' ORDER BY fecha DESC LIMIT 5")
            context["recent_leads"] = [{"nombre": r[0], "telefono": r[1], "fecha": str(r[2])} for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            logger.warning("[JARVIS ASK] DB error: %s", e)
            context["total_leads"] = 0
            context["leads_pending"] = 0
            context["leads_closed"] = 0
            context["recent_leads"] = []
        try:
            from core.billing.subscription_engine import subscription_engine
            metrics = subscription_engine.get_metrics()
            context["mrr_mxn"] = metrics.get("mrr_mxn", 0)
            context["arr_mxn"] = metrics.get("arr_mxn", 0)
            context["active_subscriptions"] = metrics.get("active_subscriptions", 0)
        except Exception:
            context["mrr_mxn"] = 0
            context["arr_mxn"] = 0
            context["active_subscriptions"] = 0
        try:
            from core.jarvis.guardian_engine import guardian_engine
            report = guardian_engine.execute()
            context["health_score"]  = report.overall_score
            context["health_status"] = report.status
            context["alerts"]        = report.alerts
            context["incidents"]     = len(report.incidents)
        except Exception:
            context["health_score"]  = 0
            context["health_status"] = "UNKNOWN"
            context["alerts"]        = []
            context["incidents"]     = 0
        return context

    def _build_prompt(self, question: str, ctx: Dict) -> str:
        alerts_str = "\n".join(f"  - [{a.get('severity','?')}] {a.get('message','')}" for a in ctx.get("alerts", [])[:3]) or "  - Sin alertas activas"
        leads_str  = "\n".join(f"  - {l['nombre']} | {l['telefono']} | {l['fecha']}" for l in ctx.get("recent_leads", [])) or "  - Sin leads recientes"
        return f"""Eres JARVIS Omega, el Director General Autonomo de MESAN Omega.
MESAN Omega es una plataforma SaaS de diagnostico de riesgo empresarial para PyMEs mexicanas.
ESTADO ACTUAL ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}):
COMERCIAL: Leads totales: {ctx.get('total_leads',0)} | Sin atender: {ctx.get('leads_pending',0)} | Cerrados: {ctx.get('leads_closed',0)}
LEADS SIN ATENDER:\n{leads_str}
FINANCIERO: MRR: ${ctx.get('mrr_mxn',0):,.0f} MXN | Clientes activos: {ctx.get('active_subscriptions',0)}
INFRAESTRUCTURA: Health Score: {ctx.get('health_score',0):.1f}/100 | Estado: {ctx.get('health_status','UNKNOWN')} | Incidentes: {ctx.get('incidents',0)}
ALERTAS:\n{alerts_str}
PREGUNTA: {question}
Responde directo, ejecutivo y orientado a accion. Maximo 3 parrafos. Usa los datos reales. Habla en espanol."""

    def _call_claude(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        payload = json.dumps({"model": CLAUDE_MODEL, "max_tokens": MAX_TOKENS, "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
        req = urllib.request.Request(CLAUDE_API_URL, data=payload, headers={"Content-Type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["content"][0]["text"]

    def _fallback_answer(self, question: str, ctx: Dict) -> str:
        return f"JARVIS detecta {ctx.get('leads_pending',0)} leads sin atender y Health Score de {ctx.get('health_score',0):.0f}/100. Revisa el War Room. (Motor Claude temporalmente no disponible)"

jarvis_ask = JarvisAsk()
