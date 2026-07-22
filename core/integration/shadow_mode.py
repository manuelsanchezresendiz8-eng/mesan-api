# core/integration/shadow_mode.py -- MESAN Omega Shadow Mode v1.0
# Corre exposure_engine v2 y scoring_engine v2 en paralelo
# NO modifica el resultado del pipeline actual
# Solo registra diferencias para validacion
import logging, os
from typing import Any, Dict
logger = logging.getLogger("mesan.shadow")
FLAG = "MESAN_SHADOW_MODE"

def _flag(): return os.getenv(FLAG,"false").strip().lower() in ("1","true","yes","on")

def shadow_exposure(data: Dict[str, Any], current_result: Dict) -> None:
    if not _flag(): return
    try:
        from core.exposure_engine import ExposureEngine
        eng = ExposureEngine()
        shadow = eng.calcular(data) if hasattr(eng,"calcular") else eng.evaluate(data) if hasattr(eng,"evaluate") else None
        if shadow:
            current = current_result.get("total_exposure_mxn", 0)
            shadow_val = shadow.get("total_exposure_mxn", shadow.get("total", 0)) if isinstance(shadow, dict) else getattr(shadow,"total",0)
            diff = abs(float(shadow_val) - float(current))
            logger.info("[SHADOW] exposure current=%.0f shadow=%.0f diff=%.0f", current, shadow_val, diff)
    except Exception as e:
        logger.warning("[SHADOW] exposure error: %s", e)

def shadow_scoring(data: Dict[str, Any], current_score: float) -> None:
    if not _flag(): return
    try:
        from core.scoring_engine import calcular_score
        shadow = calcular_score(data)
        shadow_score = shadow.get("score", shadow.get("total", 0)) if isinstance(shadow, dict) else 0
        diff = abs(float(shadow_score) - float(current_score))
        logger.info("[SHADOW] scoring current=%.1f shadow=%.1f diff=%.1f", current_score, shadow_score, diff)
    except Exception as e:
        logger.warning("[SHADOW] scoring error: %s", e)
