---
tags: [process, deployment, eclipse, azure, github-actions, docker, containers]
aliases: [Eclipse Azure deployment, Eclipse deploy process, Azure staging swap]
sources: [daily/2026-04-17.md, session/2026-04-28, session/2026-04-29, session/2026-06-17]
created: 2026-04-17
updated: 2026-06-17
---

# Eclipse → Azure Deployment (GitHub Actions + Slot Swap)

Runbook for deploying [[Eclipse]] (and similar [[Azure]] web apps like [[core_api]]) from the Eclipse repo's [[GitHub Actions]] workflow to production via a staging-slot + **swap** pattern.

> **⚠ CORRECTION (2026-06-17) — Eclipse is now CONTAINER-deployed. This supersedes the code-deploy guidance below.**
>
> The App Service runs a **Docker image** from GHCR (`linuxFxVersion = DOCKER|ghcr.io/aldc-io/eclipse:<tag>` on **both** slots — verified on `aldcprodwbapeclipse1c01`). Because of that:
> - **`deploy_az_webapp.yaml` ("Deploy to Azure App Service") is a NO-OP.** It builds Next.js and pushes to `wwwroot`, which a container App Service **ignores entirely**. Every run "succeeds" but changes nothing the running app serves. Do **not** use it.
> - **The real deploy is the container pipeline:** **`deploy_az_webapp_container.yaml` ("Deploy to Azure (Staging)")** — build + push image, deploy to the `stage` slot. Run it **manually (`workflow_dispatch`)**, not on push.
>
> **Correct procedure (proven 2026-06-17):**
> 1. `gh workflow run 194355199 --repo ALDC-io/eclipse --ref eclipse-2.1 -f force_deploy=true`
>    (Workflow id `194355199` = "Deploy to Azure (Staging)". Use `force_deploy=true` whenever the **stage image ≠ prod image** — its `rollback-check` blocks otherwise. That mismatch is the normal steady state, so you almost always need `force_deploy=true`.)
> 2. Wait for `rollback-check → build → deploy`. The image is tagged by GitVersion (currently `2.0.0-eclipse-2-1.1`) and deployed to the **`stage` slot**.
> 3. **Verify on the stage slot** (`https://aldcprodwbapeclipse1c01-stage.azurewebsites.net`) that the new behaviour is actually served — see § Verifying a container deploy. Allow ~1–2 min for the container to fully roll (mixed old/new instances appear briefly).
> 4. **Swap `stage` → `production`** (`az webapp deployment slot swap -g aldcprodrsgp1c -n aldcprodwbapeclipse1c01 --slot stage --target-slot production`) and re-verify on `eclipse.analyticlabs.io`.
> 5. Rollback = swap back.
>
> **Known gotchas:** GitVersion reuses the same tag across builds (**mutable tag** → both slots can share a tag and the rollback net is degraded; push unique tags ideally). The **push-triggered** auto-staging deploy fails every merge by design (can't pass `force_deploy`) — ignore that failure, use manual dispatch. Production URL is `eclipse.analyticlabs.io` (NOT the stale `eclipse.aldc.io`, which is the legacy Pages-Router app).

## App Service Names (Production 2 / `aldcprodrsgp1c`)

| Role | App Service | Staging Slot URL |
|---|---|---|
| Frontend | `aldcprodwbapeclipse1c01` | `aldcprodwbapeclipse1c01-stage.azurewebsites.net` |
| Backend | `aldcprodwbapcore1c01` | `aldcprodwbapcore1c01-stage.azurewebsites.net` |

Both are in **Production 2** subscription, resource group `aldcprodrsgp1c`.

## TL;DR

> **Contradiction (2026-06-17):** the original TL;DR below used the **code-deploy** workflow ("Deploy to Azure App Service"). That is a **no-op** for the now-containerized app — see the ⚠ CORRECTION callout above for the current, correct container procedure. The **swap** and **verify-before-swap** principles below still hold; only the build/deploy-to-stage mechanism changed.

1. ~~Trigger **"Deploy to Azure App Service"**~~ → **superseded.** Trigger **"Deploy to Azure (Staging)"** manually (`workflow_dispatch`) on `eclipse-2.1` with `force_deploy=true` → builds the Docker image + deploys to `stage` slot
2. Do the same for `core_api` if backend changes are included (note: `core_api` has no real deploy workflow yet — deployed via another mechanism)
3. **Verify changes on the staging slot before swapping** (this step is non-negotiable — skipping it caused the 2026-06-17 incident)
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

> **Contradiction (2026-06-17):** the line that said *"CRITICAL: Do NOT use the container workflow — it's a dummy stub; the only real one is Deploy to Azure App Service"* is now **INVERTED**. The App Service was switched to run a Docker container, so:
> - `deploy_az_webapp.yaml` ("Deploy to Azure App Service") = **no-op** (pushes code to `wwwroot`, which the container ignores).
> - `deploy_az_webapp_container.yaml` ("**Deploy to Azure (Staging)**") = **the real deploy** (builds + pushes the image, deploys to `stage`). Use this, via manual `workflow_dispatch` with `force_deploy=true`.
>
> Use the container procedure in the ⚠ CORRECTION callout at the top. The step below describes the obsolete code-deploy and is kept only for historical context.

This (obsolete) workflow built the Next.js app (`npm install && npm run build`) and deployed to `wwwroot` of the **`stage` slot** — which a containerized App Service does not serve.

### 2. Verify the deploy actually changed what's SERVED (not just that the run was green)

Before swapping, confirm the new behaviour is genuinely being served by the **stage slot** — a green workflow run is **not** sufficient (see § Incident: 2026-06-17):

- Open the GitHub Actions run for **"Deploy to Azure (Staging)"** — `rollback-check`, `build`, and `deploy` jobs must all be green
- Confirm the stage slot's image updated: `az webapp config show -n aldcprodwbapeclipse1c01 -g aldcprodrsgp1c --slot stage --query linuxFxVersion -o tsv`
- **Functionally verify on the stage URL** that the changed feature is present (§ Verifying a container deploy). If it isn't there, do **not** swap

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
- **core_api deploy workflow — STALE NOTE CORRECTED (2026-07-23, GP-299/GP-300).** `core_api` now HAS a real, working container deploy, same pattern as eclipse: **"Deploy to Azure (Staging)"** (`deploy_az_webapp_container.yaml`, workflow id `192556804`) → `rollback-check → build → deploy` to the **`stage` slot** of backend **`aldcprodwbapcore1c01`** (Production 2, RG `aldcprodrsgp1c`). Run manually (`gh workflow run 192556804 --repo ALDC-io/core_api --ref eclipse-2.1 -f force_deploy=true`). Notes: (1) the **push-triggered** auto-run on merge to `eclipse-2.1` **fails by design** (can't pass `force_deploy`) — ignore it, use manual dispatch; (2) `force_deploy=true` is normally required because the mutable GitVersion tag makes stage≠prod trip `rollback-check`; (3) then **swap** `az webapp deployment slot swap -g aldcprodrsgp1c -n aldcprodwbapcore1c01 --slot stage --target-slot production` (rollback = swap back, time-sensitive due to the mutable tag); (4) `jwt_secret` is **slot-specific** — a stage-minted token 401s on prod, so smoke-test prod with a prod-minted token or the prod frontend. (`build_docker_image.yaml` is the reusable build; `deploy_on_premise.yaml` remains a stub.)
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

## Verifying a container deploy

A green workflow + healthy `HTTP 200` proves the app boots — **not** that your change is live. Verify the changed behaviour is actually served:

- **Image check:** `az webapp config show ... --slot stage --query linuxFxVersion` shows the expected `DOCKER|ghcr.io/...:<tag>`.
- **Bundle check (no UI needed):** log in (a Playwright script works) and grep the loaded JS chunks for a string unique to your change. If absent, the running container is stale.
- **UI check:** exercise the actual feature. Allow ~1–2 min after deploy/restart — during rollout you can hit **mixed old/new instances** (one request shows the new bundle, another shows the old menu). Re-check until results are consistent before swapping.
- **Mutable-tag caveat:** GitVersion currently reuses the same tag (`2.0.0-eclipse-2-1.1`) across builds, so a restart may not re-pull. If a deploy doesn't take, restart the slot and re-verify; ideally push **unique per-build tags**.
- A reusable lite smoke for the Visuals "Duplicate" feature lives (uncommitted) at `repos/eclipse/e2e/duplicate-visual.smoke.mjs`; credentials in `vault/eclipse-smoke-login.env`.

## Incident: 2026-06-17 — code-deploy no-op + swap regression

### What happened
Deploying eclipse PR #80 (Duplicate-visual button) using the **documented** runbook — "Deploy to Azure App Service" (`deploy_az_webapp.yaml`) + slot swap — the feature never appeared in production despite the workflow succeeding.

### Why it broke
1. **The App Service runs a Docker container** (`DOCKER|ghcr.io/aldc-io/eclipse:<tag>`). `deploy_az_webapp.yaml` pushes Next.js to `wwwroot`, which the container **ignores** — a silent no-op. (Confirmed: deployed `wwwroot/.next` files were fresh and *did* contain the feature, but the running container never reads them.)
2. **The runbook was stale** — it named the code-deploy as "the only real workflow" and the container workflow as a "dummy stub." That was true once; the app was later switched to containers, inverting it.
3. **Swapping before verifying served content** then **regressed production** for ~1 hour from `2.0.0-eclipse-2-1.1` to the older April `2.0.0-DV-364-simple-external-apps.1` image (a slot swap exchanges the container image between slots). Detected via `az monitor activity-log` and restored by swapping back.

### Resolution
Deployed correctly via the **container** pipeline: `gh workflow run 194355199 --ref eclipse-2.1 -f force_deploy=true` → verified the feature on the **stage** slot → swapped to production → re-verified on `eclipse.analyticlabs.io` (Edit/Duplicate/Delete present, modal pre-fills "<name> (copy)").

### Prevention
- **Use the container workflow** ("Deploy to Azure (Staging)", manual dispatch, `force_deploy=true`). The code-deploy workflow is a no-op for this app.
- **Always verify served content on the stage slot before swapping** (§ Verifying a container deploy). A green run is not verification.
- **Never swap before that verification** — a swap mutates production (and exchanges container images between slots).

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
