# MESAN Ω — P0.1 Multi-tenant authentication

## Scope
This change adds persistent tenant/user/membership records, a controlled first-owner bootstrap, JWT login, tenant-scoped lead access, and a PostgreSQL-backed append-only audit-seal ledger. The existing CRM Comercial Basic Auth routes remain separate and unchanged.

## Required environment
- `DATABASE_URL`: existing PostgreSQL connection.
- `MESAN_SECRET_KEY`: strong random signing secret for JWT. Required for login and protected API requests.
- `MESAN_BOOTSTRAP_TOKEN`: one-time bootstrap secret. Use a long random value; remove it from the deployment environment immediately after the first owner is created.
- `MESAN_P5_SNAPSHOT`: leave unset/false until migration 002 is applied and validated. Set to `true` only in the validation environment to enable audit sealing.

Do not reuse the legacy `JWT_SECRET` value from `pro/auth.py`.

## Apply sequence (manual, after backup)
1. Take and verify a PostgreSQL backup.
2. Review and execute `migrations/20261123_001_tenant_isolation.up.sql`.
3. Review and execute `migrations/20261123_002_audit_seals_postgres.up.sql`.
4. Set `MESAN_SECRET_KEY` and temporarily set `MESAN_BOOTSTRAP_TOKEN`.
5. Deploy the branch only to a non-production validation environment.
6. Call `POST /auth/bootstrap` once with `X-Bootstrap-Token` and JSON fields `tenant_name`, `email`, and `password` (minimum 12 characters).
7. Remove `MESAN_BOOTSTRAP_TOKEN` from the environment and restart the validation service.
8. Call `POST /auth/login` with `email`, `password`, and the returned `tenant_id`. Use the returned bearer token for protected API routes.
9. Enable `MESAN_P5_SNAPSHOT=true` only after confirming the audit table exists and the service can insert/read a test seal. Restart the service and verify a seal can be read after a second process start.

Bootstrap is disabled unless the environment secret is configured, and it refuses to run after any user exists. Login requires an active user, active tenant, and active membership.

## Private tenant API
After login, send the bearer token to:
- `GET /api/v1/tenant/leads` — list only leads assigned to the authenticated tenant.
- `GET /api/v1/tenant/leads/{lead_id}` — read only a lead owned by that tenant; cross-tenant and public/unassigned records return 404.
- `PATCH /api/v1/tenant/leads/{lead_id}` — update allowlisted fields only, with the same tenant ownership check.
- `GET /execute/audit/{trace_id}` — retrieve only the audit seal belonging to the authenticated tenant.

These routes are separate from the legacy CRM endpoints. The one-time bootstrap uses a PostgreSQL advisory transaction lock to serialize concurrent first-owner attempts.

## Audit seal persistence and integrity
- Audit records are inserted into `mesan_audit_seals` in PostgreSQL; the runtime JSONL file and in-memory trace index are no longer the source of truth.
- A unique constraint prevents duplicate `(tenant_id, trace_id)` seals.
- The database trigger rejects UPDATE and DELETE operations on the audit ledger.
- Lookup, history, and verification require a tenant ID and filter by both tenant and trace where applicable.
- If the feature flag is off, or the migration/table is unavailable, sealing remains disabled and the main diagnostic path continues. This is not evidence that audit persistence is operational.
- The audit ledger stores seal metadata and the SHA-256 hash, not the complete diagnostic response. Verification requires the same response document to be presented again.
- PostgreSQL durability depends on the configured database's backup and retention policy; validate that policy separately.

## Data handling
Existing and public landing leads remain `tenant_id IS NULL`. They are not assigned to the first tenant. Legacy CRM access remains governed by its existing Basic Auth dependencies; do not expose its unscoped lead-store methods as customer endpoints.

## Rollback
Review the impact first. Export and verify audit seals before considering `20261123_002_audit_seals_postgres.down.sql`; that migration permanently drops the audit ledger. The P0.1 down migration deletes tenant memberships/users/tenants and removes `leads.tenant_id`; do not run it after real customer data has been created unless that data is intentionally being discarded or exported.
