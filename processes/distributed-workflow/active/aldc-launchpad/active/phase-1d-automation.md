---
tags: [ops-platform, launchpad, credentials, automation, monitoring, active]
created: 2026-05-13
updated: 2026-05-13
---

# Phase 1D: Automation & Monitoring

**Status:** Deferred (starts after 1A-1C proven)
**Effort:** 5–10 days
**Depends on:** Phases 1A-1C

## Goal

Automate credential health monitoring, client reminder chains, link regeneration, Windsor verification, and onboarding email generation. Eliminate manual follow-up for stale credentials.

## Deliverables

1. **Automated reminder chain** — configurable per client/priority:
   - Day 3: gentle email reminder
   - Day 7: urgent, CC EI lead
   - Day 14: red alert + direct outreach trigger
2. **Dashboard aging indicators** — "Pending Xd" with color escalation (blue 1-3d → amber 4-7d → red 8+d)
3. **Link health + auto-regeneration** — scheduled function checks link validity, regenerates if expired
4. **Credential health monitor** — daily Azure Function tests each provisioned credential
5. **Expiry alerts** — Slack webhook when tokens approach expiry
6. **Windsor auto-verification** — poll Windsor API for connection status
7. **Onboarding email integration** — auto-generate one email with ALL submission links per client
8. **Zeus Memory event push** — credential lifecycle → client Zeus staging context

## See Also

- [[phase-1c-prefect-provisioning]] — Prerequisite
- [[../backlog/phase-6-zeus]] — Zeus deep integration builds on this
