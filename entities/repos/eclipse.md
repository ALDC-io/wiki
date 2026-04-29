---
tags: [entity, repo, eclipse, nextjs, react, frontend, ui]
aliases: [Eclipse UI, Eclipse portal, eclipse repo, Eclipse Next.js]
sources: [repos/eclipse/README.md, repos/eclipse/package.json, repos/eclipse/authOptions.ts, repos/eclipse/middleware.ts, repos/eclipse/next.config.mjs, repos/eclipse/Dockerfile, repos/eclipse/compose.yaml, repos/eclipse/compose_test.yaml, repos/eclipse/.env.template, repos/eclipse/pages/api/coreAPI.tsx, repos/eclipse/.github/workflows/ci.yml, repos/eclipse/.github/workflows/PR_checks.yaml, repos/eclipse/.github/workflows/deploy_az_webapp.yaml, repos/eclipse/.github/workflows/quality-gate.yml]
created: 2026-04-20
updated: 2026-04-29
---

# Eclipse (repo)

> **Disambiguation:** This page covers the `eclipse` Next.js UI repo specifically. The broader [[Eclipse]] platform concept (connections, templates, tasks, connector standards) lives at `entities/tools/eclipse.md`. The next-gen successor is [[eclipse_exp]] (FastAPI + Next.js 15 + Postgres, running at `eclipse-exp.aldc.io`). For the deploy runbook see [[eclipse-azure-deployment]].
>
> **⚠ Page staleness (flagged 2026-04-21):** The detail below describes the **legacy Next 14 Pages Router** version of the repo, still served at **`https://eclipse.aldc.io`** via Azure App Service `aldcprodwbapportal1c01`. The repo on disk has since been **rewritten to Next 15 App Router** (branch `eclipse-2.1`); the current production product runs at **`https://eclipse.analyticlabs.io/`** (Azure App Service `aldcprodwbapeclipse1c01`, Production 2 / DG1 — see [[deployment-groups]]). The Azure default URL `https://aldcprodwbapeclipse1c01.azurewebsites.net/` is reachable but CORS-blocked for auth because prod core_api only allowlists the `.analyticlabs.io` origin. The two deployments run in **parallel on different brand domains** (`aldc.io` vs `analyticlabs.io`) — not a DNS cutover of the same hostname. A full refresh of this page is tracked in [[action-items]].

The `eclipse` repo is the legacy **Next.js 14 (Pages Router) frontend portal** for the Eclipse platform — the user-facing web app covering login, account management, connection/template configuration, application-hosting iframes, and data-model dashboards. Every data or control operation proxies server-side through `pages/api/coreAPI.tsx` to [[core_api]] (Azure Functions backend); the repo itself holds no business logic and no database. Data movement is handled by the separate [[connector]] repo. The app is deployed at `eclipse.aldc.io` (production) with per-env subdomains (e.g. `eclipse2-test.aldc.io`). It is the **legacy** UI being replaced by [[eclipse_exp]] via a strangler-fig migration — new tenants go to eclipse_exp; existing tenants stay here.

---

## Architecture

### Repository layout

| Path | Purpose |
|---|---|
| `pages/` | All routes (Pages Router). 34 files total. |
| `pages/api/coreAPI.tsx` | **The** universal proxy — every client-side data call goes here |
| `pages/api/auth/[...nextauth].tsx` | NextAuth entry point |
| `pages/api/core/` | F92 notification wrappers (`notificationCreate`, `notificationUpdate`) |
| `pages/api/dios/` | DIOS audience API (`process`, `projects/[name]/audiences`) |
| `pages/api/netsuite/sync/` | NetSuite PO sync (`syncpo`, `enabled`) |
| `pages/application/[...slug].tsx` | Iframe app loader (Flight Check, etc.) |
| `pages/connections/`, `pages/templates/` | Connection + template CRUD |
| `pages/dashboards/` | Dashboard authoring + viewer |
| `pages/manage_accounts/`, `pages/manage_team/` | Admin screens |
| `pages/data_dictionary/` | Data dictionary viewer + relationships |
| `components/` | ~71 React components |
| `components/dashboard/` | Widget system: `Workspace`, `Dashboard`, `LayoutTree`, `Widget`, `WidgetEditorPane`, `TableWidget`, `FilterForm`, `fetchDatasetData` |
| `components/Fusion92/` | F92-only: `POModal`, `ProcessAudienceFilesButton`, `SubmitFlightButton` |
| `components/nonHTMLcomponents/` | Utility: `F92Theme`, `UserAccountGroupAPI`, `Condition`, `StringFormatting` |
| `authOptions.ts` | NextAuth config (credentials provider delegating to `user/login`) |
| `middleware.ts` | Next.js edge middleware: `withAuth` gate + CSP injection |
| `next.config.mjs` | `reactStrictMode: true`, `output: "standalone"` |
| `styles/globals.scss` | Global SCSS |
| `tailwind.config.ts` + `postcss.config.js` | Tailwind + `postcss-preset-mantine` |
| `public/` | Static assets including F92 branding |
| `types/next-auth.d.tsx` | NextAuth session/JWT type augmentation for ALDC fields |
| `__test__/` + `__mock__/` | Jest tests (one file) + static-asset mocks |
| `Dockerfile`, `compose.yaml`, `compose_test.yaml` | Container build + runtime |
| `.github/workflows/` | 7 CI/CD workflows (see Deployment) |
| `.husky/` | Pre-commit lint-staged hook |

### Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | Next.js 14.2 — Pages Router, **not** App Router | `next: ^14.2.23`; contrast with [[eclipse_exp]] which uses Next 15 App Router |
| Runtime | Node 18 (Dockerfile) / Node 20 (PR_checks + deploy) / Node 22 (quality-gate CI) | **Mismatch** — recommend Node 20 for local parity with PR_checks |
| Auth | NextAuth 4 (`next-auth: ^4.24.7`) — credentials provider | Delegates email/password to `user/login` via coreAPI proxy |
| UI | Mantine 7 (`@mantine/core`, `carousel`, `hooks`, `modals`, `notifications`) + NextUI 2 | Two competing primary UI kits coexist — older screens use NextUI, newer use Mantine |
| Styling | Tailwind 3.4 + SCSS + `postcss-preset-mantine` | |
| HTTP | `axios`, `fetch` | Most pages use `fetch("/api/coreAPI", …)` |
| State | React local state + provider stack (SessionProvider, NextUIProvider, MantineProvider) | No Redux/Zustand/React Query |
| Cookies | `cookies-next` | `display_mode` drives light/dark theme |
| CSV | `papaparse` | Connection/template config imports |
| Testing | Jest 29 + `@testing-library/react 16` + `jest-environment-jsdom` | **One test file** exists (`__test__/index.test.js`) |
| Lint/format | ESLint 8 + `eslint-config-next` + `@typescript-eslint` + Prettier 3 | `lint:check` uses `--max-warnings=0` |
| Pre-commit | Husky 9 + lint-staged 15 | ESLint fix + Prettier on staged files |
| TypeScript | `typescript: ^5`, `strict: true`, path alias `@/* → ./*` | |

### How a request flows

1. Browser navigates to a page (e.g. `/dashboards`). `middleware.ts` intercepts all routes except `api/*`, `_next/*`, `login`, `password_reset` (matcher config).
2. `withAuth` checks for a NextAuth JWT session cookie. Unauthenticated requests redirect to `/login` (defined in `authOptions.pages.signIn`).
3. Middleware sets `Content-Security-Policy: child-src 'self' ${CHILD_SRC_ALLOWED_ORIGINS}` on every page response — gates iframe embeds.
4. `_app.tsx` wraps the page with `SessionProvider` → `MantineProvider` (custom `eclipseBlue` palette, primaryShade 9) → `ModalsProvider` → `NextUIProvider`, plus `Nav` + `Sidebar` + `BreadCrumb` chrome. Login + password_reset paths skip the chrome.
5. Pages call `fetch("/api/coreAPI", { method: "POST", body: JSON.stringify({ url, message }) })` for all data needs.
6. `pages/api/coreAPI.tsx` adds `Authorization: ${api_token}` header, forwards the POST to `${api_url}${url}`, unwraps the `{response: {code, payload}}` envelope, returns `{response, status, message, http_code}`.
7. Specialised routes (`/api/core/*`, `/api/dios/*`, `/api/netsuite/*`) follow the same proxy pattern but use F92-specific env vars.

### Key abstractions

**`pages/api/coreAPI.tsx` — the universal proxy.** Every client-side data call in the app funnels through this one server-side handler. It reads `api_url` + `api_token` from env, POSTs to `${api_url}${url}`, checks `response.code === 200`, and returns a normalised `ResponseData = { response, status, message, http_code }`. It is also exported as `apiCall()` so other server-side API routes can reuse it. Single most important file in the repo.

**`authOptions.ts` — NextAuth credentials provider.** `authorize()` POSTs email/password to `${NEXTAUTH_URL}/api/coreAPI` → `user/login`, then stores the result as JWT claims: `first_name`, `last_name`, `email`, `active_account`, `active_account_name`, `id`, `is_internal`, `is_admin`, `applications`, `groups`, `date_joined`, `home_page`. JWT strategy. Cookie prefix is `__Secure-` on HTTPS, empty on HTTP; domain derived from `NEXTAUTH_URL` hostname. The `trigger === "update"` branch rewrites `active_account` / `active_account_name` for account-switching, plus `is_admin`, name, and `home_page`.

**`middleware.ts` — auth gate + CSP injection.** Wraps `withAuth`; sets `child-src` CSP on every page response. Matcher excludes `api/*`, Next internals, `login`, `password_reset`.

**`pages/application/[...slug].tsx` — iframe app loader.** Resolves app name from slug, calls `application/readmetadata`, sets iframe `src` to the registered app URL. Listens for `NAVIGATION_CHANGE` postMessage events from the child app to sync the parent URL. This is how [[dax-media-app]] / Flight Check embeds inside the portal. `CHILD_SRC_ALLOWED_ORIGINS` (space-separated) must whitelist the child origin.

**`components/dashboard/` — widget/dashboard authoring primitives.** `Workspace`, `Dashboard`, `LayoutTree`, `Widget`, `WidgetContainer`, `WidgetEditorPane`, `WidgetDrawerPane`, `TableWidget`, `TableWidgetForm`, `FilterForm`, `fetchDatasetData`, `ConfigProviders`. Powers `/dashboards/index.tsx`. Datasets loaded via `dataset/list` + `dataset/describe`.

**NextAuth session type extension (`types/next-auth.d.tsx`).** Augments `Session`/`JWT` interfaces with ALDC-specific fields so TS callsites see `session.user.active_account`, etc.

### API surface (frontend → backend)

All calls go through `fetch("/api/coreAPI", { url, message })` → [[core_api]] Azure Functions. Known endpoint categories:

| Category | Examples |
|---|---|
| Auth | `user/login`, `user/passwordreset` |
| Account | `account/describe`, `account/list`, `account/encode` |
| Connections | `connection/list`, `connection/read`, `connection/write` |
| Templates | `template/list`, `template/read`, `template/write` |
| Applications | `application/readmetadata`, `application/heirarchy` (legacy typo in core_api) |
| Datasets | `dataset/list`, `dataset/describe` |
| Notifications | `notification/create`, `notification/update` (via F92 wrappers) |
| Users | `user/*` (team management, profile) |

### Design decisions worth calling out

- **Pages Router, not App Router.** [[eclipse_exp]] uses Next 15 App Router. Any "port a component over" effort must account for this architectural gap.
- **All data proxies through `/api/coreAPI` server-side** — keeps the bearer token (`api_token`) out of the browser; provides a uniform error envelope; avoids CORS entirely.
- **Applications embedded as iframes** — each has its own hosted URL registered via `readmetadata`. Navigation synced via `postMessage` `NAVIGATION_CHANGE`. CSP `child-src` gates allowed origins.
- **F92-specific routes in `pages/api/`** — hard-coded Fusion92 workflow URLs/tokens; dead code for non-F92 tenants. Tech debt pending decoupling.
- **Dual UI kits (Mantine 7 + NextUI 2)** — older components use NextUI; newer use Mantine. No clean cut-over.
- **Client-side rendering by default** — no `getServerSideProps`/`getStaticProps`. First paint is always empty + spinner.
- **No server state caching** — no React Query/SWR. Every page mount refetches.
- **Theme via cookie** — `display_mode` cookie is source of truth; React state shadows it.
- **`output: "standalone"`** — required for the Dockerfile's `.next/standalone` copy pattern (build script: `npm run build && cp -r .next/static .next/standalone/.next/ && cp -r public .next/standalone/`).

---

## Data Flow

This is a **UI repo, not a data pipeline** — data flow here means user interactions → backend API calls → rendered state, not ingestion/ETL.

### Overall shape

```
Browser
  └─ Next.js page component
       └─ fetch /api/coreAPI  (server-side, adds bearer token)
            └─ core_api (Azure Functions)
                 ├─ CosmosDB (Eclipse configs, user accounts)
                 ├─ Snowflake (warehouse data)
                 └─ Azure Storage (blobs)

Special legs:
  NextAuth login → /api/coreAPI → user/login → core_api
  /api/core/notification* → F92_NOTIFICATION_URL
  /api/dios/* → DIOS_API_URL
  /api/netsuite/sync/* → F92_NETSUITE_WORKFLOW_URL
```

### Auth data flow

1. Login form → NextAuth `signIn("credentials", { email, password })`
2. Server-side `authorize()` in `authOptions.ts` fetches `${NEXTAUTH_URL}/api/coreAPI` with `{ url: "user/login", message: { email, password } }`
3. `coreAPI.tsx` adds `Authorization: ${api_token}` and forwards to `${api_url}user/login`
4. core_api validates and returns user record
5. JWT callback populates token with ALDC fields; session callback exposes them to pages
6. Cookie: `__Secure-next-auth.session-token` (HTTPS) or `next-auth.session-token` (HTTP)

### Typical page data fetch

Mount → `useSession()` → page issues `fetch("/api/coreAPI", { method: "POST", body: JSON.stringify({ url, message }) })` → proxy adds bearer + forwards → unwraps `response.payload` → component state → render.

### Account-context switching

Sidebar/Nav reads `session.user.active_account`. Switch calls NextAuth `update({ active_account, active_account_name })`. The `trigger === "update"` branch in `authOptions.ts` rewrites those JWT claims without a re-login. Downstream pages see the new account context on the next `useSession()` call.

### Fusion92-specific flows

- **DIOS audience processing** — `POST /api/dios/audience/process` → `${DIOS_API_URL}/audience/process` with `x-auth-apikey: ${DIOS_API_KEY}`. Cross-reference [[custom-fusion-92-audience-api]].
- **DIOS project audiences** — `GET /api/dios/projects/[projectName]/audiences`.
- **NetSuite PO sync** — `POST /api/netsuite/sync/syncpo` → `${F92_NETSUITE_WORKFLOW_URL}` with `x-functions-key: ${F92_NETSUITE_SYNC_TOKEN}`. Called from `POModal` / `SubmitFlightButton`. See [[fusion92-platform-ids]] + [[dax-media-app]].
- **NetSuite sync enabled** — `GET /api/netsuite/sync/enabled` — returns `F92_NETSUITE_SYNC_ENABLED` flag.
- **F92 notification wrappers** — `notificationCreate` + `notificationUpdate` inject `F92_NOTIFICATION_URL` + `F92_NOTIFICATION_KEY` into the doc before forwarding to `notification/create` or `notification/update` on core_api.

### Application (iframe) loading flow

1. User navigates to `/application/flight-check`
2. `[...slug].tsx` calls `application/readmetadata` via coreAPI → gets app URL
3. Sets `<iframe src={app_url + reroutePath}>`
4. Child app posts `{ type: "NAVIGATION_CHANGE", path }` via `postMessage`
5. Parent handles the event: `router.push("/application" + path, undefined, { shallow: true })`
6. Origin check: `event.origin != appUrl` — silently no-ops mismatched origins; `CHILD_SRC_ALLOWED_ORIGINS` CSP must whitelist the child domain

---

## Developer Guide

### Prerequisites

- Node.js 20 (recommended for local parity with `PR_checks.yaml` CI; Dockerfile pins 18, `ci.yml` uses 22 — pick 20 to match the PR gate)
- npm
- A running [[core_api]] backend (local or remote) — see [[core-api-local-setup]] for the local runbook
- Access to `NEXTAUTH_SECRET` and a bearer `api_token` for the target environment

### Environment variables

Full list from `.env.template`:

| Variable | Purpose |
|---|---|
| `api_url` | [[core_api]] base URL (must end with `/`) |
| `api_token` | Bearer token for core_api requests |
| `NEXTAUTH_URL` | Public app URL (drives cookie prefix + domain) |
| `NEXTAUTH_SECRET` | Session encryption key |
| `STAC_NAME`, `STAC_KEY` | Azure Storage Account credentials |
| `F92_NOTIFICATION_KEY` | F92 notification API key |
| `F92_NOTIFICATION_URL` | F92 notification service URL |
| `F92_NETSUITE_SYNC_ENABLED` | Toggle NetSuite sync feature |
| `F92_NETSUITE_WORKFLOW_URL` | F92 NetSuite Logic App URL |
| `F92_NETSUITE_SYNC_TOKEN` | `x-functions-key` for NetSuite sync |
| `F92_NETSUITE_PUBLISHERS_TOKEN` | Additional NetSuite auth token |
| `DIOS_API_URL` | DIOS audience API URL |
| `DIOS_API_KEY` | DIOS API key (`x-auth-apikey` header) |
| `CHILD_SRC_ALLOWED_ORIGINS` | Space-separated list of domains allowed in `child-src` CSP (production: `flight-check.eclipse.aldc.io`) |

Env values per environment are in `vault/core-api-local-settings.md`.

### Local setup

```bash
git clone <eclipse repo>
cd eclipse
npm ci
# Create .env.local
cp .env.template .env.local
# Fill in: api_url, api_token, NEXTAUTH_URL=http://localhost:3000, NEXTAUTH_SECRET=<any 32+ char string>
# Start dev server
npm run dev
```

Open `http://localhost:3000`. Log in with a real ALDC user credential — the credentials provider delegates to core_api, so local core_api must be running (or point `api_url` at a remote QA environment).

### Running against a real core_api

Point `api_url` at the QA Function App endpoint from `vault/core-api-local-settings.md`, or at `http://localhost:7071/api/` for a local instance (see [[core-api-local-setup]]). Set `api_token` to the matching bearer token for that environment.

### Docker Compose

**Production-like:**
```bash
# Requires .env.production
docker compose -f compose.yaml up
```

**Test/local:**
```bash
# Requires .env.local
docker compose -f compose_test.yaml up
```

Both pull `ghcr.io/aldc-io/eclipse:${ECLIPSE_VERSION}`. Port: 3000.

### Running tests

```bash
npm test        # Jest + RTL, jsdom environment
npm test:watch  # Watch mode
```

**Important:** only one test file exists (`__test__/index.test.js`) — coverage is effectively zero. `__mock__/` provides `fileMock.js`, `nextFontMock.js`, `styleMock.js`. Mutation testing in CI won't fire until there are real tests under `src/**`.

### Linting and formatting

```bash
npm run lint          # ESLint fix (in-place)
npm run lint:check    # ESLint read-only (CI gate, --max-warnings=0)
npm run format        # Prettier write
npm run format:check  # Prettier check (CI gate)
```

Husky `pre-commit` runs lint-staged on staged files: ESLint fix on `.{js,ts,tsx}` + Prettier on `.{js,jsx,ts,tsx,css,md,html,json}`.

### Debugging

- **Next.js dev overlay + HMR** — instant feedback on frontend errors.
- **Server-side logs** — `coreAPI.tsx` logs errors with `console.error`; visible in `npm run dev` terminal or Azure App Service Log Stream.
- **Auth** — `NEXTAUTH_DEBUG=true` in `.env.local` for verbose NextAuth output.
- **CSP violations** — visible in browser DevTools Console; check `CHILD_SRC_ALLOWED_ORIGINS`.
- **Session inspection** — `console.log(useSession())` from any component during dev.

### Common pitfalls

| Pitfall | Fix |
|---|---|
| Node version mismatch (18 / 20 / 22 across files) | Use Node 20 locally for PR-gate parity |
| `api_url` without trailing slash | `coreAPI.tsx` does `api_url + url`; missing `/` produces double-path errors |
| HTTPS `NEXTAUTH_URL` sets `__Secure-` cookie prefix — required on HTTPS | Ensure `NEXTAUTH_URL` protocol matches runtime; HTTP locally |
| `CHILD_SRC_ALLOWED_ORIGINS` is space-separated, not comma-separated | Per `middleware.ts:9` — `child-src 'self' <value>` |
| Missing F92 env vars crash F92 routes with 500 | Only affects routes under `/api/core/`, `/api/dios/`, `/api/netsuite/` |
| Mantine CSS import missing | `@mantine/core/styles.css` in `_app.tsx` is mandatory; new Mantine packages need their own CSS imports |
| `output: "standalone"` build chain broken | `npm run build` copies `static` + `public` into `.next/standalone/` — don't break this during refactor |
| Iframe `postMessage` silently ignored | `event.origin != appUrl` check fails if `readmetadata` hasn't resolved yet |
| `JSON.parse(req.body)` in some API handlers | Some routes (`notificationCreate.tsx`, `syncpo.ts`) parse body unconditionally — keep client payloads stringified |

---

## Deployment

### Infra at a glance

| Thing | Value | Source |
|---|---|---|
| Hosting | Azure App Service (Linux, container) | `deploy_az_webapp.yaml` |
| Container registry | GHCR — `ghcr.io/aldc-io/eclipse:${ECLIPSE_VERSION}` | `compose.yaml` |
| Runtime image base | `node:18-alpine` | `Dockerfile:3` |
| Startup | `node server.js` (Next.js standalone) | `Dockerfile:CMD` |
| User | Non-root `nextjs:nodejs` (UID/GID 1001) | `Dockerfile:31-33` |
| Port | 3000 | `compose.yaml` |
| Public URLs | `eclipse.aldc.io`, `eclipse2-test.aldc.io` | [[eclipse-azure-deployment]] |
| DNS | [[Cloudflare]] CNAMEs → Azure App Service hostnames | |

### Environment model

Each environment (dev/test/qa/prod) is a **separate Azure App Service** with its own GitHub deployment-environment secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`) and a variable `AZURE_APP_SERVICE_NAME`. Each App Service has a **`stage` deployment slot**. Deploy goes to `stage` first; promote to production via a manual slot swap in the Azure Portal.

This is the **slot-swap model** documented in [[eclipse-azure-deployment]]. Contrast with [[eclipse_exp]], which uses Azure Container Apps revisions with no staging slot.

Cross-reference [[azure-environments]] + [[deployment-groups]].

### CI / PR gates — workflow inventory

7 workflow files in `.github/workflows/`:

**`ci.yml`** — The primary PR gate. Fires on push/PR to `main` and `eclipse-2.1`. Calls the reusable `quality-gate.yml` with `language: typescript`, `node-version: "22"`, `mutation-testing: true`, `supply-chain-scan: true`. Requires secrets `SEMGREP_APP_TOKEN` + `ANTHROPIC_API_KEY`.

**`quality-gate.yml`** — Reusable 6-gate pipeline (cross-reference [[ai-pr-workflow]]):
1. **Semgrep** — SAST + AI-smell rules (PR-only, non-Dependabot)
2. **TruffleHog** — verified secret scanning (all events; v3.94.3)
3. **Architecture** — dependency-cruiser (`.dependency-cruiser.cjs`) for TS — **not currently configured in this repo**, gate is skipped
4. **Mutation testing** — StrykerJS incremental on `src/**/*.ts(x)` — **won't fire** since source lives under `pages/`+`components/`, not `src/**`
5. **Supply chain** — GuardDog npm + Aikido Safe Chain (48-hour min package age)
6. **Claude Opus review** — `claude-opus-4-6`, checks cross-file impact, architectural intent, removed safety, intent mismatch, AI code smells; blocks merge on `has_blockers: true`

Required status check: `gate` (aggregator job).

**`PR_checks.yaml`** — Fires on `pull_request: [synchronize]`. Node 20. `npm install` → `npm audit` → `lint:check` → `format:check`.

**`deploy_az_webapp.yaml`** — **The production deploy workflow.** Manual dispatch with `environment` input. Azure OIDC login → Node 20 → `npm install && npm run build` → `azure/webapps-deploy@v3` to `vars.AZURE_APP_SERVICE_NAME` slot `stage` → `az logout`. Package: `./.next/standalone`. Does **not** build or push a Docker image.

**`build_docker_image.yaml`** — **Stub** (echoes placeholder). Unfinished.

**`deploy_az_webapp_container.yaml`** — **Stub** (echoes dummy message). Unfinished.

**`deploy_on_premise.yaml`** — **Stub** (echoes placeholder on self-hosted runner). Unfinished.

> **Summary:** only `deploy_az_webapp.yaml` performs a real deployment. The three stub workflows are placeholders pending implementation. **Always deploy from `eclipse-2.1`** (now the default branch as of 2026-04-29). See [[eclipse-azure-deployment]] § Incident: 2026-04-29 wrong-branch deploy for why `main` must not be used.

### Rollback

Slot swap is bidirectional. If `stage` was just promoted to production and something is wrong, swap back in the Azure Portal. To redeploy a prior commit, re-run `deploy_az_webapp.yaml` from a prior tag/SHA — no automated rollback on health failure (unlike [[eclipse_exp]]'s Container Apps revision-rollback).

### Release tagging

`compose.yaml` pulls `ghcr.io/aldc-io/eclipse:${ECLIPSE_VERSION}`. The `deploy_az_webapp.yaml` pipeline does **not** push to GHCR — it builds a Next.js standalone and deploys directly. How GHCR tags are published is not currently wired (the `build_docker_image.yaml` stub would do it once completed). **Confirm with team** before relying on the GHCR image for production Docker deployments.

---

## F92 Integrations

F92-specific surface area in the codebase. Irrelevant for non-Fusion92 tenants but present in all deployments.

**Components:**
- `components/Fusion92/POModal.tsx` — PO commit modal (triggers NetSuite sync)
- `components/Fusion92/ProcessAudienceFilesButton.tsx` — DIOS audience processing trigger
- `components/Fusion92/SubmitFlightButton.tsx` — Flight Check PO submit
- `components/F92ApplicationForm.tsx`, `F92ApplicationTable.tsx`, `F92ApplicationParentDetails.tsx` — F92-branded application management screens
- `components/F92DataTable.tsx`, `F92Login.tsx`, `F92NotificationSettings.tsx` — F92-branded variants
- `components/nonHTMLcomponents/F92Theme.tsx` — F92 colour/theme override

**API routes:**
- `pages/api/core/notificationCreate.tsx` + `notificationUpdate.tsx` — inject `F92_NOTIFICATION_URL` + `F92_NOTIFICATION_KEY` before forwarding to core_api
- `pages/api/dios/audience/process.ts` — DIOS audience processing; `x-auth-apikey: ${DIOS_API_KEY}`
- `pages/api/dios/projects/[projectName]/audiences.ts` — DIOS project audiences
- `pages/api/netsuite/sync/syncpo.ts` — NetSuite PO sync; `x-functions-key: ${F92_NETSUITE_SYNC_TOKEN}`
- `pages/api/netsuite/sync/enabled.ts` — returns `F92_NETSUITE_SYNC_ENABLED`

**Assets:** `public/Fusion92/` + `public/F92GreenBackgroundLogin.png`.

Cross-references: [[fusion92]], [[dax-media-app]], [[custom-fusion-92-audience-api]], [[fusion92-platform-ids]].

---

## Relationship to eclipse_exp

This repo and [[eclipse_exp]] run **in parallel** during the strangler-fig migration:

| Dimension | `eclipse` (this repo) | [[eclipse_exp]] |
|---|---|---|
| Framework | Next.js 14 Pages Router | Next.js 15 App Router |
| Auth | NextAuth 4 + CosmosDB | HS256 JWT + Postgres |
| Backend | [[core_api]] (Azure Functions) | FastAPI (in same container) |
| Storage | [[CosmosDB]] | PostgreSQL + RLS |
| Deployment | Azure App Service + slot swap | Azure Container Apps + revision rollback |
| Status | Legacy — existing tenants | Active — new tenants |

Existing tenants stay on this repo; new tenants provision directly on eclipse_exp. Generic new features should go to eclipse_exp. Bugfixes for legacy tenants go here. See [[eclipse_exp]] § Migration from Legacy Eclipse for the cutover mechanics (`TenantCutover`, `DualWriteConfig`).

---

## See Also

- [[Eclipse]] — Platform/concept page (connections, templates, tasks). Same product name; different wiki page. Use `[[entities/repos/eclipse|eclipse (repo)]]` when path precision matters.
- [[core_api]] — Azure Functions backend that every API call terminates at
- [[eclipse_exp]] — Next-gen successor (FastAPI + Next.js 15 + Postgres)
- [[connector]] — Sibling data-plane repo (data movement; Prefect migration in progress)
- [[clients-repo]] — Source of truth for Eclipse connection/template JSON configs
- [[eclipse-azure-deployment]] — Deployment runbook (slot-swap model)
- [[azure-environments]] — Subscription / environment model
- [[deployment-groups]] — Per-env Azure resource inventory
- [[GitHub Actions]] — CI/CD hosting layer
- [[ai-pr-workflow]] — The 6-gate PR pipeline this repo uses
- [[Azure]] — App Service hosting
- [[Cloudflare]] — DNS CNAMEs
- [[dax-media-app]] — Flight Management app embedded via iframe
- [[custom-fusion-92-audience-api]] — DIOS API that `/api/dios/*` routes call
- [[fusion92]], [[fusion92-platform-ids]] — Client context for F92 integrations
- [[postman-collections]] — To exercise core_api endpoints the UI calls
- [[CosmosDB]] — Where core_api reads the Eclipse config data this UI surfaces
