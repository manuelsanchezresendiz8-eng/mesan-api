# MESAN Ω — P0.1 Multi-tenant authentication

## Scope
This change adds persistent tenant/user/membership records, a controlled first-owner bootstrap, and JWT login. The existing CRM Comercial Basic Auth routes remain separate and unchanged.

## Required environment
- `DATABASE_URL`: existing PostgreSQL connection.
- `MESAN_SECRET_KEY`: strong random signing secret for JWT. Required for login and protected API requests.
- `MESAN_BOOTSTRAP_TOKEN`: one-time bootstrap secret. Use a long random value; remove it from the deployment environment immediately after the first owner is created.

Do not reuse the legacy `JWT_SECRET` value from `pro/auth.py`.

## Apply sequence (manual, after backup)
1. Take and verify a PostgreSQL backup.
2. Review and execute `migrations/20261123_001_tenant_isolation.up.sql`.
3. Set `MESAN_SECRET_KEY` and temporarily set `MESAN_BOOTSTRAP_TOKEN`.
4. Deploy the branch only to a non-production validation environment.
5. Call `POST /auth/bootstrap` once with `X-Bootstrap-Token` and JSON fields `tenant_name`, `email`, and `password` (minimum 12 characters).
6. Remove `MESAN_BOOTSTRAP_TOKEN` from the environment and restart the validation service.
7. Call `POST /auth/login` with `email`, `password`, and the returned `tenant_id`. Use the returned bearer token for protected API routes.

Bootstrap is disabled unless the environment secret is configured, and it refuses to run after any user exists. Login requires an active user, active tenant, and active membership.

## Private tenant API
After login, send the bearer token to:
- `GET /api/v1/tenant/leads` — list only leads assigned to the authenticated tenant.
- `GET /api/v1/tenant/leads/{lead_id}` — read only a lead owned by that tenant; cross-tenant and public/unassigned records return 404.
- `PATCH /api/v1/tenant/leads/{lead_id}` — update allowlisted fields only, with the same tenant ownership check.

These routes are separate from the legacy CRM endpoints. The one-time bootstrap uses a PostgreSQL advisory transaction lock to serialize concurrent first-owner attempts.

## Data handling
Existing and public landing leads remain `tenant_id IS NULL`. They are not assigned to the first tenant. Legacy CRM access remains governed by its existing Basic Auth dependencies; do not expose its unscoped lead-store methods as customer endpoints.

## Rollback
Review the impact first. The down migration deletes tenant memberships/users/tenants and removes `leads.tenant_id`; do not run it after real customer data has been created unless that data is intentionally being discarded or exported.
