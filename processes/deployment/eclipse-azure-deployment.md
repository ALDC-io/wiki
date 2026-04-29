---
tags: [process, deployment, eclipse, azure, github-actions]
aliases: [Eclipse Azure deployment, Eclipse deploy process, Azure staging swap]
sources: [daily/2026-04-17.md, session/2026-04-28, session/2026-04-29]
created: 2026-04-17
updated: 2026-04-29
---

# Eclipse → Azure Deployment (GitHub Actions + Slot Swap)

Runbook for deploying [[Eclipse]] (and similar [[Azure]] web apps like [[core_api]]) from the Eclipse repo's [[GitHub Actions]] workflow to production via a staging-slot + **swap** pattern.

## App Service Names (Production 2 / `aldcprodrsgp1c`)

| Role | App Service | Staging Slot URL |
|---|---|---|
| Frontend | `aldcprodwbapeclipse1c01` | `aldcprodwbapeclipse1c01-stage.azurewebsites.net` |
| Backend | `aldcprodwbapcore1c01` | `aldcprodwbapcore1c01-stage.azurewebsites.net` |

Both are in **Production 2** subscription, resource group `aldcprodrsgp1c`.

## TL;DR

1. Trigger **"Deploy to Azure App Service"** workflow manually for **`eclipse-2.1` branch + "Production (Eclipse 2.1)" environment** → deploys to `stage` slot
2. Do the same for `core_api` if backend changes are included (note: `core_api` has no real deploy workflow yet — deployed via another mechanism)
3. Verify changes on the staging URL before swapping
4. **Swap backend first**, then swap frontend — wait for backend swap to complete before starting frontend
5. If something's wrong, swap back (swap is bidirectional)

> **Default branch (2026-04-29):** Both `ALDC-io/eclipse` and `ALDC-io/core_api` now use `eclipse-2.1` as the GitHub default branch. This ensures the real deploy workflow (`deploy_az_webapp.yaml`) is visible in the Actions UI and prevents accidental deployments from `main` (which contains only dummy workflow stubs). See § Pitfalls for the incident that prompted this change.

## Detailed steps

### 1. Kick off the GitHub Actions workflow

- Repo: `ALDC-io/eclipse` (not [[clients-repo]])
- Actions tab → **"Deploy to Azure App Service"** → **Run workflow**
- Branch: `eclipse-2.1` (this is the default branch — it should already be selected)
- Environment: `Production (Eclipse 2.1)`
- **Manually triggered** — merging to `eclipse-2.1` does NOT auto-deploy; it only runs the CI quality gate
- **CRITICAL: Do NOT use "Deploy a container to an Azure Web App"** — that is a dummy/stub workflow that does nothing. The only real deploy workflow is **"Deploy to Azure App Service"** (`deploy_az_webapp.yaml`)

This workflow builds the Next.js app (`npm install && npm run build`) and deploys to the **`stage` slot** of `aldcprodwbapeclipse1c01`.

### 2. Verify the container push succeeded

Before swapping, confirm the deploy succeeded:

- Open the GitHub Actions run for the workflow
- Inspect the **deploy step** output — it should show a successful push to the container registry
- If that step failed, do **not** swap. Fix the root cause and re-run the workflow

### 3. Swap the staging slot into production — backend first

**Order matters when frontend + backend changes ship together.** New frontend code calls new API endpoints — if you swap frontend first, those calls 404 against the old backend.

1. **Backend first:** Azure Portal → `aldcprodwbapcore1c01` → Deployment slots → Swap (stage → production). Wait for completion.
2. **Frontend second:** Azure Portal → `aldcprodwbapeclipse1c01` → Deployment slots → Swap (stage → production).

If only frontend changes shipped, order doesn't matter — but doing backend first is always safe.

### 4. Verify the staging URL before swapping

- Frontend staging: `https://aldcprodwbapeclipse1c01-stage.azurewebsites.net`
- Login with any account in the `user` CosmosDB container (staging CosmosDB: `aldctestcsdb1c01`, database: `core`)
- The `user` container holds Eclipse UI users. `auth_user` holds machine OAuth clients — do not confuse them

### 5. Rolling back

If production is broken after swap, swap again — this points production back at the previous (now-staging) slot. This is the standard rollback; you don't need a redeploy to revert.

## Pitfalls

- **Deploying from `main` branch** — `main` contains only dummy/stub workflows (`deploy_az_webapp_container.yaml`, `build_docker_image.yaml`, `deploy_on_premise.yaml` — all just echo statements). Deploying from `main` does nothing useful and **overwrites the Actions UI** so the real workflow ("Deploy to Azure App Service") disappears from the sidebar. The default branch was changed to `eclipse-2.1` on 2026-04-29 to prevent this. If it happens again: change the default branch back to `eclipse-2.1` in Settings → General, or trigger the workflow via CLI: `gh workflow run 137914444 --repo ALDC-io/eclipse --ref eclipse-2.1 -f environment="Production (Eclipse 2.1)"`. See § Incident: 2026-04-29 wrong-branch deploy below for the full post-mortem
- **Swapping frontend before backend** — new frontend code calls new API endpoints; 404s result if backend isn't already on the new version
- **Forgetting the second swap** — frontend-only or backend-only swaps leave the endpoint out of sync with its backend
- **Confusing staging slot vs TEST 1 subscription** — this runbook deploys to the staging **slot inside Production 2**. TEST 1 is a separate subscription. Don't conflate the two
- **Wrong Azure subscription** — the prod apps are in **Production 2** subscription. If `az webapp show --name aldcprodwbapeclipse1c01` returns nothing, run `az account set --subscription "Production 2"` first
- **core_api has no real deploy workflow** — `deploy_az_webapp_container.yaml`, `build_docker_image.yaml`, and `deploy_on_premise.yaml` in `ALDC-io/core_api` are all dummy placeholder workflows (just echo statements). The backend is deployed via a different mechanism — clarify before assuming GitHub Actions handles it
- **Metrics card visuals for testing** — test Metrics Card / YoY features in the **GEP account** (`da8904db`), not Fusion92 (`0fc00e34`). GEP has the Metrics Card visuals with `show_previous_period: true`. YoY tooltip only appears with timeframes under 1 year

## Incident: 2026-04-29 wrong-branch deploy

### What happened

On 2026-04-28/29, the **"Deploy a container to an Azure Web App"** workflow was triggered from the `main` branch for both `ALDC-io/eclipse` and `ALDC-io/core_api`, intending to deploy the YoY Metrics Card feature (eclipse PR #75 + core_api PR #233). Both PRs were correctly merged into `eclipse-2.1`, but the deploy was run from `main`.

### Why it broke

1. **`main` branch is stale.** The `main` branch's latest commits were from April 10 (eclipse) and April 13 (core_api) — CI quality gate PRs only. It does not contain any feature work from `eclipse-2.1`.
2. **The wrong workflow was used.** "Deploy a container to an Azure Web App" (`deploy_az_webapp_container.yaml`) is a **dummy workflow** on all branches — it just runs `echo`. The real workflow is "Deploy to Azure App Service" (`deploy_az_webapp.yaml`), which only exists on `eclipse-2.1`.
3. **GitHub Actions UI shows workflows from the default branch.** When `main` was the default branch, the Actions sidebar reflected `main`'s workflow files. After the dummy workflow ran from `main`, the real "Deploy to Azure App Service" workflow disappeared from the UI because it didn't exist on `main`.

### Impact

The SKU Profitability app (`navira-demo`) broke for GEP users. Symptoms:
- Sidebar showed "SKU Profitability" as a **grouped dropdown** with "navira-demo" and "Admin" as child items (old `Navbar.tsx` behavior from before PR #69 / DV-364)
- Clicking "navira-demo" loaded a **mangled iframe URL** (`https://navira-demo.analyticlabs.io//navira-demo` instead of `https://navira-demo.analyticlabs.io/`) because the old `Application.tsx` appended the URL slug to the app URL
- The SKU Profitability dashboard did not display

Root cause: the code running in production was the old `main` branch code, which predated PR #69 (DV-364 — "Simplify External Apps", merged 2026-04-20). PR #69 had flattened the navbar to show apps as direct links and fixed the iframe URL construction.

### Resolution

1. **Immediate rollback:** Slot swap in Azure Portal for both `aldcprodwbapeclipse1c01` and `aldcprodwbapcore1c01` — swapped staging back to production, restoring the pre-incident code
2. **Default branch change:** Changed the default branch from `main` to `eclipse-2.1` for both `ALDC-io/eclipse` and `ALDC-io/core_api` repositories. This ensures:
   - The real "Deploy to Azure App Service" workflow appears in the Actions UI
   - The branch dropdown defaults to `eclipse-2.1` when triggering workflows
   - Prevents accidental deployment from `main`

### Prevention

- **Always deploy from `eclipse-2.1`** — this is the active development branch for both repos
- **Use "Deploy to Azure App Service"** — the only real deploy workflow. All other deploy-named workflows are dummies
- The default branch change to `eclipse-2.1` is the primary guardrail going forward

## Related flows

- [[connector-docker-deployment]] — different pattern: connector uses Portainer + workstation-agent Docker builds, not slot swaps
- [[gep-snowflake-pbi-deployment]] — the data-side deploy (Snowflake SQL + PBI model refresh). Totally independent of the Azure app deploy

## Eclipse 2.0 Azure deployment

Eclipse 2.0 is the next-generation portal (Next.js / Node). Its Azure deployment differs from the legacy slot-swap pattern — it uses a standard Azure Web App with Oryx build-in-place rather than GitHub Actions + container registry.

### Steps

1. **Create an Azure Web App** for the new environment (Runtime: Node; OS: Linux)
2. **Copy config from an existing node app** (or create from scratch). Template — substitute your environment values:
   ```json
   [
     { "name": "api_token",                    "value": "<bearer-token — generate fresh per env>" },
     { "name": "api_url",                      "value": "https://aldctestfnapcore1c01.azurewebsites.net/v1/" },
     { "name": "NEXT_PUBLIC_domain",           "value": "https://eclipse2-test.aldc.io" },
     { "name": "NEXT_PUBLIC_PASSPHRASE_LENGTH","value": "14" },
     { "name": "NEXT_PUBLIC_stac_key",         "value": "<storage-account-key>" },
     { "name": "NEXT_PUBLIC_stac_name",        "value": "aldcteststacportal1c01" },
     { "name": "NEXTAUTH_SECRET",              "value": "{{ECLIPSE2_NEXTAUTH_SECRET}}" },
     { "name": "NEXTAUTH_URL",                 "value": "https://eclipse2-test.aldc.io" },
     { "name": "SCM_DO_BUILD_DURING_DEPLOYMENT","value": "true" }
   ]
   ```
   `NEXTAUTH_SECRET` and `api_token` values: see `vault/infra-credentials.md` § Eclipse 2.0.
3. **Create a staging slot** (Deployment Slots → Add slot) so you can swap between staging and production
4. **Deploy code** — push to the Web App; wait for Oryx build to complete (5–10 min). Do not interact with the Azure resource during the Oryx build — it is fragile and breaks when interrupted
5. **Create Cloudflare DNS** — add CNAME in [[Cloudflare]] pointing the new domain (e.g. `eclipse2-test.aldc.io`) to the Azure Web App default hostname
6. **Copy application metadata** from an existing environment using Azure Cosmos Data Explorer (manual step)
7. **Create superuser** via Postman — call the create-user endpoint with role assignment

### Key differences vs legacy Eclipse deployment

| | Legacy Eclipse (slot-swap) | Eclipse 2.0 |
|---|---|---|
| Build | GitHub Actions → container registry → staging slot | Oryx build-in-place on Azure Web App |
| Deploy trigger | Manual GitHub Actions workflow | Push to Web App (SCM) |
| DNS | Existing CNAMEs, unchanged by swap | New CNAME per environment in Cloudflare |
| Superuser | Created via Portal deploy step | Created via Postman API call |

## See Also

- [[Eclipse]] — the service being deployed (platform concept page)
- [[entities/repos/eclipse|eclipse (repo)]] — the Next.js 14 UI repo; "Eclipse 2.0" in this runbook refers to the `eclipse` repo (`repos/eclipse/`), deployed via `deploy_az_webapp.yaml`
- [[GitHub Actions]] — the workflow layer that builds and pushes to the staging slot
- [[Azure]] — hosting platform
- [[azure-environments]] — subscription model; explains Production 2 vs TEST 1
- [[Cloudflare]] — CNAMEs eventually fronted by the web apps; unchanged by swap
- [[core_api]] — same deployment pattern
