# pro/cfdi.py — MESAN Ω

from fastapi import APIRouter
import logging

router = APIRouter()

REGIMENES = {
    "601": "General de Ley Personas Morales",
    "612": "Personas Fisicas con Actividades Empresariales",
    "626": "Simplificado de Confianza (RESICO)",
    "630": "Enajenacion de acciones en bolsa",
    "615": "Regimen de los ingresos por obtencion de premios",
}

USOS_CFDI = {
    "G01": "Adquisicion de mercancias",
    "G03": "Gastos en general",
    "I01": "Construcciones",
    "I04": "Equipo de computo y accesorios",
    "P01": "Por definir",
    "S01": "Sin efectos fiscales",
}


@router.post("/pro/cfdi/validar")
async def validar_cfdi(data: dict):
    try:
        rfc = data.get("rfc", "").strip().upper()
        regimen = data.get("regimen_fiscal", "")
        uso = data.get("uso_cfdi", "G03")
        errores = []

        if len(rfc) < 12 or len(rfc) > 13:
            errores.append("RFC invalido — debe tener 12 (moral) o 13 (fisica) caracteres")
        if not rfc.replace("-", "").isalnum():
            errores.append("RFC contiene caracteres no permitidos")
        if regimen not in REGIMENES:
            errores.append(f"Regimen fiscal '{regimen}' no reconocido")
        if uso not in USOS_CFDI:
            errores.append(f"Uso CFDI '{uso}' no reconocido")

        if errores:
            return {"valido": False, "errores": errores, "rfc": rfc}

        return {
            "valido": True,
            "rfc": rfc,
            "regimen": REGIMENES.get(regimen, ""),
            "uso_cfdi": USOS_CFDI.get(uso, ""),
            "mensaje": "Datos fiscales validos para emision de CFDI"
        }

    except Exception as e:
        logging.error(f"Error validando CFDI: {e}")
        return {"error": str(e), "valido": False}


@router.post("/pro/cfdi/generar")
async def generar_cfdi(data: dict):
    try:
        nombre = data.get("nombre", "")
        rfc = data.get("rfc", "").strip().upper()
        monto = float(data.get("monto", 0))
        concepto = data.get("concepto", "Servicio de diagnostico empresarial MESAN Omega")
        uso = data.get("uso_cfdi", "G03")

        iva = round(monto * 0.16, 2)
        total = round(monto + iva, 2)

        return {
            "ok": True,
            "cfdi": {
                "emisor": "MESAN OMEGA SA DE CV",
                "receptor": nombre,
                "rfc_receptor": rfc,
                "concepto": concepto,
                "subtotal": monto,
                "iva": iva,
                "total": total,
                "uso_cfdi": uso,
                "moneda": "MXN",
                "forma_pago": "03",
                "metodo_pago": "PUE",
                "estado": "PENDIENTE_TIMBRADO"
            },
            "nota": "Integrar con PAC (Finkok/SW) para timbrado real"
        }

    except Exception as e:
        logging.error(f"Error generando CFDI: {e}")
        return {"error": str(e), "ok": False}
