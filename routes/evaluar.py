import json, time, datetime, os
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from services.sello import generar_sello
from services.ledger import guardar_sello
from database import conectar
from limiter import limiter

router = APIRouter()
_cache_nodos = {}

def verificar_api_key(x_api_key: str = Header(...)):
    clave = os.environ.get("MESAN_API_KEY")
    if x_api_key != clave:
        raise HTTPException(status_code=401, detail="API Key invalida")

def validar_kill_switch(ciudad: str) -> bool:
    ahora = time.time()
    if ciudad in _cache_nodos:
        valor, ts = _cache_nodos[ciudad]
        if ahora - ts < 60:
            return valor
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT activo FROM nodos_licencia WHERE id_nodo = ?", (ciudad,)
        )
        res = cursor.fetchone()
    finally:
        conn.close()
    resultado = bool(res and res[0] == 1)
    _cache_nodos[ciudad] = (resultado, ahora)
    return resultado

def guardar_lead(email, tel, data):
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leads (email, telefono, data) VALUES (?, ?, ?)",
            (email, tel, json.dumps(data))
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()

@router.post("/evaluar", dependencies=[Depends(verificar_api_key)])
@limiter.limit("60/minute")
def evaluar(request: Request, data: dict):
    if not validar_kill_switch(data.get("ciudad", "")):
        raise HTTPException(status_code=403, detail="Nodo inactivo")
    datos = data.get("datos", [])
    if not datos:
        raise HTTPException(status_code=422, detail="Campo datos vacio")
    score = round((sum(datos) / len(datos)) * 100, 2)
    resultado = {
        "score": score,
        "estatus": "VULNERABLE" if score < 80 else "ESTABLE",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    sello_data = generar_sello(resultado, data.get("email", ""), input_data=data)
    guardar_sello(sello_data["hash"], {
        "resultado": resultado,
        "metadata": sello_data["metadata"]
    })
    guardar_lead(
        data.get("email"),
        data.get("telefono"),
        {"resultado": resultado, "cert_hash": sello_data["hash"]}
    )
    return {"analisis": resultado, "certificacion": sello_data}