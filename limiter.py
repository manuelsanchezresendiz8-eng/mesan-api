  
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

def identificar_cliente(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key[-8:]}"
    return get_remote_address(request)

limiter = Limiter(key_func=identificar_cliente)