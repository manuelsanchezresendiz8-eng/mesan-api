-- MESAN Ω P0.1 — rollback del ledger. Exportar/verificar los sellos antes.
BEGIN;

DROP TRIGGER IF EXISTS trg_mesan_audit_seals_no_truncate ON mesan_audit_seals;
DROP TRIGGER IF EXISTS trg_mesan_audit_seals_immutable ON mesan_audit_seals;
DROP FUNCTION IF EXISTS mesan_prevent_audit_seal_mutation();
DROP TABLE IF EXISTS mesan_audit_seals;

COMMIT;
