# core/regulatory_registry.py -- MESAN Omega Regulatory Registry v1.1
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime

@dataclass
class RegulatoryVersion:
    version_id: str
    regulator:  str
    valid_from: str
    active:     bool = False
    rules:      Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class RegulatoryRegistry:
    VERSION = "1.1.0"
    DEFAULT_GLOBAL_VERSION = "GLOBAL_2026"

    def __init__(self):
        self._versions: Dict[str, RegulatoryVersion] = {}
        self._active_versions: Dict[str, str] = {}

    def register_version(self, version: RegulatoryVersion):
        if version.version_id in self._versions:
            raise ValueError(f"Version already registered: {version.version_id}")
        self._versions[version.version_id] = version
        if version.active:
            self.activate_version(version.regulator, version.version_id)

    def activate_version(self, regulator: str, version_id: str):
        version = self._versions.get(version_id)
        if not version: raise ValueError(f"Version not registered: {version_id}")
        if version.regulator != regulator:
            raise ValueError(f"Version {version_id} does not belong to regulator {regulator}")
        current = self._active_versions.get(regulator)
        if current and current in self._versions:
            self._versions[current].active = False
        version.active = True
        self._active_versions[regulator] = version_id

    def rollback_version(self, regulator: str, version_id: str):
        if version_id not in self._versions:
            raise ValueError(f"Rollback target not found: {version_id}")
        self.activate_version(regulator, version_id)

    def get_active(self, regulator: str) -> str:
        return self._active_versions.get(regulator, self.DEFAULT_GLOBAL_VERSION)

    def get_active_version(self, regulator: str) -> Optional[RegulatoryVersion]:
        return self._versions.get(self.get_active(regulator))

    def get_all_active(self) -> Dict[str, str]:
        return dict(self._active_versions)

    def get_registered_versions(self) -> List[str]:
        return list(self._versions.keys())

    def compare_versions(self, v1_id: str, v2_id: str) -> dict:
        v1 = self._versions.get(v1_id)
        v2 = self._versions.get(v2_id)
        if not v1 or not v2:
            return {"success": False, "error": "Version not found"}
        k1=set(v1.rules); k2=set(v2.rules)
        added=k2-k1; removed=k1-k2
        changed={k for k in k1&k2 if v1.rules[k]!=v2.rules[k]}
        return {"success":True,"v1":v1_id,"v2":v2_id,
                "added":sorted(added),"removed":sorted(removed),"changed":sorted(changed),
                "breaking_changes":bool(removed or changed),
                "total_changes":len(added)+len(removed)+len(changed),
                "comparison_timestamp":datetime.utcnow().isoformat()}

    def health(self) -> dict:
        return {"status":"HEALTHY","registry_version":self.VERSION,
                "registered_versions":len(self._versions),
                "active_regulators":len(self._active_versions),
                "timestamp":datetime.utcnow().isoformat()}
