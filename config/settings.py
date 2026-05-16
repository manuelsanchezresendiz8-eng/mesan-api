# config/settings.py — MESAN Ω v2.5.0

import os

class Settings:
    # Auth
    JWT_SECRET          = os.getenv("JWT_SECRET", "mesan_secret_2026")
    JWT_ALGORITHM       = "HS256"
    JWT_EXPIRE_MINUTES  = 480
    MESAN_API_KEY       = os.getenv("MESAN_API_KEY", "mesan2026mexicali")

    # IA
    OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL        = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY")

    # Stripe
    STRIPE_SECRET_KEY       = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET   = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID         = os.getenv("STRIPE_PRICE_ID")
    PRECIO_PRO_MXN          = 29900
    PRECIO_ENTERPRISE_MXN   = 49900

    # DB
    DATABASE_URL        = os.getenv("DATABASE_URL")
    REDIS_HOST          = os.getenv("REDIS_HOST")

    # App
    BASE_URL            = os.getenv("BASE_URL", "https://mesanomega.com")
    DEBUG               = os.getenv("DEBUG", "false").lower() == "true"
    VERSION             = "2.5.0"

    # WhatsApp
    WA_NUMERO_MANUEL    = "526861629643"
    WA_NUMERO_DANIEL    = "526865242805"
    WHATSAPP_TOKEN      = os.getenv("WHATSAPP_TOKEN", "")

    # Email
    RESEND_API_KEY      = os.getenv("RESEND_API_KEY", "")
    EMAIL_DESTINO       = os.getenv("EMAIL_DESTINO", "contacto@mesanomega.com")

    # SMG 2026
    SMG_FRONTERA        = 447.00
    SMG_INTERIOR        = 278.80
    FACTOR_CARGA_SOCIAL = 1.45
    IVA_FRONTERA        = 0.08
    IVA_INTERIOR        = 0.16
    MARGEN_OPERATIVO    = 0.35
    INSUMOS_MES         = 1200

settings = Settings()
