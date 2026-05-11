---
tags: [ops-platform, launchpad, phase5, credentials, self-serve, onboarding]
created: 2026-05-09
updated: 2026-05-09
---

# Phase 5: Credential Portal & Self-Serve Onboarding

**Boot prompt:** `aldc-shipyard/.claude/commands/launchpad-phase5-creds.md` → `/launchpad-phase5-creds`
**Status:** Planned

## Goal

Build the self-serve credential collection portal and the full self-serve onboarding path.

## Deliverables

1. `connect.analyticlabs.io` — credential portal (OAuth flows, API key inputs, file uploads)
2. Onboarding email integration (Graph API or SMTP)
3. Self-serve onboarding: select industry → connect sources → profiler → dashboard generated
4. Windsor OAuth for Google + Meta (proven on Fusion92)

## Key Constraints

- Credentials in CosmosDB with Fernet encryption
- Windsor.ai proxy for Google, Meta, Bing, Trade Desk
- LWA OAuth for Amazon (direct)
- Fully self-serve — no engineering involvement

## See Also

- [[phase-4-superset]] — Dashboard generation (prerequisite)
- [[phase-6-zeus]] — Zeus integration at onboarding steps
