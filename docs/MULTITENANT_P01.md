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

Tenant JWTs represent a user acting inside one active tenant membership. They must not grant global platform control. The current schema has tenant users and memberships only; it has no independent platform-operator identity, credential lifecycle, or operator role assignment. Do not treat tenant roles (including `owner`) as platform roles.

### Route classification from the P0.1 branch audit

| Route group | Data / capability | Required boundary |
|---|---|---|
| `/api/v1/tenant/leads` | Tenant-owned lead records | Tenant JWT; member may read, admin/owner may update |
| `/execute/audit/{trace_id}` | Tenant audit seal | Tenant JWT; tenant-filtered lookup |
| `/market/regulatory/alerts/{tenant_id}` | Tenant-specific regulatory profile | Tenant JWT; path tenant must equal authenticated tenant |
| `/commercial/*` | Global commercial pipeline, lead data, marketing and scheduler | Existing CRM Basic Auth dependency plus a future platform-operator boundary; do not grant to tenant owners |
| `/jarvis/*`, `/jarvis-sales/*` | Global JARVIS dashboards, leads, KPIs and operational intelligence | Platform operator only unless a route is redesigned as tenant-scoped |
| `/guardian/*`, `/system/*` | Infrastructure, incidents, control plane, scheduler and system operations | Platform operator only |
| `/commercial/shadow/*` | Global lead processing and activation/deactivation | Platform operator only; keep `MESAN_P5_SNAPSHOT` disabled until staging validation |
| `/smtp/*` | Platform email sending and status | Platform operator only; never tenant-owner permission |
| `/commercial/mission-control*` | Global leads, billing, Guardian and system metrics | Platform operator only |
| Public intake / demo / checkout | Anonymous prospect capture, public diagnostics and demo data | Explicit allowlist only; never return customer records |

### Required operator architecture before enabling platform routes

1. Add a separate persistent platform-operator identity model, not a tenant membership role. It must support active/revoked status, unique normalized identity, password hash, and explicit platform permissions.
2. Use a distinct platform login and a distinct signed token type/audience. Tenant tokens must be rejected by platform routes even if their tenant role is `owner`; platform tokens must not be accepted by tenant data routes.
3. Keep platform permissions explicit and least-privilege (for example read-only operations vs. operational control). Activation, scheduler control, SMTP send, cleanup, and other mutations require a stronger permission than dashboard reads.
4. Derive tenant scope from the authenticated tenant context. Never trust a request body, query parameter, or path value as proof of tenant identity. Where a tenant identifier remains in a URL for compatibility, compare it to the authenticated context and deny mismatches.
5. Keep current CRM Basic Auth dependencies intact while designing a deliberate migration. Do not silently remove Basic Auth or assume it is equivalent to platform identity.
6. Add negative tests for token-type confusion, tenant-owner access to platform routes, revoked operators, missing permissions, and cross-tenant path/body tampering.
7. Deploy only after a staging migration, bootstrap/revocation rehearsal, Postgres integration tests, and process-restart validation. Do not enable platform routes by default before this sequence.

### Additional finding: JARVIS briefing tenant spoofing

The current `POST /jarvis/briefing` handler passes `body.get('tenant_id', 'public')` to the JARVIS bridge. This is request-controlled tenant selection. Before the route is exposed to tenant users, it must use the trusted tenant context and reject missing context; a platform-only version must use an explicit platform permission and must not impersonate a tenant from arbitrary request data.

### P0.1 decision

Until the independent operator identity and token separation exist, global platform routes remain restricted to the current authenticated boundary and P0.1 remains open. Do not grant global access to tenant `owner`, `admin`, or `member`. No production activation, main-branch merge, or production database migration is authorized by this document.
