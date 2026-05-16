# core/repse.py — MESAN Ω v2.5.0

REPSE_SERVICES = {
    "limpieza": "Servicios de limpieza y mantenimiento de inmuebles",
    "seguridad": "Seguridad privada y vigilancia",
    "mantenimiento": "Mantenimiento industrial y de equipos",
    "jardineria": "Jardineria y areas verdes",
    "mensajeria": "Mensajeria, paqueteria y logistica",
    "comedores": "Comedores industriales y servicios de alimentacion",
    "transporte": "Transporte de personal y ejecutivo",
    "call_center": "Call center y servicios de atencion al cliente",
    "ti": "Servicios de tecnologia con personal especializado",
    "vigilancia": "Vigilancia patrimonial y resguardo de valores",
    "construccion": "Construccion y obra civil especializada",
    "lavanderia": "Lavanderia industrial",
    "fumigacion": "Control de plagas y fumigacion",
    "auditoria": "Auditoria y consultoria especializada",
    "capacitacion": "Capacitacion y adiestramiento de personal"
}

def validar_giro_repse(giro: str) -> dict:
    giro = giro.lower().strip()
    if giro in REPSE_SERVICES:
        return {
            "valido": True,
            "descripcion": REPSE_SERVICES[giro],
            "giro": giro
        }
    return {
        "valido": False,
        "descripcion": "Giro no registrado en REPSE",
        "giro": giro
    }
