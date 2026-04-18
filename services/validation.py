import os
import xml.etree.ElementTree as ET
from fastapi import UploadFile, HTTPException

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'.xml', '.pdf'}


async def validar_documento(file: UploadFile) -> bytes:

    ext = os.path.splitext(file.filename or "")[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Extension no permitida")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande")

    if ext == ".xml":
        try:
            ET.fromstring(content)
        except ET.ParseError:
            raise HTTPException(status_code=400, detail="XML invalido")

    return content
