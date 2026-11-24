-- MESAN Ω P0.1 — identidad independiente de operador de plataforma.
-- Requiere aplicar tenant isolation 001. No crea operadores automáticamente.
BEGIN;

CREATE TABLE IF NOT EXISTS mesan_platform_operators (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    permissions JSON NOT NULL DEFAULT '[]'::json,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_mesan_platform_operators_email
    ON mesan_platform_operators(email);

COMMIT;
