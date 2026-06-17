from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

# Render entrega DATABASE_URL como "postgresql://..." o "postgres://...".
# SQLAlchemy, sin un driver explicito en la URL, intenta usar psycopg2
# por defecto -- pero el proyecto instala psycopg (v3, via psycopg[binary]
# en requirements.txt), no psycopg2. Forzamos el dialecto correcto aqui
# para evitar "ModuleNotFoundError: No module named 'psycopg2'" en deploy.
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from models import Lead
    Base.metadata.create_all(bind=engine)

def conectar():
    return engine.connect()
