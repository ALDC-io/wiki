---
tags: [concept, pattern, snowflake, automation, testing, sandbox]
aliases: [sandbox feature delivery, per-feature schema, test schema isolation]
sources: [entities/projects/workflow-automation.md, GP-207, GP-208, gep-snowflake-pbi-deployment]
created: 2026-04-18
updated: 2026-04-18
---

# Sandbox Feature Delivery (Per-Feature Schema Pattern)

A pattern for isolating in-flight data warehouse changes from each other during development and testing, using per-ticket Snowflake schemas within a shared test environment. Designed for the ALDC stack where a shared prod→test data share is available and Power BI workspace provisioning is manual-only.

> **Origin**: designed in [[workflow-automation]] as the practical sandbox for the GEP automated feature-delivery loop. Extracted here as a reusable pattern applicable to any ALDC client with the same Snowflake + PBI setup.

---

## The Problem

Multiple in-flight feature branches writing to a shared `WAREHOUSE.*` schema in `TEST_DG1_GEP` cause collisions: deploy A overwrites tables that deploy B is currently validating. The traditional workaround (per-engineer personal schemas like `WAREHOUSE_TEST_PAUL`) is informal, undocumented, and not tied to the feature lifecycle.

---

## The Pattern

For each in-flight feature, auto-create a dedicated schema named after the ticket:

```
TEST_DG1_GEP.WAREHOUSE_TEST_<TICKET_ID>
```

- **Created**: when `deploy.py` runs for the first time against that ticket
- **Isolated**: views and tables for this feature land here, not in `WAREHOUSE.*`
- **Shared source data**: all schemas in `TEST_DG1_GEP` read from the same `PROD_DG1_GEP` data share — production data volumes, no maintenance required
- **Torn down**: explicitly via `deploy.py --teardown`, or manually after the feature is validated and promoted

```
PROD_DG1_GEP (data share, read-only)
  ↓  (GP-207 inbound share — mounted permanently)
TEST_DG1_GEP
  ├── WAREHOUSE.*               ← permanent; used by GEP Test Models PBI
  ├── WAREHOUSE_TEST_GP208.*    ← feature GP-208 in-flight
  ├── WAREHOUSE_TEST_GP210.*    ← feature GP-210 in-flight
  └── WAREHOUSE_TEST_<ticket>   ← next feature...
```

---

## Lifecycle

| Event | Action |
|---|---|
| Engineer starts deploy for ticket X | `deploy.py` runs `CREATE SCHEMA IF NOT EXISTS WAREHOUSE_TEST_X` |
| Deploy + validation pass | Schema stays live for PBI smoke-test |
| PBI smoke-test passes; PR merged to development | `deploy.py --teardown` drops `WAREHOUSE_TEST_X` |
| Feature promoted to user-testing / main | PROD deploy targets `PROD_DG1_GEP.WAREHOUSE.*` directly (no per-feature schema needed in prod) |

---

## Why True Ephemeral Isn't Achievable Today

The full "ephemeral environment" ideal — one isolated Snowflake schema + one isolated PBI workspace per branch — breaks at the Power BI layer. As of 2025, Microsoft's Power BI REST API does not expose public endpoints for:
- Programmatically creating or deleting workspaces
- Deploying `.pbix` files at scale
- Scripting the Explore/smoke-test flow

The Snowflake half is fully automatable. The PBI half is not. The practical sandbox is therefore:

| Layer | Isolation | Automated? |
|---|---|---|
| Snowflake schema | Per-feature (`WAREHOUSE_TEST_<ticket>`) | ✅ |
| Snowflake task chain | Triggered per-deploy | ✅ |
| PBI workspace | Shared (`GEP Test Models`) | ❌ Manual |
| Prod→test data | Shared (GP-207 share, always current) | ✅ (infrastructure) |

---

## Applying This Pattern to a New Client

Requirements:
1. A test Snowflake environment exists (e.g., `TEST_DG1_<CLIENT>`)
2. A prod→test data share is mounted (equivalent of [[GP-207]] for GEP)
3. `deploy.py` is parameterized with `--client` and `--env` flags

If requirement 2 is missing (no data share), the per-feature schema is still valid but will reference the test environment's own source tables (potentially smaller/staler than production). The isolation benefit still applies; the data-volume parity benefit does not.

---

## Related Tooling

- `deploy.py` — creates the schema, runs SQL files, triggers task chain. See [[workflow-automation]] §3.4.
- `validate.py` — runs universal + ticket-specific checks against the schema. See [[workflow-automation]] §3.5.

---

## See Also

- [[workflow-automation]] — full design doc; this pattern is instantiated for GEP there
- [[GP-207]] — the prod→test data share that makes per-feature schemas viable (production data volumes in test)
- [[snowflake-data-share-refresh]] — share refresh failure modes to be aware of when designing these schemas
- [[gep-snowflake-pbi-deployment]] — deployment runbook this pattern extends
- [[GEP]] — primary client where pattern is first applied
