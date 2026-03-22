import json
from database import conectar

def guardar_sello(hash_sello: str, data: dict) -> bool:
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO sellos (hash, data) VALUES (?, ?)",
            (hash_sello, json.dumps(data, ensure_ascii=False))
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error al guardar sello: {e}")
        return False
    finally:
        conn.close()

def verificar_sello(hash_sello: str):
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data, created_at FROM sellos WHERE hash = ?",
            (hash_sello,)
        )
        res = cursor.fetchone()
        if res:
            data = json.loads(res[0])
            data["_registrado_en"] = res[1]
            return data
        return None
    finally:
        conn.close()