---
tags: [architecture, flight-check, dax-media-app, fusion92, engineering-guide, nextjs, azure-functions, onboarding, security]
aliases: [Flight Check Engineering Guide, DAX Media App Engineering Guide, Flight Check Architecture Guide]
sources:
  - entities/repos/flight-check.md
  - entities/repos/workflows.md
  - entities/projects/dax-media-app.md
  - processes/operations/flight-check.md
created: 2026-04-22
updated: 2026-09-08
---

# Flight-Check Engineering Guide

Consolidated onboarding + architecture reference for the Flight Management web application built for [[fusion92]] (product name **DAX Media App**). Synthesises [[entities/repos/flight-check|flight-check (repo)]] (frontend), [[workflows|workflows (repo)]] (backend), and [[dax-media-app]] (product) into one place for a new engineer.

> **Scope note — three "Flight Check" pages coexist:**
> - **This page** — engineering synthesis across the frontend + backend.
> - [[entities/repos/flight-check|flight-check (repo)]] — engineering reference for the Next.js frontend repo.
> - [[workflows|workflows (repo)]] — engineering reference for the Azure Functions backend (`F92_workflow_app` = DAX API).
> - [[dax-media-app]] — the product page (roles, statuses, phases, NetSuite business rules).
> - [[flight-check]] (`processes/operations/`) — ALDC's operational data-pipeline validation runbook. Different thing, same name.

---

## 1. Executive Summary

| Attribute | Value |
|---|---|
| **Product** | DAX Media App (Flight Management for [[fusion92]]) |
| **Frontend repo** | [[entities/repos/flight-check|flight-check]] — Next.js 16 (Pages Router), TypeScript 5.9 |
| **Backend repo** | [[workflows]] → `fusion_92/F92_workflow_app/` — Azure Functions Python v2 |
| **Host model** | Embedded iframe inside the [[entities/repos/eclipse|Eclipse portal]] (`*.eclipse.aldc.io`) |
| **Prod URL** | `https://dax.fusion92.eclipse.aldc.io` |
| **QA URL** | `https://dax.fusion92.eclipse.aldc-ca-w1.com` (note `.com`, not `.io`) |
| **Owner** | Karen Prete (ALDC) |
| **Client** | [[fusion92]] (account IDs `0fc00e34` prod/test, `f49f9aa3` QA) |
| **Timezone (backend business logic)** | `America/Chicago` |
| **In production since** | November 2024 (replaced Fusion92's legacy Firebase Flight Check app) |

The app lets Fusion92 media planners create **Jobs** (campaigns) and **Flights** (media buys within a job), submit them through an approval workflow (Draft → Submitted → In Review → Approved/Declined), sync approved Direct-Partner flights to **NetSuite POs**, process **DIOS audiences**, and receive pacing + status-change email notifications. It bidirectionally syncs flight/job/metrics data with [[Snowflake]] for BI, all via [[core_api]].

---

## 2. System Architecture

### 2.1 High-level architecture diagram

```mermaid
flowchart LR
  user([Fusion92 User])
  subgraph browser["Browser"]
    portal["Eclipse Portal<br/>(Next.js 14)"]
    iframe["flight-check iframe<br/>(Next.js 16)<br/>dax.fusion92.eclipse.aldc.io"]
    ph["PostHog JS"]
  end

  subgraph aldc_azure["ALDC Azure"]
    core["core_api<br/>(Azure Functions)"]
    cosmos[("Cosmos DB<br/>jobs, flights, users,<br/>notifications, metadata")]
    f92fa["F92_workflow_app<br/>(Azure Functions Python v2)<br/>= DAX API backend"]
    snow[("Snowflake<br/>JOB / FLIGHT /<br/>FLIGHT_METRICS")]
    mj["Mailjet<br/>(via core_api)"]
  end

  dios["DIOS<br/>(custom-fusion-92-audience-api)<br/>FastAPI, on-prem"]
  ns["NetSuite<br/>(SuiteQL + REST)"]
  msads["Microsoft Ads<br/>OAuth"]
  posthog["PostHog SaaS"]

  user --> portal
  portal -- iframes + shares session cookie --> iframe
  iframe -- "postMessage<br/>NAVIGATION_CHANGE" --- portal
  iframe -->|/api/coreAPI| core
  iframe -->|/api/dax/*<br/>x-functions-key| f92fa
  iframe -->|/api/netsuite/*<br/>x-functions-key| f92fa
  iframe -->|/api/dios/*<br/>x-auth-apikey| dios
  ph --> posthog

  f92fa -->|HTTP Bearer| core
  core --> cosmos
  f92fa -->|datastore/upload via core_api| core
  core -->|direct writer| snow
  f92fa -->|JWT ES256| ns
  f92fa -->|OAuth refresh| msads
  f92fa -->|application/email| core
  core --> mj
```

### 2.2 Four backends, one frontend

Every data call in the frontend is a server-side proxy route in `flight-check` that forwards to exactly one of four upstream services — each with a different auth scheme. Internalise this first.

| Upstream | Frontend proxy | Auth header | Env var |
|---|---|---|---|
| [[core_api]] | `POST /api/coreAPI`, `/api/core/*` | `Authorization: <raw token>` (not `Bearer`) | `api_token` |
| **DAX API** (= `F92_workflow_app`) | `/api/dax/*` | `x-functions-key` | `DAX_API_MASTER_TOKEN` |
| **NetSuite Workflow** (= **same** `F92_workflow_app` host, different key) | `/api/netsuite/*` | `x-functions-key` | `F92_NETSUITE_SYNC_TOKEN`, `F92_NETSUITE_PUBLISHERS_TOKEN` |
| **DIOS** ([[custom-fusion-92-audience-api]]) | `/api/dios/*` | `x-auth-apikey` | `DIOS_API_KEY` |

`DAX_API_URL` and `F92_NETSUITE_WORKFLOW_URL` resolve to the **same Azure Functions app** — two separate env vars and two separate function keys for namespace + scope isolation.

### 2.3 Auth model — parent-portal session cookie

The frontend cannot log a user in by itself. `pages/api/auth/[...nextauth].tsx` registers NextAuth with **empty `providers: []`**. The session is issued by the **parent [[entities/repos/eclipse|Eclipse portal]]** and shared via the `__Secure-next-auth.session-token` cookie scoped to `.eclipse.aldc.io`. The flight-check app reads that cookie because `authOptions.cookies.sessionToken.options.domain = .${new URL(NEXTAUTH_URL).hostname}`. `NEXTAUTH_SECRET` **must match the parent portal's secret** for JWT interop.

```mermaid
sequenceDiagram
  participant U as User
  participant E as Eclipse Portal<br/>(parent)
  participant F as flight-check<br/>(iframe)
  participant C as core_api

  U->>E: Login (Django / core_api)
  E-->>U: Set-Cookie __Secure-next-auth.session-token<br/>domain=.eclipse.aldc.io
  U->>E: Navigate to DAX app
  E->>F: iframe src=dax.fusion92.eclipse.aldc.io<br/>(CSP child-src allow-list)
  Note over U,F: Browser attaches shared cookie<br/>on same parent domain
  F->>F: NextAuth decodes JWT via<br/>NEXTAUTH_SECRET (same as parent)
  F->>C: /api/coreAPI (server-side)<br/>Authorization: <api_token>
  C-->>F: data
  F-->>U: rendered page
  F-->>E: postMessage NAVIGATION_CHANGE
  E-->>F: postMessage PARENT_NAVIGATION_CHANGE
```

**JWT role refresh (added [[FU92-396]]):** The `jwt` callback in `authOptions.ts` periodically re-fetches `applications` and `groups` from CosmosDB via the `user/list` v1 core API endpoint (5-minute TTL via `ROLE_REFRESH_MS`). This ensures role changes made in Eclipse Admin → User Management take effect within 5 minutes without requiring the user to log out. Prior to this fix, roles were only set at initial login and cached indefinitely in the JWT.

> ### ⛔ `pages/api/coreAPI.tsx` is an unvalidated pass-through carrying the privileged token
>
> The session model above governs the *page*. It does **not** govern this route. Measured 2026-09-08:
>
> - `apiCall()` sets `Authorization: process.env.api_token` — the server-side core_api credential.
> - `handler()` takes **caller-supplied** `reqObject.url` and `reqObject.message` and forwards them
>   verbatim: `apiCall(reqObject.url, reqObject.message)`.
> - There is **no `getServerSession` check, no route allow-list, and no body schema.**
>
> So a `POST /api/coreAPI {"url": "application/update", "message": {…}}` reaches core_api with our
> privileged token attached, and `application/update` is a permissive merge that will set arbitrary
> fields (see [[core-api-data-model]] § `application/update`). The blast radius is every core_api v1
> route reachable by that token, read **and write**, for anyone who can load the app.
>
> This is a *different and broader* exposure than the unauthenticated export on the `dax.` host
> (ALDC-1064) — that one is read-only. Both live on the same deploy path, so read this before
> scheduling any DAX Media App release. Note also that
> [[reference_core_api_token_rotation_pending|`CORE_API_CLIENT_TOKEN`]] has leaked into tracked
> commits and has not been rotated, which compounds it.
>
> When fixing: add a session check **and** an explicit allow-list of permitted `url` values, rather
> than only the session check — a valid session should not imply permission to call every v1 route.

### 2.4 Iframe ↔ parent URL sync

`pages/_app.tsx:44–204` sets up a bidirectional `postMessage` bridge so the URL bar in Eclipse stays in sync with the DAX app. Mechanism: monkey-patches `history.pushState`/`replaceState`, intercepts `popstate`/`hashchange`, uses a `MutationObserver` + a 2-second interval fallback. Messages:

- **Child → Parent**: `{type: "NAVIGATION_CHANGE", path, timestamp}`
- **Parent → Child**: `{type: "PARENT_NAVIGATION_CHANGE", path, source}` — if `source === "popstate"`, the child uses `replaceState` (not `pushState`) to avoid double-stacking history.

---

## 3. Data Flow Diagrams

### 3.1 Job / Flight CRUD (happy path)

```mermaid
sequenceDiagram
  participant UI as Browser (iframe)
  participant FE as flight-check /api/coreAPI
  participant DAX as DAX API (F92_workflow_app)
  participant Core as core_api
  participant Cos as Cosmos DB

  UI->>FE: POST /api/coreAPI {url: "application/read", message: {id}}
  FE->>Core: POST https://core/v1/application/read<br/>Authorization: <api_token>
  Core->>Cos: read JobDocument / FlightDocument
  Cos-->>Core: doc
  Core-->>FE: JSON (may contain NaN tokens)
  FE->>FE: strip NaN → null (coreAPI.tsx:29–35)
  FE-->>UI: JSON

  Note over UI,DAX: For pacing/actuals (separate channel):
  UI->>FE: GET /api/dax/flights/{id}?add-calc=true
  FE->>DAX: GET /api/dax/flights/{id}<br/>x-functions-key: DAX_API_MASTER_TOKEN
  DAX->>Core: application/read (flight)
  DAX->>Core: dataset/query (Snowflake metrics)
  DAX->>DAX: calculations.py pacing math
  DAX-->>FE: FlightDocument + FlightCalculations
  FE->>FE: lib/dax/flights.ts:<br/>pacing * 100 (proportion→percent)
  FE-->>UI: normalised shape
```

### 3.2 NetSuite PO sync (Direct Partner flights only)

```mermaid
sequenceDiagram
  participant UI as Browser
  participant FE as flight-check<br/>/api/netsuite/sync/syncpo
  participant WF as F92_workflow_app<br/>/api/f92_netsuite_po_sync
  participant Core as core_api
  participant NS as NetSuite

  UI->>FE: POST /api/netsuite/sync/syncpo<br/>{account_id, flight_id}
  FE->>FE: Check F92_NETSUITE_SYNC_ENABLED
  FE->>WF: POST /api/f92_netsuite_po_sync<br/>x-functions-key: F92_NETSUITE_SYNC_TOKEN
  WF->>WF: Assert body.account_id == FUSION_ACCOUNT_ID<br/>(else 403)
  WF->>Core: application/read (flight)
  WF->>Core: application/read (parent job)
  WF->>NS: OAuth2 JWT grant (ES256, 15-min JWT)
  NS-->>WF: access_token
  WF->>NS: SuiteQL vendor lookup (Publisher Name)
  WF->>NS: SuiteQL inventory item (channel → item map)
  WF->>NS: SuiteQL project (job number)
  WF->>NS: SuiteQL PO existence check (if po_number)
  WF->>NS: PUT /purchaseOrder/eid:{flight.id}<br/>{replace: "item"}
  NS-->>WF: 201 Location
  WF->>NS: GET <Location>
  NS-->>WF: saved PO doc
  WF->>Core: application/update flight<br/>{po_number, netsuite_sync: "connected"}
  WF-->>FE: legacy envelope {response: {code, data: {synced_po}}}
  FE-->>UI: success
```

Sync is **one-way** (Flight → NetSuite). External ID = Flight document UUID is the sync anchor, not the PO number. See [[dax-media-app]] § NetSuite PO Sync for the full field-mapping table and business rules.

### 3.3 Scheduled notification emails

```mermaid
sequenceDiagram
  participant Cron as Azure Timer<br/>(9am/11am/2pm/5pm CT)
  participant WF as F92_workflow_app<br/>f92_status_change_notifications
  participant Core as core_api
  participant Cos as Cosmos
  participant MJ as Mailjet

  Cron->>WF: Timer fires (NCrontab UTC;<br/>DST-switched twice yearly)
  WF->>Core: notification/read/list
  Core->>Cos: fetch enabled NotificationDocuments
  loop per notification
    WF->>Core: application/read (flights to include)
    WF->>WF: change_notifications.py<br/>build HTML table
    WF->>Core: application/email<br/>from: support@aldc.io,<br/>body: base64 HTML
    Core->>MJ: send
    Note over WF: Errors swallowed per-doc<br/>(printed, appended to errors list,<br/>batch continues)
  end
```

Timer cron schedules have **both summer (CDT) and winter (CST) decorators in source**; one is commented out per DST season — a manual twice-a-year redeploy is required. Every timer function must also be disabled on the **staging slot** via `AzureWebJobs.<func_name>.Disabled=true` as a slot-specific setting, or a slot-swap causes double-sends.

### 3.4 Snowflake bidirectional sync

```mermaid
sequenceDiagram
  participant Cron as Azure Timer<br/>(HH:20 + HH:50, 10:20–23:50 UTC)
  participant WF as f92_flight_check_{job,flight}_sync
  participant Core as core_api
  participant Cos as Cosmos
  participant DS as core_api DataStore<br/>(datastore/upload)
  participant Snow as Snowflake

  Cron->>WF: Timer fires (2×/hr, covers US business day)
  WF->>Core: application/list (only_recent=true → last 30 days)
  Core->>Cos: fetch jobs / flights
  WF->>WF: Strip heavy fields<br/>(audit_trail, calculations, metrics)
  WF->>DS: POST datastore/upload<br/>{store_id, records, max 10k/batch}
  DS->>Snow: write JOB / FLIGHT / FLIGHT_METRICS tables
  DS-->>WF: ok
```

Three hard-coded DataStore UUIDs must exist in each target environment:
- JOB — `61e68798-20f5-4a38-b7e1-ffcb00e5d767` (PK: `ID, ACCOUNT_ID`)
- FLIGHT — `54a3d07c-c8cd-40bc-8b75-822dbf1c007d` (PK: `ID, APP_ID, ACCOUNT_ID`)
- FLIGHT_METRICS — `20ae845b-334b-4dd4-ade7-a28dc87142be` (PK: `FLIGHT_ID, DATE`)

Merge mode is `add`, batch cap is 10k rows. No direct Snowflake SDK in the backend — all writes go through core_api's `datastore/upload`. This feeds Snowflake → Power BI (the reverse direction of the pacing data flow in Phase 2 / PRJ537). See [[data-pipeline-flow]].

### 3.5 DIOS audience processing

```mermaid
sequenceDiagram
  participant UI as Browser
  participant FE as flight-check /api/dios/*
  participant DIOS as custom-fusion-92-audience-api<br/>(FastAPI, on-prem)

  UI->>FE: GET /api/dios/projects/{name}/audiences
  FE->>DIOS: GET /projects/{name}/audiences<br/>x-auth-apikey: DIOS_API_KEY
  DIOS-->>FE: audiences[]
  FE-->>UI: dropdown options

  UI->>FE: POST /api/dios/audience/process (raw body passthrough)
  FE->>DIOS: POST /audience/process
  DIOS-->>FE: status
  FE-->>UI: status
```

---

## 4. Component Breakdown

### 4.1 Frontend — [[entities/repos/flight-check|flight-check]] repo (Next.js 16, Pages Router)

- **Host model**: `output: "standalone"` Next.js build → Docker (`node:24-alpine` multi-stage) → Azure App Service with a **staging slot**.
- **Auth**: NextAuth 4 with empty providers; inherits session from parent Eclipse portal.
- **State**: React local state only. One React Context — `NetSuiteSyncContext`. No Redux / Zustand / React Query.
- **UI kits (all coexist — legacy migration residue)**: Mantine 7 + NextUI 2 + flowbite-react + headlessui. New code targets Mantine.
- **Date libs (all coexist)**: `@js-joda/core`, `date-fns`, `dayjs`. Consolidation target is js-joda.
- **Analytics**: PostHog; project key hard-coded in `components/PostHogProvider.tsx:8` (public-by-design but shadows an unused env var).
- **Metadata-driven forms**: `metadata/Job.json`, `job_details.json`, `admin.json` declare field order, sections, roles. Interpreted at runtime by `FormSectionsRenderer.tsx` + `FormFieldRenderer.tsx`. **These JSON files carry env-specific `account_id` and `app_url` values and must be manually pasted into the target CosmosDB metadata container after every deploy that touches them.**
- **Key proxy**: `pages/api/coreAPI.tsx` silently rewrites raw `NaN` tokens in core_api responses to `null` before `JSON.parse` (lines 29–35) — band-aid for non-RFC JSON emitted upstream.
- **Mega-files (don't attempt a full refactor in one PR)**: `[...slug].tsx` ~25 k lines, `ApplicationTable.tsx` ~99 k, `AccountForm.tsx` ~106 k, `F92DataTable.tsx` ~40 k.
- **Tests**: one placeholder (`expect(true).toBe(true)`). Effectively zero coverage.
- **CI**: `.github/workflows/PR_checks.yaml` — Node 24 lint + format + `npm audit --omit=dev`. **Triggers on `pull_request.synchronize` only** — the first push to a new PR skips CI (known oversight).
- **CD**: `.github/workflows/deploy_az_webapp.yaml` — manual `workflow_dispatch`, OIDC Azure login, `next build`, deploys `.next/standalone` to the **staging slot**. Manual slot-swap in Azure Portal promotes to prod.

### 4.2 Backend — [[workflows]] → `fusion_92/F92_workflow_app` (Azure Functions Python v2)

- **Single-file bindings**: all HTTP + Timer triggers declared via decorators in `function_app.py` on one `func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)` instance.
- **Two parallel API namespaces** (by design):
  - `dax_api/` — **target pattern**. Pydantic-typed, `DaxCoreAPIClient`, `@handle_dax_api_errors` decorator, envelope `{error, error_description, error_context}` with correct HTTP status.
  - `workflows/` — **legacy pattern** (3 endpoints remain: `f92_netsuite_po_sync`, `f92_netsuite_publishers`, `f92_refresh_microsoft_ads_token`). Untyped dicts, `LegacyCoreAPIClient` (DEPRECATED), `WorkflowError`, envelope `{"response": {"code", "message", "data"}}` with HTTP code mirrored in body.
- **Account-ID gating**: NetSuite endpoints reject any request whose body `account_id != FUSION_ACCOUNT_ID` with 403 (`function_app.py:213–221`, `243–250`) — belt-and-suspenders on top of the function key.
- **No CI/CD anywhere** — no `.github/` folder in the repo. Deploys are right-click "Deploy to Function App" from VS Code Azure Functions extension, or `func azure functionapp publish <app-name>`. Outlier in the ALDC portfolio.
- **Tests**: `test/test_job_calculations.py` — 4 classes, 556 lines. `pytest` locally, no CI runs them.
- **Env loader**: `dotenv.load_dotenv(override=True)` at every module import — **can cause env-var bleed between shell sessions**.

### 4.3 Shared constants in both repos

These are hard-coded in both frontend and backend and must be kept in sync:

| Constant | Value | Where |
|---|---|---|
| `FUSION_ACCOUNT_ID` (prod/test) | `0fc00e34` | FE: `components/nonHTMLcomponents/constants.tsx`, BE: `global_constants.py` |
| `FUSION_ACCOUNT_ID` (QA) | `f49f9aa3` | same |
| `APPLICATION_FLIGHT_ID` | `9b9a62ab-6021-4147-85f9-74f9ebe9767a` | FE + BE (hard-coded Cosmos application doc ID) |
| `APPLICATION_JOB_ID` | `127edb5c-7f9a-4dfa-a679-a6689cd2a70e` | FE + BE |
| `PLATFORM_TECH_PERCENTAGE_PLATFORMS` | `["viant", "youtube"]` | BE: `global_constants.py:56` — **must match the FE list** |
| `LAST_SMARTSHEET_YEAR` | `2025` | FE + BE (Smartsheet is being sunset) |

---

## 5. Integration Context

| System | Role | Direction | Auth | Host | Deeper reading |
|---|---|---|---|---|---|
| Eclipse portal | Parent frame, session issuer | in | Shared NextAuth cookie (`NEXTAUTH_SECRET` must match) | Azure App Service | [[entities/repos/eclipse|eclipse (repo)]] |
| core_api | Primary data plane (Cosmos + DataStore access) | both | Bearer (`api_token` / `core_api_token`) | Azure Functions | [[core_api]], [[cosmosdb-schema]], [[core-api-data-model]] |
| F92_workflow_app (self) | DAX API backend | — | `x-functions-key` | Azure Functions | [[workflows]] |
| NetSuite | PO create/update | out | OAuth2 JWT (ES256, 15-min, PEM private key) | NetSuite SaaS | [[dax-media-app]] § NetSuite PO Sync |
| DIOS | Audience lookup + processing | out | `x-auth-apikey` | **On-prem** Docker (Nginx + Cloudflare DNS, proxying disabled; 60 GB RAM) | [[custom-fusion-92-audience-api]] |
| Microsoft Ads | OAuth refresh | out | OAuth refresh token (daily job at 07:00 UTC) | Microsoft Advertising | [[bing-ads]], [[connector-token-refresh]] |
| Snowflake | BI warehouse (via core_api DataStore) | out | via core_api | Snowflake SaaS | [[data-pipeline-flow]], [[fusion92-data-architecture]] |
| Mailjet | Email delivery (via core_api `application/email`) | out | via core_api | Mailjet SaaS | [[mailjet]] |
| PostHog | Analytics | out | Public project key | PostHog SaaS | — |

### Environment model

| Env | Frontend URL | Backend (F92_workflow_app) | Snowflake | Account ID |
|---|---|---|---|---|
| **Prod** | `dax.fusion92.eclipse.aldc.io` (**`.io`**) | `aldcprod…fnap…` | PROD | `0fc00e34` |
| **QA** | `dax.fusion92.eclipse.aldc-ca-w1.com` (**`.com`**) | `aldcqa…fnap…` | QA | `f49f9aa3` |
| **Test** | n/a (QA covers pre-prod) | `aldctest…fnap…` | TEST | `0fc00e34` |
| **Local** | `http://localhost:3100` (FE) + `http://localhost:7071` (BE) | local `func start` | — | dev pick |

> **Recurring trap**: Prod uses the `.io` TLD but QA uses the `.com` TLD (`eclipse.aldc-ca-w1.com`). Same app, different suffix. Always double-check the URL when debugging cross-environment issues.

See [[azure-environments]] and [[deployment-groups]] for the broader Azure mapping; [[aldc-naming-convention]] for naming.

---

## 6. Local Dev Setup

This section is the new-engineer walkthrough. Allow ~1 hour end-to-end the first time.

> **Correction (2026-04-23):** A prior revision of this section claimed `NEXTAUTH_URL=http://localhost:3100` would block local dev because the cookie domain becomes `.localhost`. That advice was wrong. The working pattern is to set `NEXTAUTH_URL` to the **parent Eclipse portal's URL** (e.g. `http://localhost:3000/`), which gives the cookie domain `.localhost` — browsers accept this across ports on hostname `localhost`, so the session cookie issued by the parent flows to flight-check at `:3100` without any hosts-file aliasing. JWT-minting is unnecessary for normal dev. Confirmed against a working `.env.local`.

### 6.1 What you're standing up

Up to four processes cooperate; only the first two are needed for most UI work:

| # | Process | Repo | Port | Required for basic dev? |
|---|---|---|---|---|
| 1 | **flight-check** (frontend) | `repos/flight-check` | `3100` | ✅ |
| 2 | **eclipse** (parent portal — session issuer) | `repos/eclipse` | `3000` | ✅ |
| 3 | **F92_workflow_app** (DAX API + NetSuite backend) | `repos/workflows/fusion_92/F92_workflow_app` | `7071` | Only when editing pacing / NetSuite / notifications |
| 4 | **core_api** (control plane) | `repos/core_api` | `7071` (or `7072` to avoid clash) | Only when debugging upstream data |

Default target for processes 3 and 4 is the deployed **QA** environment (`aldcqafnapcore1c01`, `aldcqafnapf921c01`). The shared master token works across dev/test/qa/prod.

### 6.2 Prerequisites

- **Node.js 24.x** (pinned in Dockerfile + PR_checks.yaml). `nvm use 24`.
- **Python 3.11** — only if running core_api locally (`pyarrow==15.0.0` has no wheels for 3.13+). `winget install Python.Python.3.11`.
- **Azure Functions Core Tools v4** (`func` CLI) — only for local backends. `npm install -g azure-functions-core-tools@4 --unsafe-perm true`.
- **Azure CLI** (`az`) — for backend deploys and pulling Function App config.
- **Git Bash or WSL** on Windows (activate scripts differ from macOS/Linux).
- **VS Code Azure Functions extension** — optional; required for one-click deploys of `F92_workflow_app` (it has no CI/CD).
- **Docker + Docker Compose** — optional; only for `compose_test.yaml` or image-build flows.
- **Credentials from Dashlane / `vault/credentials.md`**: `DAX_API_MASTER_TOKEN`, `F92_NETSUITE_SYNC_TOKEN`, `F92_NETSUITE_PUBLISHERS_TOKEN`, `DIOS_API_KEY`, `NEXTAUTH_SECRET` (must match parent Eclipse), plus `NETSUITE_PRIVATE_KEY` (PEM sandbox) and `MICROSOFT_ADS_CLIENT_SECRET` if running the backend.

> **`api_token` is the shared master bearer.** Value `<REDACTED — core_api MASTER bearer; see vault/infra-credentials.md § MASTER API bearer (default)>` (base64 of `FFFFFFFF0000:<REDACTED — see vault/infra-credentials.md § MASTER API bearer (default)>`). Same across all core_api environments — you only need to change `api_url` to switch envs.

### 6.3 Auth model — parent-portal session cookie

The frontend registers NextAuth with `providers: []` and cannot log users in. The session cookie is issued by the parent Eclipse portal and shared via `__Secure-next-auth.session-token` (or `next-auth.session-token` on HTTP).

Working local pattern:

1. Run parent Eclipse at `localhost:3000`, flight-check at `localhost:3100`.
2. In flight-check's `.env.local`, set `NEXTAUTH_URL=http://localhost:3000/` — i.e. the **parent** URL, not flight-check's own. Cookie domain becomes `.localhost`, which modern browsers accept for cookies shared across ports on the same hostname.
3. Set the same `NEXTAUTH_SECRET` in both apps.
4. Log in at `http://localhost:3000`; navigate to the DAX app — parent iframes `:3100` and the cookie flows.

**Hosts-file alias (secondary)** — only when you need a realistic origin for CSP testing:
- Map `iframe.fusion92.website.org` → `127.0.0.1` in hosts.
- Set `NEXTAUTH_URL=http://iframe.fusion92.website.org:3100/` and `CHILD_SRC_ALLOWED_ORIGINS=iframe.fusion92.website.org:3100`.
- Both lines exist as commented defaults in the canonical `.env.local`.

### 6.4 Frontend — flight-check (minimum setup)

```bash
cd C:/Users/PaulRussell/repos/flight-check
nvm use 24
npm install
cp .env.template .env.local
# ECLIPSE_URL is referenced in pages/api/core/sendWelcomeEmail.tsx:44
# but missing from .env.template — add it manually.
npm run dev                               # :3100
```

**Canonical `.env.local` for QA-backed UI work** (NetSuite sync off, PostHog/notifications omitted):

```bash
NEXTAUTH_URL=http://localhost:3000/
NEXTAUTH_SECRET=<same value as parent Eclipse>
CHILD_SRC_ALLOWED_ORIGINS=localhost:3100
ECLIPSE_URL=http://localhost:3000

# core_api — shared master bearer across dev/test/qa/prod; switch env by swapping api_url alone
api_url=https://aldcqafnapcore1c01.azurewebsites.net/v1/
api_token=<REDACTED — core_api MASTER bearer; see vault/infra-credentials.md § MASTER API bearer (default)>

# Fusion account the app binds to (TEST/PROD = 0fc00e34, QA = f49f9aa3)
account_id="0fc00e34"

# DAX API (QA)
DAX_API_URL="https://aldcqafnapf921c01.azurewebsites.net/api/dax"
DAX_API_MASTER_TOKEN=<from Dashlane>

# NetSuite workflow (TEST — keys from Dashlane). Sync disabled by default.
F92_NETSUITE_SYNC_ENABLED=false
F92_NETSUITE_WORKFLOW_URL=https://aldctestfnapf921c01.azurewebsites.net
F92_NETSUITE_PUBLISHERS_TOKEN=<from Dashlane>
F92_NETSUITE_SYNC_TOKEN=<from Dashlane>

# DIOS (on-prem)
DIOS_API_URL=https://audience-fusion92-app.aldc-ca-w1.com
DIOS_API_KEY=<from Dashlane>
```

**Leave blank / omit for basic dev:**
- `STAC_NAME` / `STAC_KEY` — dead vars.
- `NEXT_PUBLIC_POSTHOG_*` — unused; project key is hard-coded in `components/PostHogProvider.tsx:8`.
- `F92_NOTIFICATION_KEY` / `F92_NOTIFICATION_URL` — only needed when exercising the notification-settings page.

**Env switching.** The canonical `.env.local` keeps dev/test/local alternatives commented next to each active block. To switch: uncomment the matching `api_url` / `DAX_API_URL` / `F92_NETSUITE_WORKFLOW_URL` lines, flip `account_id` (`f49f9aa3` for QA, `0fc00e34` for TEST/PROD). `api_token` doesn't change — it's the shared master bearer.

> **Cross-env mix is valid.** A working config may point `api_url`+`DAX_API_URL` at QA while `F92_NETSUITE_WORKFLOW_URL` points at TEST — the master token grants access to all envs. Be aware which deployment group the NetSuite publisher lookups resolve against when debugging.

> **PostHog events from local dev land in the production PostHog project** because the key is hard-coded. Stub `PostHogProvider.tsx` if that matters for your work.

### 6.5 Parent portal — eclipse

```bash
cd C:/Users/PaulRussell/repos/eclipse
nvm use 24
npm install
cp .env.template .env.local              # fill in; NEXTAUTH_SECRET must match flight-check
npm run dev                              # :3000
```

### 6.6 Minimum end-to-end run (two terminals)

With the config above — DAX API and core_api pointed at QA — you **do not need Python or `func start`**:

```bash
# Terminal 1 — parent portal (session issuer)
cd eclipse
npm run dev                              # :3000

# Terminal 2 — flight-check
cd flight-check
npm run dev                              # :3100
```

**Do not open `http://localhost:3100/` directly** — `pages/` has no `index.tsx`, so the required catch-all `[...slug].tsx` returns 404 at the root. The app is only designed to be reached from the parent portal, with a slug attached.

**Entry URL that works** (verified 2026-04-23):

```
http://localhost:3000/login?callbackUrl=%2Fapplication%2Fhome%2FFlight%2520Check
```

- `callbackUrl` URL-decodes to `/application/home/Flight Check`.
- Log in with the super/admin credentials from `vault/credentials.md`.
- After login the portal navigates to `/application/home/Flight Check`, which iframes flight-check with the session cookie and the correct slug attached. The DAX app loads successfully.

If you land on the Eclipse portal home instead, manually navigate into the **Flight Check** tile — same result, the portal constructs the slugged iframe URL for you.

Data flows: browser → flight-check (`:3100`) → QA core_api + QA DAX API + TEST NetSuite publishers.

### 6.7 Backend — F92_workflow_app (only when needed)

Stand this up when editing pacing/calculations, NetSuite PO sync, or timer-driven jobs:

```bash
cd C:/Users/PaulRussell/repos/workflows/fusion_92/F92_workflow_app

python -m venv .venv
source .venv/Scripts/activate            # Git Bash
pip install -r requirements.txt
cp local.settings.template.json local.settings.json
# Fill in per table below. Put NETSUITE_PRIVATE_KEY in a separate .env (never in settings JSON).

func start                               # :7071
```

Then in flight-check's `.env.local`, repoint:
```bash
DAX_API_URL="http://127.0.0.1:7071/api/dax"
DAX_API_MASTER_TOKEN="none-for-local"
# Also set F92_NETSUITE_WORKFLOW_URL=http://127.0.0.1:7071 and F92_NETSUITE_SYNC_ENABLED=true
# if testing NetSuite PO sync end-to-end locally.
```

**Required `local.settings.json` values:**

| Var | Value for local |
|---|---|
| `AzureWebJobsStorage` | `UseDevelopmentStorage=true` (Azurite) or dev storage connection string |
| `FUNCTIONS_WORKER_RUNTIME` | `python` |
| `core_api_url` | e.g. `https://aldcqafnapcore1c01.azurewebsites.net/v1/` — **must end with `/`** |
| `core_api_token` | QA function key from Dashlane |
| `account_id` | `f49f9aa3` (QA) or `0fc00e34` (TEST/PROD) |
| `eclipse_url` | `http://localhost:3000` |
| `ENVIRONMENT` | `local` |
| `application_type` | `9b9a62ab-6021-4147-85f9-74f9ebe9767a` |
| `AzureWebJobs.<timer-func>.Disabled` | `true` for every timer (keep template defaults) |
| NetSuite | `NETSUITE_ACCOUNT_ID=7378083-sb1`, `NETSUITE_CLIENT_ID`, `NETSUITE_CERTIFICATE_ID`, `ALDC_NETSUITE_EMPLOYEE_ID=13456`, `NETSUITE_PO_CLIENT_LEAD_ID=13417`, **`NETSUITE_PO_PROJECT_MANAGER_ID=2747`** |
| Microsoft Ads | `MICROSOFT_ADS_CLIENT_SECRET`, `MICROSOFT_ADS_CONNECTION_ID` (env `MICROSOFT_ADS_CLIENT_ID` is ignored — hard-coded in `bing_ads.py:31`) |

> **Two gotchas baked into the template:**
> 1. Template names `NETSUITE_PO_PROJECT_MANAGER_LEAD`; code at `workflows/netsuite.py:232` reads `NETSUITE_PO_PROJECT_MANAGER_ID`. **Use `_ID`.**
> 2. `MICROSOFT_ADS_CLIENT_ID` in the template is **not read** — hard-coded in `bing_ads.py:31`.

Separate `.env` file for the PEM body (template explicitly says don't paste into settings JSON):
```
NETSUITE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...-----END PRIVATE KEY-----
```

**Smoke test:**
```bash
curl -H "x-functions-key: anything" \
  "http://localhost:7071/api/dax/flights/<known-flight-id>?add-calc=true"
```
Expect a JSON `FlightDocument`. A 500 with `error_context` pointing at `core_api_url` usually means a missing trailing `/`.

### 6.8 core_api locally (only when debugging upstream)

Full runbook: [[core-api-local-setup]]. Short version — core_api and F92_workflow_app both default to port 7071, so run one on `--port 7072`:

```bash
cd C:/Users/PaulRussell/repos/core_api
py -3.11 -m venv .venv
source .venv/Scripts/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
# Get local.settings.json from vault/core-api-local-settings.md (never commit).
func start --port 7072
```

Then update flight-check's `.env.local`:
```bash
api_url=http://127.0.0.1:7072/v1/        # note: /v1/, not /api/v1/ (routePrefix: "")
# api_token stays as the shared master bearer
```

### 6.9 Running tests and lint

**Frontend:**
```bash
npm run lint          # ESLint --fix --max-warnings=0
npm run lint:check    # no --fix (runs in PR_checks.yaml)
npm run format        # Prettier write
npm run format:check  # Prettier check (runs in PR_checks.yaml)
npm test              # Jest — one placeholder test
```
Husky pre-commit runs `lint-staged` (ESLint fix + Prettier) on changed files.

**Backend:**
```bash
cd workflows/fusion_92/F92_workflow_app
pytest                # test/test_job_calculations.py (4 classes, 556 lines)
```
No CI runs these. Ignore `test_function.ps1` — it points at a non-existent endpoint.

### 6.10 Debugging tips

| Symptom | Where to look |
|---|---|
| `GET /` returns 404 on `http://localhost:3100/` | Expected — no `pages/index.tsx`; required catch-all `[...slug].tsx` doesn't match root. Enter via the parent portal's login page with a `callbackUrl` (see § 6.6). |
| Session resolves as null | Confirm `NEXTAUTH_URL` points at the **parent** portal URL (§ 6.3), and `NEXTAUTH_SECRET` matches the parent's. Visit `/api/auth/session` to inspect JWT claims. |
| "Why is X null?" | `pages/api/coreAPI.tsx:29–35` silently rewrites `NaN` → `null` before `JSON.parse`. Check the raw upstream response. |
| Form bound to wrong Fusion account | `metadata/Job.json` / `job_details.json` / `admin.json` carry env-specific `account_id` (`0fc00e34` TEST/PROD vs `f49f9aa3` QA) + `app_url` (`.io` prod / `.com` QA). |
| PostHog events in prod project | Hard-coded key in `components/PostHogProvider.tsx:8` fires in all envs including local. Stub it for local work. |
| `/v1application/read` 404 | Missing trailing `/` on `core_api_url` / `api_url`. Every caller concatenates `f"{url}{route}"`. |
| Local core_api 404 on `/api/v1/...` | `host.json` sets `routePrefix: ""`. Use `/v1/...`. |
| Double-sent notifications (prod) | Staging slot wasn't disabled for timer functions. Set `AzureWebJobs.<func>.Disabled=true` as slot-specific. |
| Microsoft Ads OAuth refresh failing | `CLIENT_ID` is hard-coded in `bing_ads.py:31`; env var is ignored. Manual PowerShell fallback in [[connector-token-refresh]]. |
| Timer not firing locally | Intended — every `AzureWebJobs.<func>.Disabled` is `true` in the template. Flip one to `false` to test, or invoke the paired HTTP endpoint. |
| Port 7071 clash | core_api and F92_workflow_app both default to 7071. Run one on `func start --port 7072`. |
| pyarrow build fails | Python 3.13+. Recreate venv with `py -3.11`. |

---

## 7. Deployment — At a Glance

### Frontend (flight-check)

1. Merge PR to `main`.
2. GitHub Actions → "Deploy to Azure App Service" → `workflow_dispatch` → pick env.
3. Azure login via OIDC → `next build` → `azure/webapps-deploy@v3` → **staging slot**.
4. Smoke-test the staging slot URL.
5. Azure Portal → App Service → Deployment slots → **Swap staging ↔ production**.
6. **If `metadata/*.json` changed**: update `account_id` + `app_url` for the target env, then paste into the target CosmosDB metadata container via Cosmos Data Explorer. No automation.
7. Rollback = swap again.

Follows the [[eclipse-azure-deployment]] pattern.

### Backend (F92_workflow_app)

1. No CI/CD — right-click `F92_workflow_app/` → "Deploy to Function App…" in VS Code Azure Functions extension (or `func azure functionapp publish <app-name>`).
2. In Azure Portal → Function App → Configuration, set env vars per § 6.2.
3. On the **staging slot**, add each `AzureWebJobs.<timer>.Disabled=true` as **slot-scoped** (the "Deployment Slot" checkbox) so a swap doesn't propagate to prod.
4. Twice a year: edit `function_app.py` to swap commented-in cron strings (summer ↔ winter) and redeploy.
5. Rollback = **swap back**, not "redeploy previous commit" — see § 7.1.

### 7.1 Deploying from the CLI — what the tooling gets wrong (measured 2026-09-09, prod)

A full prod deploy of both tiers was done from the command line rather than VS Code. Four things bit,
all worth knowing before the next one.

**⛔ The app name in `workflows/README.md` is wrong.** It lists `aldcprodfnapfn921c01`; the resource is
**`aldcprodfnapf921c01`** (no `n` after `fnap`). The README's own test URLs are correct. RG is
`aldcprodfnapf921c01`; plan is **Y1 / Dynamic** (Linux Consumption). The frontend is
`aldcprodwbapflightcheck1c01` in RG `aldcprodrsgp1c` — take it from the Production environment
variable `AZURE_APP_SERVICE_NAME`, not from memory.

**⛔ `func azure functionapp publish --slot` reports the OPPOSITE of the truth, in both directions:**

```
Resetting all workers for aldcprodfnapf921c01-stage.azurewebsites.net
Reset all workers endpoint responded with ... 404 (Site Not Found).
Deployment Failed. ... Remote build failed!
[exited with code 0]
```

The exit code said success while the output said failure — *and the failure was itself false*: the
remote build had completed, the squashfs artifact was uploaded, and the code was serving. The only
genuine failure is the final worker-reset call, whose endpoint **does not resolve for a slot on a
Y1/Dynamic plan**. Treat that specific message as expected noise here; **verify by what the host
serves, never by the exit code or the log.**

**⭐ The credential-free way to tell which build a Function App is serving.** Azure Functions returns
**404 for an undeclared HTTP method** on a matched route and **401 for a declared method without a
key** — so a status code alone reveals whether a new verb exists, with no function key needed:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST "https://<app>.azurewebsites.net/api/<route>"
#   401 -> the method is declared (new build)      404 -> undeclared (old build)
```

Always run the *old* host first as a control, to prove method mismatch really does yield 404 in that
app — otherwise a 401 proves nothing. This also verifies the rollback artifact: after a swap the stage
slot should flip back to 404, which *measures* that the previous build is parked and revertible.

**⛔ The frontend Actions workflow deploys to `stage` and health-checks it — it never swaps.** A green
run does **not** mean production changed. The swap is a separate deliberate step (step 5 above), and it
is the easiest thing in this pipeline to forget.

### 7.2 Rollback — one command per tier, seconds, no rebuild

Because both tiers deploy to `stage` and then swap, the swap itself *preserves the previous production
build in the stage slot*. That, not a redeploy, is the rollback:

```bash
# backend
az functionapp deployment slot swap --subscription "Production 2" \
  -g aldcprodfnapf921c01 -n aldcprodfnapf921c01 --slot stage --target-slot production
# frontend
az webapp deployment slot swap --subscription "Production 2" \
  -g aldcprodrsgp1c -n aldcprodwbapflightcheck1c01 --slot stage --target-slot production
```

**Prod is untouched until the swap**, so up to that point the rollback is "do nothing". Verify the
artifact is really parked (§ 7.1) rather than assuming it.

### 7.3 Pre-deploy checks that are cheap and have paid off

- **Does the change add or remove functions?** The README's key-swap failure mode is pinned to exactly
  that. Enumerate with `az functionapp function list` and compare — prod ran **20** functions in
  Sept 2026. A change that only adds an HTTP verb adds none, and is therefore the low-risk shape.
- **Are all `AzureWebJobs.*.Disabled` settings slot-scoped?** Confirmed yes in prod (all 7), so they
  correctly do not travel on a swap. ⚠ Project **names only** when listing app settings —
  `starts_with(name,'AzureWebJobs')` also matches `AzureWebJobsStorage`, whose value is a live storage
  account key. Use `'AzureWebJobs.'` **with the dot**.
- **Verify the key path after swapping, without a session:** call the frontend proxy with a *bogus*
  job id. A **500** means the request reached application logic, so the server-side key still
  authenticates; a **401** means the keys swapped. No client data is returned either way.

---

## 8. Known Tech Debt / Gotchas Checklist

**Security**
- [ ] **Rotate Cosmos keys** — `workflows/fusion_92/F92_notification_cron_update/.env` is committed with **prod, dev, and test Cosmos hostnames + keys** (all six values are in git history). Extracted to `vault/infra-credentials.md` § Fusion92 — Cosmos DB. Rotate + gitignore + consider history rewrite.
- [ ] `update.py` in that same folder is a **destructive utility pointed at prod by default** — would set every Fusion production notification cron to `* * * * *` (once per minute). No dry-run flag, no confirmation prompt.

**Frontend**
- [ ] `package.json` name is `"eclipse"` — fork-scaffold leftover.
- [ ] PR checks trigger on `pull_request.synchronize` only (first push of a new PR skips CI).
- [ ] No healthcheck endpoint — Azure probes `/`.
- [ ] No Application Insights / Log Analytics integration — server-side errors are `console.error` only.
- [ ] Hard-coded PostHog key shadows the `.env.template` var.
- [ ] `NaN → null` scrubbing is a band-aid; proper fix belongs in core_api response serialisation.
- [ ] Four UI kits + three date libs coexist — consolidation targets are Mantine + js-joda.
- [ ] `pacing * 100` hack in `lib/dax/flights.ts:62` — should be fixed in the DAX API backend.
- [ ] `STAC_NAME` / `STAC_KEY` in `.env.template` are dead.
- [ ] `ECLIPSE_URL` is referenced in code but missing from `.env.template` — add manually.
- [ ] QA uses `.com` TLD while Prod uses `.io` — persistent source of confusion; rename target.
- [ ] GHCR image-publish step is not visible in `.github/workflows/`; `compose.yaml` references an image that nothing pushes on `main`.
- [ ] Mega-files: `[...slug].tsx` ~25 k lines, `ApplicationTable.tsx` ~99 k, `AccountForm.tsx` ~106 k, `F92DataTable.tsx` ~40 k.

**Backend**
- [ ] **No CI/CD at all** — no `.github/` in the repo. Manual VS Code deploys. No test gate, no reproducible build. Outlier in the ALDC portfolio.
- [ ] Two parallel API patterns (`dax_api/` typed + `workflows/` legacy). Three endpoints still legacy.
- [ ] DST cron switch is manual (twice-a-year redeploy).
- [ ] Timer slot-swap discipline is only documented in `function_app.py` docstrings.
- [ ] `NETSUITE_PO_PROJECT_MANAGER_LEAD` vs `..._ID` template/code mismatch.
- [ ] Microsoft Ads `CLIENT_ID` hard-coded in `bing_ads.py:31`.
- [ ] `test_function.ps1` references a non-existent endpoint.
- [ ] `core_api_url` must end with `/`.
- [ ] `dotenv.load_dotenv(override=True)` at module import → env bleed between shells.
- [ ] `dataset/query` FIXME — should be `dataset/request` per `core_client.py:257–259`.
- [ ] Unpinned `requirements.txt`, no `pyproject.toml`.
- [ ] One test file covering calculations; nothing else tested.
- [ ] Email-send errors silently swallowed per-document in the batch loop — check App Insights when notifications go missing.
- [ ] **Snowflake sync `only_recent` 30-day window silently drops flights** ([[FU92-419]]). `dax_api/sync/lib.py` `RECENT_DAYS_TO_PULL=30`; a flight edited just before a sync outage ages out of the window on resume and is never re-synced (stale CDC snapshot persists → "$0 / no data" in the UI, e.g. 6T901 / Job PRJ002345, fixed 2026-06-05). Fix = periodic full reconcile or last-successful-sync high-water-mark.
- [ ] **Legacy Firebase Flight Check sync still scheduled** ([[FU92-419]]) — the pre-Nov-2024 Firebase app (`flight-check-ae37d`, ~10,444 dead flights) is still synced into `FLIGHT_CHECK.FLIGHTS_FLIGHTS` and fires false "customer-impacted" alerts. Retire it.

> **Two-backend gotcha (confirmed 2026-06-05):** current flights live in **Cosmos** (authoritative since Nov 2024); the **Firebase** project is the *legacy* app. They feed **different** Snowflake tables — Cosmos → `DATA_STORE.FLIGHT_CHECK_SYNC_FLIGHT` → `SHARED_DIM_FLIGHT` (the warehouse the UI/spend-matching reads); Firebase → `FLIGHT_CHECK.FLIGHTS_FLIGHTS` (legacy). When debugging a "$0" flight, trace the **Cosmos** path. `SHARED_DIM_FLIGHT`/`FCT_PLATFORM_SPEND`/`FCT_DAILY_SPEND` are **dynamic tables** (`TARGET_LAG=DOWNSTREAM`) — force propagation with `ALTER DYNAMIC TABLE … REFRESH`.

---

## See Also

- [[entities/repos/flight-check|flight-check (repo)]] — full engineering reference for the frontend repo (canonical source for FE internals).
- [[workflows]] — full engineering reference for the backend / DAX API (canonical source for BE internals).
- [[dax-media-app]] — the product page. Roles, statuses, phases, NetSuite PO sync business rules, UAT history.
- [[entities/repos/eclipse|eclipse (repo)]] — the host portal this app iframes into; shares NextAuth session cookie + admin UI components.
- [[core_api]] — primary backend; every `/api/coreAPI` call routes through it.
- [[custom-fusion-92-audience-api]] — DIOS (on-prem FastAPI) proxied by `/api/dios/*`.
- [[fusion92]] — client page.
- [[fusion92-platform-ids]] — platform account/campaign/order ID mapping used by Flight Check.
- [[fusion92-data-architecture]] — upstream Snowflake setup.
- [[data-pipeline-flow]] — end-to-end ALDC pipeline context (Snowflake sync is a leaf).
- [[cosmosdb-schema]], [[core-api-data-model]] — data-model context for jobs / flights / users / notifications / metadata.
- [[eclipse-azure-deployment]] — the staging-slot deploy pattern flight-check follows.
- [[connector-token-refresh]] — manual fallback when `f92_refresh_microsoft_ads_token` fails.
- [[bing-ads]] — Microsoft Ads connector reference.
- [[mailjet]] — downstream email delivery.
- [[azure-environments]], [[deployment-groups]], [[aldc-naming-convention]] — Azure environment + naming context.
- [[flight-check]] — **different thing**. ALDC's operational data-pipeline validation runbook. Same name only.
