from fastapi import APIRouter, HTTPException, Request
from services.ledger import verificar_sello
from limiter import limiter

router = APIRouter()

@router.get("/verificar/{hash_sello}")
@limiter.limit("120/minute")
def verificar(request: Request, hash_sello: str):
    if len(hash_sello) != 64:
        raise HTTPException(status_code=400, detail="Hash invalido")
    data = verificar_sello(hash_sello)
    if not data:
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    return {"estatus": "VERIFICADO", "data": data}