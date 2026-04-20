import psycopg2
import os
import logging


def get_conn():
    try:
        return psycopg2.connect(os.getenv("DATABASE_URL"))
    except Exception as e:
        logging.error(f"DB connection error: {e}")
        raise


def guardar_diagnostico(conn, lead_id: str, resultado: dict):
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO diagnosticos
            (lead_id, score, nivel, indice_omega, impacto_anual, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            lead_id,
            resultado["resultado"]["score"],
            resultado["resultado"]["nivel"],
            resultado["indice_omega"]["indice_omega"],
            resultado["impacto"]["impacto_anual_max"],
            resultado["resumen"]["estado"]
        ))
        conn.commit()
        logging.info(f"Diagnostico guardado para lead {lead_id}")

    except Exception as e:
        conn.rollback()
        logging.error(f"Error guardando diagnostico: {e}")
        raise e


def marcar_pagado(conn, session_id: str):
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE pagos SET pagado = TRUE
            WHERE stripe_session = %s
        """, (session_id,))
        conn.commit()

    except Exception as e:
        conn.rollback()
        logging.error(f"Error marcando pagado: {e}")
        raise e


def guardar_evento(conn, lead_id: str, tipo: str, descripcion: str):
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO eventos (lead_id, tipo, descripcion)
            VALUES (%s, %s, %s)
        """, (lead_id, tipo, descripcion))
        conn.commit()

    except Exception as e:
        conn.rollback()
        logging.error(f"Error guardando evento: {e}")
        raise e
