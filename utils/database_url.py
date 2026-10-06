import os

def get_direct_database_url():
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql://", 1)
    if url.startswith("postgres+psycopg://"):
        return url.replace("postgres+psycopg://", "postgresql://", 1)
    return url
