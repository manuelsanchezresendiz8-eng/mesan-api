-- Eliminar solo después de revocar sesiones y confirmar que se desea borrar operadores.
BEGIN;
DROP TABLE IF EXISTS mesan_platform_operators;
COMMIT;
