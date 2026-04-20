import json
import logging
from datetime import datetime


def guardar_documento(db, lead_id: str, nombre: str, tipo: str, resultado: dict):
    try:
        db.execute("""
            INSERT INTO documentos (lead_id, nombre, tipo, resultado)
            VALUES (%s, %s, %s, %s)
        """, (lead_id, nombre, tipo, json.dumps(resultado)))

        db.execute("""
            UPDATE leads
            SET documentos_subidos = TRUE,
                ultimo_analisis = NOW()
            WHERE id = %s
        """, (lead_id,))

        db.commit()
        logging.info(f"Documento guardado: {nombre} para lead {lead_id}")

    except Exception as e:
        db.rollback()
        logging.error(f"Error guardando documento: {e}")
        raise e


def actualizar_lead(db, lead_id: str, resultado: dict):
    try:
        db.execute("""
            UPDATE leads
            SET score = %s,
                indice_omega = %s,
                nivel_riesgo = %s
            WHERE id = %s
        """, (
            resultado["resultado"]["score"],
            resultado["indice_omega"]["indice_omega"],
            resultado["indice_omega"]["decision"],
            lead_id
        ))
        db.commit()
        logging.info(f"Lead {lead_id} actualizado")

    except Exception as e:
        db.rollback()
        logging.error(f"Error actualizando lead: {e}")
        raise e


def crear_evento(db, lead_id: str, accion: dict):
    try:
        db.execute("""
            INSERT INTO eventos (lead_id, tipo, descripcion)
            VALUES (%s, %s, %s)
        """, (lead_id, "decision", accion.get("accion", "")))
        db.commit()

    except Exception as e:
        db.rollback()
        logging.error(f"Error creando evento: {e}")
        raise e
