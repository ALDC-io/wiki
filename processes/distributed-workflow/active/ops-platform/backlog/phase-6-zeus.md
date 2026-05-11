---
tags: [ops-platform, launchpad, phase6, zeus, intelligence, automation]
created: 2026-05-09
updated: 2026-05-09
---

# Phase 6: Zeus Deep Integration

**Boot prompt:** `aldc-shipyard/.claude/commands/launchpad-phase6.md` → `/launchpad-phase6`
**Status:** Planned

## Goal

Integrate Zeus Memory and Zeus Chat at every wizard step and client lifecycle touchpoint.

## Deliverables (7 integration points + 3 features)

1. Wizard Profile: live Zeus Memory search on client name
2. Wizard Framework: industry patterns from existing deployments
3. Wizard Profiler: Zeus Chat explains profiling results
4. Wizard Infra: actual Snowflake costs from QBO invoices
5. Wizard Security: compliance requirements from meeting transcripts
6. Wizard Generate: Zeus Chat reviews client.yaml
7. Post-deploy: onboarding progress tracking, stall detection, follow-up email drafting
8. Attribution + confidence scoring (universal, not per-site)
9. CRM pipeline integration (demos.aldc.io → Eclipse EXP)

## Key Constraints

- `mcp__ccx__cce_memory_search` for all Zeus queries
- Per-client Zeus sub-tenants aligned with Snowflake client_id
- CCX repo patterns for MCP tool integration

## See Also

- [[phase-5-credentials]] — Self-serve flow (prerequisite)
- [[phase-7-e2e-testing]] — Full validation
