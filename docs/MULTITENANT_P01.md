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


## Platform operator identity boundary (P0.1 security review)

Tenant JWTs represent a user acting inside one active tenant membership. They must not grant global platform control. The branch now defines a separate persistent platform-operator identity and distinct token audience/type. Do not treat tenant roles (including `owner`) as platform roles.

### Route classification from the P0.1 branch audit

| Route group | Data / capability | Required boundary |
|---|---|---|
| `/api/v1/tenant/leads` | Tenant-owned lead records | Tenant JWT; member may read, admin/owner may update |
| `/execute/audit/{trace_id}` | Tenant audit seal | Tenant JWT; tenant-filtered lookup |
| `/market/regulatory/alerts/{tenant_id}` | Tenant-specific regulatory profile | Tenant JWT; path tenant must equal authenticated tenant |
| `/commercial/*` | Global commercial pipeline, lead data, marketing and scheduler | Platform-operator token on every route; existing route-level CRM Basic Auth remains as an additional check where configured |
| `/jarvis/*`, `/jarvis-sales/*` | Global JARVIS dashboards, leads, KPIs and operational intelligence | Platform operator only unless a route is redesigned as tenant-scoped |
| `/guardian/*`, `/system/*` | Infrastructure, incidents, control plane, scheduler and system operations | Platform operator only |
| `/commercial/shadow/*` | Global lead processing and activation/deactivation | Platform operator only; keep `MESAN_P5_SNAPSHOT` disabled until staging validation |
| `/smtp/*` | Platform email sending and status | Platform operator only; never tenant-owner permission |
| `/commercial/mission-control*` | Global leads, billing, Guardian and system metrics | Platform operator only |
| Public intake / demo / checkout | Anonymous prospect capture, public diagnostics and demo data | Explicit allowlist only; never return customer records |

### Operator architecture implemented on this branch; staging validation still required

1. The `PlatformOperator` table and separate platform login are implemented; operator creation remains a controlled manual database action (no public bootstrap).
2. Tenant tokens use `typ=tenant` and `aud=mesan-tenant-api`; platform tokens use `typ=platform` and `aud=mesan-platform-api`. The middleware rejects token-type/audience crossover.
3. Platform route permissions are checked against PostgreSQL on every request: `platform:read` for GET/HEAD and `platform:operate` for mutations; `platform:admin` is an explicit override.
4. Tenant-specific scope is derived from authenticated tenant context. The JARVIS briefing and Market regulatory alert endpoints are explicit tenant-scoped exceptions.
5. Existing CRM Basic Auth dependencies remain intact. Routes already protected by those dependencies are excluded from the platform-token gate, not made public.
6. Token separation and route classification tests have been added but have not been executed. End-to-end tests for revoked operators, missing permissions, tenant-owner denial, and DB behavior remain required.
7. Deploy only after a staging migration, operator provisioning/revocation rehearsal, PostgreSQL integration tests, and process-restart validation.

### Additional finding: JARVIS briefing tenant spoofing

The current `POST /jarvis/briefing` handler passes `body.get('tenant_id', 'public')` to the JARVIS bridge. This is request-controlled tenant selection. Before the route is exposed to tenant users, it must use the trusted tenant context and reject missing context; a platform-only version must use an explicit platform permission and must not impersonate a tenant from arbitrary request data.

### P0.1 decision

The independent operator identity and token separation are now implemented on this branch, but P0.1 remains open pending staging migration and end-to-end validation. Do not grant global access to tenant `owner`, `admin`, or `member`. No production activation, main-branch merge, or production database migration is authorized by this document.


## Independent platform operator authentication

The platform operator identity is separate from `mesan_users` and `mesan_memberships`.

### Migration and first operator provisioning

1. Back up the staging database.
2. Apply `migrations/20261123_003_platform_operators.up.sql` after migrations 001 and 002.
3. Provision the first operator manually through a controlled database session. There is deliberately no public operator-bootstrap endpoint.
4. Generate a password hash in a trusted administrative shell (never put the plaintext password in SQL, source control, logs, or chat):

```python
from getpass import getpass
from core.auth.passwords import hash_password
print(hash_password(getpass("New platform operator password (12+ chars): ")))
```

5. Insert the operator with a newly generated UUID, normalized email, returned hash, active status, and only the permissions required. Example SQL (replace placeholders; never use these placeholder values):

```sql
INSERT INTO mesan_platform_operators
    (id, email, password_hash, status, permissions)
VALUES
    ('<NEW-UUID>', '<OPERATOR-EMAIL>', '<PBKDF2-HASH>', 'active',
     '["platform:read","platform:operate"]'::jsonb);
```

6. Authenticate at `POST /auth/platform/login` with email and password. The response is a 30-minute bearer token with `typ=platform` and `aud=mesan-platform-api`.
7. Tenant login tokens use `typ=tenant` and `aud=mesan-tenant-api`. Middleware verifies token type and audience before database authorization; neither token type is accepted by the other route class.

### Permission policy

- `platform:read`: read-only platform routes (GET/HEAD).
- `platform:operate`: mutating platform routes (POST/PATCH/PUT/DELETE).
- `platform:admin`: explicit override for both permission classes; grant only to a tightly controlled operator.
- Operators must be active in `mesan_platform_operators`; revoking status blocks their next request. Token permissions are not trusted: permissions are loaded from PostgreSQL on every request.
- Tenant JWTs are rejected on platform-only routes. Platform JWTs are rejected on tenant routes.
- `/jarvis/briefing` and `/market/regulatory/alerts/{tenant_id}` remain tenant-scoped and must use the authenticated tenant context.
- Existing routes with explicit CRM Basic Auth remain outside the new operator-only gate; their existing dependencies are not removed.

### Platform route gate currently applied

The middleware requires a platform operator token and database permission for all `/commercial/*`, JARVIS global routes (except tenant briefing), JARVIS Sales, Guardian, System, SMTP, and Market global routes (except tenant regulatory alerts). Existing Basic Auth dependencies remain active on routes where they were already configured, so those endpoints require both checks.

The platform login is intentionally public only at its exact POST path. No operator account is created by migration or by the login endpoint.

### Compatibility and rollout warning

Tenant JWTs issued before the token-type/audience change are intentionally invalid under this branch's stricter verifier. Before any deployment, coordinate session expiration/re-login and test existing clients in staging. Do not deploy this branch or apply its migrations to production as part of this task.

Rollback file: `migrations/20261123_003_platform_operators.down.sql`. It drops operator identities; use only after confirming intentional revocation and backup.
