---
tags: [workflow, zeus-memory, phase-4, onboarding, self-service, oauth]
aliases: [Zeus Memory Phase 4, Tenant Onboarding Automation]
sources: []
created: 2026-05-02
updated: 2026-05-02
---

# Phase 4 — Tenant Onboarding Automation

**Priority:** 4 · **Status:** Blocked on Phase 3

## Objective

Make tenant onboarding fully self-service. A new customer signs up, connects their tools through OAuth flows, selects what to ingest, and the system handles everything automatically — no ALDC engineering intervention required.

## Prerequisites

- [ ] Phase 3 complete — batch migration orchestration working
- [ ] OAuth flows designed and tested for each connector
- [ ] Tenant provisioning pipeline defined

## Deliverables

### Self-Service Onboarding Wizard
Step-by-step flow for new tenants:
1. Create account / accept invite
2. Connect data sources (OAuth for each tool)
3. Select scope (which Confluence spaces, Jira projects, Git repos)
4. Review and confirm
5. Trigger initial migration
6. Monitor progress

### OAuth Integration
No manual credential pasting — proper OAuth flows for:
- Confluence Cloud (Atlassian OAuth 2.0 3LO)
- Jira Cloud (same Atlassian OAuth app)
- GitHub (GitHub App or OAuth App)
- GitLab (OAuth 2.0)

### Scope Selection UI
- Browse available Confluence spaces → select/deselect
- Browse Jira projects → select/deselect
- Browse Git repos → select/deselect
- Estimate migration size (page count, issue count, repo size)

### Automated Provisioning
- Tenant account creation (database records, storage allocation)
- Knowledge base initialization (empty tenant KB ready for ingestion)
- Connector configuration (store OAuth tokens, selected scopes)
- Migration job creation and trigger

### Onboarding Health Check
After migration completes, verify the knowledge base is healthy:
- Expected document count matches source (within tolerance)
- No critical errors in any connector
- Cross-source relationships populated
- Drift detection baseline established

### Documentation
- Support runbook for troubleshooting failed onboardings
- Admin guide for manual intervention when needed
- Tenant-facing FAQ

## Acceptance Criteria

- [ ] New tenant can onboard without ALDC engineering intervention
- [ ] OAuth flows work for Confluence Cloud, Jira Cloud, GitHub
- [ ] Onboarding takes < 1 hour for a typical enterprise (100–500 Confluence pages, 50–200 Jira issues, 5–20 Git repos)
- [ ] Health check validates completeness after migration
- [ ] Support runbook written and tested

## User Testing Consideration

The 75-person Food Bank Canada demo surfaces an opportunity: if the product reaches user-testing stage, different roles stress-test it differently:

| Role | Tests | Focus |
|---|---|---|
| CEO | Strategic value, ROI, adoption friction | Does this save time? |
| Engineer | API reliability, edge cases, error handling | Does this break? |
| Product Owner | Workflow fit, feature gaps, user stories | Does this solve the right problem? |
| DevOps | Deployment, scaling, monitoring | Can we run this? |
| QA | Edge cases, data integrity, regression | What did we miss? |

A workshop format with role-specific test scripts could be valuable.

## Boot Prompt

````
You are resuming the Zeus Memory workstream, Phase 4: Tenant Onboarding Automation.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read the workstream hub: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\README.md`
3. Read this phase: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-4-tenant-onboarding-automation.md`
4. Read Phase 3 (orchestration): `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-3-batch-migration-orchestration.md`

Plan mode rule: plan-mode on first session.
Checkpoint per `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § Checkpoint.
````

## Session Log

_(append sessions here)_

## See Also

- [[../README]] — workstream hub
- [[phase-3-batch-migration-orchestration]] — prerequisite (batch migration)
- [[zeus-memory]] — product entity page
