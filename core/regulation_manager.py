# core/regulation_manager.py -- MESAN Omega Enterprise Regulation Manager v1.1
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json, logging, os

logger = logging.getLogger("mesan.regulations")

class RegulationManager:
    VERSION = "1.1.0"
    DEFAULT_RULESET = "GLOBAL_2026"

    def __init__(self, config_path: str = "config/regulations"):
        self.config_path = Path(config_path)
        self._active_rulesets: Dict[str,str] = {}
        self._cache: Dict[str,Dict[str,Any]] = {}
        self._load_active_rulesets()

    def _load_active_rulesets(self):
        self._active_rulesets = {
            "SAT":       os.getenv("MESAN_SAT_VERSION",       "sat_2026_05"),
            "IMSS":      os.getenv("MESAN_IMSS_VERSION",      "imss_2026_04"),
            "REPSE":     os.getenv("MESAN_REPSE_VERSION",     "repse_2025_11"),
            "LABORAL":   os.getenv("MESAN_LABORAL_VERSION",   "lft_2026_02"),
            "INFONAVIT": os.getenv("MESAN_INFONAVIT_VERSION", "infonavit_2026_01")
        }

    def get_active_ruleset(self, regulator: str) -> str:
        return self._active_rulesets.get(regulator.upper(), self.DEFAULT_RULESET)

    def activate_ruleset(self, regulator: str, version: str):
        self._active_rulesets[regulator.upper()] = version
        logger.warning(f"[REGULATIONS] {regulator.upper()} switched to {version}")

    def get_all_versions(self) -> dict:
        return dict(self._active_rulesets)

    def load_ruleset(self, regulator: str, version: Optional[str] = None) -> Dict[str,Any]:
        regulator = regulator.upper()
        version   = version or self.get_active_ruleset(regulator)
        cache_key = f"{regulator}:{version}"
        if cache_key in self._cache: return self._cache[cache_key]
        file_path = self.config_path / regulator.lower() / f"{version}.json"
        if not file_path.exists():
            logger.error(f"[REGULATIONS] Missing ruleset: {file_path}")
            return {"error": "RULESET_NOT_FOUND", "regulator": regulator, "version": version}
        with open(file_path, "r", encoding="utf-8") as f:
            rules = json.load(f)
        self._cache[cache_key] = rules
        return rules

    def validate_ruleset(self, rules: Dict[str,Any]) -> dict:
        required = ["version","valid_from","rules"]
        missing = [k for k in required if k not in rules]
        return {"valid": len(missing)==0, "missing_fields": missing}

    def compare_rulesets(self, regulator: str, version_a: str, version_b: str) -> dict:
        a = self.load_ruleset(regulator, version_a)
        b = self.load_ruleset(regulator, version_b)
        if "error" in a or "error" in b:
            return {"success": False, "error": "RULESET_LOAD_FAILED"}
        ra=a.get("rules",{}); rb=b.get("rules",{})
        added=set(rb)-set(ra); removed=set(ra)-set(rb)
        changed={k for k in ra if k in rb and ra[k]!=rb[k]}
        return {"success":True,"regulator":regulator,"version_a":version_a,"version_b":version_b,
                "added":list(added),"removed":list(removed),"changed":list(changed),
                "breaking_changes":bool(removed or changed)}

    def clear_cache(self):
        self._cache.clear()

    def health(self) -> dict:
        return {"status":"HEALTHY","active_rulesets":len(self._active_rulesets),
                "cached_rulesets":len(self._cache),"config_path":str(self.config_path),
                "version":self.VERSION,"timestamp":datetime.utcnow().isoformat()}
