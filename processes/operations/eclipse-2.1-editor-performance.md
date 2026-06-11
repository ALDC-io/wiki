---
tags: [process, operations, eclipse, eclipse-2.1, performance, power-bi, explorer, runbook]
aliases: [Eclipse 2.1 Editor Slowness, Visual Editor Performance, Explorer Visual Lag, Lori Slow Eclipse]
sources: [conversation 2026-06-11 (Lori Beck "creating visuals for Heather is soooo slow"), repos/eclipse src/app/(app_shell)/explorer/view EditVisual.tsx, repos/core_api v1/route_dataset.py + v1/__init__.py, CosmosDB core (capacity/dataset/explorer_visual), Azure App Service metrics + Log Analytics, Power BI executeQueries timing]
created: 2026-06-11
updated: 2026-06-11
---

# Eclipse 2.1 — Visual Editor Performance (Slow "Build a Visual")

Investigation runbook + root-cause record for **slowness while creating/editing visuals** in the
[[entities/repos/eclipse|eclipse (repo)]] 2.1 Explorer (`eclipse.analyticlabs.io`). Companion to
[[eclipse-incident-response]] (connector-outage recovery) — same **read-only-triage-first** discipline,
different failure class (UI/data-query, not pipeline). First worked end-to-end on the **2026-06-11**
report from **Lori Beck** ("creating visuals in Eclipse for Heather and it is soooo slow").

## TL;DR (root cause)

It is **not** the server, **not** Snowflake, and **not the user's machine**. The Explorer visual
**editor re-runs the full data query (Power BI `executeQueries` DAX, ~3–4 s each) on every
un-debounced field/measure/sort change**, with no de-dup or cancellation. Building one table fires a
*storm* of heavy DAX queries — **~16 s of cumulative backend wait for a 5-edit table** — and repeats
don't cache. Amplified hourly when the model's 4–7 min refresh overlaps editing.

**Fix:** debounce the value that drives the live `<Visual>` preview (frontend), add a timeout/retry to
the backend `executeQueries` (resilience). See § Remediation.

## Principle: clear the infrastructure read-only before touching code

All triage below is read-only (Azure metrics, Log Analytics, CosmosDB reads, a service-principal DAX
*read*). No prod mutation. Confirm at the **consumer layer** (the actual DAX against the live model),
per the evidence-gated rule — don't infer from "the app feels slow".

## Step 1 — Clear the web tier (Azure App Service metrics)

Eclipse 2.1 runs on **Azure App Service `aldcprodwbapeclipse1c01`** (P1v3, Always-On, single worker),
sharing plan `aldcprodapspnode1c101` with the v2 backend `aldcprodwbapcore1c01` (Linux container,
`ghcr.io/aldc-io/core-api`), the node app, and flight-check. Sub **Production 2** / RG `aldcprodrsgp1c`.

```bash
az account set --subscription "Production 2"
# UI + backend response time / errors / CPU (name-form avoids Git-Bash path mangling on full ARM IDs)
az monitor metrics list --resource aldcprodwbapeclipse1c01 -g aldcprodrsgp1c --resource-type Microsoft.Web/sites \
  --metric AverageResponseTime Http5xx Requests --interval PT1H --offset 6h -o table
az monitor metrics list --resource aldcprodapspnode1c101 -g aldcprodrsgp1c --resource-type Microsoft.Web/serverfarms \
  --metric CpuPercentage MemoryPercentage --interval PT1H --offset 6h -o table
```

**2026-06-11 result:** UI response **6–130 ms**, **0× HTTP 5xx**, plan CPU **~6 %** (15 % peak),
memory flat **48 %**; v2 backend **<360 ms**, 0× 5xx. The web tier is healthy and idle — **not the
cause.** There is **no Power BI / Fabric capacity in any Azure subscription** (`Microsoft.PowerBIDedicated/capacities`
+ `Microsoft.Fabric/capacities` both empty) → the model runs on **Power BI SaaS** (Premium/PPU),
invisible to `az`.

## Step 2 — Trace the exact visual → dataset → capacity path (CosmosDB `core`)

Visuals query through `UI → /api/coreAPI → core_api v2 → Power BI executeQueries (DAX) → semantic model`.
Find what the user is actually building (Cosmos conn from `vault/core-api-local-settings.md` or
`az cosmosdb keys list --name aldcprodcsdb1c01 -g aldcprodrsgp1c --type connection-strings`):

- `user` → the person (e.g. `lori.beck@aldc.io`).
- `explorer_visual` (filter recent by `_ts`) → their visuals + `data_view_id` + `account_id`.
- `explorer_data_view` → `dataset_id`; `dataset` → `capacity_id` + `capacity_options`.
- `capacity` → provider + `workspace_id`/`service_client_id`/`impersonation` (PBI) **or**
  `service_password_core/report` (Snowflake). PBI secret is in **`encrypted_options`** (Fernet).

**2026-06-11 result:** Lori (account `da8904db` = Navira/GEP) edited four **Table** visuals
("Sales by SKU w/RR% - Table", etc.) 19:22–19:50 UTC → data-view **"Data Model – Full View"** →
dataset **"Sales Model"** → capacity `87888186…` = **Power BI** (`provider=data_model`),
workspace `de58032f…`, PBI dataset `74a529b3…` ("Data Model"), **RLS impersonation `heather.tabor@gep.aldc.io`**.
(Corroborates [[GP-259]]/[[GP-256]]: all 38 Navira dashboards bind to "Sales Model".)

## Step 3 — Measure the DAX at the consumer layer (service principal)

The PBI SP secret is encrypted in `capacity.encrypted_options` with **Fernet** using the backend's
`ENCRYPTION_KEY` app setting (`core_api/v1/func_common.py` `encrypt`/`decrypt`). Decrypt it, get a
client-credentials token (tenant `e2bae64b…`, scope `https://analysis.windows.net/powerbi/api/.default`),
then time `POST /v1.0/myorg/groups/{ws}/datasets/{ds}/executeQueries` with the visual's DAX and
`impersonatedUserName` = the capacity's impersonation user. (Read-only; mirrors what the app does.)

**2026-06-11 metrics** (Sales Model, 5000-row SKU table, impersonating Heather):

| Measure | Result |
|---|---|
| Model storage mode | **Import (`Abf`)** — Snowflake not in live path; queries hit the in-memory model |
| Model refresh | **Hourly, ~4–7 min each** (e.g. 18:00→18:04, 19:00→19:07, 20:00→20:05) |
| One query (SKU + Product Name + Gross + Buy Box % + Return Rate %) | **~3.2–3.9 s** |
| Adding the Return Rate % measure | +~1.2 s (2.6 s → 3.8 s) |
| **Building the table column-by-column (5 edits)** | **~16 s cumulative DAX wait** |
| Same final query repeated ×3 | 3.2 / 4.3 / 3.2 s — **no cache benefit; every re-render pays full price** |

## Step 4 — Root cause (in code)

- **Frontend — `repos/eclipse/src/app/(app_shell)/explorer/view/[[...slug]]/EditVisual.tsx`.**
  The form debounces **only** title + filters (`debouncedFieldPatterns: [/^title/, /^options.filters/]`,
  350 ms). Every other change (field, measure, sort, options) calls `setFormState(values)` immediately,
  and `formState` drives `<Visual visual={formState}/>`, which re-issues the dataView data request.
  The debounce is at the *input-component* level (`useFormDebounced` → `enhanceGetInputProps`), so the
  field/measure controls (which call `setFieldValue` directly) aren't debounced even by regex. No
  React-Query-key stabilization, **no de-dup, no AbortController cancellation**.
- **Backend — `repos/core_api/v1/route_dataset.py`** (`model_query`, provider `data_model`): the
  Power BI `executeQueries` `requests.post(...)` has **no timeout and no retry** → a slow/throttled PBI
  call hangs the editor.

Net: heavy DAX (≈3–4 s) × an editor that over-fires it = the slowness. Worse during the hourly refresh.

## Step 5 — (optional) Server-side request timing without a restart

App Insights' codeless agent does **not** inject into Linux **containers**, and flipping its
connection string just restarts the app for no telemetry. Instead enable **diagnostic settings →
Log Analytics** (no restart):

```bash
# enabled 2026-06-11 as "perf-diag-lori" on both apps → workspace DefaultWorkspace-…-CCAN
az monitor diagnostic-settings create --name perf-diag-lori \
  --resource <ARM-id of aldcprodwbapcore1c01> --workspace <ARM-id of LA workspace> \
  --logs '[{"category":"AppServiceHTTPLogs","enabled":true},{"category":"AppServiceConsoleLogs","enabled":true}]'
# then, after editor traffic:
az monitor log-analytics query -w <customerId> --analytics-query \
  'AppServiceHTTPLogs | where TimeGenerated>ago(1h) | where CsUriStem contains "data" | project TimeGenerated,CsUriStem,ScStatus,TimeTaken | order by TimeTaken desc'
```
> Use PowerShell (not Git Bash) for the `--workspace`/`--resource` full ARM IDs — MSYS rewrites the
> leading `/` and corrupts the ID. Requires the `log-analytics` az extension.
> Caveat: the v2 backend authenticates per-user (session JWT); the static `API_TOKEN` is **rejected
> (401)**, so you cannot replay `dataViews/{id}/data` with it — measure via the SP DAX (Step 3) or these logs.

## Credential-store map (for this app)

| Store | Holds | Note |
|---|---|---|
| **Backend app settings** (`aldcprodwbapcore1c01`) | `ENCRYPTION_KEY` (Fernet, decrypts SP secret), `MASTER_CLIENT_ID/SECRET` (core_api's own OAuth client = the legacy `API_TOKEN`), `COSMOS_KEY`, `JWT_SECRET` | `ENCRYPTION_KEY` also in `vault/infra-credentials.md` + `vault/core-api-local-settings.md` |
| **CosmosDB `capacity.encrypted_options`** | the **Power BI SP secret** (`7a7225f4…`), Fernet-encrypted | decrypt with `ENCRYPTION_KEY` |
| **Wiki vault** (`vault/`) | `ENCRYPTION_KEY`, `AZURE_TENANT_ID e2bae64b…`, "Power BI Prod API Token" (a *Core API* OAuth client, NOT the SP), Snowflake `SERVICE_POWER_BI` | see `infra-credentials.md` §Power BI |
| **Azure Key Vault** `aldc-vault-prod/dev/test` (rg-aldc-launchpad) | launchpad/connector/snowflake creds (`snowflake-prod-admin`, `connector-agent--core-api--*`, `lectric--amazon-spapi--*`) | **no** Eclipse PBI SP or PostHog here |
| **PostHog** | Cloud US (`us.i.posthog.com`); token = build-time GitHub var `POSTHOG_TOKEN` | `instrumentation-client.ts`; collection-status unverified — may be dormant in prod |

> **Gotcha — `service_power_bi`:** this is a **Snowflake** service account (role SYSADMIN) the PBI model
> uses to *refresh from Snowflake* — **not** an AAD user and **not** the PBI service principal. A
> username/password named `service_power_bi` will **not** authenticate against Entra (AADSTS50034).

## Remediation

1. **F1 — frontend (primary).** Debounce the value that drives the live preview query so the UI stays
   responsive but the query fires only once the user pauses. Shadow branch
   **`perf/editor-debounce-query-storm`** (eclipse repo): `useDebouncedValue(formState, 400)` →
   `<Visual visual={debouncedFormState}/>`. Optionally add AbortController cancellation + query-key
   stabilization. Test on the **`stage` slot** first; A/B = count `dataViews/.../data` requests while
   building a table (one-per-edit → one-per-pause). Deploy via slot-swap (see [[eclipse-azure-deployment]]).
2. **F2 — backend (resilience).** Add `timeout=` + bounded retry/backoff to the `executeQueries` POST
   in `core_api/v1/route_dataset.py`.
3. **Quick win.** The hourly **model refresh (4–7 min)** overlaps editing at the top of each hour;
   consider shifting its schedule off peak working hours.
4. **Observability (durable).** Bake the OpenTelemetry Azure Monitor SDK into the `core-api` image to
   capture PBI dependency durations permanently; add a synthetic "editor data request" probe + p95
   alert to the [[observability-platform]].

## See Also

- [[eclipse-incident-response]] — connector-outage runbook (the other Eclipse ops failure class)
- [[entities/repos/eclipse|eclipse (repo)]] — the 2.1 UI; § visual editor
- [[core_api]] — v2 backend; `route_dataset.py` data_model/executeQueries path
- [[dashboard]] — Eclipse dashboard/dataset/capacity document model
- [[GP-259]] / [[GP-256]] — Navira "Sales Model" / Return Rate %; same PBI model
- [[observability-platform]] — where the synthetic probe + alert should live
