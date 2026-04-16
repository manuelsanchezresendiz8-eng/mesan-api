from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from database import SessionLocal
import os

auth_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET = os.environ.get("JWT_SECRET", "mesan_secret_2026")

def hash_password(p): 
    return pwd_context.hash(p)

def verify_password(p, h): 
    return pwd_context.verify(p, h)

def create_token(email):
    return jwt.encode(
        {"sub": email, "exp": datetime.utcnow() + timedelta(hours=12)},
        SECRET,
        algorithm="HS256"
    )

@auth_router.post("/login")
async def login(data: dict):
    email = data.get("email")
    password = data.get("password")

    # Usuario hardcodeado por ahora
    USERS = {
        os.environ.get("ADMIN_EMAIL", "admin@mesanomega.com"): 
        os.environ.get("ADMIN_PASSWORD", "mesan2026")
    }

    if USERS.get(email) != password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_token(email)
    return {"access_token": token}
