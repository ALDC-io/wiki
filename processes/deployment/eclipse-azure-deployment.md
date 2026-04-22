---
tags: [process, deployment, eclipse, azure, github-actions]
aliases: [Eclipse Azure deployment, Eclipse deploy process, Azure staging swap]
sources: [daily/2026-04-17.md]
created: 2026-04-17
updated: 2026-04-17
---

# Eclipse → Azure Deployment (GitHub Actions + Slot Swap)

Runbook for deploying [[Eclipse]] (and similar [[Azure]] web apps like [[core_api]]) from the Eclipse repo's [[GitHub Actions]] workflow to production via a staging-slot + **swap** pattern.

## TL;DR

1. Trigger **"Deploy to Azure (Staging)"** GitHub Actions workflow manually (Eclipse repo → Actions)
2. Watch the workflow; confirm the deploy step shows the push to the container registry succeeded
3. In Azure Portal → the Eclipse web app → **Deployment Slots**, click **Swap**
4. Repeat the swap for **both the frontend and backend app services** — don't forget either
5. If something's wrong, swap back (swap is bidirectional)

## Detailed steps

### 1. Kick off the GitHub Actions workflow

- Repo: the Eclipse repo (not [[clients-repo]])
- Actions tab → **Deploy to Azure (Staging)**
- **Manually triggered** (no auto-deploy on merge)

This workflow builds the container and pushes it to the container registry, then deploys into the **staging slot** of the Production 2 web app.

### 2. Verify the container push succeeded

Before swapping, confirm the deploy succeeded:

- Open the GitHub Actions run for the workflow
- Inspect the **deploy step** output — it should show a successful push to the container registry
- If that step failed, do **not** swap. Fix the root cause and re-run the workflow

### 3. Swap the staging slot into production

- Azure Portal → the web app (e.g., `Eclipse 1` for the portal, `Eclipse 2` for the node — see [[azure-environments]] for domain mapping) → **Deployment Slots**
- Click **Swap**
- This repoints the production hostname at the formerly-staging slot. The previous production slot becomes the new staging slot (so swap is reversible)

### 4. **Swap both halves**

Eclipse has two app services that must stay in sync:

- **Frontend** (Eclipse 1 / portal)
- **Backend** (Eclipse 2 / node)

Run swap on **both**. Forgetting one leaves the public endpoint out of sync with its backend — a common failure mode.

### 5. Rolling back

If production is broken after swap, swap again — this points production back at the previous (now-staging) slot. This is the standard rollback; you don't need a redeploy to revert.

## Pitfalls

- **Forgetting the second swap** — frontend-only or backend-only swaps are a leading cause of confusing post-deploy behavior
- **Confusing staging slot vs TEST 1 subscription** — this runbook deploys to the staging **slot inside Production 2**. TEST 1 is a different thing (a separate subscription shared with clients). Don't conflate the two
- **Swap does not redeploy** — if you swap before verifying the container push succeeded, you'll promote whatever was already in staging. Always check the Actions run first

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
