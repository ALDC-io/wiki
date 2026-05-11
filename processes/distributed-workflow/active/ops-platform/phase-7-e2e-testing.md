---
tags: [ops-platform, launchpad, phase7, testing, e2e, validation]
created: 2026-05-09
updated: 2026-05-09
---

# Phase 7: E2E Testing

**Boot prompt:** `aldc-shipyard/.claude/commands/launchpad-phase7.md` → `/launchpad-phase7`
**Status:** Planned

## Goal

Validate the complete Launchpad platform end-to-end with a synthetic test client.

## Deliverables

1. Synthetic test client "TestCorp" (e-commerce, 3 connectors, individual tier)
2. Full flow: wizard → client.yaml → aldc onboard → credentials → data flowing → Superset dashboard
3. Onboarding time: target < 30 minutes
4. Regression: existing clients (GEP, Fusion92) unaffected
5. Multi-tenant isolation validation (Snowflake RLS, Superset RLS, Zeus sub-tenant)
6. Security review (`/security-review`)
7. Wiki documentation: final architecture, runbook, deployment guide

## Key Constraints

- Test client uses the self-serve path (no engineering shortcuts)
- Must validate isolation in all 3 systems
- Performance target: < 30 minutes wizard to data flowing

## See Also

- [[phase-6-zeus]] — All features complete (prerequisite)
- [[phase-0-design-system]] — Where it started
