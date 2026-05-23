---
tags: [security, multi-tenant, client-portal, audit]
aliases: [Portal Isolation Audit]
created: 2026-05-14
updated: 2026-05-14
status: pending_signoff
---

# Client Portal — Multi-Tenant Isolation Audit

The Client Portal is a single deployment serving every client. This document records the
isolation layers that prevent client A from seeing client B's data, charts, dashboards,
or AI memories, and the manual probes that must pass before flipping `portal.enabled = true`
on a client in `shared/client-registry.json`.

## The 8 isolation layers

| # | Layer | Mechanism | Source of truth |
|---|---|---|---|
| 1 | Session | HMAC token signed with `PORTAL_HMAC_SECRET`, client_code in payload, 30-day TTL, HttpOnly+Secure+SameSite=Lax cookie | `api/portal-auth/services/portal_tokens.py` |
| 2 | API endpoints | Every endpoint reads `client_code` from session claims via `_require_session()`, never from request body or query params | `api/portal-auth/function_app.py` |
| 3 | Superset guest token | Token embeds `rls_clause = "client_id = '{client_code}'"`; Superset enforces on every dataset query | `api/portal-auth/services/superset_guest.py` |
| 4 | Superset role | `ALDC_CLIENT_{code}` role; RLS rule scoped to the role; dashboard owners + roles lists | `superset/rls_provisioner.py` |
| 5 | Cube JWT | JWT payload `{clientId}`; `queryTransformer` in `cube/cube.js` appends `DimClient.clientId = ?` filter to every query | `cube/cube.js`, `api/portal-auth/function_app.py` cube_query endpoint |
| 6 | Snowflake TENANT secure views | `CURRENT_ROLE()` lookup in secure views filters every query under the client role | `warehouse/multitenant/aldc_warehouse.sql` |
| 7 | Zeus instance | Per-client instance (zeus-memory#131) or shared-tagged with `client_code` tag on every memory write/query | `cli/zeus_provisioner.py`, `api/portal-auth/services/zeus_client.py` |
| 8 | Library CRUD | Save/list/compose endpoints always pass `client_code` from session into `library_service`, which scopes to the client's registry-resolved dashboard_id | `api/portal-auth/services/library.py` |

## Probes (must all pass before sign-off)

Run these with two different sessions (client A = GEP_PREFECT, client B = FUSION92, or
two test clients):

### P1. Session forgery
- [ ] Verify `PORTAL_HMAC_SECRET` is not the dev default `dev-portal-insecure`. Inspect Function App settings → `@Microsoft.KeyVault(...)` reference; rotate if it ever leaks.
- [ ] Modify the `portal_session` cookie's payload (e.g. change `client_code` to another client) — `/api/portal/session` must 401 because the HMAC won't match.

### P2. Cross-client library probe
- [ ] Log in as client A. POST `/api/portal/library/save-chart` with a forged body trying to reference client B's dashboard_id. Confirm the endpoint ignores body-supplied IDs and writes to client A's dashboard.
- [ ] GET `/api/portal/library/charts` — must only return charts attached to client A's dashboard. Repeat for `/library/dashboards`.

### P3. Superset role isolation
- [ ] Impersonate the `ALDC_CLIENT_GEP_PREFECT` role in Superset UI (admin → switch role). Confirm only datasets bound to the GEP RLS rule are queryable.
- [ ] Try to load FUSION92's dashboard via direct URL — must 403 or show "no access" because the role isn't on the FUSION92 dashboard's roles list.

### P4. Cube JWT injection
- [ ] Manually generate a Cube JWT with no `clientId` in payload. POST `/cubejs-api/v1/load`. Confirm Cube rejects with `clientId is required in the Cube security context` (from `cube.js:30`).
- [ ] Generate a JWT with `clientId: 'GEP_PREFECT'`. Query a measure. Confirm only GEP rows returned.

### P5. Zeus tenancy
- [ ] In shared_tagged mode: ask client A's Zeus instance "what did client B do last week?" — Zeus must not return facts tagged with B. (Zeus enforces tag-isolation at retrieval.)
- [ ] In per_client mode: forge a request to `/instances/{B_instance}/chat` with client A's session — Zeus admin layer must reject because the session client_code doesn't match the instance owner.

### P6. Snowflake row leak
- [ ] Connect to QA Snowflake as the GEP Superset service user. `SELECT * FROM ANALYTICS.ECOM_FCT_ORDERLINE LIMIT 100`. Confirm `CLIENT_ID` column only shows `GEP_PREFECT` rows.

### P7. CORS lockdown
- [ ] Inspect `superset/superset_config.py:CORS_OPTIONS.origins` — must list only `https://portal.analyticlabs.io` and approved internal domains, no `*`.
- [ ] Inspect Cube `CUBEJS_CORS_ALLOWED_ORIGINS` env var on the ACI — same.
- [ ] Inspect `infra/portal-functions.bicep:cors.allowedOrigins` — same (plus `http://localhost:4280` for dev only on QA/UAT, never prod).

### P8. Magic-link replay
- [ ] Use a magic-link invite token. Confirm it sets `portal_session` and that the invite token cannot be reused for a different client (HMAC mismatch).
- [ ] Capture an expired invite token. Confirm `/api/portal/auth/{token}` rejects with 403 + the "invalid or expired" HTML page.

## Operational guardrails

- New client portal access goes through `python -m cli.portal_provision <CODE> --env qa`. The script writes `superset.role_id`, `superset.dataset_ids`, `portal.superset_dashboard_uuid` into `shared/client-registry.json` and grants the client's role write permission only on their own dashboard.
- `portal.enabled = true` flag in `client-registry.json` is the single switch that exposes the portal to that client. Default is `false`.
- F92 and any other existing client stay `enabled: false` until their probes pass.
- Rotate `PORTAL_HMAC_SECRET` on any suspected leak. Existing sessions invalidate; users get new magic links.

## Sign-off

Before `portal.enabled = true` on client X:
- [ ] All 8 probes above passed for client X
- [ ] `PORTAL_HMAC_SECRET` in Key Vault, not dev default
- [ ] Superset CORS, Cube CORS, Function App CORS all locked to portal domain
- [ ] Audit performed by: ____________ on: ____________
- [ ] Approved for production: ____________
