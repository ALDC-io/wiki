---
tags: [ops-platform, launchpad, phase4, superset, dashboard-generation]
created: 2026-05-09
updated: 2026-05-09
---

# Phase 4: Superset Integration

**Boot prompt:** `aldc-shipyard/.claude/commands/launchpad-phase4.md` → `/launchpad-phase4`
**Status:** Planned

## Goal

Deploy Apache Superset, build the dashboard template engine, and enable programmatic per-client dashboard generation.

## Deliverables

1. Superset deployment (Docker, self-hosted Azure, Snowflake connection)
2. Dashboard template library per industry (ecommerce, nonprofit, sports, consulting, association)
3. Template engine: client_code + industry → Superset dashboard JSON → import via API
4. RLS integration: Superset roles auto-created per client with client_id filter
5. `aldc onboard` Superset provisioning step

## Key Constraints

- Self-hosted Superset (not Preset managed)
- Templates must be industry-specific but client-configurable
- Embeddable for future client portal (connect.analyticlabs.io)
- RLS aligned with Snowflake (same client_id filter)

## See Also

- [[phase-3-multitenant]] — Snowflake RLS (prerequisite)
- [[phase-5-credentials]] — Credential portal serves embedded dashboards
