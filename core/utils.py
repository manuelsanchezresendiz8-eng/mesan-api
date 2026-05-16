# core/utils.py — MESAN Ω v2.5.0

def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ["true", "1", "yes", "si"]
    return False

def safe_get(d, key, default=0):
    return d.get(key) if isinstance(d, dict) else default

def limpiar_texto(texto: str) -> str:
    return texto.replace("Ω", "Omega").replace("ω", "omega").strip()
