import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException

try:
    from core.parser_cfdi import analizar_cfdi
except:
    analizar_cfdi = None

try:
    from core.validador_sat import validar_cfdi
except:
    validar_cfdi = None

try:
    from core.motor_total import motor_total
except:
    motor_total = None

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/documento")
async def subir_documento(
    file: UploadFile = File(...),
    lead_id: str = None,
    empleados: int = 50
):

    if not file.filename:
        raise HTTPException(400, "Archivo requerido")

    filename = file.filename
    ext = filename.lower().split(".")[-1]

    if ext not in ["xml", "pdf"]:
        raise HTTPException(400, "Solo se aceptan archivos XML o PDF")

    contenido = await file.read()

    if len(contenido) > 5 * 1024 * 1024:
        raise HTTPException(400, "Archivo demasiado grande. Maximo 5MB")

    filepath = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{filename}")

    with open(filepath, "wb") as f:
        f.write(contenido)

    logging.info(f"Archivo recibido: {filename} | lead: {lead_id}")

    # XML — CFDI
    if ext == "xml":

        if not analizar_cfdi or not validar_cfdi:
            return {
                "tipo": "CFDI",
                "mensaje": "Parser no disponible",
                "archivo": filename
            }

        try:
            xml_str = contenido.decode("utf-8")
        except:
            xml_str = contenido.decode("latin-1")

        cfdi = analizar_cfdi(xml_str)
        validacion = validar_cfdi(cfdi)

        resultado_motor = {}
        if motor_total:
            resultado_motor = motor_total({
                "cfdi": validacion,
                "empleados": empleados
            })

        return {
            "tipo": "CFDI",
            "archivo": filename,
            "analisis": cfdi,
            "validacion": validacion,
            "resultado": resultado_motor
        }

    # PDF
    return {
        "tipo": "PDF",
        "archivo": filename,
        "mensaje": "PDF recibido. Analisis avanzado pendiente."
    }
