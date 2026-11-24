-- MESAN Ω P0.1 — rollback. Ejecutar solo tras confirmar que no se requieren
-- los datos multiempresa creados después de aplicar la migración.
BEGIN;

DROP INDEX IF EXISTS ix_leads_tenant_id;
ALTER TABLE leads DROP COLUMN IF EXISTS tenant_id;

DROP TABLE IF EXISTS mesan_memberships;
DROP TABLE IF EXISTS mesan_users;
DROP TABLE IF EXISTS mesan_tenants;

COMMIT;
