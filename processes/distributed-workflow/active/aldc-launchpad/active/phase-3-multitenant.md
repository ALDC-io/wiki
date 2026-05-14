---
tags: [aldc-launchpad, phase3, snowflake, multi-tenant, rls, warehouse]
created: 2026-05-14
updated: 2026-05-14
deployed_qa: 2026-05-14
commit: fc22007
---

# Phase 3: Multi-Tenant Snowflake Foundation

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase3.md` → `/launchpad-phase3`
**Status:** Deployed to QA — 45/45 isolation tests pass
**Session:** 2026-05-14
**Commit:** `fc22007`

## Goal

Build the multi-tenant Snowflake foundation for onboarding new clients at scale. Single `ALDC_WAREHOUSE` database with `client_id` partitioning, secure view RLS, client registry as single source of truth, and `aldc onboard` CLI for provisioning.

GEP and Fusion92 stay on their existing dedicated databases — this template is for **new clients**.

## Architecture Decisions

- **Secure views for RLS** (not Row Access Policies) — QA account (`og35375`) is Snowflake Standard Edition which doesn't support native Row Access Policies. TENANT schema contains secure views that filter on `CLIENT_ID` via `CURRENT_ROLE()` lookup against `CLIENT_REGISTRY`. Client roles access TENANT views only, never ANALYTICS tables directly. Admin roles (`SYSADMIN`, `ACCOUNTADMIN`, `ALDC_ADMIN`) bypass the filter. Upgrade path: if account moves to Enterprise Edition, swap secure views for native Row Access Policies without changing the client-facing schema.
- **Composite surrogate keys** — `SHA2(CONCAT(CLIENT_ID, '|', ENTITY_ID))` prevents key collisions in shared tables. Pipe separator (not dash) because dashes appear in business keys.
- **Dual-mode coexistence** — `CLIENT_REGISTRY.database_mode`: `'shared'` (ALDC_WAREHOUSE) or `'dedicated'` ({ENV}_DG1_{CLIENT}). Both tracked in same registry.
- **Clustering on CLIENT_ID** — fact tables clustered by `(CLIENT_ID, DATE_KEY)` for scan efficiency.

## Deliverables

| # | Deliverable | File | Status |
|---|---|---|---|
| 1 | ALDC_WAREHOUSE DDL | `warehouse/multitenant/aldc_warehouse.sql` | Deployed QA |
| 2 | Client registry + audit log | `warehouse/multitenant/client_registry.sql` | Deployed QA |
| 3 | Secure view RLS + stored procedures | `warehouse/multitenant/rls_provision.sql` | Deployed QA |
| 4 | RLS test harness | `warehouse/multitenant/test_rls.sql` | 45/45 pass |
| 5 | `aldc onboard` CLI | `cli/aldc_onboard.py` + 3 modules | Built |
| 6 | Deploy script | `warehouse/multitenant/deploy.py` | Tested |
| 7 | platform.json feature updates | `platform/master/data/platform.json` | Done |

## Schema Design

```
{ENV}_ALDC_WAREHOUSE
├── RAW          — connector landing zone, CLIENT_ID first column
├── ANALYTICS    — star schema facts/dims, CLIENT_ID partitioned (admin-only access)
│   ├── DIM_CLIENT             — one row per tenant
│   ├── ECOM_DIM_PRODUCT       — e-commerce product dimension
│   ├── ECOM_DIM_CUSTOMER      — e-commerce customer dimension
│   ├── ECOM_FCT_ORDERLINE     — e-commerce order facts (multi-currency)
│   ├── AGENCY_DIM_FLIGHT      — agency flight/campaign dimension
│   ├── AGENCY_FCT_SPEND       — agency spend facts (CPC/CTR)
│   └── AGENCY_FCT_BUDGET      — agency budget vs actuals
├── TENANT       — client-facing secure views (RLS via CURRENT_ROLE() lookup)
│   ├── DIM_CLIENT, ECOM_DIM_PRODUCT, ECOM_DIM_CUSTOMER, ECOM_FCT_ORDERLINE
│   ├── AGENCY_DIM_FLIGHT, AGENCY_FCT_SPEND, AGENCY_FCT_BUDGET
│   └── SHARED_DIM_COMPANY_CURRENCY_MAP
├── REFERENCE    — shared, no CLIENT_ID
│   ├── SHARED_DIM_DATE        — 2015-2035 (7305 rows)
│   ├── SHARED_DIM_CURRENCY    — USD, CAD, EUR, GBP, MXN, AUD
│   ├── SHARED_DIM_INDUSTRY    — template routing lookup
│   └── SHARED_DIM_COMPANY_CURRENCY_MAP  — per-client consolidation rates
└── ADMIN
    ├── CLIENT_REGISTRY        — master client table (22 columns)
    ├── PROVISIONING_LOG       — immutable audit trail
    ├── V_ACTIVE_CLIENTS       — convenience view
    └── V_RECENT_PROVISIONING  — convenience view
```

## CLI Commands

```bash
python -m cli.aldc_onboard provision <config.json> --env qa   # Full provisioning
python -m cli.aldc_onboard status <client_id> --env qa        # Show status
python -m cli.aldc_onboard list --env qa                      # List all clients
python -m cli.aldc_onboard verify <client_id> --env qa        # RLS isolation test
```

## RLS Flow (Secure Views)

1. TENANT schema has 8 secure views mirroring ANALYTICS tables
2. Each view has `WHERE CLIENT_ID IN (SELECT CLIENT_CODE FROM ADMIN.CLIENT_REGISTRY WHERE CURRENT_ROLE() IN (SNOWFLAKE_ROLE_READ, SNOWFLAKE_ROLE_WRITE, SNOWFLAKE_ROLE_ADMIN))`
3. Client roles get TENANT + REFERENCE access. No ANALYTICS access.
4. Admin roles (`SYSADMIN`, `ACCOUNTADMIN`, `ALDC_ADMIN`) see all rows via OR clause
5. `PROVISION_CLIENT_RLS(client_id, env)` stored procedure creates roles + grants on TENANT/REFERENCE/RAW
6. `DEPROVISION_CLIENT_RLS(client_id, env)` drops roles, marks client suspended

## QA Deployment Results (2026-05-14)

- **Step 1** (DDL): 30/30 — database, 5 schemas, 10 tables, clustering keys, 7305 dates seeded
- **Step 2** (Registry): 9/9 — CLIENT_REGISTRY + PROVISIONING_LOG + GEP/F92 seed + views
- **Step 3** (RLS): 13/13 — TENANT schema, 8 secure views, 2 stored procedures
- **Step 4** (Tests): 45/45 — full isolation test suite pass

Tests verified: ALPHA can't see BETA data, BETA can't see ALPHA data, admin sees all, REFERENCE shared, DIM_CLIENT filtered, cleanup successful.

## Azure Infrastructure (also provisioned 2026-05-14)

| Subscription | Resource Group | Key Vault | Snowflake Secret |
|---|---|---|---|
| Development 2 | rg-aldc-launchpad | aldc-vault-dev | snowflake-admin-nonprod |
| Test 1 | rg-aldc-launchpad | aldc-vault-test | snowflake-admin-nonprod |
| Quality 1 | rg-aldc-launchpad | aldc-vault-qa | snowflake-admin-nonprod |
| Production 2 | rg-aldc-launchpad | aldc-vault-prod | _(prod creds in Dashlane)_ |

## Gotchas

- **Snowflake Standard Edition** does not support Row Access Policies. Discovered during QA deploy. Switched to secure views — same isolation, different enforcement model. If upgrading to Enterprise, swap `rls_provision.sql` back to native RAPs.
- **Snowflake VALUES clause** does not support function calls (SHA2, etc.). Use `SELECT ... UNION ALL` or CTEs for inserts with computed values.
- **Snowflake SQL scripting** uses `:=` for variable assignment, not `SET` (which is for session variables).
- **PowerShell + az CLI** strips inner JSON quotes when passing to `az keyvault secret set --value`. Use `--file` with a temp file instead.
- **Python subprocess on Windows** needs `az.cmd` not `az`.

## What's Next

- E2E test: provision a real test client via CLI, run data through the pipeline
- Connector framework update: shared-mode clients need connector writes routed to `ALDC_WAREHOUSE.RAW`
- Phase 4 (Superset) depends on this — secure views extend to Superset dashboard permissions
- Prod deployment: deploy to `wj66376.canada-central.azure` when ready

## See Also

- [[phase-2-connector-activation]] — API services reused by CLI
- [[../ops-platform/backlog/phase-3-multitenant|ops-platform Phase 3]] — original backlog entry (superseded)
- [[phase-0-monorepo-restructure]] — monorepo where this lives
