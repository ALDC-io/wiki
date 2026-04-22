---
tags: [entity, tool, github-actions, ci-cd, deployment]
aliases: [GitHub Actions, GH Actions, Actions]
sources: [daily/2026-04-17.md]
created: 2026-04-17
updated: 2026-04-17
---

# GitHub Actions

ALDC's CI/CD mechanism for building and deploying services hosted on [[Azure]]. Workflows live in each repo under `.github/workflows/`. For the engineering-owned web apps ([[Eclipse]], [[core_api]]), Actions handles container build + push to the container registry + deploy into the Azure **staging slot** — a manual slot swap then promotes to production.

## Primary workflows

### Eclipse repo — **Deploy to Azure (Staging)**

- **Manually triggered** (no auto-deploy on merge)
- Builds the container, pushes to the container registry, deploys into the Production 2 staging slot
- Paired with a manual Azure Portal **swap** step (swap the frontend and backend app services; see [[eclipse-azure-deployment]])

Verification pattern: before swapping, open the workflow run and confirm the **deploy step** shows a successful push to the container registry. Swap before verifying = promote whatever happened to be in staging.

## How ALDC uses Actions (general pattern)

1. Engineer merges to the deploy branch (or manually triggers the workflow)
2. Actions builds Docker image, runs tests (where present), pushes to container registry
3. Deploy step updates the Azure web app's **staging slot** (not production)
4. Engineer verifies in Actions that the deploy step succeeded
5. Engineer opens Azure Portal → **Deployment Slots** → **Swap** to promote to production
6. For Eclipse specifically: swap **both** frontend and backend app services

See [[eclipse-azure-deployment]] for the full runbook.

## What Actions does NOT handle

- **Snowflake deploys** — all SQL is run manually in Snowsight (see [[gep-snowflake-pbi-deployment]])
- **Power BI model deploys** — published manually from PBI Desktop
- **Eclipse connection/template registration** — registered into [[CosmosDB]] via the Eclipse admin UI / API
- **The actual production swap** — Actions pushes to staging; the swap itself is manual in Azure Portal

This keeps deployments gated by a human even when build-side CI succeeds.

## Connector repo: different pattern

The [[connector]] repo does **not** follow the Actions-to-Azure-staging-slot pattern. It uses a Docker-based workflow: SSH to `workstation-agent` → `build.sh` → push to GHCR → deploy via Portainer across test/prod/QA hosts. See [[connector-docker-deployment]].

## Troubleshooting

| Problem | Where to check |
|---------|---------------|
| "Was my container actually pushed?" | Actions run → deploy step output (explicit success/failure) |
| Swap promoted the wrong code | The deploy step may not have completed before swap — verify that step first next time |
| Workflow didn't fire | Workflow is manual-trigger only for the Azure deploys; confirm you actually kicked it off |

## Access / emergency contacts

- Brayden Marshall — `brayden.w.marshall@gmail.com` (should be listed on the repo's contributors / GitHub access for emergencies)

## See Also

- [[eclipse-azure-deployment]] — full deploy runbook using this workflow
- [[Azure]] — hosting target; deployment slots are the handoff point
- [[Eclipse]] — primary service deployed via Actions
- [[core_api]] — also deployed via Actions (same pattern)
- [[connector]] — different deploy pattern (Docker / Portainer, not Actions slot swap)
- [[connector-docker-deployment]] — the connector's alternate deploy runbook
- [[azure-environments]] — where the staging slot + prod slot live (Production 2)
