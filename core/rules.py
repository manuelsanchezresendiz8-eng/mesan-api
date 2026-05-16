# core/rules.py — MESAN Ω v2.5.0
# Reglas dinamicas — SIN fechas hardcodeadas

RULES = {
    "REPSE_INVALID": {
        "risk_level": "CRITICO",
        "imss_action_days": 5,
        "sat_action": "INMEDIATO",
        "audit_window_days": 30,
        "descripcion": "REPSE vencido o sin registro"
    },
    "WORKERS_UNREGISTERED": {
        "risk_level": "ALTO",
        "imss_action_days": 3,
        "sat_action": "48H",
        "audit_window_days": 20,
        "descripcion": "Empleados sin registro IMSS"
    },
    "FACTURA_IRREGULAR": {
        "risk_level": "ALTO",
        "imss_action_days": 7,
        "sat_action": "72H",
        "audit_window_days": 15,
        "descripcion": "Diferencias en CFDI vs nomina real"
    },
    "SIN_CONTRATOS": {
        "risk_level": "MEDIO",
        "imss_action_days": 10,
        "sat_action": "7DIAS",
        "audit_window_days": 45,
        "descripcion": "Personal sin contratos laborales formalizados"
    },
    "INSPECCION_SAT": {
        "risk_level": "CRITICO",
        "imss_action_days": 1,
        "sat_action": "INMEDIATO",
        "audit_window_days": 7,
        "descripcion": "Inspeccion SAT activa o requerimiento fiscal"
    },
    "SUBREGISTRO_SALARIAL": {
        "risk_level": "ALTO",
        "imss_action_days": 5,
        "sat_action": "48H",
        "audit_window_days": 20,
        "descripcion": "Salario declarado menor al real"
    },
    "MARGEN_BAJO": {
        "risk_level": "MEDIO",
        "imss_action_days": 30,
        "sat_action": "REVISION",
        "audit_window_days": 60,
        "descripcion": "Margen operativo por debajo del 15%"
    }
}
