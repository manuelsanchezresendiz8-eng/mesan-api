-- MESAN Ω P0.1 — aislamiento multiempresa.
-- Ejecutar explícitamente después de backup. No se ejecuta desde init_db().
BEGIN;

CREATE TABLE IF NOT EXISTS mesan_tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mesan_users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_mesan_users_email ON mesan_users(email);

CREATE TABLE IF NOT EXISTS mesan_memberships (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES mesan_tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES mesan_users(id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL DEFAULT 'member',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_mesan_membership_tenant_user UNIQUE (tenant_id, user_id)
);
CREATE INDEX IF NOT EXISTS ix_mesan_memberships_tenant_id ON mesan_memberships(tenant_id);
CREATE INDEX IF NOT EXISTS ix_mesan_memberships_user_id ON mesan_memberships(user_id);

ALTER TABLE leads ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36) NULL;
CREATE INDEX IF NOT EXISTS ix_leads_tenant_id ON leads(tenant_id);

-- Los registros existentes quedan NULL (legacy/unassigned).
-- No asignar leads históricos ni leads públicos a un tenant por defecto.

COMMIT;
