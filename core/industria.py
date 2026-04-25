def detectar_industria(texto: str) -> str:
    t = texto.lower()

    if any(p in t for p in [
        "consultorio", "consultario", "consultoio",
        "medico", "medico", "doctor", "medicina",
        "clinica", "clinika", "farmacia",
        "cofepris", "cofepreis", "cofepri", "copefris",
        "hospital", "salud", "sanitario"
    ]):
        return "SALUD"

    if any(p in t for p in ["tienda", "ropa", "retail", "mostrador", "comercio"]):
        return "RETAIL"

    if any(p in t for p in ["obra", "construccion", "albanil", "contratista", "edificio"]):
        return "CONSTRUCCION"

    if any(p in t for p in ["restaurante", "cocina", "alimentos", "comida", "cafe"]):
        return "ALIMENTOS"

    if any(p in t for p in ["fabrica", "produccion", "maquinaria", "planta", "linea"]):
        return "MANUFACTURA"

    return "GENERAL"
