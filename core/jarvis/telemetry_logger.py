# core/jarvis/telemetry_logger.py -- MESAN Omega Telemetry Logger v1.0
"""
Logger centralizado usando el modulo estandar logging de Python.
Cada categoria escribe a su archivo dedicado.
GuardianTelemetryEngine es una capa sobre este logger.
"""

import logging
import json
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def _json_formatter():
    formatter = logging.Formatter("%(message)s")
    return formatter


def _get_file_handler(filename):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    filepath = LOG_DIR / filename
    handler = logging.FileHandler(filepath, encoding="utf-8")
    handler.setFormatter(_json_formatter())
    return handler


def _build_logger(name, filename):
    log = logging.getLogger("mesan.telemetry." + name)
    log.setLevel(logging.DEBUG)
    if not log.handlers:
        log.addHandler(_get_file_handler(filename))
        log.propagate = False
    return log


api_logger = _build_logger("api", "api.log")
security_logger = _build_logger("security", "security.log")
payment_logger = _build_logger("payment", "payments.log")
system_logger = _build_logger("system", "system.log")
guardian_logger = _build_logger("guardian", "guardian.log")


def write_event(logger_instance, event_dict):
    severity = event_dict.get("severity", "INFO").upper()
    line = json.dumps(event_dict, ensure_ascii=False)
    if severity == "CRITICAL":
        logger_instance.critical(line)
    elif severity in ("HIGH", "WARNING"):
        logger_instance.warning(line)
    elif severity == "ERROR":
        logger_instance.error(line)
    else:
        logger_instance.info(line)