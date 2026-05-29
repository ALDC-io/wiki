---
tags: [process, deployment, azure-functions, credential-exchange, gep, report-export, runbook]
aliases: [func-aldc-cred deploy, credential-exchange deploy, report export deploy, Data Model export]
created: 2026-05-29
updated: 2026-05-29
---

# Credential-Exchange Function Deploy & GEP Report Export

Runbook for deploying the `func-aldc-cred-qa` Azure Function and for the GEP
"Data Model" / "Validation Report" Excel export it produces — plus the manual
upload fallback when the timer is down. Captured from the GP-276 marketing-spend
fix + write_only deploy ([[GP-200]], 2026-05-29).

## The function app

| Property | Value |
|---|---|
| Name | `func-aldc-cred-qa` |
| Subscription / RG | **Quality 1** / `rg-aldc-launchpad` |
| Plan | **Y1 Dynamic (Consumption)** — 1.5 GB memory ceiling, 5-min default timeout |
| Runtime | **Linux, PYTHON\|3.11** |
| Key Vault | **`aldc-cred-vault-qa`** (`KEY_VAULT_URL` + `SNOWFLAKE_VAULT_URL` both point here) — holds `eclipse-storage-da8904db`, `eclipse-postgres-test`, `snowflake-admin-nonprod`. Reachable only from inside Azure. |
| Source | `aldc-launchpad/api/credential-exchange/` |

Hosts the credential-exchange endpoints **and** the report export:
- `export_data_model_timer` — timer trigger, **15:00 UTC daily**
- `export_data_model_http` — `POST /api/reports/export` (function-key auth), body `{"clientCode":"GEP"}`

## Deploy procedure (the hard-won part)

> **Two traps cost a full debug cycle on 2026-05-29 — read these first.**

1. **`func` needs Python 3.11 on PATH.** The local default `python` may be 3.14,
   which makes `func azure functionapp publish` abort with a version-mismatch +
   `ArgumentException: Destination is too short` CLI crash. Put 3.11 first:
   ```bash
   export PATH="/c/Users/PaulRussell/AppData/Local/Programs/Python/Python311:$PATH"
   python --version   # must report 3.11.x
   ```
   (`py -3.11` confirms it's installed.)

2. **`az functionapp deployment source config-zip` does NOT work here.** On Linux
   Consumption Python apps it **silently no-ops** — exit 0, no output, **zero
   deployments registered**, function list stays empty. Do not trust its exit
   code. The only working method is `func publish` with remote build:
   ```bash
   cd api/credential-exchange
   az account set --subscription "Quality 1"
   func azure functionapp publish func-aldc-cred-qa --build remote
   ```
   `--build remote` runs Oryx on the Azure 3.11 agent (installs
   `requirements.txt`); local deps/venv are irrelevant. Success = it prints the
   indexed function list (incl. `export_data_model_timer`). Verify:
   `az functionapp function list ... --query "[].name"`.

3. **`.funcignore` must exclude `*.xlsx`** — the local build artifacts (Data
   Model ~38 MB, Validation Report ~8 MB) live in the function dir and would
   otherwise bloat the package.

### Clean deploy of report code only (skip in-progress credential work)

The function dir often has uncommitted, not-yet-working credential changes
(`function_app.py`, `host.json`, `providers/`, `windsor.py`). To ship only
committed report code, stash those, deploy from clean HEAD, restore:
```bash
git stash push -u -m "deploy isolation" -- \
  api/credential-exchange/function_app.py \
  api/credential-exchange/host.json \
  api/credential-exchange/providers/__init__.py \
  api/credential-exchange/providers/windsor.py \
  "api/credential-exchange/Data Model.xlsx" \
  "api/credential-exchange/GEP Validation Report.xlsx"
# ... func publish ...
git stash pop
```
`func publish` deploys the **working tree**, not git HEAD — so the stash is what
makes the deploy clean.

## openpyxl memory: write_only is mandatory

The Data Model OrderLine sheet is ~290K rows. The standard openpyxl cell model
OOMs the 1.5 GB Y1 plan (this is why the timer silently failed for weeks). Both
builders in `services/report_export.py` use **write_only** mode:
- `Workbook(write_only=True)`; sheets via `create_sheet` (no `wb.active`)
- styled/formatted cells = `WriteOnlyCell`; rows via `ws.append([...])`
- column widths via `ColumnDimension(ws, min=i, max=i, width=w)` **before** appending
- Excel Tables need **explicit** `tab.tableColumns = [TableColumn(id=i+1, name=h) ...]`

Measured after the rewrite: Data Model build peak heap **51 MB**, total RSS
**757 MB**, full export **HTTP 200 in ~101 s** on the live Y1 function (well under
the 5-min cap). No `functionTimeout` is set in `host.json` (defaults to 5 min) —
fine at current data volume, but raise it (max 10 min) if rows grow materially.

## Marketing tab business rule

`MARKETING_FCT_ACTIVITY.SPEND_MODEL` is a **pricing-model label** (CPC / VCPM /
UNKNOWN, derived in [[GP-199]]) — **not** dollars. The dollar spend is `COST`.
Surface them as separate columns (`Spend Model` + `Spend`/`Cost`); never alias
`SPEND_MODEL` as a financial metric.

## Manual upload fallback (when the timer is down)

The portal serves `Data Model.xlsx` + `GEP Validation Report.xlsx` from blob
`aldcteststac1cda8904db/files/`, registered in portal Postgres `app_report`
(account_id 19 = GEP, rows id 50 + 55). To push corrected files from a laptop:

1. **Build locally** via `ReportExportService` in Development mode
   (`AZURE_FUNCTIONS_ENVIRONMENT=Development` writes to `api/credential-exchange/`).
2. **Storage key** — `aldcteststac1cda8904db` is invisible to ARM in all 4
   subscriptions, and `eclipse-storage-da8904db` is NOT in `aldc-vault-test`
   (`aldc-credential-vault` won't even resolve from a laptop — private endpoint).
   Pull the key the way the portal does: **Eclipse TEST CosmosDB
   (`aldctestcsdb1c01`) → `core` DB → `account_secret` container → doc
   `id='da8904db'` → field `storage_sas_1`** (an 88-char account key, mis-named
   "sas"). Cosmos creds: `clients/ALDC_ENG/eclipse/connections/eclipse_test1c01.json`.
3. **Upload** both files to container `files`, `overwrite=True`, xlsx
   content-type + `attachment` content-disposition.
4. **Bump freshness:** `UPDATE app_report SET updated_datetime = now() WHERE
   file_path IN ('Data Model.xlsx','GEP Validation Report.xlsx') AND
   account_id = 19` on `aldctestpgdbportal1c01` (DB `eclipse`).

**Postgres firewall:** `aldctestpgdbportal1c01` (Test 1, `aldctestrsgp1c`) blocks
by IP. Laptop runs need a firewall rule (e.g. `paul_russell_launchpad` →
`24.85.224.160`, residential/dynamic — may rotate). Azure-hosted workloads
already pass via the existing `AllowAllAzureServicesAndResourcesWithinAzureIps`
(0.0.0.0) rule — so the firewall is never the *timer's* blocker.

Local-only helper: `aldc-launchpad/scripts/_upload_reports_to_portal.py`
(hardcoded PG creds — not committed).

## See Also

- [[GP-200]] — Amazon UK orders; holds the dated session log for this work
- [[GP-199]] — ASIN attribution; defines `SPEND_MODEL`
- [[dashboard]] — Eclipse portal report-row mechanism (`app_report` + `app_group_reports`)
- [[Eclipse]] · [[Snowflake]] · [[Azure]]
- [[eclipse-azure-deployment]] — the *web-app* (Eclipse/core_api) deploy, different from this function deploy
