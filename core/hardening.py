# core/hardening.py v1.0
import os,gc
from datetime import datetime,timezone
from pathlib import Path
REQUIRED=["DATABASE_URL","STRIPE_SECRET_KEY"]
class Hardening:
    def __init__(self):self.version="1.0.0"
    def validate_env(self):
        missing=[v for v in REQUIRED if not os.getenv(v)]
        return{"status":"OK" if not missing else "CRITICAL","missing":missing}
    def cleanup_logs(self,max_mb=50):
        log_dir=Path(__file__).resolve().parent.parent/"logs"
        if not log_dir.exists():return{"status":"NO_LOGS"}
        cleaned=0
        for f in log_dir.glob("*.log"):
            if f.stat().st_size/(1024*1024)>max_mb:f.write_text("");cleaned+=1
        return{"cleaned":cleaned}
    def full_check(self):
        deps={}
        try:
            import psycopg;conn=psycopg.connect(os.getenv("DATABASE_URL",""),connect_timeout=5);conn.close();deps["postgresql"]="OK"
        except:deps["postgresql"]="OFFLINE"
        deps["stripe"]="OK" if os.getenv("STRIPE_SECRET_KEY") else "MISSING"
        return{"timestamp":datetime.now(timezone.utc).isoformat(),"version":self.version,"env":self.validate_env(),"deps":deps}
hardening=Hardening()