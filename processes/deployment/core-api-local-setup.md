---
tags: [process, deployment, core-api, local-setup, runbook, api]
aliases: [core_api local setup, running core_api locally, core_api dev setup]
sources: [daily/2026-04-17.md]
created: 2026-04-17
updated: 2026-04-17
---

# Running core_api Locally — Developer Runbook

End-to-end guide to get [[core_api]] running on your machine, point [[Postman]] at it, trigger endpoints (especially warehouse-rebuild), and debug failures. This is the canonical onboarding runbook for any developer who needs to work on core_api — follow it top-to-bottom the first time.

> Runbook scope: **Azure Functions Python app running locally**, backed by real prod/qa/test Azure resources (no local CosmosDB or storage). You point local core_api at the same CosmosDB and storage accounts the deployed environments use — env-switching happens by swapping which block in `local.settings.json` is active.

> **Gotchas this runbook will save you from** (all confirmed 2026-04-17 during Paul's first setup):
> - Local URLs are `http://localhost:7071/v1/...`, **not** `/api/v1/...` — `host.json` sets `routePrefix: ""`
> - The HTTP trigger is `authLevel: anonymous`; `x-function-key` is irrelevant locally (the app does its own auth in the `Authorization` header)
> - The `Authorization` header is a raw base64 of `client_id:client_secret` — **no** `Bearer ` or `Basic ` prefix (Postman's built-in Basic Auth will break this)
> - Postman variable precedence is env > collection — keep `bearer_token` OFF environments or it silently clobbers the pre-request-computed value

## Prerequisites

### 1. Python 3.11 (in a virtualenv)

core_api **requires Python 3.11**. Newer versions fail to build `pyarrow==15.0.0` (no Windows wheels for 3.13+), and older versions fail the Azure Functions Python worker pin in `requirements.txt`.

Install Python 3.11 if you don't already have it:

```bash
# Recommended — registers with the py launcher cleanly
winget install Python.Python.3.11
# Alternatives: python.org installer (check "Add to PATH" + "Install launcher"),
# or Microsoft Store (py launcher sometimes doesn't see Store installs).

# Verify
py -3.11 --version   # should print Python 3.11.x
```

Then create the venv and install deps:

```bash
# From the core_api repo root
py -3.11 -m venv .venv
source .venv/Scripts/activate   # Git Bash; cmd/PowerShell: .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

If `pip install` fails with `ModuleNotFoundError: No module named 'pkg_resources'` while building `pyarrow`, you're on the wrong Python. Delete `.venv`, confirm `py -3.11 --version` works, recreate the venv.

### 2. Azure Functions Core Tools

Install the Core Tools CLI (`func`) — needed to run Azure Functions locally:

- Install via `npm install -g azure-functions-core-tools@4 --unsafe-perm true` (Node 18+ required)
- Or use the VS Code Azure Functions extension's bundled version
- Confirm with `func --version` (should report v4.x)

### 3. Azure extension for VS Code (optional)

Only needed if you want to press F5 to debug or pull prod settings directly. CLI-only workflow works fine without it. If you install, **Azure Tools** (or specifically **Azure Functions**):

- **Reads `local.settings.json`** to populate env vars when you press F5 / "Start Debugging"
- Lets you pull settings from a deployed function app directly (e.g., `aldcprodfnapcore1c01 → Application Settings`) — useful if `local.settings.json` drifts from prod
- Shows logs and trigger invocations live

Steven's note: populating local env vars by pulling directly from `aldcprodfnapcore1c01`'s Azure portal env vars (specifically `STORAGE_SAS1`, `STORAGE_SAS2`) is the fallback if the shared `local.settings.json` is stale.

### 4. `local.settings.json`

This file is **required** and must not be committed. Get it from the vault:

- Path in repo: `core_api/local.settings.json`
- Reference: `vault/core-api-local-settings.md` (gitignored) — contains the full JSON Steven shared

Confirm `local.settings.json` is in core_api's `.gitignore` before creating it.

### 5. [[Postman]] setup

See [[postman-collections]] for the full design rationale. Short version — the clean, team-shareable setup:

1. **Generate the import artifacts** by running the extractor script in the vault:
   ```bash
   python C:/Users/PaulRussell/repos/wiki/vault/postman-build.py
   ```
   Output: 6 files in `C:/Users/PaulRussell/postman-exports/` (2 collections + 4 envs).

2. **Install the Postman Desktop Agent** (one-time, ~20s silent install) if you plan to use the Postman web app. The browser sandbox can't reach `localhost:7071`; the agent is a small helper Postman's web app talks to. Download link appears inline the first time you try a localhost request. Alternative: use the Postman desktop app, which hits `localhost` natively with no agent.

3. **Create a team workspace** in Postman (`ALDC — core_api` or similar) so other engineers inherit the same collection/env setup.

4. **Import all 6 files** via Postman → Import → drag the folder.

5. **Delete `bearer_token` from any env it shows up in.** If you imported a previously-exported env (not generated by `postman-build.py`), it will have this variable. Leaving it there — even empty — silently breaks auth. See the bearer-token gotcha callout at the top of this page. `postman-build.py` already omits it, but existing exports from the vault's daily file include it.

6. **Verify**: select the `LOCAL` env, open `core_api (new) → dataset → list`, set `account_id` = an existing account (e.g. `8425e311` for Kit & Ace, or `f49f9aa3` for a Fusion-style), Send. Expect `HTTP 200` with `"client master": true, "client id": "FFFFFFFF0000"`.

## Run core_api locally

### Option A — CLI (primary)

```bash
# Activate venv first
source .venv/Scripts/activate   # Git Bash; cmd/PowerShell: .venv\Scripts\activate

# From the core_api repo root
func start
```

First boot takes 20–60s on Windows while the worker imports pyarrow/pandas/snowflake. Watch for the single registered function `v1` with route template `v1/{function:alpha}/{option:alpha}` — this is a catchall; all endpoints route through it to the appropriate `route_*.py` module internally. That's why you **don't** see 50+ endpoints listed.

Confirm the host is up from another shell:
```bash
curl -s http://localhost:7071/admin/host/status
# Expect {"state":"Running", ...}
```

### Option B — VS Code (optional)

1. Open the core_api repo in VS Code
2. Ensure the Python interpreter selected is the 3.11 venv (`.venv\Scripts\python.exe`)
3. Ensure `local.settings.json` is in place
4. Press **F5** (or Run → Start Debugging). The Azure Functions extension spawns `func start` with the local settings loaded as env vars
5. Same endpoints as Option A

## Smoke test (curl, no Postman)

Fastest way to prove the whole stack is up end-to-end — works before you touch Postman:

```bash
# Base64 of MASTER_CLIENT_ID:MASTER_CLIENT_SECRET from local.settings.json
BEARER="RkZGRkZGRkYwMDAwOmFsRGM5ODc2IQ=="

curl -s -X POST \
  -H "Authorization: $BEARER" \
  -H "Content-Type: application/json" \
  "http://localhost:7071/v1/account/list?debug=full" \
  -d '{}'
```

Expect a JSON payload starting with `"response": { "code": 200, ..., "payload": [...] }` and `"request": { "client master": true, "client id": "FFFFFFFF0000", ... }`. Anything else — 404, 500 inside a 200 envelope, or `client master: false` — see the common-failures table below.

> Note the URL: `/v1/...`, **not** `/api/v1/...`. `host.json` sets `routePrefix: ""` so the default `/api/` prefix is suppressed.

## Choosing which environment to point at

`local.settings.json` has four top-level blocks — `Values` (active), `_test_values`, `_qa_values`, `_prod_values`. To switch environments:

1. Stop the local function host
2. Move the current `Values` contents into e.g. `_prod_values` (if they were prod)
3. Copy the target env's block into `Values`
4. Restart `func start`

Local core will now talk to that env's CosmosDB, storage, subscription, etc. Be careful — pointing local runs at **prod** means you're mutating real production CosmosDB documents if you hit write endpoints.

## Key endpoint: warehouse rebuild

The main reason most devs run core_api locally: debugging why warehouse data is wrong.

- **File**: `route_warehouse.py`
- **Function**: `warehouse_recreate_current`
- **What it does**: rebuilds the data that feeds the `CURRENT_*` and combined views in [[Snowflake]]

Wire-up:

1. Local core_api running (`func start`)
2. Postman → `core_api (new)` collection → find the `warehouse_recreate_current` request (under `application` or `dataset` — confirm by searching the collection)
3. Set `account_id` (collection variable) to the client you're debugging (Fusion, GEP, etc.)
4. Fire — the request hits `http://localhost:7071/v1/warehouse/recreate_current` (or the route the request already has baked in)
5. Watch the terminal for errors
6. Check [[Snowflake]] **Query History** for any failed queries the rebuild emitted
   - Use the `ACCOUNTADMIN` role to see the **un-redacted** version of query text (otherwise parameters are masked and debugging is much harder)

See [[debugging-warehouse-loads]] for the full investigation workflow that wraps this endpoint.

## Verifying the service principal works

If core_api can't read CosmosDB / storage / the resource group, the service principal in `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` / `AZURE_TENANT_ID` has lost access. Test by:

1. Open the target CosmosDB (`aldcprodcsdb1c01` for prod) in Azure Portal
2. Access control (IAM) → check the service principal has `Contributor` or `Cosmos DB Account Reader Role`
3. If missing, someone with owner permissions must grant it

## Common failures

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `pyarrow` build fails with `ModuleNotFoundError: No module named 'pkg_resources'` | Venv on Python 3.13/3.14 — no Windows wheel for pyarrow 15.0.0 on those versions, pip falls back to source build and trips on setuptools | Install Python 3.11 (`winget install Python.Python.3.11`), delete `.venv`, recreate with `py -3.11 -m venv .venv` |
| `func: command not found` | Azure Functions Core Tools not installed | See Prereq 2 |
| Python errors about missing modules at `func start` | Wrong Python version (not 3.11) or venv not activated | Recreate venv with `py -3.11`; activate before `func start` |
| `401 Unauthorized` from CosmosDB | `COSMOS_KEY` is stale or rotated | Pull fresh key from Azure Portal → CosmosDB → Keys; update `local.settings.json` |
| `Storage: AuthenticationFailed` | `AzureWebJobsStorage` / `STORAGE_SAS*` expired | Regenerate in Azure Portal → Storage account → Shared access signature / Access keys |
| Postman: *"Postman Desktop Agent required"* | Browser sandbox blocks localhost from Postman web | Install the Postman Desktop Agent (download link in the error), or use the Postman desktop app |
| Postman 200 OK but response `"code": 500` with `JSONDecodeError: Expecting value` and `client authenticated: false` | `{{bearer_token}}` resolved to an empty string — an env var named `bearer_token` is overriding the collection-scoped value set by the pre-request script. Postman precedence is env > collection | Delete the `bearer_token` variable from every environment (it should only live on the collection, computed at send time by the pre-request script) |
| `HTTP 404` to a `/api/v1/...` URL | Wrong prefix. `host.json` sets `routePrefix: ""` | Use `/v1/...` — no `/api/` segment |
| Postman hangs forever on local call | Azure Functions host isn't running or on wrong port | Confirm `func start` is up; `curl http://localhost:7071/admin/host/status` should return `{"state":"Running"}` |
| Request works in Postman against prod URL but not local | Usually an env not selected, or the request uses `Basic Auth` instead of raw bearer | Active env in the top-right dropdown; confirm `Authorization` header is literally `{{bearer_token}}` (no `Basic`/`Bearer ` prefix) |
| `warehouse_recreate_current` succeeds but data still wrong | Stale template in [[CosmosDB]] `schema` container OR upstream source issue | Escalate to [[debugging-warehouse-loads]] |

## Old core vs new core

- **New core** (current) — targeted by **Steven's Dax and Core Collection**. Daily driver
- **Old core** (legacy) — targeted by **Analytic Labs Control v1 (LAWRENCE)**. Kept for reference; most endpoints still resolve but the repo has diverged
- **Fusion Netsuite Sandbox API** — separate legacy collection, rarely used anymore

If a bug is reported against an endpoint that only exists in Lawrence's collection, you're probably dealing with old-core territory — confirm with the team which runtime the failing caller is hitting.

## Security notes

- `local.settings.json` contains real prod/test/qa secrets. **Never commit it**, never paste it in Slack, email, or the daily notes
- If it leaks, rotate the service principal secret, CosmosDB keys, storage SAS, GPT key, and Mailjet secret — full list in `vault/core-api-local-settings.md`
- Paul has already captured a cleanup action to scrub the raw secrets out of `daily/2026-04-17.md` — see [[action-items]]

## See Also

- [[core_api]] — entity overview
- [[postman-collections]] — collection-by-collection reference + clean workspace design
- [[Postman]] — tool overview
- [[Azure]] — hosting / resource layout
- [[azure-environments]] — which Azure resources map to which env
- [[CosmosDB]] — what's on the other end of `COSMOS_*` env vars
- [[debugging-warehouse-loads]] — when you're here because a warehouse load is wrong
- [[Snowflake]] — where `warehouse_recreate_current` ultimately writes; also where the query history lives
- `vault/core-api-local-settings.md` — actual secrets (gitignored)
- `vault/postman-build.py` — regenerates the 6 Postman import artifacts from `daily/2026-04-17.md` (gitignored)
