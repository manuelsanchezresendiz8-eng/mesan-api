import hashlib
import json
import datetime

def generar_sello(resultado, email="", input_data=None):
    timestamp = datetime.datetime.utcnow().isoformat()
    payload = {
        "resultado": resultado,
        "email": email,
        "input": input_data,
        "timestamp": timestamp
    }
    raw = json.dumps(payload, sort_keys=True)
    hash_val = hashlib.sha256(raw.encode()).hexdigest()
    return {
        "hash": hash_val,
        "metadata": {
            "timestamp": timestamp,
            "email": email
        }
    }

def guardar_sello(hash_val, data):
    from database import conectar
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO sellos (hash, data) VALUES (?, ?)",
            (hash_val, json.dumps(data))
        )
        conn.commit()
    finally:
        conn.close()
