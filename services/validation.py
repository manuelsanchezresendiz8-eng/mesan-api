# services/validation.py

import os
import logging

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_TYPES = ["application/pdf", "text/xml", "application/xml"]
ALLOWED_EXTENSIONS = [".pdf", ".xml"]


async def validate_file(file) -> bytes:
    filename = file.filename or ""
    ext = "." + filename.lower().split(".")[-1] if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Tipo de archivo no permitido: {ext}")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"Archivo demasiado grande. Maximo 5MB")

    if len(content) == 0:
        raise ValueError("Archivo vacio")

    logging.info(f"Archivo validado: {filename} ({len(content)} bytes)")

    return content


def validar_payload(data: dict, campos_requeridos: list) -> bool:
    for campo in campos_requeridos:
        if not data.get(campo):
            logging.warning(f"Campo requerido faltante: {campo}")
            return False
    return True


def sanitizar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.strip()
    texto = texto.replace("<", "").replace(">", "")
    texto = texto.replace("Ω", "Omega")
    return texto[:500]


def validar_email(email: str) -> bool:
    if not email:
        return False
    return "@" in email and "." in email.split("@")[-1]


def validar_telefono(telefono: str) -> bool:
    if not telefono:
        return False
    digitos = "".join(filter(str.isdigit, telefono))
    return len(digitos) >= 10

# v2 — actualizado
