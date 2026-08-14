---
tags: [entity, tool, github-actions, ci-cd, deployment, trufflehog, ghcr]
aliases: [GitHub Actions, GH Actions, Actions, silent publish-skip]
sources: [daily/2026-04-17.md, prefect-connectors PR #32 (2026-08-14)]
created: 2026-04-17
updated: 2026-08-14
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

## ⚠ The silent publish-skip failure mode

**The most expensive CI failure at ALDC is not a red build — it is a build that goes red for an
unrelated reason, skips the image publish, and leaves every subsequent run executing old code while
looking healthy.** [[prefect-connectors]] hit this twice, once for **77 days**.

The shape is always the same: a gate *earlier* in the workflow fails → the docker publish job is
**skipped** (not failed) → the registry keeps serving the previous image → runs succeed, tests pass,
and the fix you merged simply is not running.

### Cause 1 — a secret-scanner false positive

TruffleHog's **Lob detector** matches `test_` followed by ~35 lowercase characters — i.e. **any
sufficiently descriptive pytest name**. Four "verified" findings, all of them test function names,
failed the quality gate and skipped the publish.

```bash
trufflehog ... --exclude-detectors=lob
```

Generalise the lesson rather than the flag: a scanner that gates a publish will eventually
false-positive on ordinary code. Know which gate skips the publish, and check the artifact rather
than the verdict.

### Cause 2 — a transient GHCR `denied` **after a successful login**

Login succeeded, push refused — same actor, same package as a run 2½ hours earlier. A plain
`gh run rerun --failed` cleared it. **This is not a permissions problem — do not go pruning packages
or reissuing PATs.**

### Verification rules (both causes)

- **Check the registry's `updated_at`, not the workflow run's conclusion.** The run is a claim; the
  package timestamp is the fact.
- **Poll for the run matching your merge SHA** — never `gh run list --limit=1`. A stale green run
  from an earlier commit will happily convince you an image published when it had not (this misled
  two separate sessions on the same day).
- **An image gate should read the docker *job*, not the run.** A red CI run with a green
  `docker / build-and-push` job has in fact published correctly.

**This is one instance of a wider shape** — a healthy-looking container with no content in it. A
skipped publish job still contributes a conclusion; a green `claude / review` check means the bot
*ran*, not that anything was reviewed. Same family, same fix: read one field deeper than the one you
act on. See [[vacuous-verification]].

## Troubleshooting

| Problem | Where to check |
|---------|---------------|
| "Was my container actually pushed?" | Registry `updated_at` — **not** the run conclusion. Then the publish job's own status |
| "My fix isn't running even though CI is green" | The publish job was **skipped**, not failed — see the silent publish-skip section above |
| Scanner blocks the build on a test file | Likely a detector false positive (TruffleHog Lob vs long `test_` names) — exclude the detector, don't rename the test |
| GHCR `denied` immediately after a successful login | Transient. `gh run rerun --failed`. Not a permissions issue |
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
- [[prefect-connectors]] — where the silent publish-skip was diagnosed (77-day stale image, then the Lob false positive)
- [[schema-dialect-drift]] — the defect that the skipped publish kept hiding; its fix ships in the **image**, so a stale image means the fix is not running
- [[ai-pr-workflow]] — the PR pipeline whose TruffleHog step is the gate in question
- [[vacuous-verification]] — the general pattern: a green check is a claim about work, not evidence of it
