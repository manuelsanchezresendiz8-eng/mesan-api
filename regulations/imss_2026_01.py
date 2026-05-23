# regulations/imss_2026_01.py -- MESAN Omega IMSS Regulatory Transitional Pack v1.1
# TODO: migrate to YAML/JSON + RegulatoryLoader

from dataclasses import dataclass
from typing import Dict, Any
from decimal import Decimal
from functools import lru_cache

VERSION    = "IMSS_2026_01"
VALID_FROM = "2026-01-01"
REGULATOR  = "IMSS"

UMA_DIARIA              = Decimal("108.57")
UMA_MENSUAL             = Decimal("3303.56")
SALARIO_MINIMO_GENERAL  = Decimal("278.80")
SALARIO_MINIMO_FRONTERA = Decimal("419.88")

CUOTAS_PATRONALES: Dict[str, Decimal] = {
    "enfermedades_maternidad":       Decimal("0.1050"),
    "invalidez_vida":                Decimal("0.0175"),
    "guarderias":                    Decimal("0.0100"),
    "riesgos_trabajo_base":          Decimal("0.0054"),
    "retiro":                        Decimal("0.0200"),
    "cesantia_vejez":                Decimal("0.0350"),
    "infonavit_aportacion_patronal": Decimal("0.0500"),
}

MULTAS = {
    "omision_alta":           {"min": Decimal("20"),  "max": Decimal("350")},
    "salario_incorrecto":     {"min": Decimal("20"),  "max": Decimal("75")},
    "no_pago_cuotas":         {"min": Decimal("40"),  "max": Decimal("100")},
    "obstruccion_inspeccion": {"min": Decimal("20"),  "max": Decimal("125")},
}

RECARGOS_MENSUALES     = Decimal("0.0060")
CUOTA_TOTAL_PATRONAL   = sum(CUOTAS_PATRONALES.values())

@dataclass(frozen=True)
class RegulatoryMetadata:
    regulator: str; version: str; valid_from: str; transitional: bool = True

METADATA = RegulatoryMetadata(regulator=REGULATOR, version=VERSION, valid_from=VALID_FROM)

@lru_cache(maxsize=1)
def get_regulation_snapshot() -> Dict[str, Any]:
    return {
        "metadata":    {"regulator": METADATA.regulator, "version": METADATA.version,
                        "valid_from": METADATA.valid_from, "transitional": METADATA.transitional},
        "uma":         {"diaria": float(UMA_DIARIA), "mensual": float(UMA_MENSUAL)},
        "salario_minimo": {"general": float(SALARIO_MINIMO_GENERAL), "frontera": float(SALARIO_MINIMO_FRONTERA)},
        "cuotas_patronales": {k: float(v) for k,v in CUOTAS_PATRONALES.items()},
        "multas":      {k: {"min": float(v["min"]), "max": float(v["max"])} for k,v in MULTAS.items()},
        "recargos_mensuales": float(RECARGOS_MENSUALES),
    }

def calcular_multa(tipo: str, uma_diaria: Decimal = None) -> dict:
    uma   = uma_diaria or UMA_DIARIA
    rango = MULTAS.get(tipo, {"min": Decimal("20"), "max": Decimal("100")})
    return {"tipo": tipo, "min_mxn": round(float(rango["min"]*uma),2),
            "max_mxn": round(float(rango["max"]*uma),2),
            "version": VERSION, "regulator": REGULATOR, "transitional": True}

def validate_configuration() -> dict:
    errors = []
    if UMA_DIARIA <= 0:          errors.append("UMA_DIARIA invalida")
    if CUOTA_TOTAL_PATRONAL <= 0: errors.append("CUOTA_TOTAL_PATRONAL invalida")
    return {"valid": len(errors)==0, "errors": errors, "version": VERSION}
