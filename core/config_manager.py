# core/config_manager.py -- MESAN Omega Enterprise Configuration System
import os
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class MesanConfig:
    # Scoring
    score_critico:  int   = 85
    score_alto:     int   = 65
    score_medio:    int   = 40
    # Risk limits
    max_dias_supervivencia_critico: int = 15
    max_dias_supervivencia_alto:    int = 30
    # Penalties
    max_validation_penalty:    int   = 40
    max_contradiction_penalty: int   = 50
    # Replay
    max_replay_events:         int   = 10000
    # Regulatory
    active_sat_version:   str = "SAT_2026_05"
    active_imss_version:  str = "IMSS_2026_01"
    active_repse_version: str = "REPSE_2026_01"
    # Observability
    enable_metrics:  bool = True
    enable_tracing:  bool = True
    log_level:       str  = "INFO"
    # AI
    claude_model:    str  = "claude-haiku-4-5-20251001"
    ai_timeout:      int  = 20
    ai_max_retries:  int  = 3

class ConfigManager:
    VERSION = "1.0.0"
    _config: MesanConfig = MesanConfig()

    @classmethod
    def get(cls) -> MesanConfig:
        return cls._config

    @classmethod
    def set(cls, key: str, value: Any):
        if hasattr(cls._config, key):
            setattr(cls._config, key, value)

    @classmethod
    def from_env(cls):
        c = cls._config
        c.score_critico     = int(os.getenv("MESAN_SCORE_CRITICO", c.score_critico))
        c.active_sat_version= os.getenv("MESAN_SAT_VERSION", c.active_sat_version)
        c.claude_model      = os.getenv("CLAUDE_MODEL", c.claude_model)
        c.ai_timeout        = int(os.getenv("AI_TIMEOUT", c.ai_timeout))
        c.ai_max_retries    = int(os.getenv("AI_MAX_RETRIES", c.ai_max_retries))
        c.log_level         = os.getenv("LOG_LEVEL", c.log_level)
        return c

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        c = cls._config
        return {k: getattr(c, k) for k in c.__dataclass_fields__}
