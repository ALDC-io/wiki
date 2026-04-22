---
tags: [entity, tool, postman, collections, core-api, reference]
aliases: [Postman collections, ALDC postman collections]
sources: [daily/2026-04-17.md]
created: 2026-04-17
updated: 2026-04-17
---

# Postman Collections Reference

Catalog of the [[Postman]] collections ALDC engineers use to exercise [[core_api]] and related services. Describes the clean team-shareable workspace design, structure, variables, and when to use each — actual collection JSON and live secrets live in `vault/postman-collections.md`, and the extractor/generator lives at `vault/postman-build.py`.

## Quick chooser

| I want to... | Use |
|--------------|-----|
| Hit an endpoint on the **current** core_api | **core_api (new)** (formerly "Steven's Dax and Core Collection") + `LOCAL` env (for local) or `PROD` env (to hit prod) |
| Hit an endpoint that only exists on **legacy** core | **core_api (legacy)** (formerly "Analytic Labs Control v1 (LAWRENCE)") |
| Poke at Fusion Netsuite sandbox | Fusion Netsuite Sandbox API collection (rarely needed today) |

## Clean workspace design (canonical setup)

Paul re-designed the workspace on 2026-04-17 as part of his first core_api local setup. Goals: minimise per-env toggling, eliminate secret drift, and make the workspace safe to share across the team. Follow this layout when onboarding a new engineer — the `vault/postman-build.py` script generates import files that already match.

**Workspace**: single team workspace, e.g. `ALDC — core_api`. Team workspace lets new engineers inherit the setup; individual current-values stay per-user.

**Collections (2):**

| Collection | Source | When to use |
|---|---|---|
| `core_api (new)` | Steven's export | Daily driver for current core_api |
| `core_api (legacy)` | Lawrence's export | Reference only — don't edit |

**Environments (4):** one per deployment target.

| Env | `aldc_base_url` | Extra vars |
|---|---|---|
| `LOCAL` | `http://localhost:7071` | `x-function-key = none-for-local` |
| `TEST` | (confirm function app name) | real `x-function-key` |
| `QA` | `https://aldcqafnapcore1c01.azurewebsites.net` | real `x-function-key` |
| `PROD` | `https://aldcprodfnapcore1c01.azurewebsites.net` | real `x-function-key`, plus `f92_function_app_url`, `workflow_publisher_key`, `workflow_sync_key`, `dax_api_master_token` |

**Variable placement — the key design decision:**

| Variable | Scope | Why |
|---|---|---|
| `aldc_base_url` | **Environment** | Changes per deployment target |
| `x-function-key` | **Environment** (type: `secret`) | Per-env Azure Functions host key. Irrelevant locally (`host.json` sets `authLevel: anonymous` on the HTTP trigger) but still present for env consistency |
| `client_id`, `client_secret` | **Environment** (type: `secret`) | Source of truth for auth. Currently identical across envs (`FFFFFFFF0000` / `alDc9876!` from `MASTER_CLIENT_*` in `local.settings.json`) but conceptually per-env |
| `bearer_token` | **Collection variable — auto-computed by pre-request script** | Derived from `client_id:client_secret` at send time. **Must not exist as an env var** — see gotcha below |
| `account_id`, `dataset_id`, `capacity_id` | **Collection variable** (override per folder/request when needed) | Describe *what* you're testing, not *which* env |
| `f92_function_app_url`, `workflow_*`, `dax_api_master_token` | **Environment** (PROD only, type: `secret`) | Prod-only surface |

**Pre-request script at collection root (`core_api (new)` → Scripts → Pre-request):**

```javascript
// Auto-compute bearer_token from client_id:client_secret in the active environment.
const id = pm.environment.get('client_id');
const secret = pm.environment.get('client_secret');
if (id && secret) {
  const token = Buffer.from(`${id}:${secret}`).toString('base64');
  pm.collectionVariables.set('bearer_token', token);
}
```

**Authorization header.** The app expects the raw base64 string — *not* `Basic <base64>` or `Bearer <base64>`. Don't use Postman's built-in Basic Auth type — it'll prepend `Basic ` and break auth. Either:
- Let each request keep its own `Authorization: {{bearer_token}}` header (Steven's export already has this on every request), **or**
- Add a single collection-level header `Authorization: {{bearer_token}}` so all requests inherit it.

### Gotcha — `bearer_token` in an env variable silently breaks auth

Postman's variable precedence is **data > local > environment > collection > global**. If `bearer_token` exists as an environment variable (even empty), it wins over the value the pre-request script writes at collection scope → `{{bearer_token}}` resolves to `""` → requests go out with an empty `Authorization` header → the server assigns a garbage fallback `client_id`, marks `client authenticated: false`, and usually crashes inside the handler with a misleading 500 like `JSONDecodeError: Expecting value`.

**Fix:** delete `bearer_token` from every environment. `vault/postman-build.py` omits it from its env outputs by design. Old exports from the daily file (`LOCAL.postman_environment.json` at lines 10266–10365) include it — strip it after import.

### Team-workspace secret hygiene

Master client creds and workflow keys are shared team secrets (every engineer already has them via `vault/`), so syncing them to a team workspace adds no new exposure. If you want a given secret to stay strictly per-user: after import, open the env → click the secret → **clear Initial Value** but keep Current Value. Initial Value syncs to the team workspace, Current Value doesn't.

## Extraction recipe

`vault/postman-build.py` regenerates the 6 import artifacts from the embedded JSON in `daily/2026-04-17.md`. Run it any time you need fresh copies or when the source JSON updates:

```bash
python C:/Users/PaulRussell/repos/wiki/vault/postman-build.py
```

Output (6 files in `C:/Users/PaulRussell/postman-exports/`):

| File | Size | Contents |
|---|---|---|
| `core_api-new.postman_collection.json` | ~47 KB | Steven's collection, renamed, pre-request script wired, collection vars for `bearer_token`/`account_id`/`dataset_id`/`capacity_id` pre-seeded |
| `core_api-legacy.postman_collection.json` | ~265 KB | Lawrence's collection, verbatim, renamed |
| `LOCAL.postman_environment.json` | ~0.7 KB | `aldc_base_url=http://localhost:7071`, `x-function-key=none-for-local`, master creds filled |
| `TEST.postman_environment.json` | ~0.7 KB | `aldc_base_url` blank (fill after confirming function app name), master creds filled |
| `QA.postman_environment.json` | ~0.7 KB | `aldc_base_url` filled, `x-function-key` blank (fill from Azure Portal → App keys), master creds filled |
| `PROD.postman_environment.json` | ~1.4 KB | `aldc_base_url` filled, `x-function-key` blank, workflow keys + `f92_function_app_url` filled, `dax_api_master_token` blank |

Drag all 6 into Postman via **Import** → two collections + four environments appear in the sidebar.

## Collections

### Steven's Dax and Core Collection — new core (daily driver)

Primary collection for current core_api work. Sections:

| Section | Endpoints (base `{{aldc_base_url}}/v1/`) | What it does |
|---------|------------------------------------------|--------------|
| **dataset** | `dataset/synchronize`, `dataset/describe`, `dataset/list`, `dataset/request`, `dataset/query` | DAX dataset operations — synchronize Power BI-backed datasets, describe schema, run DAX or raw Snowflake queries |
| **application** | `application/clone`, `read`, `list`, `audit`, `exportreport`, `readmetadata` | Application container management (cloning a template app for a new account, reading an existing app, exporting reports) |
| **Fusion Workflows** | `get_publisher_names`, `po_sync`, `change_notification` | Fusion92-specific workflow endpoints. Usage unclear — not commonly touched. Steven's note: "not sure what this does, don't think it is used often" |
| **auth** | `token (refresh_token_grant_confidential / public)`, `token (authorization_code_grant)`, `authorize (user_name_and_password)` | OAuth flows. Mostly for grabbing a bearer token for other requests |
| **datastore** | `create`, `list`, `get`, `delete`, `upload`, `status`, `statuslist` | Datastore (file / object) CRUD + upload |
| **old_core_notification** | `execute`, `read` | Legacy-core notification endpoints still callable from new-core collection |
| **dax-api** | `get_flight`, `get_flight_calculations`, `get_job`, `get_job_flights`, `get_single_job_export`, `get_multi_job_export`, `sync_flights`, `sync_jobs`, `send_pacing_notifications`, `send_status_change_notifications` | Fusion DAX reporting API — flights (campaigns), jobs (exports), sync + notifications |

**Default request shape**: `POST {{aldc_base_url}}/v1/<section>/<name>?debug=full` with JSON body, `Authorization: {{bearer_token}}`, `Content-Type: application/json`.

**Variables used**: `aldc_base_url`, `bearer_token`, `account_id`, `dataset_id`, `capacity_id`, `f92_function_app_url`, `workflow_publisher_key`, `workflow_sync_key`, `dax_api_master_token`.

### Analytic Labs Control v1 (LAWRENCE) — old core (legacy)

Broader surface than the new-core collection — reflects everything the legacy core exposed. Sections:

| Section | Example endpoints | Purpose |
|---------|-------------------|---------|
| **account** | `account list`, `account describe`, `account encode`, `account invoice`, `account clientinfo`, `account create`, `account update`, `account enable`, `account disable`, `account new tasks` | Account CRUD + billing/tasks |
| **admin** | `admin environment` | Env-level admin ops |
| **agent** | `agent create`, `describe`, `update`, `list` | Agent entity management |
| **authorization** | `authorization create / updatename / updateaccount / enable / addaccount / removeaccount / addservice / removeservice / disable / newsecret` | Fine-grained auth management |
| **schedule** | `schedule init / event / update / complete / describe / list / details list / list all / zombie / template log` | Scheduler primitives |
| **session** | `session init / complete / update / event / list / list all / describe / zombie` | Session lifecycle |
| **setup** | `setup staging`, `setup capacity`, `setup stac sas` | Initial account/capacity provisioning (including SAS issuance) |
| **work** | `work pick`, `pick old`, `activate`, `complete`, `scan`, `scan old`, `scan template`, `list instance`, `backlog`, `reset`, `queue`, `size`, `size detail`, `describe`, `partition list / method / delete bulk / status`, `template create / delete / update / describe / list / status / clone`, `connection create / delete / update / describe / list / status / clone`, `active partition queue` | The entire Eclipse **work** execution surface — partitions, templates, connections, queue management |
| **warehouse** | `warehouse extract`, `check target`, `schema`, `search`, `merge`, `statements`, `stage`, `reset`, `integrity`, `current`, `script`, `current rebuild`, `capacity partition delete`, `get list`, `stored procedure cleanup` | Warehouse-side ops. **`warehouse current rebuild`** is the legacy-core version of what `warehouse_recreate_current` does in new core |
| **system** | `system configsearch`, `system log`, `system copycontainer`, `system cleanup container (1..6)` | Platform-level maintenance |
| **portal** | `portal log`, `portal appinfo`, `portal data` | Eclipse portal data surface |
| **capacity** | `capacity create`, `create/drop reader account`, `add/remove table to reader account`, `add/remove user reader account`, `account reader maintenance`, `check account reader`, `get reader details`, `capacity list`, `describe`, `create provider`, `list provider`, `capacity usage` | Snowflake reader-account provisioning (capacity = Snowflake share) and capacity CRUD |
| **utility** | `utility encodebearer / encodesecret / decodesecret / decodebearer`, `log_system` | Bearer-token + secret encoding helpers — useful when building new clients |
| **report** | `report create / describe / update / list / status / clone`, `dataset refresh` | Report definitions |
| **task** | `task create`, `task create Copy`, `scan`, `trigger`, `enable`, `disable` | Eclipse task management |
| **notification** | `notification queue group`, `notification send` | Legacy notification surface |
| **service item / service request** | Full CRUD on each | Service-catalog entities |
| **dataset** | `data fetch`, `data fetch power bi`, `data random`, `data columnlist`, `data tablelist`, `create dataset` | Legacy dataset API |
| **stage** | `parquet cleanup` | Parquet stage maintenance |
| **invoice header** | `invoiceheader create / describe / list / approved / update / service item / service item delete` | Invoicing |
| **telemetry** | `kpi`, `getdata` | Telemetry queries |
| **connector** | `connector create` | Connector CRUD (legacy path — new path is the [[connector]] repo) |
| **dashboard** | `get data`, `get list`, `create`, `delete`, `idrename` | Dashboard surface |
| **schedule** (second) | `schema master`, `schema template master`, `get master`, `update master`, `get master list` | Master-schema operations |
| **schema** | `master`, `master list`, `templatemaster`, `master warehouse schema`, `update master`, `update master warehouse` | Schema management |
| **llm** | `talk`, `talk assistant`, `prep`, `uuid`, `message trail`, `message trail assistant`, `create view` | LLM/GPT-backed endpoints (uses `GPT_KEY`) |
| **user** | `user create`, `user list` | User management |

> **Old-core rule of thumb**: if you find an endpoint only in Lawrence's collection, confirm with the team whether the caller in question is actually hitting old core or new core before you start debugging.

## URL prefix — `/v1/...`, not `/api/v1/...`

core_api's `host.json` sets `"routePrefix": ""`, which suppresses Azure Functions' default `/api/` prefix. All request URLs resolve to `{{aldc_base_url}}/v1/<function>/<option>` — Steven's collection already uses this shape. If you ever see a 404, check for an accidental `/api/` segment first.

The HTTP trigger is also `authLevel: anonymous`, so function keys are irrelevant locally. `x-function-key` only matters against deployed function apps (QA/PROD).

## Variable reference (canonical per clean design)

| Variable | Scope | Meaning |
|----------|-------|---------|
| `aldc_base_url` | Env | Base URL of core_api (`http://localhost:7071` for LOCAL) |
| `x-function-key` | Env (secret) | Azure Functions host key. `none-for-local` locally, real key in QA/PROD |
| `client_id` | Env (secret) | Master client id (`FFFFFFFF0000`) — pairs with `client_secret` |
| `client_secret` | Env (secret) | Master client secret (`alDc9876!`) — source for the auto-bearer |
| `bearer_token` | **Collection, auto-computed** | Base64 of `client_id:client_secret`. **Never in env.** Set by the collection pre-request script |
| `account_id` | Collection | Short hex account identifier (e.g. `8425e311`, `5d556742`, `f49f9aa3`) |
| `dataset_id` | Collection | GUID for a DAX dataset |
| `capacity_id` | Collection | Snowflake capacity (share) identifier |
| `f92_function_app_url` | Env (PROD) | Fusion92's function app base URL |
| `workflow_publisher_key` / `workflow_sync_key` | Env (PROD, secret) | Host keys for Fusion workflow endpoints |
| `dax_api_master_token` | Env (PROD, secret) | Master token for DAX API (currently empty in captured export) |

Legacy exports from the vault's daily-notes JSON put `bearer_token`, `account_id`, `dataset_id`, and `capacity_id` on the environment. That works but creates the `bearer_token` precedence trap and forces you to duplicate `account_id` defaults across every env. The clean design puts derived + testing-context vars on the collection, source-of-truth + env-specific vars on the environment.

## Getting the collection files

**Preferred**: run `python vault/postman-build.py` — see "Extraction recipe" above. Generates six import-ready files.

**Raw source** (if you need to audit or re-extract manually): the original JSON exports are embedded in `daily/2026-04-17.md` at these line ranges:

| Artifact | Lines |
|---|---|
| Steven's (source for `core_api (new)`) | 445–1911 |
| Lawrence's (source for `core_api (legacy)`) | 1914–10090 |
| QA env (legacy shape) | 10095–10140 |
| PROD env (legacy shape, has workflow keys + multiple bearer_token values) | 10144–10261 |
| LOCAL env (legacy shape, has multiple account_id values, hardcoded bearer_token) | 10266–10365 |

`vault/postman-collections.md` has the re-import metadata (secrets + notes). `vault/postman-build.py` is the canonical extractor/transformer.

## See Also

- [[Postman]] — tool overview
- [[core_api]] — main service these collections exercise
- [[core-api-local-setup]] — wiring these collections up to local core_api (includes the smoke-test walkthrough)
- [[debugging-warehouse-loads]] — uses `warehouse_recreate_current` (new core) or `warehouse current rebuild` (legacy)
- [[connector]] — sibling repo, not covered by these collections
- `vault/postman-collections.md` — collection JSON + env secrets metadata (gitignored)
- `vault/postman-build.py` — extractor/generator script (gitignored)
