# core/jarvis/commercial/sales_pipeline.py -- MESAN Omega Sales Pipeline v1.0
import os, logging
from datetime import datetime, timezone
from collections import defaultdict
logger = logging.getLogger("mesan.commercial.pipeline")

STAGES = ["nuevo","contactado","propuesta","negociacion","cerrado_ganado","cerrado_perdido"]

class SalesPipeline:
    def __init__(self):
        self.version = "1.0.0"
        logger.info("[SalesPipeline] v%s iniciado", self.version)

    def get_pipeline(self):
        leads = self._fetch_leads()
        pipeline = defaultdict(list)
        for lead in leads:
            stage = lead.get("estatus", "nuevo")
            pipeline[stage].append(lead)
        total = len(leads)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_leads": total,
            "stages": {s: len(pipeline.get(s, [])) for s in STAGES},
            "conversion_rate": round(len(pipeline.get("cerrado_ganado", [])) / max(total, 1) * 100, 2),
            "hot_leads": [l for l in leads if l.get("score_comercial", 0) >= 70],
            "warm_leads": [l for l in leads if 45 <= l.get("score_comercial", 0) < 70],
        }

    def get_hot(self):
        leads = self._fetch_leads()
        return [l for l in leads if l.get("estatus") == "nuevo"][:10]

    def _fetch_leads(self):
        try:
            import psycopg
            conn = psycopg.connect(os.getenv("DATABASE_URL"), connect_timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, empresa, correo, telefono, sector, empleados, estatus, created_at FROM leads ORDER BY created_at DESC LIMIT 100")
            rows = cur.fetchall()
            cur.close(); conn.close()
            return [{"id":str(r[0]),"nombre":r[1],"empresa":r[2],"correo":r[3],"telefono":r[4],"sector":r[5],"empleados":r[6],"estatus":r[7] or "nuevo","created_at":str(r[8])} for r in rows]
        except Exception as e:
            logger.error("[Pipeline] DB error: %s", e)
            return []

sales_pipeline = SalesPipeline()