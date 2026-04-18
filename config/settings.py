import os

class Settings:
    JWT_SECRET = os.getenv("JWT_SECRET", "mesan_secret_2026")
    JWT_ALGORITHM = "HS256"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    REDIS_HOST = os.getenv("REDIS_HOST")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    DATABASE_URL = os.getenv("DATABASE_URL")
    BASE_URL = os.getenv("BASE_URL", "https://mesanomega.com")

settings = Settings()
