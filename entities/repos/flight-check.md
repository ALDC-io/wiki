---
tags: [entity, repo, flight-check, dax-media-app, fusion92, nextjs, react, frontend]
aliases: [flight-check repo, DAX Media App frontend, Flight Check frontend, dax.fusion92.eclipse.aldc.io]
sources: [repos/flight-check/README.md, repos/flight-check/package.json, repos/flight-check/Dockerfile, repos/flight-check/compose.yaml, repos/flight-check/compose_test.yaml, repos/flight-check/.env.template, repos/flight-check/authOptions.ts, repos/flight-check/next.config.mjs, repos/flight-check/pages/_app.tsx, repos/flight-check/pages/api/coreAPI.tsx, repos/flight-check/pages/api/auth/[...nextauth].tsx, repos/flight-check/pages/api/dax/calculations.ts, repos/flight-check/pages/api/dax/jobs/[job_id]/index.ts, repos/flight-check/pages/api/dax/jobs/[job_id]/export/index.ts, repos/flight-check/pages/api/dax/jobs/export.ts, repos/flight-check/pages/api/dax/flights/[flight_id].ts, repos/flight-check/pages/api/netsuite/publishers.ts, repos/flight-check/pages/api/netsuite/sync/enabled.ts, repos/flight-check/pages/api/netsuite/sync/syncpo.ts, repos/flight-check/pages/api/dios/audience/process.ts, repos/flight-check/pages/api/dios/projects/[projectName]/audiences.ts, repos/flight-check/pages/api/core/notificationCreate.tsx, repos/flight-check/pages/api/core/notificationUpdate.tsx, repos/flight-check/pages/api/core/sendWelcomeEmail.tsx, repos/flight-check/lib/dax/apiUtils.ts, repos/flight-check/lib/dax/types.ts, repos/flight-check/lib/dax/flights.ts, repos/flight-check/lib/dax/jobs.ts, repos/flight-check/lib/dax/notifications.ts, repos/flight-check/lib/dax/metricsTable.ts, repos/flight-check/lib/dax/exports.ts, repos/flight-check/metadata/README.MD, repos/flight-check/metadata/Job.json, repos/flight-check/metadata/admin.json, repos/flight-check/.github/workflows/PR_checks.yaml, repos/flight-check/.github/workflows/deploy_az_webapp.yaml]
created: 2026-04-20
updated: 2026-04-20
---

# flight-check (repo)

> **Disambiguation:** Three wiki pages share the "flight check" phrase.
> - **This page** — the Next.js frontend repo at `C:\Users\PaulRussell\repos\flight-check`. Engineering reference.
> - **[[dax-media-app]]** — the *product* page (Fusion92-facing: "DAX Media App" / "Flight Check App"). Roles, phases, NetSuite sync flow, UAT history. Go there for product scope.
> - **[[flight-check]]** (`processes/operations/flight-check.md`) — ALDC's operational data-pipeline validation runbook. Completely different thing, same name.

The **Next.js frontend** for the [[dax-media-app|DAX Media App]] — Fusion92's flight-management UI that replaced their legacy Firebase Flight Check app in November 2024. In production at `https://dax.fusion92.eclipse.aldc.io` (QA: `https://dax.fusion92.eclipse.aldc-ca-w1.com` — note `.com`, not `.io`).

The app runs as an embedded iframe inside the [[entities/repos/eclipse|eclipse portal]] and communicates with the parent frame via `postMessage` (`pages/_app.tsx:44–204`, `NAVIGATION_CHANGE` / `PARENT_NAVIGATION_CHANGE` events). All data calls are proxied server-side through four backends: [[core_api]], the **DAX API** ([[workflows|workflows repo]] — `F92_workflow_app`), **DIOS** (→ [[custom-fusion-92-audience-api]]), and **F92's NetSuite Workflow service** (also [[workflows|workflows repo]] — both `DAX_API_URL` and `F92_NETSUITE_WORKFLOW_URL` resolve to the same `F92_workflow_app` function app).

This repo is a fork/clone of the [[entities/repos/eclipse|eclipse repo]] scaffold — `package.json` still reads `"name": "eclipse"` (copy-paste artefact from the scaffold; ignore it). Many components (`AccountForm`, `ApplicationForm`, `BreadCrumb`, `Sidebar`, `UserForm`) are duplicated across both repos — any fix to shared-looking UI may need to land in both repos.

Product-level scope (roles, statuses, phases, NetSuite sync rules, DIOS audience flow, Buyer role, PRJ537) lives on [[dax-media-app]]; this page covers the **engineering/repo** side only.

---

## Architecture

### Repository layout

| Path | Purpose |
|---|---|
| `pages/` | Pages Router routes. `[...slug].tsx` is the main dynamic app loader (~25 k lines). |
| `pages/_app.tsx` | Provider stack + **iframe URL-sync `postMessage` bridge** to parent Eclipse portal (lines 44–204) |
| `pages/api/coreAPI.tsx` | Universal proxy to [[core_api]] (mirrors the [[entities/repos/eclipse|eclipse]] pattern). Also strips `NaN` tokens from response text before `JSON.parse` (`coreAPI.tsx:29–35`) |
| `pages/api/auth/[...nextauth].tsx` | NextAuth entry — **empty `providers: []`**; auth is inherited via shared session cookie issued by the parent portal |
| `pages/api/core/` | `notificationCreate`, `notificationUpdate`, `sendWelcomeEmail` — routed through the `coreAPI` proxy |
| `pages/api/dax/` | Thin proxies to the DAX API (`calculations`, `jobs/[job_id]`, `jobs/export`, `jobs/[job_id]/export`, `flights/[flight_id]`) using `lib/dax/apiUtils.ts` |
| `pages/api/netsuite/` | `publishers`, `sync/enabled`, `sync/syncpo` — proxies to F92's NetSuite Workflow app |
| `pages/api/dios/` | `audience/process`, `projects/[projectName]/audiences` — proxies to [[custom-fusion-92-audience-api]] (DIOS) |
| `pages/settings.tsx` | User profile + `DaxMediaNotificationSettings` (pacing + status notifications, F92-only) |
| `pages/security_and_groups.tsx` | Admin RBAC |
| `pages/manage_team/` | Team admin (add_user, edit_user) |
| `pages/account_settings/` | Account admin (internal: full form; others: read-only) |
| `components/` | ~38 top-level components + subdirs: `Fusion92/`, `application/`, `flights/metricsTable/`, `inputs/`, `nonHTMLcomponents/`, `settings/` |
| `components/Fusion92/` | F92-only: `DownloadAuditTrail`, `NetSuiteCreatePOButton`, `NetSuiteModal`, `NetSuiteSyncContext`, `NetSuiteSyncStatus`, `NetSuiteUnlockPOButton`, `NetSuiteUtils`, `ProcessAudienceFilesButton` |
| `components/application/` | `FormBottomControls`, `FormFieldRenderer`, `FormModals`, `FormSectionsRenderer`, `FormStatusHeader`, `SearchedDropdown` — drive the metadata-driven form engine |
| `components/flights/metricsTable/` | Pacing grid: `FlightMetricsTable`, `FlightMetrics`, `FlightMetricsTableDataRow`, `FlightMetricsTableActionRow`, `EditFlightMetricsRowModal`, `DeleteFlightMetricsRowModal`, `FilterFlightMetricsTableModal` |
| `components/nonHTMLcomponents/` | Utilities: `ApplicationDataCleanup` (F92JobListFormat, F92FlightListFormat), `F92Theme`, `F92StatusTransitions`, `StringFormatting`, `constants` (F92 account IDs, Dataset ID, `FLIGHT_CHECK_APPLICATION_TYPE_*`), `UserAccountGroupAPI`, `Condition`, `util`, `ColorLogic` |
| `components/settings/` | `DaxMediaNotificationSettings`, `NotificationSetting` |
| `lib/dax/` | DAX API client lib — `apiUtils.ts` (env loader + GET/POST helpers), `types.ts`, `flights.ts`, `jobs.ts`, `notifications.ts`, `metricsTable.ts`, `exports.ts` |
| `lib/dates.ts`, `lib/numbers.ts` | Date/number helpers (js-joda + date-fns + dayjs — three date libs coexist; see tech debt) |
| `metadata/` | JSON metadata files that drive forms at runtime — `Job.json`, `job_details.json`, `admin.json`. Must be manually copied to CosmosDB on deploy (`metadata/README.MD`) |
| `authOptions.ts` | NextAuth config — empty providers; cookie `domain: .${NEXTAUTH_URL hostname}` shares session with parent portal. JWT claims: `first_name`, `last_name`, `email`, `active_account(_name)`, `id`, `is_internal`, `is_admin`, `applications`, `groups`, `date_joined` |
| `next.config.mjs` | `reactStrictMode: true`, `output: "standalone"` |
| `types/next-auth.d.tsx` | Type augmentation for session fields (same shape as eclipse repo) |
| `__test__/index.test.js` | **The only test file** — trivial `expect(true).toBe(true)` placeholder. Effectively untested. |
| `__mock__/` | Jest mocks for static assets |
| `.github/workflows/PR_checks.yaml` | Node 24 lint + format + `npm audit --omit=dev` |
| `.github/workflows/deploy_az_webapp.yaml` | Manual `workflow_dispatch` → Azure Web App staging slot |
| `Dockerfile`, `compose.yaml`, `compose_test.yaml` | Node 24 Alpine multi-stage image, standalone build, `CHILD_SRC_ALLOWED_ORIGINS=flight-check.eclipse.aldc.io` |
| `.husky/pre-commit` | `npx lint-staged` |

### Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | Next.js **16.1.6** (Pages Router) | Newer than the [[entities/repos/eclipse\|eclipse]] repo (14.2) — upgrade was likely opportunistic; no App Router |
| Node runtime | Node 24 (Dockerfile + both GitHub workflows) | Consistent across build/run |
| Language | TypeScript 5.9 strict mode, `paths: {@/*: ./*}`, `target: ES2017` | |
| UI primary | Mantine 7 + NextUI 2 + flowbite-react + `@headlessui/react` | **Four UI kits coexist** — legacy migration residue; new code targets Mantine |
| Styling | Tailwind 3.4 + SCSS + `postcss-preset-mantine` + `postcss-simple-vars` + CSS vars (`--font-light` etc.) | Theme tokens via CSS vars for light/dark |
| Auth | NextAuth 4 (`next-auth: ^4.24.7`) — **`providers: []`** | Session cookie issued by parent Eclipse portal, shared via `__Secure-next-auth.session-token` at domain `.eclipse.aldc.io`. This app cannot log users in on its own. |
| Analytics | PostHog (`posthog-js: ^1.364.4`) | Key hard-coded in `components/PostHogProvider.tsx:8` — PostHog project keys are public by design, but stylistically should be env-var-driven (see tech debt) |
| HTTP | `fetch` (built-in) + `axios` (dependency, few call-sites) | |
| Date/time | `@js-joda/core`, `date-fns`, `dayjs`, `react-datepicker` | Three date libs — consolidation in progress toward js-joda |
| CSV | `papaparse` | |
| State | React local state only — no Redux/Zustand/React Query. `NetSuiteSyncContext` is the single React Context. | |
| Testing | Jest 29 + `@testing-library/react 16` + `jest-environment-jsdom`; `next/jest` preset | One trivial test file — effectively untested |
| Lint/format | ESLint 8 + `@typescript-eslint/*` + `@stylistic/*` + `next/core-web-vitals` + Prettier 3.4 | `lint:check` uses `--max-warnings=0`; Husky 9 + lint-staged 15 pre-commit |

### How a request flows

1. Parent [[entities/repos/eclipse|eclipse]] portal loads `https://dax.fusion92.eclipse.aldc.io` in an iframe (the parent's `Content-Security-Policy: child-src` allow-list governs this; `metadata/admin.json` `app_url` tells the portal where to point the iframe).
2. Because the subdomain is `*.eclipse.aldc.io`, the shared NextAuth session cookie (`__Secure-next-auth.session-token`, domain `.eclipse.aldc.io`) is sent with every request. `authOptions.cookies.sessionToken.options.domain = .${new URL(NEXTAUTH_URL).hostname}`.
3. Next.js page mounts inside `_app.tsx`. Provider stack (outermost→innermost): `SessionProvider` → `PostHogProviderWrapper` → `ThemeWrapper` → `MantineProvider` (custom `eclipseBlue` palette) → `ModalsProvider` → `NextUIProvider`.
4. `_app.tsx` registers a bidirectional `postMessage` bridge (lines 44–204): monkey-patches `window.history.pushState`/`replaceState`, intercepts `popstate`/`hashchange`, a `MutationObserver`, and a 2-second poll fallback. On any URL change, posts `{type: "NAVIGATION_CHANGE", path, timestamp}` to `window.parent`. Listens for `{type: "PARENT_NAVIGATION_CHANGE", path, source}` to sync itself (uses `replaceState` when `source === "popstate"` to avoid polluting history).
5. Pages call `fetch("/api/coreAPI", { method: "POST", body: {url, message} })` for core_api data, or `/api/dax/*` for DAX data, `/api/dios/*` for DIOS, `/api/netsuite/*` for NetSuite.
6. Each server-side API route reads its credential env var, calls the upstream service, normalises the response, and returns JSON to the client.

### Key abstractions

**`pages/api/coreAPI.tsx` — universal core_api proxy.** Reads `api_url` + `api_token` and POSTs to `${api_url}${url}`. Non-obvious: cleans `NaN` tokens from response text before `JSON.parse` (lines 29–35 — `.replace(/:\s*NaN/g, ": null")` etc.) because core_api sometimes emits non-standard JSON. Exported as `apiCall()` for reuse in `api/core/sendWelcomeEmail.tsx` and `api/core/notificationCreate.tsx`.

**`lib/dax/apiUtils.ts` — DAX API client lib.** `get_dax_api_env()` reads `DAX_API_URL` + `DAX_API_MASTER_TOKEN` (throws if missing). `setup_dax_api_headers(key)` sets `x-functions-key` (Azure Functions key-based auth) + `Content-Type`. `dax_api_get()` / `dax_api_post()` return a unified `{status, data}` shape where `data` is either the payload or a `{error, error_description, error_context}` triple. Every `pages/api/dax/*` file is a thin wrapper around these.

**`authOptions.ts` — NextAuth with empty providers.** Session/JWT callbacks shape the token from an upstream login (done in the parent Eclipse portal). Cookie domain set to `.${NEXTAUTH_URL hostname}` for cross-subdomain sharing. `trigger === "update"` branch supports account-switch (updates `active_account`, `active_account_name`, `is_admin`, etc.). No credentials/OAuth providers registered here — counter-intuitive but intentional.

**`pages/_app.tsx` iframe bridge.** Bidirectional URL sync with parent via `postMessage`. Monkey-patches push/replaceState, intercepts popstate/hashchange, uses MutationObserver + 2-second interval fallback for edge cases. `PARENT_NAVIGATION_CHANGE` with `source === "popstate"` uses `replaceState` to avoid double-stacking history entries.

**Metadata-driven forms.** `metadata/Job.json` + `metadata/job_details.json` + `metadata/admin.json` declare field order, sections, roles, and form layouts. `FormSectionsRenderer.tsx` + `FormFieldRenderer.tsx` interpret these files and render forms at runtime. These files also carry env-specific values: `account_id` and `app_url` differ between QA and Prod (see Deployment § pitfalls). Every metadata deploy requires a manual CosmosDB paste step.

**`NetSuiteSyncContext` — single React Context for NetSuite sync.** Owns `isNetSuiteSyncing` + `isNetsuiteSyncEnabled`. `syncFlightWithNetSuite(accountId, flightId, onSuccess, onFailure)` POSTs to `/api/netsuite/sync/syncpo`, shows a Mantine modal during sync, routes to error or success modal on completion. Gated globally by `F92_NETSUITE_SYNC_ENABLED=true` (queried once at mount via `/api/netsuite/sync/enabled`). See [[dax-media-app]] § NetSuite PO Sync for the business rules.

**Flight Check application-type constants** (`components/nonHTMLcomponents/constants.tsx`). Two magic UUIDs: `FLIGHT_CHECK_APPLICATION_TYPE_FLIGHT = 9b9a62ab-...` and `FLIGHT_CHECK_APPLICATION_TYPE_JOB = 127edb5c-...`. Hard-coded `FUSION_92_ACCOUNT_IDS = ["0fc00e34", "f49f9aa3"]` + `FUSION_92_DATASET_ID`. Values cross-referenced in `metadata/Job.json:9` and `metadata/admin.json:59–62`.

**`FlightMetricsTable` + `processTableDataForDisplay`** (`lib/dax/metricsTable.ts`) — pacing grid. Handles four calculation sources: `dax` (daily, backend-derived), `smartsheet` (monthly, legacy, capped at `LAST_SMARTSHEET_YEAR`), `direct` (daily, UI aggregates to month), `manual_mixed` (user-entered). `filterAndSortTableData()` filters by date overlap, sorts by start date. `groupDailyTableDataByMonth()` aggregates daily rows into `year-month` buckets — only when `tableSource === "direct"`.

**PostHog init at module scope** (`components/PostHogProvider.tsx:7–25`). Fires before `PostHogProviderWrapper` mounts. User identified via `posthog.identify(user.id, {...})` when session resolves; re-identified on account-switch via `posthog.capture("$set", …)`. Config: `capture_pageview: false` (manual), `capture_pageleave: true`, `autocapture: true`.

### API surface — frontend → internal routes → upstream

| Internal route | Upstream | Credential env var |
|---|---|---|
| `POST /api/coreAPI` | `${api_url}` (core_api) | `api_token` |
| `POST /api/core/notificationCreate` | core_api `notification/create/` | via `api_token` |
| `POST /api/core/notificationUpdate` | core_api `notification/update/` | via `api_token` |
| `POST /api/core/sendWelcomeEmail` | core_api `portal/newuseremail/` (session-gated via `getServerSession`) | via `api_token` |
| `GET /api/dax/flights/[flight_id]?add-calc=true` | `${DAX_API_URL}/flights/{id}` | `DAX_API_MASTER_TOKEN` (`x-functions-key`) |
| `GET /api/dax/jobs/[job_id]?add-calc=true` | `${DAX_API_URL}/jobs/{id}` | `DAX_API_MASTER_TOKEN` |
| `GET /api/dax/jobs/[job_id]/export?type=&orientation=&flight_ids=` | `${DAX_API_URL}/jobs/{id}/export` | `DAX_API_MASTER_TOKEN` |
| `POST /api/dax/jobs/export` | `${DAX_API_URL}/jobs/export` | `DAX_API_MASTER_TOKEN` |
| `POST /api/dax/calculations` | `${DAX_API_URL}/calculations` | `DAX_API_MASTER_TOKEN` |
| `GET /api/netsuite/publishers?account_id=` | `${F92_NETSUITE_WORKFLOW_URL}/api/f92_netsuite_publishers` | `F92_NETSUITE_PUBLISHERS_TOKEN` (`x-functions-key`) |
| `GET /api/netsuite/sync/enabled` | (none — reads `F92_NETSUITE_SYNC_ENABLED` env only) | n/a |
| `POST /api/netsuite/sync/syncpo` | `${F92_NETSUITE_WORKFLOW_URL}/api/f92_netsuite_po_sync` | `F92_NETSUITE_SYNC_TOKEN` (`x-functions-key`) |
| `POST /api/dios/audience/process` | `${DIOS_API_URL}/audience/process` | `DIOS_API_KEY` (`x-auth-apikey`) |
| `GET /api/dios/projects/[projectName]/audiences` | `${DIOS_API_URL}/projects/{name}/audiences` | `DIOS_API_KEY` |
| `GET/POST /api/auth/[...nextauth]` | NextAuth (empty providers) | `NEXTAUTH_SECRET`, `NEXTAUTH_URL` |

### Design decisions worth calling out

- **Embedded-iframe architecture.** The app does not stand alone; it expects a parent window that issues the NextAuth cookie and handles `postMessage` navigation events. Opening the raw URL in a fresh browser without a session redirects to the parent Eclipse portal login.
- **Fork-of-eclipse.** Shares components and cookie/session plumbing with [[entities/repos/eclipse|eclipse]]. Same proxy pattern, same session claims, same admin screens. Not a monorepo — pure duplication. Fixes to shared-looking components may need to land in both repos.
- **Metadata-driven forms.** Form structure is config in `metadata/*.json`, not React code. Lets Fusion92 add/remove field options without a deploy (within `options`/`options_inactive`). Env-specific values embedded in the same files create a manual deploy hazard (see Deployment).
- **Four-backend fan-out.** core_api, DAX API, DIOS, NetSuite Workflow — all different auth schemes (`Authorization` bearer vs `x-functions-key` vs `x-auth-apikey`). No unified retry/circuit-breaker.
- **Standalone Next.js build.** `output: "standalone"` in `next.config.mjs`. Build script copies `.next/static` + `public/` into `.next/standalone/` (`package.json:build`). Matches the Azure Web App deploy target.
- **Hard-coded PostHog key.** `components/PostHogProvider.tsx:8`. PostHog project keys are designed to be public (not a secret), but should move to env var for consistency; env vars already exist in `.env.template` but are shadowed.

---

## Data Flow

### Data inputs — where job/flight data originates

- **Jobs, flights, application metadata** — [[core_api]] / [[CosmosDB]]. Read via `/api/coreAPI` → `application/list`, `application/read`, `application/heirarchy` [sic], `application/readmetadata`.
- **Flight calculations (pacing, actuals, metrics table)** — **DAX API** (Azure Functions backend, `DAX_API_URL`; no wiki page yet — gap). Fetched via `/api/dax/calculations` (POST) or `add-calc=true` query params on jobs/flights endpoints. Returns `FlightCalculations` shape (`lib/dax/types.ts`).
- **NetSuite publisher names** — F92's NetSuite Workflow app via `/api/netsuite/publishers?account_id=…` (drives "Publisher Name" dropdown on Direct Partner flights).
- **DIOS audiences** — DIOS via `/api/dios/projects/[projectName]/audiences` (drives "DIOS Audience Name" dropdown).
- **Notifications** — core_api `notification/read/list` via session-authenticated routes.
- **User/account/RBAC** — core_api via `/api/coreAPI`.
- **Session** — NextAuth session cookie issued by the parent Eclipse portal, shared via `__Secure-next-auth.session-token` at domain `.eclipse.aldc.io`.

### Data outputs — where user actions go

- **Job/flight create/update/delete** — back to core_api via `/api/coreAPI` → `application/create|update|delete`.
- **NetSuite PO sync** — `/api/netsuite/sync/syncpo` triggers F92's workflow, which creates/updates the PO in NetSuite. Prerequisites: flight in correct status; `F92_NETSUITE_SYNC_ENABLED=true`. See [[dax-media-app]] § NetSuite PO Sync for the full business flow.
- **DIOS audience processing** — `/api/dios/audience/process` forwards the raw body directly to DIOS (no transformation in this app).
- **Notification settings** — `/api/core/notificationCreate` + `/api/core/notificationUpdate` → core_api → [[CosmosDB]].
- **Welcome email on new user** — `/api/core/sendWelcomeEmail` → core_api `portal/newuseremail/` (session-gated via `getServerSession`).
- **Analytics** — PostHog (`posthog-js`) direct from browser to `https://us.i.posthog.com/`.

### Transformations inside this app

- **Calculation load** — `lib/dax/flights.ts:loadFlightCalculationData()` normalises DAX API response: coerces string dates to `LocalDate` (js-joda), fills missing values with typed zeros, **multiplies `pacing` by 100** (backend ships a proportion; UI treats as percent — `flights.ts:62`). A TODO comment flags this should be backend-normalised.
- **Job load** — `lib/dax/jobs.ts:loadJobDataApiResponse()` converts `created` string → `Date`.
- **Metrics-table display pipeline** — `processTableDataForDisplay()` in `lib/dax/metricsTable.ts`:
  1. `filterAndSortTableData()` — filter by date range (keep rows that *overlap* the filter dates), sort by start date.
  2. `groupDailyTableDataByMonth()` — **only when `tableSource === "direct"`** — aggregates daily rows into `year-month` buckets (`dax`/`smartsheet`/`manual_mixed` rows are left at their native grain).
- **List formatters** — `F92JobListFormat` / `F92FlightListFormat` in `components/nonHTMLcomponents/ApplicationDataCleanup.tsx` prepare server rows for `F92DataTable` (pacing colour coding, status chiclets, action buttons).
- **NaN-stripping in the core_api proxy** — `pages/api/coreAPI.tsx:29–35` rewrites raw `NaN` tokens in the response text to `null` before `JSON.parse`. Band-aid for non-RFC JSON shipped by [[core_api]].

### Storage in this app

- **No durable storage.** All data lives upstream.
- **Cookies:** NextAuth session cookie (`__Secure-next-auth.session-token` on HTTPS / `next-auth.session-token` on HTTP) + NextAuth CSRF + callback-url cookies.
- **LocalStorage:** Mantine color-scheme preference (via MantineProvider); `ThemeWrapper` syncs to `cookies-next`.
- **In-memory only:** All page state. No React Query, no SWR.

### Audit + observability

- **F92 audit trail download** — `components/Fusion92/DownloadAuditTrail.tsx` exports a CSV/Excel from core_api records.
- **PostHog** — `$pageview` on route change, `posthog.identify(user.id, …)` on session resolve, `posthog.capture("$set", …)` on account switch. No backend spans.
- **No structured logs.** API routes use `console.error` only. No correlation IDs, no Application Insights integration.

---

## Developer Guide

### Prerequisites

- **Node.js 24.x** — pinned in Dockerfile, both GitHub workflows, and `package.json` dev script.
- **npm** — uses `npm ci` in workflow and Dockerfile.
- **Docker + Docker Compose** — optional; needed for image build or `compose_test.yaml` flow.
- **Backend credentials** — `api_token` (core_api), `DAX_API_MASTER_TOKEN`, `DIOS_API_KEY`, `F92_NETSUITE_*_TOKEN`. Vault pointers: `vault/credentials.md`.
- **A NextAuth session cookie** — most local dev relies on logging into the parent Eclipse portal on a same-domain subdomain and sharing the cookie. See cookie-domain pitfall below.

### Environment variables

Source of truth: `.env.template`. Populate as `.env.local` for dev or `compose_test.yaml` flows.

| Var | Purpose |
|---|---|
| `api_url` | Base URL for [[core_api]] (e.g. `https://aldcprodfnapcore1c01.azurewebsites.net/api/`) |
| `api_token` | Bearer token for core_api — sent as raw `Authorization: <token>` (not `Bearer <token>`; see `coreAPI.tsx:16`) |
| `STAC_NAME`, `STAC_KEY` | Legacy Azure Storage keys — no references in current source code; likely dead |
| `NEXTAUTH_URL` | Full URL of this app (e.g. `https://dax.fusion92.eclipse.aldc.io`) — drives cookie prefix (`__Secure-` only on HTTPS) and cookie domain |
| `NEXTAUTH_SECRET` | JWT signing secret — **must match the parent Eclipse portal** for session cookie interop |
| `F92_NOTIFICATION_KEY`, `F92_NOTIFICATION_URL` | F92 email notification service (used by `DaxMediaNotificationSettings`) |
| `F92_NETSUITE_SYNC_ENABLED` | `"true"`/`"false"` — read by `/api/netsuite/sync/enabled`; gates the NetSuite sync button globally |
| `F92_NETSUITE_WORKFLOW_URL` | Base URL for F92's NetSuite Workflow App |
| `F92_NETSUITE_SYNC_TOKEN` | `x-functions-key` for `/api/f92_netsuite_po_sync` |
| `F92_NETSUITE_PUBLISHERS_TOKEN` | `x-functions-key` for `/api/f92_netsuite_publishers` |
| `DIOS_API_URL`, `DIOS_API_KEY` | Points at [[custom-fusion-92-audience-api]] (DIOS); `DIOS_API_KEY` sent as `x-auth-apikey` |
| `DAX_API_URL`, `DAX_API_MASTER_TOKEN` | DAX API (Azure Functions backend); token sent as `x-functions-key` |
| `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST` | **Currently unused** — shadowed by the hard-coded value in `components/PostHogProvider.tsx:8–9` |
| `ECLIPSE_URL` | Referenced in `pages/api/core/sendWelcomeEmail.tsx:44` but **absent from `.env.template`** — gap; add before running locally |
| `CHILD_SRC_ALLOWED_ORIGINS` | Set at container level in `compose.yaml` (not in app code); passed to parent portal's CSP allow-list |

### Local setup — Option A: run against real backends

1. `git clone` + `cd flight-check`
2. `nvm use 24` (or install Node 24).
3. `npm install`
4. Copy `.env.template` → `.env.local`. Fill values from `vault/credentials.md`. Note: `ECLIPSE_URL` is missing from the template — add it manually.
5. Set `NEXTAUTH_URL` to a URL on the `*.eclipse.aldc.io` domain (or a local override that shares the cookie domain). If `NEXTAUTH_URL=http://localhost:3100`, the cookie domain becomes `.localhost` — most browsers reject this; session will resolve as null.
6. `npm run dev` — serves on **port 3100** (not 3000; that port is reserved for the parent Eclipse dev server).
7. Visit `http://localhost:3100`. Expect redirect to the parent portal login if no session cookie is present.

### Local setup — Option B: Docker Compose against prebuilt image

- `compose_test.yaml` pulls `ghcr.io/aldc-io/flight-check:${FLIGHT_CHECK_VERSION}` and binds `.env.local`. Use when you want to run the production image locally.
- `compose.yaml` is the production compose (requires GHCR access + `.env.production`).
- Command: `FLIGHT_CHECK_VERSION=<tag> docker compose -f compose_test.yaml up`
- App binds to host port 3000 (`compose_test`) or 3100 (`compose`).

### Local setup — Option C: build the Docker image from source

```bash
docker build -t flight-check:local .
```

Multi-stage Dockerfile: `builder` stage (Node 24 Alpine) installs deps + runs `next build`; final stage copies `.next/standalone` + static + public, runs as non-root `nextjs:nodejs` (UID/GID 1001). Note: **no healthcheck in the Dockerfile** (unlike `eclipse_exp`); Azure App Service probes the default `/`.

### Running tests and lint

```bash
npm run lint          # ESLint --fix --max-warnings=0
npm run lint:check    # same without fix (runs in PR_checks.yaml)
npm run format        # Prettier (write)
npm run format:check  # Prettier (check only, runs in PR_checks.yaml)
npm test              # Jest (one trivial test — effectively nothing to run)
npm run test:watch    # Jest watch
```

Pre-commit hook runs `lint-staged`: ESLint fix on `.{js,jsx,ts,tsx}` + Prettier on `.{js,jsx,ts,tsx,css,md,html,json}`.

### Debugging

- **Browser console** — PostHog calls `posthog.debug()` on `NODE_ENV === "development"` (`PostHogProvider.tsx:22`).
- **Session inspection** — visit `/api/auth/session` to see the JWT claims for the current cookie.
- **Proxy-response inspection** — the coreAPI/dax/dios/netsuite handlers all `console.error` failures to server logs; watch the `npm run dev` terminal.
- **Metadata-form issues** — check `metadata/Job.json` / `job_details.json` for the field definition. A QA `account_id` mismatch manifests as forms binding to the wrong account.
- **PostMessage bridge** — use Browser DevTools → Application → Frames to inspect iframe context; add `console.log` around `handleMessage` in `_app.tsx` to trace navigation sync.

### Common pitfalls

- **Dev port is 3100**, not 3000. Don't override — 3000 is used by the parent Eclipse dev server.
- **Empty NextAuth providers.** You cannot log in from this app directly. The session must come from the parent Eclipse portal. For isolated local dev you'd have to mint a JWT manually and set the cookie.
- **Cookie domain constraint.** `NEXTAUTH_URL` hostname controls `cookies.sessionToken.options.domain`. Setting `NEXTAUTH_URL=http://localhost:3100` makes the domain `.localhost` — browsers reject this; session resolves as null.
- **Metadata env swap.** `metadata/Job.json` + `job_details.json` + `admin.json` carry Prod-only `account_id` (`0fc00e34`) and Prod-only `app_url` (`dax.fusion92.eclipse.aldc.io`). Running these against QA binds forms to the wrong Fusion account. Per `metadata/README.MD`, swap `account_id` to the QA value and flip `app_url` to the `.com` QA domain before pasting into QA CosmosDB.
- **NaN in API responses.** `coreAPI.tsx` silently scrubs `NaN` → `null` before parse. If you're debugging "why is X null", check the raw upstream response first.
- **Hard-coded PostHog key** fires in all environments including local dev. Events from `localhost` land in the production PostHog project. Consider stubbing `PostHogProvider.tsx` for local work.
- **Four UI libraries coexist.** When editing a button or modal, check whether it's Mantine, NextUI, flowbite, or headlessui — each has different props and theming.
- **Three date libraries coexist.** `lib/dax/types.ts` uses `LocalDate` (js-joda); `metricsTable.ts` mixes them; many components still use `dayjs`. Be careful converting between formats.
- **`[...slug].tsx` is ~25 k lines.** The main dynamic-route handler for the whole app. Don't attempt a full refactor in a single PR.
- **`package.json` name is `"eclipse"`.** npm run log lines will say `eclipse`. This is a fork-scaffold leftover — ignore it.

---

## Deployment

### Infra at a glance

| Thing | Value | Source |
|---|---|---|
| Production URL | `https://dax.fusion92.eclipse.aldc.io` | `metadata/Job.json:8`, `metadata/README.MD:41` |
| QA URL | `https://dax.fusion92.eclipse.aldc-ca-w1.com` (**`.com`**, not `.io`) | `metadata/README.MD:42` |
| Deploy target | Azure Web App, staging slot | `deploy_az_webapp.yaml:48` |
| App Service name | Per-env `vars.AZURE_APP_SERVICE_NAME` | `deploy_az_webapp.yaml:46` |
| Azure auth | OIDC federated (`azure/login@v2`) | `deploy_az_webapp.yaml:28–31` |
| Container image (compose path) | `ghcr.io/aldc-io/flight-check:${FLIGHT_CHECK_VERSION}` | `compose.yaml:3` |
| Base image | `node:24-alpine` (multi-stage) | `Dockerfile:3` |
| Parent CSP allow-list | `CHILD_SRC_ALLOWED_ORIGINS=flight-check.eclipse.aldc.io` | `compose.yaml:16` |
| Container user | `nextjs:nodejs` (UID/GID 1001) non-root | `Dockerfile:31–33` |
| CSP `child-src` set by | *Parent* Eclipse portal middleware, not this app | cross-ref [[entities/repos/eclipse\|eclipse]] |

### Environment model

| Environment | URL | Notes |
|---|---|---|
| Prod | `dax.fusion92.eclipse.aldc.io` | `.io` TLD |
| QA | `dax.fusion92.eclipse.aldc-ca-w1.com` | `.com` TLD — different suffix; source of confusion. Rename target. |
| Local | `localhost:3100` via `npm run dev`, or prebuilt image via `compose_test.yaml` | Session cookie constraint — see Developer Guide |

No separate "dev" environment beyond developer laptops.

### CI — PR checks

Reference: `.github/workflows/PR_checks.yaml`. Triggered on `pull_request.synchronize` (**not** `opened` — first push of a new PR skips the check; this is a known oversight).

1. Checkout.
2. Setup Node 24.
3. `npm install`.
4. `npm audit --omit=dev` (runtime deps only).
5. `npm run lint:check` (`--max-warnings=0`, hard fail).
6. `npm run format:check` (Prettier).

No test gate (no real tests). No standalone `tsc --noEmit` gate (type-checking runs implicitly via `next build` during deploy).

### CD — manual Azure Web App deploy

Reference: `.github/workflows/deploy_az_webapp.yaml`. Triggered by `workflow_dispatch` with environment input.

1. Checkout.
2. Azure login via OIDC (`client-id`, `tenant-id`, `subscription-id` from secrets).
3. Setup Node 24.
4. `npm install && npm run build` — `next build` + copies `.next/static` into `.next/standalone/.next/` + copies `public/` into `.next/standalone/`.
5. `azure/webapps-deploy@v3` with `package: ./.next/standalone`, `slot-name: stage`.
6. `az logout`.

**Staging-slot model** — deploys land on `stage` slot. A manual slot swap in the Azure Portal promotes to production. Follows the same pattern as [[eclipse-azure-deployment]].

### GHCR image path (alternate deploy route)

`compose.yaml` references `ghcr.io/aldc-io/flight-check:${FLIGHT_CHECK_VERSION}`, but `deploy_az_webapp.yaml` deploys the standalone bundle directly — it does **not** push to GHCR. The GHCR route is likely used for Docker-on-VM / Portainer deployments (per [[connector-docker-deployment]] pattern) or is a residual from an older deploy model. **Gap: no image-publish step is visible in `.github/workflows/` on `main`.** Verify with Vlad.

### Deploy steps — end-to-end

1. Merge PR into `main`.
2. GitHub UI → Actions → "Deploy to Azure App Service" → Run workflow → pick environment (prod/QA).
3. Wait for workflow to complete (build + deploy to `stage` slot).
4. Smoke-test the staged app (direct URL to the staging slot — not canonically documented; verify with Vlad).
5. Azure Portal → App Service → Deployment slots → Swap staging ↔ production.
6. **If the deploy touches `metadata/*.json`** (form structure, fields, admin layout), additionally:
   - Compare `options` / `options_inactive` between QA and Prod — keep them in parity.
   - **Update `account_id`** to the target env's Fusion account ID (differs between ALDC QA and Prod).
   - **Update `app_url`** to the target env's URL (`.io` for Prod, `.com` for QA).
   - Paste the updated JSON into the metadata container of the target CosmosDB via Cosmos Data Explorer.

### Rollback

- **Azure Web App** — swap staging ↔ production again to return the previous revision. Same pattern as [[eclipse-azure-deployment]].
- **Metadata** — CosmosDB containers don't maintain history. A rollback requires pasting the previous JSON manually. Mitigation: commit JSON changes to the repo *before* pasting into CosmosDB so git history acts as the rollback source.
- **No DB migrations** to unwind — this app has no database.

### Secrets storage

- **GitHub Actions:** `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` (OIDC).
- **Azure App Service env vars:** `api_token`, `DAX_API_MASTER_TOKEN`, `DIOS_API_KEY`, `F92_NETSUITE_*_TOKEN`, `NEXTAUTH_SECRET` set directly in the App Service configuration panel.
- Canonical vault pointer: [[vault/credentials]].

### Observability in prod

- **PostHog** — pageviews, autocapture, user identification. Dashboard owned by Karen Prete (see [[dax-media-app]]).
- **Azure App Service logs** — accessible in the Azure Portal. No Application Insights or Log Analytics Workspace integration.
- **No healthcheck endpoint** — no `/health` or `/ping`; Azure App Service probes `/`.
- **No structured logs** — API routes use `console.error` only.

---

## Integrations

| System | Direction | Internal route / mechanism | Auth | Wiki page |
|---|---|---|---|---|
| [[core_api]] | in/out | `POST /api/coreAPI` proxy → `${api_url}{url}` | `api_token` (raw `Authorization` header) | [[core_api]] |
| DAX API (Azure Functions) | in/out | `/api/dax/*` → `${DAX_API_URL}/*` | `x-functions-key: DAX_API_MASTER_TOKEN` | TODO: create wiki page |
| [[custom-fusion-92-audience-api]] (DIOS) | out | `/api/dios/*` → `${DIOS_API_URL}/*` | `x-auth-apikey: DIOS_API_KEY` | [[custom-fusion-92-audience-api]] |
| F92 NetSuite Workflow | out | `/api/netsuite/*` → `${F92_NETSUITE_WORKFLOW_URL}/api/*` | `x-functions-key: F92_NETSUITE_*_TOKEN` | TODO: verify hosting (Azure vs on-prem at Fusion92) |
| [[entities/repos/eclipse\|eclipse portal]] | in | `postMessage` bridge (`_app.tsx:44–204`) + shared session cookie | `__Secure-next-auth.session-token`, domain `.eclipse.aldc.io` | [[entities/repos/eclipse\|eclipse]] |
| PostHog | out | Browser-direct to `https://us.i.posthog.com/` | Hard-coded project key (public by design) | No wiki page yet |
| [[CosmosDB]] (indirect via core_api) | in/out | Via core_api only — jobs, flights, users, notifications, metadata | Via `api_token` | [[CosmosDB]] |
| F92 email notifications | out | `DaxMediaNotificationSettings` → `F92_NOTIFICATION_URL` | `F92_NOTIFICATION_KEY` | Gap — endpoint not documented |

---

## Known Issues / Tech Debt

- **`package.json` `name: "eclipse"`** — fork-scaffold leftover; rename to `"flight-check"`.
- **Hard-coded PostHog key** in `components/PostHogProvider.tsx:8`. PostHog project keys are public by design, but the env vars (`NEXT_PUBLIC_POSTHOG_KEY`) are already declared in `.env.template` — should use them for env parity.
- **NaN-scrubbing band-aid** in `coreAPI.tsx:29–35` — proper fix belongs in [[core_api]]'s response serialisation, not in the frontend proxy.
- **Four UI kits coexist** — Mantine 7 + NextUI 2 + flowbite-react + headlessui. Consolidation in progress toward Mantine; no target date.
- **Three date libraries coexist** — `@js-joda/core`, `date-fns`, `dayjs`. Consolidation target is js-joda (already used in types.ts and flights.ts).
- **One trivial test file** — `__test__/index.test.js` is a placeholder `expect(true).toBe(true)`. Zero meaningful test coverage. No Playwright/Cypress/Storybook.
- **`pacing * 100` hack** in `lib/dax/flights.ts:62` — backend returns a proportion; UI multiplies by 100 to get a percentage. A TODO comment exists; fix belongs in the DAX API backend.
- **Metadata env-swap is manual** — `account_id` and `app_url` in `metadata/*.json` differ between QA and Prod; no automation. Candidate for Cosmos-managed env-tagged records.
- **`ECLIPSE_URL` env var** — referenced in `pages/api/core/sendWelcomeEmail.tsx:44` but missing from `.env.template`. Must be added manually to `.env.local`.
- **`STAC_NAME` + `STAC_KEY` in `.env.template`** — no references found in current source code; likely dead variables.
- **`PR_checks.yaml` triggers on `synchronize` only** — opening a new PR without pushing additional commits skips the CI check.
- **No healthcheck endpoint** — no `/health` or `/ping`; Azure App Service probes `/`.
- **No Application Insights / Log Analytics integration** — server-side errors are `console.error` only.
- **File size:** `[...slug].tsx` ~25 k lines, `ApplicationTable.tsx` ~99 k, `AccountForm.tsx` ~106 k, `F92DataTable.tsx` ~40 k — all refactor candidates but high blast radius.
- **QA URL uses `.com` TLD** (`eclipse.aldc-ca-w1.com`) while production uses `.io` (`eclipse.aldc.io`) — a persistent source of confusion. Rename target.
- **GHCR image-publish step not visible in workflows** — the `compose.yaml` references a GHCR image but no `.github/workflow` builds and pushes it on `main`. Verify whether this is a dead path or an undocumented manual step.

---

## See Also

- [[dax-media-app]] — the product this repo implements. Defer product scope, roles, UAT history, NetSuite sync business rules, and Phase 2/PRJ537 to that page.
- [[entities/repos/eclipse|eclipse (repo)]] — the host portal this app iframes into; shares NextAuth session cookie, admin UI components, and the coreAPI proxy pattern.
- [[core_api]] — primary backend; every `/api/coreAPI` + `/api/core/*` call routes through it.
- [[custom-fusion-92-audience-api]] — the DIOS API this app proxies to for audience data.
- [[fusion92]] — the client.
- [[fusion92-platform-ids]] — platform ID mapping used by Flight Check data matching.
- [[fusion92-data-architecture]] — upstream Snowflake setup for Fusion92.
- [[flight-check]] (`processes/operations/`) — **NOT this repo** — ALDC's operational data-pipeline validation runbook. Same name, completely different thing.
- [[eclipse-azure-deployment]] — the staging-slot deploy pattern this repo follows.
- [[GitHub Actions]] — CI/CD pattern reference.
- [[azure-environments]] — Azure subscription → environment mapping.
- [[Eclipse]] — the broader Eclipse platform concept.
- [[CosmosDB]] — indirect storage for metadata, jobs, flights (via core_api).
