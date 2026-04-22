---
tags: [entity, repo, core-api, aldc, eclipse, api, azure-functions]
aliases: [core_api, core-api, core api]
sources: [daily/2026-04-17.md, ~/.claude/CLAUDE.md, CORE/1467940876, CORE/1048248321, CORE/238387201, CORE/7929869, CORE/886603777, CORE/885620774, CORE/909737996, CORE/892796955]
created: 2026-04-17
updated: 2026-04-18
---

# core_api

ALDC's core API service. Lives at `C:\Users\PaulRussell\repos\core_api`. The backend API powering [[Eclipse]] — reads connection/template configs from [[CosmosDB]], handles warehouse-rebuild functions, and previously also held connector data-pull queries before they were migrated to the [[connector]] repo for [[Prefect]].

## Runtime

- **Python 3.11** (hard requirement — pinned by the Azure Functions worker)
- **Azure Functions v4** (`FUNCTIONS_EXTENSION_VERSION=~4`, `FUNCTIONS_WORKER_RUNTIME=python`)
- Deployed to [[Azure]] Function Apps (one per env — see table below)
- Reads all runtime config from env vars, loaded locally from `local.settings.json`

## Environments (function app → resources)

| Env | Function App | Resource Group | Storage (core / queue) | [[CosmosDB]] |
|-----|--------------|----------------|------------------------|--------------|
| **prod** | `aldcprodfnapcore1c01` | `aldcprodrsgp1c` | `aldcprodstaccore1c01` / `aldcprodstacqueue1c01` | `aldcprodcsdb1c01` |
| **qa** | `aldcqafnapcore1c01` | `aldcqarsgp1c` | `aldcqastaccore1c01` / `aldcqastacqueue1c01` | `aldcqacsdb1c01` |
| **test** | (confirm — name not captured yet) | `aldctestrsgp1c` | `aldcteststaccore1c01` / `aldcteststacqueue1c01` | `aldctestcsdb1c01` |

All envs share tenant `e2bae64b-6e5f-4f55-b81c-ada320c7f572`. Full per-env secrets in `vault/core-api-local-settings.md`.

## Role in the pipeline

core_api is the **Eclipse-side** control plane. It is **not directly connected to [[Snowflake]]** in the Prefect world — the data path is:

```
connector (Prefect flow) ──► Azure Storage Account ──► Snowflake query pulls into DWH
            │
            │   (connector = transport layer)
            ▼
         core_api (Eclipse API)
```

So data **transport** is owned by the [[connector]] repo; core_api's job is Eclipse-API surface area and warehouse-rebuild functions — not moving data itself.

> **Open question (2026-04-17):** the exact role split between core_api and connector is still fuzzy. Today's KT note: "for prefect connector/template — connection through PBI — not core_api anymore." That phrasing needs unpacking — specifically what "connection through PBI" means in the Prefect flow context.

## Key modules / endpoints

### `route_warehouse.py` — warehouse rebuild

The most frequently-touched module when debugging bad data. Key function:

- **`warehouse_recreate_current`** — rebuilds the data that feeds the `CURRENT_*` and combined views in [[Snowflake]]
  - Invoke via [[Postman]] (Steven's collection has the request pre-wired)
  - On failure: check [[Snowflake]] **Query History** for failed queries. Use the `ACCOUNTADMIN` role to see the **un-redacted** query text — otherwise parameters are masked

### Other surface areas (from Postman collections)

Based on the request organization in Steven's and Lawrence's collections — see [[postman-collections]] for the full catalog:

- **account/** — `list`, `describe`, `encode`, `invoice`, `clientinfo`, etc.
- **dataset/** — `synchronize`, `describe`, `list`, `request`, `query` (DAX + Snowflake-backed)
- **application/** — `clone`, application-container management
- **notification/** — notifications surface
- **warehouse/** — `warehouse_recreate_current` and related

## Running locally

Full runbook: [[core-api-local-setup]]. TL;DR:

1. Python 3.11 venv
2. Azure Functions Core Tools + Azure VS Code extension
3. `local.settings.json` from `vault/core-api-local-settings.md`
4. `func start` (or F5 in VS Code)
5. Point [[Postman]] at `http://localhost:7071`, use `x-function-key: none-for-local`
6. Use a real Fusion or GEP `account_id` — those are the accounts the collection is pre-wired against

## Debugging workflow

When an endpoint misbehaves:

1. Reproduce in [[Postman]] against local core_api
2. Inspect terminal / VS Code Functions output for exceptions
3. Check [[Snowflake]] Query History (as `ACCOUNTADMIN` for un-redacted text) if the call touches warehouse data
4. Check [[CosmosDB]] `schema` container for stale template documents if the failure is around Eclipse template resolution
5. Follow [[debugging-warehouse-loads]] for the full decision tree

## Migration from core_api → connector

Historically, queries that pulled data from external APIs lived in core_api. 

For the [[Prefect]] migration:

- **Transport/data-pull queries** have been moved out of core_api and into the [[connector]] repo (`connector/accounts/<ACCOUNT>/deployments/`)
- **Core API surface** (Eclipse backend, warehouse rebuild triggers) **stays** in core_api

This matches the broader split: Eclipse (= core_api + web UI) is the control plane; connector is the data plane.

## Old core vs new core

There are **two lineages** of core_api still visible in the Postman collections:

- **New core** — current production. Target with **Steven's Dax and Core Collection**
- **Old core** — legacy surface. Target with **Analytic Labs Control v1 (LAWRENCE)** collection

Most endpoints have converged, but if a bug is reported against an endpoint only present in Lawrence's collection, confirm with the team whether it's hitting old or new core before chasing it in source.

## Deployment

core_api deploys like other ALDC [[Azure]] web apps / function apps: [[GitHub Actions]] builds the container and pushes it to the staging slot, then a manual **swap** in the Azure Portal points production traffic at the new slot. See [[eclipse-azure-deployment]] for the full flow (same pattern as Eclipse) and [[GitHub Actions]] for the workflow-level detail.

## Access

Paul's current state (2026-04-17):

- Eclipse production access granted 2026-04-17 (covers the core_api backend)
- Has Steven's `local.settings.json` (stored in `vault/core-api-local-settings.md`)
- Service principal (from `local.settings.json`) has active access to prod CosmosDB / storage
- Azure owner permissions still pending (Brayden → Sean)

## Datasets API

Source: Confluence CORE/1467940876 (Datasets and API Access, 2025-10-08).

Datasets are a data-access abstraction layer — clients request curated data via REST without knowing the underlying infrastructure.

**Endpoints:**
- Test: `https://api-test.aldc.io/v1/dataset/request`
- Prod: `https://api.aldc.io/v1/dataset/request`

### Request format

```json
{
  "account_id": "<ACCOUNT_ID>",
  "dataset_id": "<DATASET_ID>",
  "preview": false,
  "request": {
    "format": "row",
    "fields": ["'Date (Action)'[Year Name]", "'Account'[Account Name]"],
    "filters": [{"field": "'Date (Action)'[Year Name]", "operator": "equals", "value": 2024}],
    "measures": ["Actual - Spend - Gross"]
  }
}
```

`format` options: `row` (default), `column`, `array`, `parquet` (base64 gzip), `csv` (base64). Set `preview: true` to get row count only.

### Dataset introspection

`POST /v1/dataset/describe?debug=full` — returns `definition.columns` (use `column_locator` in `fields`), `definition.measures` (use `measure_name` in `measures`), and `definition.tables`.

### CosmosDB setup (capacity_provider → capacity → dataset)

Three documents required per account:

1. **capacity_provider** — `type: "tenant"`, `provider: "data_model"`, holds `tenant_id` + `admin_service_client_id` + encrypted `admin_service_client_secret`
2. **capacity** — links `account_id` to `capacity_provider_id`; holds `workspace_id`, `service_client_id`, encrypted `service_client_secret`, and `impersonation` list
3. **dataset** — `type: "data_model"`, links `account_id` to `capacity_id`; holds `dataset_name` + `dataset_id` from Power BI

### App registration requirements

Two Azure app registrations per account:

| App | API Permissions | CosmosDB role |
|---|---|---|
| `Power BI REST API {ACCOUNT_ID}` | `Capacity.READ.ALL`, `Dataset.READ.ALL`, `Semantic Model.READ.ALL`, `Workspace.READ.ALL` | Capacity + capacity provider |
| `Power BI REST API {ACCOUNT_ID} Admin` | None | Admin on capacity provider |

Both apps added to Entra group `Power BI Embed {ACCOUNT_SHORT_CODE}`. That group needs **Service principals can call Fabric public APIs** and **Service principals can access read-only admin APIs** enabled in Power BI Admin portal, and **Contributor** access to the PBI workspace.

See also: [[powerbi-secret-refresh]] for secret rotation runbook.

## Azure Queue Storage Trigger (dispatcher)

Source: Confluence CORE/1048248321 (Azure Queue Storage Trigger, 2022-12-08).

> *Verify deployment approach against current infrastructure — created 2022.*

Task queue messages are consumed by a Python Azure Function (the "dispatcher") using a Queue Storage Trigger. This replaced the legacy task/trigger and runs exclusively for the task daemon.

### Function app naming

`aldc{env}fnapdispatch{dg}{region}{seq}` — e.g., `aldcprodfnapdispatch1c01`.

### function.json binding

```json
{
  "bindings": [{
    "name": "msg",
    "type": "queueTrigger",
    "direction": "in",
    "queueName": "tasks",
    "connection": "{STORAGE_ACCOUNT_NAME}_STORAGE"
  }]
}
```

`connection` must match the custom connection string name in Azure portal settings.

### Required app settings (Azure portal)

| Setting | Value |
|---|---|
| `CLIENT_ID` | Master client ID or service account for the deployment group |
| `CLIENT_SECRET` | Corresponding secret |
| `{STORAGE_ACCOUNT_NAME}_STORAGE` | Queue storage account connection string (same as `AzureWebJobsStorage`) |

### Local setup

Add `{STORAGE_ACCOUNT_NAME}_STORAGE` + `CLIENT_ID` + `CLIENT_SECRET` to `local.settings.json`. Set `LocalHttpPort: 7072` if running alongside core_api (which uses 7071). Update `launch.json` port to `9091`.

## REST API Specification (2021 design)

Source: Confluence CORE/238387201 (2021-02).

> *2021 design spec — endpoint surface has evolved. Use [[postman-collections]] as the current source of truth for live endpoints.*

### URL structure

```
POST https://{targethost}.azurewebsites.net/v1/{function}/{option}
```

**Auth:** `Authorization: Bearer {TOKEN}` where TOKEN = Base64(`sas_id:sas_key`).

**Debug param:** `?debug=full|partial|none`

### Standard response envelope

```json
{
  "response": {
    "code": 200,
    "type": "Success",
    "message": "...",
    "origin": "function/option",
    "payload": {}
  }
}
```

### Endpoint reference (2021)

| Endpoint | Purpose |
|---|---|
| `account/describe` | Account metadata + storage SAS tokens |
| `account/list` | Accounts accessible by SAS ID |
| `session/init` | Create session → returns `session_id` |
| `session/event` | Write event (setup/output/transport/stage/merge) with start/end status |
| `session/complete` | Close session, compute duration |
| `session/describe` | Full session + all events |
| `session/list` | Sessions by account + status filter |
| `session/zombie` | Sessions exceeding timeout threshold |
| `schedule/init` | Initialize schedule entry |
| `schedule/event` | Write schedule event |
| `schedule/complete` | Close schedule, compute duration |
| `schedule/describe` | Full schedule + events |
| `schedule/list` | Schedules by account + status |
| `schedule/zombie` | Schedules exceeding timeout |
| `warehouse/schema` | Most recent schema for a session |
| `warehouse/extract` | Store schema against session_id |
| `warehouse/stage` | Ingest staged Parquet from Azure Storage into Snowflake stage table |
| `warehouse/merge` *(planned)* | Merge session data with master table |
| `fragment/*` *(planned)* | Fragment inventory management (reconciliation, incomplete tracking) |
| `data/table` *(planned)* | Table metadata for a catalog |
| `data/query` *(planned)* | Execute query against catalog |

### Session event flow

`session/init` → events: `setup` → `output` → `transport` → `stage` → `merge` → `session/complete`

Each event phase has `start` + `end` status writes. Zombie detection kills sessions that exceed timeout without a `complete` call.

### Planned migration

OAuth 2.0 token model was planned to replace SAS-credential Bearer tokens. Current state: unknown — check with team.

## Environment Variables

Source: Confluence CORE/886603777 (2022-07).

> *All actual secret values are redacted — see `vault/infra-credentials.md` § External services credentials + § Dev/old-env core_api credentials.*

### Full variable glossary

| Variable | Description | Example / Default |
|---|---|---|
| `COSMOS_DATABASE` | CosmosDB database name | `"core"` |
| `COSMOS_HOSTNAME` | CosmosDB URL | `https://aldc{env}csdb{inst}.documents.azure.com/` |
| `COSMOS_KEY` | CosmosDB auth key | → vault |
| `COSMOS_THROUGHPUT` | Container throughput (RU/s); `-1` = serverless | `-1` |
| `COSMOS_RETENTION` | Analytical Store retention (seconds); `-1` = infinite | `15768000` (6 months) |
| `ENVIRONMENT_LEVEL` | Tier | `dev`, `test`, `prod`, `stage` |
| `ENVIRONMENT_VERSION` | Deployed version | `"2022-03"` |
| `ENVIRONMENT_ADMIN` | Admin controls enabled | `1` / `0` |
| `ENVIRONMENT_LOCATION` | Runtime context | `"VS Code Runtime Local"`, `"Azure"` |
| `ENCRYPTION_KEY` | Two-way secret encryption key (Base64, **32 bytes exactly**) | → vault |
| `MASTER_CLIENT_ID` | Master client with all API privileges | `FFFFFFFF0000` |
| `MASTER_CLIENT_SECRET` | Master client secret | → vault |
| `MASTER_CLIENT_ENABLE` | Master client enabled | `1` / `0` |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription | → vault |
| `AZURE_CLIENT_ID` | Service principal client ID | → vault |
| `AZURE_TENANT_ID` | Azure AD tenant ID | `e2bae64b-6e5f-4f55-b81c-ada320c7f572` |
| `AZURE_CLIENT_SECRET` | Service principal secret | → vault |
| `SYS_STORAGE_NAME` | Storage account name | `aldcdevstac01coresvc` |
| `STORAGE_SAS1` / `STORAGE_SAS2` | SAS tokens (primary / secondary) | → vault |
| `PUSHOVER_TOKEN` | Pushover push token | → vault |
| `TWILIO_SID` / `TWILIO_TOKEN` / `TWILIO_NUMBER` | Twilio SMS credentials | → vault |
| `MAILJET_EMAIL` / `MAILJET_KEY` / `MAILJET_SECRET` | Mailjet email credentials | → vault |

Full `local.settings.json` for each environment: `vault/core-api-local-settings.md`.

## Architecture & Language Stack

Source: Confluence CORE/7929869 (Architecture Overview, 2020-11).

> *2020 design context. Python version upgraded from 3.8 → 3.11; everything else broadly consistent.*

**Main components:** Source Systems → Work Agent → Core API (Azure Function App) → CosmosDB + Storage Account + Snowflake → Power BI / Eclipse (App Service).

**External services:** Twilio (SMS), Pushover (push notifications), Mailjet (email), Fivetran (data integration).

**Language stack:** Python 3.8 original (now 3.11), PL/SQL (Snowflake), frontend TBD. Source control: GitHub.

> **Note (2020):** Python 3.9 was flagged as incompatible with pyarrow. Python 3.13 has the same issue — see [[core-api-local-setup]] § Common failures.

## Notification Module (route_notification.py)

Source: Confluence CORE/885620774 (2021-11).

> *2021 — verify function signatures and queue integration against current codebase.*

The notification system is asynchronous: messages are queued via Azure Queue Storage, then consumed and routed to the appropriate delivery channel.

**Queue functions:**
- `notification_queue_user()` — queues for a single user
- `notification_queue_group()` — queues for a group
- `func_common.send_message_to_queue()` → writes to `"notifications"` queue

`notification_send()` dequeues messages and routes on `method`:

### Pushover

```python
def pushover_notification(user_list, message, origin, title, priority, device=None):
```

- `priority`: `"high"` → 1, `"medium"` → 0, `"low"` → -1
- `user_list`: single key in list **or** comma-separated string (no spaces) for groups
- Posts to `https://api.pushover.net:443/1/messages.json`
- Returns `1` on success, `0` on failure
- Env var: `PUSHOVER_TOKEN` → `vault/infra-credentials.md` § External services

### SMS (Twilio)

```python
def sms_notification(user, message, origin):
```

- Single recipient per call (unlike Pushover's batch support)
- Phone number requires `+1` prefix for US numbers
- Env vars: `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_NUMBER` → vault

## Task Daemon (route_task.py)

Source: Confluence CORE/909737996 (2022-07).

> *2022 — verify against current codebase. The Azure Queue Storage Trigger (§ above) now handles task execution in newer deployments.*

Four-stage pipeline for scheduled task execution:

1. **`/task/create`** — creates task doc in CosmosDB; sets `datetimestamp_next_utc` if created via API
2. **`schedule_integrator`** — computes next execution timestamp from cron schedule (uses `croniter`; adds sub-minute `seconds` field)
3. **`/task/scan`** — finds tasks where `datetimestamp_next_utc ≤ now`; pushes to queue; sets `next_utc = None` to prevent duplicates
4. **`/task/trigger`** — dequeues + executes API call; updates `datetimestamp_last_utc`; calls `schedule_integrator` for next `next_utc`

Task lifecycle: create → scan picks up → trigger executes → reschedule → repeat.

Cron format: standard 5-field (`* * * * *`) plus optional `seconds` int. `* * * * *` + `seconds: 30` = every 30 seconds. See [[cosmosdb-schema]] § Task Collection for document schema.

## Portal Data Export & Power BI Integration

Source: Confluence CORE/892796955 (2021-12).

> *2021 — verify `route_portal.py` endpoint name and request format against current codebase.*

`route_portal.py` → `portal_data` function queries Snowflake views and returns results. Use `format: "row"` for Power BI compatibility.

### Request format

```json
{
  "account_id": "ef53b697",
  "view": "GA_COUNTRY_SOURCE",
  "options": {
    "columns": ["GA_COUNTRY", "PAGEVIEWS", "GA_SOURCE"],
    "filters": [{"field": "PAGEVIEWS", "operator": "equals", "value": 10}]
  },
  "format": "row"
}
```

### Import into Power BI

1. Postman → send request → Save Response → JSON file
2. Power BI Desktop → **Get Data** → **JSON** → select file
3. Power Query Editor: find `response.payload` column → expand (double arrows) → **Expand to New Rows** → expand again, uncheck "Use original column name as prefix"
4. Ctrl+click desired columns → **Remove Other Columns**

Result: clean table with keys as headers, values as rows.

## Emergency contact

- Brayden Marshall — `brayden.w.marshall@gmail.com` (personal — use only in emergencies; should also be on the GitHub contributors list for core_api)

## Development Standards

All code in core_api must follow ALDC standards:

- [[ai-pr-workflow]] — automated PR checks (Semgrep, TruffleHog, Claude Opus review, PyTestArch, quality gate). Live as of 2026-04-10.
- [[adversarial-investigation-skill]] — `/investigate-adversarial` skill for debugging and architecture decisions
- [[ai-development-project-standard]] — mandatory header + ROI tracking for any feature with >50% AI authorship
- [[python-development-standards]] — PEP 8, Google docstrings, VS Code + PyLint conventions (Python 3.11 hard requirement in this repo)
- [[git-branching-strategy]] — ALDC branching model; core_api follows the same `development` → `user-testing` → `main` flow

## Relationship to eclipse_exp

[[eclipse_exp]] is the next-generation successor to core_api + [[Eclipse]]. It runs in parallel via a strangler-fig migration: new clients provision directly on eclipse_exp (FastAPI + PostgreSQL + JWT + RLS), while existing clients served by core_api (Azure Functions + CosmosDB + legacy auth) continue unaffected. During the migration window, core_api remains the production control plane for all legacy tenants. The two systems do not share a database — eclipse_exp uses its own PostgreSQL schema (`eclipse_exp`) while core_api reads from CosmosDB. See [[eclipse_exp]] § Migration from Legacy Eclipse for the cutover mechanics.

## Known API Gaps

The repo actually exposes **two API surfaces side-by-side**: the legacy Azure Functions `v1` (port 7071, `/v1/…`) and a newer FastAPI `v2` (port 8000, `/v2/…`, entrypoint `api/main.py`, started via `python run.py` or `python run_debug.py`). The v2 surface is the active backend for the current `eclipse` repo on disk and is **deployed in production at `https://api.eclipse.analyticlabs.io/v2/`** (CORS allowlist: `https://eclipse.analyticlabs.io` — the paired [[entities/repos/eclipse|eclipse-2.1]] frontend). The rest of this page still primarily documents v1. A full refresh is pending (see [[action-items]]).

### v2 has no PATCH/PUT for `application_metadata` (surfaced 2026-04-21 by [[DV-444]])

`core_api/api/applications/router.py` exposes only `GET /hierarchy/` and `GET /metadata/`. The update handler exists in `core_api/v1/route_application.py` (`update_metadata_item`, ~lines 308–329) and is routed as `application/updatemetadata` by `core_api/api/legacy_router.py`. However `core_api/api/main.py:164` **comments out the legacy router**, so that path is **not reachable** on the running v2 service.

**Workaround used for DV-444**: direct CosmosDB patch via Azure Portal Data Explorer against the `application_metadata` container, partition key `/account_id`. See [[DV-444]] for the exact record and steps.

**Proper fix (open action item)**: add a v2 PATCH endpoint on `/v2/applications/{id}` that validates input, calls an update-metadata equivalent, and handles the camelCase-vs-snake_case translation (v2 schema uses `appName`; the raw CosmosDB document uses `app_name`). Tracked in [[action-items]].

Uncommenting the legacy router to re-enable `application/updatemetadata` was considered and rejected — it would expose every legacy v1 endpoint, not just the one needed.

## See Also

- [[core-api-local-setup]] — step-by-step runbook for running locally
- [[python-development-standards]] — PEP 8 + Google docstring + linter conventions for all ALDC Python
- [[postman-collections]] — collections that drive core_api (Steven's new-core, Lawrence's old-core)
- [[Eclipse]] — the UI / platform core_api backs
- [[connector]] — sibling repo that owns the data-transport layer post-Prefect migration
- [[CosmosDB]] — where core_api reads connection/template configs
- [[Azure]] — hosts core_api as a function app
- [[azure-environments]] — subscription / env map
- [[Postman]] — used to reproduce and debug core_api calls
- [[debugging-warehouse-loads]] — runbook for warehouse-load failures involving core_api
- [[eclipse-azure-deployment]] — deployment process (staging slot + swap)
- [[connector-timeout-outage]] — prior incident touching the core_api / Azure Function boundary
- `vault/core-api-local-settings.md` — actual secrets (gitignored)
