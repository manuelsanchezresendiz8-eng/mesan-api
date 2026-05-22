# core/explainability_engine.py
# MESAN Omega — Explainability Engine v2.0
# Deterministic | Auditable | Enterprise Hardened

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


# ============================================================
# GLOBAL CONFIG
# ============================================================

ENGINE_VERSION = "2.0.0"
REGULATORY_VERSION = "MESAN_2026_05"


# ============================================================
# ENUMS
# ============================================================

class Severity(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


# ============================================================
# DATA MODELS
# =================================================
