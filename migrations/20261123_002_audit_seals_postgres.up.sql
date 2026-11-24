-- MESAN Ω P0.1 — ledger durable de sellos SHA-256.
-- Requiere aplicar primero 20261123_001_tenant_isolation.up.sql.
BEGIN;

CREATE TABLE IF NOT EXISTS mesan_audit_seals (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(128) NOT NULL,
    trace_id VARCHAR(128) NOT NULL,
    snapshot_id VARCHAR(36) NOT NULL,
    sealed_at VARCHAR(40) NOT NULL,
    state_hash VARCHAR(64) NOT NULL,
    algorithm VARCHAR(16) NOT NULL DEFAULT 'SHA-256',
    engine_version VARCHAR(32) NOT NULL,
    omega_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    risk_level VARCHAR(20) NOT NULL,
    exposure_total DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_mesan_audit_seal_tenant_trace UNIQUE (tenant_id, trace_id)
);

CREATE INDEX IF NOT EXISTS ix_mesan_audit_seals_tenant_id
    ON mesan_audit_seals(tenant_id);
CREATE INDEX IF NOT EXISTS ix_mesan_audit_seals_tenant_time
    ON mesan_audit_seals(tenant_id, sealed_at DESC);

-- Protección adicional: la aplicación solo inserta y consulta; no actualiza ni borra.
CREATE OR REPLACE FUNCTION mesan_prevent_audit_seal_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'MESAN_AUDIT_SEALS_APPEND_ONLY';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_mesan_audit_seals_immutable ON mesan_audit_seals;
CREATE TRIGGER trg_mesan_audit_seals_immutable
BEFORE UPDATE OR DELETE ON mesan_audit_seals
FOR EACH ROW EXECUTE FUNCTION mesan_prevent_audit_seal_mutation();

COMMIT;
