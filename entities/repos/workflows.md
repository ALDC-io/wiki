---
tags: [entity, repo, workflows, fusion92, dax-media-app, azure-functions, netsuite, bing-ads, notifications]
aliases: [workflows repo, fusion92 workflows, DAX API backend, F92 workflow app, Fusion workflow function app]
sources:
  - Confluence TECH/1777106945 (Steven Offboarding)
  - repos/workflows/README.md
  - repos/workflows/fusion_92/F92_workflow_app/function_app.py
  - repos/workflows/fusion_92/F92_workflow_app/global_constants.py
  - repos/workflows/fusion_92/F92_workflow_app/host.json
  - repos/workflows/fusion_92/F92_workflow_app/local.settings.template.json
  - repos/workflows/fusion_92/F92_workflow_app/requirements.txt
  - repos/workflows/fusion_92/F92_workflow_app/.funcignore
  - repos/workflows/fusion_92/F92_workflow_app/.gitignore
  - repos/workflows/fusion_92/F92_workflow_app/test_function.ps1
  - repos/workflows/fusion_92/F92_workflow_app/.vscode/tasks.json
  - repos/workflows/fusion_92/F92_workflow_app/.vscode/launch.json
  - repos/workflows/fusion_92/F92_workflow_app/.vscode/settings.json
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/jobs/routing.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/jobs/schema.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/jobs/lib/calculations.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/jobs/lib/export_options.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/jobs/lib/exports.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/jobs/lib/fetch.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/jobs/lib/utils.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/notifications/routing.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/notifications/schema.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/notifications/lib.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/notifications/change_notifications.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/notifications/pacing_notifications.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/sync/routing.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/sync/schema.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/sync/lib.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/lib/core_client.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/lib/error.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/lib/response.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/lib/date.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/users/schema.py
  - repos/workflows/fusion_92/F92_workflow_app/dax_api/users/lib.py
  - repos/workflows/fusion_92/F92_workflow_app/workflows/bing_ads.py
  - repos/workflows/fusion_92/F92_workflow_app/workflows/netsuite.py
  - repos/workflows/fusion_92/F92_workflow_app/workflows/lib.py
  - repos/workflows/fusion_92/F92_workflow_app/test/resources.py
  - repos/workflows/fusion_92/F92_workflow_app/test/test_job_calculations.py
  - repos/workflows/fusion_92/F92_notification_cron_update/update.py
  - repos/workflows/fusion_92/F92_notification_cron_update/requirements.txt
  - repos/workflows/fusion_92/F92_notification_retrofitting_app/migrate.py
  - repos/workflows/fusion_92/F92_notification_retrofitting_app/requirements.txt
created: 2026-04-20
updated: 2026-05-21
---

# workflows (repo)

> **Disambiguation — four adjacent pages share similar names:**
> - **This page** — the `ALDC-io/workflows` repo at `C:\Users\PaulRussell\repos\workflows`. The **DAX API backend** for [[dax-media-app]]. Engineering reference.
> - **[[dax-media-app]]** — the *product* page (Fusion92-facing: "DAX Media App" / "Flight Check App"). Business scope, statuses, phases, UAT history. The `F92_workflow_app` sub-project in this repo is the backend of that product.
> - **[[entities/repos/flight-check|flight-check (repo)]]** — the *Next.js frontend* of the DAX Media App. Every `/api/dax/*` and `/api/netsuite/*` proxy call in flight-check calls an HTTP route defined here. Distinct repo, distinct page.
> - **[[flight-check]]** (`processes/operations/flight-check.md`) — ALDC's operational data-pipeline validation runbook. Completely different thing; same phrase.
> - **[[dax-ai]]** — DAX AI analytics dashboard suite. A separate product; the name `dax_api/` in this repo is the Python package name, not a reference to "DAX AI". The similarity is coincidental — do not conflate.

The `workflows` repo holds client-specific workflow code. Today it contains one client's worth of code under `fusion_92/` — three sub-projects: a deployed Azure Functions app (`F92_workflow_app`), a one-shot notification backfill script (`F92_notification_retrofitting_app`), and a one-shot cron-patch utility (`F92_notification_cron_update`). The repo structure is designed to be multi-client (a future `gep/` folder could sit alongside `fusion_92/`), but only Fusion92 code exists today.

`F92_workflow_app` is the **DAX API backend** — the service [[entities/repos/flight-check|flight-check (repo)]] calls for all flight/job data, notifications, NetSuite PO sync, and Snowflake sync. Where flight-check resolves `DAX_API_URL/jobs/{id}` or `F92_NETSUITE_WORKFLOW_URL/api/f92_netsuite_po_sync`, it is calling HTTP routes in `function_app.py`. Both env vars (`DAX_API_URL` and `F92_NETSUITE_WORKFLOW_URL`) resolve to the **same Azure Functions app**. The [[entities/repos/flight-check|flight-check (repo)]] page § API surface enumerates every proxy call and its upstream; this page documents the upstream side.

> **Note on naming collision.** The sub-package at `F92_workflow_app/workflows/` (Python package with `bing_ads.py` + `netsuite.py`) has the same name as this repo (`workflows`). This is an unfortunate coincidence. In this page, "workflows package" refers to the Python sub-package; "this repo" or "`workflows` repo" refers to `ALDC-io/workflows`.

> **Security flag.** The committed `.env` at `fusion_92/F92_notification_cron_update/.env` contains production Cosmos DB hostname and key (plus commented-out dev and test values). Those values have been extracted to `vault/infra-credentials.md` § Fusion92 — Cosmos DB per wiki rule #2. The wiki page body does not reproduce them. See § Security & Credentials for the full flag.

---

## Architecture

### Repository layout

```
workflows/
├── README.md                                    (1 line: "Repository for client specific code")
└── fusion_92/
    ├── F92_workflow_app/                        # Azure Functions app (production)
    │   ├── function_app.py                      # All Azure function bindings (HTTP + Timer triggers)
    │   ├── global_constants.py                  # FUSION_ACCOUNT_ID, ENVIRONMENT, timezone, app type IDs
    │   ├── host.json                            # Functions host v2, App Insights sampling
    │   ├── local.settings.template.json         # Env-var template (committed, not gitignored)
    │   ├── requirements.txt
    │   ├── test_function.ps1                    # Stale PowerShell smoke-test script (endpoint no longer exists)
    │   ├── .funcignore                          # Excludes .env, test/, local.settings* from deployment
    │   ├── .gitignore
    │   ├── .vscode/                             # Azure Functions VS Code integration (settings, tasks, launch)
    │   ├── dax_api/                             # Newer, typed, "DAX API" package (target pattern)
    │   │   ├── jobs/
    │   │   │   ├── routing.py                   # HTTP handler implementations for job/flight endpoints
    │   │   │   ├── schema.py                    # Pydantic models (FlightDocument, JobDocument, etc.)
    │   │   │   └── lib/
    │   │   │       ├── calculations.py          # Core pacing/budget/fee computation engine (~34 KB)
    │   │   │       ├── exports.py               # Excel export builder (base64 xlsx)
    │   │   │       ├── export_options.py
    │   │   │       ├── fetch.py
    │   │   │       └── utils.py
    │   │   ├── notifications/
    │   │   │   ├── routing.py
    │   │   │   ├── schema.py
    │   │   │   ├── lib.py
    │   │   │   ├── change_notifications.py      # Status-change email logic
    │   │   │   └── pacing_notifications.py      # Pacing email logic
    │   │   ├── sync/
    │   │   │   ├── routing.py
    │   │   │   ├── schema.py
    │   │   │   └── lib.py                       # FlightCheckSnowflakeSyncWorkflow
    │   │   ├── users/
    │   │   │   ├── schema.py
    │   │   │   └── lib.py
    │   │   └── lib/
    │   │       ├── core_client.py               # DaxCoreAPIClient — typed wrapper around core_api HTTP
    │   │       ├── error.py                     # APIError, DocumentNotFound, ServerError
    │   │       ├── response.py                  # api_success(), api_error(), @handle_dax_api_errors
    │   │       ├── date.py                      # Timezone/date helpers (America/Chicago)
    │   │       └── string.py
    │   ├── workflows/                           # Legacy, "Workflow" package (being phased out)
    │   │   ├── bing_ads.py                      # MicrosoftAdsTokenRefreshWorkflow
    │   │   ├── netsuite.py                      # NetSuiteAPIClient + F92NetsuitePOWorkflow
    │   │   └── lib.py                           # LegacyCoreAPIClient (DEPRECATED), WorkflowError
    │   └── test/                               # pytest (4 test classes, 556 lines)
    │       ├── resources.py                     # Test fixtures
    │       └── test_job_calculations.py
    ├── F92_notification_retrofitting_app/       # One-shot backfill (run once per env during rollout)
    │   ├── migrate.py
    │   ├── requirements.txt
    │   └── .gitignore
    └── F92_notification_cron_update/            # One-shot cron patch (dev utility)
        ├── update.py                            # Sets every Fusion notification schedule to "* * * * *"
        ├── requirements.txt
        ├── .env                                 # ⚠ COMMITTED production Cosmos DB credentials
        └── .gitignore
```

---

### Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Runtime | Azure Functions Python v2 programming model | `azureFunctions.projectLanguageModel: 2` in `.vscode/settings.json`; `func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)` in `function_app.py:75` |
| Host | `host.json` version `"2.0"`, extension bundle `[4.*, 5.0.0)` | Application Insights sampling enabled; request-type invocations excluded from sampling |
| Python | 3.x (not version-pinned) | No `pyproject.toml`; VS Code scaffold targets `.venv` |
| Data validation | Pydantic (with `[email]` extra) | Used throughout `dax_api/`; legacy `workflows/` path is untyped dicts |
| HTTP client | `requests` | No async client |
| NetSuite auth | `pyjwt[crypto]` | ES256 JWT client assertion via PEM private key env var |
| Microsoft Ads | `bingads` SDK | `OAuthWebAuthCodeGrant` refresh-token flow |
| Cosmos DB | `azure-cosmos` (one-shot scripts only) | `F92_workflow_app` goes through [[core_api]], not Cosmos directly |
| Spreadsheet export | `pandas`, `pandas-stubs`, `xlsxwriter` | Excel exports emitted as base64-encoded strings in the response body |
| Email | via [[core_api]] `application/email` endpoint | No direct Mailjet SDK — emails round-trip through core_api's queue. See [[core_api]] § Notification Module |
| Timezone | `pytz`, `zoneinfo.ZoneInfo` | `America/Chicago` (`FUSION_TZINFO`); DST-aware but switched by hand (see § Pitfalls) |
| Testing | `pytest` + `pytest-mock` | Local only — no CI |
| Env loading | `python-dotenv` with `override=True` | Every module top-level loads dotenv; can cause env-var mix-up between shells (see § Pitfalls) |
| Formatter | `black` (VS Code) | `.vscode/settings.json:9-12` |

---

### Two parallel package namespaces

The single most important architectural fact in this repo: two Python packages implement the same conceptual surface with different quality levels, and they coexist by design.

**`dax_api/` — target pattern (new work goes here)**

Contract-first. Pydantic-typed request/response models. Route handlers call `DaxCoreAPIClient` (`dax_api/lib/core_client.py:18`), which returns validated models and raises structured `APIError` / `DocumentNotFound` / `ServerError`. Responses flow through `dax_api.lib.response.api_success` / `api_error` wrapped by the `@handle_dax_api_errors` decorator. Error envelope: `{error, error_description, error_context}` with an HTTP status matching the exception's `http_code`.

**`workflows/` — legacy pattern (migration pending)**

Untyped dicts. `LegacyCoreAPIClient` (`workflows/lib.py:35`, explicitly marked DEPRECATED in the docstring). `WorkflowError` exception with hand-rolled `success_response` / `workflow_error_response` / `exception_response` wrappers that emit the older envelope shape: `{"response": {"code": ..., "message": ..., "data": ...}}`. The HTTP status code is mirrored inside the body envelope.

The `function_app.py` module docstring (lines 1–25) states the direction explicitly: new code should use `dax_api/` + `@handle_dax_api_errors`. The three existing legacy entries (`f92_netsuite_po_sync`, `f92_netsuite_publishers`, `f92_refresh_microsoft_ads_token`) will migrate "if it makes sense" (`workflows/lib.py:40`).

**Consequence for callers:** The two envelope shapes are **incompatible**. `flight-check`'s `lib/dax/apiUtils.ts` handles only the DAX API shape. The `/api/netsuite/*` handlers in flight-check handle the legacy shape separately. Any new endpoint must declare which pattern it uses so the client-side proxy is written correctly.

---

### Request flow — two shapes

**HTTP (DAX API shape)**

Azure function receives `func.HttpRequest` → `@handle_dax_api_errors` catches exceptions → handler calls a `dax_api.<area>.routing.*` function → routing function instantiates `DaxCoreAPIClient`, fetches docs, runs calculations/transformations → returns a Pydantic model → `api_success(model)` wraps it in HTTP 200. Example: `dax_get_job` (`function_app.py:393–410`).

**HTTP (Legacy workflow shape)**

Azure function receives `func.HttpRequest` → handler validates method + account_id explicitly → instantiates `NetSuiteAPIClient()` + `LegacyCoreAPIClient()` → passes both to a `Workflow` class instance → calls `workflow.run()` → returns `success_response(msg, data)` / `workflow_error_response(WorkflowError)` / `exception_response`. Example: `f92_netsuite_po_sync` (`function_app.py:201–231`).

**Timer trigger**

Azure invokes on cron → handler wraps a `try/except` for `APIError`/`Exception` → calls the same `route_*` / workflow class as the HTTP counterpart. Per the `function_app.py` docstring: "All timer triggered functions should have a matched API endpoint unless the workflow will never need to be triggered manually" (lines 10–13). Example: `f92_status_change_notifications` (`function_app.py:86–109`) is the timer half of `dax_notifications_send_status_change` (`function_app.py:112–126`).

---

### Key abstractions

**`DaxCoreAPIClient`** (`dax_api/lib/core_client.py:18–289`)

Typed wrapper around the [[core_api]] HTTP API. Reads `core_api_url` + `core_api_token` env vars at class load time; raises `ServerError` if either is missing. Key methods: `post_validated(route, body, return_type) -> T`, `post_validated_list(..., return_type) -> list[T]`, `application_read_validated(id, T) -> T`, `dataset_query_validated(body, T) -> list[T]`. Holds a deprecated `post()` (untyped) used by older callers. Docstring notes a pending switch from `dataset/query` (legacy) to `dataset/request` — not yet in production as of 2026-01 (`core_client.py:257–259`).

**`LegacyCoreAPIClient`** (`workflows/lib.py:35–85`)

DEPRECATED per docstring. Same env-var source (`core_api_url` + `core_api_token`) but untyped — returns raw `payload` dict-or-list, raises `WorkflowError("Cosmos document query failed", …)` on non-200.

**`NetSuiteAPIClient`** (`workflows/netsuite.py:24–211`) — see also § NetSuite Authentication Setup below for the key pair and certificate provisioning guide.

Handles OAuth2 `client_credentials` grant with JWT client assertion (ES256) against `https://{ACCOUNT_ID}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token`. 15-minute JWT expiry (`netsuite.py:89`). Env vars: `NETSUITE_CLIENT_ID`, `NETSUITE_CERTIFICATE_ID`, `NETSUITE_ACCOUNT_ID`, `NETSUITE_PRIVATE_KEY` (PEM). Key methods: `connect()` (exchanges JWT for access token), `call_suiteql(query)` (paginated SuiteQL, 10k-offset cap), `put_purchase_order(po_json, external_id)` (creates/updates PO using external ID, then GETs the Location header to return the saved doc).

**`F92NetsuitePOWorkflow`** (`workflows/netsuite.py:217–564`)

Orchestrates the PO sync. Steps: read flight + parent job from core_api → look up NetSuite vendor (by publisher name), inventory item (by channel → mapped item name), project (by job number), existing PO (if `po_number` present) → build PO body → PUT → write `po_number` and `netsuite_sync="connected"` back to flight. Channel-to-item mapping is hard-coded in `channel_to_inventory_item_name()` (`netsuite.py:528–563`) — **9 channels**: Programmatic (CTV / Digital Audio / Display / OTT / Video / DOOH / Native), Social, Paid Search (SEM / Sponsored Reach / App Store), Direct, Print (OOH), Radio (Terrestrial), TV (Linear). Uses Unicode en dashes (`–`) because NetSuite item names use en dashes, not hyphens. Business rules for the PO sync live on [[dax-media-app]] § NetSuite PO Sync — do not re-author here.

**`MicrosoftAdsTokenRefreshWorkflow`** (`workflows/bing_ads.py:15–229`) — **if Microsoft Ads data stops showing up in the Fusion warehouse, the first thing to check is whether this workflow is running successfully** (per Steven Offboarding TECH/1777106945).

Hard-coded `CLIENT_ID = "98fe3659-b606-4550-9b16-c5e51a792618"` (the ALDC Microsoft Ads app registration — not a secret, but flagged as a tech-debt hard-code). Reads `MICROSOFT_ADS_CLIENT_SECRET`, `account_id`, `MICROSOFT_ADS_CONNECTION_ID`. Flow: fetch `work/connectionlist` → extract `developer_token` + `refresh_token` → call `oauth_client.request_oauth_tokens_by_refresh_token(refresh_token)` → call `work/connectionupdate` with new refresh token. Runs daily at 07:00 UTC (`function_app.py:275`). Cross-link: [[connector-token-refresh]] documents the manual fallback when this workflow fails.

**`MetaAdsTokenRefreshWorkflow`** (`workflows/meta_ads.py`) — Daily refresh of Meta/Facebook long-lived access tokens (~60-day expiry). Reads `app_id`, `appsecret`, `access_token` from CosmosDB connection doc `1df7d48a` via core_api, exchanges via Meta Graph API `fb_exchange_token` grant, writes new token back. Added 2026-05-21 per [[FU92-415]]. Same structural pattern as `MicrosoftAdsTokenRefreshWorkflow`. Env var: `META_ADS_CONNECTION_ID`. Runs daily at 08:00 UTC (`function_app.py:302`). Cross-link: [[connector-token-refresh]] documents the manual fallback.

**`FlightCheckSnowflakeSyncWorkflow`** (`dax_api/sync/lib.py:122+`)

Uploads job / flight / flight-metrics Cosmos docs to Snowflake via [[core_api]]'s `datastore/upload` endpoint (`sync/lib.py:332–362`). Three hard-coded `DataStoreDocument` instances with UUIDs that must exist in the per-environment data stores: `JOB` (`61e68798-20f5-4a38-b7e1-ffcb00e5d767`), `FLIGHT` (`54a3d07c-c8cd-40bc-8b75-822dbf1c007d`), `FLIGHT_METRICS` (`20ae845b-334b-4dd4-ade7-a28dc87142be`). Upload batch size `MAX_UPLOAD_ROWS = 10_000`. Excludes heavy fields before upload: `EXCLUDED_JOB_FIELDS = ["audit_trail", "calculations"]`, `EXCLUDED_FLIGHT_FIELDS = ["audit_trail", "rejection_notes", "metrics", "changed_fields", "calculations"]` (`sync/lib.py:78–85`). `only_recent` flag limits the pull to the last `RECENT_DAYS_TO_PULL = 30` days.

**Flight/Job calculations** (`dax_api/jobs/lib/calculations.py`, ~34 KB)

The computation engine behind the "DAX API" name. Applies pacing, budget, and platform-fee math to daily Snowflake metrics + Cosmos flight docs. Test coverage in `test/test_job_calculations.py` (4 test classes, 556 lines) is the only substantive test surface in the repo.

---

### `global_constants.py` as environment selector

`ENVIRONMENT` is resolved from env var (default `QA`). `FUSION_ACCOUNT_ID` is env-overridable (default `0fc00e34` — the Fusion prod/test account ID). `ECLIPSE_BASE_URL` is env-overridable (default `https://fusion92.eclipse.aldc-ca-w1.com`). `APPLICATION_FLIGHT_ID = "9b9a62ab-6021-4147-85f9-74f9ebe9767a"` and `APPLICATION_JOB_ID = "127edb5c-7f9a-4dfa-a679-a6689cd2a70e"` are hard-coded Cosmos application document IDs — same across all environments. `FUSION_TIMEZONE_STRING = "America/Chicago"`. `LAST_SMARTSHEET_YEAR = 2025` (historical Smartsheet integration, now sunset). `PLATFORM_TECH_PERCENTAGE_PLATFORMS = ["viant", "youtube"]` is maintained in sync with the flight-check frontend — any platform added here must also be added in `flight-check`.

---

### Design decisions worth calling out

- **Azure Functions v2 programming model.** Single-file function declarations via decorators on a `func.FunctionApp` instance. Forces all function bindings into `function_app.py`; the `dax_api/jobs/routing.py` top-of-file docstring explains why route logic moves out into sub-packages (lines 1–17).
- **Auth model: `AuthLevel.FUNCTION` for all HTTP routes** (`function_app.py:75`). Clients pass `x-functions-key`. No bearer-token or OAuth on the HTTP surface. Flight-check holds three separate function keys: `DAX_API_MASTER_TOKEN`, `F92_NETSUITE_PUBLISHERS_TOKEN`, `F92_NETSUITE_SYNC_TOKEN`.
- **Account-ID gating.** NetSuite endpoints explicitly reject any request whose body `account_id != FUSION_ACCOUNT_ID` with 403 (`function_app.py:213–221`, `243–250`). Belt-and-suspenders on top of the function key.
- **Deployment-slot cron safety.** Every timer function has a docstring telling the deployer to disable the function in the staging slot via `AzureWebJobs.<func_name>.Disabled=true` — marked as slot-specific (not swapped to prod). Missing this causes double-sends. Not enforced by code.
- **DST manual switch.** Cron schedules are hand-edited and redeployed twice a year. Both summer and winter schedules are present as sibling decorators, commented in/out. Known tech debt — flagged inline in `function_app.py:85–86`, `129–130`, `155–156`.
- **Multi-client-ready layout.** The repo's `fusion_92/` folder is an explicit client namespace. Other clients would get peer folders. None exist today.

---

## Data Flow

### Inbound — HTTP requests from flight-check (and admins)

All inbound HTTP originates from [[entities/repos/flight-check|flight-check (repo)]]'s server-side `/api/dax/*` and `/api/netsuite/*` proxy routes. Every request carries `x-functions-key`. `DAX_API_URL` and `F92_NETSUITE_WORKFLOW_URL` are separate env vars in flight-check but both resolve to the same Azure Functions app — two keys, one host.

| Method | Path | Namespace | Purpose | Caller env var |
|---|---|---|---|---|
| `GET` | `/api/dax/jobs/{job_id}` | `dax_api/jobs` | Return `JobDocument` (optionally with calculations) | `DAX_API_MASTER_TOKEN` |
| `GET` | `/api/dax/jobs/{job_id}/flights` | `dax_api/jobs` | Return `list[FlightDocument]` for a job | `DAX_API_MASTER_TOKEN` |
| `GET` | `/api/dax/flights/{flight_id}` | `dax_api/jobs` | Return single `FlightDocument` | `DAX_API_MASTER_TOKEN` |
| `POST` | `/api/dax/calculations` | `dax_api/jobs` | Compute `FlightCalculations` from a `FlightDocument` body | `DAX_API_MASTER_TOKEN` |
| `GET` | `/api/dax/jobs/{job_id}/export` | `dax_api/jobs` | Build single-job Excel export (`DaxExport` base64 xlsx) | `DAX_API_MASTER_TOKEN` |
| `POST` | `/api/dax/jobs/export` | `dax_api/jobs` | Build multi-job Excel export | `DAX_API_MASTER_TOKEN` |
| `POST` | `/api/dax/notifications/send/status` | `dax_api/notifications` | Trigger status-change notification batch | `DAX_API_MASTER_TOKEN` |
| `POST` | `/api/dax/notifications/send/pacing` | `dax_api/notifications` | Trigger pacing notification batch | `DAX_API_MASTER_TOKEN` |
| `POST` | `/api/dax/sync/jobs` | `dax_api/sync` | Upload job docs to Snowflake via core_api datastore | `DAX_API_MASTER_TOKEN` |
| `POST` | `/api/dax/sync/flights` | `dax_api/sync` | Upload flight docs to Snowflake via core_api datastore | `DAX_API_MASTER_TOKEN` |
| `GET` | `/api/f92_netsuite_publishers` | `workflows/netsuite` | Return NetSuite vendor list | `F92_NETSUITE_PUBLISHERS_TOKEN` |
| `POST` | `/api/f92_netsuite_po_sync` | `workflows/netsuite` | Create/update NetSuite PO from a flight | `F92_NETSUITE_SYNC_TOKEN` |

Every DAX API handler calls back to [[core_api]] (over HTTP) for Cosmos documents, and sometimes to `dataset/query` for Snowflake dataset reads. NetSuite handlers call core_api for Cosmos data plus NetSuite REST/SuiteQL for vendor, item, project, and PO lookups.

---

### Outbound — scheduled timer functions

Six timer-triggered functions run on a recurring basis. Cron strings use NCrontab 6-field format (seconds, minutes, hours, day-of-month, month, day-of-week) — the leading `0` field is seconds. Both summer (CDT, UTC-5) and winter (CST, UTC-6) schedules coexist in source as sibling decorators; one is commented out per DST season.

| Function | Summer CRON (UTC) | Winter CRON (UTC) | Local time (America/Chicago) | Purpose |
|---|---|---|---|---|
| `f92_status_change_notifications` | `0 0 15,17,20,23 * * *` | `0 0 14,16,19,22 * * *` | 9am / 11am / 2pm / 5pm | Status-change email batch |
| `f92_out_of_range_pacing_notifications` | `0 0 15 * * 2,4` | `0 0 14 * * 2,4` | 9am Tue + Thu | Pacing out-of-range emails |
| `f92_flight_end_pacing_notifications` | `0 0 15 * * *` | `0 0 14 * * *` | 9am daily | Flight-end pacing emails to creators |
| `f92_refresh_microsoft_ads_token` | `0 0 7 * * *` | `0 0 7 * * *` | 7am UTC (midnight PST) | Microsoft Ads OAuth token refresh |
| `f92_refresh_meta_ads_token` | `0 0 8 * * *` | `0 0 8 * * *` | 8am UTC (1am PST) | Meta/Facebook long-lived token refresh ([[FU92-415]]) |
| `f92_flight_check_job_sync` | `0 20,50 10-23 * * *` | `0 20,50 10-23 * * *` | HH:20 + HH:50, 10:20–23:50 UTC | Upload job docs to Snowflake |
| `f92_flight_check_flight_sync` | `0 20,50 10-23 * * *` | `0 20,50 10-23 * * *` | HH:20 + HH:50, 10:20–23:50 UTC | Upload flight docs to Snowflake |

Note: the `f92_refresh_microsoft_ads_token` and `f92_refresh_meta_ads_token` schedules do not toggle with DST because token refresh is not time-sensitive to the Fusion business day. The sync functions run twice an hour from ~3:20am–4:50pm PST (covering the US business day). The notification functions follow the Fusion-requested send times.

---

### Core-API-mediated Snowflake upload

No direct Snowflake SDK in this repo. All Snowflake writes go through [[core_api]]'s `datastore/upload` endpoint — a JSON records array with `account_id`, `store_id`, `records`. `datastore/get` is used as an existence check. This is the same `DataStore` abstraction documented in [[core-api-data-model]] and [[cosmosdb-schema]]. Maximum batch size: 10k rows per upload (`sync/lib.py:69`).

Three data stores — UUIDs are hard-coded and must exist in each target environment:

| Store | UUID | Primary Key | Merge mode |
|---|---|---|---|
| JOB | `61e68798-20f5-4a38-b7e1-ffcb00e5d767` | `["ID", "ACCOUNT_ID"]` | add |
| FLIGHT | `54a3d07c-c8cd-40bc-8b75-822dbf1c007d` | `["ID", "APP_ID", "ACCOUNT_ID"]` | add |
| FLIGHT_METRICS | `20ae845b-334b-4dd4-ade7-a28dc87142be` | `["FLIGHT_ID", "DATE"]` | add |

This sync is a leaf of the platform-wide data pipeline — see [[data-pipeline-flow]] for context.

---

### NetSuite Authentication Setup

Source: Confluence TECH/1777106945 (Steven Offboarding — Dax API section).

NetSuite uses RSA key pairs for M2M authentication. Three setup steps:

**1. Create an App Integration** in NetSuite (`Setup > Integration > Manage Integrations > New`):
- Save the `CLIENT_ID` and `CLIENT_SECRET` to Dashlane immediately — they are hidden after leaving the page
- Check **Access Rest API Services**
- Check **Client Credentials (Machine to Machine) Grant**
- For the current auth flow, only `CLIENT_ID` is needed (but save both)

**2. Generate a key pair:**
```bash
openssl req -new -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes -days 728 -out public.pem -keyout private.pem
```
Copy both keys to Dashlane.

**3. Create a certificate** in NetSuite (`Setup > Integration > OAuth 2.0 Client Credentials (M2M) Setup`):
- Assign the ALDC user with the appropriate role (currently Admin; ideally a lower role if Fusion can create one)
- Select the app integration from step 1
- Upload the `public.pem` from step 2
- Copy the generated **Certificate ID** and store in Dashlane — needed for JWT token generation

**NetSuite access:** Use the `Fusion NetSuite Credentials` entry in Dashlane (username + password + authenticator). Choose sandbox or production role after login.

**Sandbox vs. Production:** The Dax API uses env vars to switch between NetSuite environments. In QA these should point to the Sandbox. Testing new features in production is OK if coordinated with Fusion — POs go through Fusion's 2-person approval process before being used.

**Reference links:** [NetSuite Docs](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_162686838198.html) · [Video Tutorial](https://www.youtube.com/watch?v=Ug2ZtI8wCDg)

---

### NetSuite PO write path

End-to-end: flight-check FE "Sync" button → `POST /api/netsuite/sync/syncpo` (flight-check proxy) → `POST /api/f92_netsuite_po_sync` (this repo) → core_api `application/read` for flight + job → NetSuite auth (ES256 JWT grant) → SuiteQL vendor lookup → SuiteQL inventory item lookup → SuiteQL project lookup → SuiteQL PO existence check (if `po_number` present) → `PUT /purchaseOrder/eid:<flight.id>` with `{replace: "item"}` → `GET <Location>` → core_api `application/update` with `po_number` + `netsuite_sync="connected"`.

Business rules for this sync (field mapping, lock behaviour, sync statuses, troubleshooting) live on [[dax-media-app]] § NetSuite PO Sync.

---

### Notification email path

`route_send_status_change_notifications` → fetch all `NotificationDocument`s from Cosmos via core_api → for each enabled, good-status doc → build HTML table → call [[core_api]]'s `application/email` endpoint (`change_notifications.py:181–202`). The email is base64-encoded and sent from `support@aldc.io`. [[core_api]] handles [[mailjet]] delivery. Errors within the per-document loop are caught, printed, and appended to an `errors` list — they do not abort the batch, but are silently lost if no one checks the Application Insights logs.

---

### One-shot scripts (out-of-band)

**`F92_notification_retrofitting_app/migrate.py`**

Iterates all users in Cosmos, and for each user with the Fusion Flight application, creates two `NotificationDocument`s ("My Notifications" + "Group Notifications") with preconfigured `status_to_report` lists. Run once per environment during the Notifications feature rollout. Talks to Cosmos **directly** via `azure-cosmos` (bypasses core_api). Default `schedule = "0 14,16,19,22 * * *"` (winter UTC for the Fusion send times). Target document IDs are minted as `uuid.uuid4()`.

**`F92_notification_cron_update/update.py`**

Lists every notification in Cosmos, filters for ones with `account_id == os.environ["account_id"]`, sets each `schedule = "* * * * *"`, and upserts. The committed `.env` in this folder currently points at **production** Cosmos (`aldcprodcsdb1c01.documents.azure.com`). This utility was almost certainly written as a dev debugging tool. In its committed state, running it would set **every Fusion production notification to fire once per minute**. See § Tech Debt for the full hazard flag. Credentials extracted to `vault/infra-credentials.md` § Fusion92 — Cosmos DB.

---

## Developer Guide

### Prerequisites

- Python 3.x (3.10+ recommended — Pydantic, bingads, azure-functions all support it; repo does not pin a version).
- Azure Functions Core Tools (`func`) v4 — required by the VS Code `"func: host start"` task (`.vscode/tasks.json`).
- Azure CLI (`az`) — for deployment.
- PowerShell — present for `test_function.ps1`, though that script references a non-existent endpoint (see § Pitfalls).
- Access to core_api dev/test/QA environment + function keys.
- (For NetSuite work) NetSuite sandbox client ID, certificate ID, and RSA private key from Dashlane.
- (For Microsoft Ads work) Microsoft Ads client secret from Dashlane.

---

### Environment variables

Canonical schema: `local.settings.template.json` (committed). Values fill in `local.settings.json` (gitignored).

**Always required:**

| Variable | Example value | Notes |
|---|---|---|
| `AzureWebJobsStorage` | (connection string) | Required by Azure Functions runtime |
| `FUNCTIONS_WORKER_RUNTIME` | `python` | Fixed value |
| `core_api_url` | `https://aldcqafnapcore1c01.azurewebsites.net/v1/` | Must end with `/` — see § Pitfalls |
| `core_api_token` | (function key) | Auth for that core_api environment |
| `account_id` | `f49f9aa3` (QA) / `0fc00e34` (TEST/PROD) | Scopes all Cosmos document access to the Fusion tenant |
| `eclipse_url` | `http://localhost:3000` (local) | Base URL of the portal Eclipse instance |
| `ENVIRONMENT` | `local` / `QA` / `TEST` / `PROD` | Used by `environment_prefix()` and DST toggles |
| `application_type` | `9b9a62ab-6021-4147-85f9-74f9ebe9767a` | Comma-separated Cosmos application document IDs (generally the flight app ID) |

**NetSuite PO sync:**

| Variable | Template default | Notes |
|---|---|---|
| `ALDC_NETSUITE_EMPLOYEE_ID` | `13456` | ALDC employee ID in NetSuite |
| `NETSUITE_PO_CLIENT_LEAD_ID` | `13417` | Client lead ID |
| `NETSUITE_PO_PROJECT_MANAGER_ID` | `2747` | **Note: template uses `NETSUITE_PO_PROJECT_MANAGER_LEAD` but code reads `NETSUITE_PO_PROJECT_MANAGER_ID`** — see § Pitfalls |
| `NETSUITE_ACCOUNT_ID` | `7378083-sb1` (sandbox) | Prod value differs |
| `NETSUITE_CLIENT_ID` | (from Dashlane) | OAuth client ID |
| `NETSUITE_CERTIFICATE_ID` | (from Dashlane) | Certificate ID for JWT |
| `NETSUITE_PRIVATE_KEY` | (PEM body) | Must go in `.env`, not `local.settings.json`; template has `__NETSUITE_PRIVATE_KEY` placeholder |

**Microsoft Ads:**

| Variable | Notes |
|---|---|
| `MICROSOFT_ADS_CLIENT_ID` | Template says "SAME IN ALL ENVS" but `bing_ads.py:31` **ignores this env var** and hard-codes `"98fe3659-b606-4550-9b16-c5e51a792618"` — see § Pitfalls |
| `MICROSOFT_ADS_CLIENT_SECRET` | From Dashlane |
| `MICROSOFT_ADS_CONNECTION_ID` | Cosmos connection document ID for the Microsoft Ads connection |
| `META_ADS_CONNECTION_ID` | Cosmos connection document ID for the Meta/Facebook Ads connection (`1df7d48a-2deb-4477-b9b0-31f654d27152`) |

**Disable-timers-locally pattern:** `local.settings.template.json` sets `AzureWebJobs.<func>.Disabled: true` for every timer function. This prevents `func host start` from firing timers during local development. Always keep this pattern when deriving a local settings file.

---

### Local setup — F92_workflow_app

1. `cd workflows/fusion_92/F92_workflow_app`.
2. `python -m venv .venv && source .venv/bin/activate` (Windows Git Bash: `.venv/Scripts/activate`).
3. `pip install -r requirements.txt` (or let VS Code's `"pip install (functions)"` task do it).
4. Copy `local.settings.template.json` → `local.settings.json`; fill in all values per § Environment variables.
5. For NetSuite work: create a `.env` file in the same folder containing `NETSUITE_PRIVATE_KEY=<PEM body>`. Loaded by `dotenv.load_dotenv(override=True)` at every module import.
6. `func start` (or F5 in VS Code — launches `"func: host start"` task and attaches debugger on `localhost:9091` per `.vscode/launch.json`).
7. All routes are available at `http://localhost:7071/api/...`.

---

### Local setup — one-shot scripts

**`F92_notification_retrofitting_app/`**

```
pip install -r requirements.txt
# Create .env with: cosmos_hostname, cosmos_key, cosmos_database, application_id, api_url, api_key
python migrate.py
```

Do not run against production without coordination — creates two notification docs per Fusion user.

**`F92_notification_cron_update/`**

> **Warning.** The committed `.env` points at production Cosmos (`aldcprodcsdb1c01.documents.azure.com`). Do not run `python update.py` with the committed env — doing so will set every Fusion production notification to `* * * * *`. Scrub the `.env` (replace with dev/local values) before running.

---

### Running tests

```
cd fusion_92/F92_workflow_app && pytest
```

Runs `test/test_job_calculations.py` (4 classes, 556 lines). No pytest config file — discovery by default `test_*.py` convention. No CI. Test failures block nothing automatically.

Test fixtures live in `test/resources.py`. `test_function.ps1` is a stale PowerShell smoke test pointing at `/api/f92_notification` — that endpoint does not exist. Disregard it.

---

### Debugging

- **VS Code debugpy** — configured. F5 → "Attach to Python Functions" on `localhost:9091`.
- **Application Insights** — enabled via `host.json`. Deployed function-app resources have Application Insights linked; query via Azure Portal.
- **Request correlation** — none beyond Azure Functions' default `InvocationId` (surfaces in AI traces).
- **Local console logs** — `logging.info/error` (stdlib). No structured logging.
- **Debugging timer functions locally** — set the target function's `Disabled` setting to `false` in `local.settings.json`, then invoke the matched HTTP endpoint instead of waiting for the timer. For example, to test `f92_status_change_notifications`, POST to `http://localhost:7071/api/dax/notifications/send/status`.

---

### Common pitfalls

- **DST cron toggle is manual.** Cron strings in `function_app.py` must be edited twice a year and redeployed. Both summer and winter decorators coexist in the file; one is commented out per season.
- **Timer slot-disable is easily missed.** In Azure, every timer function must be disabled in the staging slot (`AzureWebJobs.<func>.Disabled=true` as a **slot-specific** app setting — tick "Deployment Slot" when creating). Missing this causes double-sends when staging is warm.
- **`core_api_url` must end with `/`.** Every caller concatenates `f"{CORE_API_URL}{route}"`. Missing the trailing slash produces broken paths like `/v1application/read`.
- **`override=True` in dotenv.** Every module does `dotenv.load_dotenv(override=True)` at import. Leftover system env vars from a prior shell session can mix up environments; running `python update.py` in a shell with stale env vars from a previous `func host start` may target the wrong Cosmos instance.
- **`NETSUITE_PO_PROJECT_MANAGER_ID` naming mismatch.** `local.settings.template.json` uses `NETSUITE_PO_PROJECT_MANAGER_LEAD` (suffix `LEAD`) but `workflows/netsuite.py:232` reads `NETSUITE_PO_PROJECT_MANAGER_ID` (suffix `ID`). In production the env var must be set as `NETSUITE_PO_PROJECT_MANAGER_ID`.
- **Microsoft Ads `CLIENT_ID` is hard-coded.** `bing_ads.py:31` hard-codes `CLIENT_ID = "98fe3659-b606-4550-9b16-c5e51a792618"`. The env var `MICROSOFT_ADS_CLIENT_ID` in `local.settings.template.json` is never read by the code.
- **`test_function.ps1` references a non-existent endpoint** (`/api/f92_notification`). The script is from an older iteration. Disregard or delete.
- **Committed `.env` in `F92_notification_cron_update/`.** Production Cosmos credentials are in the git history. See § Security & Credentials.
- **No `pyproject.toml`, unpinned deps.** `requirements.txt` is unpinned; version drift between environments is possible. Consider `pip freeze > requirements.lock` locally to reproduce a known-good state.
- **Email-send errors are silently swallowed.** The per-document `try/except` in `route_send_status_change_notifications` (`notifications/routing.py:85–93`) prints errors and appends to `errors` list but does not abort the batch and does not re-raise. Always check Application Insights when diagnosing missing notification emails.

---

## Deployment

### Infra at a glance

- **Deploy target:** Azure Functions (one function app per environment — QA, TEST, PROD inferred from `local.settings.template.json` comments and naming pattern).
- **Runtime:** Python v2 programming model, extension bundle `[4.*, 5.0.0)`.
- **Auth:** `AuthLevel.FUNCTION` — all HTTP routes require `x-functions-key`.
- **Storage:** one storage account per function app (`AzureWebJobsStorage`). Storage Queue is not used directly — emails route through core_api's queue.
- See [[azure-environments]] and [[deployment-groups]] for the canonical environment list; naming follows [[aldc-naming-convention]] (expect `aldc<env>fnap<dax>1c01` or similar).

---

### No CI/CD pipeline

There is no `.github/` folder anywhere in this repo — not at the repo root, not in `fusion_92/`, not in any sub-project. No Azure DevOps pipeline, no Makefile, no deploy script.

Deployment is **manual**, almost certainly via the VS Code Azure Functions extension's "Deploy to Function App" right-click action. `.vscode/settings.json` has `azureFunctions.deploySubpath: "."` and `scmDoBuildDuringDeployment: true` confirming this. Alternatively, `func azure functionapp publish <app-name>` from inside `F92_workflow_app/`.

This makes this repo an outlier in the ALDC Azure-deployed portfolio — contrast with [[eclipse-azure-deployment]] (slot-swap CI/CD) and the GitHub Actions pipeline in [[entities/repos/flight-check|flight-check (repo)]]. There is no PR gate, no test-must-pass check, and no reproducible build step. Flagged in § Tech Debt.

---

### Deployment steps (manual)

1. Ensure `local.settings.json` is scrubbed locally before deploying (don't leak local secrets into the SCM build).
2. Right-click `F92_workflow_app/` in VS Code Azure Functions extension → "Deploy to Function App…" → select the target environment.
3. After deploy, in Azure Portal → Function App → Configuration, set all env vars from § Environment variables.
4. For the **staging slot**: add the following app settings and mark each as **"Deployment Slot"** scoped (checkbox in Azure Portal) so a slot-swap does not carry them into production:
   - `AzureWebJobs.f92_refresh_microsoft_ads_token.Disabled = true`
   - `AzureWebJobs.f92_refresh_meta_ads_token.Disabled = true`
   - `AzureWebJobs.f92_flight_check_flight_sync.Disabled = true`
   - `AzureWebJobs.f92_flight_check_job_sync.Disabled = true`
   - `AzureWebJobs.f92_out_of_range_pacing_notifications.Disabled = true`
   - `AzureWebJobs.f92_flight_end_pacing_notifications.Disabled = true`
   - `AzureWebJobs.f92_status_change_notifications.Disabled = true`
5. Twice a year (spring-forward / fall-back): edit `function_app.py` to swap the commented-in cron strings between summer/winter schedules, then redeploy. No automation.

---

### Rollback

Manual — re-deploy the previous commit. No staging-slot safety net (no pipeline to swap). For one-shot scripts (`F92_notification_cron_update`, `F92_notification_retrofitting_app`) there is no rollback — they are idempotent by design (upsert / re-entry guard), but a bad run against production leaves state requiring manual cleanup.

---

### Secrets management

- Function keys (`x-functions-key`, Host key) — managed in Azure Portal → Function App → App keys.
- NetSuite and Microsoft Ads keys — stored in Dashlane + Azure App Configuration.
- Cosmos credentials for the one-shot scripts — see `vault/infra-credentials.md` § Fusion92 — Cosmos DB.

---

## API Reference

### Endpoint table

All paths are prefixed `/api/` by Azure Functions. Two response envelope shapes — see below.

| Method | Path | Namespace | Handler | Purpose | Request shape | Response shape |
|---|---|---|---|---|---|---|
| `GET` | `dax/jobs/{job_id}` | `dax_api/jobs` | `dax_get_job` → `get_job` (`routing.py:86–106`) | Return `JobDocument`. Query: `add-calc=true` adds `FlightCalculations` | URL param | `JobDocument` (Pydantic) |
| `GET` | `dax/jobs/{job_id}/flights` | `dax_api/jobs` | `dax_get_all_flights` → `get_all_flights` (`routing.py:109–131`) | Return all flights for a job | URL param | `list[FlightDocument]` |
| `GET` | `dax/flights/{flight_id}` | `dax_api/jobs` | `dax_get_flight` → `get_flight` (`routing.py:54–73`) | Return single flight | URL param | `FlightDocument` |
| `POST` | `dax/calculations` | `dax_api/jobs` | `dax_get_flight_calculations` → `get_flight_calculations` (`routing.py:76–83`) | Compute pacing/budget math | `FlightDocument` body | `FlightCalculations` |
| `GET` | `dax/jobs/{job_id}/export` | `dax_api/jobs` | `dax_get_single_job_flight_export` → `build_single_job_flight_export` (`routing.py:135–160`) | Build single-job Excel | Query: `type=`, `orientation=`, `flight_ids=` | `DaxExport` (base64 xlsx) |
| `POST` | `dax/jobs/export` | `dax_api/jobs` | `dax_get_all_job_flight_export` → `build_all_job_flight_export` (`routing.py:163–191`) | Build multi-job Excel | `MultiJobExportRequestParams` | `DaxExport` |
| `POST` | `dax/notifications/send/status` | `dax_api/notifications` | `dax_notifications_send_status_change` → `route_send_status_change_notifications` | Trigger status-change email batch | `StatusChangeNotificationRequestParams` | `LegacyChangeNotificationResponse` |
| `POST` | `dax/notifications/send/pacing` | `dax_api/notifications` | `dax_notifications_send_pacing` → `route_send_pacing_notifications` | Trigger pacing email batch | `PacingNotificationRequestParams` | `NotificationResponse` |
| `POST` | `dax/sync/jobs` | `dax_api/sync` | `dax_sync_jobs` → `sync_flight_check_jobs` (`sync/routing.py:11–14`) | Upload job docs to Snowflake | `{only_recent: bool}` | success/error |
| `POST` | `dax/sync/flights` | `dax_api/sync` | `dax_sync_flights` → `sync_flight_check_flights` (`sync/routing.py:5–8`) | Upload flight docs to Snowflake | `{only_recent: bool}` | success/error |
| `GET` | `f92_netsuite_publishers` | `workflows/netsuite` | `f92_netsuite_publishers` | Return NetSuite vendor list | Query: `account_id=` | `[{id, name}]` (legacy envelope) |
| `POST` | `f92_netsuite_po_sync` | `workflows/netsuite` | `f92_netsuite_po_sync` → `F92NetsuitePOWorkflow.run()` | Create/update NetSuite PO from flight | `{account_id, flight_id}` | legacy envelope with `synced_po` dict |

---

### Response envelopes — two shapes

**DAX API shape** (all `dax_api/*` endpoints):

HTTP 200 + JSON body of the Pydantic model. Errors raise `APIError(kind, message, context, http_code)`, caught by `@handle_dax_api_errors`, returning `{error, error_description, error_context}` with the correct HTTP status code.

**Legacy workflow shape** (`f92_netsuite_*` endpoints):

HTTP 200 (even for errors) + JSON envelope: `{"response": {"code": <int>, "message": <str>, "data": <payload>}}`. The HTTP status code is mirrored in the body `code` field. Errors use `workflow_error_response` / `exception_response` with the same shape. `flight-check`'s `/api/netsuite/*` proxy handlers are written to expect this envelope; the `/api/dax/*` proxies use `lib/dax/apiUtils.ts` which expects the DAX API shape.

---

### Timer schedule reference

| Function | Summer CRON | Winter CRON | Purpose |
|---|---|---|---|
| `f92_status_change_notifications` | `0 0 15,17,20,23 * * *` | `0 0 14,16,19,22 * * *` | Status-change notification batch |
| `f92_out_of_range_pacing_notifications` | `0 0 15 * * 2,4` | `0 0 14 * * 2,4` | Pacing out-of-range (Tue + Thu) |
| `f92_flight_end_pacing_notifications` | `0 0 15 * * *` | `0 0 14 * * *` | Flight-end pacing (daily) |
| `f92_refresh_microsoft_ads_token` | `0 0 7 * * *` | `0 0 7 * * *` | Microsoft Ads token refresh |
| `f92_refresh_meta_ads_token` | `0 0 8 * * *` | `0 0 8 * * *` | Meta/Facebook token refresh ([[FU92-415]]) |
| `f92_flight_check_job_sync` | `0 20,50 10-23 * * *` | `0 20,50 10-23 * * *` | Job doc Snowflake upload (2×/hr) |
| `f92_flight_check_flight_sync` | `0 20,50 10-23 * * *` | `0 20,50 10-23 * * *` | Flight doc Snowflake upload (2×/hr) |

NCrontab format: `{seconds} {minutes} {hours} {day-of-month} {month} {day-of-week}`. The leading `0` is seconds. `0 0 15 * * *` = 15:00:00 UTC every day.

---

## Schemas

Pydantic schemas live in `dax_api/`. The `workflows/` legacy package has no schemas — all dict-shaped.

**`dax_api/jobs/schema.py`** (~25 KB) — `FlightDocument`, `JobDocument`, `FlightCalculations`, `JobCalculations`, `MetricsTableRow`, `FlightStatus` (StrEnum), `CalculationSource` (StrEnum: `Direct`, `Dax`, `Smartsheet`, `Grouped`), `SingleJobExportRequestParams`, `MultiJobExportRequestParams`, `DaxExport`. Note `PLATFORM_TECH_PERCENTAGE_PLATFORMS` gate: `dax_tech_percentage` is only applied when `platform` is in the valid list (maintained in `global_constants.py:56`).

**`dax_api/notifications/schema.py`** — `NotificationDocument`, `StatusReportSetting`, `PacingNotificationSetting`, `PacingNotificationType` (StrEnum: `out-of-range`, `flight-end`, `all`), `PacingNotificationRequestParams`, `NotificationResponse`, `StatusChangeNotificationRequestParams`, `LegacyChangeNotificationResponse`.

**`dax_api/sync/schema.py`** — `DataStoreDocument`, `SyncJobDocument`, `SyncFlightDocument`, `FlightMetricsUploadRow`.

**`dax_api/users/schema.py`** — user schema used by notification recipient lookup.

Supporting helpers: `dax_api/lib/date.py` (timezone/date utilities for `America/Chicago`) and `dax_api/lib/string.py` (minor string helpers).

---

## Security & Credentials

### Committed credentials — action required

> **Known hazard — `F92_notification_cron_update/.env`**
>
> This file is committed to the `ALDC-io/workflows` git repository and contains:
> - Production Cosmos DB hostname + key (lines 1–2): `aldcprodcsdb1c01.documents.azure.com`
> - Dev Cosmos DB hostname + key (lines 3–4, commented out): `aldcdevcsdb2c01.documents.azure.com`
> - Test Cosmos DB hostname + key (lines 5–6, commented out): `aldctestcsdb1c01.documents.azure.com`
> - A redundant prod duplicate (lines 7–8, commented out)
>
> All six values (3 hostnames + 3 keys) are in the git history.
>
> **Extracted values**: `vault/infra-credentials.md` § Fusion92 — Cosmos DB. The wiki page body does not contain the actual key values.
>
> **Required actions:**
> 1. Rotate all three Cosmos DB keys (prod, dev, test) in Azure Portal.
> 2. Add `.env` to `F92_notification_cron_update/.gitignore` so future runs do not commit secrets.
> 3. Consider rewriting git history to remove the file (Paul's call — scope and blast radius depends on how widely the keys were distributed before this extraction).
>
> **Destructive utility risk**: `update.py`, pointed at prod by the committed `.env`, would set every Fusion production notification `schedule` to `"* * * * *"` (once per minute). There is no confirmation prompt or dry-run flag. See § Tech Debt.

---

### Auth model

| Surface | Auth mechanism |
|---|---|
| HTTP routes (inbound) | `AuthLevel.FUNCTION` — `x-functions-key` header |
| NetSuite-only endpoints (account gating) | Body `account_id` must equal `FUSION_ACCOUNT_ID`; 403 otherwise |
| core_api (inter-service) | Bearer token (`core_api_token`) in `Authorization` header, per-environment |
| NetSuite (outbound) | OAuth2 `client_credentials` grant with ES256 JWT client assertion; 15-minute JWT expiry |
| Microsoft Ads (outbound) | OAuth2 refresh-token flow via `bingads.authorization.OAuthWebAuthCodeGrant`; refresh token persisted in Cosmos connection document, refreshed daily by `f92_refresh_microsoft_ads_token` |
| Meta/Facebook Ads (outbound) | Long-lived access token (~60-day expiry) re-exchanged daily via `fb_exchange_token` grant by `f92_refresh_meta_ads_token`; token persisted in Cosmos connection document `1df7d48a` |

---

### Trust boundaries

- This app trusts [[core_api]] via a static `core_api_token` per environment.
- [[entities/repos/flight-check|flight-check (repo)]] trusts this app via one of three function keys.
- NetSuite trusts this app via JWT-signed client assertion (ES256 with PEM private key).
- No mutual TLS anywhere.

---

### Known risks

- Committed `.env` with production credentials (see above — rotation required).
- No CI/CD, no test gate → regressions ship without automated detection.
- Microsoft Ads `CLIENT_ID` is hard-coded in source (low-risk; public in the OAuth flow, but bad practice).
- DST-cron deployments have no rollback safety net.

---

## Tech Debt & Known Issues

- **No CI/CD anywhere.** No `.github/` folder in this repo. Manual VS Code deploys, no test gate, no reproducible build. Outlier in the ALDC Azure portfolio.
- **Committed production Cosmos credentials in `F92_notification_cron_update/.env`.** Git history retains all three environment pairs (prod, dev, test). See § Security & Credentials for the action items.
- **`F92_notification_cron_update/update.py` is a destructive utility with no safety guard.** Pointed at production by the committed `.env`, it would set every Fusion production notification cron to `* * * * *`. No dry-run flag, no confirmation prompt.
- **Two parallel API patterns** (`dax_api/` typed + `@handle_dax_api_errors` vs `workflows/` untyped dict-based + `LegacyCoreAPIClient`). Migration is in progress per `function_app.py` docstring, but all three legacy routes (`f92_netsuite_po_sync`, `f92_netsuite_publishers`, `f92_refresh_microsoft_ads_token`) remain in the legacy namespace.
- **DST cron switch is manual.** Twice-yearly deploy required; both schedules coexist in source as commented-in/commented-out decorator pairs.
- **`NETSUITE_PO_PROJECT_MANAGER_LEAD` vs `NETSUITE_PO_PROJECT_MANAGER_ID` naming mismatch** between `local.settings.template.json` and `workflows/netsuite.py:232`. In production the env var must use the suffix `ID`.
- **Microsoft Ads `CLIENT_ID` hard-coded** in `bing_ads.py:31` despite the `local.settings.template.json` placeholder suggesting it is an env var.
- **`test_function.ps1` references a non-existent endpoint** (`/api/f92_notification`). The script is from an older iteration.
- **One-shot scripts bypass core_api** — they talk to Cosmos directly via `azure-cosmos`. Breaks the repo's otherwise-consistent "go through core_api" abstraction.
- **`dataset/query` vs `dataset/request` FIXME** — `DaxCoreAPIClient.dataset_query_validated` uses the legacy route; a comment in `core_client.py:257–259` notes the new `dataset/request` endpoint is not yet in production as of 2026-01.
- **No `pyproject.toml`, unpinned `requirements.txt`** — version drift between environments is possible.
- **Single test file.** `test/test_job_calculations.py` is the only test. No coverage for NetSuite workflows, Microsoft Ads refresh, notifications, or sync.
- **README is one line.** "Repository for client specific code." This wiki page is the effective README.
- **Timer-slot-swap discipline is documented only in `function_app.py` docstrings.** Easy to miss on first deploy. Missed slot disabling causes double-sends.
- **`ECLIPSE_BASE_URL` defaults to a deployed production URL** (`https://fusion92.eclipse.aldc-ca-w1.com`) in `global_constants.py`. Not sensitive, but a developer who forgets to set this env var locally may inadvertently hit production.

---

## See Also

- [[dax-media-app]] — the product this repo's `F92_workflow_app` is the backend of. Business scope, statuses, phases, NetSuite PO sync rules, UAT history. Heaviest cross-link.
- [[entities/repos/flight-check|flight-check (repo)]] — the Next.js frontend that calls every HTTP route in this repo. See its § API surface for the caller side of every endpoint. *(Not [[flight-check]], the ops runbook.)*
- [[connector-token-refresh]] — documents the manual fallback when `f92_refresh_microsoft_ads_token` or `f92_refresh_meta_ads_token` fails. Full audit matrix (2026-05-21).
- [[bing-ads]] — Bing Ads / Microsoft Advertising connector page.
- [[facebook-ads]] — Meta/Facebook Ads connector page. Operational status + token refresh details.
- [[FU92-415]] — Meta token refresh automation ticket.
- [[FU92-416]] — Trade Desk + Viant auth investigation ticket.
- [[fusion92]] — the client. `FUSION_ACCOUNT_ID = "0fc00e34"` and the `America/Chicago` timezone decisions originate here.
- [[core_api]] — every HTTP handler and workflow in this repo calls core_api via `DaxCoreAPIClient` or `LegacyCoreAPIClient`. Notification emails are queued through core_api's `application/email` endpoint.
- [[core-api-data-model]] — context for the `datastore/upload` and `datastore/get` endpoints used by the Snowflake sync workflow.
- [[cosmosdb-schema]] — context for the `notification`, `user`, `work_connection`, and `application` Cosmos containers that the main app and one-shot scripts touch.
- [[CosmosDB]] — Azure Cosmos DB tool page.
- [[data-pipeline-flow]] — `FlightCheckSnowflakeSyncWorkflow` is a leaf of the platform-wide pipeline.
- [[fusion92-platform-ids]] — platform account/campaign/order ID mapping; complements the `PLATFORM_TECH_PERCENTAGE_PLATFORMS` gate in `global_constants.py`.
- [[fusion92-data-architecture]] — Fusion92 Snowflake setup and data model.
- [[azure-environments]], [[deployment-groups]], [[aldc-naming-convention]] — Azure environment and naming context.
- [[Azure]] — primary cloud platform.
- [[GitHub Actions]] — note: this repo does not use GitHub Actions. No `.github/` folder exists. Included here as a contrast point with other ALDC repos.
- [[mailjet]] — downstream of core_api's `application/email` (handles actual email delivery).
