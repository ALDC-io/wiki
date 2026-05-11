---
tags: [ops-platform, launchpad, phase3, snowflake, multi-tenant, rls]
created: 2026-05-09
updated: 2026-05-09
---

# Phase 3: Multi-Tenant Foundation

**Boot prompt:** `aldc-shipyard/.claude/commands/launchpad-phase3.md` → `/launchpad-phase3`
**Status:** Planned

## Goal

Build the multi-tenant Snowflake foundation: single ALDC_WAREHOUSE database with client_id partitioning, automated RLS policies, client registry, and `aldc onboard` CLI.

## Deliverables

1. Snowflake DDL: ALDC_WAREHOUSE with RAW, ANALYTICS, REFERENCE, ADMIN schemas
2. `ADMIN.client_registry` table: maps client_code → Snowflake role, Zeus tenant, Superset connection, Prefect pool
3. RLS automation script: creates Snowflake role + RLS policies per client
4. `aldc onboard` CLI stub: reads client.yaml, provisions Snowflake tenant
5. Update `data/platform.json`: mark `automated-rls` and `client-yaml-gen` as done

## Schema Design

```
ALDC_WAREHOUSE
├── RAW          — ingested data, client_id partitioned
├── ANALYTICS    — transformed facts/dims, client_id partitioned
├── REFERENCE    — shared (exchange rates, benchmarks, catalog)
└── ADMIN        — client_registry, connector_config, onboarding_status
```

## Key Constraints

- Multi-tenant default, dedicated DB as premium tier
- RLS code-controlled and testable
- Service account credentials via CosmosDB

## See Also

- [[phase-2-platform-dashboard]] — Architecture tab shows this model
- [[phase-4-superset]] — Superset integration depends on this
