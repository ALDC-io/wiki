---
tags: [distributed-workflow, archived, repo-documentation, docs]
aliases: [Repo Documentation Workstream]
sources: []
created: 2026-04-20
updated: 2026-04-20
archived: 2026-04-20
status: complete
---

# Repo Documentation — Workstream Tracker

> **✅ Workstream complete 2026-04-20.** 9 repos documented + cross-repo integration map produced ([[repo-integration-map]]). 10 new wiki pages, 4 memories, 1 potential ticket (`.pbip` migration), 11 stale cross-references flagged for follow-up. See the workstream closure entry at the bottom of this tracker and in [[log]].

Creates engineering documentation (architecture, data flow, developer workflow, deployment/infra) for each ALDC repo. One plan session + one execution session per repo, then a final cross-repo integration session.

All repos live at `C:\Users\PaulRussell\repos\`. **All docs are written to the wiki only** — no files written into the repos themselves.

## Goal

Every repo gets a wiki page (or updated existing page) under `entities/repos/` containing:
- **Architecture** — components, tech stack, design decisions
- **Data Flow** — how data moves in/out (omit section if not applicable)
- **Developer Guide** — local setup, running, debugging, common pitfalls
- **Deployment** — infra, CI/CD, environment model, deployment steps
- Additional sections as warranted (API reference, connector specs, etc.)

Final cross-repo session produces `concepts/architecture/repo-integration-map.md` with diagrams.

"Done" = all 9 repos documented + integration session complete. **✅ WORKSTREAM COMPLETE 2026-04-20** — all 9 repos documented, integration map at [[repo-integration-map]] written (541 lines, 4 Mermaid diagrams covering 12 repos).

## Session model

For each repo:
1. **Plan session (Opus)** — reads the repo thoroughly, proposes a doc outline for each file including section headings and key content. Outputs a structured plan. Does NOT write docs yet.
2. **Execution session (Sonnet)** — receives the approved plan, writes all `docs/` files and the wiki page.

Final:
3. **Integration session (Opus)** — reads all 9 wiki pages + key docs, maps relationships, writes `concepts/architecture/repo-integration-map.md` with Mermaid diagrams.

## Repo queue

| #   | Repo                            | Path                                  | Type                                           | Plan         | Execution    |
| --- | ------------------------------- | ------------------------------------- | ---------------------------------------------- | ------------ | ------------ |
| 1   | `eclipse_exp`                   | `repos/eclipse_exp`                   | FastAPI + Postgres — next-gen Eclipse platform | ✅ 2026-04-20 | ✅ 2026-04-20 |
| 2   | `eclipse`                       | `repos/eclipse`                       | Next.js — current Eclipse web UI               | ✅ 2026-04-20 | ✅ 2026-04-20 |
| 3   | `flight-check`                  | `repos/flight-check`                  | Next.js — DAX Media App (Flight Management)    | ✅ 2026-04-20 | ✅ 2026-04-20 |
| 4   | `custom-fusion-92-audience-api` | `repos/custom-fusion-92-audience-api` | FastAPI — DIOS audience distribution API       | ✅ 2026-04-20 | ✅ 2026-04-20 |
| 5   | `claude_code_enhanced`          | `repos/claude_code_enhanced`          | TS/Python — CCE + skills library               | ✅ 2026-04-20 | ✅ 2026-04-20 |
| 6   | `workflows`                     | `repos/workflows`                     | Mixed — client-specific workflow code          | ✅ 2026-04-20 | ✅ 2026-04-20 |
| 7   | `prospect-site-template`        | `repos/prospect-site-template`        | Next.js — ALDC prospect microsites             | ✅ 2026-04-20 | ✅ 2026-04-20 |
| 8   | `aldc-scripts`                  | `repos/aldc-scripts`                  | Python/Bash — internal utility scripts         | ✅ 2026-04-20 | ✅ 2026-04-20 |
| 9   | `power_bi`                      | `repos/power_bi`                      | Power BI — shared templates + custom reports   | ✅ 2026-04-20 | ✅ 2026-04-20 |
| —   | **Integration**                 | all repos                             | Cross-repo architecture map + diagrams         | —            | ✅ 2026-04-20 |

## Boot prompts

### Per-repo plan session (Opus)

Replace `<REPO_NAME>` and `<REPO_PATH>` with the target repo.

````
You are running the **plan session** for `<REPO_NAME>` as part of the ALDC Repo Documentation workstream.

## Your job

Read the repo at `C:\Users\PaulRussell\repos\<REPO_PATH>` thoroughly and produce a **detailed doc plan** — a structured outline for each documentation file we will create. You are NOT writing the docs yet; you are producing the plan that the execution session will implement.

## Docs to plan

All docs go into a **single wiki page** at `entities/repos/<repo-slug>.md` (create new or update existing). Plan the sections for that page:

1. **Architecture** — components, tech stack, design decisions, key abstractions
2. **Data Flow** — how data enters, transforms, and exits (skip if not applicable — note this explicitly)
3. **Developer Guide** — prerequisites, local setup step-by-step, how to run, how to debug, common pitfalls
4. **Deployment** — infra overview, environment model, CI/CD pipeline, deployment steps, rollback
5. Any additional sections the repo warrants (API reference, connector spec, etc.)

No files are written into the repos themselves — wiki only.

## Context to read first

- `wiki/CLAUDE.md` (wiki page format, conventions)
- `wiki/index.md` (existing repo pages to avoid duplication)
- Existing wiki page if one exists (check `wiki/entities/repos/`)
- The repo itself: README, package.json / pyproject.toml / requirements.txt, key source files, existing docs/

## Output format

For each planned doc file, output:

```
### docs/ARCHITECTURE.md
**Purpose:** <one sentence>
**Sections:**
- ## Overview — <what this covers>
- ## Tech Stack — <what to list>
- ## Component Map — <what components to describe>
... (all sections with a note on key content)
```

End with a **Judgment calls** section noting anything non-obvious (e.g. "DATA_FLOW.md is not applicable — this is a UI repo with no data pipeline").

## After the plan

Update `processes/distributed-workflow/active/repo-documentation.md` — mark the Plan column for this repo ✅ and paste the approved plan into a new `## <REPO_NAME> — Approved Plan` section at the bottom of the tracker. Then append to `wiki/log.md`.
````

### Per-repo execution session (Sonnet)

Replace `<REPO_NAME>` with the target repo.

````
You are running the **execution session** for '<REPO_NAME>' as part of the ALDC Repo Documentation workstream.

## Your job

Read the approved plan from `processes/distributed-workflow/active/repo-documentation.md` § '<REPO_NAME>' — Approved Plan`, then implement it: write all `docs/` files and the wiki page.

## Rules

- All output goes to **one wiki page** at `wiki/entities/repos/<repo-slug>.md` — no files written into the repo
- Follow the exact section structure from the approved plan — don't invent new sections
- Be concrete: real file paths, real commands, real env var names. No placeholders except where a value genuinely isn't known (mark those `TODO`)
- Wiki page format: follow `wiki/CLAUDE.md` conventions (frontmatter, wikilinks, See Also)
- Do NOT modify any source code

## Sequence

1. Read the approved plan from the tracker
2. Read the repo source to fill in the real details
3. Write/update the wiki page at `wiki/entities/repos/<repo-slug>.md`
4. Update `wiki/index.md` if the page is new
5. Mark the Execution column ✅ in the tracker
6. Append to `wiki/log.md`
````

### Integration session (Opus)

````
You are running the **integration session** for the ALDC Repo Documentation workstream. All 9 repos have been documented.

## Your job

Read all 9 wiki pages under `wiki/entities/repos/` plus key `docs/ARCHITECTURE.md` files from each repo. Map how the repos relate to each other and produce `wiki/concepts/architecture/repo-integration-map.md`.

## What to produce

`repo-integration-map.md` should contain:

1. **Summary table** — all 9 repos with one-line purpose and integration tier (core platform / client-facing / tooling / internal)
2. **Mermaid diagram — data flow** — which repos send data to which, labelled with the data type
3. **Mermaid diagram — dependency graph** — which repos depend on (call / import / deploy) which
4. **Per-repo integration notes** — for each repo: what it consumes, what it produces, what calls it
5. **Isolated repos** — repos with no integration points (document why they stand alone)

## Context

- All wiki pages in `wiki/entities/repos/`
- `wiki/concepts/architecture/data-pipeline-flow.md`
- `wiki/entities/repos/clients-repo.md` (for overall ALDC platform context)
- `wiki/CLAUDE.md` for page format

## After

Update `wiki/index.md` (add `repo-integration-map` under Architecture). Mark Integration ✅ in the tracker. Mark the workstream DONE if all criteria met. Append to `wiki/log.md`.
````

## Session Log

### 2026-04-20 — Workstream created

- did: created this tracker. Cloned all 9 repos to `C:\Users\PaulRussell\repos\`. Quick-scanned READMEs to confirm repo types.
- decided: execution order prioritises most complex / highest platform value first (eclipse_exp → eclipse → flight-check → ...). Power BI and aldc-scripts last (lowest complexity).
- next: Start with `eclipse_exp` — open an Opus plan session using the boot prompt above.

## Approved Plans

_(Plans appended here as each plan session completes.)_

---

## eclipse_exp — Approved Plan

**Plan session:** 2026-04-20 (Opus)
**Target wiki page:** `wiki/entities/repos/eclipse_exp.md` (new page)
**Wiki index entry:** add under `Entities › Repos` alongside existing `eclipse`, `core_api`, `connector`, etc.

> Disambiguation note for the execution session: the legacy Next.js frontend repo is `eclipse` (wiki: [[eclipse]] — currently a *tool* page, not yet a repo page). `eclipse_exp` is a **separate, newer** unified repo that bundles a FastAPI backend AND a Next.js 15 frontend into a single Docker image. The repo-level name on the wiki is `eclipse_exp` (underscore, matches the repo folder); the product name inside the repo is "Eclipse EXP" / "ALDC next-generation data platform"; the deployed URL is `eclipse-exp.aldc.io`.

### Doc structure — single wiki page with these sections

All content goes into one page: `wiki/entities/repos/eclipse_exp.md`. Sections below are in the order they should appear on the page. Each section gives the execution session concrete, already-verified facts to write from (paths, filenames, env var names, line/table counts) — the execution session should fill in prose around these anchors, not re-derive them.

---

### Frontmatter

```yaml
---
tags: [entity, repo, eclipse-exp, platform, fastapi, nextjs, multi-tenant]
aliases: [Eclipse EXP, eclipse-exp, eclipse_exp API, ALDC next-gen platform]
sources: [repos/eclipse_exp/README.md, repos/eclipse_exp/CLAUDE.md, repos/eclipse_exp/docs/ARCHITECTURE.md, repos/eclipse_exp/docs/DEPLOYMENT.md, repos/eclipse_exp/docs/TARGET_ARCHITECTURE.md, repos/eclipse_exp/docs/MIGRATION_STRATEGY.md, repos/eclipse_exp/docs/PRINCIPLES.md, repos/eclipse_exp/docs/RUNBOOK.md, repos/eclipse_exp/docs/SECURITY.md, repos/eclipse_exp/docs/API_GUIDE.md, repos/eclipse_exp/docs/ONBOARDING.md, repos/eclipse_exp/app.py, repos/eclipse_exp/Dockerfile, repos/eclipse_exp/supervisord.conf, repos/eclipse_exp/.github/workflows/deploy.yml]
created: 2026-04-20
updated: 2026-04-20
---
```

---

### Section 1 — Intro paragraph (top of page, no heading)

**Purpose:** Position `eclipse_exp` against the rest of the ALDC stack so a cold reader knows what this repo is vs. [[eclipse]], [[core_api]], [[connector]].

**Key content:**
- One-sentence identity: *contract-first, AI-native multi-tenant data platform*.
- Relationship to the legacy stack: successor to the current [[eclipse]] Next.js UI + [[core_api]] pair; runs in parallel via a strangler-fig migration (not a replacement — see Principle 3, `docs/PRINCIPLES.md:28-33`).
- What's unusual about it: the repo bundles **both** the FastAPI backend AND the Next.js 15 frontend into a **single Docker image** managed by `supervisord` (gunicorn on :8080 + node on :3000). This is a deliberate deployment-simplicity choice, different from how legacy Eclipse was split.
- Deployed URL: `https://eclipse-exp.aldc.io`.
- Scale anchors (from `CLAUDE.md`): 36 route modules, 87 SQL migrations, 50 connector types, 67 RLS-enabled tables, 3,848 backend + 388 frontend tests.

---

### Section 2 — `## Architecture`

**Purpose:** Give a reader the mental map for the codebase in one screenful, then drill into the pieces that aren't obvious from a `ls`.

**Sub-sections:**

- `### Repository layout` — table of top-level dirs with one-line purpose. Use the list from `CLAUDE.md:7-28` as the source of truth. Include: `app.py`, `auth/`, `core/` (with `core/routes/`, `core/services/`, `core/governance/`, `core/rbac/`), `connectors/` (with `base/v2/`, `rest/`, `odbc/`, `custom/`, `file/`, `odata/`), `api/`, `onboarding/`, `dashboards/`, `migration/`, `db/`, `ingestion/`, `pipeline/`, `orchestration/`, `agents/`, `contracts/`, `clients/`, `sdk/`, `dbt/`, `frontend/`, `migrations/` (note plural SQL migrations vs singular `migration/` Python package), `scripts/`, `tools/`, `ops/`, `tests/`, `docs/`.

- `### Tech stack` — table grouped by layer. Source: `docs/ARCHITECTURE.md:162-182` and `requirements.txt`. Columns: Layer | Choice | Notes. Must name: FastAPI ≥0.115, Python 3.12, asyncpg ≥0.29, pydantic-settings, gunicorn + uvicorn workers (2 workers, 120s timeout, from `supervisord.conf:8`), slowapi rate limits, structlog + asgi-correlation-id, OpenTelemetry (OTLP), prometheus-fastapi-instrumentator, cryptography (Fernet) + optional Azure Key Vault, Anthropic SDK (AI chat / onboarding), Azure Cosmos (migration cutover only), dbt-core + DuckDB (dev) / Snowflake (prod), PyJWT (HS256), msal, pandas + pyarrow + duckdb for in-process analytics, Next.js 15 with `basePath=/internal` + Mantine 8 + NextAuth 4 + React Query 5 + Sentry.

- `### How a request flows` — narrative walkthrough following the middleware stack from `app.py`:
  1. slowapi `SlowAPIMiddleware` (rate limits, 100/min default, 30/min auth — `app.py:218-220`).
  2. `CorrelationIdMiddleware` (asgi-correlation-id — `app.py:223`).
  3. CORS middleware with env-driven origins, wildcard only in `ENVIRONMENT=development` (`app.py:227-242`).
  4. `security_headers_middleware` (X-Content-Type-Options, X-Frame-Options=DENY, Referrer-Policy, HSTS in non-dev — `app.py:245-254`).
  5. Prometheus auto-instrumentation at `/metrics` (`app.py:257-260`).
  6. Custom `auth_middleware` — resolves tenant from Bearer JWT or `X-API-Key`, skips public paths (`/ping`, `/health`, `/docs`, `/api/v1/auth/*`, `/internal/*`, OAuth callbacks, WS endpoint) (`app.py:267-322`).
  7. Route handler acquires DB connection via `tenant_connection()` (from `db/pool.py`) which does `SET LOCAL app.tenant_id` — RLS takes over from here.
  8. Response flows back through the same stack.

- `### Key abstractions` — list with one-paragraph each:
  - **`Settings` (pydantic-settings)** — `core/config.py`. Fails the app at startup on missing `DATABASE_URL` or <32-char `ECLIPSE_EXP_JWT_SECRET`. Full env var list in Deployment section below.
  - **asyncpg pool + `tenant_connection()`** — `db/pool.py`. Pool init sets `search_path` to `eclipse_exp, public`; `tenant_connection(pool, tenant_id)` wraps `SET LOCAL app.tenant_id = $1` inside a transaction. Exponential-backoff retry (1s/2s/4s) on pool create, auto-retry once on `InterfaceError`. Defaults: `min_size=2, max_size=10, command_timeout=60, max_inactive_connection_lifetime=300`.
  - **`WorkQueueRunner`** — `core/worker.py`. Polls `work_queue` with `SELECT … FOR UPDATE SKIP LOCKED` so multiple replicas don't double-process. `register_all()` wires task-type → handler map (`ingestion`, `ingestion_v2`, `activation`, `cutover`, `dashboard_gen`). Immediate Slack alert on failure via `pipeline.alerting.send_immediate_failure_alert`.
  - **Background schedulers** (all started in `app.py:99-124`, gated by `SCHEDULER_ENABLED`): `ConnectorScheduler` (polls `work_templates` on cron), `WorkflowScheduler`, `TaskNotifier` (daily 6 AM ET Slack DMs), `PipelineAlertScheduler` (background rule eval).
  - **Auto-migration on startup** — `scripts/auto_migrate.py` invoked from lifespan (`app.py:50-79`). Applies any pending `migrations/*.sql` in numeric order, then runs a hard-coded set of `ALTER TABLE IF NOT EXISTS` safety patches for known skipped migrations. *Flag this as non-obvious*: migrations run in-process at every cold start, not as a separate CI step.
  - **`BaseConnectorV2`** (contract-first V2 connector pattern) — `connectors/base/v2/base.py`. Paired with `ConnectorConfig` (Pydantic), `ConnectorResponse` (DataFrame + metadata), `DataContract` (columns/PKs/quality rules). 50 connectors total split across `rest/` (24), `odbc/` (9), `file/` (2), `custom/` (10) and their `v2/` subdirs. Legacy V1 classes (`BaseConnector`, `BaseConnectorFlat`, `BaseConnectorOdbc`) remain for the older connectors. Cross-reference [[connector-development-standards]].
  - **`TenantCutover` / `DualWriteConfig`** (strangler-fig migration machinery) — `migration/`. Lets a tenant dual-write to Cosmos + Postgres, then cut over when verified. Requires `COSMOS_CONNECTION_STRING`.
  - **Reverse proxy to Next.js** — `app.py:575-630`. `/internal/{path:path}` is proxied to `$ECLIPSE_FRONTEND_URL` (defaults to `http://localhost:3000`). Preserves multi-Set-Cookie headers for NextAuth. Rewrites absolute `Location` headers through the proxy. This is how a single `eclipse-exp.aldc.io` origin serves both API (`/api/v1/*`) and UI (`/internal/*`).

- `### API surface` — table reproduced from `README.md:52-70` (the 15 `/api/v1/*` prefixes) but **add** the post-README routers actually registered in `app.py` lines 402-551: `catalog`, `prospect-data`, `governance`, `onboarding` (two different onboarding routers — `api/onboarding_routes.py` for provisioning, `core/routes/onboarding.py` for data-model onboarding), `self-service`, `admin`, `pipeline`, `portal`, `ops`, `filter-metadata`, `integrations` (QBO/TSheets OAuth), `tasks` + `tasks-ws` (kanban + WebSocket), `profitability`, `business-context`, `monitors`, `workflows`, `apps` (app registry / marketplace), `connectors/health`, `connectors/catalog`, `flight-checks` (FlightCheck EXP — Fusion92 parallel build), `onboarding_chat` (SSE), `ai-chat` (Claude SSE streaming), `strategy`, `meetings`, `management_meetings` (Lori/Marshall/Mike owner model), `sred` (SR&ED tracker), `marketing`, `strat-map`, `health` (Zeus Memory perf dashboard), `campaigns` (Graph API email parsing). Also: compatibility aliases at `/api/v1/dataViews`, `/api/v1/signUp`, `/api/v1/passwordReset` (camelCase, `include_in_schema=False`, for legacy Eclipse frontend).

- `### Design decisions worth calling out`
  - **Contract-first** — `docs/PRINCIPLES.md`. Contracts in `contracts/` (compatibility, generator, schema) are the source of truth; governance engine (`core/governance/`) validates changes.
  - **RLS from day one** — every tenant table uses `NULLIF(current_setting('app.tenant_id', true), '') IS NULL OR tenant_id = …::uuid`. Admin endpoints bypass RLS by never setting the GUC. Cross-reference `migrations/019_rls_security.sql`, `021_rls_safe_tenant_check.sql`, `068_multi_tenant_hardening.sql`.
  - **No `from __future__ import annotations` in route files** — breaks slowapi/FastAPI parameter detection (`CLAUDE.md:35`). Call this out explicitly — it's a foot-gun.
  - **Single-container unified deployment** — one image runs gunicorn + node via supervisord. Rationale: one CI/CD pipeline, one Azure Container App, one DNS, simpler revision rollback. Trade-off: frontend and backend always ship together.
  - **Strangler-fig migration** — legacy Eclipse stays on NextAuth + Cosmos DB; eclipse_exp runs alongside on JWT + Postgres + RLS. Clients migrate via feature flag/DNS. See `docs/MIGRATION_STRATEGY.md`.
  - **Dual query-engine target** — DuckDB locally, Snowflake in prod, for Gold/semantic layer reads. PostgreSQL is the primary store in all environments.

---

### Section 3 — `## Data Flow`

**Purpose:** Describe how data enters, transforms, and exits. This repo *is* a data pipeline — section is very applicable.

**Sub-sections:**

- `### Source → Bronze → Silver → Gold → Dashboard` — reproduce the 10-step pipeline from `docs/ARCHITECTURE.md:45-68` with wiki cross-references to [[data-pipeline-flow]] and [[star-schema-convention]]. Steps: Connector.fetch() → ConnectorResponse → DataContract.assert() → BronzeWriter (immutable Parquet, path `{tenant}/{connector}/{table}/{timestamp}/data.parquet`, added cols `_aldc_ingested_at / _aldc_source_hash / _aldc_tenant_id`) → SchemaRegistry (drift detection) → QualityGateRunner (PK non-null, uniqueness, custom rules) → dbt staging (Silver) → DimensionalModel (Gold fact+dim) → SemanticLayerService → Dashboard API.

- `### Ingestion triggers` — three ways data gets pulled:
  1. **Scheduled** — `ConnectorScheduler` polls `work_templates` every `SCHEDULER_POLL_INTERVAL` seconds (default 60), enqueues jobs on cron match.
  2. **Queued** — anyone writes to `work_queue`; `WorkQueueRunner` picks it up via `SELECT FOR UPDATE SKIP LOCKED`.
  3. **Onboarding-triggered** — new tenant provisioning queues `activation` + initial `ingestion_v2` jobs.

- `### Storage` — Bronze Parquet on local disk (`BRONZE_STORAGE_ROOT=/tmp/eclipse_exp/bronze/`, `BRONZE_STORAGE_BACKEND=local`; ADLS is a future target per `core/config.py:62`). Silver/Gold in PostgreSQL tables. dbt models in `dbt/models/{staging,intermediate,gold,semantic}`.

- `### Dashboard generation` — `dashboards/generator.py` + `dashboards/branding.py` + `dashboards/template_library.py`. AI-heuristic layout from dataset definition + brand colors. 9 business-type templates (`agency`, `ecommerce`, `saas`, `healthcare`, `nonprofit`, `real_estate`, `education`, `government`, `other` — list from `docs/ONBOARDING.md:84-95`).

- `### Out-of-band data paths`
  - **Onboarding chat SSE** — `/api/v1/onboarding-chat` streams Claude responses during AI-driven prospect onboarding.
  - **AI chat SSE** — `/api/v1/ai-chat` streams Claude responses, tenant-aware.
  - **Task WebSocket** — `/api/v1/tasks/ws` real-time kanban updates (auth via query token, not JWT header).
  - **Prometheus scrape** — `/metrics`.
  - **Audit logging** — writes to `audit_logs` table fire-and-forget from 16 route modules / 62+ write endpoints (`docs/SECURITY.md:27-34`).
  - **Slack alerts** — immediate failure alerts from `WorkQueueRunner`; daily 6 AM ET digest from `TaskNotifier`.

---

### Section 4 — `## Developer Guide`

**Purpose:** Get a developer from clean machine to running local server + first API call.

**Sub-sections:**

- `### Prerequisites`
  - Python 3.12 (repo's mypy config pins `python_version = "3.12"`; Dockerfile uses `python:3.12-slim`).
  - Node.js 22 (frontend requires ≥22.0.0 per `frontend/package.json:engines`).
  - PostgreSQL 16 (GHA CI uses `pgvector/pgvector:pg16`, migrations include vector extension — see `030_vector_embeddings.sql`).
  - Docker + Docker Compose (optional but recommended).
  - `cryptography` + `python-dotenv` installed via `requirements.txt`.

- `### Environment variables`
  - Point readers to `core/config.py` as the canonical schema.
  - **Required:** `DATABASE_URL`, `ECLIPSE_EXP_JWT_SECRET` (min 32 chars — the Pydantic validator rejects anything shorter).
  - **Common optional:** `ENVIRONMENT` (development/staging/production; wildcard CORS only in development), `CORS_ORIGINS`, `ENCRYPTION_KEY` (Fernet), `AZURE_KEY_VAULT_URL`, `ECLIPSE_API_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `ANTHROPIC_API_KEY`, `ZEUS_API_URL` / `ZEUS_ALDC_API_KEY`, `COSMOS_CONNECTION_STRING` (migration only), `SCHEDULER_ENABLED` (default true; set false to skip all background schedulers during dev), `BRONZE_STORAGE_ROOT`, `PBI_*` (per-workspace Power BI service principals), `POWERBI_*`, `RATE_LIMIT_DEFAULT` (100/minute), `RATE_LIMIT_AUTH` (30/minute), `ECLIPSE_FRONTEND_URL` (defaults to `http://localhost:3000`).
  - **Key generation commands** (from `docs/DEPLOYMENT.md:42-48`):
    - JWT: `python3 -c "import secrets; print(secrets.token_hex(32))"`.
    - Fernet: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

- `### Local setup — backend only`
  1. `git clone` + `cd eclipse_exp`.
  2. `python3.12 -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
  3. `pip install azure-mgmt-resourcehealth==1.0.0b6` (beta pin, must install first per `Dockerfile:35` and `deploy.yml:77`).
  4. `pip install -r requirements.txt`.
  5. Start Postgres 16 locally (Docker: `docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16`).
  6. Create `.env` with `DATABASE_URL`, `ECLIPSE_EXP_JWT_SECRET` (generated above), `ENVIRONMENT=development`, `SCHEDULER_ENABLED=false` (skip schedulers while iterating).
  7. Run: `python -m uvicorn app:app --reload --port 8080`. Migrations auto-apply at startup.
  8. Smoke test: `curl http://localhost:8080/ping` → `{"status":"ok","service":"eclipse_exp"}`.
  9. Swagger UI: `http://localhost:8080/docs` (has a Bearer-auth button — wired up by the custom OpenAPI shim at `app.py:200-215`).

- `### Local setup — frontend only`
  1. `cd frontend && npm ci`.
  2. `npm run dev` (Next.js dev server on :3000). With `NODE_ENV !== production`, Next proxies `/api/v1/*` to `http://127.0.0.1:8081/api/v1/*` (note port **8081**, from `next.config.mjs:22-33`). To drive a Python backend on a different port during dev, either change the rewrite or run the backend on 8081.
  3. Lint gate before committing: `npm run lint:check` (strict: `--max-warnings=0`) AND `npm run format:check`.

- `### Local setup — full stack via Docker Compose`
  - `cp .env.example .env` then fill in values (but repo does **not** ship a complete `.env.example`; direct readers to `core/config.py` + `docs/DEPLOYMENT.md:54-75`).
  - `docker-compose up --build`.
  - App at `http://localhost:8080`; `docker-compose.yml` ships just the api service — pair with a local Postgres container or point `DATABASE_URL` at your machine's Postgres.

- `### Running tests`
  - `pytest` — uses `pytest.ini` testpaths, `asyncio_mode=auto`. Baseline to protect: **3,848 backend + 388 frontend** (`CLAUDE.md:60`).
  - With DB: `DATABASE_URL=postgresql://… pytest` — integration tests auto-skip without it.
  - Count verification before PR: `python3 -m pytest --collect-only -q 2>&1 | tail -3`.
  - Fixtures (from root `conftest.py`): `mock_pool`, `mock_conn`, `auth_token(role="owner")`, `auth_headers(role="owner")`.
  - Tenant patching idiom: `@patch("core.routes.module.tenant_connection")`.
  - Frontend tests: `cd frontend && npm test` (Jest + Vitest configs both present).

- `### Debugging`
  - **Structured logs** — JSON via structlog. Every request has a `correlation_id` (asgi-correlation-id). `cat logs.json | jq 'select(.correlation_id == "…")'`.
  - **Per-tenant filter** — `jq 'select(.tenant_id == "b513bc6e-…")'`.
  - **Slow requests** — `jq 'select(.duration_ms > 5000)'`.
  - **Pool metric** — `eclipse_db_pool_size` gauge (labels `state=free|used`). When `used==max_size` the pool is exhausted.
  - **Pool exhaustion recovery** — `SELECT * FROM pg_stat_activity WHERE state='active'`; `pg_terminate_backend(pid)` on the offender; restart container if persistent. Full runbook at `docs/RUNBOOK.md:108-120`.
  - **Custom metrics** — `eclipse_onboarding_duration_seconds` (histogram), `eclipse_connector_runs_total` (counter).
  - **Local scheduler disable** — `SCHEDULER_ENABLED=false` in `.env` turns off all four schedulers; useful when you just want to hit routes.

- `### Common pitfalls`
  - **`from __future__ import annotations` in route files breaks slowapi** — `CLAUDE.md:35`. Don't add it to new route modules.
  - **Frontend `basePath=/internal`** — use `/tasks` not `/internal/tasks` in links. Next.js prepends `basePath` automatically — hardcoding causes `/internal/internal/tasks` (`CLAUDE.md:41`).
  - **`useSearchParams()` needs a Suspense boundary in Next.js 16** (repo is currently on Next 15 per `frontend/package.json`, but upgrading is on the path — pre-emptive note).
  - **API proxy `redirect:"manual"`** — required to preserve the Authorization header through FastAPI 307 redirects (`CLAUDE.md:44`).
  - **Short JWT secret** — app exits on startup with `JWT secret must be at least 32 characters`.
  - **Pool creation retries 3× then exits** — if PostgreSQL isn't up when the app starts, it dies after 7s (1+2+4). Start Postgres first.
  - **Migration auto-apply in production** — migrations run inside the FastAPI lifespan. A bad migration blocks startup. If startup fails, inspect the log for the exact SQL that broke — `app.py:80-81` catches the exception but still logs it.
  - **No emoji flags in the frontend** — `CLAUDE.md:46`. Render country codes instead (Linux/Windows fonts render the flag emojis inconsistently).

---

### Section 5 — `## Deployment`

**Purpose:** How a commit becomes a production revision, and how to unstick things when it doesn't.

**Sub-sections:**

- `### Infra at a glance` — table:

  | Thing | Value | Source |
  |---|---|---|
  | Resource group | `rg-zeus-memory-dev` | `deploy.yml:9` |
  | Container App | `eclipse-exp-api` | `deploy.yml:10` |
  | ACR | `acrzeusmemorydev.azurecr.io` | `deploy.yml:11` |
  | Container Apps Env | `cae-zeus-memory-dev` | `deploy.yml:12` |
  | Public URL | `https://eclipse-exp.aldc.io` | `deploy.yml:180` |
  | DB host | Azure Database for PostgreSQL (name in `vault/`) | `docs/SECURITY.md:16` |
  | Runtime image | `python:3.12-slim` base, Node 22 installed, Next.js standalone copied in from builder stage | `Dockerfile` |

- `### Environment model` — single production environment (eclipse-exp-api Container App); no separate staging Container App exists — staging traffic rides on prior Container App revisions. Call out that this is *different from legacy Eclipse*, which uses paired staging/production slots per [[eclipse-azure-deployment]]. Cross-reference [[azure-environments]] and [[deployment-groups]].

- `### CI/CD pipeline — push-to-main auto-deploy`
  Reference: `.github/workflows/deploy.yml`. Five jobs:
  1. **`changes`** — uses `dorny/paths-filter` to classify the diff as `backend` and/or `frontend`. Skips unaffected test jobs.
  2. **`test-backend`** (only if backend changed) — Python 3.12, spins up a `pgvector/pgvector:pg16` service, `pip install -r requirements.txt`, runs `pip-audit` (non-blocking), runs `pytest` with coverage. CI uses `ECLIPSE_EXP_JWT_SECRET=ci-test-secret-that-is-at-least-32-characters-long`. Some tests intentionally skipped: `not test_list_accounts_returns_list and not test_lookup_entity_success`.
  3. **`lint-frontend`** (only if frontend changed) — Node 22, `npm ci`, `npm audit --audit-level=critical`, `tsc --noEmit`, `eslint . --max-warnings=0`, `prettier --check .`, `npm test`.
  4. **`deploy`** (main branch only, on test success OR test skipped) — Azure login via `AZURE_CREDENTIALS` secret, `az acr login`, `docker build` tagged both `:latest` and `:${{ github.sha }}`, push, `az containerapp update` to the SHA tag, then curl `https://eclipse-exp.aldc.io/health` and fail if `status != healthy`. On failure, **automatic rollback** — reactivates the previous active revision.
  5. **`load-test`** (on successful deploy) — k6 10 VUs for 30s against `/internal/navira`, summary uploaded as artifact.
  Also present: `ai-security-audit.yml` (PR-triggered AI security review on security-relevant paths) and `daily-self-improve.yml` (weekly cron — Mon 9 AM PST — Opus-backed security review + few-shot harvesting that can open PRs).
  Dependabot is configured (`.github/dependabot.yml`).

- `### Deployment steps (manual fallback)` — reproduced from `docs/DEPLOYMENT.md:100-126`:
  ```bash
  docker build -t acrzeusmemorydev.azurecr.io/eclipse-exp-api:<tag> -f Dockerfile .
  az acr login --name acrzeusmemorydev
  docker push acrzeusmemorydev.azurecr.io/eclipse-exp-api:<tag>
  az containerapp update --name eclipse-exp-api --resource-group rg-zeus-memory-dev \
      --image acrzeusmemorydev.azurecr.io/eclipse-exp-api:<tag>
  ```

- `### Setting/rotating secrets` — `az containerapp secret set` + `--set-env-vars secretref:…` idiom from `docs/DEPLOYMENT.md:130-144`. For Fernet key rotation see `docs/RUNBOOK.md:124-142` (generate new key, set `ENCRYPTION_KEY_NEW`, re-encrypt all `auth_config` values via `SecretManager.rotate_key`, swap `ENCRYPTION_KEY`, restart).

- `### Runtime layout inside the container`
  - supervisord (`supervisord.conf`) runs two processes:
    - **gunicorn** on `:8080`: `gunicorn app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080 --timeout 120 --access-logfile - --forwarded-allow-ips="*"`.
    - **nextjs** on `:3000`: `/usr/local/bin/docker-entrypoint.sh node server.js` (entrypoint injects runtime env vars into `.env.local` before starting Next).
  - Only `:8080` is exposed; `/internal/*` requests are proxied in-process from gunicorn to `http://127.0.0.1:3000`.
  - Healthcheck in Dockerfile hits `/ping` every 30s (3 retries, 10s timeout).

- `### Rollback`
  - **Automatic** — failed smoke test on deploy re-activates the previous revision (`deploy.yml:187-203`).
  - **Manual** — list revisions: `az containerapp revision list -n eclipse-exp-api -g rg-zeus-memory-dev -o table`; shift traffic: `az containerapp ingress traffic set -n eclipse-exp-api -g rg-zeus-memory-dev --revision-weight <prev>=100`.
  - **Migration rollback** — provisioning is atomic (single transaction); for manual cleanup use the `DELETE FROM eclipse_exp.*` chain in `docs/RUNBOOK.md:173-183`.

- `### Observability`
  - **Metrics** — Prometheus scrape at `/metrics`. Custom gauges/counters: `eclipse_db_pool_size`, `eclipse_onboarding_duration_seconds`, `eclipse_connector_runs_total`. HTTP metrics auto-instrumented.
  - **Traces** — OpenTelemetry, OTLP exporter, enabled when `OTEL_EXPORTER_OTLP_ENDPOINT` is set (`app.py:141-144`).
  - **Logs** — structlog JSON, per-request `correlation_id`. Query recipes in `docs/RUNBOOK.md:187-211`.
  - **Alert rules / dashboards** — `ops/alert-rules.yml`, `ops/grafana-dashboard.json`.
  - **Slack** — immediate failure alerts on work-queue job failure; daily 6 AM ET digest from `TaskNotifier`.

- `### Health probes`
  - `GET /ping` — liveness, no auth, no DB. `{"status":"ok","service":"eclipse_exp"}`.
  - `GET /health` — readiness, executes `SELECT 1`. Returns `healthy` or `degraded` + DB state. Used by the deploy smoke test and should be the Container App readiness probe.
  - `GET /metrics` — Prometheus text format.

---

### Section 6 — `## Security Model`

**Purpose:** Summarise the multi-tenant guarantees so the reader knows what's enforced where. Pulls from `docs/SECURITY.md`, `docs/TARGET_ARCHITECTURE.md`, `docs/ARCHITECTURE.md:183-234`.

**Sub-sections:**

- `### Authentication` — two mechanisms:
  - Bearer JWT (HS256, 1h expiry, signed with `ECLIPSE_EXP_JWT_SECRET`). Payload carries `tenant_id`, `user_id`, `role`, `team`. Refresh via `/api/v1/auth/refresh`.
  - API key via `X-API-Key`. Stored as SHA-256 hash in `tenant_api_keys`. In-memory cache after first lookup (`core/cache.py`). Supports expiration.
- `### Authorization (RBAC)` — 6 roles with hierarchy (viewer < member < editor < admin ≈ superuser < owner), 20 permissions across accounts/datasets/dashboards/visuals/data-views/users/rbac. Implementation in `core/rbac/`.
- `### Tenant isolation via RLS`
  - PostgreSQL schema `eclipse_exp` — 67+ RLS-enabled tables (`CLAUDE.md:3`).
  - Pattern: `NULLIF(current_setting('app.tenant_id', true), '') IS NULL OR tenant_id = current_setting('app.tenant_id')::uuid`. Admin endpoints deliberately *don't* set the GUC, which grants cross-tenant access.
  - `tenant_connection()` helper wraps every handler's DB access in a transaction with `SET LOCAL app.tenant_id = $1`. Pool `init` resets `search_path` on acquire.
- `### Secret management`
  - Fernet symmetric encryption, `enc:v1:` prefix identifies encrypted values.
  - Optional Azure Key Vault backend via `AZURE_KEY_VAULT_URL`.
  - `SecretManager.rotate_key()` for rotation.
- `### TLS` — Azure Container Apps terminates TLS at ingress. All PostgreSQL connections use `sslmode=require`. API keys/JWTs only in headers, never query params.
- `### Audit logging` — fire-and-forget via `audit_write()` on 62+ write endpoints across 16 route modules; inserted into `audit_logs` asynchronously. `UPDATE`/`DELETE` blocked by triggers (immutable).
- `### Governing principles` — name-check the nine principles from `docs/PRINCIPLES.md` and link. P9 ("Tenant Context Is Infrastructure") is the one most relevant to day-to-day route coding.

---

### Section 7 — `## Database Schema & Migrations`

**Purpose:** Anchor readers in how schema changes happen.

**Key content:**
- Schema name: `eclipse_exp`. Grants to role `eclipse_app` (`CLAUDE.md:38`).
- 87 numbered SQL migrations in `migrations/`. Name format: `NNN_description.sql`. Migrations **must** use `IF NOT EXISTS` and grant to `eclipse_app`. Rule from `CLAUDE.md:38`.
- Auto-applied on startup by `scripts/auto_migrate.py` inside `lifespan` (no separate CI step). Idempotent — reruns safely.
- Table inventory (from `docs/ARCHITECTURE.md:247-266`): `tenants`, `users`, `tenant_api_keys`, `tenant_secrets`, `connector_configs`, `connections`, `work_templates`, `work_queue`, `onboarding_jobs`, `contracts`, `contract_changes`, `quality_gates`, `audit_logs`, `cutover_jobs`, `dual_write_config`. Plus dozens more added by later migrations (tasks, boards, meetings, strat_map, marketing tables, vector embeddings, etc.).
- Migration ID collisions exist (two `019_*`, two `030_*`, two `035_*`, two `038_*`, two `039_*`, two `058_*`, two `059_*`, two `068_*`, two `069_*`) — auto_migrate handles these but flag it: **numbering is not strictly monotonic**; some pairs ship in one PR, some were back-added. Not a bug, but worth documenting so a new developer doesn't renumber.
- pgvector required (`030_vector_embeddings.sql`) — local dev needs `pgvector/pgvector:pg16` not vanilla `postgres:16`.

---

### Section 8 — `## Onboarding Pipeline`

**Purpose:** This is the flagship user-facing flow (prospect → production tenant in 6 steps). Worth its own section.

**Key content:**
- Two entrypoints:
  1. **Enterprise onboarding (ALDC-initiated)** — `POST /api/v1/onboarding/provision` with prospect URL + industry hints. Runs full pipeline: discovery → config-gen → provision → activate. Monitor via `GET /api/v1/onboarding/jobs/{job_id}`.
  2. **Self-service** — `/api/v1/portal/*` for smaller clients.
- 6-step orchestrator in `onboarding/`:
  1. **Discovery** (`onboarding/scraper.py` + `agents/discovery.py`) — scrapes prospect URL, AI classifies business type.
  2. **Classification** (`onboarding/classifier.py`).
  3. **Config generation** (`agents/config_gen.py`, `onboarding/templates.py`) — maps inferred sources to connector configs + KPI templates.
  4. **Validation** (`onboarding/validator.py`).
  5. **Provisioning** (`agents/provisioning.py`) — atomic DB transaction: creates tenant + account + connections + templates + API key. Rolls back on any failure.
  6. **Activation** (`agents/activation.py`) — queues initial ingestion jobs.
- Tracked in `onboarding_jobs` table.
- Business types supported and their KPI templates: reproduce the 9-row table from `docs/ONBOARDING.md:84-95`.
- Webhook path: `/api/v1/onboarding/webhooks/prospect-created` — public (no auth) path used by prospect-builder (`build.prospect.aldc.io` — which is the [[prospect-site-template]] repo).

---

### Section 9 — `## Connectors`

**Purpose:** eclipse_exp hosts 50 connector types. Inventory them.

**Key content:**
- Count breakdown from `docs/ARCHITECTURE.md:78-82`: REST 24, ODBC 9, File 2, Custom 10 (plus OData — a newer category not in the original table) = 50 total connector types.
- Full REST list: alphavantage, amazon_sellercentral, azure_metrics, dor_api, esri_shapefile, exchange_rates_api, google_maps, intuit_tsheets, jira, microsoft_bing_ads, nasa_worldview, nutshell, opendatasoft, openweathermap, phone_burner, qbo_accounting, restcountrieseu, scrape_loblaw, scrape_shopify, scrape_shoppersdrugmart, scrape_wunderground, seller_cloud, shopify_conn, tomtom, windsor_ai.
- Full ODBC list: athena_s3, cosmosdb, mysql, netsuite_analytics, netsuite_connect, postgresql, redshift, snowflake_conn, sql_server.
- Full Custom list: amazon_ads, facebook_business, firebase, google_ads, hubspot, mongodb, s3, smartsheet, tradedesk_myreports, viant_dsp_reporting.
- V1 vs V2 split: older connectors extend legacy `BaseConnector` in `connectors/base/base_connector*.py`; newer ones extend `BaseConnectorV2` in `connectors/base/v2/`. Each of `rest/`, `odbc/`, `custom/` has a `v2/` subdirectory for the migrated implementations. The `task_type=ingestion` handler runs V1; `task_type=ingestion_v2` runs the Bronze-layer V2 pipeline.
- Cross-reference [[connector-development-standards]] for the canonical V2 pattern, and [[connector]] for the separate data-plane runtime.
- Key V2 abstractions: `BaseConnectorV2`, `ConnectorConfig`, `ConnectorResponse`, `DataContract`, `Router` (dispatch by name+topic), plus `circuit_breaker.py` and `errors.py`.
- Cataloging/health endpoints: `/api/v1/connectors/catalog` (LLM-discoverable metadata) and `/api/v1/connectors/health` (monitoring).

---

### Section 10 — `## Migration from Legacy Eclipse`

**Purpose:** Point at the strangler-fig migration machinery and explain when this repo participates.

**Key content:**
- Overall strategy — strangler fig, documented in `docs/MIGRATION_STRATEGY.md` and `docs/CUTOVER.md`. Existing Eclipse clients stay on NextAuth + Cosmos; new clients provision on eclipse_exp (JWT + Postgres + RLS).
- Implementation in `migration/`:
  - `dual_write.py` / `DualWriteConfig` — per-tenant flag saying "write to Cosmos primary + Postgres shadow" or the reverse.
  - `data_sync.py` — verifies parity between the two stores.
  - `cutover.py` / `TenantCutover` — switches a tenant's primary store. Registered as `task_type=cutover` in the work queue.
  - Routes: `/api/v1/migration/*` (`migration/routes.py`).
- Requires `COSMOS_CONNECTION_STRING` — the Cosmos client is lazy-loaded in lifespan (`app.py:126-138`). Without it, cutover endpoints fail gracefully but read/write on eclipse_exp still works.
- Cross-reference [[eclipse-azure-deployment]] (the legacy deploy path this is replacing) and [[data-pipeline-flow]] (the platform-wide pipeline this participates in).

---

### Section 11 — `## See Also`

Wikilinks to related pages. Must include:
- [[eclipse]] — legacy Next.js UI this platform succeeds (currently indexed as a tool; consider adding a *repo* page for it during Plan session #2).
- [[core_api]] — legacy Azure Functions control plane; dual-runs alongside this repo during the migration period.
- [[connector]] — separate data-plane repo (Prefect flows); complementary to the in-process connectors here.
- [[connector-development-standards]] — the canonical V2 connector pattern that `base/v2/` implements.
- [[data-pipeline-flow]], [[star-schema-convention]], [[accumulating-source-tables]] — platform-wide data patterns.
- [[azure-environments]], [[deployment-groups]], [[aldc-naming-convention]] — Azure context.
- [[ai-pr-workflow]] — the PR workflow (Semgrep + TruffleHog + Claude Opus review + PyTestArch) that gates merges here.
- [[ai-development-project-standard]] — ALDC's >50% AI project standard (tokens/cost/time header) — flag whether this repo's files already carry it.
- [[zeus-memory]] — the memory platform this repo reads/writes to (via `clients/zeus_memory.py`).
- [[postman-collections]] — for anyone wanting to exercise `/api/v1/*` interactively.

---

## Judgment calls

- **`## Data Flow` IS applicable.** eclipse_exp is a data platform — ingestion → Bronze Parquet → dbt Silver/Gold → semantic layer → dashboard API. Do not skip this section.
- **Single wiki page is the right container, not multiple pages.** The boot prompt specifies one page at `entities/repos/<slug>.md`, and the repo is cohesive enough that splitting would force readers to jump. Size target: ~800–1200 lines. If it overruns, the CLAUDE.md schema says pages >200 lines on a sub-topic can split — the natural splits would be Onboarding Pipeline (Section 8), Connectors (Section 9), and Migration (Section 10), each becoming its own page under `processes/` or `concepts/` respectively. Flag during execution if we cross 1400 lines.
- **Do not duplicate in-repo `docs/*.md` verbatim.** The repo has 19 docs totaling ~4200 lines. The wiki page should **summarise and link**, not copy. Execution session should resist the urge to paste.
- **Disambiguation required.** Both `eclipse` (legacy) and `eclipse_exp` exist. The wiki currently has `[[eclipse]]` under Tools and `[[eclipse-exp]]` is not yet wikilinked anywhere except the workstream tracker. The execution session should use the wiki slug **`eclipse_exp`** (underscore) to match the repo path, and explicitly note in the intro that this is distinct from [[eclipse]].
- **Prospective eclipse repo page will need backlinks.** Plan session #2 (the `eclipse` repo) should update the [[eclipse]] wiki page to cross-reference eclipse_exp as its successor. Out of scope for this plan, but called out in Session Log so we don't lose it.
- **`core_api` page needs a "relationship to eclipse_exp" note.** The existing `entities/repos/core_api.md` doesn't mention eclipse_exp. Execution session should add a one-paragraph cross-reference there.
- **No `docs/DATA_FLOW.md`, `docs/DEVELOPER_GUIDE.md`, or `docs/ARCHITECTURE.md` files are being written into the repo itself.** Output is wiki-only per the boot prompt.
- **Sections 6–10 are extras beyond the four mandatory ones.** Justified because: Security (Section 6) is a named page requirement from the CLAUDE.md concepts structure; Database Schema (Section 7) is non-trivial (87 migrations, the numbering-collision gotcha); Onboarding Pipeline (Section 8) and Connectors (Section 9) are the core product features; Migration (Section 10) is the strategic positioning. If the execution session finds this expands past the size budget, collapse Section 7 into Architecture and Section 10 into Migration-linked one-liner.
- **Scheduler behaviour is non-obvious** and belongs in Architecture → Key abstractions, not buried in runtime config. Four background loops start in lifespan, all gated by one env var. Worth the call-out.
- **Migration auto-apply at startup is a deployment gotcha worth flagging twice** — once in Architecture (as a design decision), once in Developer Guide (as a pitfall).
- **`ECLIPSE_FRONTEND_URL` is missing from `docs/DEPLOYMENT.md`'s env var table** even though it's read in `app.py:569`. Execution session should document it in the Developer Guide + Deployment sections.
- **No dedicated staging environment** — unlike legacy Eclipse's slot-swap model documented in [[eclipse-azure-deployment]]. Call this out explicitly in the Environment model sub-section; it's a material operational difference between the two systems.

### Session Log entry to add

```
### 2026-04-20 — eclipse_exp plan session complete

- did: read repo (README, CLAUDE.md, app.py, Dockerfile, supervisord.conf, docker-compose.yml, pyproject.toml, requirements.txt, core/config.py, db/pool.py, pytest.ini, all docs/*.md, connectors tree, migrations count, .github/workflows/*).
- produced: 11-section plan for `wiki/entities/repos/eclipse_exp.md` covering intro, Architecture, Data Flow, Developer Guide, Deployment, Security Model, Database Schema & Migrations, Onboarding Pipeline, Connectors, Migration from Legacy Eclipse, See Also.
- decided: single wiki page (not multi-file); Data Flow applicable (data platform); summarise-and-link docs/* rather than copy; 3 extras (Security, Onboarding Pipeline, Connectors, Migration) added on top of the four mandatories because the repo warrants them. Size budget ~800–1200 lines; split triggers flagged.
- next: execution session (Sonnet) writes `entities/repos/eclipse_exp.md`, updates index.md, adds cross-reference paragraph to `entities/repos/core_api.md`, marks Execution ✅ in this tracker.
```

---

## flight-check — Approved Plan

**Plan session:** 2026-04-20 (Opus)
**Target wiki page:** `wiki/entities/repos/flight-check.md` (new page)
**Wiki index entry:** add under `Entities › Repos` alongside existing `eclipse`, `eclipse_exp`, `core_api`, `connector`, `custom-fusion-92-audience-api`.

> **Disambiguation note for the execution session:** three names collide here and must be kept separate on every page touched.
> - **`flight-check` (repo)** — this Next.js repo at `C:\Users\PaulRussell\repos\flight-check`. Wiki slug: `flight-check` (hyphen). Note `package.json` has `name: "eclipse"` — a copy-paste artefact from the scaffold; don't let that confuse identity.
> - **[[dax-media-app]]** — the *product* page (Fusion92-facing name: "DAX Media App" / "Flight Check App"). This repo **is** the frontend half of that product. Cross-reference heavily; do not duplicate the product-scope content.
> - **[[flight-check]]** — the ALDC *operational runbook* (Eclipse connector health / Snowflake task chain / data freshness). Completely different thing, same wiki-slug collision risk. The repo page should use an explicit See-Also callout pointing at that page.
>
> The wiki currently has no `entities/repos/flight-check.md`, so there is no naming collision on disk — but the repo slug `flight-check` and the operational-runbook page `processes/operations/flight-check.md` both live under the wiki root with similar-looking paths. Verify which you are linking to on every wikilink.

### Doc structure — single wiki page with these sections

All content goes into one page: `wiki/entities/repos/flight-check.md`. Sections below are in the order they should appear. Each section gives the execution session concrete, verified anchors (file paths, env var names, ports, endpoint paths) so the executor writes prose around facts rather than re-deriving them.

---

### Frontmatter

```yaml
---
tags: [entity, repo, flight-check, dax-media-app, fusion92, nextjs, react, frontend]
aliases: [flight-check repo, DAX Media App frontend, Flight Check frontend, dax.fusion92.eclipse.aldc.io]
sources: [repos/flight-check/README.md, repos/flight-check/package.json, repos/flight-check/Dockerfile, repos/flight-check/compose.yaml, repos/flight-check/compose_test.yaml, repos/flight-check/.env.template, repos/flight-check/authOptions.ts, repos/flight-check/next.config.mjs, repos/flight-check/pages/_app.tsx, repos/flight-check/pages/api/coreAPI.tsx, repos/flight-check/pages/api/auth/[...nextauth].tsx, repos/flight-check/pages/api/dax/calculations.ts, repos/flight-check/pages/api/dax/jobs/[job_id]/index.ts, repos/flight-check/pages/api/dax/jobs/[job_id]/export/index.ts, repos/flight-check/pages/api/dax/jobs/export.ts, repos/flight-check/pages/api/dax/flights/[flight_id].ts, repos/flight-check/pages/api/netsuite/publishers.ts, repos/flight-check/pages/api/netsuite/sync/enabled.ts, repos/flight-check/pages/api/netsuite/sync/syncpo.ts, repos/flight-check/pages/api/dios/audience/process.ts, repos/flight-check/pages/api/dios/projects/[projectName]/audiences.ts, repos/flight-check/pages/api/core/notificationCreate.tsx, repos/flight-check/pages/api/core/notificationUpdate.tsx, repos/flight-check/pages/api/core/sendWelcomeEmail.tsx, repos/flight-check/lib/dax/apiUtils.ts, repos/flight-check/lib/dax/types.ts, repos/flight-check/lib/dax/flights.ts, repos/flight-check/lib/dax/jobs.ts, repos/flight-check/lib/dax/notifications.ts, repos/flight-check/lib/dax/metricsTable.ts, repos/flight-check/lib/dax/exports.ts, repos/flight-check/metadata/README.MD, repos/flight-check/metadata/Job.json, repos/flight-check/metadata/admin.json, repos/flight-check/.github/workflows/PR_checks.yaml, repos/flight-check/.github/workflows/deploy_az_webapp.yaml]
created: 2026-04-20
updated: 2026-04-20
---
```

---

### Section 1 — Intro paragraph (top of page, no heading)

**Purpose:** Position `flight-check` against the [[dax-media-app]] product, [[eclipse]] host portal, and the three upstream APIs (core_api, DAX API, DIOS, NetSuite).

**Key content:**
- One-sentence identity: the **Next.js frontend** for the [[dax-media-app|DAX Media App]] — Fusion92's flight-management UI that replaced their legacy Firebase Flight Check app (Nov 2024). In production at `https://dax.fusion92.eclipse.aldc.io` (QA: `dax.fusion92.eclipse.aldc-ca-w1.com`, note `.com` not `.io`).
- Runs as an embedded iframe app inside the [[entities/repos/eclipse|eclipse portal]] — talks to the parent frame via postMessage (`pages/_app.tsx:64-76`, `NAVIGATION_CHANGE` / `PARENT_NAVIGATION_CHANGE` events).
- Proxies data calls server-side through four backends: [[core_api]] (via `pages/api/coreAPI.tsx` — identical pattern to [[entities/repos/eclipse|eclipse repo]]), the **DAX API** (a separate Azure-Functions backend, not documented elsewhere in the wiki yet — flag as a gap), **DIOS** (→ [[custom-fusion-92-audience-api]]), and **NetSuite workflow APIs** (via F92's Workflow service — `F92_NETSUITE_WORKFLOW_URL`).
- Repo is a fork/clone of the [[entities/repos/eclipse|eclipse repo]] scaffold — `package.json` still reads `"name": "eclipse"`. Many components (`AccountForm`, `ApplicationForm`, `BreadCrumb`, `Sidebar`, `UserForm`) are duplicated across the two repos. Call this out explicitly — any fix to shared-looking UI may need to land in both repos.
- Product-level scope (roles, statuses, phases, NetSuite sync, DIOS audience flow, buyer role, Phase 2) lives on [[dax-media-app]]; this page covers only the **repo/engineering** side.

---

### Section 2 — `## Architecture`

**Purpose:** Give a reader the mental map for the codebase in one screenful, then drill into the non-obvious bits.

**Sub-sections:**

- `### Repository layout` — table of top-level dirs with one-line purpose. Must include:
  | Path | Purpose |
  |---|---|
  | `pages/` | Pages Router routes. `[...slug].tsx` is the main dynamic app loader (25k lines). |
  | `pages/_app.tsx` | Provider stack + **iframe URL-sync `postMessage` bridge** to parent Eclipse portal |
  | `pages/api/coreAPI.tsx` | Universal proxy to [[core_api]] (mirrors the [[entities/repos/eclipse|eclipse]] pattern). Also cleans `NaN` out of response bodies before JSON parse (`coreAPI.tsx:29-35`) |
  | `pages/api/auth/[...nextauth].tsx` | NextAuth entry (empty `providers: []` — auth is inherited via shared session cookie with parent portal) |
  | `pages/api/core/` | `notificationCreate`, `notificationUpdate`, `sendWelcomeEmail` — routed through the coreAPI proxy |
  | `pages/api/dax/` | Thin proxies to the DAX API (`calculations`, `jobs/[job_id]`, `jobs/export`, `jobs/[job_id]/export`, `flights/[flight_id]`) using the `lib/dax/apiUtils.ts` helper |
  | `pages/api/netsuite/` | `publishers`, `sync/enabled`, `sync/syncpo` — proxies to the F92 NetSuite Workflow app |
  | `pages/api/dios/` | `audience/process`, `projects/[projectName]/audiences` — proxies to [[custom-fusion-92-audience-api]] (DIOS) |
  | `pages/settings.tsx` | User profile + `DaxMediaNotificationSettings` (pacing + status notifications, F92-only) |
  | `pages/security_and_groups.tsx` | Admin RBAC |
  | `pages/manage_team/` | Team admin (add_user, edit_user) |
  | `pages/account_settings/` | Account admin (internal users see full form, others see read-only) |
  | `components/` | ~38 top-level components + subdirs `Fusion92/`, `application/`, `flights/metricsTable/`, `inputs/`, `nonHTMLcomponents/`, `settings/` |
  | `components/Fusion92/` | F92-only: `DownloadAuditTrail`, `NetSuiteCreatePOButton`, `NetSuiteModal`, `NetSuiteSyncContext`, `NetSuiteSyncStatus`, `NetSuiteUnlockPOButton`, `NetSuiteUtils`, `ProcessAudienceFilesButton` |
  | `components/application/` | `FormBottomControls`, `FormFieldRenderer`, `FormModals`, `FormSectionsRenderer`, `FormStatusHeader`, `SearchedDropdown` — drive the metadata-driven form engine |
  | `components/flights/metricsTable/` | Pacing grid: `FlightMetricsTable`, `FlightMetrics`, `FlightMetricsTableDataRow`, `FlightMetricsTableActionRow`, `EditFlightMetricsRowModal`, `DeleteFlightMetricsRowModal`, `FilterFlightMetricsTableModal` |
  | `components/nonHTMLcomponents/` | Utilities: `ApplicationDataCleanup` (F92JobListFormat, F92FlightListFormat), `F92Theme`, `F92StatusTransitions`, `StringFormatting`, `constants` (F92 account IDs, Dataset ID, FLIGHT_CHECK_APPLICATION_TYPE_*), `UserAccountGroupAPI`, `Condition`, `util`, `ColorLogic` |
  | `components/settings/` | `DaxMediaNotificationSettings`, `NotificationSetting` |
  | `lib/dax/` | **DAX-API client lib** — `apiUtils.ts` (env loader + GET/POST helpers), `types.ts`, `flights.ts`, `jobs.ts`, `notifications.ts`, `metricsTable.ts`, `exports.ts`, `calculations` support |
  | `lib/dates.ts`, `lib/numbers.ts` | Date/number helpers (js-joda + date-fns + dayjs — three date libs coexist) |
  | `metadata/` | **JSON metadata files** that drive forms — `Job.json`, `job_details.json`, `admin.json`. Copy-pasted between QA and Prod per `metadata/README.MD` |
  | `authOptions.ts` | NextAuth config — **empty providers array**; cookie config reuses `__Secure-next-auth.session-token` on HTTPS, shared with parent portal via `domain: .${NEXTAUTH_URL hostname}` |
  | `next.config.mjs` | `reactStrictMode: true`, `output: "standalone"` |
  | `authOptions.ts` | Session/JWT claim shaping: `first_name`, `last_name`, `email`, `active_account(_name)`, `id`, `is_internal`, `is_admin`, `applications`, `groups`, `date_joined` — matches the [[entities/repos/eclipse|eclipse]] token shape |
  | `types/next-auth.d.tsx` | Type augmentation for those session fields (same as eclipse repo) |
  | `__test__/index.test.js` | **The only test file** — a trivial `expect(true).toBe(true)` placeholder. Effectively untested |
  | `__mock__/` | Jest mocks for static assets |
  | `.github/workflows/PR_checks.yaml` | Node 24 lint + format + `npm audit --omit=dev` |
  | `.github/workflows/deploy_az_webapp.yaml` | Manual `workflow_dispatch` → Azure Web App staging slot |
  | `Dockerfile`, `compose.yaml`, `compose_test.yaml` | Node 24 Alpine image, standalone build, `CHILD_SRC_ALLOWED_ORIGINS=flight-check.eclipse.aldc.io` env |
  | `.husky/pre-commit` | `npx lint-staged` |

- `### Tech stack` — table grouped by layer. Must include:

  | Layer | Choice | Notes |
  |---|---|---|
  | Framework | Next.js **16.1.6** (Pages Router) | **Newer than the [[entities/repos/eclipse|eclipse]] repo (14.2)** — flag this; upgrade may have been opportunistic. Pages Router, not App Router |
  | Node runtime | Node 24 (Dockerfile + both GitHub workflows) | Consistent across build/run, unlike eclipse repo |
  | Language | TypeScript 5.9 strict mode, `paths: {@/*: ./*}`, `target: ES2017` | |
  | UI primary | Mantine 7 (`@mantine/core`, `carousel`, `hooks`, `modals`, `notifications`) + NextUI 2 + flowbite-react + `@headlessui/react` | **Four UI kits coexist** — legacy migration residue. Most new code uses Mantine |
  | Styling | Tailwind 3.4 + SCSS + `postcss-preset-mantine` + `postcss-simple-vars` + `postcss-import` + CSS vars (`--font-light` etc.) | Theme tokens set via CSS vars for light/dark |
  | Auth | NextAuth 4 (`next-auth: ^4.24.7`) — **`providers: []`** | **Empty providers** — session cookie is issued by the parent Eclipse portal and shared cross-subdomain via the `__Secure-next-auth.session-token` cookie domain config. This app does *not* log users in on its own |
  | Analytics | PostHog (`posthog-js: ^1.364.4`) | **Hard-coded key** in `components/PostHogProvider.tsx:8` (`phc_LInuskdo6EBhTQv36KN1eJY4e9ZOb1BkQZLWWCoRU79`); env-var-based init is commented out. Flag as a security-hygiene issue |
  | HTTP | `fetch` (built-in) + `axios` (dependency only, few call-sites) | |
  | Date/time | `@js-joda/core`, `date-fns`, `dayjs`, `react-datepicker` | Three date libs — consolidate target |
  | CSV | `papaparse` | |
  | Table components | Custom `DataTable`, `F92DataTable`, `BasicTable`, `ApplicationTable` | |
  | Forms | `react-hook-form`-adjacent pattern (not used) — roll-your-own driven by metadata + `FormFieldRenderer.tsx` + `react-select` + `react-imask` + `imask` + `react-switch` | |
  | State | React local state only — no Redux/Zustand/React Query. `NetSuiteSyncContext` is the single React Context | |
  | Testing | Jest 29 + `@testing-library/react 16` + `jest-environment-jsdom`; next/jest preset | **One trivial test file** — effectively untested |
  | Lint/format | ESLint 8 + `@typescript-eslint/*` + `@stylistic/*` + `next/core-web-vitals` + Prettier 3.4; `lint:check` uses `--max-warnings=0` | Husky 9 + lint-staged 15 pre-commit |
  | Telemetry | PostHog + `NEXT_PUBLIC_POSTHOG_KEY`/`NEXT_PUBLIC_POSTHOG_HOST` in `.env.template` (shadowed by hard-code) | |

- `### How a request flows` — narrative walkthrough:
  1. Parent [[entities/repos/eclipse|eclipse]] portal loads `https://dax.fusion92.eclipse.aldc.io` in an iframe (governed by parent's `Content-Security-Policy: child-src …` set by the eclipse middleware). The `metadata/admin.json` `app_url` tells the parent portal where to point the iframe.
  2. Because the subdomain is `*.eclipse.aldc.io`, the shared NextAuth session cookie (`__Secure-next-auth.session-token`, cookie domain `.eclipse.aldc.io`) is sent with every request. `authOptions.cookies.sessionToken.options.domain = .${new URL(NEXTAUTH_URL).hostname}`.
  3. Next.js page mounts inside `_app.tsx`. The provider stack wraps every page: `SessionProvider` → `PostHogProviderWrapper` → `ThemeWrapper` → `MantineProvider` (custom `eclipseBlue` palette) → `ModalsProvider` → `NextUIProvider`.
  4. `_app.tsx` registers `postMessage` bridge (lines 44-204): intercepts `pushState`, `replaceState`, `popstate`, `hashchange` + a `MutationObserver` + a 2-second poll; on any URL change posts `{type: "NAVIGATION_CHANGE", path, timestamp}` to `window.parent`. Listens for `{type: "PARENT_NAVIGATION_CHANGE", path, source}` to sync itself when the user navigates in the outer portal. This is how the iframe keeps its URL in sync with the parent.
  5. Pages call `fetch("/api/coreAPI", { method: "POST", body: {url, message} })` for core_api data, or `/api/dax/*` for DAX data, or `/api/dios/*`, or `/api/netsuite/*`.
  6. Each server-side API route reads the relevant env-var-scoped credential (`api_token`, `DAX_API_MASTER_TOKEN`, `DIOS_API_KEY`, `F92_NETSUITE_SYNC_TOKEN`, `F92_NETSUITE_PUBLISHERS_TOKEN`), calls the upstream, normalises the response, and returns JSON to the client.

- `### Key abstractions` — one-paragraph each:
  - **`pages/api/coreAPI.tsx` — universal core_api proxy.** Reads `api_url` + `api_token`, POSTs to `${api_url}${url}`. Unusual: cleans `NaN` out of the response text before `JSON.parse` (lines 29-35 — `.replace(/:\s*NaN/g, ": null")` etc.) because core_api sometimes returns non-standard JSON. Exported as `apiCall()` for other server routes to reuse (see `api/core/sendWelcomeEmail.tsx` and `api/core/notificationCreate.tsx`).
  - **`lib/dax/apiUtils.ts` — DAX API client lib.** `get_dax_api_env()` reads `DAX_API_URL` + `DAX_API_MASTER_TOKEN` and throws if missing. `setup_dax_api_headers(key)` sets `x-functions-key` (Azure Functions key-based auth) + `Content-Type: application/json`. `dax_api_get(url, headers)` / `dax_api_post(url, body, headers)` return a unified `{status, data}` shape where `data` is either the payload or a `{error, error_description, error_context}` triple. Every `pages/api/dax/*` file is a thin wrapper that validates method, builds a URL with query params, calls these helpers, and forwards `{status, data}`.
  - **`authOptions.ts` — NextAuth config with empty providers.** Session/JWT callbacks shape the token from an external login (done upstream in the parent Eclipse portal). Cookie config sets `domain: .${NEXTAUTH_URL hostname}` so the session cookie is shared with `eclipse.aldc.io`. `trigger === "update"` branch supports account-switch (`active_account`, `active_account_name`, `is_admin`, names, email). No credentials/OAuth providers are registered here — call this out; it's counter-intuitive.
  - **`pages/_app.tsx` iframe bridge.** Bidirectional URL sync with parent via `postMessage`. Monkey-patches `window.history.pushState` + `replaceState`, intercepts `popstate`/`hashchange`, MutationObserver + 2-second interval fallback. On `PARENT_NAVIGATION_CHANGE` messages uses `window.history.replaceState` (not push) when `source === "popstate"` to avoid polluting the history stack.
  - **Metadata-driven forms.** `metadata/Job.json` + `metadata/job_details.json` + `metadata/admin.json` declare field order, sections, roles, and form layouts. `components/application/FormSectionsRenderer.tsx` + `FormFieldRenderer.tsx` interpret those JSON files and render forms at runtime. Also carries env-specific values — `account_id` differs between QA and Prod (per `metadata/README.MD`); `app_url` differs between `dax.fusion92.eclipse.aldc.io` (prod) and `dax.fusion92.eclipse.aldc-ca-w1.com` (QA, note `.com`). *This is a known deploy pitfall — see Deployment section.*
  - **`NetSuiteSyncContext` — single React Context for NetSuite sync.** Owns `isNetSuiteSyncing` + `isNetsuiteSyncEnabled`. `syncFlightWithNetSuite(accountId, flightId, onSuccess, onFailure)` POSTs to `/api/netsuite/sync/syncpo`, shows a Mantine modal during sync, routes to error or success modal on completion. Gated globally by `F92_NETSUITE_SYNC_ENABLED=true` (queried once at mount via `/api/netsuite/sync/enabled`).
  - **Flight Check application-type constants** (`components/nonHTMLcomponents/constants.tsx`) — two magic UUIDs (`FLIGHT_CHECK_APPLICATION_TYPE_FLIGHT = 9b9a62ab-...`, `FLIGHT_CHECK_APPLICATION_TYPE_JOB = 127edb5c-...`) + hard-coded `FUSION_92_ACCOUNT_IDS = ["0fc00e34", "f49f9aa3"]` + `FUSION_92_DATASET_ID`. These are used across many components. Values also appear in `metadata/Job.json:9` and `metadata/admin.json:59-62`.
  - **`FlightMetricsTable` + `processTableDataForDisplay`** (`lib/dax/metricsTable.ts`) — pacing grid. Handles 4 calculation sources: `dax` (daily, backend-derived), `smartsheet` (monthly, legacy, capped at `LAST_SMARTSHEET_YEAR`), `direct` (daily, UI aggregates to month), `manual_mixed` (user-entered). Date filter + sort + groupByMonth for direct source. `LAST_SMARTSHEET_YEAR` gates editability per row.
  - **`posthog-js` init at module-scope** (`components/PostHogProvider.tsx:7-25`). Fires before the `PostHogProviderWrapper` mounts. Config: `capture_pageview: false` (manual), `capture_pageleave: true`, `autocapture: true`, `person_profiles: identified_only`. User identified in the `useEffect` via `posthog.identify(user.id, {...})` when session resolves; re-identified on account-switch via `posthog.capture("$set", …)`.

- `### API surface (frontend → internal routes → upstream)` — table:

  | Internal route | Upstream | Credential env var |
  |---|---|---|
  | `POST /api/coreAPI` | `${api_url}` (core_api) | `api_token` |
  | `POST /api/core/notificationCreate` | core_api `notification/create` | via `api_token` |
  | `POST /api/core/notificationUpdate` | core_api `notification/update` | via `api_token` |
  | `POST /api/core/sendWelcomeEmail` | core_api `portal/newuseremail` (session-gated via getServerSession) | via `api_token` |
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

- `### Design decisions worth calling out`
  - **Embedded-iframe architecture** — the app does not stand alone; it expects a parent window that issues the NextAuth cookie and handles `postMessage` navigation events. Opening the raw URL in a fresh browser without a session routes back to the parent Eclipse portal login.
  - **Fork-of-eclipse** — shares components and cookie/session plumbing with [[entities/repos/eclipse|eclipse]]. Same proxy pattern (`api/coreAPI.tsx`), same session claims, same admin screens. Not a monorepo — pure duplication.
  - **Metadata-driven forms** — form structure is config in `metadata/*.json`, not React code. Lets Fusion92 add/remove fields without a deploy (when the change is within `options`/`options_inactive`). Env-specific values embedded in the same files (see Deployment pitfalls).
  - **Four-backend fan-out** — core_api, DAX API, DIOS, NetSuite Workflow. Different auth schemes (`Authorization` bearer vs `x-functions-key` vs `x-auth-apikey`). No unified retry/circuit-breaker; each route handles its own errors.
  - **Hard-coded PostHog key** — in code, not env. Env vars are in `.env.template` but commented-out in source. Call out during security review.
  - **Standalone Next.js build** — `output: "standalone"` produces `.next/standalone/` bundle; build script copies `.next/static` + `public/` into it (`package.json:build`). Matches the Azure Web App deploy target.

---

### Section 3 — `## Data Flow`

**Purpose:** Document how data enters, transforms, and exits this app. *Applicability:* this is a UI repo, **not** a data-pipeline repo — data flow here = how the frontend fetches/submits data through its four upstream services and renders it. Worth a section because the multi-backend fan-out is the non-obvious part of this codebase.

**Sub-sections:**

- `### Data inputs — where job/flight data originates`
  - **Jobs + flights + application metadata** — [[core_api]] / [[CosmosDB]]. Read via `/api/coreAPI` → `application/list`, `application/read`, `application/heirarchy` [sic], `application/readmetadata`. Writes via `application/create`, `application/update`, `application/delete`.
  - **Flight calculations (pacing, actuals, planned, metrics table)** — **DAX API** (Azure Functions backend not documented elsewhere; `DAX_API_URL` in `.env.template`). Fetched via `/api/dax/calculations` (POST) or as `add-calc=true` query params on `/api/dax/jobs/[job_id]` and `/api/dax/flights/[flight_id]`. Returns `FlightCalculations` shape (see `lib/dax/types.ts`).
  - **NetSuite publisher names** (for the "Publisher Name" dropdown on Direct Partner flights) — F92's NetSuite Workflow app via `/api/netsuite/publishers?account_id=…`.
  - **DIOS audiences** — DIOS via `/api/dios/projects/[projectName]/audiences`. Drives the "DIOS Audience Name" dropdown.
  - **Notifications docs** — core_api `notification/read/list` via session-authenticated routes.
  - **User/account/RBAC** — core_api via `/api/coreAPI`.
  - **Session** — NextAuth session cookie issued by the parent Eclipse portal, shared via `__Secure-next-auth.session-token` at cookie domain `.eclipse.aldc.io`.

- `### Data outputs — where user actions go`
  - **Job/flight create/update/delete** — back to core_api via `/api/coreAPI` → `application/create|update|delete`.
  - **NetSuite PO sync** — `/api/netsuite/sync/syncpo` triggers F92's workflow, which creates/updates the PO in NetSuite. Prerequisites: flight in correct status; `F92_NETSUITE_SYNC_ENABLED=true`; status transitions managed by `F92StatusTransitions.tsx`. Cross-reference [[dax-media-app]] § NetSuite PO Sync.
  - **DIOS audience processing** — `/api/dios/audience/process` forwards raw body directly (no transformation) to DIOS.
  - **Notification settings** — `/api/core/notificationCreate` + `/api/core/notificationUpdate` → core_api `notification/create`|`update` → [[CosmosDB]].
  - **Welcome email on new user creation** — `/api/core/sendWelcomeEmail` → core_api `portal/newuseremail` (session-gated via `getServerSession`).
  - **Analytics** — PostHog (`posthog-js`) direct from browser to `https://us.i.posthog.com/`.

- `### Transformations inside this app`
  - **Calculation load** — `lib/dax/flights.ts:loadFlightCalculationData()` normalises DAX API response: coerces string dates to `LocalDate` (`@js-joda`), fills missing values with typed zeros, **multiplies `pacing` by 100** (backend ships a proportion, UI treats it as percent — line 62). A TODO exists flagging this should be backend-normalised.
  - **Job load** — `lib/dax/jobs.ts:loadJobDataApiResponse()` converts `created` string → `Date`.
  - **Metrics-table display pipeline** — `processTableDataForDisplay()`:
    1. `filterAndSortTableData()` — filter by date range (keep rows that *overlap* the filter dates), sort by start date asc/desc.
    2. `groupDailyTableDataByMonth()` — **only when `tableSource === "direct"`**, aggregates daily rows into `year-month` buckets (`dax`/`smartsheet`/`manual_mixed` rows are left at their native grain).
  - **List formatters** — `F92JobListFormat` / `F92FlightListFormat` in `components/nonHTMLcomponents/ApplicationDataCleanup.tsx` prepare server rows for the `F92DataTable` (pacing colour coding, status chiclets, action buttons).
  - **NaN-stripping in the core_api proxy** — `pages/api/coreAPI.tsx:29-35` rewrites raw `NaN` tokens in the response text to `null` before `JSON.parse`. Band-aid for non-RFC JSON shipped by core_api.

- `### Storage in this app`
  - **No durable storage.** All data lives upstream.
  - **Cookies:** NextAuth session cookie (`__Secure-next-auth.session-token` on HTTPS, `next-auth.session-token` on HTTP) + NextAuth CSRF + callback-url cookies. `cookies-next` is a dependency but not actively used for app state.
  - **LocalStorage:** Mantine color-scheme preference (via MantineProvider), `ThemeWrapper` sets `theme` in React state; persisted to `cookies-next`.
  - **In-memory only:** All page state. No React Query, no SWR.

- `### Audit + observability`
  - **F92 audit trail download** — `components/Fusion92/DownloadAuditTrail.tsx` exports a CSV/Excel from core_api records. UI-only.
  - **PostHog** — `$pageview` on route change, `posthog.identify(user.id, …)` on session resolve, `posthog.capture("$set", …)` on account switch. No backend spans.
  - **No structured logs.** API routes use `console.error` only. No correlation IDs.

---

### Section 4 — `## Developer Guide`

**Purpose:** Get a developer from clean machine to running local app + able to exercise the full UI against a real backend.

**Sub-sections:**

- `### Prerequisites`
  - Node.js **24.x** (Dockerfile + both GitHub workflows pin `node:24-alpine` / `NODE_VERSION: 24.x`).
  - npm (uses `npm ci` in workflow and Dockerfile).
  - Docker + Docker Compose (optional — only needed for full-stack parity with production image build).
  - Access to core_api, DAX API, DIOS, NetSuite-Workflow keys (vault pointers in Deployment section).
  - A NextAuth-signed session cookie — most local dev flows rely on *logging in on the parent Eclipse portal* and then running this app on a same-domain subdomain. Explain the cookie-domain constraint.

- `### Environment variables`
  Source: `.env.template`. Populate as `.env.local` (compose_test) or `.env.production` (compose). Required vars:

  | Var | Purpose |
  |---|---|
  | `api_url` | Base URL for [[core_api]] (e.g. `https://aldcprodfnapcore1c01.azurewebsites.net/api/`) |
  | `api_token` | Bearer token for core_api — sent as raw `Authorization: <token>` (not `Bearer <token>`, see `coreAPI.tsx:16`) |
  | `STAC_NAME`, `STAC_KEY` | Legacy Azure Storage keys (unused in current code paths — flag as possibly-dead vars) |
  | `NEXTAUTH_URL` | Full URL of this app (e.g. `https://dax.fusion92.eclipse.aldc.io`) — drives cookie prefix (`__Secure-` only on HTTPS) and cookie domain |
  | `NEXTAUTH_SECRET` | JWT signing secret — **must match the parent Eclipse portal** so session cookies interoperate |
  | `F92_NOTIFICATION_KEY`, `F92_NOTIFICATION_URL` | F92 email notification service (used by `DaxMediaNotificationSettings`) |
  | `F92_NETSUITE_SYNC_ENABLED` | `"true"`/`"false"` toggle read by `/api/netsuite/sync/enabled` |
  | `F92_NETSUITE_WORKFLOW_URL` | Base URL for F92's NetSuite Workflow App |
  | `F92_NETSUITE_SYNC_TOKEN` | `x-functions-key` for `/api/f92_netsuite_po_sync` |
  | `F92_NETSUITE_PUBLISHERS_TOKEN` | `x-functions-key` for `/api/f92_netsuite_publishers` |
  | `DIOS_API_URL`, `DIOS_API_KEY` | Points at [[custom-fusion-92-audience-api]]; sent as `x-auth-apikey` |
  | `DAX_API_URL`, `DAX_API_MASTER_TOKEN` | DAX API Azure Functions backend |
  | `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST` | **Currently unused** — hard-coded in `components/PostHogProvider.tsx:8-9` |
  | `ECLIPSE_URL` | Referenced in `pages/api/core/sendWelcomeEmail.tsx:44` but missing from `.env.template` — flag as a gap |
  | `CHILD_SRC_ALLOWED_ORIGINS` | Set at container level in `compose.yaml` (not app code); passed to parent portal's CSP allow-list |

- `### Local setup — Option A: run against real backends`
  1. `git clone` + `cd flight-check`.
  2. `nvm use 24` (or install Node 24).
  3. `npm install`.
  4. Copy `.env.template` to `.env.local`. Fill in each value from `vault/credentials.md` (flag: credentials for DAX API + DIOS + NetSuite keys should be extracted into `vault/` per wiki rules — may not all be there yet).
  5. Set `NEXTAUTH_URL` to a localhost URL on the `eclipse.aldc.io` domain scheme (or an `eclipse-local.aldc.io` loopback) to make the shared cookie resolve. *Or* set `NEXTAUTH_URL=http://localhost:3100` and log in directly — but without cookie sharing you won't have a session.
  6. `npm run dev` — serves on **port 3100** (`package.json:scripts.dev`). Note: **not 3000** like most Next apps; explain why (3000 reserved for the parent Eclipse dev server).
  7. Visit `http://localhost:3100`. Expect redirect to parent portal login if no session cookie is present.

- `### Local setup — Option B: Docker Compose against prebuilt image`
  - `compose_test.yaml` pulls `ghcr.io/aldc-io/flight-check:${FLIGHT_CHECK_VERSION}` and binds `.env.local`. Use when you want to run the production image locally.
  - `compose.yaml` is the production compose (requires GHCR access + `.env.production`).
  - Command: `FLIGHT_CHECK_VERSION=<tag> docker compose -f compose_test.yaml up`.
  - App on host port 3000 (compose_test) or 3100 (compose).

- `### Local setup — Option C: build the Docker image from source`
  - `docker build -t flight-check:local .` (uses Dockerfile: multi-stage, Node 24 Alpine, installs deps in `builder`, copies `.next/standalone` + static + public into final runner, runs as `nextjs:nodejs` non-root).
  - Note: Dockerfile healthcheck is **not present** (unlike eclipse_exp's container). Container App platform relies on external healthcheck.

- `### Running tests + lint`
  - `npm run lint` — ESLint `--fix --max-warnings=0`.
  - `npm run lint:check` — same without fix (runs in `PR_checks.yaml`).
  - `npm run format` / `npm run format:check` — Prettier.
  - `npm test` — Jest (`jest.config.ts` uses `next/jest` + `jsdom` + `coverageProvider: "v8"`). **Only one trivial test** — there is effectively nothing to run.
  - `npm run test:watch` — Jest watch mode.
  - Pre-commit hook runs `lint-staged` — ESLint fix on changed `.{js,jsx,ts,tsx}` + Prettier on `.{js,jsx,ts,tsx,css,md,html,json}`.

- `### Debugging`
  - **Browser console** — PostHog logs in dev (`posthog.debug()` on `NODE_ENV === "development"`, `PostHogProvider.tsx:22`).
  - **Session inspection** — visit `/api/auth/session` to see the JWT claims resolved for the current cookie.
  - **Proxy-response inspection** — the coreAPI/dax/dios/netsuite handlers all `console.error` failures to server logs. For local dev, watch the terminal running `npm run dev`.
  - **Metadata-form issues** — check `metadata/Job.json` / `job_details.json` for the field definition; env-specific `account_id` + `app_url` mismatches manifest as forms binding to the wrong account.
  - **PostMessage bridge** — use browser DevTools → Application → Frames to inspect iframe context; add `console.log` around `handleMessage` in `_app.tsx` to trace navigation sync.

- `### Common pitfalls`
  - **Dev port is 3100**, not 3000. Don't override.
  - **Empty NextAuth providers.** If you're trying to log in from this app directly, you can't. The session must be issued by the parent Eclipse portal. For fully isolated local dev you'd have to mint a JWT by hand and set the cookie manually.
  - **Cookie domain binds the dev environment to `*.eclipse.aldc.io` behaviour.** `NEXTAUTH_URL` hostname controls `cookies.sessionToken.options.domain`. If set to `localhost`, domain becomes `.localhost` which most browsers reject — you may see session resolve as null.
  - **Metadata env swap.** `metadata/Job.json` + `job_details.json` + `admin.json` carry Prod-only `account_id` (`0fc00e34`) and Prod-only `app_url`. Running these verbatim against QA will bind forms to the wrong account. Per `metadata/README.MD`, swap `account_id` to the QA value + flip `app_url` to `.com` domain before pasting into QA CosmosDB.
  - **NaN in API responses.** `coreAPI.tsx` silently scrubs `NaN` to `null` — if you're debugging "why is X null", check the raw response first.
  - **Hard-coded PostHog key** (`components/PostHogProvider.tsx:8`) fires in all environments including local dev. Events from `localhost` will land in the production PostHog project. Consider stubbing or disabling for local work.
  - **Four UI libraries coexist.** Changing a button/modal, check whether it's Mantine, NextUI, flowbite, or headlessui — each has different props and theming.
  - **Three date libraries coexist** (`@js-joda/core`, `date-fns`, `dayjs`). `lib/dax/types.ts` uses `LocalDate`; `metricsTable.ts` composes them; many components still use `dayjs`. Be careful converting.
  - **`[...slug].tsx` is 25k lines** — the main dynamic-route handler for the whole app, touches most state. Don't try to refactor it in a single PR.
  - **`package.json` name is `"eclipse"`** — don't be surprised when `npm run` log lines say `eclipse`. Left over from fork.

---

### Section 5 — `## Deployment`

**Purpose:** How a commit becomes a production revision, plus the metadata-copy step that has no automation.

**Sub-sections:**

- `### Infra at a glance` — table:

  | Thing | Value | Source |
  |---|---|---|
  | Production URL | `https://dax.fusion92.eclipse.aldc.io` | `metadata/Job.json:8`, `metadata/README.MD:41` |
  | QA URL | `https://dax.fusion92.eclipse.aldc-ca-w1.com` (**`.com`**, not `.io`) | `metadata/README.MD:42` |
  | Deploy target | Azure Web App, staging slot | `deploy_az_webapp.yaml:48` |
  | App-Service name (prod) | Per-env `vars.AZURE_APP_SERVICE_NAME` | `deploy_az_webapp.yaml:46` |
  | Azure auth | OIDC federated (`azure/login@v2`) | `deploy_az_webapp.yaml:28-31` |
  | Container image (compose-deploy path) | `ghcr.io/aldc-io/flight-check:${FLIGHT_CHECK_VERSION}` | `compose.yaml:3` |
  | Base image | `node:24-alpine` (multi-stage) | `Dockerfile:3` |
  | Parent CSP allow-list | `CHILD_SRC_ALLOWED_ORIGINS=flight-check.eclipse.aldc.io` | `compose.yaml:16` |
  | Container user | `nextjs:nodejs` (UID/GID 1001) non-root | `Dockerfile:31-33` |
  | CSP child-src set by | *parent* Eclipse portal middleware, not this app | cross-ref [[entities/repos/eclipse|eclipse]] |

- `### Environment model`
  - **Prod** — `dax.fusion92.eclipse.aldc.io`; resolves to production Azure Web App (`eclipse.aldc.io` subscription, see [[azure-environments]]).
  - **QA** — `dax.fusion92.eclipse.aldc-ca-w1.com` (**different TLD** — `.com`, noted in `metadata/README.MD`). Flag as a rename target; the TLD mismatch is a source of confusion.
  - **Local** — port 3100 via `npm run dev`, or the prebuilt image via `compose_test.yaml`.
  - No separate "dev" environment beyond developer laptops.

- `### CI — PR checks`
  Reference: `.github/workflows/PR_checks.yaml` (triggered on `pull_request.synchronize`):
  1. Checkout.
  2. Setup Node 24.
  3. `npm install`.
  4. `npm audit --omit=dev` (runtime deps only).
  5. `npm run lint:check` (`--max-warnings=0`, hard fail on any warning).
  6. `npm run format:check` (Prettier).
  No tests gate the PR (there are no real tests).
  No TypeScript-only gate (`tsc --noEmit`) — the build step does type-checking implicitly via `next build` when deploy runs.
  Note: workflow triggers on `synchronize` only — **not on `opened`**. Opening a PR without pushing more commits skips the check; this is a bug/oversight.

- `### CD — manual Azure Web App deploy`
  Reference: `.github/workflows/deploy_az_webapp.yaml` (triggered by `workflow_dispatch` with environment input):
  1. Checkout.
  2. Azure login via OIDC (`client-id`, `tenant-id`, `subscription-id` from secrets).
  3. Setup Node 24.
  4. `npm install && npm run build` (build script runs `next build` + copies `.next/static` into `.next/standalone/.next/` + copies `public/` into `.next/standalone/`).
  5. `azure/webapps-deploy@v3` with `package: ./.next/standalone`, `slot-name: stage`.
  6. `az logout`.
  **Staging-slot model** — deploys land on `stage` slot; a manual slot-swap in Azure Portal promotes to production. Cross-reference [[eclipse-azure-deployment]] which documents the same slot-swap pattern for eclipse/core_api.

- `### GHCR image path (alt deploy route)`
  `compose.yaml` implies an alternative deploy route: building the Docker image and pushing to `ghcr.io/aldc-io/flight-check`. The `deploy_az_webapp.yaml` workflow does **not** push to GHCR — it deploys the standalone bundle directly. So the GHCR path is likely:
  - Used for non-Azure-Web-App hosts (Docker on a VM, Portainer) per [[connector-docker-deployment]]-style pattern, or
  - A residual from an older deploy model.
  Flag this as a gap in documentation — the actual image-publish step isn't in `.github/workflows/` on `main`. Execution session should verify and note accordingly.

- `### Deploy steps — end-to-end`
  1. Merge PR into `main`.
  2. GitHub UI → Actions → "Deploy to Azure App Service" → Run workflow → pick environment (prod/QA).
  3. Wait for workflow to complete — build + deploy to `stage` slot.
  4. Smoke test the staged app (direct URL to `<appname>-stage.azurewebsites.net` or similar — not canonically documented; verify with Vlad).
  5. In Azure Portal → App Service → Deployment slots → Swap staging ↔ production.
  6. **If the deploy touches `metadata/*.json`** (changes to form structure, fields, admin layout), additionally copy the JSON into CosmosDB for the target environment per `metadata/README.MD`:
     - Verify `options` and `options_inactive` fields match the target env — if not, copy Prod options into QA first to keep parity.
     - **Update `account_id`** to the target env's Fusion account ID (different between ALDC QA and Prod Fusion).
     - **Update `app_url`** to the target env's URL (`.io` for Prod, `.com` for QA).
     - Paste into the metadata container of the target CosmosDB (via Cosmos Data Explorer).

- `### Rollback`
  - **Azure Web App** — swap staging ↔ production again to return the previous revision to production. This matches the [[eclipse-azure-deployment]] playbook.
  - **Metadata** — metadata is versioned only in git (for in-repo changes); CosmosDB containers don't maintain history automatically. A rollback requires pasting the previous JSON back in manually. Mitigation: commit the JSON changes to the repo *before* pasting into Cosmos so git history acts as the rollback source.
  - **No DB migrations** to unwind — this app has no DB.

- `### Secrets storage`
  - GitHub Actions secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` (OIDC). App-Service-level env vars in Azure Portal for `api_token`, `DAX_API_MASTER_TOKEN`, `DIOS_API_KEY`, `F92_NETSUITE_*_TOKEN`, `NEXTAUTH_SECRET`.
  - Cross-reference [[vault/credentials]] for the canonical source.
  - **Hard-coded PostHog key** in `components/PostHogProvider.tsx:8` — not a secret per PostHog's model (public project key) but worth flagging; should move to env var.

- `### Observability in prod`
  - **PostHog** — pageviews, autocapture, identified user events. Dashboard owned by Karen Prete (per [[dax-media-app]]). No link to Azure Application Insights.
  - **Azure App Service logs** — accessible via Azure Portal. No centralised log aggregation (no Application Insights, no Log Analytics Workspace integration configured in code).
  - **No healthcheck endpoint in the app.** No `/health` or `/ping` — Azure App Service probes the default `/`.
  - **No Prometheus** / no structured logs.

---

### Section 6 — `## Integrations`

**Purpose:** One place to see every external system this app talks to and the surface area. (Condenses the separate tables above into a single reference table for lookups.)

**Key content:** table columns `System | Direction | Endpoint | Auth | Owner page`. Rows:
- [[core_api]] — in/out — `/api/coreAPI` proxy → `${api_url}{url}` — bearer `api_token` — [[core_api]]
- DAX API (TODO: create wiki page) — in/out — `/api/dax/*` → `${DAX_API_URL}/*` — `x-functions-key: DAX_API_MASTER_TOKEN` — no wiki page yet
- [[custom-fusion-92-audience-api]] (DIOS) — out — `/api/dios/*` → `${DIOS_API_URL}/*` — `x-auth-apikey: DIOS_API_KEY` — [[custom-fusion-92-audience-api]]
- F92 NetSuite Workflow (TODO: verify whether this is on-prem at Fusion92 or Azure-hosted) — out — `/api/netsuite/*` → `${F92_NETSUITE_WORKFLOW_URL}/api/*` — `x-functions-key: F92_NETSUITE_*_TOKEN` — flag as doc gap
- [[entities/repos/eclipse|eclipse portal]] — in — postMessage bridge — parent-frame cookie (`__Secure-next-auth.session-token`, domain `.eclipse.aldc.io`) — [[entities/repos/eclipse|eclipse]]
- PostHog — out — `https://us.i.posthog.com/` — hard-coded project key — no wiki page yet
- [[CosmosDB]] (indirect via core_api) — via core_api only — reads/writes `metadata/*` (when deploy re-seeds), jobs, flights, users, notifications — [[CosmosDB]]
- F92 email notifications (`F92_NOTIFICATION_URL` + `F92_NOTIFICATION_KEY`) — out — unknown endpoint — no wiki page yet; flag as gap

---

### Section 7 — `## Known issues / tech debt`

**Purpose:** Make the backlog visible on the wiki so incoming work has context. Lift from source observations + cross-link `[[dax-media-app]]` where appropriate.

**Key content:**
- `package.json` `name: "eclipse"` — fork-scaffold leftover; rename to `"flight-check"`.
- Hard-coded PostHog key in `components/PostHogProvider.tsx:8` — should move to env var; env vars are already declared in `.env.template`.
- `NaN` scrubbing band-aid in `coreAPI.tsx` — proper fix belongs in core_api's response serialisation.
- Four UI kits (Mantine + NextUI + flowbite-react + headlessui). Consolidation in progress toward Mantine.
- Three date libs (`@js-joda/core`, `date-fns`, `dayjs`).
- **One trivial test file** — zero meaningful test coverage. No Playwright/Cypress/Storybook.
- `pacing * 100` hack in `lib/dax/flights.ts:62` — backend should return percent.
- Metadata env-swap is manual — `account_id` and `app_url` differ between QA and Prod (`metadata/README.MD`). Candidate for Cosmos-managed env-tagged records.
- `ECLIPSE_URL` env var referenced in `sendWelcomeEmail.tsx:44` but not in `.env.template`.
- `STAC_NAME` + `STAC_KEY` in `.env.template` — **no references in source**; likely dead vars.
- `PR_checks.yaml` triggers on `synchronize` only, not `opened` — first push of a new PR is unchecked.
- No healthcheck endpoint in the app.
- No Application Insights / Log Analytics integration.
- `[...slug].tsx` is 25k lines; `ApplicationTable.tsx` 99k, `AccountForm.tsx` 106k, `F92DataTable.tsx` 40k — refactor candidates.

---

### Section 8 — `## See Also`

Wikilinks to related pages. Must include:
- [[dax-media-app]] — the product this repo implements. Defer product-scope / roles / UAT history / Phase 2 to that page.
- [[entities/repos/eclipse|eclipse]] — the host portal this app iframes into; shares NextAuth session cookie + most UI components.
- [[core_api]] — primary backend. Every `/api/coreAPI` + `/api/core/*` + `/api/netsuite/sync/enabled` + `/api/netsuite/publishers` flow routes through (or directly reads the env that drives) this.
- [[custom-fusion-92-audience-api]] — the DIOS API this app proxies to for audience data.
- [[fusion92]] — the client.
- [[fusion92-platform-ids]] — platform ID mapping that drives data matching used in this app.
- [[fusion92-data-architecture]] — upstream Snowflake setup for Fusion92.
- [[flight-check]] (processes/operations) — **NOT this repo** — ALDC's operational validation runbook. Disambiguation callout.
- [[eclipse-azure-deployment]] — the deploy runbook pattern this repo follows.
- [[github-actions]] — CI/CD pattern.
- [[azure-environments]] — Azure subscription → environment mapping.
- [[Eclipse]] (platform, tool page) — the broader Eclipse platform concept.
- [[CosmosDB]] — indirect storage (metadata, jobs, flights).

---

## Judgment calls

- **`## Data Flow` IS applicable, but reframed.** This is a frontend/UI repo with no data pipeline, *but* the multi-backend fan-out (core_api + DAX + DIOS + NetSuite Workflow) is the single most non-obvious thing about the repo. The data-flow section is worth including, framed as "how data flows through this UI", not "how this UI is part of a pipeline."
- **Single wiki page is correct.** Size target: ~600–900 lines. Smaller than eclipse_exp because this is a UI repo without migrations/connectors/RLS/auth systems to document. If the executor finds it overruns 1000 lines, collapse Section 6 Integrations (the table is already duplicated within Sections 2–3).
- **Do not duplicate [[dax-media-app]] content.** That page already documents product scope (roles, statuses, Phase 1 timeline, NetSuite sync flow, DIOS integration at the feature level, ID mapping). The repo page should **reference** product behaviours and focus on *how the code implements them* (endpoints, component names, env vars, proxies).
- **Disambiguation is load-bearing.** The existing wiki has:
  - `entities/projects/dax-media-app.md` — the product (has alias "Flight Check App")
  - `processes/operations/flight-check.md` — the ALDC runbook for data-pipeline validation
  - and now `entities/repos/flight-check.md` — this page.
  All three carry the "flight check" phrase. Every cross-page link must be explicit about which is which. Leave a disambiguation block at the top of this page and propose adding matching disambiguation blocks to the other two pages during execution.
- **The DAX API is a missing wiki entity.** This repo talks to an Azure-Functions backend at `DAX_API_URL` that isn't documented anywhere in the wiki. The execution session should create a stub page at `entities/tools/dax-api.md` (or `entities/repos/dax-api.md` if there's a matching repo — verify before creating) and cross-link. Scope of the stub: host, auth mechanism, endpoint catalogue (calculations, jobs, jobs/export, jobs/{id}/export, flights/{id}), known open questions. This is out-of-scope for the *current* plan and into the execution session's judgement.
- **F92 NetSuite Workflow** is another undocumented integration. Recommend flagging it but *not* creating a page in this workstream — it's a Fusion92-owned service, not an ALDC repo. Leave it as a `TODO: document` in the Integrations table.
- **PostHog is also undocumented** as a tool page. Low priority — standard SaaS analytics tool. Out of scope for this plan.
- **Update the `dax-media-app` product page during execution** to add a "Repo" link pointing at the new `entities/repos/flight-check.md`. Keep the change surgical (one line under "## See Also" or similar).
- **Update the existing [[flight-check]] (operations) page** to add a disambiguation note at the top pointing to this new repo page. Surgical edit.
- **No files written into the repo itself.** Wiki only — per boot prompt and repo CLAUDE.md conventions (this repo has no CLAUDE.md at repo root).
- **No `.md` duplicates of `metadata/README.MD`** — the README inside the repo is the source of truth for the env-swap caveats; the wiki summarises + links to file path, not copies.
- **Execution session should verify whether `components/PostHogProvider.tsx` key is actually production or a placeholder** before flagging it as a credentials leak — PostHog project keys are designed to be public, so this may be intentional. Still worth calling out stylistically.

### Session Log entry to add (executor should append after writing the page)

```
### 2026-04-20 — flight-check plan session complete

- did: read repo (README, package.json, Dockerfile, compose files, .env.template, authOptions.ts, next.config.mjs, pages/_app.tsx, pages/api/coreAPI.tsx, pages/api/auth/*, pages/api/dax/*, pages/api/dios/*, pages/api/netsuite/*, pages/api/core/*, lib/dax/*, metadata/README.MD + Job.json + admin.json, components/Fusion92/NetSuiteSyncContext.tsx, components/PostHogProvider.tsx, components/Sidebar.tsx, components/F92ApplicationLanding.tsx, components/nonHTMLcomponents/constants.tsx, .github/workflows/*, .husky/pre-commit, __test__/index.test.js, tsconfig.json, jest.config.ts, tailwind.config.ts).
- produced: 8-section plan for `wiki/entities/repos/flight-check.md` covering intro, Architecture, Data Flow, Developer Guide, Deployment, Integrations, Known issues / tech debt, See Also.
- decided: single wiki page (~600–900 lines); Data Flow applicable (reframed as multi-backend fan-out); defer product-level scope to [[dax-media-app]]; disambiguation block is load-bearing because three wiki pages share the "flight check" phrase (repo / product / ops runbook). Flagged DAX API, F92 NetSuite Workflow, PostHog as wiki gaps.
- next: execution session (Sonnet) writes `entities/repos/flight-check.md`, updates index.md with a "Repo" entry, adds a one-line "See Also" cross-link to both `entities/projects/dax-media-app.md` and `processes/operations/flight-check.md` pointing to the new page, marks Execution ✅ in this tracker.
```

---

## custom-fusion-92-audience-api — Approved Plan

**Scope:** update existing `wiki/entities/repos/custom-fusion-92-audience-api.md` — preserve integration/business content, layer in code-level Architecture, Data Flow (service-level), API Reference, Platform Specifications table, Developer Guide, expanded Deployment, and Tech Debt sections.

### `wiki/entities/repos/custom-fusion-92-audience-api.md` (update existing)

**Purpose:** single repo-documentation page for the DIOS-to-DAX audience API — what it does, how it's built, how to run it locally, how it deploys, endpoint/platform reference, and the existing integration context.

**Frontmatter updates:**
- `updated: 2026-04-20`
- Append `sources:` entry for repo review (README, main.py, file_specification.py, file_handler.py, gunicorn.conf.py, Dockerfile, requirements.txt, client/client.py, generate_sample_file.py)
- Tags unchanged — already covers `entity, repo, fusion92, aldc, api, on-prem`

**Target size:** ~500–700 lines.

**Sections (in order):**

- ## Intro paragraph (**keep existing** — name, purpose, repo URL `https://github.com/ALDC-io/custom-fusion-92-audience-api`, prod URL `https://audience-fusion92-app.aldc-ca-w1.com/`)

- ## What it does (**keep existing** — DIOS → per-platform transform + Nextcloud export, with Reddit/Meta examples and the "DIOS-to-DAX" naming note)

- ## Architecture (**NEW**)
  - **Tech stack**: Python 3.11+ · FastAPI + Pydantic · Gunicorn with UvicornWorker · pandas · nextcloud-api-wrapper · dotenv. From `requirements.txt`.
  - **Entry points**: `main:app` FastAPI app; Gunicorn runs it per `gunicorn.conf.py` (workers = `2 * cpu_count() + 1`, `timeout=0`, `timeout_keep_alive=600`, `max_requests=200` with `jitter=50`, `limit_request_fields=32768`, bind `0.0.0.0:80`).
  - **Request auth**: single API key in `x-auth-apikey` header, validated against `X_AUTH_APIKEY` env by `authorize()` at `main.py:80`. No per-user auth, no rate limit.
  - **Key abstractions**:
    - `FileHandler` ABC (`file_handler.py:23`) with `NextcloudFileHandler` (WebDAV, 2-retry wrapper in `_with_retry`) and `LocalFileHandler` (shutil/pathlib). Swap point: `create_file_handler()` in `main.py:47-49` — hard-coded to Nextcloud.
    - `FileSpecification` (`file_specification.py:20`) — declarative per-platform output config: `audience1_schema` / `audience2_schema`, `hash_fields` (SHA256 list, default `["email"]`), `is_single_column`, `is_headerless`, `min_row_count`, `max_row_count`, `file_size_limit_bytes` (hard-capped at 100 MB by `FILE_SIZE_LIMIT_BYTES`), `file_suffix`, `combined_columns`, `extra_fields`. The module-level `file_specifications: list[FileSpecification]` (`file_specification.py:124`) is the source of truth for all platform output behaviour — adding a platform is a list append.
    - `Platform` enum (`file_specification.py:4`) — 14 values. Snapchat has 3 specs (EMAIL/PHONE/MAID via `file_suffix`), Reddit has 2 (EMAIL/MAID). **Platform count ≠ spec count.**
  - **Request lifecycle**: 202-Accepted pattern — validate → register upload → schedule FastAPI `BackgroundTasks` → return immediately. Heavy work runs after response.
  - **In-memory state**: `in_progress_uploads: set[tuple[str, str]]` (`main.py:29`) rejects duplicate uploads with 202. **Non-obvious limitation:** per-process. With `workers = 2*CPU+1` Gunicorn workers, duplicate-rejection is best-effort, not guaranteed across workers.
  - **Transform pipeline** (`format_audience_data`, `main.py:157`):
    1. Temp path + staging dir created
    2. Per `FileSpecification`: `min_row_count` guard → single-column vs multi-column branches (hash → rename → combine → filter → dedup) → split by `max_row_count` → write CSV → size-check → further split by `file_size_limit_bytes` (bounded by `file_count_limit`) → write chunks `{platform}{suffix}_{N}.csv`
    3. Atomic move: temp → real staging (deletes existing target first)
  - **`audience2` pivot**: input is long-form `{RECD_LUID, TYPE, VALUE}`. `build_audience2_dataframe` (`main.py:104`) pivots on `TYPE`; only types in current spec's `audience2_schema.keys()` are kept — filters out `HARDWARE_TV`, `UID2`, `TTD`, `HEM_MD5` etc.
  - **Error handling reality**: `ValidationError` → 400; `Exception` → 500 with schema hint on `/upload`. `process_audience_data` logs errors but returns — failures silent to caller. `# FIXME: Better error messages` comments at `main.py:408` and `main.py:478`.

- ## Data Flow (**NEW**) — service-level.
  - Pipeline: DIOS (S3, F92-owned) → HTTP POST JSON → `POST /audience/upload` → background transform → Nextcloud `DAX_RAW_DoNotUse/<netsuite_project>/<audience_name>/<platform>/*.csv` → (user-triggered) `POST /audience/process` → copy to `DAX/<netsuite_project>/<audience_name>/<platform>/*.csv` → consumed by [[flight-check]] UI / DAX ad-platform activation.
  - **Upload payload structure**: parallel lists `audience` (PII keyed by `recd_luid`) and `audience2` (pivot rows by `(RECD_LUID, TYPE)`). Case inconsistency (`recd_luid` lowercase vs `RECD_LUID` uppercase) matches DIOS's source format — not a bug.
  - **Scale**: up to 1M `audience` rows; `audience2` larger; joined in-memory; up to 60 GB RAM at target scale.
  - **Folder structure & semantics**: (**fold in existing "Nextcloud Folder Structure & Workflow"** — `DAX_RAW_DoNotUse` vs `DAX`, Flight Check dropdown, Process Audience copy).
  - **Processed-file naming**: `{platform}_{file_count}.csv` default; `{platform}_{suffix}_{file_count}.csv` for Snapchat/Reddit variants.
  - **Hashing**: SHA256 on `hash_fields` per spec (default `["email"]`; Amazon DSP hashes 7 PII fields). MD5 is internal DataFrame hashing only, not output.

- ## API Reference (**NEW**)
  - Auth: `x-auth-apikey` header matching `X_AUTH_APIKEY`.
  - `POST /audience/upload` (202, async) · `POST /audience/process` (202, async) · `GET /projects/{project_name}/audiences` (200, sync).
  - One request/response schema per endpoint (trimmed from README).
  - `/upload` response contains `peak_memory_mb`, `current_memory_mb`, `duration_seconds` via `tracemalloc` — useful for debugging.

- ## Platform Specifications (**NEW**) — **highest-value new content**.
  - Table with one row per `FileSpecification` entry (17 rows — because Snapchat=3, Reddit=2).
  - Columns: Platform · File suffix · Audience1 mappings · Audience2 mappings · Hash fields · Single-column · Headerless · Min rows · Max rows · File size limit · Combined columns · Extra fields.
  - Source: `file_specification.py:124-354`.
  - Call-outs: Meta `min_row_count=100`, Microsoft Ads `max_row_count=4M`, Amazon DSP `max_row_count=5M` + hashes 7 fields, LinkedIn `file_size_limit=20 MB`, Viant `file_count_limit=10`.

- ## Developer Guide (**NEW**)
  - **Prerequisites**: Python 3.11+ · pip · (optional) Docker · Nextcloud access or `LocalFileHandler` switch · API key.
  - **Clone + venv + install**: standard flow.
  - **`.env` setup**: all 6 env vars (`NEXTCLOUD_HOST`, `NEXTCLOUD_PATH`, `NEXTCLOUD_STAGING_PATH`, `NEXTCLOUD_USER`, `NEXTCLOUD_PASSWORD`, `X_AUTH_APIKEY`). Values in `vault/credentials.md` (Fusion92).
  - **Run dev**: `uvicorn main:app --reload`.
  - **Run Docker**: `docker build -t dios-api .` · `docker run -p 80:80 --env-file .env dios-api`.
  - **Local-only mode**: edit `main.py:49` to return `LocalFileHandler()`. Code edit, not env toggle — tech debt.
  - **Smoke testing**: `python generate_sample_file.py` (edit `row_count` at line 43) → `python client/client.py` (edit URL at line 8).
  - **Large-payload testing**: Postman/Bruno choke on 1M rows; use `client/client.py`.
  - **Debugging**: logs to `uvicorn.error`; `/upload` response has tracemalloc stats even while background task runs.
  - **Common pitfalls**:
    - Hard-coded Nextcloud in `create_file_handler` — easy to forget to flip back
    - Per-worker `in_progress_uploads` — duplicate-upload rejection not cross-worker
    - Nextcloud 100 MB write cap — `FILE_SIZE_LIMIT_BYTES` handles this
    - `gunicorn timeout=0` — no worker watchdog
    - `recd_luid` lowercase vs `RECD_LUID` uppercase between `audience` and `audience2`
    - `/audience/process` silent on partial failures

- ## Deployment (**expand existing**)
  - Keep: on-prem Docker host · Nginx reverse proxy (timeout maxed) · Cloudflare DNS (proxying disabled) · Why on-prem (memory/time) · Path to cloud-hosting.
  - Add **Image build**: `docker build -t dios-api .`. Dockerfile = `python:3.11`, install deps, COPY source, EXPOSE 80/443, `CMD ["gunicorn", "main:app"]` (picks up `gunicorn.conf.py`).
  - Add **Image publishing / registry**: **no `.github/` workflows directory** — no automated CI/CD. Deployment is manual `docker build` + `docker run` on the Support Docker host. Executor must confirm during review.
  - Add **Env config on host**: `.env` file or `--env-file`. Values in `vault/credentials.md`.
  - Add **Rollback**: rerun previous image tag or rebuild from prior commit. No blue/green, no slots.
  - Add **No environments**: single production deployment — no staging/test slot. Differs from `core_api` / `eclipse` / `eclipse_exp`.

- ## Path to cloud-hosting (open) (**keep existing**)

- ## DIOS → DAX Integration Specification (**keep existing** — CF92/1364688898 meeting notes)

- ## Tech Debt / Known Issues (**NEW**)
  - Per-process `in_progress_uploads` — multi-worker gap
  - `gunicorn timeout=0` — no watchdog
  - `/audience/process` silent partial failures (`# FIXME` at lines 408, 478)
  - `create_file_handler` hard-coded — should be env-driven
  - No test suite — `client/client.py` is a script, not a test
  - No CI/CD — no `.github/` directory
  - **Committed credential** at `client/client.py:16` (prod API key literal). **Execution must extract to `vault/credentials.md` (Fusion92), redact from wiki prose, flag rotation.**
  - No `.env.example` / `.env.template`

- ## See Also (**augment existing**)
  - Keep: [[fusion92]], [[Cloudflare]], [[Snowflake]], [[nextcloud]], [[flight-check]], [[fusion92-data-architecture]]
  - Add: [[entities/repos/flight-check|flight-check (repo)]], [[dax-media-app]], [[local-network]], [[aldc-naming-convention]]

### Judgment calls

- **Update, don't rewrite.** Existing page has source-cited content (Confluence TECH/1766031362, CF92/1692991495, CF92/1364688898). Executor must preserve "What it does", "Nextcloud Folder Structure & Workflow", "Path to cloud-hosting (open)", "DIOS → DAX Integration Specification" verbatim — knowledge not recoverable from repo.
- **Data Flow IS applicable.** Service-level dataflow (DIOS → staging → DAX → Flight Check) is the page's core subject; absorbs existing folder-structure content.
- **Single wiki page.** ~145 → ~600 lines. Within convention.
- **Platform Specifications table is the highest-value new content** — saves readers from reading `file_specification.py`. Build mechanically from source.
- **`client/client.py:16` credential extraction mandatory per wiki rule #2.** API key `y1oGOoyM3rgtocsX0pmG28f2VndvHiV5` committed in git. Execution must (a) add to `vault/credentials.md` Fusion92 section, (b) redact in wiki prose, (c) flag in Tech Debt that the key should be rotated and file refactored to env var. **Plan session is not writing to vault — flagging for executor.**
- **CI/CD is absent, not "TODO'd".** No `.github/` — manual Docker build + run. Executor should confirm with Paul rather than invent a pipeline.
- **No `docs/` sub-files.** Single wiki page per boot prompt; sample `docs/ARCHITECTURE.md` in boot prompt is a plan-format placeholder, not an output file.
- **No disambiguation block needed.** Unambiguous name; aliases in frontmatter ([DIOS API, DIOS-to-DAX API, DAX API]) suffice.
- **Keep Snapchat/Reddit multi-spec rows explicit** in platform table — 14 `Platform` enum values but 17 specs.
- **Do not create `entities/tools/dios.md`** in this workstream. DIOS is Fusion92-owned; out of ALDC perimeter. Leave as wiki gap.

### Session Log entry to add (executor should append after writing the page)

```
### 2026-04-20 — custom-fusion-92-audience-api plan session complete

- did: read repo (README, main.py, file_specification.py, file_handler.py, gunicorn.conf.py, Dockerfile, requirements.txt, client/client.py, client/requirements.txt, generate_sample_file.py, dockerignore, git log) and existing wiki page (entities/repos/custom-fusion-92-audience-api.md).
- produced: update plan for existing wiki page — preserve business/integration sections (What it does, Nextcloud folders, Path to cloud, DIOS→DAX spec); add Architecture, Data Flow, API Reference, Platform Specifications table (17 rows), Developer Guide, expanded Deployment, Tech Debt.
- decided: single wiki page (~500–700 lines); Data Flow applicable (reframed as service-level); platform-spec table is highest-value new content; no CI/CD to document (confirmed absent); no disambiguation needed.
- flagged: `client/client.py:16` contains a production API key literal — execution session must extract to `vault/credentials.md` (Fusion92) and redact from wiki prose per wiki rule #2. Also: `in_progress_uploads` multi-worker gap, `gunicorn timeout=0`, silent partial failures in `/audience/process` — all call-outs for Tech Debt section.
- next: execution session (Sonnet) updates `entities/repos/custom-fusion-92-audience-api.md`, extracts the committed credential to vault, updates index.md entry, marks Execution ✅ in this tracker.
```


---

## claude_code_enhanced — Approved Plan

**Plan session:** 2026-04-20 (Opus)
**Target wiki page:** `wiki/entities/repos/claude_code_enhanced.md` (**new page** — companion to existing `entities/projects/cce.md`)
**Wiki index entry:** add under `Entities › Repos` alongside existing `eclipse_exp`, `eclipse (repo)`, `core_api`, `connector`, `custom-fusion-92-audience-api`, `flight-check (repo)`, `clients-repo`.

> **Disambiguation note for the execution session.** Two wiki pages must coexist:
> - [[cce]] (at `entities/projects/cce.md`) — **the product / project**. Vision, goals, current state, open questions. Already exists — do NOT rewrite or collapse it.
> - `entities/repos/claude_code_enhanced.md` (**new, this plan**) — **the repo**. What's in the codebase, how to run it, how to extend it, how to distribute it. Cross-links to [[cce]] for the "why", defers to [[zeus-memory]] for the backend.
>
> The repo folder is `claude_code_enhanced`; the product is "CCE" / "Claude Code Enhanced"; the global CLI is `cce` (symlinked to `/usr/local/bin/cce` by `install.sh`); there is no separate deployed URL — distribution is `git clone` + `install.sh`.

### Doc structure — single wiki page with these sections (in order)

All content goes into `wiki/entities/repos/claude_code_enhanced.md`. Each bullet names the section and the key anchors the execution session must include — real paths, real commands, real env var names. Do not re-derive; this plan is the verified map.

---

### Frontmatter

```yaml
---
tags: [entity, repo, cce, claude-code-enhanced, zeus-memory, skills, hooks, agentic-coding]
aliases: [CCE repo, claude_code_enhanced, claude-code-enhanced, Claude Code Enhanced repo]
sources:
  - repos/claude_code_enhanced/README.md
  - repos/claude_code_enhanced/CLAUDE.md
  - repos/claude_code_enhanced/SKILLS_INDEX.md
  - repos/claude_code_enhanced/EXTERNAL_SKILLS.md
  - repos/claude_code_enhanced/cce
  - repos/claude_code_enhanced/scripts/install.sh
  - repos/claude_code_enhanced/tools/cce_cli.py
  - repos/claude_code_enhanced/tools/cce_setup.sh
  - repos/claude_code_enhanced/tools/zeus_integration.py
  - repos/claude_code_enhanced/hooks/*.sh
  - repos/claude_code_enhanced/hooks/*.py
  - repos/claude_code_enhanced/docs/architecture/CCE_ARCHITECTURE.mermaid
  - repos/claude_code_enhanced/docs/decision-agent-accountability.md
  - repos/claude_code_enhanced/.github/workflows/claude.yml
  - repos/claude_code_enhanced/.env.example
  - repos/claude_code_enhanced/.mcp.json
created: 2026-04-20
updated: 2026-04-20
---
```

### Section outline

- ## Overview (top-of-page paragraph)
  - One paragraph: "CCE is ALDC's opinionated wrapper around Claude Code. This repo ships the `cce` launcher, an auto-syncing hook system that enforces team conventions at session boundaries, a ~195-skill library under `.claude/skills/`, a set of Python orchestration tools (multi-agent, workflow executor, context compactor, recovery manager), and an AI-first project-template CLI. It is installed per-developer via `git clone` + `install.sh`; there is no server-side deploy. The backend — Zeus Memory — lives in a separate repo ([[zeus-memory]])."
  - Link [[cce]] for product-level context (what/why), this page for engineering context (how).

- ## Tech Stack
  - Primary languages: **Bash** (launcher, hooks, setup, install, deploy scripts) and **Python 3** (hooks, tools, tests — stdlib-first; `requests`, `httpx`, `urllib` used).
  - No formal package manifest — **no `pyproject.toml`, no `package.json`, no `requirements.txt`** at repo root. Python tools rely on stdlib + a handful of installed packages (`requests`, `httpx`, `pytest`). Note this explicitly — execution must list actual dependencies discovered via `import` grep if prose wants them.
  - Distribution artefacts: `cce` (Bash launcher, ~600 lines), `scripts/install.sh` (one-command install), `tools/cce_setup.sh` (per-machine credential + config setup).
  - Integration protocols: HTTPS to Zeus Memory API (`https://zeus.aldc.io`), MCP (`https://zeus.aldc.io/mcp` — declared in `.mcp.json`), Unix domain socket for the messaging broker (`/run/user/$UID/cce/broker.sock`), local file cache (`~/.cache/cce/`).
  - Runs on: macOS, Linux, Windows (Git Bash). Windows compatibility notes are a first-class concern — several hooks explicitly probe `python3`/`python`/`py` in that order because `command -v` returns alias text in non-interactive Git Bash contexts.

- ## Repo Layout
  - Table mapping top-level entries to purpose. Concrete entries (from `ls` of root):
    - `cce` — main bash launcher (8-phase startup: resync repo → skill check → MCP config → messaging init → local settings → hook sync → readiness check → `exec claude`).
    - `scripts/install.sh` — one-command installer (curl-pipeable). Clones repo, symlinks `cce` to `/usr/local/bin`, runs readiness check.
    - `tools/` — Python tooling (~30 files). Includes `cce_cli.py` (project template CLI), `cce_setup.sh` (machine setup), `zeus_integration.py` (API client), `multi_agent_orchestrator.py`, `workflow_executor.py`, `context_compactor.py`, `recovery_manager.py`, `parallel_executor.py`, `skill_discovery.py`, `skill_generator.py`, `model_router.py`, `troubleshooter.py`, `production_builder.py`, `context7_handler.py`.
    - `hooks/` — 20 hook scripts (see § Hook System). These are the runtime enforcement layer. Mix of `.sh` and `.py`.
    - `.claude/skills/` — ~195 skill `.md` files across ~55 category directories (see `SKILLS_INDEX.md`). Every skill has a `SKILL.md` in its directory.
    - `.claude/commands/` — Claude Code slash-command definitions. Distinct from skills. ~30 commands including `msg/`, `session-exit/`, `cce-optimize/`, `repo-learn/`, `zeus-health/`, `discover-skills/`, `weekly-brief.md`, `util.md`.
    - `.claude/settings.local.json` — per-machine permissions (gitignored; generated on first launch).
    - `commands/msg/` — **separate from `.claude/commands/`** — contains the legacy `msg` command definition used outside the `.claude/` conventions.
    - `projects/` — AI-first project instances created by `cce init`. Template at `projects/CLAUDE_CODE_PROJECT_TEMPLATE.md`. Sub-directories are dated project folders (e.g., `2026-03-11-ecommerce-commission-engine/`). `completed/` archive subdir.
    - `tests/` — Python pytest suites (`test_phase1.py`, `test_phase2_{compactor,parallel,recovery,workflow}.py`, `test_phase2_5_skills.py`, `test_hallucination_reduction.py`). Locally runnable only — no CI test job.
    - `docs/` — repo-local architecture docs. `architecture/CCE_ARCHITECTURE.mermaid` is the canonical diagram; `decision-agent-accountability.md`, `ENVIRONMENT_BEST_PRACTICES.md`, `QA_ENV_CONFIGURATION_2026-01-26.md`.
    - `integrations/` — integration notes (`tsheets-data.md`).
    - `_archive/` — historical reports/research.
    - `contract-*.md`, `connector-scaffold.md`, `generate-connector.md` — top-level command definitions.
    - `SKILLS_INDEX.md` (auto-generated table of all skills), `SKILL_TEMPLATE.md`, `skills_index.json` (machine-readable).
    - `EXTERNAL_SKILLS.md` — list of third-party skill repos (Anthropic skills, VoltAgent awesome-agent-skills, travisvn awesome-claude-skills, etc.).
    - `CLAUDE.md` — the "First Principles" + context-recovery instructions loaded into every session.
    - `.mcp.json` — Zeus Memory MCP server config (HTTP transport, bearer token from `$ZEUS_API_KEY`).
    - `.env.example` — env-var template covering GitHub, Anthropic, Gemini, Voyage, Zeus API + DB, Azure, Slack, Nextcloud, Miro.
    - `.github/workflows/claude.yml` — only CI workflow. Runs `anthropics/claude-code-action@v1` when a human `@claude`-mentions in an issue, issue comment, or PR review comment. **Not a test pipeline.**

- ## Architecture — components and key abstractions
  - **Launcher (`cce`)** — the entrypoint. 8 phases on every invocation: (1) full repo resync via `git fetch origin main` + `git reset --hard origin/main` if clean; (2) session-start skill discovery check; (3) Zeus MCP configuration injection into `~/.claude/mcp.json`; (4) messaging broker + listener + task watcher init via `zeus-memory/api/messaging/cce-messaging-init.sh`; (5) generate project-level `.claude/settings.local.json` if missing; (6) sync every `hooks/*.sh`/`*.py` from repo to `~/.claude/hooks/` and patch `~/.claude/settings.json` with desired hook + statusLine + env config; (7) startup readiness check; (8) `exec claude`. All phases are skippable via `CCE_SKIP_*` env vars (`CCE_SKIP_UPDATE`, `CCE_SKIP_SKILL_CHECK`, `CCE_SKIP_MCP_CONFIG`, `CCE_SKIP_MESSAGING`, `CCE_SKIP_HOOKS`, `CCE_SKIP_READINESS`).
  - **Hook system (runtime enforcement)** — hooks live in `~/.claude/hooks/` (synced from repo) and are wired into Claude Code events in `~/.claude/settings.json`. Four event bindings:
    - `SessionStart` → `cce-session-start.sh` (launches poller daemon + messaging broker, kills stale pollers, auto-installs `team-msg` / `cce-msg-doctor` symlinks in `~/.local/bin/`).
    - `PostToolUse` → `cce-posttool-check.sh` + `tool_usage_logger.sh` (writes JSONL tool-usage log to `~/.cache/cce/session-logs/<session_id>.jsonl`).
    - `Stop` → `cce-stop-check.sh` (batches the auto-learn job — reads the tool-usage JSONL, compiles stats, POSTs a session summary to Zeus; flags with per-session marker file to prevent duplicates).
    - `SessionEnd` → `cce-session-end.sh` (final cleanup).
    - `statusLine` → `cce-statusline.sh` (renders `CCE v<ver> | <n> Inbox | <n> Assigned | <daily>/<daily_target> DR | <daily>/<daily_target> TDR | <online-users>` in the Claude Code bottom bar; reads from `~/.cache/cce/{inbox-messages.json,tasks-stats,learnings-stats,presence-online.json}`).
  - **Background poller (`cce-poller-daemon.py`)** — separate long-lived Python process started by `cce-session-start.sh`. Polls `GET /api/presence/messages?peek=true` every 3 s (updates `inbox-messages.json` + `inbox-status`), sends `POST /api/presence/heartbeat` every 30 s (updates `presence-online.json`). Self-terminates if its PID file disappears, if it is replaced by a newer poller, or after 12 h max lifetime.
  - **Auto-update trio (the "virtuous cycle")** —
    - `cce-hooks-updater.py` (~22 KB, stdlib-only): fetches signed hook manifest from Zeus (`GET /api/hooks/manifest`), HMAC-SHA256 verifies against `$CCE_HOOKS_HMAC_KEY`, SHA-256 checksums each file, atomically replaces `~/.claude/hooks/*` via staging → swap, preserves previous copy in `~/.claude/hooks/_previous/`, writes 100-line log to `~/.cache/cce/hooks-update/updater.log`. Uses `$ZEUS_ALDC_API_KEY` (ALDC team key) in preference to `$ZEUS_API_KEY`.
    - `cce-auto-learn.sh`: the "learn" half. Reads the per-session tool-usage JSONL, POSTs a session summary to `/api/store` with `source=cce-session-auto-learn`, `tenant_id=11111111-1111-1111-1111-111111111111` (ALDC Management Team tenant for shared roll-up; `b513bc6e` is JK's private tenant).
    - The CCE repo itself is fully resynced (`git fetch` + `git reset --hard origin/main`) on every `cce` launch — repo working tree is effectively read-only on dev machines; customisation belongs in `~/.claude/`.
  - **Skills library (`.claude/skills/`)** — ~195 skills across ~55 categories (see `SKILLS_INDEX.md` + `skills_index.json` for the catalog; don't enumerate in this section). Category highlights: `zeus-memory/` (33 skills — the largest), `azure/` (14), `core/` (13), `deployment/` (12), `eclipse-app/` (10), `memory-governance/` (7), `backend/` (6), `cce/` (5), `frontend/` (5). Each skill is a self-contained markdown file with input params, output format, and ALDC-specific patterns. Each is also addressable via `Skill(<name>)` from Claude Code.
  - **Slash-command library (`.claude/commands/`)** — distinct from skills. Each has a `SKILL.md` or top-level `.md` with YAML frontmatter (`name`, `description`, `model`, `allowed-tools`). Notable: `msg/` (team messaging via Zeus + Slack fallback), `session-exit/`, `cce-optimize/`, `discover-skills/`, `repo-learn/`, `zeus-health/`, `journal/`, `weekly-brief.md`, `log-failed-approach/`.
  - **CCE CLI (`tools/cce_cli.py`, ~33 KB)** — subcommands routed by the `cce` launcher: `init|update|status|list|validate|archive|search|decompose|troubleshoot`. `init` creates a project folder from `projects/CLAUDE_CODE_PROJECT_TEMPLATE.md` with placeholder substitution; `status`/`list`/`archive` operate on `projects/` folder; `search` proxies to Zeus Memory search; `decompose` breaks a workflow description into atomic tasks. Project template is MANDATORY per `CLAUDE.md` for all CCE work.
  - **Machine-setup flow (`tools/cce_setup.sh`)** — 7-step interactive setup: (1) gather creds (manual or `--pull <IP>` via `sshpass`); (2) write `~/.env` (0600); (3) configure global git (`user.name`, `user.email`, `credential.helper=store`, `~/.git-credentials`); (4) write `~/.claude/mcp.json` + `~/.claude/settings.local.json` with Zeus MCP + permission allowlist; (5) create `~/.cce/{cron,logs,sessions,skills}`; (6) append CCE section to `~/.bashrc`; (7) clone `zeus-memory` into `~/repos/zeus-memory-api`. Invoked via `cce setup` or `cce setup --pull <IP>`.
  - **Python orchestration toolkit (`tools/*.py`, "Phase 2" features)** — secondary to the runtime loop but part of the repo's surface area: `multi_agent_orchestrator.py` (~47 KB), `workflow_executor.py`, `context_compactor.py`, `recovery_manager.py`, `parallel_executor.py`, `model_router.py`, `performance_optimizer.py`, `production_builder.py`. Execution session should describe these at one-paragraph depth; don't turn into full API reference.
  - **MCP integration** — `.mcp.json` at repo root declares the `zeus-memory` MCP server (HTTP transport at `https://zeus.aldc.io/mcp`, bearer `${ZEUS_API_KEY}`). `hooks/ensure_zeus_mcp_configured.py` reconciles this into the user's `~/.mcp.json` at session start.
  - **"First Principles" as design invariants** — the 8 principles declared in `CLAUDE.md` are the repo's design rubric, not marketing. Architecture section should surface the three with the most code implications: #2 Virtuous Cycle (the auto-update + auto-learn loop), #3 Federation (Zeus as central memory), #6 Bidirectional Communication (team messaging). The remaining five belong to the [[cce]] project page, not here.
  - **ASCII/diagram reference** — point readers at `docs/architecture/CCE_ARCHITECTURE.mermaid` (in-repo) for the full system diagram. Don't re-author in the wiki.

- ## Data Flow (**applicable — document it**)
  - Data Flow IS applicable. CCE is fundamentally a data-plumbing layer between a developer's machine and Zeus Memory. Four flows should be documented:
  - **1. Tool-use → auto-learn flow (outbound):** every Claude tool invocation → `PostToolUse` hook → `tool_usage_logger.sh` → appends JSONL to `~/.cache/cce/session-logs/<session_id>.jsonl`. On `Stop` hook → `cce-auto-learn.sh` parses that JSONL, computes tool counts / files modified / duration → `POST /api/store` with `source=cce-session-auto-learn`, `tenant_id=11111111-1111-1111-1111-111111111111` → stored in Zeus Postgres. Idempotent via per-session marker file `~/.cache/cce/auto-learn-<session_id>`.
  - **2. Inbox / presence flow (bidirectional):** poller daemon polls `GET /api/presence/messages?peek=true` (3 s) → writes `inbox-messages.json` + `inbox-status` to `~/.cache/cce/` → `cce-statusline.sh` reads those on every status refresh and renders in the Claude Code bottom bar. Outbound heartbeats: `POST /api/presence/heartbeat` (30 s, identifies by `$USER` normalized via `USER_MAP` to canonical `{jk, lori, marshall, mike, brayden, paul}`). Presence details (`GET /api/team-messages/presence`) also cached in `presence-online.json` for the statusline.
  - **3. Messaging flow (outbound):** user types `/msg <recipient> <message>` → command definition in `commands/msg/msg.md` + `.claude/commands/msg/` → invokes `zeus-memory/api/messaging/delivery.send_message()` → Zeus attempts CCE-native delivery if recipient online, falls back to Slack Bot Token API if not. Recipients: `lori, mike, marshall (aliases mush/mushparker), brayden, jk, steven`; `team`/`all` fans out to everyone except sender.
  - **4. Hook-update flow (inbound):** `cce-hooks-updater.py` (SessionStart) → `GET /api/hooks/manifest` → HMAC-SHA256 verify with `$CCE_HOOKS_HMAC_KEY` → per-file SHA-256 verify → atomic replace in `~/.claude/hooks/` with prior copies preserved in `_previous/`. Plus the repo-level resync: `cce` launcher does `git fetch origin main && git reset --hard origin/main` (only if working tree clean) on every invocation.
  - **Credentials discovery chain:** launcher and every hook search `$HOME/.env` → `$CCE_ROOT/.env` → `$HOME/projects/.env` (launcher); `$HOME/.env` → `$HOME/zeus-memory/.env` → `$HOME/repos/zeus-memory/.env` (hooks). Per-machine values live in `~/.env` (0600); repo `.env.example` is the schema.
  - **Recommended diagram form:** mermaid sequence (or simple block) showing `{developer machine} ↔ {zeus.aldc.io}` with the four flows labelled. Execution session may reproduce the in-repo `CCE_ARCHITECTURE.mermaid` as a pointer rather than re-draw.

- ## Hook System (reference sub-section)
  - Table of every hook in `hooks/`, its trigger event, and its job. ~20 total. Execution session should build this table by running `ls hooks/` and reading the docstring of each. Starting point:

    | Hook file | Trigger | Purpose |
    |-----------|---------|---------|
    | `cce-session-start.sh` | SessionStart | Launch poller + broker, clear stale cache, symlink `team-msg`/`cce-msg-doctor` |
    | `cce-poller-daemon.py` | daemon | 3 s message poll + 30 s heartbeat loop (lives in cache dir) |
    | `cce-posttool-check.sh` | PostToolUse | Surface inbox messages mid-session (reads cache only — no network) |
    | `tool_usage_logger.sh` | PostToolUse | Append every tool-use to `~/.cache/cce/session-logs/<session_id>.jsonl` |
    | `cce-stop-check.sh` | Stop | Spawn `cce-auto-learn.sh` in background |
    | `cce-auto-learn.sh` | (called by stop) | Roll up session → `POST /api/store` (Zeus) |
    | `cce-session-end.sh` | SessionEnd | Final cleanup (signal poller shutdown) |
    | `cce-statusline.sh` | statusLine | Render status bar from cache files |
    | `cce-inbox-check.sh` | (cron-ish) | Cache refresh helper |
    | `cce-learnings-cache.py` | background | Produce `learnings-stats` for statusline |
    | `cce-tasks-cache.py` | background | Produce `tasks-stats` for statusline |
    | `cce-hooks-updater.py` | SessionStart (via settings.json) | HMAC-verified auto-update of `~/.claude/hooks/` from Zeus |
    | `cce-commands-sync.sh` | SessionStart | Sync `.claude/commands/` from repo |
    | `session_start_skill_check.py` | SessionStart | Report pending skill candidates |
    | `session_start_messaging.sh` | SessionStart | Messaging init (alternate path) |
    | `session_stop_messaging.sh` | Stop | Messaging teardown |
    | `message_check.sh` | periodic | Inbox poll helper |
    | `ensure_zeus_mcp_configured.py` | SessionStart | Reconcile `~/.mcp.json` with repo `.mcp.json` |
    | `ecosystem_review_check.py` | SessionStart | Auto-run ecosystem review if >7 d / >30 d / never |
    | `startup_readiness_check.py` | launch-time | 11-check verification (credentials, GitHub, Zeus API, skills) |
    | `precompact_context_saver.sh` | PreCompact | Preserve session state ahead of compaction |

  - Also cover the **caching model**: `${XDG_CACHE_HOME:-$HOME/.cache}/cce/` holds poller PID, inbox JSON + status one-liner, presence JSON, tasks-stats, learnings-stats, session-logs/, hooks-update/ (manifest + staging + updater.log + _previous/). Everything is regenerable — safe to wipe.
  - **Windows/Git Bash compatibility**: several hooks contain an explicit Python-binary probe loop (`for _py in python3 python py; do ... done`) because `command -v` returns alias text in non-interactive Git Bash contexts where aliases aren't loaded. Execution session should mention this as a real compatibility choice, not boilerplate.

- ## Skills & Commands
  - **Skills vs commands** — the repo holds both. Skills (`.claude/skills/<category>/<skill>.md`) are reusable prompt templates invoked mid-session ("use the X skill"); commands (`.claude/commands/<name>/` or top-level `.md`) are slash-command invocations (`/msg`, `/session-exit`, `/repo-learn`, `/discover-skills`, `/zeus-health`, `/cce-optimize`, etc.). Keep the distinction explicit.
  - **Scale**: ~195 skills across ~55 categories (per `SKILLS_INDEX.md` header; `CLAUDE.md` says "178 skills + 14 command skills" — discrepancy reflects counting convention, not a contradiction). Top-five by skill count: `zeus-memory/` (33), `azure/` (14), `core/` (13), `deployment/` (12), `eclipse-app/` (10).
  - **Catalog pointers**: link `SKILLS_INDEX.md` (human-readable table), `skills_index.json` (machine-readable, 42 KB), and `SKILL_TEMPLATE.md` (when creating a new skill). Also mention `EXTERNAL_SKILLS.md` for third-party skill repos (Anthropic official, VoltAgent awesome-agent-skills, travisvn awesome-claude-skills, alirezarezvani claude-skills, wshobson commands).
  - **When to create a skill** — codify the rule from `README.md`: create when a pattern is explained 3+ times, or needs to be standardised / security-enforced / token-compressed. Don't create for one-offs.
  - **5-step skill creation workflow** — preserve verbatim from `README.md` §"Creating New Skills": identify → template → test → save to category → commit.
  - **Keep this section short** — this is a repo page, not a skill catalog. Deep-dive per skill belongs in the skill files themselves.

- ## CLI Reference (`cce` + `cce_cli.py`)
  - Table of every `cce` subcommand with one-line purpose. Include the actual handler location (launcher vs `cce_cli.py`).
    - `cce` (no args) — full 8-phase startup + `exec claude`
    - `cce exit` — session-exit workflow (learn + Zeus store + cleanup). Handled inline in the launcher, not CLI.
    - `cce learn` — skill-extraction guidance printer (launcher).
    - `cce decompose "<description>"` — delegates to `cce_cli.py decompose`.
    - `cce init <name> [--type=T] [--priority=P] [--duration=D] [--objective="..."]` — new project from `CLAUDE_CODE_PROJECT_TEMPLATE.md`.
    - `cce status <name>` — read `status.json` from project dir.
    - `cce update <name> --phase=<phase> --content="<update>"` — append to project `PROGRESS.md`.
    - `cce list [--status=active|completed|archived]` — projects inventory.
    - `cce validate <name>` — structure check.
    - `cce archive <name>` — move to `projects/completed/` (and Nextcloud, per `CLAUDE.md`).
    - `cce search "<query>"` — Zeus Memory search proxy.
    - `cce git commit --message="..."` / `cce git branch <name> --type=feature` — wrappers around `git_integration.GitWorkflowManager` (soft dep; gracefully disabled if import fails).
    - `cce setup [--pull <IP>] [--user <username>]` — one-shot machine setup (delegates to `tools/cce_setup.sh`).
    - `cce troubleshoot` — full diagnostics (`tools/troubleshooter.py`).
    - `cce help` — text help.
  - Also document the `CCE_SKIP_*` bypass env vars — important when debugging the launcher.

- ## Developer Guide
  - **Prerequisites**: `git`, `python3` (3.10+), `claude` CLI installed, `bash`. Optional: `curl`, `jq`, Docker (for some skills), `gh` CLI. Windows users: Git Bash is supported but the hook Python-probe pattern matters.
  - **One-command install** (from README):
    - `git clone https://github.com/ALDC-io/claude_code_enhanced.git ~/repos/claude_code_enhanced && bash ~/repos/claude_code_enhanced/scripts/install.sh`
    - Or `curl -sSL https://raw.githubusercontent.com/ALDC-io/claude_code_enhanced/main/install.sh | bash` (note: real script lives at `scripts/install.sh` — the README's root-level path is a curl convention, not a file at the repo root).
  - **Per-machine setup**: `cce setup` (interactive) or `cce setup --pull <reference-machine-IP> --user <ssh-user>` (copies creds from an existing working machine via `sshpass`). Writes `~/.env`, `~/.claude/mcp.json`, `~/.claude/settings.local.json`, `~/.cce/`, `~/.bashrc` append, clones `zeus-memory` into `~/repos/zeus-memory-api`.
  - **Required env vars** (from `.env.example`): `ZEUS_API_KEY`, `ZEUS_TENANT_EMAIL`/`ZEUS_TENANT_ID`, `GH_TOKEN` (and/or `GITHUB_TOKEN`), `ANTHROPIC_API_KEY`. Optional but frequently used: `ZEUS_ALDC_API_KEY` (team tenant — used for shared learnings), `CCE_HOOKS_HMAC_KEY` (hook updater), `DB_*` (Zeus Postgres direct), `SLACK_BOT_TOKEN`/`SLACK_USER_TOKEN`, Azure/Nextcloud/Miro for specific skills.
  - **Tenant IDs** (from `CLAUDE.md`): `b513bc6e-ad51-4a11-bea3-e3b1a84d7b55` = JK Confidential; `11111111-1111-1111-1111-111111111111` = ALDC Management (use this for all shared learnings / `cce learn` writes). Wiki rule: these are **tenant UUIDs, not credentials** — safe to document; the actual API keys live in `~/.env`.
  - **Running locally**: after install, just `cce` from any directory. The launcher self-locates via `$CCE_ROOT` → script-resolved path → `$HOME/repos/claude_code_enhanced/` → `$HOME/cce/repos/claude_code_enhanced/` → `$HOME/claude_code_enhanced/`.
  - **Running without launcher mutations** (for debugging): `CCE_SKIP_UPDATE=true CCE_SKIP_HOOKS=true CCE_SKIP_SKILL_CHECK=true cce` — starts Claude Code without touching the repo, hooks, or `~/.claude/`.
  - **Running tests**: `cd ~/repos/claude_code_enhanced && python -m pytest tests/` — seven test files (Phase 1, Phase 2 workflow/compactor/recovery/parallel, Phase 2.5 skills, hallucination reduction). **Tests are NOT run in CI.** No `.github/workflows/test.yml` exists. Pass locally before merging.
  - **Context Recovery after `/clear`** (from `CLAUDE.md`): three commands to re-establish state — `curl https://zeus.aldc.io/health`, `PGPASSWORD=... psql ... -c "SELECT COUNT(*) FROM zeus_core.memories WHERE tenant_id='b513bc6e-...'"`, `git log --oneline -20 && ls -la projects/`.
  - **Common pitfalls** (merge with [[cce-troubleshooting]] rather than duplicate):
    - **Repo working tree is ephemeral** — `cce` resets it to `origin/main` on every launch. Never hand-edit files inside `~/repos/claude_code_enhanced/` expecting them to survive. Customisation goes in `~/.claude/` (skills, hooks, settings) or per-project `CLAUDE.md`.
    - **`.claude/settings.local.json` regeneration** — gitignored and recreated on launch if missing. If you customise it, the launcher will not overwrite (it only creates when absent), but git reset will not touch it (gitignored).
    - **`command -v python3` fails in non-interactive Git Bash** — use the probe-loop pattern from `cce-session-start.sh` when writing new hooks on Windows.
    - **`ZEUS_API_KEY` vs `ZEUS_ALDC_API_KEY`** — team learnings use the ALDC key; personal memory uses the personal key. `cce-auto-learn.sh` prefers `ZEUS_ALDC_API_KEY` when set.
    - **Stale poller daemon** — PID file at `~/.cache/cce/poller.pid`; `cce-session-start.sh` kills stale pollers (SIGTERM then SIGKILL). If messaging seems dead, check `ls ~/.cache/cce/poller.pid` + `kill -0 <pid>`.
    - **Broker socket path** — `/run/user/$UID/cce/broker.sock`. On Windows/Git Bash, this path may not exist; the broker falls back silently.
    - **`projects/` folder is project state, not gitignored** — committed. Don't let it balloon with in-progress private work. Move to `completed/` and then archive to Nextcloud via `cce archive <name>`.

- ## Distribution & Deployment
  - **There is no server-side deploy.** CCE is a client-side CLI. "Deployment" = distribution to developer machines.
  - **Install channel**: GitHub (`github.com/ALDC-io/claude_code_enhanced`). Install via `scripts/install.sh` or curl-pipe from README.
  - **Update channel**: `cce` launcher resyncs `origin/main` on every invocation (if working tree clean). No version pinning — latest-always. Skip with `CCE_SKIP_UPDATE=true`.
  - **Hook distribution**: two paths. (a) Repo `hooks/*.sh|*.py` synced to `~/.claude/hooks/` by the launcher itself. (b) Independently, `cce-hooks-updater.py` can pull HMAC-verified hook updates from Zeus without a repo resync — this is the remote-enforcement path used when ALDC needs to push a hook fix without waiting for every dev to `cce` again.
  - **Per-machine config**: `cce setup` or `cce setup --pull <reference-IP>`. Pulls creds via SSH from a reference machine (see `tools/cce_setup.sh` for the step-by-step).
  - **No staging / test environments** — single production track. The "test" for a hook/skill change is: run `cce` on a developer machine and see what happens. Risky changes should be guarded by env flags (`CCE_SKIP_*` patterns).
  - **CI/CD**: the only GitHub workflow is `.github/workflows/claude.yml` — runs `anthropics/claude-code-action@v1` when a human `@claude`-mentions in an issue/PR. Permissions: `contents:write, pull-requests:write, issues:write`; secret: `ANTHROPIC_API_KEY`. **Not a build or test pipeline.** No linting, no tests, no package publishing.
  - **Rollback**: since distribution is `git reset --hard origin/main`, rollback = revert the offending commit on `main`. The next `cce` on each machine pulls the revert automatically. For hook-only issues pushed via the updater (not the repo), `~/.claude/hooks/_previous/` holds the prior version — swap back manually.
  - **Azure / container infra**: the repo has Azure-related skills and `scripts/deploy-with-health-checks.sh`, `scripts/deploy-phase1.sh`, `scripts/azure-diagnostics.sh`, `scripts/container-logs-stream.sh`, `scripts/secret-audit.sh`. These deploy [[zeus-memory]], not CCE itself — worth clarifying to avoid confusion. Point readers at [[zeus-memory]] for the container-apps deploy runbook.

- ## Project Template System
  - CCE enforces a mandatory project-template workflow via `cce init` / `cce status` / `cce update` / `cce archive`. Template file: `projects/CLAUDE_CODE_PROJECT_TEMPLATE.md`.
  - Every CCE work session must be inside a named project folder (`projects/YYYY-MM-DD-project-name/`). Each project has `project_plan.md` and `status.json`; progress updates append to `PROGRESS.md` (checkpoint per Claude session).
  - `cce archive <name>` moves the project to `projects/completed/` and (per `CLAUDE.md`) should be followed by a Nextcloud push.
  - Template placeholders include project type (`Bug Fix | Feature Development | System Integration | Performance Optimization | Other`), priority, duration, objective, target Zeus Memory ID.

- ## Integrations
  - **Zeus Memory** — primary dependency. HTTP API at `https://zeus.aldc.io` (+ `/mcp` MCP endpoint). Code in `tools/zeus_integration.py` (stdlib-ish client with sanitised-error logging and JSON validation). Hook traffic uses `urllib.request` + bearer-token headers. See [[zeus-memory]].
  - **MCP** — `zeus-memory` MCP server wired via `.mcp.json` (repo) → `~/.mcp.json` (user), reconciled by `ensure_zeus_mcp_configured.py`. HTTP transport.
  - **Slack** — messaging fallback when a recipient is not online in CCE. Via `SLACK_BOT_TOKEN` only (per `CLAUDE.md`: "webhooks go stale"). Recipient list and user IDs live in the `msg` command skill.
  - **Context7 MCP** — `tools/context7_handler.py` (~30 KB). Token-aware cache with ranker. Used for hallucination reduction (see `tests/test_hallucination_reduction.py`).
  - **Anthropic / OpenAI / Gemini / Voyage AI** — API keys in `.env.example`; consumers scattered across tools and skills. Voyage is the embedding model used by Zeus.
  - **Miro / Nextcloud** — in `.env.example`; consumed by specific skill categories (`miro/`, nothing directly in-repo for Nextcloud but pattern is established).
  - **GitHub** — `GH_TOKEN` for repo auth; `tools/git-askpass.sh` feeds it to git for non-interactive HTTPS auth; `.git-credentials` written by `cce setup`. `gh` CLI is used by some skills.

- ## Tech Debt / Known Issues
  - **No package manifest.** Python dependencies are implicit; a new dev has no one-shot `pip install -r ...`. Fix candidates: add `pyproject.toml` or `requirements.txt`. Note this explicitly.
  - **No CI tests.** Seven pytest files, zero CI runs. Regressions only caught locally.
  - **Hook distribution by HMAC is team-trust based.** `CCE_HOOKS_HMAC_KEY` shared across machines; compromise of that key plus the Zeus API key means arbitrary code execution on every team member's machine via hook push. Worth documenting as an architectural trust boundary.
  - **`git reset --hard` on every launch** — if a dev has uncommitted work in the repo working tree, `cce` skips the reset (`git diff --quiet HEAD` gate). But this is fragile; the design assumes the repo is read-only. Document the assumption.
  - **Windows path handling is by convention, not enforcement.** Every new hook author has to remember the `for _py in python3 python py; do ... done` pattern. Consider a shared `hooks/_lib.sh` helper in future.
  - **Duplicate skill count** — `README.md` says "190+", `SKILLS_INDEX.md` header says 195, `CLAUDE.md` says "178 skills + 14 command skills". All three counts coexist. Execution session should quote the latest (`SKILLS_INDEX.md`) and note that the other figures are stale copies.
  - **`commands/msg/` duplicates `.claude/commands/msg/`** — the legacy top-level `commands/` folder has one entry (`msg/`). Unclear whether this is load-bearing or historical. Flag for cleanup.
  - **No `.gitignore` discipline on `projects/`** — project work is committed to the repo. Potential for accidental leak of client data. Consider gitignoring `projects/` and using Nextcloud as the canonical store.
  - **Committed API key in `.env.example`?** — verified safe (`.env.example` contains only placeholder values like `ghp_your_github_token_here`). Execution session should re-verify via grep during writeup but no action required per this plan.

- ## See Also
  - [[cce]] — **the product / project page**. Vision, principles, open questions. Cross-link from the top.
  - [[zeus-memory]] — the backend (API, Postgres, DAA, MCP). All CCE's persistence lives there.
  - [[cce-troubleshooting]] — settings.local.json parsing, Windows path bugs, Zeus API key, poller daemon startup. **Don't duplicate its content here** — link to it.
  - [[ai-pr-workflow]] — the broader ALDC AI-PR workflow (Semgrep + TruffleHog + Opus review + PyTestArch). CCE is a dev-side layer under this umbrella.
  - [[ai-driven-dev-workflow]] — methodology.
  - [[monorepo-research]] — analysis of consolidating repos to maximise CCE skill reuse.
  - [[factoria]], [[openclaw]] — sibling agentic projects.
  - [[postman-collections]] — unrelated repo but referenced in CCE skills for API debugging patterns.

### Judgment calls

- **This is a repo page, not a project page.** `entities/projects/cce.md` already covers vision / goals / principles. This new page covers the codebase: what's in `hooks/`, how `cce` launches, how to run it. Cross-link both ways. The execution session must not rewrite or collapse the project page.
- **Data Flow IS applicable and is a centrepiece.** CCE is plumbing between dev machines and Zeus; the four flows (tool-use → learn, inbox/presence, messaging, hook updates) are the architecturally interesting thing. This is why Data Flow gets a full section, not a "skip — UI only" note.
- **No formal "Deployment" in the traditional sense.** Reframed as "Distribution & Deployment" — install, auto-update, hook-push updater, rollback. Execution session should resist the urge to invent a staging/prod model that doesn't exist.
- **Skills catalog belongs in `SKILLS_INDEX.md`, not the wiki.** One-paragraph pointer + top-five-by-count is enough. Linking to the in-repo index + JSON is the right move; enumerating 195 skills in the wiki adds no value.
- **Hook table is the highest-value new content.** ~20 hooks, all with distinct jobs, zero existing documentation of them as a set. Execution session should build the full table from `ls hooks/` + docstrings. This is the section that will get the most reader traffic.
- **Don't re-author the mermaid diagram.** `docs/architecture/CCE_ARCHITECTURE.mermaid` exists in-repo. Point to it, or reproduce as a code fence if the wiki renders mermaid (it does in Obsidian). Either way, the authoritative copy is in-repo.
- **Disambiguation callout is mandatory.** Repo slug (`claude_code_enhanced`), product name ("CCE" / "Claude Code Enhanced"), CLI command (`cce`), and existing project-page name ([[cce]]) are all distinct. Frontmatter aliases + an explicit disambiguation block up top prevents confusion.
- **No credential extraction required.** Unlike the audience-API plan, there are no hard-coded prod credentials in this repo — `.env.example` is placeholder-only. Execution session should still grep for obvious leaks during writeup (`grep -rE "(sk-ant-|ghp_|xoxb-|zm_|zeus-)" --exclude-dir=.git .claude/ hooks/ tools/ scripts/`) but no action is expected.
- **Page length budget.** Target ~600–900 lines. Hook table + CLI table + data-flow section are the bulk. If the page blows past 1,000 lines, split out a `concepts/architecture/cce-hooks-reference.md` sub-page rather than compress — the hook table is a high-utility reference that deserves room.
- **Cross-reference hygiene.** Must link [[cce]], [[zeus-memory]], [[cce-troubleshooting]], [[ai-pr-workflow]]. Should link [[ai-driven-dev-workflow]], [[monorepo-research]], [[factoria]], [[openclaw]]. Do NOT link tool skills ([[azure]], [[Snowflake]] etc.) — CCE is orthogonal to them.
- **Stale count reconciliation.** `README.md` says "190+", `CLAUDE.md` says "178 + 14 command skills", `SKILLS_INDEX.md` says "195 across 49 categories". Quote the `SKILLS_INDEX.md` figure (it's auto-generated) and note the others are stale. Do not attempt to make them agree by hand.
- **One wiki page, no repo-internal `docs/` additions.** Per the boot prompt, execution session writes only to the wiki. Do not add `docs/` files to the repo. The boot-prompt example `docs/ARCHITECTURE.md` heading is a plan-format placeholder, not an output file.

### Session Log entry to add (executor should append after writing the page)

```
### 2026-04-20 — claude_code_enhanced plan session complete

- did: read repo thoroughly — README.md, CLAUDE.md, SKILLS_INDEX.md, EXTERNAL_SKILLS.md, cce (launcher), scripts/install.sh, tools/cce_cli.py, tools/cce_setup.sh, tools/zeus_integration.py, all hooks/*.sh and hooks/*.py, docs/architecture/CCE_ARCHITECTURE.mermaid, docs/decision-agent-accountability.md, .github/workflows/claude.yml, .env.example, .mcp.json, .claude/commands/ structure, .claude/skills/ structure. Also read existing entities/projects/cce.md and wiki index.
- produced: plan for new wiki page entities/repos/claude_code_enhanced.md — Overview, Tech Stack, Repo Layout, Architecture (launcher + hooks + poller + auto-update trio + skills/commands + CLI + setup flow + Python orchestration + MCP + First Principles), Data Flow (4 flows — tool-use/learn, inbox/presence, messaging, hook updates), Hook System (reference table of ~20 hooks), Skills & Commands, CLI Reference, Developer Guide, Distribution & Deployment, Project Template, Integrations, Tech Debt, See Also.
- decided: Data Flow IS applicable and is the centrepiece (CCE = plumbing); no traditional deployment section (reframed as Distribution & Auto-update); keep existing entities/projects/cce.md untouched (project vs repo split); hook table is highest-value new content; no repo-internal docs/ writes (wiki only).
- flagged: no hard-coded credentials in repo (unlike audience-API). Stale skill counts across README/CLAUDE.md/SKILLS_INDEX.md — execution session should quote SKILLS_INDEX.md and note others are stale. No formal Python package manifest — note as tech debt. No CI test job. commands/msg/ duplicates .claude/commands/msg/ — flag for cleanup but don't act.
- next: execution session (Sonnet) creates entities/repos/claude_code_enhanced.md (~600–900 lines), updates index.md to add the new repo entry under Entities › Repos, marks Execution ✅ in this tracker, appends to log.md.
```

---

## workflows — Approved Plan

**Plan session:** 2026-04-20 (Opus)
**Target wiki page:** `wiki/entities/repos/workflows.md` (**new page** — no existing page)
**Wiki index entry:** add under `Entities › Repos` alongside existing `eclipse_exp`, `eclipse (repo)`, `core_api`, `connector`, `custom-fusion-92-audience-api`, `flight-check (repo)`, `claude_code_enhanced (repo)`, `clients-repo`.

> **Disambiguation note for the execution session.** Four neighbouring names collide and must be kept separate on every page touched.
> - **`workflows` (this repo)** — `C:\Users\PaulRussell\repos\workflows`, GitHub `ALDC-io/workflows`. Today holds **one client's worth of code** (`fusion_92/`) and three sub-apps inside that: a deployed Azure Functions app (`F92_workflow_app`), a one-shot retrofit script (`F92_notification_retrofitting_app`), and a one-shot cron-update script (`F92_notification_cron_update`). Repo root `README.md` says only "Repository for client specific code" — the repo is explicitly **multi-client-ready but currently single-client-populated**. Wiki slug: `workflows`.
> - **[[dax-media-app]]** (project page) — the Fusion92-facing product ("DAX Media App" / "Flight Check App"). The `F92_workflow_app` is the **backend** of that product. The [[flight-check]] repo page says the DAX API has "no wiki page yet; flagged as gap" (repo page line 18). **This plan closes that gap.** Heavy cross-link; do not duplicate product scope.
> - **[[entities/repos/flight-check|flight-check (repo)]]** — the **Next.js frontend** of the DAX Media App. Every `/api/dax/*`, `/api/netsuite/*` proxy in that repo calls into `F92_workflow_app` here. The flight-check page's Upstream/Downstream section (lines 118–125) enumerates the exact endpoints this repo serves.
> - **[[flight-check]]** (ops-runbook page at `processes/operations/flight-check.md`) — ALDC's operational validation runbook (Eclipse connector health / Snowflake task chain / data freshness). **Different page with the same-looking slug.** Also important: this repo's `f92_flight_check_flight_sync` + `f92_flight_check_job_sync` timer functions are *not* the ops runbook — they are data-sync jobs serving the *app*. Disambiguate explicitly.
>
> Two additional wiki pages are already adjacent and partly document this repo without naming it:
> - **[[connector-token-refresh]]** already says "Deployed in the **Fusion workflow function app** for each environment" and documents the Microsoft Ads 90-day refresh token cycle. The daily automated refresh lives in this repo's `workflows/bing_ads.py`. Cross-link; do not re-author the runbook.
> - **[[dax-ai]]** (project page) — DAX AI dashboard suite. Unrelated product — do **not** confuse `dax_api/` (this repo's package name) with "DAX AI" (the analytics product). The name collision is coincidental.

### Doc structure — single wiki page with these sections (in order)

All content goes into one page: `wiki/entities/repos/workflows.md`. Sections below are in the order they should appear. Each bullet names anchors the execution session must include — real paths, real cron strings, real env var names. The plan does verification work once so the executor writes prose around verified facts.

---

### Frontmatter

```yaml
---
tags: [entity, repo, workflows, fusion92, dax-media-app, azure-functions, netsuite, bing-ads, notifications]
aliases: [workflows repo, fusion92 workflows, DAX API backend, F92 workflow app, Fusion workflow function app]
sources:
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
updated: 2026-04-20
---
```

---

### Section 1 — Intro paragraph (top of page, no heading)

**Purpose:** Position `workflows` against [[dax-media-app]], [[entities/repos/flight-check|flight-check (repo)]], [[core_api]], and [[connector]]. Resolve the "what is this repo actually" question up front.

**Key content:**
- One-sentence identity: *client-specific workflow code; today a single Fusion92 Azure Functions app plus two one-shot Cosmos-DB migration scripts.*
- Position: this repo is the **DAX API backend** referenced (but unnamed) throughout [[entities/repos/flight-check|flight-check (repo)]]. Where flight-check calls `DAX_API_URL/jobs/{id}`, `DAX_API_URL/flights/{id}`, `DAX_API_URL/jobs/export`, `DAX_API_URL/calculations`, and `F92_NETSUITE_WORKFLOW_URL/api/f92_netsuite_po_sync` — it is calling `F92_workflow_app` HTTP routes defined in `function_app.py`. The `DAX_API_URL` base and `F92_NETSUITE_WORKFLOW_URL` base both resolve to this function app.
- Structural reality: the repo contains one folder — `fusion_92/` — with three sub-projects:
  1. `F92_workflow_app/` — the production Azure Functions app (HTTP + Timer triggered). ~90% of the repo by weight.
  2. `F92_notification_retrofitting_app/` — one-shot migration script that back-populated default notification documents in Cosmos for all Fusion users. Run once per environment during Notifications rollout.
  3. `F92_notification_cron_update/` — one-shot cron patcher (sets every Fusion notification's `schedule` to `* * * * *` — most plausibly a dev/test tool). Committed `.env` with production credentials — flag.
- Repo root README is one line: *"Repository for client specific code."* The folder name `fusion_92/` is the client namespace; the design assumes future clients would get peer folders (e.g. `gep/`), though none exist today.
- Flag in intro: **`.env` with production Cosmos DB hostname + key is committed to `F92_notification_cron_update/.env`** (plus commented-out dev and test hostnames/keys). Execution session must extract these to `vault/infra-credentials.md` § Fusion92 before writing prose, following wiki rule #2. Then the intro paragraph references the vault pointer.

---

### Section 2 — `## Architecture`

**Purpose:** Map the three sub-projects, the Python package layout inside `F92_workflow_app`, and the two parallel route conventions (DAX API vs Fusion workflow).

**Sub-sections:**

- `### Repository layout` — tree form. The whole repo is:

  ```
  workflows/
  ├── README.md                                    (1 line)
  └── fusion_92/
      ├── F92_workflow_app/                        # Azure Functions app (prod)
      │   ├── function_app.py                      # All Azure function bindings (HTTP + Timer)
      │   ├── global_constants.py                  # FUSION_ACCOUNT_ID, ENVIRONMENT, timezone, app type IDs
      │   ├── host.json                            # Functions host v2, Application Insights sampling
      │   ├── local.settings.template.json         # Env-var template (not gitignored)
      │   ├── requirements.txt
      │   ├── test_function.ps1                    # Manual PowerShell smoke-test script (stale endpoint)
      │   ├── .funcignore                          # Excludes .env, test/, local.settings* from deployment
      │   ├── .gitignore
      │   ├── .vscode/                             # Azure Functions VS Code integration
      │   ├── dax_api/                             # Newer, typed, "Dax API" package
      │   │   ├── jobs/{routing.py, schema.py, lib/{calculations.py, exports.py, export_options.py, fetch.py, utils.py}}
      │   │   ├── notifications/{routing.py, schema.py, lib.py, change_notifications.py, pacing_notifications.py}
      │   │   ├── sync/{routing.py, schema.py, lib.py}
      │   │   ├── users/{schema.py, lib.py}
      │   │   └── lib/{core_client.py, error.py, response.py, date.py, string.py}
      │   ├── workflows/                           # Legacy, "Workflow" package (being phased out)
      │   │   ├── bing_ads.py                      # Microsoft Ads OAuth refresh workflow
      │   │   ├── netsuite.py                      # NetSuite PO sync workflow + NetSuiteAPIClient
      │   │   └── lib.py                           # LegacyCoreAPIClient, WorkflowError, response helpers
      │   └── test/                                # pytest for calculations (4 classes, 556 lines)
      │       ├── resources.py                     # Test fixtures
      │       └── test_job_calculations.py
      ├── F92_notification_retrofitting_app/       # One-shot backfill
      │   ├── migrate.py                           # Create default notification docs for every Fusion user
      │   ├── requirements.txt
      │   └── .gitignore
      └── F92_notification_cron_update/            # One-shot cron patch (dev utility)
          ├── update.py                            # Set every Fusion notification's schedule to "* * * * *"
          ├── requirements.txt
          ├── .env                                 # ⚠ COMMITTED production Cosmos creds
          └── .gitignore
  ```

- `### Tech stack` — table.

  | Layer | Choice | Notes |
  |---|---|---|
  | Runtime | Azure Functions Python v2 programming model | `azureFunctions.projectLanguageModel: 2` in `.vscode/settings.json`; `func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)` in `function_app.py:75` |
  | Host | `host.json` version `"2.0"`, extension bundle `[4.*, 5.0.0)` | Application Insights sampling enabled, request type excluded |
  | Python | 3.x (not pinned — VS Code uses `.venv`) | No `pyproject.toml`, no version pin in `requirements.txt` |
  | Data validation | Pydantic (with `[email]` extra) | Used in `dax_api/` schemas, not in `workflows/` legacy path |
  | HTTP | `requests` | No async client |
  | NetSuite auth | `pyjwt[crypto]` | ES256 JWT via private key in env var (see §Security) |
  | Microsoft Ads | `bingads` | Official SDK — `OAuthWebAuthCodeGrant` |
  | Cosmos DB | `azure-cosmos` + core_api indirection | Only the two one-shot scripts talk directly to Cosmos; `F92_workflow_app` goes through core_api |
  | Spreadsheet export | `pandas`, `pandas-stubs`, `xlsxwriter` | Excel exports emit base64-encoded strings |
  | Email | via `core_api` `application/email` endpoint | No direct Mailjet SDK — emails round-trip through core_api's queue. See [[core_api]] Notification Module. |
  | Timezone | `pytz`, `zoneinfo.ZoneInfo` | `America/Chicago` (`FUSION_TZINFO`); daylight-savings handled by recompiling (see §Pitfalls) |
  | Testing | `pytest` + `pytest-mock` | Local only — no CI |
  | Env loading | `python-dotenv` with `override=True` | Every module top-level loads dotenv; dev leak risk noted below |
  | Formatter | `black` (VS Code) | `.vscode/settings.json:9-12` |

- `### Two parallel package namespaces — `dax_api/` vs `workflows/`` — this is the single most important architectural thing to say, because it affects every new feature decision.
  - `dax_api/` is the **target pattern**. Contract-first, Pydantic-typed, uses `DaxCoreAPIClient` (`dax_api/lib/core_client.py:18`) which returns validated models and raises structured `APIError` / `DocumentNotFound` / `ServerError`. Responses go through `dax_api.lib.response.api_success` / `api_error` + the `@handle_dax_api_errors` decorator.
  - `workflows/` is the **legacy pattern**. Untyped dicts, `LegacyCoreAPIClient` (`workflows/lib.py:35`, explicitly marked DEPRECATED in the docstring), `WorkflowError` exception with hand-rolled `success_response`/`workflow_error_response`/`exception_response` wrappers that emit the older core_api-style envelope (`{"response": {"code", "message", "data"}}`).
  - `function_app.py`'s module docstring (lines 1-25) states the direction explicitly: new code should be `dax_api/` + `@handle_dax_api_errors`; the existing `workflows/` entries (`f92_netsuite_po_sync`, `f92_netsuite_publishers`, `f92_refresh_microsoft_ads_token`) will be migrated "if it makes sense" (`workflows/lib.py:40`).
  - Execution session should state this split **up front** and label every route table row with which namespace it lives in.

- `### Request flow — two shapes`
  - **HTTP (DAX API shape):** Azure function receives `func.HttpRequest` → `@handle_dax_api_errors` catches exceptions → handler calls a `dax_api.<area>.routing.*` function → routing function instantiates `DaxCoreAPIClient` + fetches docs + runs calculations/transformations → returns a Pydantic model → `api_success(model)` wraps it in HTTP 200. Example: `dax_get_job` (`function_app.py:393-410`).
  - **HTTP (Legacy workflow shape):** Azure function receives `func.HttpRequest` → handler validates method + account_id explicitly → instantiates `NetSuiteAPIClient()` + `LegacyCoreAPIClient()` → passes both to a `Workflow` class instance → calls `workflow.run()` → returns `success_response(msg, data)` / `workflow_error_response(WorkflowError)` / `exception_response`. Example: `f92_netsuite_po_sync` (`function_app.py:201-231`).
  - **Timer trigger:** Azure invokes on cron → handler wraps a `try/except` for `APIError`/`Exception` → calls the same `route_*` / workflow class as the HTTP counterpart. Example: `f92_status_change_notifications` (`function_app.py:86-109`) is the timer half of `dax_notifications_send_status_change` (`function_app.py:112-126`). Per the `function_app.py` docstring: *"All timer triggered functions should have an matched API endpoint unless the workflow will never need to be triggered manually"* (lines 10-13).

- `### Key abstractions` — one paragraph each:
  - **`DaxCoreAPIClient`** (`dax_api/lib/core_client.py:18-289`) — typed wrapper around the core_api HTTP API. Reads `core_api_url` + `core_api_token` env vars at class load time; raises `ServerError` if either missing. Key methods: `post_validated(route, body, return_type) -> T`, `post_validated_list(..., return_type) -> list[T]`, `application_read_validated(id, T) -> T`, `dataset_query_validated(body, T) -> list[T]`. Still holds a deprecated `post()` (untyped) used by older callers. Docstring notes the pending switch from `dataset/query` (legacy) to `dataset/request` — not yet in production as of 2026-01 (`core_client.py:257-259`).
  - **`LegacyCoreAPIClient`** (`workflows/lib.py:35-85`) — DEPRECATED per docstring. Same env-var source (`core_api_url` + `core_api_token`) but untyped, returns raw `payload` dict-or-list, raises `WorkflowError("Cosmos document query failed", …)` on non-200.
  - **`NetSuiteAPIClient`** (`workflows/netsuite.py:24-211`) — handles OAuth2 `client_credentials` grant with JWT client assertion (ES256) against `https://{ACCOUNT_ID}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token`. 15-minute JWT expiry (`netsuite.py:89`). Env vars: `NETSUITE_CLIENT_ID`, `NETSUITE_CERTIFICATE_ID`, `NETSUITE_ACCOUNT_ID`, `NETSUITE_PRIVATE_KEY` (PEM). Key methods: `connect()` (exchanges JWT → access_token), `call_suiteql(query)` (paginated SuiteQL, 10k-offset cap), `put_purchase_order(po_json, external_id)` (creates/updates PO using external ID, then GETs the Location header to return the saved doc).
  - **`F92NetsuitePOWorkflow`** (`workflows/netsuite.py:217-564`) — orchestrates the PO sync. Inputs: `account_id` (must equal `FUSION_ACCOUNT_ID`), `flight_id`. Steps: read flight + parent job from core_api → look up NetSuite vendor (by publisher name), inventory item (by channel → mapped item name), project (by job number), existing PO (if `po_number`) → build PO body → PUT → write `po_number` and `netsuite_sync="connected"` back to flight. Channel-to-item mapping is hard-coded in `channel_to_inventory_item_name()` (`netsuite.py:528-563`) — **9 channels**: Programmatic (CTV/Digital Audio/Display/OTT/Video/DOOH/Native), Social, Paid Search (SEM/Sponsored Reach/App Store), Direct, Print (OOH), Radio (Terrestrial), TV (Linear). Uses Unicode `–` (en dash) because the NetSuite item names contain en dashes, not hyphens.
  - **`MicrosoftAdsTokenRefreshWorkflow`** (`workflows/bing_ads.py:15-229`) — Hard-coded `CLIENT_ID = "98fe3659-b606-4550-9b16-c5e51a792618"` (the ALDC Microsoft Ads app registration — not sensitive, but flag the hard-code). Reads `MICROSOFT_ADS_CLIENT_SECRET`, `account_id`, `MICROSOFT_ADS_CONNECTION_ID`. Flow: `work/connectionlist` → extract `developer_token` + `refresh_token` → `oauth_client.request_oauth_tokens_by_refresh_token(refresh_token)` → `work/connectionupdate` with new refresh token. Runs daily at 07:00 UTC (`function_app.py:275`). Cross-link [[connector-token-refresh]] (the manual fallback runbook).
  - **`FlightCheckSnowflakeSyncWorkflow`** (`dax_api/sync/lib.py:122+`) — uploads job / flight / flight-metrics Cosmos docs into Snowflake via core_api's `datastore/upload` endpoint (`dax_api/sync/lib.py:332-362`). Three hard-coded `DataStoreDocument` instances with UUIDs that must match the per-environment data stores: JOB (`61e68798-…`), FLIGHT (`54a3d07c-…`), FLIGHT_METRICS (`20ae845b-…`). Upload batch size `MAX_UPLOAD_ROWS = 10_000`. Excludes heavy fields from docs before upload (`EXCLUDED_JOB_FIELDS = ["audit_trail", "calculations"]`, `EXCLUDED_FLIGHT_FIELDS = ["audit_trail", "rejection_notes", "metrics", "changed_fields", "calculations"]` — `sync/lib.py:78-85`). `only_recent` flag limits the pull to the last `RECENT_DAYS_TO_PULL = 30` days.
  - **Flight / Job calculations** (`dax_api/jobs/lib/calculations.py`, 34 KB) — the computation engine behind the "DAX API" name. Applies pacing, budget, and platform-fee math to daily Snowflake metrics + Cosmos flight docs. Test coverage in `test/test_job_calculations.py` (4 test classes, 556 lines) is the only real test surface in the repo.

- `### `global_constants.py` as environment selector` — `ENVIRONMENT` resolved from env var (default `QA`); `FUSION_ACCOUNT_ID` env-overridable (default `0fc00e34` — prod/test account); `ECLIPSE_BASE_URL` env-overridable (default `https://fusion92.eclipse.aldc-ca-w1.com`); `APPLICATION_FLIGHT_ID = "9b9a62ab-6021-4147-85f9-74f9ebe9767a"` and `APPLICATION_JOB_ID = "127edb5c-7f9a-4dfa-a679-a6689cd2a70e"` are hard-coded Cosmos application document IDs — same across environments. `FUSION_TIMEZONE_STRING = "America/Chicago"`; `LAST_SMARTSHEET_YEAR = 2025` (historical Smartsheet integration sunset). `PLATFORM_TECH_PERCENTAGE_PLATFORMS = ["viant", "youtube"]` is maintained in sync with the frontend — any platform added here must also be added in `flight-check`.

- `### Design decisions worth calling out`
  - **Azure Functions v2 programming model** — single-file function declarations via decorators on a `func.FunctionApp` instance. Forces everything to live in `function_app.py`; the `dax_api/jobs/routing.py` top-of-file docstring is explicit about why routes move their logic out into sub-packages (lines 1-17).
  - **Auth model:** `AuthLevel.FUNCTION` for all HTTP routes (`function_app.py:75`). Clients (flight-check, retrofit scripts) pass `x-functions-key`. No bearer-token or OAuth on the HTTP surface. The function key is *shared* with `DAX_API_MASTER_TOKEN` / `F92_NETSUITE_PUBLISHERS_TOKEN` / `F92_NETSUITE_SYNC_TOKEN` on the flight-check side (three different tokens — flight-check holds three separate keys).
  - **Account-ID gating** — NetSuite endpoints explicitly reject any request whose body `account_id != FUSION_ACCOUNT_ID` with 403 (`function_app.py:213-221`, `243-250`). Belt-and-suspenders because the function key already restricts access.
  - **Deployment-slot cron safety** — every timer function has a docstring note telling the deployer to disable the function in the staging slot via `AzureWebJobs.<func_name>.Disabled=true` on the slot (not swapping with deployment settings). Missing this would cause double-sends. Not enforced by code.
  - **Daylight-savings manual switch** — cron schedules are hand-edited and redeployed twice a year. Summer and winter schedules are both present in the file as sibling decorators, commented in/out. See function_app.py:85-86, 129-130, 155-156. Known tech-debt — called out in the file's inline comments.
  - **Two package namespaces coexist by design.** The README says "client specific code" — as other clients join, they'd get their own top-level folders under `workflows/`.

---

### Section 3 — `## Data Flow`

**Purpose:** Describe how data flows through this repo. **Data Flow IS applicable** — this is a backend API and an ETL-adjacent sync service.

**Sub-sections:**

- `### Inbound — HTTP requests from flight-check (and admins)`
  - All inbound HTTP comes from the flight-check Next.js app (server-side `/api/dax/*` and `/api/netsuite/*` proxies). Every call carries `x-functions-key`.
  - Endpoint list (reproduce as a table, labelled by namespace):
    - **DAX API (`dax_api/*`):** `GET /api/dax/jobs/{job_id}` · `GET /api/dax/jobs/{job_id}/flights` · `GET /api/dax/flights/{flight_id}` · `POST /api/dax/calculations` · `GET /api/dax/jobs/{job_id}/export` · `POST /api/dax/jobs/export` · `POST /api/dax/notifications/send/status` · `POST /api/dax/notifications/send/pacing` · `POST /api/dax/sync/jobs` · `POST /api/dax/sync/flights`.
    - **Legacy workflow (`workflows/*`):** `POST /api/f92_netsuite_po_sync` · `GET /api/f92_netsuite_publishers`.
  - Every DAX-API handler calls back out to core_api (over HTTP) for Cosmos documents, and sometimes to core_api's `dataset/query` for Snowflake dataset reads. NetSuite handlers call core_api for Cosmos + NetSuite REST/SuiteQL for vendor/item/project/PO lookups.

- `### Outbound — scheduled timer functions`
  - `f92_status_change_notifications` — summer `0 0 15,17,20,23 * * *` (UTC) / winter `0 0 14,16,19,22 * * *` → 9am/11am/2pm/5pm **America/Chicago**. Reads all `NotificationDocument`s, sends status-change emails via core_api's `application/email` endpoint. Fusion-scheduled times.
  - `f92_out_of_range_pacing_notifications` — summer `0 0 15 * * 2,4` / winter `0 0 14 * * 2,4` → 9am Tue+Thu America/Chicago. Sends pacing out-of-range emails.
  - `f92_flight_end_pacing_notifications` — summer `0 0 15 * * *` / winter `0 0 14 * * *` → 9am daily America/Chicago. Sends flight-end-pacing emails to creators.
  - `f92_refresh_microsoft_ads_token` — `0 0 7 * * *` → 7am UTC (midnight PST). Refreshes Microsoft Ads OAuth refresh token and writes back to Cosmos connection doc. Must run outside any template-run window (docstring at `function_app.py:276-286`).
  - `f92_flight_check_job_sync` + `f92_flight_check_flight_sync` — both `0 20,50 10-23 * * *` → HH:20 + HH:50 from 10:20 UTC to 23:50 UTC (~3:20am–4:50pm PST). Uploads Cosmos app docs + Snowflake metrics to Snowflake via `datastore/upload` twice an hour.

- `### Core-API-mediated Snowflake upload`
  - No direct Snowflake SDK here. Snowflake uploads go through **core_api's `datastore/upload` endpoint** — a JSON records array with `account_id`, `store_id`, `records`. `datastore/get` is used as the existence check. This is the same `DataStore` abstraction documented in [[core-api-data-model]] / [[cosmosdb-schema]]. Max batch 10k rows (`sync/lib.py:69`).
  - Three data stores (IDs hard-coded, must exist in each Snowflake/core env):
    - `JOB` — `61e68798-20f5-4a38-b7e1-ffcb00e5d767`, PK `["ID", "ACCOUNT_ID"]`, merge=add.
    - `FLIGHT` — `54a3d07c-c8cd-40bc-8b75-822dbf1c007d`, PK `["ID", "APP_ID", "ACCOUNT_ID"]`, merge=add.
    - `FLIGHT_METRICS` — `20ae845b-334b-4dd4-ade7-a28dc87142be`, PK `["FLIGHT_ID", "DATE"]`, merge=add.

- `### NetSuite PO write path`
  - End-to-end: flight-check FE "Sync" button → `POST /api/netsuite/sync/syncpo` (flight-check proxy) → `POST /api/f92_netsuite_po_sync` (this repo) → core_api `application/read` for flight + job → NetSuite auth (JWT grant) → `SELECT id FROM vendor WHERE companyName = '<publisher_name>'` (SuiteQL) → `SELECT id FROM item WHERE itemid = '<channel-mapped>'` → `SELECT id, entityid, projectmanager FROM job WHERE entityid = '<job_number>'` → (if `po_number` present) `SELECT id, externalid, tranid FROM transaction WHERE tranid = '<po_number>'` → `PUT /purchaseOrder/eid:<flight.id>` with `{replace: "item"}` → `GET <Location>` → core_api `application/update` with `po_number` + `netsuite_sync="connected"`.
  - Business rules live on [[dax-media-app]] § NetSuite PO Sync — do not re-author here; link.

- `### Notification email path`
  - `route_send_status_change_notifications` → fetch all `NotificationDocument` (Cosmos via core_api) → for each enabled, good-status doc → `send_status_change_notifications(account_id, notification_id)` → build HTML table + call **core_api's `application/email`** endpoint (`change_notifications.py:181-202`). The email is base64-encoded and sent `from: support@aldc.io`. core_api handles Mailjet delivery (see [[core_api]] § Notification Module).

- `### One-shot scripts (out-of-band)`
  - `F92_notification_retrofitting_app/migrate.py`: iterates all users in Cosmos, for each user with the Fusion Flight app, creates two `NotificationDocument`s ("My Notifications" + "Group Notifications") with preconfigured `status_to_report` lists. Run once per environment during Notifications rollout. Uses `azure-cosmos` directly (bypasses core_api). Default `schedule = "0 14,16,19,22 * * *"` (winter UTC for the old hours). Target doc IDs minted as `uuid.uuid4()`.
  - `F92_notification_cron_update/update.py`: lists every notification in Cosmos, for ones with `account_id == os.environ["account_id"]` sets `schedule = "* * * * *"` and upserts. Committed `.env` currently points at **prod** (`aldcprodcsdb1c01.documents.azure.com`). This is almost certainly a dev debugging utility; in its current committed form running it would set every Fusion prod notification to once-per-minute. Execution session should flag this with a "Known hazard" block.

---

### Section 4 — `## Developer Guide`

**Purpose:** Get a developer from clean machine to running the function app locally.

**Sub-sections:**

- `### Prerequisites`
  - Python 3.x (repo unpins; VS Code scaffold targets `.venv`). Recent 3.10+ works — `pydantic`, `bingads`, `azure-functions` all support it.
  - Azure Functions Core Tools (`func`) v4 — required by the VS Code `"func: host start"` task (`.vscode/tasks.json`).
  - Azure CLI (`az`) — for deployment.
  - PowerShell — `test_function.ps1` is a smoke-test script (note: endpoint in that script is stale; see pitfalls).
  - Access to core_api dev/test/QA environment + function keys.
  - (For NetSuite work) NetSuite sandbox client ID, certificate ID, and RSA private key from Dashlane.
  - (For Microsoft Ads work) Microsoft Ads client secret from Dashlane.

- `### Environment variables`
  - Canonical schema: `local.settings.template.json` (committed). Values fill in `local.settings.json` (gitignored).
  - **Required:**
    - `AzureWebJobsStorage` — storage-account connection string (required by Azure Functions).
    - `FUNCTIONS_WORKER_RUNTIME` = `"python"`.
    - `core_api_url` — e.g. `https://aldcqafnapcore1c01.azurewebsites.net/v1/` (note trailing slash).
    - `core_api_token` — function key for that core_api.
    - `account_id` — `f49f9aa3` for QA, `0fc00e34` for TEST/PROD. Used by every timer function to gate access to Fusion-specific docs.
    - `eclipse_url` — base URL of the portal Eclipse instance (e.g. `http://localhost:3000` for local).
    - `ENVIRONMENT` — `local` / `QA` / `TEST` / `PROD` (used by `environment_prefix()` and DST toggles).
    - `application_type` — comma-separated Cosmos application document IDs; generally the flight app ID `9b9a62ab-…`.
  - **NetSuite PO sync:**
    - `ALDC_NETSUITE_EMPLOYEE_ID` (`13456` — dev default).
    - `NETSUITE_PO_CLIENT_LEAD_ID` (`13417`).
    - `NETSUITE_PO_PROJECT_MANAGER_LEAD` — template key; actual code reads `NETSUITE_PO_PROJECT_MANAGER_ID` (**mismatch; flag**). `2747` default in template.
    - `NETSUITE_ACCOUNT_ID` — sandbox `7378083-sb1` (prod differs).
    - `NETSUITE_CLIENT_ID`, `NETSUITE_CERTIFICATE_ID` — from Dashlane.
    - `NETSUITE_PRIVATE_KEY` — PEM body. Must go in `.env` not `local.settings.json` (template has leading `__NETSUITE_PRIVATE_KEY` placeholder noting this).
  - **Microsoft Ads:**
    - `MICROSOFT_ADS_CLIENT_ID` — template note says "same in all envs", but actual code ignores this env var and hard-codes `"98fe3659-b606-4550-9b16-c5e51a792618"` in `bing_ads.py:31`.
    - `MICROSOFT_ADS_CLIENT_SECRET` — from Dashlane.
    - `MICROSOFT_ADS_CONNECTION_ID` — Cosmos connection document id for the Microsoft Ads connection.
  - **Disable-timers-locally pattern** — `local.settings.template.json` sets `AzureWebJobs.<func>.Disabled: true` for every timer function so running `func host start` locally doesn't fire them. Keep this pattern when deriving a local settings file.

- `### Local setup — F92_workflow_app`
  1. `cd workflows/fusion_92/F92_workflow_app`.
  2. `python -m venv .venv && source .venv/bin/activate` (Windows Git Bash: `.venv/Scripts/activate`).
  3. `.venv/bin/python -m pip install -r requirements.txt` (or let VS Code's `"pip install (functions)"` task do it).
  4. Copy `local.settings.template.json` → `local.settings.json`; fill in all values per §Environment variables.
  5. Add NetSuite private key (if doing NetSuite work) to a `.env` file in the same folder. Filename literally `.env` — loaded by `dotenv.load_dotenv(override=True)` at the top of every module.
  6. `func start` (or press F5 in VS Code — launches `"func: host start"` task and attaches the debugger on `localhost:9091` per `.vscode/launch.json`).
  7. Routes available at `http://localhost:7071/api/...` — every route in §Data Flow is reachable.

- `### Local setup — one-shot scripts`
  - `F92_notification_retrofitting_app/`: `pip install -r requirements.txt`; create a `.env` with `cosmos_hostname`, `cosmos_key`, `cosmos_database`, `application_id`, `api_url`, `api_key`; `python migrate.py`. **Do not run against prod without coordination** — creates two notification docs per Fusion user.
  - `F92_notification_cron_update/`: **the committed `.env` points at prod**. Do not run `python update.py` with the committed env or you will set every Fusion prod notification to `* * * * *`. Scrub the `.env` first.

- `### Running tests`
  - `cd fusion_92/F92_workflow_app && pytest` — runs only `test/test_job_calculations.py` (4 classes, 556 lines). No pytest config file; pytest discovers via default `test_*.py`.
  - No CI. **There is no `.github/workflows/` anywhere in this repo.** Test failures block nothing.
  - Test data fixtures live in `test/resources.py`.
  - `test_function.ps1` is a PowerShell smoke test against `http://localhost:7071/api/f92_notification` — that endpoint does not exist in the current code. Script is stale; don't rely on it.

- `### Debugging`
  - **VS Code debugpy** — configured. F5 → Attach to Python Functions on `localhost:9091`.
  - **Application Insights** — enabled via `host.json`. Deployed function-app resources have AI linked; query via Azure Portal.
  - **Request correlation** — none beyond Azure Functions' default `InvocationId` (surfaces in AI traces).
  - **Local console logs** — `logging.info/error` (stdlib). Structured logging is not used.
  - **Debugging timer functions locally** — set the target function's `Disabled` setting to `false` in `local.settings.json` AND invoke the matched HTTP endpoint (every timer has one per the `function_app.py` docstring rule). E.g. to test `f92_status_change_notifications`, POST to `http://localhost:7071/api/dax/notifications/send/status`.

- `### Common pitfalls`
  - **DST cron toggle is manual** — cron strings in `function_app.py` must be edited twice a year and redeployed. Both summer and winter decorators are kept in the file, one commented.
  - **Timer slot-disable** — in Azure, every timer function must be disabled in the staging slot (`AzureWebJobs.<func>.Disabled=true` as a **slot-specific** setting — tick "Deployment Slot" when creating). Missing this causes double-sends when staging is warm.
  - **`core_api_url` must end with `/`** — every client concatenates `f"{CORE_API_URL}{route}"`; missing trailing slash produces `/v1application/read` (broken) instead of `/v1/application/read`.
  - **`override=True` in dotenv** — every module does `dotenv.load_dotenv(override=True)` at import. If you have system env vars set from a previous `func host start` run, a new `.env` will overwrite them. Conversely, running `python update.py` in a shell with leftover env vars from a prior test can mix up environments. Export clean shells.
  - **NETSUITE_PO_PROJECT_MANAGER_ID naming mismatch** — `local.settings.template.json` uses `NETSUITE_PO_PROJECT_MANAGER_LEAD` (key suffix `LEAD`) but `workflows/netsuite.py:232` reads `NETSUITE_PO_PROJECT_MANAGER_ID` (suffix `ID`). One of the two needs to be renamed to match; in production this env var must be set under `NETSUITE_PO_PROJECT_MANAGER_ID`.
  - **Microsoft Ads CLIENT_ID hard-coded** — `bing_ads.py:31` hard-codes `CLIENT_ID = "98fe3659-…"`. The env-var note in `local.settings.template.json` ("FILL IN FROM DASHLANE - SAME IN ALL ENVS") is misleading; the code ignores `MICROSOFT_ADS_CLIENT_ID`. Document the ID in vault for reference.
  - **`f92_notification` endpoint in `test_function.ps1` doesn't exist** — the script is from an older iteration. Disregard or delete.
  - **Committed `.env` in `F92_notification_cron_update/`** — production Cosmos credentials checked into git. See §Security.
  - **No `pyproject.toml` / no version pins** — `requirements.txt` is unpinned; drift between envs is possible. Consider `pip freeze > requirements.lock` locally to reproduce.
  - **Email-send path goes through core_api** — if `application/email` is unavailable, every notification fails silently per-doc (the `try/except` in `route_send_status_change_notifications` at `notifications/routing.py:85-93` just prints the error and appends to the `errors` list). Always check core_api health when diagnosing missing emails.

---

### Section 5 — `## Deployment`

**Purpose:** How the function app lands in Azure, and the environment topology.

**Sub-sections:**

- `### Infra at a glance`
  - **Deploy target:** Azure Functions (one function app per environment).
  - **Runtime:** Python v2 programming model, extension bundle `[4.*, 5.0.0)`.
  - **Auth:** `AuthLevel.FUNCTION` — all HTTP routes require `x-functions-key`.
  - **Environments exist for: QA, TEST, PROD** (inferred from `local.settings.template.json` comments and naming pattern; cross-reference [[azure-environments]] and [[deployment-groups]] for the canonical list; naming follows [[aldc-naming-convention]] — expect `aldc<env>fnap<f92work|dax>1c01` or similar).
  - **Storage:** one storage account per function app (`AzureWebJobsStorage`). Storage Queue is *not* used directly by this repo — emails route through core_api's queue.

- `### No CI/CD pipeline exists in this repo**
  - Verify: `ls .github/workflows/` → does not exist. No `.github/` folder at repo root, in `fusion_92/`, or in any sub-app. No Azure DevOps pipeline. No Makefile or deploy script committed.
  - Deployment is **manual** — almost certainly via the VS Code Azure Functions extension's "Deploy to Function App" right-click action (scaffold supports this — `.vscode/settings.json` has `azureFunctions.deploySubpath: "."` and `scmDoBuildDuringDeployment: true`). Alternatively `func azure functionapp publish <app-name>` from the `F92_workflow_app` folder.
  - **Flag as tech debt** — no PR gate, no test-must-pass, no reproducible build. Pair this with the "no CI tests" pitfall above.
  - Contrast with [[eclipse-azure-deployment]] (slot-swap CI/CD) and the paired-slot model in [[entities/repos/flight-check|flight-check (repo)]]. This repo is **an outlier** in the ALDC Azure-deployed portfolio.

- `### Deployment steps (manual)`
  1. Ensure `local.settings.json` locally is scrubbed (don't leak local secrets into deployment).
  2. Right-click `F92_workflow_app/` in VS Code Azure Functions extension → "Deploy to Function App…" → pick the env.
  3. After deploy, in Azure Portal → Function App → Configuration, set:
     - All env vars from §Environment variables.
     - For the **staging slot**: set `AzureWebJobs.f92_refresh_microsoft_ads_token.Disabled=true`, `AzureWebJobs.f92_flight_check_flight_sync.Disabled=true`, `AzureWebJobs.f92_flight_check_job_sync.Disabled=true`, `AzureWebJobs.f92_out_of_range_pacing_notifications.Disabled=true`, `AzureWebJobs.f92_flight_end_pacing_notifications.Disabled=true`, `AzureWebJobs.f92_status_change_notifications.Disabled=true`. **Mark each as "Deployment Slot" scoped** (checkbox in Azure Portal) so a slot-swap doesn't move them into prod.
  4. Twice a year (spring-forward / fall-back): edit `function_app.py` to swap the commented-in cron strings between summer/winter, redeploy. No automation.
  5. Cross-link slot-swap mechanics to [[eclipse-azure-deployment]] if this repo ever migrates to that pattern.

- `### Rollback`
  - **Manual** — re-deploy the previous commit. No slot-swap safety net (no pipeline to swap).
  - For one-shot scripts (`F92_notification_cron_update`, `F92_notification_retrofitting_app`) there is no rollback — they are idempotent by design (upsert / `found_flag` re-entry guard) but a bad run against prod leaves state to clean up manually.

- `### Secrets management`
  - Function keys (`x-functions-key`, Host key) — managed in Azure Portal → Function App → App keys.
  - NetSuite + Microsoft Ads + Cosmos keys — rotated in Dashlane + Azure App Configuration.
  - **Vault pointers:** execution session should add one-line pointers under `vault/infra-credentials.md` § Fusion92 for every hard-coded production value found (extracted during plan session):
    - `cosmos_hostname` = `aldcprodcsdb1c01.documents.azure.com` (from `F92_notification_cron_update/.env:1`).
    - `cosmos_key` = `6AmlcEuJ…rg==` (from `F92_notification_cron_update/.env:2`). **ACTION: rotate after extract.**
    - Commented-out `cosmos_hostname_dev` = `aldcdevcsdb2c01.documents.azure.com` (line 3) and `cosmos_key_dev` (line 4). **Rotate.**
    - Commented-out `cosmos_hostname_test` = `aldctestcsdb1c01.documents.azure.com` (line 5) and `cosmos_key_test` (line 6). **Rotate.**
    - `application_id` = `9b9a62ab-6021-4147-85f9-74f9ebe9767a` (line 10 — same as `APPLICATION_FLIGHT_ID` in `global_constants.py:35`; not sensitive).
    - `account_id` = `0fc00e34` (line 12 — Fusion prod account id; not sensitive).
    - Microsoft Ads `CLIENT_ID` = `98fe3659-b606-4550-9b16-c5e51a792618` (hard-coded `bing_ads.py:31`; not sensitive).
    - NetSuite app IDs `APPLICATION_FLIGHT_ID` and `APPLICATION_JOB_ID` (hard-coded `global_constants.py:34-35`; not sensitive but document).
  - Execution session must follow wiki CLAUDE.md rule #2: **redact the sensitive values from wiki page; record them in `vault/infra-credentials.md`; the wiki page references them by name only**.

---

### Section 6 — `## API Reference`

**Purpose:** Complete request/response surface so future maintainers don't have to re-read `function_app.py`.

**Content:**

- Reproduce a full endpoint table. Columns: `Method`, `Path`, `Namespace`, `Handler`, `Purpose`, `Key request/response shape`, `Caller`.
- Rows (all paths prefixed `/api/` by Azure Functions):
  - `GET dax/jobs/{job_id}` — `dax_api/jobs` — `dax_get_job` → `get_job` (`routing.py:86-106`) — returns `JobDocument` (Pydantic). Query: `add-calc=true`.
  - `GET dax/jobs/{job_id}/flights` — `dax_api/jobs` — `dax_get_all_flights` → `get_all_flights` (`routing.py:109-131`) — returns `list[FlightDocument]`.
  - `GET dax/flights/{flight_id}` — `dax_api/jobs` — `dax_get_flight` → `get_flight` (`routing.py:54-73`).
  - `POST dax/calculations` — `dax_api/jobs` — `dax_get_flight_calculations` → `get_flight_calculations` (`routing.py:76-83`). Body: `FlightDocument`. Response: `FlightCalculations`.
  - `GET dax/jobs/{job_id}/export?type=&orientation=&flight_ids=` — `dax_api/jobs` — `dax_get_single_job_flight_export` → `build_single_job_flight_export` (`routing.py:135-160`). Response: `DaxExport` (base64 xlsx string).
  - `POST dax/jobs/export` — `dax_api/jobs` — `dax_get_all_job_flight_export` → `build_all_job_flight_export` (`routing.py:163-191`). Body: `MultiJobExportRequestParams`.
  - `POST dax/notifications/send/status` — `dax_api/notifications` — `dax_notifications_send_status_change` → `route_send_status_change_notifications`. Body: `StatusChangeNotificationRequestParams`. Response: `LegacyChangeNotificationResponse`.
  - `POST dax/notifications/send/pacing` — `dax_api/notifications` — `dax_notifications_send_pacing` → `route_send_pacing_notifications`. Body: `PacingNotificationRequestParams`. Response: `NotificationResponse`.
  - `POST dax/sync/jobs` — `dax_api/sync` — `dax_sync_jobs` → `sync_flight_check_jobs` (`sync/routing.py:11-14`). Body: `{only_recent: bool}`.
  - `POST dax/sync/flights` — `dax_api/sync` — `dax_sync_flights` → `sync_flight_check_flights` (`sync/routing.py:5-8`). Body: `{only_recent: bool}`.
  - `POST f92_netsuite_po_sync` — `workflows/netsuite` — `f92_netsuite_po_sync` → `F92NetsuitePOWorkflow.run()`. Body: `{account_id, flight_id}`. Response: legacy wrapper with `synced_po` dict.
  - `GET f92_netsuite_publishers?account_id=…` — `workflows/netsuite` — `f92_netsuite_publishers`. Response: `[{id, name}]` (vendor list).

- **Response envelopes — two shapes, by namespace**:
  - **DAX API:** body is `api_success(model)` → HTTP 200 + JSON body of the Pydantic model. Errors raise `APIError(kind, message, context, http_code)` and are caught by `@handle_dax_api_errors`, returning `{error, error_description, error_context}` with the correct status code.
  - **Legacy workflow:** body is `success_response(message, data)` → `{"response": {"code": 200, "message": ..., "data": ...}}` (HTTP 200 with the envelope status code **repeated in the body**). Errors use `workflow_error_response` / `exception_response` with the same envelope shape and the HTTP status code matching `error.http_code`.
  - Execution session must emphasise that these envelopes are *incompatible* — flight-check's `lib/dax/apiUtils.ts` handles only the DAX-API shape; `/api/netsuite/*` handlers on flight-check handle the legacy shape.

- **Timer schedule table** — reproduce the 6 timer functions with their summer/winter CRONs (from §Data Flow). Add a note that CRONs use NCrontab (Azure Functions) 6-field format (seconds included) — the `0 0 14 * * *` form is correct for NCrontab, not standard 5-field cron.

---

### Section 7 — `## Schemas`

**Purpose:** Point at the Pydantic models so a developer doesn't have to go hunting.

**Content:**

- `dax_api/jobs/schema.py` (~25 KB) — `FlightDocument`, `JobDocument`, `FlightCalculations`, `JobCalculations`, `MetricsTableRow`, `FlightStatus` (StrEnum), `CalculationSource` (StrEnum: `Direct`, `Dax`, `Smartsheet`, `Grouped`), `SingleJobExportRequestParams`, `MultiJobExportRequestParams`, `DaxExport`. Note `PLATFORM_TECH_PERCENTAGE_PLATFORMS` gate — `dax_tech_percentage` is only applied when `platform` is in the valid list (`global_constants.py:56`).
- `dax_api/notifications/schema.py` — `NotificationDocument`, `StatusReportSetting`, `PacingNotificationSetting`, `PacingNotificationType` (StrEnum: `out-of-range`, `flight-end`, `all`), `PacingNotificationRequestParams`, `NotificationResponse`, `StatusChangeNotificationRequestParams`, `LegacyChangeNotificationResponse`.
- `dax_api/sync/schema.py` — `DataStoreDocument`, `SyncJobDocument`, `SyncFlightDocument`, `FlightMetricsUploadRow`.
- `dax_api/users/schema.py` — user schema used by notification recipient lookup.
- **No schemas in `workflows/` legacy namespace** — all dict-shaped.

Also note the **timezone/date helpers** at `dax_api/lib/date.py` and the small string helper at `dax_api/lib/string.py`. Keep this section short — real reference is the schema files.

---

### Section 8 — `## Security & Credentials`

**Purpose:** Be explicit about the trust boundaries and the credential extraction actions.

**Sub-sections:**

- `### Committed credentials — ACTION REQUIRED`
  - `F92_notification_cron_update/.env` contains production Cosmos hostname + key (lines 1-2) plus commented-out dev + test hostnames/keys (lines 3-8). Git history will retain these.
  - **Action for execution session:**
    1. Extract the values to `vault/infra-credentials.md` § Fusion92 (per wiki rule #2).
    2. Do **not** include the values in the wiki page body; reference the vault by name.
    3. Append an action item to `action-items.md` titled "Rotate Fusion92 Cosmos keys (prod/dev/test) — exposed in `workflows/fusion_92/F92_notification_cron_update/.env`" with source `from [[workflows]]` and ref `[[fusion92]]`.
    4. Suggest to Paul (not auto-edit) that `.env` be added to `F92_notification_cron_update/.gitignore` and the file removed from git, then rewrite history if the keys were widely distributed.

- `### Auth model`
  - HTTP: `AuthLevel.FUNCTION` everywhere → `x-functions-key`.
  - Internal: every NetSuite and "Fusion-only" endpoint checks `body["account_id"] == FUSION_ACCOUNT_ID` and returns 403 otherwise.
  - Inter-service: core_api authenticates this app with a bearer token (`core_api_token`) passed as `Authorization`. Token lives in Azure App Configuration per-env.
  - NetSuite: OAuth2 client_credentials grant with JWT client assertion (ES256). Private key in env.
  - Microsoft Ads: OAuth2 refresh-token flow via `bingads.authorization.OAuthWebAuthCodeGrant`. Refresh token is persisted in the Cosmos connection document; refreshed daily by the timer function.

- `### Trust boundaries`
  - This app trusts core_api's identity via the static `core_api_token`.
  - Flight-check trusts this app via a function key (one of three separate keys).
  - NetSuite trusts this app via JWT-signed client assertion.
  - No mutual-TLS anywhere.

- `### Known risks`
  - Committed `.env` (see above).
  - No PR gate, no tests-in-CI → regressions ship.
  - Microsoft Ads `CLIENT_ID` in source (low-risk; public in the OAuth flow).
  - Cron-based deployments have no rollback safety.

---

### Section 9 — `## Tech Debt & Known Issues`

**Purpose:** One place to surface everything the execution session found worth surfacing.

**Content:** mix of what's already called out above, consolidated:

- **No CI/CD** (no `.github/workflows/` anywhere; manual VS Code deploys; no test gate).
- **Two parallel API patterns** (`dax_api/` contract-first vs `workflows/` legacy dict-based) — ongoing migration per `function_app.py` docstring.
- **DST cron switch is manual** (twice-yearly deploy; both schedules coexist in source).
- **`NETSUITE_PO_PROJECT_MANAGER_LEAD` vs `NETSUITE_PO_PROJECT_MANAGER_ID` naming mismatch** between template and code.
- **Microsoft Ads `CLIENT_ID` hard-coded** despite env-var placeholder.
- **`test_function.ps1` references a non-existent endpoint** (`/api/f92_notification`).
- **`F92_notification_cron_update/` commits prod creds** in `.env` (security — see §Security).
- **`F92_notification_cron_update/update.py` is a destructive utility** (sets every Fusion notification to once-per-minute) — no safety guard, works against whatever Cosmos the committed `.env` points at.
- **One-shot scripts bypass core_api** (talk to Cosmos directly with `azure-cosmos`) — they break the repo's otherwise-consistent "go through core_api" rule.
- **`dataset/query` vs `dataset/request`** — `DaxCoreAPIClient.dataset_query_validated` uses the legacy route with a FIXME noting the new endpoint isn't in production as of 2026-01.
- **No `pyproject.toml`, unpinned deps** — version drift risk.
- **Single test file** — `test/test_job_calculations.py`. No test coverage for the NetSuite or Microsoft Ads workflows, notifications, or sync.
- **README is one line** — "Repository for client specific code". No architectural intent documented in-repo. (This wiki page *is* the README.)
- **Timer-slot-swap discipline** is manual and documented only in docstrings inside `function_app.py`. Easy to miss during first deploy.
- **Committed hard-coded `ECLIPSE_BASE_URL`** defaults to `https://fusion92.eclipse.aldc-ca-w1.com` — a deployed environment URL. Not sensitive but worth noting.

---

### Section 10 — `## See Also`

Wikilinks to related pages. Must include:
- [[dax-media-app]] — **the product** this repo's F92_workflow_app is the backend of. Heaviest cross-link. Business scope, status taxonomy, UAT history.
- [[entities/repos/flight-check|flight-check (repo)]] — **the frontend** that calls every HTTP route in this repo. See its API-proxy table for caller/callee side of every endpoint. *(Disambiguate vs [[flight-check]] ops-runbook.)*
- [[connector-token-refresh]] — documents the **manual fallback** for the Microsoft Ads refresh-token workflow that `f92_refresh_microsoft_ads_token` automates daily. The runbook already references "the Fusion workflow function app for each environment".
- [[bing-ads]] — Bing Ads / Microsoft Advertising connector page.
- [[fusion92]] — the client. `FUSION_ACCOUNT_ID = "0fc00e34"` and timezone decisions originate here.
- [[core_api]] — every HTTP-handler and workflow calls core_api via `DaxCoreAPIClient` / `LegacyCoreAPIClient`. Email send goes through core_api's `application/email`.
- [[core-api-data-model]] — context for the `datastore/upload` / `datastore/get` endpoints used by the sync workflow.
- [[cosmosdb-schema]] — context for the `notification`, `user`, `work_connection`, `application` containers the retrofit + cron scripts + main app touch.
- [[CosmosDB]] — tool page.
- [[data-pipeline-flow]] — this repo's `FlightCheckSnowflakeSyncWorkflow` is a leaf of the platform-wide pipeline; cross-reference.
- [[fusion92-platform-ids]] — platform account/campaign/order ID mapping, complementary to the `PLATFORM_TECH_PERCENTAGE_PLATFORMS` gate.
- [[fusion92-data-architecture]] — Fusion92 Snowflake setup.
- [[azure-environments]], [[deployment-groups]], [[aldc-naming-convention]] — Azure context.
- [[Azure]], [[GitHub Actions]] — tool pages. (`GitHub Actions` gets a See Also with the footnote that **this repo doesn't use it yet**.)
- [[mailjet]] — downstream of core_api's `application/email` (email sending).
- Do NOT link [[dax-ai]] — different product despite similar name.
- Do NOT link [[connector]] — separate data-plane repo; no overlap.

---

### Judgment calls

- **Single wiki page is correct container.** The repo is small (one function app + two scripts, ~50 source files total). Splitting would fragment. Target budget **~700–1000 lines**. Hard stop at 1200; if it crosses, split Section 6 (API Reference) into a standalone page under `concepts/architecture/dax-api-reference.md`.
- **"Data Flow" IS applicable and is substantive.** Both inbound HTTP (from flight-check) and outbound scheduled work (timers + sync to Snowflake + email) are material. Do not skip this section. It is the primary value-add over what [[dax-media-app]] already says.
- **Do not create per-sub-project wiki pages.** The two one-shot scripts (`F92_notification_retrofitting_app`, `F92_notification_cron_update`) each take ~one subsection of the main page. They are not independent wiki entities.
- **Do not create a separate page for "DAX API".** The "DAX API" is flight-check's name for this repo's `F92_workflow_app`. It's the same thing. Folding it into `workflows` avoids a zombie page. The flight-check page's flagged "gap: DAX API has no wiki page yet" is resolved by linking to this page.
- **Extract committed credentials to vault BEFORE drafting the wiki body.** Wiki rule #2 is non-negotiable. Execution session must:
  1. Open `vault/infra-credentials.md`; add a `## Fusion92 — Cosmos DB (exposed in workflows repo)` block.
  2. Record the three `(hostname, key)` pairs and the `application_id` + `account_id`.
  3. Reference by name in the wiki page body (e.g., *"see vault/infra-credentials.md § Fusion92 — Cosmos DB"*). **Never inline the key value in the wiki page.**
  4. Open `action-items.md` and append one item per the Security section.
- **Do NOT file a separate vault entry for hard-coded `APPLICATION_FLIGHT_ID` / `APPLICATION_JOB_ID` / `MICROSOFT_ADS_CLIENT_ID`.** These are identifiers (UUIDs / OAuth client IDs), not secrets. They belong in the wiki page inline for reference.
- **Disambiguation block is mandatory.** Four adjacent pages (`dax-media-app`, `flight-check (repo)`, `flight-check` ops-runbook, `dax-ai`) could all be confused with this one. Put the callout at the top.
- **Mention the `workflows` folder-within-F92_workflow_app is unfortunately named.** The package `F92_workflow_app/workflows/` (legacy Python package with `bing_ads.py` + `netsuite.py`) has the same name as this repo (`workflows`). Note the collision once and move on.
- **Do NOT document every route handler body.** API Reference table is enough; full behaviour is in-repo. A wiki page is not a replacement for docstrings.
- **Close the flight-check wiki gap.** Once this page exists, update the flight-check repo page's intro (line 18) — *"the DAX API (Azure Functions — no wiki page yet; flagged as gap)"* should become *"the DAX API ([[workflows|workflows repo]] — `F92_workflow_app`)"*. Execution session should make this edit as part of finalising the page. Also: flight-check line 124 has `${F92_NETSUITE_WORKFLOW_URL}/api/f92_netsuite_po_sync` — add a one-line note that the NetSuite Workflow URL and `DAX_API_URL` point at the *same* function app (two env vars, one target).
- **Close the gap in [[dax-media-app]].** That page says "email notifications for flight status transitions" but doesn't say *where they're sent from*. Add a one-line back-reference to `[[workflows]]` as implementation.
- **Close the gap in [[connector-token-refresh]].** Already mentions "Fusion workflow function app" generically. Add an explicit `[[workflows|workflows repo]]` wikilink where that phrase appears.
- **No in-repo `docs/` writes.** Per boot prompt. Wiki only.
- **No modifications to source code.** Per boot prompt.
- **Cross-reference hygiene — must link:** [[dax-media-app]], [[entities/repos/flight-check|flight-check (repo)]], [[core_api]], [[fusion92]], [[connector-token-refresh]], [[bing-ads]], [[core-api-data-model]], [[cosmosdb-schema]], [[data-pipeline-flow]]. Should link: [[azure-environments]], [[deployment-groups]], [[aldc-naming-convention]], [[Azure]], [[GitHub Actions]] (with "not used here" note), [[mailjet]], [[fusion92-data-architecture]], [[fusion92-platform-ids]]. Do **not** link: [[dax-ai]] (unrelated despite name), [[connector]] (data-plane is different), [[flight-check]] ops-runbook (disambiguate).
- **README gap** — the repo's in-tree `README.md` is one line. The wiki page effectively becomes the README. Don't recommend editing the in-repo README (out of scope for this workstream).
- **Page length:** plan for ~800 lines, ceiling 1000. API reference table will be the longest section.
- **Tone:** neutral technical. Do not editorialise on the tech-debt items beyond what's objective.

### Session Log entry to add (executor should append after writing the page)

```
### 2026-04-20 — workflows plan session complete

- did: read repo thoroughly — README.md; fusion_92/F92_workflow_app/ (function_app.py, global_constants.py, host.json, requirements.txt, local.settings.template.json, .funcignore, .gitignore, .vscode/{settings,tasks,launch}.json, test_function.ps1); dax_api/{jobs,notifications,sync,users,lib}/*.py; workflows/{bing_ads,netsuite,lib}.py; test/{resources,test_job_calculations}.py; fusion_92/F92_notification_retrofitting_app/{migrate.py, requirements.txt}; fusion_92/F92_notification_cron_update/{update.py, .env, requirements.txt}. Cross-read existing wiki pages: index.md, entities/repos/{flight-check,core_api,eclipse_exp,eclipse,connector,custom-fusion-92-audience-api,claude_code_enhanced}.md, entities/projects/{dax-media-app,dax-ai}.md, entities/clients/active/fusion92.md, processes/operations/connector-token-refresh.md.
- produced: 10-section plan for new wiki page `entities/repos/workflows.md` — Intro (disambiguation-heavy), Architecture (repo layout + tech stack + dax_api vs workflows split + request flows + key abstractions + global_constants), Data Flow (inbound HTTP, outbound timers, Snowflake upload via core_api datastore, NetSuite PO write path, notification email path, one-shot scripts), Developer Guide (prereqs, env vars, local setup for all 3 sub-apps, tests, debugging, pitfalls), Deployment (no CI/CD, manual deploy, rollback, secrets), API Reference (12-row endpoint table + timer-schedule table + two response envelopes), Schemas (Pydantic model pointers), Security & Credentials (committed-cred action items + auth model + trust boundaries + known risks), Tech Debt (13+ issues), See Also.
- decided: single wiki page (repo is small); Data Flow is a full section (repo is both API and scheduler); do not create sub-pages for the two one-shot scripts; do not create a separate "DAX API" page (same thing); extract committed Cosmos credentials to `vault/infra-credentials.md` before writing wiki body; disambiguation block vs [[dax-media-app]], [[flight-check]] (both repo and runbook), [[dax-ai]] is mandatory at top; close existing wiki gaps in [[entities/repos/flight-check|flight-check (repo)]] (line 18 "no wiki page yet"), [[dax-media-app]] (add backlink), [[connector-token-refresh]] (explicit wikilink) as part of execution.
- flagged: **SECURITY — committed prod Cosmos hostname + key in `fusion_92/F92_notification_cron_update/.env`** plus commented-out dev + test keys. Extract to vault, rotate, suggest gitignore + history rewrite. Other flags: no CI/CD (no `.github/workflows/` anywhere); `NETSUITE_PO_PROJECT_MANAGER_LEAD` vs `NETSUITE_PO_PROJECT_MANAGER_ID` env-var naming mismatch; Microsoft Ads `CLIENT_ID` hard-coded despite template placeholder; `test_function.ps1` references non-existent endpoint; `F92_notification_cron_update` is a destructive utility pointed at prod by committed `.env`; DST cron toggle is manual; one-line README; single pytest file; two parallel API namespaces (`dax_api/` target vs `workflows/` legacy) — migration in progress.
- next: execution session (Sonnet) — (1) extract creds to `vault/infra-credentials.md` § Fusion92; (2) append rotation action to `action-items.md`; (3) create `entities/repos/workflows.md` (~700–1000 lines) per this plan; (4) update [[entities/repos/flight-check|flight-check (repo)]] to remove "DAX API no wiki page yet" gap; (5) add backlinks from [[dax-media-app]] and [[connector-token-refresh]]; (6) add new repo entry to `index.md` under Entities › Repos; (7) mark Execution ✅ in this tracker; (8) append to `log.md`.
```

---

## prospect-site-template — Approved Plan

**Plan session:** 2026-04-20 (Opus)
**Target wiki page:** `wiki/entities/repos/prospect-site-template.md` (new page — confirmed absent)
**Wiki index entry:** add under `Entities › Repos` alongside `eclipse`, `flight-check`, `workflows`, etc.

> Disambiguation note for the execution session: this repo is the **generator**, not any individual deployed site. The string "prospect site" does not appear on any existing wiki page. The nearest adjacent entity is [[zeus-memory]] (the product whose `/api/memory` endpoint the chat route optionally POSTs to) — this repo is not that project. There is also no existing `analyticlabs.io` entity page, despite `create-site.sh` embedding `${SUBDOMAIN}.analyticlabs.io` as the target domain. Execution session should NOT create a new `analyticlabs.io` page — it would be stub-weight and there's no upstream source. One committed PostHog key belongs in the wiki prose (it's openly `NEXT_PUBLIC_*`, low-sensitivity by design — see Judgment calls).

### Doc structure — single wiki page with these sections

All content goes into one page: `wiki/entities/repos/prospect-site-template.md`. Sections in the order they should appear. Each section names the heading and lists the concrete anchors (file paths, component names, route names, env vars, config fields) the execution session should fill prose around.

---

### Frontmatter

```yaml
---
tags: [entity, repo, prospect-site-template, nextjs, marketing, template, ai-generated]
aliases: [prospect-site-template, AnalyticLabs prospect microsites, Cultivate template, analyticlabs.io microsites]
sources: [repos/prospect-site-template/README.md, repos/prospect-site-template/CLAUDE.md, repos/prospect-site-template/CONTRIBUTING.md, repos/prospect-site-template/package.json, repos/prospect-site-template/next.config.ts, repos/prospect-site-template/tsconfig.json, repos/prospect-site-template/tailwind.config.ts, repos/prospect-site-template/vitest.config.ts, repos/prospect-site-template/eslint.config.mjs, repos/prospect-site-template/create-site.sh, repos/prospect-site-template/.env.example, repos/prospect-site-template/site.config.example.ts, repos/prospect-site-template/src/lib/types.ts, repos/prospect-site-template/src/lib/config.ts, repos/prospect-site-template/src/app/layout.tsx, repos/prospect-site-template/src/app/page.tsx, repos/prospect-site-template/src/app/error.tsx, repos/prospect-site-template/src/app/globals.css, repos/prospect-site-template/src/app/api/chat/route.ts, repos/prospect-site-template/src/app/calculator/page.tsx, repos/prospect-site-template/src/app/chat/page.tsx, repos/prospect-site-template/src/app/why-aldc/page.tsx, repos/prospect-site-template/src/components/nav.tsx, repos/prospect-site-template/src/components/hero-section.tsx, repos/prospect-site-template/src/components/ecosystem-diagram.tsx, repos/prospect-site-template/src/components/decision-tree.tsx, repos/prospect-site-template/src/components/zeus-chat.tsx, repos/prospect-site-template/src/components/dashboard/dashboard-page.tsx, repos/prospect-site-template/src/components/dashboard/sidebar.tsx, repos/prospect-site-template/src/components/dashboard/kpi-card.tsx, repos/prospect-site-template/src/components/pitch/pitch-page.tsx, repos/prospect-site-template/src/__tests__/setup.ts, repos/prospect-site-template/src/__tests__/live-config.test.ts, repos/prospect-site-template/src/__tests__/site-variants.test.ts, repos/prospect-site-template/src/__tests__/claude-md-claims.test.ts, repos/prospect-site-template/src/__tests__/fixtures/configs.ts, repos/prospect-site-template/src/__tests__/fixtures/dashboard-configs.ts, repos/prospect-site-template/.github/workflows/ci.yml, repos/prospect-site-template/docs/source-analysis.md]
created: 2026-04-20
updated: 2026-04-20
---
```

---

### Section 1 — Intro paragraph (top of page, no heading)

**Purpose:** Tell a cold reader exactly what this repo is in the first paragraph so they don't confuse it with (a) an individual deployed prospect site, (b) [[eclipse]]/[[entities/repos/flight-check|flight-check (repo)]] (the other Next.js repos), or (c) [[zeus-memory]].

**Key content:**

- One-sentence identity: *a single Next.js 15 application whose entire content — theme, copy, sections, calculator tree, chat system prompt — is driven by one gitignored `site.config.ts` file; Claude Code generates that config from a natural-language prompt, then the resulting folder is copied out and deployed as its own site.*
- Positioning: the repo produces **many sibling microsites** at `<subdomain>.analyticlabs.io` (Cultivate, Strategy, Packaging, EPR, Ghost Pine, AgriStack, etc. — the 15 known sites analysed in `docs/source-analysis.md`). It is the **template/factory**, not any one deployed site. Each site is eventually deployed as an independent copy (Vercel, Cloudflare Pages, Netlify, any Node host — `README.md:64-67`).
- What's unusual: README says "one config file, one codebase, three templates, any ALDC prospect microsite" (`README.md:1-3`). The codebase is deliberately shared and immutable per-site — only `site.config.ts` changes (gitignored; copied from `site.config.example.ts` by `postinstall` per `package.json:11`). This is the opposite of forking-a-template.
- Three templates selected by the `template` field (`src/lib/types.ts:268`): `"landing"` (11-site Cultivate family — dark theme, 8 scrolling sections, animated hero, ecosystem SVG, decision-tree calculator, optional Zeus Chat), `"dashboard"` (2-site family: Ghost Pine + AgriStack — light theme, sidebar, KPIs, Zeus Chat FAB), `"pitch"` (1-site: WhyALDC — dark, compounding-bars hero, lead capture form, AI comparison).
- How a site gets made: user writes a prompt → Claude reads `CLAUDE.md` → Claude picks template, reads `src/lib/types.ts` (schema) + `site.config.example.ts` (working example) → Claude generates `site.config.ts` → runs `npx vitest run` + `npm run build` → site ready at `npm run dev`. User then copies the entire folder with `cp -r .` to preserve and deploy (`CLAUDE.md:11-29`, `README.md:55-68`).
- Scale anchors: 3 page templates, 15 known prospect sites (11 cultivate + 2 dashboard + 1 pitch + 1 producer; `docs/source-analysis.md:13-21`, `src/__tests__/fixtures/configs.ts:850-883`), ~13 shared React components, 11 test files, ~260 test-definition sites (spec, `describe`/`it`/`test` greps — **note count discrepancy**: README line 83 says "624 tests", CONTRIBUTING line 22 says "394 tests"; actual `npx vitest run` should be the source of truth — execution session must run it to settle the number).
- Target domain: `<subdomain>.analyticlabs.io` — hard-coded pattern in `create-site.sh:20` and `README.md:12`. There is no [[analyticlabs.io]] wiki page and this plan intentionally does not create one (no upstream source to cite).
- Deployment target: confirmed Vercel for the existing 15 sites per `docs/source-analysis.md:342-348` (presence of `dpl_*` deployment IDs in chunk URLs). Repo itself is framework-portable — the suggested deploy hosts in README are "Netlify, Cloudflare Pages, Docker, any Node host" (`README.md:66`).

---

### Section 2 — `## Architecture`

**Purpose:** Give a reader the mental map for the codebase in one screenful, then drill into the template-selection + config-driven design.

**Sub-sections:**

- `### Repository layout` — tree with one-line purposes. Source of truth: `ls` of repo root + `CLAUDE.md:41-51`.

  ```
  prospect-site-template/
  ├── README.md                        # User-facing intro: quick start, templates, routes, CI
  ├── CLAUDE.md                        # AI-agent instructions (what to do when a user says "make me a site")
  ├── CONTRIBUTING.md                  # Commit-time checks (lint, prettier, typecheck, tests)
  ├── package.json                     # Next 15.3, React 19.1, Tailwind 3, posthog-js, vitest
  ├── next.config.ts                   # Just `reactStrictMode: true`
  ├── tsconfig.json                    # Strict; `@/*` → `./src/*`
  ├── tailwind.config.ts               # IMPORTS site.config at build time — accent/glow are per-site
  ├── postcss.config.mjs               # tailwind + autoprefixer
  ├── vitest.config.ts                 # jsdom, @vitejs/plugin-react, `@/*` alias
  ├── eslint.config.mjs                # extends next/core-web-vitals + next/typescript
  ├── .prettierrc                      # 2-space, double-quote, trailing commas es5, printWidth 100
  ├── .editorconfig                    # utf-8 LF 2-space, insert_final_newline
  ├── .env.example                     # PostHog key + Anthropic key + Zeus (5 vars)
  ├── .gitignore                       # includes `site.config.ts` — gitignored on purpose
  ├── create-site.sh                   # Bash pipeline: clone template folder → apply config → install → test → build
  ├── site.config.example.ts           # Committed example (Cultivate food waste landing site)
  ├── .github/workflows/ci.yml         # Lint + prettier + typecheck + vitest + next build
  ├── docs/
  │   ├── source-analysis.md           # 1000+-line reverse-engineering of 15 deployed sites → this template
  │   └── screenshots/                 # landing-hero.png, calculator.png (referenced from README)
  ├── public/assets/
  │   ├── aldc_logo.svg                # Shipped ALDC mark
  │   └── favicon.svg                  # Favicon (referenced in layout.tsx metadata)
  └── src/
      ├── lib/
      │   ├── types.ts                 # THE schema. All config types. Source of truth for generation.
      │   └── config.ts                # `getConfig()` re-export of ../../site.config
      ├── app/
      │   ├── layout.tsx               # Root layout; injects PostHog snippet if NEXT_PUBLIC_POSTHOG_KEY
      │   ├── page.tsx                 # Template switch: landing|dashboard|pitch
      │   ├── globals.css              # Dark default + `.theme-light` override for dashboard
      │   ├── error.tsx                # Global error boundary ("Check your site.config.ts")
      │   ├── calculator/page.tsx      # /calculator (decision tree)
      │   ├── chat/page.tsx            # /chat (Zeus Chat page)
      │   ├── why-aldc/page.tsx        # /why-aldc (stub "Coming soon")
      │   └── api/chat/route.ts        # POST /api/chat — SSE proxy to Anthropic + optional Zeus log
      ├── components/
      │   ├── nav.tsx                  # Top nav (landing + pitch). Scrollspy via IntersectionObserver.
      │   ├── footer.tsx
      │   ├── sweep-divider.tsx        # 3s gradient sweep separator
      │   ├── hero-section.tsx         # Landing hero: animated words, stat cards, CTA buttons
      │   ├── problem-section.tsx      # Landing section 1
      │   ├── ecosystem-diagram.tsx    # Landing section 2 — interactive SVG graph
      │   ├── stakeholder-grid.tsx     # Landing section 3
      │   ├── platform-timeline.tsx    # Landing section 4 — exactly 4 phases
      │   ├── global-comparison.tsx    # Landing section 5
      │   ├── alignment-section.tsx    # Landing section 6
      │   ├── funding-strategy.tsx     # Landing section 7
      │   ├── join-cta.tsx             # Landing section 8
      │   ├── decision-tree.tsx        # Calculator engine (tiered outcomes, principles sidebar)
      │   ├── zeus-chat.tsx            # Chat UI — inline MD + SVG streaming renderer
      │   ├── dashboard/
      │   │   ├── dashboard-page.tsx   # Top-level dashboard layout
      │   │   ├── sidebar.tsx          # Dashboard sidebar nav (anchor links + route links)
      │   │   └── kpi-card.tsx         # KPI tile (value, change, trend)
      │   └── pitch/
      │       └── pitch-page.tsx       # Pitch template page
      └── __tests__/                   # 11 test files, Vitest + @testing-library/react
          ├── setup.ts                 # Polyfills scrollIntoView + IntersectionObserver in jsdom
          ├── live-config.test.ts      # Validates the actual site.config.ts that will be built
          ├── config-validation.test.ts
          ├── config-negative.test.ts
          ├── site-variants.test.ts    # 15 site fixtures — 11 cultivate + 2 dashboard + 1 pitch + 1 producer
          ├── dashboard-variants.test.ts
          ├── component-render.test.tsx
          ├── decision-tree.test.ts    # No cycles, all outcomes reachable, tier integrity
          ├── sections.test.ts
          ├── theme.test.ts
          ├── theme-css.test.ts
          ├── claude-md-claims.test.ts # Asserts every rule in CLAUDE.md is enforced (hero title ends with " —", etc.)
          └── fixtures/
              ├── configs.ts           # 883 lines of fixtures: themes, heroes, siteMetadata, cultivateCalculator, eprCalculator, allSiteNames
              └── dashboard-configs.ts # ghostpineDashboard, agristackDashboard, whyaldcPitch
  ```

- `### Tech stack` — table.

  | Layer | Choice | Notes |
  |---|---|---|
  | Framework | Next.js 15.3 (App Router, Turbopack dev) | `package.json:15`; `npm run dev` uses `next dev --turbopack` |
  | React | 19.1.0 | `package.json:17-18` |
  | Language | TypeScript 5.8 (strict) | `tsconfig.json:7`; no `as any` linting rule; `@/*` alias |
  | Styling | Tailwind CSS 3.4.17 + `globals.css` custom properties | `tailwind.config.ts`; `.theme-light` class swaps dashboard to light theme (`layout.tsx:32`, `globals.css:21-24`) |
  | Analytics | PostHog (inline browser snippet) | `layout.tsx:35-46`; gated on `NEXT_PUBLIC_POSTHOG_KEY` presence; host defaults to `https://us.i.posthog.com` |
  | AI chat | Anthropic Messages API (SSE stream proxied) | `src/app/api/chat/route.ts`; server-side `ANTHROPIC_API_KEY`; default model `claude-sonnet-4-6` (env `CHAT_MODEL`) |
  | AI memory | Zeus Memory (optional) | `api/chat/route.ts:9-40`; POST `${ZEUS_API_URL}/api/memory` after each conversation; failures non-fatal. Cross-link [[zeus-memory]]. |
  | Testing | Vitest 3.2 + @testing-library/react 16 + jsdom 27 | `vitest.config.ts`; `setup.ts` polyfills `scrollIntoView` and `IntersectionObserver` |
  | Lint / format | ESLint 9 (flat config, `next/core-web-vitals` + `next/typescript`) + Prettier 3 | `eslint.config.mjs`; `.prettierrc` |
  | CI | GitHub Actions — `.github/workflows/ci.yml` | Node 22; runs `npm ci` + `eslint --max-warnings 0` + `prettier --check .` + `tsc --noEmit` + `vitest run` + `next build`; asserts `.next/standalone` or `.next/server` exists |
  | Deploy target | Vercel (extant sites; confirmed via `dpl_*` in `docs/source-analysis.md:342-348`) | Repo itself has no Vercel config — each generated site is deployed independently. README names Netlify, Cloudflare Pages, Docker, any Node host as alternatives (`README.md:66`). |
  | Build output | Next.js default (`.next/`) | No `output: "standalone"` config in `next.config.ts` — CI just checks for either `standalone` or `server` directory |

- `### The three-template selection model` — **single most important architectural fact**.
  - `src/lib/types.ts:268` — `template: "landing" | "dashboard" | "pitch"` is a literal union on the top-level `SiteConfig`.
  - `src/app/page.tsx:70-86` — `HomePage()` is a `switch (config.template)` that returns one of three trees: `<LandingPage />` (Nav + HeroSection + mapped sections + Footer), `<DashboardPage />` (Sidebar + KPI grid + active section panel + Zeus FAB), or `<><Nav /><PitchPage /><Footer /></>`.
  - `src/app/layout.tsx:32` — `body className` includes `theme-light` iff `config.template === "dashboard"`. The light-theme CSS var override lives in `globals.css:21-24`. All other templates use the dark default.
  - Every component reads `getConfig()` at module load time — React Server Components import `@/lib/config` which `import`s `../../site.config`. At build time the single config determines the whole site.
  - The three templates each require different config fields (see `CLAUDE.md:57-73` and `src/lib/types.ts:270-299`):
    - `landing` requires `hero`, `sections[]`, `ecosystemDiagram`; optional `calculator`, `chat`.
    - `dashboard` requires `dashboard.sidebarLinks`, `dashboard.kpis`, `dashboard.sections`; optional `chat`; optional `dashboard.logoPath`.
    - `pitch` requires `pitch.compoundingBars` (3), `pitch.aiComparison`, `pitch.leadForm`, `pitch.valueProps` (3); optional `chat`.

- `### Config as single source of truth — tailwind reads site.config at build time`
  - Note the unusual coupling in `tailwind.config.ts:2-4`: it `import`s `./site.config` and pulls `accentColor` + `glowColor` into the theme. This means **the build graph includes `site.config.ts`** — if the config is malformed the Tailwind build fails before Next.js even compiles.
  - Consequence: `site.config.ts` **must exist before `next build`**. The `postinstall` script in `package.json:11` (`test -f site.config.ts || cp site.config.example.ts site.config.ts`) guarantees this on fresh clones. Flag this for the developer guide.
  - `globals.css:10-24` declares `--color-background` / `--color-foreground` CSS custom properties — Tailwind classes `bg-background`, `text-foreground`, `border-foreground/10`, etc. resolve through those at runtime; the accent/glow resolve through the build-time Tailwind config. This is the theming mechanism. See `source-analysis.md:132-142` for the long history.

- `### Routes table` — 4 routes total (source: `src/app/*/page.tsx` + `api/chat/route.ts`).

  | Route | File | Template behaviour | Notes |
  |---|---|---|---|
  | `/` | `app/page.tsx` | landing → full 8-section scroller; dashboard → sidebar + KPI grid; pitch → compounding bars + lead form | Template switch on `config.template` |
  | `/calculator` | `app/calculator/page.tsx` | Renders `<DecisionTree/>` if `config.calculator` is set, else "No calculator configured"; dashboard layout wraps in Sidebar | Landing-typical but works under dashboard chrome too |
  | `/chat` | `app/chat/page.tsx` | Renders `<ZeusChat/>` if `config.chat` is set | Nav/Sidebar chrome depending on template |
  | `/why-aldc` | `app/why-aldc/page.tsx` | Always renders "Coming soon" stub | Historical — was a dedicated page in the legacy sites |
  | `/api/chat` | `app/api/chat/route.ts` | POST SSE stream proxy to Anthropic; optional Zeus log | Server route (not a page) |

- `### Key abstractions` — list with one-paragraph each:
  - **`SiteConfig`** (`src/lib/types.ts:267-299`) — the contract. 35+ fields with full Pydantic-like TypeScript interfaces. Top level: `template`, `subdomain`, `siteName`, `siteLabel`, `theme` (ThemeConfig), SEO fields (`title`, `metaDescription`, `ogDescription`, `ogSiteName`, `contactEmail`, `footerTagline`, `footerEntity`), `nav` (links + optional badges), `hero`, `sections[]`, `ecosystemDiagram`, optional `calculator`, optional `chat`, optional `dashboard`, optional `pitch`. Sub-types: `ThemeConfig`, `NavLink`, `NavBadge`, `HeroConfig`, 8 section-type interfaces in a `SectionConfig` discriminated union (`ProblemSection` | `VisionSection` | `StakeholderSection` | `PlatformSection` | `GlobalSection` | `AlignmentSection` | `FundingSection` | `JoinSection`), `EcosystemNode` + `EcosystemEdge`, `DecisionNode` + `Outcome` + `Principle` + `CalculatorConfig`, `ChatPrompt` + `ChatConfig`, `KpiCard` + `DashboardSection` + `DashboardConfig`, `PitchConfig`.
  - **`getConfig()`** (`src/lib/config.ts`) — trivial re-export `return siteConfig` from `../../site.config`. Every component imports this module (`zeus-chat.tsx`, `nav.tsx`, `layout.tsx`, `page.tsx`, `hero-section.tsx`, etc.). Server and client components share it because `site.config.ts` has no runtime side-effects.
  - **Decision tree engine** (`src/components/decision-tree.tsx`) — binary (yes/no) DAG: node IDs beginning `"outcome-"` are terminals, everything else is a question. `start` is the root ID (`CLAUDE.md:140`). Each outcome has a `tier: 1-6`, `color`, `icon`, `valueRecovery` percent, `costImpact`, action list, and a `principle` reference (indexed into the `principles` array). Validation tests in `src/__tests__/decision-tree.test.ts` assert no cycles + all outcomes reachable.
  - **`ZeusChat`** (`src/components/zeus-chat.tsx`) — client component. Streams SSE from `/api/chat`, renders inline markdown (tables, code blocks, headings, emphasis, lists, links) **and** inline `<svg>…</svg>` blocks with streaming-safe placeholders (lines 16-138). Renders suggestions from `config.chat.suggestedPrompts` on first load; sessions get a `crypto.randomUUID()` for Zeus correlation.
  - **`Nav`** (`src/components/nav.tsx`) — fixed top nav with a purple gradient stripe (`linear-gradient(135deg, #5D32BB, #615FF3)` — `nav.tsx:32`). Scrollspy via `IntersectionObserver` (line 17-27) highlights the anchor corresponding to the currently-visible section. Anchor links are rewritten to `/#anchor` form when the nav is rendered on a non-home route (`nav.tsx:63`).
  - **`Sidebar`** (`src/components/dashboard/sidebar.tsx`) — dashboard-only. Splits `dashboard.sidebarLinks` into anchor links (set `activeSection` index) vs route links (normal `<a>` nav). The anchor index maps 1:1 to `dashboard.sections[index]` in `DashboardPage`.
  - **`DecisionTree` theme tokens** — **5 hard-coded ecosystem-node colours** in `ecosystem-diagram.tsx:10-16`: hub=accent, source=`#3b82f6`, destination=`#ec4899`, circular=`#f59e0b`, policy=`#8b5cf6`. Edges carry their own colour per-config. Call this out — these five colours are NOT config-driven. Match to `CLAUDE.md:136-138`.

- `### Design decisions worth calling out`
  - **Config-driven single build, not a CMS** — all content lives in TypeScript. No DB, no headless CMS, no MDX. Trade-off: Claude-generated content is validated by the TypeScript compiler + 260-ish Vitest tests; cost is every copy change requires a rebuild.
  - **`site.config.ts` is gitignored on purpose** — `.gitignore:3`. The template stays clean; per-site content never contaminates the template repo. The `postinstall` hook copies the example in so `npm run dev` works on first clone (`package.json:11`).
  - **Three templates coexist in one codebase by deliberate design** — each deployed site uses exactly one; `page.tsx` dispatches. Adding a fourth template = one case in `page.tsx` + one new top-level component + a new optional config field. See `docs/source-analysis.md:213-289` for the evidence that the three templates correspond to three observed design languages across 15 live sites.
  - **AI comparison colours are fixed real-world brand colours** — `CLAUDE.md:158`: Gemini `#4285F4`, ChatGPT `#10a37f`, Copilot `#7B61FF`, Claude `#d97706`. These are assertions in `claude-md-claims.test.ts:61` — changing them breaks tests.
  - **Hero format is enforced by tests** — `claude-md-claims.test.ts:5-29` asserts (a) every landing hero `title` ends with ` —` (em-dash-space), (b) every `animatedWords` entry ends with `.`, (c) if exactly 2 CTA buttons then first is `solid`, second is `outline`. This is the test-driven styleguide.
  - **Light theme activates only for `dashboard`** — `layout.tsx:32`. Landing and pitch are always dark. This is a class toggle, not a theme system with multiple options.
  - **The 11 landing sites share a CSS class namespace but resolve it to different accent colours** — legacy finding from `docs/source-analysis.md:132-142` ("text-cultivate-accent" resolves to green on Cultivate, red on EPR because the CSS variable is overridden per deployment). In the current template, `ThemeConfig.tokenNamespace` records the legacy name for each site family (`cultivate`, `cpma`, `sources`, `aldc`, `producer`, `ghostpine`, `agristack` per `configs.ts:865-881`) but the active mechanism is Tailwind reading the per-config `accentColor`/`glowColor` at build time.

---

### Section 3 — `## Data Flow`

**Purpose:** Describe how data enters and leaves. **Data Flow IS applicable** for this repo despite it being a marketing site — the chat route is a real server-side data path and the Zeus logging side-channel is material. Section is brief relative to an API repo.

**Sub-sections:**

- `### Build-time — config drives the whole site`
  - Developer (or Claude) writes `site.config.ts` → `npm run build` runs → Tailwind reads `accentColor`/`glowColor` from the config (`tailwind.config.ts:2-4`) → Next.js compiles every component with the config's data baked in at module load (`getConfig()` → sync import of `../../site.config`). Output: `.next/` (static + SSR assets).
  - There is **no runtime fetch** for content. No CMS. The config becomes HTML/CSS/JS at build and is frozen.

- `### Runtime — three flows`

  1. **Page renders.** Static pages + RSC for `/`, `/calculator`, `/chat`, `/why-aldc`. No data fetching beyond the baked-in config. PostHog snippet fires client-side if `NEXT_PUBLIC_POSTHOG_KEY` is present (`layout.tsx:35-46`).
  2. **Chat request.** Browser → `POST /api/chat` with `{message, history, sessionId}` → `app/api/chat/route.ts`:
     - In-memory rate limit (20 req / min / IP — `route.ts:6-55`).
     - Body validation (`validateBody` — `route.ts:59-80`; rejects `message > 2000 chars`, `history > 20 entries`, bad roles).
     - Requires `config.chat.systemPrompt` (returns 404 if not configured).
     - Requires `ANTHROPIC_API_KEY`; 500 if missing.
     - POSTs `https://api.anthropic.com/v1/messages` with `model`, `system=config.chat.systemPrompt`, `messages=[...history, {role: "user", content: message}]`, `stream: true` (`route.ts:118-132`).
     - Streams back as SSE (`Content-Type: text/event-stream`). Each Anthropic `content_block_delta` is re-wrapped into `{type: "token", text}` frames (`route.ts:157-172`).
     - **After stream closes, fire-and-forget POST to Zeus Memory** at `${ZEUS_API_URL}/api/memory` with `X-API-Key: ${ZEUS_API_KEY}`, body `{content: "User: <Q>\n\nAssistant: <A>", content_summary: Q.slice(0,200), source: "<subdomain>_chat", metadata: {subdomain, session_id, timestamp}}` (`route.ts:9-40`). Non-fatal on error. Disabled if either var missing. Cross-link [[zeus-memory]].
  3. **Analytics.** PostHog client-side only. No server-side events. All 15 known sites share the same `NEXT_PUBLIC_POSTHOG_KEY` (see Judgment calls about low-sensitivity disclosure).

- `### Lead capture form (pitch template) — no submit handler`
  - `src/components/pitch/pitch-page.tsx:63` — `<form onSubmit={(e) => e.preventDefault()}>`. Form is visual only. Collected state is kept in component state and never POSTed.
  - This is a **known-pending** integration. CTA in the same page is a `mailto:${config.contactEmail}` link (line 177). Flag in Tech Debt.

- `### Side channels — none`
  - No NextAuth, no cookies set by the app, no Vercel cron jobs, no scheduled tasks. This is a content-only app plus one streaming route.

- `### Cross-reference`
  - The chat proxy is a small but real dependency on [[zeus-memory]] infra; call it out via wikilink.
  - Unlike [[entities/repos/flight-check|flight-check (repo)]] (which fans out to 4 backends), [[entities/repos/eclipse|eclipse (repo)]], or [[eclipse_exp]], this repo has **no backend integrations** beyond Anthropic + optional Zeus.

---

### Section 4 — `## Developer Guide`

**Purpose:** Get a developer (or Claude-driven generation) from clean clone to running `npm run dev`.

**Sub-sections:**

- `### Prerequisites`
  - Node 22 (CI pins to Node 22 — `.github/workflows/ci.yml:19`). Node 20 likely works; Node 18 will not match CI.
  - npm (package-lock.json committed; `npm ci` is the CI install).
  - Claude Code CLI (optional — only needed if using the AI-assisted generation path).
  - An Anthropic API key (optional — only needed for `/api/chat` to work locally).
  - A Zeus Memory API key (optional — only if chat logging should land in Zeus; see [[zeus-memory]]).

- `### First-run setup (from clean clone)`
  1. `git clone <repo>` and `cd prospect-site-template`. **Per `README.md:13` you must be in this directory for any Claude-driven generation to work.**
  2. `npm install` — triggers the `postinstall` script (`package.json:11`) which copies `site.config.example.ts` to `site.config.ts` iff the latter doesn't exist. This guarantees the build graph is complete (Tailwind imports the config — see Architecture).
  3. `cp .env.example .env.local` and edit:
     - `NEXT_PUBLIC_POSTHOG_KEY` — already set to the ALDC-wide key. README says "Do NOT change this" (`CLAUDE.md:37`).
     - `NEXT_PUBLIC_POSTHOG_HOST` — default `https://us.i.posthog.com`.
     - `ANTHROPIC_API_KEY` — replace the `sk-ant-xxx` placeholder with a real key. Without this, `/api/chat` returns 500.
     - `CHAT_MODEL` — defaults to `claude-sonnet-4-6`. Override only if intentionally switching.
     - `ZEUS_API_URL` / `ZEUS_API_KEY` — optional. Without them, chat works; nothing is logged to Zeus.
  4. `npm run dev` — Turbopack dev server at `http://localhost:3000`.

- `### Generating a new site via Claude`
  1. Open Claude Code in the repo directory.
  2. Tell Claude: "Make me a site about X" (or "build me a dashboard for Y", or "make an enterprise pitch page for Z").
  3. Claude reads `CLAUDE.md`, picks a template (`CLAUDE.md:55-73`), reads `src/lib/types.ts` + `site.config.example.ts`, web-searches any statistics per the fact-checking requirement (`CLAUDE.md:42-51`), writes `site.config.ts`, runs `npx vitest run`, runs `npm run build`, and tells the user to `npm run dev`.
  4. To **keep** the generated site: `cp -r . /path/to/new-site && cd /path/to/new-site && git init && git add -A && git commit -m "Initial site"`. Then deploy from the copy (`README.md:55-68`, `CLAUDE.md:17-29`). The template folder stays clean.
  5. Alternative: `./create-site.sh <subdomain> ./path/to/config.ts` — same pipeline but scripted. Writes to `./sites/<subdomain>/`, installs, tests, builds, prints deploy hints (`create-site.sh:14-73`). **Note:** the script-output directory pattern is not gitignored in this repo's `.gitignore` — if you run it inside the template folder you'll end up with uncommitted `sites/<subdomain>/` noise. Flag.

- `### Scripts` — table from `package.json:5-13`.

  | Command | What it does |
  |---|---|
  | `npm run dev` | `next dev --turbopack` on :3000 |
  | `npm run build` | `next build` (production output in `.next/`) |
  | `npm start` | `next start` against the production build |
  | `npm run lint` | `next lint` (ESLint flat config) |
  | `npm run typecheck` | `tsc --noEmit` |
  | `npm run test` | `vitest run` |
  | `postinstall` | Copies `site.config.example.ts` → `site.config.ts` iff absent |

- `### Testing`
  - Runner: Vitest 3.2 (`vitest.config.ts`).
  - Environment: jsdom, with `scrollIntoView` + `IntersectionObserver` polyfilled in `setup.ts`.
  - Globals: `describe`/`it`/`test`/`expect` available without import (`vitest.config.ts:12`).
  - 11 test files, ~260 `describe|it|test` occurrences in sources. **Number of assertions vs number of test cases differs from what README and CONTRIBUTING claim** — README says "624 tests" (`README.md:83`), CONTRIBUTING says "394 tests" (`CONTRIBUTING.md:22`). Neither matches the other; the real count depends on `it.each` cardinality (fixture expansion). Execution session should run `npx vitest run` once and record the actual number. Flag the docs mismatch in Tech Debt.
  - `live-config.test.ts` — validates whatever is currently in `site.config.ts` (theme hex validity, required fields, hero format, section types, template-specific fields). **This is what makes the test suite double as a runtime schema check** at build time.
  - `site-variants.test.ts` — validates that the 15 site fixtures in `fixtures/configs.ts` stay consistent: 11 cultivate family, 2 dashboard family, pitch is whyaldc, calculator-feature-flag sites = 11, chat sites = 4 (whyaldc + foodmesh + cpma + ghostpine), no-PostHog sites = [sources] only, contact-email exceptions (epr uses `john@analyticlabs.io`; all others `contact@analyticlabs.io`).
  - `claude-md-claims.test.ts` — asserts the rules documented in `CLAUDE.md` are enforced: hero title ends with ` —`, animated words end with `.`, first CTA button is `solid` and second is `outline`, pitch has 3 compounding bars labelled Day 1 / Day 90 / Year 1, AI comparison contains Gemini at `#4285F4`, etc.
  - `decision-tree.test.ts` — cycle detection, outcome reachability, tier 1-6 legality. Every calculator config must pass.

- `### Local debug / common pitfalls`
  - **Tailwind build failure** — if `site.config.ts` is missing or malformed, `tailwind.config.ts:2-4` fails to import it and the whole build dies before Next.js even runs. Fix: verify `site.config.ts` exists (rerun `npm install` to trigger `postinstall`) and TypeScript-compiles.
  - **`/api/chat` 500 without `ANTHROPIC_API_KEY`** — `route.ts:109-111`. Easy to miss locally if you skipped the `.env.local` copy.
  - **`/api/chat` 404 without `config.chat`** — `route.ts:102-104`. The chat route is gated on the *site* config, not the server env. A landing-only config that doesn't set `chat` gets a 404 from `/api/chat`.
  - **Rate limiter is in-memory** — `route.ts:6-8`. In any multi-instance deploy (Vercel serverless concurrent functions count here), the 20/min cap is per-instance, so the effective cap is higher. Not a security issue; call it out.
  - **PostHog key is committed** (in `.env.example`, `CLAUDE.md:37`). See Judgment calls — this is deliberate. The same key is used by all 15 sites; it's a `NEXT_PUBLIC_*` variable, leaked by design.
  - **Two tests-count claims disagree** — README "624 tests" vs CONTRIBUTING "394 tests". Neither is the actual count. Document the discrepancy.
  - **`create-site.sh` writes to `sites/<subdomain>/` in the template folder** — not gitignored; will leave uncommitted noise if run in-place (`create-site.sh:18-29`).
  - **`/why-aldc` is a "Coming soon" stub** — `src/app/why-aldc/page.tsx`. Do not mistake it for a live route.
  - **Pitch `<form>` has `onSubmit={(e) => e.preventDefault()}`** — no lead capture backend. Document this in the API surface: there is no backend to capture leads; CTA falls through to `mailto:`.
  - **React 19 + Next 15 is recent** — `next/typescript` + `next/core-web-vitals` in the flat ESLint config pick up recent rules. Prettier + lint + typecheck + tests + build must ALL pass for CI (`CONTRIBUTING.md:15-22`). Run `npx prettier --write .` before pushing if you hit a format failure.
  - **The `postinstall` copy is OS-agnostic `cp`** — works on Git Bash, WSL, macOS, Linux. On raw PowerShell without a `cp` alias it would fail; in practice Node's shell routes through `npm`'s compatibility layer. Not a known issue.

---

### Section 5 — `## Deployment`

**Purpose:** Describe the (per-site) deployment model. This repo itself is not deployed as a running service — generated copies are.

**Sub-sections:**

- `### What "deploys" here`
  - The **template repo itself** never runs in production. What deploys is a **copy of the template folder with a filled-in `site.config.ts`**, usually one copy per prospect subdomain.
  - The existing 15 sites at `*.analyticlabs.io` are on Vercel (confirmed by `dpl_*` deployment hashes observed in the RSC chunk URLs — `docs/source-analysis.md:342-348`). README suggests "Netlify, Cloudflare Pages, Docker, any Node host" (`README.md:66`) as options for new sites — no host is prescribed.
  - There is **no Vercel config** in the repo (no `vercel.json`). Vercel auto-detects Next.js.

- `### Per-site deployment flow`
  1. Generate the site (either Claude-driven or hand-written `site.config.ts`).
  2. `cp -r . /path/to/<subdomain>-site` to make a standalone copy — or run `./create-site.sh <subdomain> [config-path]` which copies `src/`, `public/`, `package.json`, `tsconfig.json`, `next.config.ts`, `tailwind.config.ts`, `postcss.config.mjs`, `vitest.config.ts`, the `.env.example` (as `.env.local`), and either the specified config or a fallback into `./sites/<subdomain>/` (`create-site.sh:30-47`).
  3. `git init && git add -A && git commit -m "Initial site"` in the copy.
  4. Push to a new GitHub repo.
  5. Connect to Vercel (or host of choice); set env vars (`ANTHROPIC_API_KEY`, `ZEUS_API_URL`, `ZEUS_API_KEY`, `CHAT_MODEL`, PostHog pair).
  6. DNS CNAME `<subdomain>.analyticlabs.io` → the Vercel deployment (see existing pattern in `docs/source-analysis.md:342-348`).

- `### Template-repo CI/CD`
  - `.github/workflows/ci.yml` (full file, 42 lines) runs on every PR to `main` and every push to `main`. Single job `validate` on `ubuntu-latest`, Node 22.
  - Steps: `actions/checkout@v4` → `actions/setup-node@v4` (with npm cache) → `npm ci` → `npx eslint . --max-warnings 0` → `npx prettier --check .` → `npx tsc --noEmit` → `npx vitest run` → `npx next build` → verify `.next/standalone` or `.next/server` exists.
  - Workflow name is **"CI — Protect Template Integrity"** — the commit message in the file spells out the intent: CI exists to protect the shared template from breaking PRs, not to deploy anything.
  - **No deploy step.** The template repo is not deployed. Each generated site has its own (external) CI/CD chain.

- `### Secrets`
  - PostHog key (`NEXT_PUBLIC_POSTHOG_KEY`) is committed in `.env.example`. Public by design — it's a `NEXT_PUBLIC_*` var; the same key is used across all 15 known sites; PostHog project IDs are low-sensitivity and typically visible in browser network tabs (see `docs/source-analysis.md:21`). Document in wiki prose; do not extract to vault. (Settled in Judgment calls.)
  - `ANTHROPIC_API_KEY`, `ZEUS_API_KEY` — `.env.example` has placeholder `sk-ant-xxx` / `zm_xxx`. Not committed in their real form. Real values live in the deployment-host secret store, NOT in any per-site repo.
  - No other credentials.

- `### Rollback`
  - Per-site: the generating deployer's standard rollback (Vercel previous deployment, GitHub revert, etc.). Nothing in the template repo orchestrates this.
  - For the **template repo**: revert the offending PR via GitHub. Running sites are unaffected (they were copied from an earlier commit and are independently deployed).

- `### Cross-reference`
  - Unlike [[entities/repos/flight-check|flight-check (repo)]], [[entities/repos/eclipse|eclipse (repo)]], [[eclipse_exp]] — which deploy to Azure Container Apps via `azure/webapps-deploy@v3` + slot swap — this repo's produced sites deploy to Vercel. Different infrastructure. Do not assume the ALDC Azure naming convention ([[aldc-naming-convention]]) applies here.

---

### Section 6 — `## The 15 known sites`

**Purpose:** Give the reader a fast map of what has been built with this template. Sourced from fixtures + `docs/source-analysis.md`. Short but useful.

**Sub-sections:**

- `### Site catalogue` — table. Columns: Subdomain | Template | Accent | Token namespace | Calculator? | Chat? | Notes.

  Rows (verified against `src/__tests__/fixtures/configs.ts:5-110` + `:850-881` + `docs/source-analysis.md`):

  | Subdomain | Template | Accent | tokenNamespace | Calculator | Chat | Notes |
  |---|---|---|---|---|---|---|
  | cultivate | landing | `#10b981` green | cultivate | ✅ | — | Flagship — "From Field to Fork" |
  | strategy | landing | `#4f46e5` indigo | cultivate | ✅ | — | — |
  | packaging | landing | `#0d9488` teal | cultivate | ✅ Compliance Tool | — | — |
  | distribution | landing | `#d97706` amber | cultivate | ✅ Loss Estimator | — | — |
  | stewardship | landing | `#059669` green | cultivate | ✅ EPR Calculator | — | — |
  | economics | landing | `#2563eb` blue | cultivate | ✅ ROI Calculator | — | — |
  | epr | landing | `#e11d48` rose | cultivate | ✅ Assessment | — | *Uses cultivate namespace with RED accent — legacy quirk per `source-analysis.md:352`* |
  | eccc | landing | — | cultivate | ✅ Assessment | — | — |
  | foodmesh | landing | — | cultivate | ✅ | ✅ | Only landing site with BOTH calculator AND chat |
  | cpma | landing | — | cpma | ✅ Navigator | ✅ | — |
  | sources | landing | — | sources | ✅ Assessment | — | **Only site without PostHog** (per `configs.ts:848`) |
  | producer | landing | — | producer | — | — | No calculator |
  | whyaldc | pitch | aldc | aldc | — | ✅ | Lead capture + AI comparison |
  | ghostpine | dashboard | `#f59e0b` amber | ghostpine | — | ✅ | Live data + Windy.com iframe (one-off features) |
  | agristack | dashboard | `#22c55e` green | agristack | — | — | Light sections below dark hero — third distinct design |

- `### Template-to-site mapping summary`
  - 11 landing (cultivate family + producer) / 1 pitch (whyaldc) / 2 dashboard (ghostpine, agristack) / 1 producer variant that is technically a landing template but opts out of calculator — matches the 3-template architecture (`configs.ts:850-863`).
  - Sites with calculator (11): cultivate, strategy, packaging, distribution, stewardship, economics, epr, eccc, foodmesh, cpma, sources.
  - Sites with chat (4): whyaldc, foodmesh, cpma, ghostpine.
  - Sites without PostHog (1): sources.

- `### This table is fixture-derived, not runtime-observed`
  - The data lives in `src/__tests__/fixtures/configs.ts` because these are *test assertions* — the fixtures encode what the template MUST be able to produce. Whether each subdomain actually has an active deployment at any given time is not guaranteed by this repo; `docs/source-analysis.md` documented 15 live sites as of its last scrape. Treat the table as "template capability" rather than "current production state".

---

### Section 7 — `## Config reference (what to fill in `site.config.ts`)`

**Purpose:** Summarise the config schema so a reader doesn't have to open `src/lib/types.ts`. Keep compact.

**Sub-sections:**

- `### Top-level fields`
  - `template` — literal `"landing" | "dashboard" | "pitch"` (required).
  - Identity: `subdomain`, `siteName`, `siteLabel` (all required).
  - Theme: `theme.{accentColor, glowColor, accentRgba, sweepName, tokenNamespace}` (all required). Accent palette suggestions in `CLAUDE.md:101-107`.
  - SEO: `title`, `metaDescription`, `ogDescription`, `ogSiteName`, `contactEmail`, `footerTagline`, `footerEntity` (all required).
  - Nav: `nav.links[]` (required), `nav.badges[]` (optional).
  - Landing-required: `hero` (HeroConfig), `sections` (SectionConfig[]), `ecosystemDiagram` (EcosystemDiagram).
  - Optional: `calculator`, `chat`.
  - Dashboard-required-if-dashboard: `dashboard.{sidebarLinks, kpis, sections}` (`logoPath` optional).
  - Pitch-required-if-pitch: `pitch.{compoundingBars, aiComparison, leadForm, valueProps}`.

- `### Landing section types`
  - `problem` (title + 3 narrative paragraphs + optional accentPhrase + optional closingLine + 3-4 timeline cards).
  - `vision` (title + subtitle — renders the ecosystemDiagram).
  - `stakeholders` (6-7 cards; last one `fullWidth` per `CLAUDE.md:115`).
  - `platform` (exactly 4 phases; required colours `#10b981` `#3b82f6` `#f59e0b` `#8b5cf6` — `CLAUDE.md:116`).
  - `global` (4 country cards with `flagColors` — `CLAUDE.md:117`).
  - `alignment` (3 pillars).
  - `funding` (2 grant categories + summary + tags).
  - `join` (CTA title + description).

- `### Ecosystem diagram coordinate conventions` (`CLAUDE.md:131-138`)
  - Hub `x:50 y:50`; sources `x:15 y:20/35/50/65/80`; destinations `x:85 y:25/50/75`; circular `x:35/65 y:90`; policy `x:50 y:8`.
  - Edge colours: `#10b981` (flow), `#ec4899` (distribution), `#f59e0b` (feedback), `#8b5cf6` (policy).

- `### Calculator tree rules` (`CLAUDE.md:140-144`)
  - Start ID = `"start"`; outcome IDs prefixed `"outcome-"`; 5-10 question nodes, 5-8 outcomes; tiers 1 (best) to 6 (worst); 4 principles; no cycles; all outcomes reachable.

- `### Pitch AI comparison required values` (`CLAUDE.md:157-158`)
  - Must include real AI tools with exact brand colours: Gemini `#4285F4`, ChatGPT `#10a37f`, Copilot `#7B61FF`, Claude `#d97706`. Enforced by tests.

- `### Fact-checking requirement` (`CLAUDE.md:42-51`)
  - Every stat, dollar figure, regulatory date, and organisation name MUST be web-verified before generating. Unverified values get a `// UNVERIFIED — check before publishing` comment. Note this in the wiki page as a generation-time discipline.

---

### Section 8 — `## Integrations`

**Purpose:** Enumerate every external system this repo touches. Short section — three integrations, each one sentence.

**Content:**

- **Anthropic Messages API** — `POST https://api.anthropic.com/v1/messages`, SSE streamed, `anthropic-version: 2023-06-01`, `x-api-key: ${ANTHROPIC_API_KEY}`, `model` from env or default `claude-sonnet-4-6`. Used by `/api/chat` route only. No SDK — raw `fetch`.
- **Zeus Memory** — optional fire-and-forget `POST ${ZEUS_API_URL}/api/memory` with `X-API-Key: ${ZEUS_API_KEY}` after each completed chat. Cross-link [[zeus-memory]]. Used by `/api/chat` only. Silent failure on error.
- **PostHog** — inline browser-side snippet injected from `layout.tsx`. Client-only. No server-side PostHog. One project key shared across all 15 sites (`docs/source-analysis.md:21`, `.env.example:2`). Cross-link: no existing PostHog wiki page; do not create one (see Judgment calls).

---

### Section 9 — `## Known issues / Tech Debt`

**Purpose:** Consolidate every issue the plan surfaced.

**Content:**

- **Test count discrepancy** — README.md line 83 says "624 tests", CONTRIBUTING.md line 22 says "394 tests". Neither number matches. Execution session should run `npx vitest run` once and record the actual number in prose; note the docs mismatch.
- **PostHog key committed** — `.env.example:2` contains the real `phc_…` key (not a placeholder). Deliberate: it's a `NEXT_PUBLIC_*` var used by every ALDC site. Document; do not extract to vault (see Judgment calls).
- **Pitch template lead capture has no backend** — `pitch-page.tsx:63` has `onSubmit={e => e.preventDefault()}`. Form is visual only. CTA falls through to `mailto:`. No lead reaches any CRM or queue.
- **In-memory rate limiter** — `api/chat/route.ts:6-8` uses a module-scoped `Map`. In serverless / multi-instance deploys (Vercel's default), each instance has its own counter, effective limit is higher than 20/min. Not a security failing; just document.
- **`create-site.sh` writes `sites/<subdomain>/` in-place** — not gitignored. Running it inside the template folder leaves untracked output. Add to `.gitignore` or run the script from outside the repo.
- **`/why-aldc` is a stub** — `app/why-aldc/page.tsx` renders "Coming soon". Exists in nav by convention only; the legacy sites have a real page here.
- **No Vercel config** — no `vercel.json`. Each generated copy relies on Vercel auto-detection; this is fine for Next.js but worth documenting so a deployer doesn't look for a config that isn't there.
- **Hard-coded ecosystem-node colours** — `ecosystem-diagram.tsx:10-16`. The 5 side-kind colours (source/destination/circular/policy) are baked in; only hub follows the config accent. Changing these requires a component edit.
- **Hard-coded nav gradient bar** — `nav.tsx:32` uses `linear-gradient(135deg, #5D32BB, #615FF3)` — not theme-driven.
- **Node-version implicit** — no `.nvmrc` or `engines` field. CI uses Node 22 explicitly; local dev could drift.
- **The `producer` site fixture is in `configs.ts` but not in the family lists** — `configs.ts:864-865` lists `cultivateFamilySites` (11 without producer) and `dashboardFamilySites` (2); `producer` is in `themes` + `tokenNamespaces` but falls outside both families. Unclear whether this is in-flight new work or a lingering fixture; the `site-variants.test.ts` tree has no dedicated producer block. Flag for human attention (see Judgment calls).

---

### Section 10 — `## See Also`

Wikilinks. Must include:

- [[zeus-memory]] — optional destination of chat conversation logs (`/api/chat` → `/api/memory`).
- [[entities/repos/eclipse|eclipse (repo)]] — other Next.js repo in the ALDC portfolio (Pages Router, older). Disambiguation only.
- [[eclipse_exp]] — another Next.js frontend, bundled with a FastAPI backend. Disambiguation only.
- [[entities/repos/flight-check|flight-check (repo)]] — third Next.js repo, fans out to multiple backends. Disambiguation only.
- [[claude_code_enhanced]] — CCE is the tool that drives the Claude-prompt generation flow described in Intro / Developer Guide.
- [[ai-development-project-standard]] — this repo's generation model aligns with ALDC's AI-developed project tracking standard.

Should also link (softer):

- [[cce]] — project-level cousin of [[claude_code_enhanced]].
- [[phaselab]] — another AI-prototyped product; shares the "config-as-truth" sensibility.

Do NOT link:

- [[dax-media-app]] / [[dax-ai]] — unrelated products.
- [[analyticlabs.io]] — page does not exist and we're deliberately not creating one.
- [[posthog]] — page does not exist and we're deliberately not creating one.

---

### Judgment calls

- **Single wiki page is correct.** The repo is small (1 app, 3 templates, ~20 source files). Splitting into multiple pages would fragment. Target budget **~550–750 lines**. Hard ceiling 900.
- **Data Flow IS included** — not because the repo has a pipeline, but because `/api/chat` is a non-trivial SSE proxy with a Zeus side-channel. Omitting it would miss the Anthropic + Zeus integrations. Section stays short relative to the API repos' Data Flow sections.
- **Do NOT create a separate `analyticlabs.io` wiki page.** No upstream source, no real content, would be stub-weight. The subdomain pattern is documented in Section 5 (Deployment) prose with an anchor to `create-site.sh:20` and `docs/source-analysis.md:342-348`.
- **Do NOT create a separate `posthog` wiki page.** Same reasoning — no upstream content worth a page, the integration is one inline script tag.
- **Do NOT create per-site sub-pages** (one per cultivate/epr/foodmesh/etc.). The 15-site catalogue fits in a table in Section 6. Individual sites are test fixtures, not wiki entities.
- **Do NOT extract the committed PostHog key to vault.** `NEXT_PUBLIC_POSTHOG_KEY` is by design a public (client-visible) identifier — any browser viewing any of the 15 sites can read it. Wiki rule #2 is about secrets; this is an identifier. Document in prose. Contrast with the situation in [[workflows]] (Cosmos keys) and [[custom-fusion-92-audience-api]] (DIOS API key), both of which WERE extracted.
- **Disambiguation block at top is mandatory.** Three other Next.js repos on the wiki ([[eclipse_exp]], [[entities/repos/eclipse|eclipse (repo)]], [[entities/repos/flight-check|flight-check (repo)]]) could be confused with this one. Put the callout inside Section 1 prose rather than as a block-quote — closer in style to the `workflows.md` intro than the `flight-check.md` dedicated block. Also disambiguate from [[zeus-memory]] (integration, not the repo).
- **Tone vs README.** The README is punchy / first-person ("Make me a site about water quality monitoring"). The wiki page should stay neutral technical — the README's voice is for end users, the wiki is for engineers maintaining the template.
- **Test count** — **run `npx vitest run` once and record the actual number**. Don't accept either README or CONTRIBUTING at face value. Note both stale claims in Tech Debt.
- **`site.config.ts` is gitignored — do not print example config into the wiki page.** The example is `site.config.example.ts` and is a thousand lines. Summarise via the Config Reference (Section 7) pointing at `src/lib/types.ts` for the full TypeScript. If a reader wants concrete values, `site.config.example.ts` is the source.
- **The `producer` site is a fixture anomaly.** It's in `themes`, `tokenNamespaces`, and `allSiteNames` but missing from `cultivateFamilySites` and `dashboardFamilySites`. Record this in Tech Debt; don't speculate about intent. Worth one bullet for Paul to assign meaning later.
- **Cross-reference hygiene — must link:** [[zeus-memory]], [[claude_code_enhanced]], [[entities/repos/eclipse|eclipse (repo)]], [[eclipse_exp]], [[entities/repos/flight-check|flight-check (repo)]]. Should link: [[cce]], [[ai-development-project-standard]], [[phaselab]]. Do NOT link: [[dax-media-app]], [[dax-ai]], [[connector]], [[core_api]] (unrelated to this client-only repo).
- **Index entry wording** — match the pattern of other repo entries in `index.md`. Proposed: *"Next.js 15 template for ALDC prospect microsites (15 deployed sites at `*.analyticlabs.io`). One config file drives three templates (landing / dashboard / pitch). Claude Code generates `site.config.ts` from a natural-language prompt; template folder copied per site and deployed independently (Vercel). Optional AI chat proxy to Anthropic + [[zeus-memory]] logging."*
- **No credential extraction.** Only semi-sensitive string is `NEXT_PUBLIC_POSTHOG_KEY` — public by design per rule above. `ANTHROPIC_API_KEY` and `ZEUS_API_KEY` are `sk-ant-xxx` / `zm_xxx` placeholders in `.env.example`. No actual secrets in the repo.
- **Section 6 (15 known sites) is a new section the prior 6 plans don't have** — justified: this repo is a template factory and the "what has been built with it" view is the single most-useful orientation a reader can have. Sourced entirely from fixtures + `docs/source-analysis.md` so no speculation.
- **No additions to existing wiki pages beyond adding this repo's entry to `index.md`.** Unlike the `workflows` plan (which closed a stated gap in `flight-check.md`), this repo doesn't plug any pre-existing gap — there's no "this repo has no wiki page yet" pointer to resolve elsewhere.
- **No in-repo `docs/` writes, no source-code edits.** Per boot prompt. Wiki only. `docs/source-analysis.md` is a committed repo artefact I read for context; do not touch it.
- **Page length target:** ~550–750 lines. Section 6 (site catalogue) and Section 7 (config reference) are the shortest; Architecture + Developer Guide are the longest. API Reference table not needed — there is only one route (`/api/chat`) and it's small.

### Session Log entry to add (executor should append after writing the page)

```
### 2026-04-20 — prospect-site-template plan session complete

- did: read repo thoroughly — README.md, CLAUDE.md, CONTRIBUTING.md, package.json, next.config.ts, tsconfig.json, tailwind.config.ts, vitest.config.ts, eslint.config.mjs, .prettierrc, .editorconfig, .env.example, .gitignore, create-site.sh, site.config.example.ts; src/lib/{types,config}.ts; src/app/{layout,page,error,globals.css, calculator/page, chat/page, why-aldc/page, api/chat/route}.ts(x); src/components/{nav, hero-section, ecosystem-diagram, decision-tree, zeus-chat, dashboard/{dashboard-page, sidebar}, pitch/pitch-page}.tsx; src/__tests__/{setup, live-config, site-variants, claude-md-claims, fixtures/configs}.ts; .github/workflows/ci.yml; docs/source-analysis.md (first ~450 lines). Cross-read existing wiki pages: index.md, entities/repos/{eclipse, eclipse_exp, flight-check, workflows, claude_code_enhanced}.md, entities/projects/zeus-memory.md.
- produced: 10-section plan for new wiki page `entities/repos/prospect-site-template.md` — Intro (identity + template model + disambiguation), Architecture (repo layout tree + tech stack table + 3-template selection model + config-is-build-input + routes table + key abstractions + design decisions), Data Flow (build-time + runtime /api/chat + pitch lead-capture gap), Developer Guide (prereqs + first-run + Claude generation flow + scripts table + testing notes + 10 pitfalls), Deployment (template-not-deployed clarification + per-site flow + repo CI detail + secrets + rollback), The 15 known sites (catalogue table + template summary + fixture caveat), Config reference (top-level fields + 8 section types + ecosystem coords + calculator rules + pitch values + fact-checking), Integrations (Anthropic + Zeus + PostHog — 3 bullets), Tech Debt (11 items), See Also.
- decided: single wiki page (~550–750 lines); Data Flow applicable (SSE chat proxy + Zeus side-channel); disambiguate vs three other Next.js repos inline in intro; do NOT create `analyticlabs.io` or `posthog` stub pages; do NOT create per-site sub-pages (15 fixtures go in a table); do NOT extract committed `NEXT_PUBLIC_POSTHOG_KEY` to vault (public by design — a NEXT_PUBLIC_ var, not a secret per wiki rule #2); run `npx vitest run` during execution to settle the README-vs-CONTRIBUTING test-count discrepancy; include a `## The 15 known sites` section (new shape relative to the prior 6 plans, justified by this being a template-factory).
- flagged: (1) README.md "624 tests" vs CONTRIBUTING.md "394 tests" disagreement; (2) PostHog key committed in `.env.example` (document, don't vault); (3) pitch template has no lead-capture backend (visual form only); (4) `create-site.sh` writes `sites/<subdomain>/` in-place without gitignore; (5) `/why-aldc` is a "Coming soon" stub; (6) `producer` site in fixtures but not in family lists — unclear intent; (7) in-memory rate limiter on `/api/chat` is per-instance in serverless; (8) hard-coded ecosystem-node colours + nav gradient are not theme-driven; (9) no Vercel config despite Vercel being the known deploy target. No credentials to extract.
- next: execution session (Sonnet) — (1) create `entities/repos/prospect-site-template.md` (~550–750 lines) per this plan; (2) run `npx vitest run` once to capture the real test count for § Testing; (3) add index.md entry under Entities › Repos with the exact blurb proposed in Judgment calls; (4) mark Execution ✅ in this tracker row 7; (5) append to log.md. No source-code edits, no repo-internal doc writes, no vault touches.
```

---

## aldc-scripts — Approved Plan

**Plan session:** 2026-04-20 (Opus)
**Target wiki page:** `wiki/entities/repos/aldc-scripts.md` (new page — confirmed absent)
**Wiki index entry:** add under `Entities › Repos` alongside existing `workflows`, `prospect-site-template`, etc.

> Disambiguation note for the execution session: this is a **small grab-bag utility repo** (3 top-level files + one `cost-monitoring/` subfolder of ~10 files). It is NOT the same as `claude_code_enhanced`'s `scripts/` directory (which holds CCE install + per-machine setup tooling — that's a submodule of that repo, on a completely different axis). It is NOT a connector repo, NOT a data pipeline, NOT a deployed service. The repo's shape is: one Python PDF-report generator (Fusion92 ticket status), one generic Slack-webhook wrapper, and a self-contained `cost-monitoring/` dashboard that unifies Azure + GitHub + Anthropic spend into a weekly Slack post. Everything is invoked either ad-hoc or via cron on one specific VM (Server4). There is no CI/CD, no package manifest, no tests, and no deploy target other than `scp` to Server4. The wiki page's centrepiece is a **script catalogue**, not Architecture.

### Doc structure — single wiki page with these sections

All content goes into one page: `wiki/entities/repos/aldc-scripts.md`. Sections below are in the order they should appear on the page. Each section names the heading and lists the concrete anchors (file paths, env var names, subscription IDs, cron schedules, cross-reference wikilinks) the execution session should fill prose around. For a grab-bag repo of this size, the section set is deliberately compressed vs. the prior 7 plans — **Architecture is replaced by a Script Catalogue as the centrepiece**, Data Flow is noted applicable-but-narrow (cost-monitoring data flow only), Developer Guide and Deployment are both short.

---

### Frontmatter

```yaml
---
tags: [entity, repo, aldc-scripts, utilities, cost-monitoring, slack, airtable, bash, python, cron]
aliases: [aldc-scripts, ALDC scripts, ALDC utility scripts, aldc/scripts, cost-monitoring scripts]
sources: [repos/aldc-scripts/f92_ticket_report.py, repos/aldc-scripts/send_slack.sh, repos/aldc-scripts/cost-monitoring/DEPLOY_TO_SERVER4.md, repos/aldc-scripts/cost-monitoring/azure-costs.sh, repos/aldc-scripts/cost-monitoring/corporate-costs-report.sh, repos/aldc-scripts/cost-monitoring/github-usage.sh, repos/aldc-scripts/cost-monitoring/send-cost-report-slack.sh, repos/aldc-scripts/cost-monitoring/install-cron.sh, repos/aldc-scripts/cost-monitoring/deploy-azure-automation.sh, repos/aldc-scripts/cost-monitoring/azure-runbook.ps1, repos/aldc-scripts/cost-monitoring/azure-logic-app.json, repos/aldc-scripts/cost-monitoring/reports/cost-report-2026-02-17.md, repos/aldc-scripts/cost-monitoring/reports/cost-report-2026-02-18.md]
created: 2026-04-20
updated: 2026-04-20
---
```

---

### Section 1 — Intro paragraph (top of page, no heading)

**Purpose:** Tell a cold reader exactly what this repo is in the first paragraph and disambiguate it from (a) `claude_code_enhanced/scripts/` (a different `scripts/` directory in a different repo — CCE install tooling, unrelated to this repo), (b) any in-repo `scripts/` folders in `eclipse_exp`, `core_api`, or `clients`, and (c) the executive-snapshot-email runbook at `[[executive-snapshot-email]]` (which is a cron job on a different VM, not part of this repo).

**Key content:**

- One-sentence identity: *a small grab-bag repo (`github.com/ALDC-io/aldc-scripts`, 3 commits total as of 2026-04-20) holding ALDC-internal utility scripts that don't belong to any one product: a Fusion92 ticket-status PDF generator, a Slack-webhook helper, and the corporate cost-monitoring dashboard (Azure + GitHub + Anthropic).*
- What's unusual: no CI/CD, no package manifest (no `requirements.txt`, no `pyproject.toml`, no `package.json`), no tests, no `README.md` at repo root. Everything runs on operator machines or the Server4 VM directly. The only in-repo doc is `cost-monitoring/DEPLOY_TO_SERVER4.md`.
- Scale anchors: 3 commits in `master` history, all authored by Lori Beck (`lori.beck@aldc.io`). 2 Python-ish + 6 Bash-ish + 1 PowerShell + 1 Logic-App JSON + 1 markdown runbook + ~10 total executable scripts. Total source footprint ~50 KB.
- Primary runtime hosts: **Server4** (production CCE host — home of the weekly cost-report cron; see `cost-monitoring/DEPLOY_TO_SERVER4.md:1-8`) and **operator workstations** (the Fusion92 report is run ad-hoc by Paul / Lori; `f92_ticket_report.py:22` writes to `Path.home().parent / aldc / reports`).
- Git remote: `https://github.com/ALDC-io/aldc-scripts.git` (default branch `master`, not `main`). Single-branch linear history.
- Frame the repo as "current-state legacy utility storage." Per memory — ALDC is consolidating onto `[[eclipse_exp]]` / Prefect. The cost-monitoring dashboard is a candidate for absorption into `[[eclipse_exp]]` ops dashboards or into a `[[Prefect]]` scheduled flow; the Fusion92 ticket report could migrate into `[[custom-fusion-92-audience-api]]` or a Prefect flow once Airtable is a supported data source. Note as "future home: TBD" rather than "should be rewritten."

---

### Section 2 — `## Repo layout`

**Purpose:** Full `ls` tree so a reader can orient in one screen. This is a 13-file repo; exhaustive tree is appropriate.

**Content — exact tree from `ls -la` (omit `.git/`, `reports/*.md` artefacts):**

```
aldc-scripts/
├── f92_ticket_report.py             # Python 3, 315 lines — Airtable → PDF report (Fusion92 ticket status)
├── send_slack.sh                    # Bash, 35 lines — generic Slack webhook wrapper (jq-escaped JSON POST)
└── cost-monitoring/
    ├── DEPLOY_TO_SERVER4.md         # Runbook (125 lines) — how to deploy cost-monitoring to Server4
    ├── azure-costs.sh               # Bash, 102 lines — Azure cost report across 9 subscriptions (ad-hoc)
    ├── corporate-costs-report.sh    # Bash, 252 lines — Unified Azure + GitHub + Anthropic MTD report → .md
    ├── github-usage.sh              # Bash, 145 lines — GitHub org (aldc-io) usage stats → .json
    ├── send-cost-report-slack.sh    # Bash, 93 lines — Weekly wrapper: runs corporate-costs + posts Slack summary
    ├── install-cron.sh              # Bash, 20 lines — Installs the weekly cron job
    ├── deploy-azure-automation.sh   # Bash, 146 lines — Provisions an Azure Automation Account + Runbook
    ├── azure-runbook.ps1            # PowerShell, 94 lines — Azure Automation alternative to send-cost-report-slack.sh
    ├── azure-logic-app.json         # Azure Logic App workflow definition — second alternative (unfinished)
    └── reports/
        ├── cost-report-2026-02-17.md  # Artefact — committed example output
        ├── cost-report-2026-02-18.md  # Artefact — committed example output
        └── slack-delivery.log          # Runtime log (gitignored on Server4; committed copies exist)
```

**One-line notes for the section body:**

- The repo owner authored every file (`git log`: Lori Beck `lori.beck@aldc.io`, 3 commits — `180d4c0` add Slack script, `111a64b` add Fusion92 report, `1254813` fix cost-monitoring paths + redact webhook).
- `reports/` contains two committed sample cost reports (Feb 17 + Feb 18, 2026). Flag in Tech Debt: these are runtime artefacts and probably shouldn't be committed — consider `.gitignore`.
- No `.gitignore`, no `.env.example`, no `README.md`, no `CLAUDE.md`, no `CODEOWNERS`, no `.github/`. This is deliberate grab-bag shape.

---

### Section 3 — `## Script catalogue` (centrepiece)

**Purpose:** One row per script with everything a maintainer needs to know at a glance. This is THE load-bearing section for this wiki page — replaces "Architecture" because the repo has no architecture beyond per-script design.

**Two tables:**

#### Table A — Script inventory

Columns: `Script` | `Lang` | `Purpose` | `Entry point` | `Frequency` | `Host` | `Credentials required` | `Cross-reference`

Rows (execution session fills in exact wording; anchors already verified):

| Script | Lang | Purpose | Entry point | Frequency | Host | Credentials required | Cross-reference |
|---|---|---|---|---|---|---|---|
| `f92_ticket_report.py` | Python 3 | Fetch Fusion92 ticket list from Airtable "Resource Allocation · F92 View \[INTERNAL\]" and generate a PDF status report with ALDC branding (executive summary + status-bar + sortable table by priority + key highlights). | `python3 f92_ticket_report.py` (writes to `~/../aldc/reports/Fusion92_Ticket_Status_YYYY-MM-DD.pdf`) | Ad-hoc (operator-run) | Operator workstation (Linux with DejaVu fonts at `/usr/share/fonts/truetype/dejavu`) | `AIRTABLE_TOKEN` read from `~/../aldc/.env` (`fetch_tickets()` at `f92_ticket_report.py:46-66`) | `[[fusion92]]` (client page), `[[airtable]]` — **no wiki page yet** (see Judgment calls: create a minimal stub) |
| `send_slack.sh` | Bash | Generic Slack incoming-webhook wrapper. Uses `jq -Rs '{text: .}'` to safely JSON-encode the message (avoids shell-escaping pitfalls) before POSTing to the webhook URL. Returns non-zero if Slack response is not `ok`. | `send_slack.sh <webhook_url> <message>` | Ad-hoc (called by other scripts) | Any machine with `bash`, `jq`, `curl` | Slack webhook URL passed as arg (not stored in repo) | `[[send-cost-report-slack]]` (primary consumer) |
| `cost-monitoring/azure-costs.sh` | Bash | Per-subscription Azure cost listing across all 9 ALDC subscriptions for the current month, with per-service breakdown via `jq group_by`. Writes both coloured stdout and `/tmp/azure-costs-YYYYMMDD.json`. | `./azure-costs.sh` (diagnostic) | Ad-hoc | Any machine with `az` CLI logged in + `jq` + `bc` | `az login` session with **Cost Management Reader** role on each subscription (script tolerates missing role with fallback to resource-count-only output) | `[[azure-environments]]` (subscription ID table already documents 4 of 9 IDs) |
| `cost-monitoring/corporate-costs-report.sh` | Bash | Unified MTD cost report across Azure + GitHub (aldc-io) + Anthropic. Writes a markdown report to `$REPORT_DIR/cost-report-YYYY-MM-DD.md` (REPORT_DIR hard-coded to `/home/aldc/scripts/cost-monitoring/reports` — **Server4-specific path**). Mutates the file in place via `sed` to insert summary rows. | `./corporate-costs-report.sh` (invoked by `send-cost-report-slack.sh`) | Weekly (via wrapper) | Server4 (paths hard-coded) | `az login` + `gh auth` + (optional) Cost Management Reader on each sub | Emits the markdown report; consumed by the Slack wrapper; also readable standalone |
| `cost-monitoring/github-usage.sh` | Bash | Standalone GitHub org report for `aldc-io` — members, repos (count/private/storage), Actions billing, storage billing, 30-day commit activity per member. Writes `/tmp/github-usage-YYYYMMDD.json`. | `./github-usage.sh` (diagnostic) | Ad-hoc | Any machine with `gh` CLI authenticated + `jq` + `bc` | `gh auth login` (owner permissions needed for Actions + Storage billing endpoints; script tolerates 403) | Not called by the weekly wrapper — superseded by inline GitHub calls in `corporate-costs-report.sh`. Retain for ad-hoc deep dives. |
| `cost-monitoring/send-cost-report-slack.sh` | Bash | **Production entry point.** Weekly cron target. Runs `corporate-costs-report.sh`, gathers Azure resource counts + GitHub members/repos, builds a Slack-formatted message, and POSTs via `send_slack.sh`. Channel `#the-olds` (recipients: Lori / JK / Mike). Logs to `reports/slack-delivery.log`. | `./send-cost-report-slack.sh` (called by cron: `0 9 * * 1`) | Weekly, Mon 09:00 server-local | Server4 | `SLACK_WEBHOOK_THE_OLDS` env var (sourced from `/home/lori/.env`), `az login`, `gh auth` | `[[send_slack.sh]]` (uses it), `[[executive-snapshot-email]]` (sibling weekly-Slack pattern on a different VM — disambiguate) |
| `cost-monitoring/install-cron.sh` | Bash | Idempotently adds the `send-cost-report-slack.sh` entry to the current user's crontab. Schedule: `0 9 * * 1` (Mon 09:00). No-op if entry already exists. | `./install-cron.sh` | One-shot (Server4 setup) | Server4 | Current user's crontab write access | `[[DEPLOY_TO_SERVER4]]` runbook (in-repo) |
| `cost-monitoring/deploy-azure-automation.sh` | Bash | Alternative Azure-native deployment path: creates resource group `rg-aldc-automation`, Automation Account `aa-aldc-cost-reports`, enables system-managed identity, assigns Cost Management Reader on 5 subscriptions, imports `azure-runbook.ps1`, publishes, schedules Mon 09:00 PST. | `./deploy-azure-automation.sh` | One-shot (setup) | Azure-authenticated workstation | `az login` with permissions to create automation account + role assignments, `SLACK_WEBHOOK_THE_OLDS` | `[[azure-environments]]`, `[[azure-runbook]]` (sibling), `[[azure-logic-app]]` (second alternative — see below) |
| `cost-monitoring/azure-runbook.ps1` | PowerShell | The Azure Automation runbook content that replaces `send-cost-report-slack.sh`. Uses managed identity + `Get-AzConsumptionUsageDetail` + GitHub REST. Reads `SlackWebhook_TheOlds` and `GitHubToken` from Automation Variables. | Invoked by Azure Automation schedule | Weekly (if deployed) | Azure Automation | Automation Variables (not env vars): `SlackWebhook_TheOlds`, `GitHubToken` | Deployed by `deploy-azure-automation.sh`. **Not currently in production** (see Judgment calls) |
| `cost-monitoring/azure-logic-app.json` | JSON (ARM) | Second alternative: an Azure Logic App workflow definition (weekly recurrence Mon 09:00 PST → HTTP GETs to Azure Subscriptions + GitHub members + GitHub repos → Compose → Slack POST). **Parameterised but incomplete** — references `parameters('github_token')` which is not defined in the `parameters` block; only `slack_webhook_url` is declared. Not deployable as-is. | Import into Azure Logic Apps | (unused) | Azure Logic Apps | `slack_webhook_url` (SecureString), undeclared `github_token` | **Not currently deployed.** Retain as prototype; flag in Tech Debt. |

#### Table B — Output artefacts

Columns: `Artefact` | `Producer` | `Path` | `Committed?`

| Artefact | Producer | Path | Committed? |
|---|---|---|---|
| `Fusion92_Ticket_Status_YYYY-MM-DD.pdf` | `f92_ticket_report.py` | `~/../aldc/reports/` (operator-local) | ❌ |
| `azure-costs-YYYYMMDD.json` | `azure-costs.sh` | `/tmp/` | ❌ |
| `github-usage-YYYYMMDD.json` | `github-usage.sh` | `/tmp/` | ❌ |
| `cost-report-YYYY-MM-DD.md` | `corporate-costs-report.sh` | `/home/aldc/scripts/cost-monitoring/reports/` (Server4) | 2 historical samples yes (Feb 17 + Feb 18, 2026); ongoing runs gitignored locally on Server4 |
| `slack-delivery.log` | `send-cost-report-slack.sh` | `reports/slack-delivery.log` | Yes (empty-ish sample committed) — **flag in Tech Debt** |
| `cron.log` | cron wrapper | `reports/cron.log` | No (log path per `install-cron.sh:6`) |

---

### Section 4 — `## Data Flow`

**Purpose:** Describe how data moves for each script that has an inbound/outbound path. Short section — the only non-trivial data flow is the weekly cost report; the Fusion92 report is a single-hop (Airtable → PDF); Slack wrapper is pass-through.

**Sub-sections:**

- `### Fusion92 ticket report`
  - Source: Airtable Base `app4jxyVmcfEH1D9k`, Table `tblOl8YykVDXq37an`, View **"F92 View \[INTERNAL\]"** (hard-coded at `f92_ticket_report.py:18-20`).
  - Auth: Bearer token (`AIRTABLE_TOKEN`) read from `~/../aldc/.env` (not the repo's `.env` — the operator's ALDC-wide env file).
  - Transform: maps Airtable records → priority-sorted dicts (P1/P2/P3/unprioritised). Uses `Status`, `Priority`, `Outcome`, `Success Criteria`, `Remediation Steps`, `Outcome Group`, `Last Modified` fields. Detects paused state by scanning `Remediation Steps` for `"PAUSED"` substring (`f92_ticket_report.py:78`).
  - Output: landscape-letter PDF via `fpdf` with embedded DejaVu Unicode font from `/usr/share/fonts/truetype/dejavu`. Logo sourced from `~/../aldc/templates/aldc-logo.png`. PDF saved to `~/../aldc/reports/Fusion92_Ticket_Status_YYYY-MM-DD.pdf`.
  - **No network output.** The PDF is an artefact; distribution to Fusion92 is manual (email attachment or upload).
  - Cross-link: `[[fusion92]]`, `[[airtable]]` (stub — see Judgment calls).

- `### Weekly corporate cost report`
  - Inputs (three, in order of execution):
    1. Azure Consumption API via `az consumption usage list` for 9 subscriptions (3 full-access expected per `azure-environments.md`, 6 returning "no data" per the Feb 18 report artefact — see Judgment calls).
    2. GitHub org API via `gh api /orgs/aldc-io/*` — members list, repo list (with `diskUsage`), Actions billing (`/settings/billing/actions`), Storage billing (`/settings/billing/shared-storage`), 30-day commit search.
    3. Anthropic API — **not queried**. Only a hard-coded stanza pointing readers at the Anthropic Console. Flag as "no programmatic Anthropic cost fetch" in Tech Debt.
  - Transform: shell-side `jq`/`bc` summation; markdown report written line-by-line.
  - Output paths:
    - Markdown report: `reports/cost-report-YYYY-MM-DD.md` (Server4 path — see DEPLOY_TO_SERVER4 runbook).
    - Slack message to `#the-olds` via `send_slack.sh` → `SLACK_WEBHOOK_THE_OLDS` webhook URL.
    - Log: `reports/slack-delivery.log` (tee'd).
  - Azure subscription list (hard-coded in THREE places: `azure-costs.sh:26-36`, `corporate-costs-report.sh:68-78`, `deploy-azure-automation.sh:54-60`). The three lists disagree: `azure-costs.sh` and `corporate-costs-report.sh` list all 9; `deploy-azure-automation.sh` lists only 5 (drops Stage 1, Demo 1, Support 1, zeus_memory_dev). Flag as drift risk in Tech Debt.
  - **Cross-reference `[[azure-environments]]`** — 4 of the 9 subscription IDs are already documented there (Production 1, Production 2, Quality 1, Test 1). The wiki page should reference the existing table and note which 5 IDs aren't yet in it (Stage 1, Development 2, Demo 1, Support 1, zeus_memory_dev).

- `### Slack webhook pass-through`
  - `send_slack.sh` is a two-hop: argv → jq-escaped JSON temp file → curl POST. No state, no logging, no retries. Returns 1 if Slack response is not the literal string `ok`.

- `### No other data flows`
  - No database writes. No cron-driven Airtable polling. No inbound webhooks. No long-running daemons.

---

### Section 5 — `## Developer Guide`

**Purpose:** Get a developer (or operator) from clean clone to running each script. Short section — there's very little to set up.

**Sub-sections:**

- `### Prerequisites (per script)`
  - **`f92_ticket_report.py`**: Python 3.10+ (uses `from pathlib import Path` and f-strings but no walrus-required syntax), `fpdf` (NOT `fpdf2` — the `uni=True` font kwarg is the legacy fpdf API), Linux with DejaVu fonts at `/usr/share/fonts/truetype/dejavu`. **Windows/macOS will fail** at font-registration unless the operator copies DejaVu into that exact path or edits `FONT_DIR`. `~/../aldc/.env` must contain `AIRTABLE_TOKEN=...`. `~/../aldc/templates/aldc-logo.png` and `~/../aldc/reports/` must exist. Note: `Path.home().parent` means *one directory above the user's home* — for `/home/lori`, that's `/home/`, so the expected structure is `/home/aldc/{.env,templates,reports}/` (this is Server4-relative, not user-home-relative — flag in pitfalls).
  - **`send_slack.sh`**: `bash`, `jq`, `curl`. Nothing else.
  - **`azure-costs.sh`**, **`corporate-costs-report.sh`**, **`github-usage.sh`**, **`send-cost-report-slack.sh`**: `bash`, `jq`, `bc`, `curl`, `sed` (GNU sed — `sed -i "/…/a …"` syntax), `az` CLI authenticated (`az login`), `gh` CLI authenticated (`gh auth login`). Azure identity needs Cost Management Reader on each subscription being scanned. GitHub identity needs org-owner scope to pull Actions and Storage billing.
  - **`deploy-azure-automation.sh`**: `az` CLI with permissions to create resource groups, automation accounts, role assignments, automation variables/runbooks/schedules.
  - **`azure-runbook.ps1`**: runs *inside* Azure Automation — uses `Get-AutomationVariable`, `Connect-AzAccount -Identity`. Not intended to run locally.
  - **`azure-logic-app.json`**: deploy via `az logic workflow create` or Azure Portal. **Incomplete** — missing `github_token` parameter declaration (see Script catalogue).

- `### Clone and run`
  1. `git clone https://github.com/ALDC-io/aldc-scripts.git && cd aldc-scripts`. Note branch is **`master`**, not `main`.
  2. `chmod +x cost-monitoring/*.sh send_slack.sh` (all committed with `0755` already, but after cloning on some systems permissions may drop).
  3. For the Fusion92 report: `pip install fpdf` (legacy package, not `fpdf2`) + ensure `AIRTABLE_TOKEN` in the operator's `.env`.
  4. For cost-monitoring: `az login && gh auth login`; export `SLACK_WEBHOOK_THE_OLDS` (obtained from `[[vault/credentials.md]]` § Slack webhooks — see Judgment calls).

- `### Running each script locally`
  - `python3 f92_ticket_report.py` — prints progress lines; output PDF path printed at end.
  - `./cost-monitoring/azure-costs.sh` — coloured stdout, `/tmp/azure-costs-*.json` dumped.
  - `./cost-monitoring/corporate-costs-report.sh` — **will fail** outside Server4 unless you manually `mkdir -p /home/aldc/scripts/cost-monitoring/reports` first (hard-coded `REPORT_DIR` at line 8). Flag in pitfalls.
  - `./cost-monitoring/github-usage.sh` — standalone, safe to run anywhere.
  - `./cost-monitoring/send-cost-report-slack.sh` — sends a real Slack message. Don't run without the webhook pointing at a test channel.
  - `./send_slack.sh <webhook> <message>` — quick webhook test.

- `### Common pitfalls`
  - **`corporate-costs-report.sh` has Server4 paths baked in** — `REPORT_DIR=/home/aldc/scripts/cost-monitoring/reports` (line 8). Running on an operator workstation writes to a path that probably doesn't exist. The `mkdir -p "$REPORT_DIR"` at line 22 will fail without sudo if `/home/aldc` doesn't exist.
  - **`SLACK_SCRIPT` hard-coded to `/home/aldc/scripts/send_slack.sh`** in `send-cost-report-slack.sh:9`. Server4-only. The committed file expects `send_slack.sh` to be copied to that exact path (deliberate per `DEPLOY_TO_SERVER4.md:35-39`).
  - **`f92_ticket_report.py` paths** — `Path.home().parent / "aldc" / ...` evaluates to `/home/aldc/...` when the runtime user is `/home/lori`. That's an implicit Server4-adjacent layout, not a per-user layout. On Windows (`C:\Users\PaulRussell`), `Path.home().parent` is `C:\Users\`, so the expected `templates/`, `reports/`, and `.env` would need to live under `C:\Users\aldc\`. Very fragile — note this.
  - **`fpdf` vs `fpdf2`** — the script uses the legacy `fpdf` package's API (`add_font(..., uni=True)`). Installing `fpdf2` will make `uni` an unknown kwarg. Pin to `fpdf` (no 2) explicitly.
  - **Azure subscription list drift** — three scripts keep their own hard-coded list; `deploy-azure-automation.sh` lists only 5, the others 9. Update one, forget the others — silent miss.
  - **GitHub Actions + Storage billing endpoints require org-owner scope**. Scripts `|| echo '{}'` the failure, so a non-owner `gh` identity runs cleanly but produces empty billing data. Easy to miss.
  - **Anthropic cost is never fetched programmatically** — the report always emits "See Console" regardless of actual spend. Document; not a bug.
  - **`fpdf` font file requirement** — `/usr/share/fonts/truetype/dejavu/DejaVuSans*.ttf`. On non-Debian hosts this package isn't always installed by default (`apt install fonts-dejavu-core`).
  - **`reports/slack-delivery.log` is committed** — running the script appends to it, so `git status` will look dirty after every run. Probably an oversight.
  - **`master` default branch** — differs from the rest of ALDC repos (`main`). Watch out for PR tooling defaults.

---

### Section 6 — `## Deployment`

**Purpose:** Describe how this repo gets onto its only deployment target (Server4). Short section — this is not a CI/CD repo.

**Sub-sections:**

- `### Deployment target — Server4 (production CCE host)`
  - The only "deployed" script in this repo is `cost-monitoring/send-cost-report-slack.sh` on Server4 via cron.
  - Server4 is the ALDC production CCE host (cross-link to wherever Server4 is documented — candidates: `[[deployment-groups]]`, `[[claude_code_enhanced]]`). The runbook `cost-monitoring/DEPLOY_TO_SERVER4.md` is the authoritative deployment guide for this repo.
  - No CI/CD — deployment is manual `scp -r cost-monitoring aldc@<server4-ip>:/home/aldc/scripts/` (per `DEPLOY_TO_SERVER4.md:14-24`).

- `### Deploy steps (summarised — defer to in-repo runbook for detail)`
  1. `scp -r cost-monitoring aldc@<server4>:/home/aldc/scripts/`.
  2. Copy `send_slack.sh` from this repo root to `/home/aldc/scripts/send_slack.sh` (same path hard-coded in `send-cost-report-slack.sh:9`).
  3. `ssh aldc@<server4>` → `chmod +x /home/aldc/scripts/cost-monitoring/*.sh` → `mkdir -p /home/aldc/scripts/cost-monitoring/reports`.
  4. Verify `az account show` + `gh auth status`; set `SLACK_WEBHOOK_THE_OLDS` in `/home/lori/.env` (this path is hard-coded in the script; see `send-cost-report-slack.sh:10` — despite running as `aldc` user, the webhook env var is sourced from `/home/lori/.env`, which is **unusual** — flag in Tech Debt).
  5. Run `./install-cron.sh` to install the Mon 09:00 cron job.
  6. Manual test: `./send-cost-report-slack.sh`.

- `### Alternative deployment paths (not currently in production)`
  - **Azure Automation** — `deploy-azure-automation.sh` + `azure-runbook.ps1`. Self-contained deployment to Azure Automation Account `aa-aldc-cost-reports` in resource group `rg-aldc-automation`, managed identity, Cost Management Reader role on 5 subscriptions. Would replace the Server4 cron job. **Not currently in production** (no evidence of live Automation Account; confirm in execution session if accessible).
  - **Azure Logic App** — `azure-logic-app.json`. Even more self-contained. **Incomplete** — missing `github_token` parameter. Treat as prototype.

- `### Rollback`
  - No rollback machinery. If a weekly cost report breaks: `crontab -e` to comment out the line, or `scp` an older version of the script tree.
  - Report files accumulate — no retention policy. Flag in Tech Debt.

- `### No repo-level CI/CD`
  - No `.github/workflows/`. No tests. No linter. No formatter. No pre-commit hook.
  - Unlike the rest of the 2026-04 ALDC portfolio ([[eclipse_exp]], [[workflows]], [[custom-fusion-92-audience-api]] which all have PR checks per `[[ai-pr-workflow]]`), this repo has zero automated gates. Any commit to `master` ships. Note: this is a low-consequence decision here because the scripts run on a single VM and outputs are read by humans — but flag it so readers don't assume the ALDC-wide CI story applies.

---

### Section 7 — `## Security & Credentials`

**Purpose:** Surface every credential, secret, and sensitive identifier in the repo. This is high-risk repo shape (shell scripts with webhooks + API tokens) — due diligence matters.

**Sub-sections:**

- `### Credential scan — results`
  - **No hardcoded secrets remaining.** Commit `1254813` "Fix cost-monitoring script paths and redact hardcoded Slack webhook" explicitly removed a hard-coded Slack webhook URL. Post-redaction state verified: `grep -r 'https://hooks.slack.com' .` returns nothing; `grep -r 'xoxb-' .` returns nothing; `grep -r 'sk-ant-' .` returns nothing; `grep -r 'ghp_' .` returns nothing; `grep -r 'AKIA' .` returns nothing.
  - **`DEPLOY_TO_SERVER4.md:85-89` still contains a partial Slack webhook URL** — `https://hooks.slack.com/services/T01Q410SQ9W/B0A9QGFT1C3/...`. The `...` suggests the private suffix was truncated deliberately, but the `T.../B...` prefixes identify the workspace + channel. Low sensitivity (not a secret on its own; can't be replayed without the suffix), but flag in Tech Debt — the doc should be reworked to reference `[[vault]]` rather than embed any part of the URL.
  - **Slack User IDs in `azure-runbook.ps1:80`** — `<@U0A6A9VN96V> <@U01NZCSEWQ7> <@U081KV3RKT8>`. These are user mention IDs for Lori, JK, Mike. Not secrets (anyone in the workspace can see them), but ALDC-internal identifiers — note but don't extract.
  - **Azure subscription IDs are hard-coded in three scripts** (`azure-costs.sh:26-36`, `corporate-costs-report.sh:68-78`, `deploy-azure-automation.sh:54-60`). Not secrets (not directly exploitable), but ALDC-internal infrastructure identifiers. Cross-link `[[azure-environments]]` which already documents 4 of the 9.
  - **Airtable Base ID `app4jxyVmcfEH1D9k`** and Table ID `tblOl8YykVDXq37an` hard-coded at `f92_ticket_report.py:18-19`. Not secrets.

- `### Runtime credentials required (operator must provide)`
  - `AIRTABLE_TOKEN` — personal access token with read scope on the F92 base. Stored in operator's ALDC-wide `~/../aldc/.env`. Cross-link `[[vault/credentials.md]]` § Airtable (if exists; if not, flag in Judgment calls).
  - `SLACK_WEBHOOK_THE_OLDS` — incoming webhook URL for the `#the-olds` Slack channel. Stored in `/home/lori/.env` on Server4. Referenced as `${SLACK_WEBHOOK_THE_OLDS:-}` with an empty-string fallback — so an unset value does NOT error out and the script runs, but webhook POST will fail. Cross-link `[[vault/credentials.md]]` § Slack webhooks.
  - `az` session credentials — AAD identity with Cost Management Reader on the relevant subscriptions.
  - `gh` session credentials — GitHub PAT or `gh auth login` session with org-owner scope on `aldc-io` for full billing visibility.
  - **For Azure Automation path only:** `SlackWebhook_TheOlds` and `GitHubToken` as encrypted Automation Variables.

- `### Trust boundaries`
  - **Server4** holds the Slack webhook URL in `/home/lori/.env`. Compromise of Server4 = ability to post arbitrary messages to `#the-olds`. Not a data-plane risk.
  - **Airtable token** stored in `/home/aldc/.env` (or equivalent on operator workstation). Compromise = read access to Fusion92 ticket list (not the base's write surface, per the PAT's scope — confirm in execution session).
  - **No secret ever flows through GitHub Actions** (there is no CI).

- `### Vault touchpoints for execution session`
  - If `[[vault/credentials.md]]` already has a Slack webhooks section: cross-reference it. If not: flag a needed addition (the execution session should NOT extract the `T01Q410SQ9W/B0A9QGFT1C3/...` URL to the vault unless the full suffix is recoverable elsewhere — partial URL is low value).
  - If `[[vault/credentials.md]]` has no Airtable entry: add a TODO in the wiki page's Security section noting the execution session could not cross-reference.
  - **Do NOT create new vault entries in this plan.** Execution session handles per-credential vault work only if full credentials are available and not already filed.

---

### Section 8 — `## Tech Debt & Known Issues`

**Purpose:** Consolidate every rough edge the plan surfaced. Unlike [[workflows]] or [[custom-fusion-92-audience-api]] this list is short — the repo is small and most issues are ergonomic, not architectural.

**Content (12 items):**

- **Three copies of the Azure subscription list** that have already drifted — `deploy-azure-automation.sh:54-60` has 5 IDs; the other two have 9. A single sourced list (YAML / JSON / .env) would remove drift risk.
- **No programmatic Anthropic cost fetch** — `corporate-costs-report.sh` always prints "See Console." Anthropic's Admin API (introduced late 2025) could fill this gap; the script predates it.
- **Server4 paths hard-coded in three scripts** (`corporate-costs-report.sh:8`, `send-cost-report-slack.sh:9`, weird `/home/lori/.env` sourcing). Running on any non-Server4 host requires edits.
- **`send-cost-report-slack.sh` sources `SLACK_WEBHOOK_THE_OLDS` from `/home/lori/.env`** while running as the `aldc` user — unusual and brittle. The comment at `send-cost-report-slack.sh:10` acknowledges this as intentional.
- **`azure-logic-app.json` is incomplete** — references undeclared `parameters('github_token')`. Not deployable as-is.
- **Committed runtime artefacts** — `reports/cost-report-2026-02-17.md`, `reports/cost-report-2026-02-18.md`, `reports/slack-delivery.log`. `.gitignore` would fix.
- **No `.gitignore`, no `README.md`, no `.env.example`, no pre-commit** — bare-bones repo hygiene.
- **Partial Slack webhook URL in `DEPLOY_TO_SERVER4.md:85-89`** — should reference `[[vault]]` instead.
- **`fpdf` (not `fpdf2`)** — legacy package with no pinning. `pip install fpdf` could regress if a future release drops `uni=True`.
- **Fusion92 report path assumptions** are Server4-adjacent (`Path.home().parent / "aldc"`) — Windows/macOS-hostile.
- **No CI/CD, no tests** — a broken script ships silently until the next Monday run.
- **Two unused alternative deploy paths** (`azure-runbook.ps1` + `azure-logic-app.json`) that were started but not finished. Either finish one and retire the cron, or delete the unused prototypes. Keeping both is confusing.

---

### Section 9 — `## Future home (platform consolidation)`

**Purpose:** Per the boot prompt — frame legacy utilities with a pointer to their future home when one exists. Short section.

**Content:**

- **Cost-monitoring dashboard** — natural candidates for absorption:
  - A `[[Prefect]]` scheduled flow (weekly, parameterised per cloud). Prefect is already the target for connector migration; adding a cost-reporting flow is trivial.
  - An `[[eclipse_exp]]` ops dashboard under `/api/v1/health` or `/api/v1/admin` — the platform already has a health/perf dashboard (per `eclipse_exp.md`'s health router).
  - An Azure Automation Account (`deploy-azure-automation.sh` already provides the scaffold; finishing + deploying it would retire Server4 as a cost-monitoring host).
- **Fusion92 ticket report** — candidates:
  - Integration into `[[custom-fusion-92-audience-api]]` (Fusion92 is already the client; adding a `/tickets/report` endpoint fits). Low fit because the report is operational, not data-plane.
  - A `[[Prefect]]` flow that runs weekly and posts the PDF to a Google Drive / Slack channel.
  - Remaining ad-hoc in this repo indefinitely is also fine — it's low-volume, operator-invoked.
- **`send_slack.sh`** — once everything that calls it moves, the script can be retired. Until then, keep.
- **No immediate migration commitment** — flag as opportunity, not requirement. Cross-link `[[ai-delivery-pivot]]` (if exists) per memory entry on ALDC's AI-driven delivery pivot.

---

### Section 10 — `## See Also`

Wikilinks. Must include:

- `[[fusion92]]` — client page; Airtable view name and priority taxonomy originate here.
- `[[azure-environments]]` — 4 of the 9 subscription IDs are already documented; the cost scripts' hard-coded lists should be reconciled against this page over time.
- `[[executive-snapshot-email]]` — sibling weekly-Slack pattern running on a different VM (Auriga → aldctestagnt1c01); disambiguate explicitly — different host, different recipients, different channel.
- `[[deployment-groups]]` — for Server4 context (the production CCE host).
- `[[claude_code_enhanced]]` — CCE lives on the same Server4 host; the repos coexist but don't share code.
- `[[Azure]]` — tool page (cost scripts use the Consumption API heavily).
- `[[vault]]` / `[[vault/credentials.md]]` — runtime credentials reference.
- `[[ai-pr-workflow]]` — the ALDC-wide PR workflow that this repo does NOT enforce (note the contrast).
- `[[Prefect]]`, `[[eclipse_exp]]` — future-home candidates (Section 9).

Should link (softer):

- `[[airtable]]` — tool page; **does not currently exist** — see Judgment calls (do NOT create in this session).
- `[[send-cost-report-slack]]` — if we promote the weekly-cost process to its own runbook page; otherwise intra-page anchor only.

Do NOT link:

- `[[eclipse]]` / `[[eclipse_exp]]` — unrelated except as a future home. One link only (in Section 9).
- `[[connector]]` / `[[workflows]]` / `[[flight-check]]` / `[[clients-repo]]` — these are data-plane repos; the Fusion92 mention here is about tickets (ops), not data. Do not force cross-links.
- `[[core_api]]` — unrelated.

---

### Judgment calls

- **Single wiki page is correct container.** The repo is tiny — 13 files total, ~50 KB of source. A multi-page split would fragment trivially-small content. Target budget **~350–500 lines**. Hard ceiling 600. (This is the smallest page in the workstream — substantially smaller than `workflows.md` (657) or `claude_code_enhanced.md` (~590).)
- **Architecture section is REPLACED by Script Catalogue.** The repo has no architecture above the per-script level. Table B/A is the centrepiece — the wiki's most-used lookup will be "what does this script do and what does it need?" A forced "Architecture" section would be hollow.
- **Data Flow IS included but compressed.** Only the weekly cost report has non-trivial data flow; Fusion92 report is a one-hop. Keep the section but short.
- **Deployment IS applicable** — Server4 cron is a real deployment target. But it's one paragraph, not a CI/CD story. The section explicitly contrasts "no CI/CD" against the rest of the ALDC portfolio.
- **Do NOT create `[[airtable]]` wiki page in this session.** No upstream source beyond this one script; would be stub-weight. Add to the page's "See Also" as a future opportunity. If the execution session notices that other wiki pages already reference `[[airtable]]` (e.g., existing brackets without a backing file), flag as a lint opportunity rather than fix inline.
- **Do NOT extract any credentials to vault in this session.** Repo has been scrubbed (commit `1254813`). The remaining `DEPLOY_TO_SERVER4.md:85-89` partial Slack URL is truncated (the full suffix was deliberately redacted to `...`). The Airtable Base/Table IDs + Azure subscription IDs + Slack User IDs are identifiers, not secrets. No extraction needed.
- **Note the partial Slack webhook URL in `DEPLOY_TO_SERVER4.md:85-89`** in Tech Debt — it's truncated (`.../...`) but the workspace + channel prefixes remain. Low severity; recommend replacing with a pointer to `[[vault]]`. Do NOT suggest amending git history — the suffix was never committed.
- **Do NOT flag Azure subscription IDs as a credential leak.** They're already documented in `[[azure-environments]]` and are not directly exploitable without an AAD identity. They are ALDC-internal infrastructure identifiers.
- **Do NOT rewrite or clean up any script** — read-only per boot prompt. Document-as-is.
- **Disambiguation callout required at page top** — three adjacent things could be confused with this repo: (1) `claude_code_enhanced/scripts/` (a different `scripts/` dir in a different repo; CCE install tooling), (2) various `scripts/` subdirs in `eclipse_exp`, `core_api`, `clients` (each repo has its own), (3) `[[executive-snapshot-email]]` runbook (another weekly-Slack cron but on a different VM). Place inline in the intro paragraph, not as a block quote.
- **Index entry wording** — match the pattern of other repo entries in `index.md`. Proposed: *"Grab-bag of internal ALDC utility scripts (Python + Bash). Fusion92 ticket-status PDF generator (Airtable → PDF), generic Slack-webhook helper, and the weekly corporate cost-monitoring dashboard (Azure 9 subs + GitHub aldc-io + Anthropic → `#the-olds` Slack). Runs via cron on Server4; no CI/CD. Candidate for future absorption into [[Prefect]] flows or [[eclipse_exp]] ops dashboards."*
- **Cross-reference hygiene — must link:** `[[fusion92]]`, `[[azure-environments]]`, `[[executive-snapshot-email]]`, `[[deployment-groups]]`, `[[Azure]]`, `[[ai-pr-workflow]]` (for the no-CI contrast), `[[vault]]`. Should link: `[[Prefect]]`, `[[eclipse_exp]]`, `[[claude_code_enhanced]]`. Do NOT link: `[[core_api]]`, `[[clients-repo]]`, `[[connector]]` — unrelated.
- **Gap-closing edits in OTHER wiki pages — OPTIONAL, not required.** Unlike the `workflows` plan which mandated closing several gaps, this repo is small enough that the only useful outbound edit is: `[[executive-snapshot-email]]` could gain a one-line "See Also: [[aldc-scripts]] for the sibling Azure + GitHub + Anthropic weekly cost Slack (different host, different channel, different recipients)." Execution session may add this as a single bullet, OR skip it.
- **`azure-environments.md` — OPTIONAL enrichment.** Execution session MAY add the 5 missing subscription IDs (Stage 1, Development 2, Demo 1, Support 1, zeus_memory_dev) to that page's subscription table, citing `corporate-costs-report.sh:68-78` as source. NOT required — if the execution session is short on time, flag the gap in Tech Debt instead.
- **Tone:** neutral technical. Do not editorialise on the tech-debt items beyond what's objective.
- **Page length target:** ~350–500 lines. Shortest page in the workstream. Script Catalogue tables are the longest content.
- **Naming note.** The repo is `aldc-scripts` (with hyphen) on GitHub. The wiki page slug should be `aldc-scripts.md` (matches repo name). The page title should be `aldc-scripts` (lowercase, matches slug + repo convention).
- **Default branch is `master`, not `main`.** Note once in Developer Guide; not worth a separate section.
- **The Fusion92 report's view name contains `[INTERNAL]` in square brackets** — that's the literal Airtable view name (URL-encoded via `urllib.parse.quote` at `f92_ticket_report.py:61`). Preserve the `[INTERNAL]` verbatim in any prose — it's not a wikilink.
- **Do NOT mistake `f92_ticket_report.py` for part of the `[[workflows]]` repo's `F92_*` function apps.** Naming is coincidental — both use the `F92` prefix because both are Fusion92-related, but they're different codebases on different runtimes (Azure Functions Python vs local Python3 CLI). Mention the naming collision once in the intro or in a See Also disambiguator.

### Session Log entry to add (executor should append after writing the page)

```
### 2026-04-20 — aldc-scripts plan session complete

- did: read repo thoroughly — f92_ticket_report.py (315 lines — Airtable → PDF with fpdf), send_slack.sh (35 lines — jq/curl wrapper), cost-monitoring/DEPLOY_TO_SERVER4.md (125-line runbook), cost-monitoring/azure-costs.sh (102 lines), cost-monitoring/corporate-costs-report.sh (252 lines), cost-monitoring/github-usage.sh (145 lines), cost-monitoring/send-cost-report-slack.sh (93 lines), cost-monitoring/install-cron.sh (20 lines), cost-monitoring/deploy-azure-automation.sh (146 lines), cost-monitoring/azure-runbook.ps1 (94 lines), cost-monitoring/azure-logic-app.json (88 lines), cost-monitoring/reports/cost-report-2026-02-18.md (artefact sample), full `git log --all` (3 commits, all Lori Beck). Credential scan: clean (no Slack webhooks, no API keys, no GH tokens, no AWS keys, no anthropic keys). Cross-read existing wiki pages: index.md, entities/repos/{eclipse_exp, claude_code_enhanced, workflows, prospect-site-template}.md, processes/operations/executive-snapshot-email.md, concepts/architecture/azure-environments.md (confirmed 4 of 9 subscription IDs already documented there), entities/clients/active/fusion92.md (confirmed client page exists).
- produced: 10-section plan for new wiki page `entities/repos/aldc-scripts.md` — Intro (identity + disambiguation vs CCE scripts + per-repo scripts + executive-snapshot-email), Repo layout (full tree, 13 files), Script catalogue (Table A — 10-row inventory: script / lang / purpose / entry point / frequency / host / creds / cross-ref; Table B — output artefacts), Data Flow (Fusion92 Airtable → PDF; weekly cost report Azure+GitHub+Anthropic → markdown+Slack; `send_slack.sh` pass-through), Developer Guide (prereqs per script, clone + run, 10 common pitfalls), Deployment (Server4 cron is the only prod target, summary of DEPLOY_TO_SERVER4.md steps, alternative Azure Automation + Logic App paths — neither in prod, no CI/CD + no tests), Security & Credentials (credential scan results, runtime creds required, trust boundaries, optional vault touchpoints), Tech Debt (12 items), Future home (Prefect flow / eclipse_exp ops dashboard candidates), See Also.
- decided: single wiki page (~350–500 lines, smallest in the workstream); Architecture section REPLACED by Script Catalogue (repo has no cross-script architecture); Data Flow applicable but compressed; Deployment applicable (Server4 cron) but short; disambiguation inline in intro (vs claude_code_enhanced/scripts/, vs per-repo `scripts/` dirs, vs `[[executive-snapshot-email]]` runbook); do NOT create `[[airtable]]` stub page; do NOT extract any credentials to vault (repo is scrubbed — commit `1254813` redacted the hard-coded Slack webhook; residual `DEPLOY_TO_SERVER4.md:85-89` has only partial URL with deliberate `...` truncation); do NOT modify scripts; "Future home" section added (per boot-prompt platform-consolidation framing) rather than "will migrate to X"; gap-closing edits in other wiki pages (`executive-snapshot-email.md`, `azure-environments.md`) marked optional, not mandatory.
- flagged: (1) three hard-coded Azure subscription lists that have drifted — `deploy-azure-automation.sh:54-60` has 5, the others 9; (2) no programmatic Anthropic cost fetch — always "See Console"; (3) Server4 paths hard-coded in three scripts; (4) `send-cost-report-slack.sh` sources `SLACK_WEBHOOK_THE_OLDS` from `/home/lori/.env` while running as `aldc` user — unusual; (5) `azure-logic-app.json` incomplete — undeclared `github_token` parameter; (6) committed runtime artefacts (`cost-report-2026-02-17.md`, `cost-report-2026-02-18.md`, `slack-delivery.log`); (7) no `.gitignore`, no `README.md`, no `.env.example`; (8) partial Slack webhook URL remains in `DEPLOY_TO_SERVER4.md:85-89` (truncated with `...`); (9) `fpdf` (not `fpdf2`) unpinned; (10) Fusion92 report Windows/macOS-hostile (`Path.home().parent / "aldc"` assumes Server4-adjacent layout); (11) no CI/CD, no tests — differs from rest of ALDC portfolio; (12) two unused alternative deploy paths (`azure-runbook.ps1` + `azure-logic-app.json`). No credentials to extract.
- next: execution session (Sonnet) — (1) create `entities/repos/aldc-scripts.md` (~350–500 lines) per this plan; (2) add index.md entry under Entities › Repos with the exact blurb proposed in Judgment calls; (3) OPTIONAL: add a one-line See Also cross-link from `processes/operations/executive-snapshot-email.md` back to `[[aldc-scripts]]`; (4) OPTIONAL: add 5 missing subscription IDs to `azure-environments.md` (Stage 1, Development 2, Demo 1, Support 1, zeus_memory_dev); (5) mark Execution ✅ in this tracker row 8; (6) append to log.md. No source-code edits, no vault touches, no stub page creation.
```

---

## power_bi — Approved Plan

**Plan session:** 2026-04-20 (Opus)
**Target wiki page:** `wiki/entities/repos/power_bi.md` (new page — confirmed absent; existing `wiki/entities/tools/power-bi.md` is a separate *tool* page, not this repo page)
**Wiki index entry:** add under `Entities › Repos` alongside existing `aldc-scripts`, `workflows`, `prospect-site-template`, etc.

> **Disambiguation for the execution session.** Two wiki pages must coexist and must not be confused:
>
> - `[[entities/tools/power-bi]]` (exists, 129 lines) — the **tool**: what Power BI is, how data gets into it, workspaces, refresh, Excel model access, template conventions. Client-facing info.
> - `[[entities/repos/power_bi]]` (this new page) — the **repo**: the GitHub-hosted `ALDC-io/power_bi.git` artefact store containing the actual `.pbix` files, its layout, its LFS story, its git cadence, what reports live where, which client folders are live vs. legacy, how a developer clones-edits-publishes.
>
> The tool page answers "how do I grant a Fusion92 user Excel model access." The repo page answers "where is the 2026-03 GEP model's `.pbix` and when was it last touched." The repo page links outbound to the tool page for anything about using Power BI; the tool page already links outbound to `[[gep-snowflake-pbi-deployment]]`/`[[model-deploy-production]]`/`[[powerbi-secret-refresh]]` for runbooks, so the repo page should NOT duplicate those — link to them.
>
> A frontmatter `aliases:` entry on the new repo page should NOT include `Power BI` or `PBI` (those belong to the tool page); use `power_bi`, `power_bi repo`, `ALDC power_bi repo`, `pbix repo`, `pbix-artifact-repo` instead. Mirror the `cce` (project) vs. `claude_code_enhanced` (repo) coexistence pattern established earlier in this workstream.

> **Second disambiguation (inside the repo).** `custom/KIT_ACE/` and `sales/KIT_ACE/` are both present but are **different things**: `custom/KIT_ACE/` is the live client reports (Daily Sales + Finance Model + Netsuite Data Search); `sales/KIT_ACE/` holds a one-off *sales-pitch demo* (Product Pairing Recommender) created for a sales conversation. Same client, two folders, different purpose. Similarly the three `templates/Eclipse Power BI Template *.pbix` files here are stale copies (last modified 2022-06) — per the tool page, the canonical template copies now live in `Nextcloud\Customers\Style Guides`, so the in-repo `templates/` folder is effectively a snapshot, not the source of truth. Flag both of these on the page.

### Doc structure — single wiki page with these sections

All content goes into one page: `wiki/entities/repos/power_bi.md`. Sections below are in the order they should appear on the page. Each section names the heading and lists the concrete anchors (folder paths, report filenames, git dates, author names, LFS-size buckets, cross-reference wikilinks) the execution session should fill prose around.

**For a binary-artefact repo with no source code to read, the usual Architecture + Data Flow + Developer Guide + Deployment shape is reframed:**

- "Architecture" section is present but short — because there is no code architecture; the repo is a filesystem of `.pbix` files. What replaces it is **Repo Layout**.
- "Data Flow" IS applicable and gets a section — but it's the tool-page's dataflow truncated and shifted: what flows into the `.pbix` files (from `REPORT_COMMON` via Snowflake, sometimes via SSMS) is worth documenting once on this page for orientation and then linking out to `[[Power BI]]`/`[[data-pipeline-flow]]` for detail.
- The **Report Catalogue** section is the centrepiece — analogous to `aldc-scripts`'s Script Catalogue. Per-folder tables of every `.pbix`, its size, its last-modified date, its inferred status. This is what a reader will actually come to this page for.
- Developer Guide is medium-length — there IS a real workflow (clone-with-LFS, open, edit, republish) that's worth writing down.
- Deployment is SHORT — Power BI deployment is not a `git push` action; it's "open in PBI Desktop, click Publish." Cross-reference the runbooks heavily rather than duplicate.

---

### Frontmatter

```yaml
---
tags: [entity, repo, power_bi, powerbi, pbix, reports, retail, lfs, git-lfs, binary-artefacts]
aliases: [power_bi, power_bi repo, ALDC power_bi repo, pbix repo, pbix-artifact-repo, power-bi-repo]
sources: [repos/power_bi/.gitattributes, repos/power_bi/.gitignore, "repos/power_bi/large file storage.txt", repos/power_bi/common/Retail/Customer Lifetime Value/retail_customer_lifetime_value.json, repos/power_bi/common/Retail/Daily Sales/2022-06/daily_sales.json, repos/power_bi/common/Retail/KPI Manager/2022-06/kpi_manager.json, repos/power_bi/common/Retail/Product Benchmark/2022-06/cosmos_report_template.json, repos/power_bi/templates/cosmos_report_template.json, repos/power_bi/templates/theme.json, repos/power_bi git log --all (353 commits, 2022-03 to 2026-03-06), repos/power_bi git lfs ls-files (94 LFS objects)]
created: 2026-04-20
updated: 2026-04-20
---
```

---

### Section 1 — Intro paragraph (top of page, no heading)

**Purpose:** Tell a cold reader in one paragraph what this repo is, what's in it, why it has LFS, and the big-picture difference vs. `[[Power BI]]` (the tool page).

**Key content (execution session writes prose from these anchors):**

- One-sentence identity: *the artefact store for ALDC's Power BI reports — 94 `.pbix` files + 3 `.pbit` template files + a handful of `.pptx` style guides + 6 CosmosDB `report` JSON companions + 1 `theme.json`, all organised by `common/ custom/ internal/ sales/ templates/`, LFS-backed, no source code.*
- Scale anchors: 353 commits since 2022-03 (first commit), 7 unique authors, most active folder is `custom/GEP/` (last commit `2026-03-06`, 20 dated sub-folders), next is `custom/FUSION_92/` (last commit `2025-12-30`, 13 dated sub-folders), `custom/DISH_DUER/` is the largest by volume (20 sub-folders, ~5.5 GB LFS storage, but last commit `2024-08-26` — client is inactive per wiki).
- Repo total footprint: ~16 GB across LFS (per `du -sh`: `custom` 15 GB, `common` 564 MB, `internal` 515 MB, `sales` 273 MB, `templates` 2.6 MB). **94 LFS-tracked `.pbix` files** (from `git lfs ls-files`).
- Git remote: `https://github.com/ALDC-io/power_bi.git`. Default branch `main`. Long-lived branches on origin: `CUST-303`, `CUST-396`, `CUST-421`, `CUST-461`, `CUST-528`, `cust-457` — all `CUST-*` ticket branches from the DISH_DUER / KIT_ACE era (none more recent than 2024 based on the DISH_DUER timeline); flag as "stale branches" in Tech Debt.
- Storage model: **100% of `.pbix` files are Git LFS**. `.gitattributes` contains exactly one line: `*.pbix filter=lfs diff=lfs merge=lfs -text`. Every clone requires LFS installed or the `.pbix` files download as 134-byte LFS pointer stubs. Note the top-level `large file storage.txt` — it is the repo's only in-repo documentation file, and it contains one sentence: *"Large file storage MUST be enabled on the client where you intend to use this repository — https://docs.github.com/…"* (quote it verbatim on the page; the execution session should cite the file name with the space in it).
- What's in the repo that's text-readable (and therefore searchable): only 9 files — `.gitattributes`, `.gitignore`, `large file storage.txt`, and 6 JSON files. **Everything else is binary.** The 6 JSON files are 4 CosmosDB `report`-document snapshots (`common/Retail/.../cosmos_report_template.json`, `.../daily_sales.json`, `.../kpi_manager.json`, `.../retail_customer_lifetime_value.json`), plus `templates/cosmos_report_template.json` and `templates/theme.json`. Flag these as valuable: they preserve old report-document schemas and glossaries (e.g., the KPI Manager glossary in `common/Retail/KPI Manager/2022-06/kpi_manager.json` defines AOV/AUR/Conversion %/Returns %/UPT, etc., with HTML-formatted descriptions — these glossaries are what power the PBI template's Glossary feature per the tool page at `entities/tools/power-bi.md:95-99`). This is the only truly readable "content" in the repo.
- Why LFS matters to the reader: a `git clone` without LFS is fast (~MB) but useless. A `git clone` with LFS is slow (GB) and consumes the operator's GitHub LFS quota. Note ALDC's LFS bandwidth considerations — flag as cost/logistics concern in Developer Guide.
- Frame the repo as **"active-but-narrow artefact store"**: actively used for GEP + Fusion92 models (both 2025–2026 commits), stale for most other clients (last commit dates 2022–2024), with legacy content that has never been pruned. Cross-reference `[[entities/tools/power-bi]]` for everything usage-related, `[[GEP]]` + `[[fusion92]]` for the active-client pointers, `[[kit-ace]]`/`[[dish-duer]]`/`[[book-depot]]`/`[[adm]]` (all in `entities/clients/inactive/`) for the legacy-client pointers.

---

### Section 2 — `## Repo layout`

**Purpose:** Full `ls -la` tree at the top-level-plus-one depth so a reader orients in one screen. Deeper detail lives in the Report Catalogue.

**Content — full top-level tree the execution session should embed verbatim:**

```
power_bi/
├── .gitattributes                  # one line: *.pbix filter=lfs diff=lfs merge=lfs -text
├── .gitignore                      # boilerplate Python gitignore (not used — no Python here)
├── large file storage.txt          # ONE-LINE note: LFS required. Repo's only in-repo doc.
├── common/
│   └── Retail/                     # ALDC Retail standard report set (used as starting point for new retail clients)
│       ├── Customer Lifetime Value/    # 1 .pbix (820 KB) + .pptx style guide + CosmosDB report JSON
│       ├── Daily Sales/                # 3 dated subfolders: 2022-01, 2022-03, 2022-06
│       ├── Finance Model/              # 1 .pbix (260 MB) + Date Logic Checker.xlsx
│       ├── Inventory Planner/          # 1 dated subfolder: 2022-01
│       ├── KPI Manager/                # 5 dated subfolders: 2022-03, 2022-06, 2023-10, 2023-11, 2024-07
│       └── Product Benchmark/          # 1 dated subfolder: 2022-06
├── custom/                         # Per-client bespoke models
│   ├── ALDC_FINANCE/               # 2 .pbix (Profitability Model + test); last commit 2024-07
│   ├── ALDC_SALES/                 # 1 .pbix — Netsuite Ops Model (543 MB); last commit 2025-08-08
│   ├── BOOK_DEPOT/                 # 2 dated sales-model subfolders (~300 MB each); last commit 2022-11
│   ├── DISH_DUER/                  # 20 dated combined_model_* / sales_model_* subfolders + executive_snapshot + 3 standalone .pbix; ~5.5 GB total; last commit 2024-08-26 (client now inactive per wiki)
│   ├── FUSION_92/                  # 13 dated subfolders (2024_01 … 2025_12 + Original); all named "Activation Model.pbix"; last commit 2025-12-30 (active client)
│   ├── GEP/                        # 20 dated subfolders (2024_05 … 2026_03 "Data Model" + 2× Daily Sales); all named "Data Model.pbix" or "Daily Sales.pbix"; last commit 2026-03-06 (active client)
│   └── KIT_ACE/                    # 7 subfolders: Daily Sales, Finance Model (2021-10 / 2021-11 / 2022-07 / 2024-10 / 2025-05), Netsuite Data Search; last commit 2025-06-02 (client inactive per wiki BUT still being maintained)
├── internal/                       # ALDC-internal models (not client-facing)
│   ├── ALDC_ENG/                   # 4 .pbix — Account Summary (Prod/Quality/Test) + Account and Template Summary; last commit 2024-12-11
│   └── aldc_demo/                  # 3 .pbix (Architecture, Daily Sales, Data Model) + 6 style-guide .pptx/.png — demo assets; last commit 2024-08 (unverified, mostly static)
├── sales/                          # Pre-sales prospect demos (one-off)
│   ├── 9TH_CO/Cluster Analysis/           # 1 .pbix — Ninth_Co Sample; last commit 2022-08-05
│   ├── APEX_BRASIL/Export Demo/           # 1 .pbix — APEX_BRASIL Export Demo (249 MB); last commit 2022-08-05
│   └── KIT_ACE/Product Pairing Recommender/  # 1 .pbix + .pptx wireframe — pre-sales demo for KIT_ACE (distinct from live custom/KIT_ACE/ reports!)
└── templates/                      # Power BI template .pbix files + theme
    ├── Eclipse Power BI Template 2022-03.pbix      # ~820 KB
    ├── Eclipse Power BI Template 2022-06.pbix      # ~820 KB
    ├── Eclipse Power BI Template 2022-07.pbix      # ~823 KB
    ├── Style Guide.pptx                            # Template style guide
    ├── cosmos_report_template.json                 # Skeleton CosmosDB report document
    └── theme.json                                  # PBI visual theme (SlicerTemplate, DIN Light fonts)
```

**Notes to include in the section body:**

- The folder structure has **two implicit conventions** that the page must surface:
  1. `common/` is *shared starter* content (Retail standard report set). `custom/` is *per-client bespoke*. `internal/` is ALDC-staff-only. `sales/` is *pre-sales demos*. `templates/` is PBI templates. The reader shouldn't have to infer this from names alone.
  2. Inside `custom/GEP/`, `custom/FUSION_92/`, `custom/DISH_DUER/`, and `custom/KIT_ACE/Finance Model (…)/`, there's a dating pattern — most folders are `YYYY_MM` or `(YYYY-MM)`. The most-recent dated folder in each is the live/current model; older dated folders are frozen snapshots retained for rollback/reference. This is a manual snapshot convention, not a git feature. Document it.
- `DISH_DUER/` has **two naming conventions**: `combined_model_2023-06` (hyphenated) through `combined_model_2023_11` (snake_cased) through `sales_model_2022_06`. Inconsistency is in the repo; document as-is.
- `custom/GEP/2025_01 Data Model/` and `custom/GEP/2025_01b Data Model/` — note the `b` variant, which is an intra-month second revision. Same pattern does not appear elsewhere.
- No `.pbip` (Power BI Project folder format) anywhere. Everything is legacy `.pbix` binary. No folder-unpacked TMDL/JSON content to read. Note this in the Developer Guide as a future opportunity (migrating to `.pbip` would make the repo diffable).
- No `docs/`, no `README.md`, no `.github/`, no CI, no workflows, no tests, no scripts. The repo is purely a binary artefact store — the opposite of `eclipse_exp`/`workflows`/`custom-fusion-92-audience-api`.
- `.gitignore` is the **boilerplate Python gitignore** (`__pycache__`, `*.py[cod]`, `.venv`, etc. — lines 1-165) — copied in by mistake or inherited from a template. No Python exists in the repo; the `.gitignore` is effectively vestigial. Flag in Tech Debt.

---

### Section 3 — `## Architecture (or lack thereof)`

**Purpose:** Explicitly explain that this repo has no code architecture — it's a filesystem hierarchy of binary artefacts. Very short section: **three or four paragraphs, no more**. Replaces the usual per-repo Architecture deep-dive.

**Content to convey:**

- **No code, no architecture at the repo level.** This is a binary artefact store. "Architecture" at the `.pbix` level (semantic model, tables, measures, visuals) lives **inside each binary** and is only inspectable by opening the file in Power BI Desktop.
- **The repo's organising principle** is the folder hierarchy: `common/` (shared), `custom/<CLIENT>/` (bespoke), `internal/`, `sales/`, `templates/`. Within each client folder, dated subfolders (`YYYY_MM` or `(YYYY-MM)`) are manually-managed snapshots — an operator creates a new dated folder when a new model revision is cut; older folders are kept for rollback/comparison.
- **No in-repo semantic model diff.** Because `.pbix` is binary, diffs are unreadable (`git diff` on a `.pbix` returns a single LFS pointer line change). Reviewing a change requires the reviewer to open both versions in PBI Desktop. This is a well-known `.pbix` pain point; the migration to `.pbip` folder format (see Tech Debt) is the industry fix and should be planned.
- **Tech stack at the repo level:** Git + Git LFS (GitHub-hosted). Nothing else. All Power-BI-the-tool stack info (desktop version, service, workspaces, gateway, datasets) belongs on `[[entities/tools/power-bi]]` and the page should link out, not repeat.
- **Design decisions worth naming** (short bulleted list):
  1. **Folder-per-client** under `custom/` (not branch-per-client). Makes switch-between-clients a filesystem `cd`, not a `git checkout`.
  2. **Dated-snapshot folders** (`YYYY_MM`) instead of git tags/branches for version history. Trade-off: simpler for non-engineer operators (Power BI analysts) who understand folders better than git tags; cost: repo bloat (every snapshot is a full LFS object).
  3. **All `.pbix` on LFS from day one** — `.gitattributes` is a single line and has been stable since repo-first-commit. Without this the repo would be unusable in GitHub (1 GB file limit without LFS).
  4. **No `.pbip` adoption** — the repo predates or hasn't migrated to the Power BI Project folder format. Flag as a worthwhile migration.
  5. **Text companions alongside binaries** — the `*.json` CosmosDB report documents and `.pptx` style guides sit next to the `.pbix` files, giving the repo at least *some* text content that can be grep'd and diff'd.

---

### Section 4 — `## Data Flow (at the repo level)`

**Purpose:** Very short orientation of what flows INTO the `.pbix` files (not the full tool-page dataflow — link that out). Worth one short section because otherwise a reader who lands here and doesn't know the ALDC stack is lost.

**Content — short, mostly a pointer, with one ASCII diagram:**

- **Inbound data to every `.pbix`** is always one of:
  1. **Snowflake `REPORT_COMMON.*` views** (majority of models — GEP, Fusion92, KIT_ACE, DISH_DUER). Connector is the native Power BI Snowflake connector. Env-specific — each `.pbix`'s M-query / data source connection points to a specific Snowflake host + warehouse (see tool page § Connection Parameters).
  2. **Intermediate SQL Server** (GEP only, for partition / reprocessing runs — see `[[SSMS]]`). The GEP `Data Model.pbix` files in `custom/GEP/20YY_MM Data Model/` may point at a SQL Server DB rather than directly at Snowflake; per `[[entities/tools/power-bi]]:11`, "data usually passes through a SQL Server layer edited via SSMS in between." Confirm per-model during execution if possible (by looking at the `.pbix`'s M-queries, which requires opening in PBI Desktop).
  3. **NetSuite direct** (ALDC_SALES / ALDC_FINANCE / KIT_ACE Finance Model / KIT_ACE Netsuite Data Search) — direct ODBC or REST ingestion, not via Snowflake. Note these are the odd ones out.
  4. **CosmosDB — report document** — NOT a data source for the PBI model's rows, but the source of the template's **Glossary** entries (per `[[entities/tools/power-bi]]:98`). The 6 `*.json` files committed to the repo are frozen copies of these CosmosDB documents. Reference them as the source of per-report glossary keys.
- **Outbound flow:** `.pbix` files don't "flow out" from the repo — they get published to Power BI Service workspaces by a developer clicking Publish in PBI Desktop. The workspace mapping per client is on `[[entities/tools/power-bi]]:56` (GEP: `GEP Test Models` + `Production`). Reference the runbooks `[[gep-snowflake-pbi-deployment]]` and `[[model-deploy-production]]` — do not duplicate.
- **Secret refresh is orthogonal** — `[[powerbi-secret-refresh]]` documents the Azure AD client-secret rotation for the DISH_DUER / FUSION92 / GEP / KIT_ACE Power BI App Registrations. Those secrets are used by the PBI Service, not the `.pbix` files themselves, but the runbook is relevant to anyone publishing to these workspaces. Cross-reference.
- **Single ASCII dataflow diagram** — mirrors the tool page's, annotated with which folder in THIS repo each box corresponds to:

```
Snowflake REPORT_COMMON.*       ◄── warehouse deploy (clients repo § snowflake/)
        │
        ▼
(optional) SQL Server + SSMS    ◄── GEP partition runs (custom/GEP/*.pbix)
        │
        ▼
.pbix semantic model            ◄── THIS REPO (common/ + custom/ + internal/)
        │                           Per-file Snowflake-connector M-queries
        │                           Per-file CosmosDB-fed Glossary + report-id
        │                           (cosmos_report_template.json / daily_sales.json / …)
        ▼
Power BI Service workspace      ◄── Publish (via Power BI Desktop, manual)
        │                           GEP: "GEP Test Models" + "Production"
        │                           FUSION92: Fusion92-specific workspace (see tool page for details)
        ▼
Client user in Excel or web     ◄── tool page § Granting Excel Model Access
```

- Finish with a one-sentence pointer: *"For the full ALDC data pipeline context, see [[data-pipeline-flow]]."*

---

### Section 5 — `## Report Catalogue` (centrepiece)

**Purpose:** Per-folder, per-`.pbix` inventory. This is the load-bearing section for the page — replaces the usual "API Reference" / "Component Map" sections — because the `.pbix` filenames and their last-commit dates are the only truly repo-specific information available, and they are what a reader comes here to look up.

**Execution session guidance:** the tables below list every committed `.pbix` as of 2026-04-20 (plan session). The execution session should re-run `ls -R` + `git log --all --pretty=format:"%ad" --date=short -- "<file>"` if content has changed, but the expected inventory is stable. Use **the LFS-listed sizes from `git lfs ls-files --size`** for the "Size" column — these were captured during the plan session and are reproduced verbatim below.

#### Table 5a — `templates/`

| File | Last modified (repo tree) | Git LFS size | Status | Notes |
|---|---|---|---|---|
| `templates/Eclipse Power BI Template 2022-03.pbix` | 2022-03 | 820 KB | **Legacy (stale)** | Snapshot only; tool page § Report Template says canonical templates live in `Nextcloud\Customers\Style Guides`. |
| `templates/Eclipse Power BI Template 2022-06.pbix` | 2022-06 | 820 KB | Legacy (stale) | Same — superseded by Nextcloud copy. |
| `templates/Eclipse Power BI Template 2022-07.pbix` | 2022-07 | 823 KB | Legacy (stale) | Same. |
| `templates/Style Guide.pptx` | 2022 | small | Reference | Style-guide deck. |
| `templates/cosmos_report_template.json` | 2022 | 1.4 KB | Readable | Skeleton CosmosDB report document; points to the 9thco "Book Outlet Campaign Demo" as its literal template text — a demo-report JSON being reused as a skeleton. |
| `templates/theme.json` | 2022 | 356 B | Readable | PBI visual theme — single SlicerTemplate, DIN Light font family, black-on-white. Execution session may quote the whole file (7 non-trivial lines). |

**Section-body notes:** call out explicitly that **the in-repo `templates/` folder is the stale snapshot; source of truth is Nextcloud** per the tool page. Recommend in Tech Debt that the in-repo copies either be removed + replaced with a README pointer, or re-synced on every template revision.

#### Table 5b — `common/Retail/`

| Path | Last commit | Git LFS size | Status | Notes |
|---|---|---|---|---|
| `common/Retail/Customer Lifetime Value/Retail - Customer Lifetime Value.pbix` | 2023-03-22 (folder last touch: 2023-03 per git log) | 820 KB | Shared retail starter | Paired with `retail_customer_lifetime_value.json` (CosmosDB report doc — name "Customer Lifetime Value", industry "Retail", client_owner Justin Cook @ 9thco.com, dev_owner Sean O'Grady). Glossary: 1 entry (`clusters`). |
| `common/Retail/Daily Sales/2022-01/Daily Sales.pbix` | 2022-01 | 4.1 MB | Legacy shared starter | Superseded by 2022-06 variant. |
| `common/Retail/Daily Sales/2022-03/Daily Sales.pbix` | 2022-03 | 1.3 MB | Legacy shared starter | Superseded by 2022-06. |
| `common/Retail/Daily Sales/2022-06/Daily Sales.pbix` + `Daily Sales Mobile.pbix` | 2022-06 | 4.4 MB + 139 KB | Current shared starter | Paired with `daily_sales.json` (CosmosDB report doc — template_version "2022-06", glossary 9 entries, 20-key config dict, status "In Progress", id `19675a6b-…`). |
| `common/Retail/Finance Model/Finance Model.pbix` + `Date Logic Checker.xlsx` | (predates git-log scope — 2022-era) | 260 MB | Shared starter | 260 MB — one of the largest files in `common/`. |
| `common/Retail/Inventory Planner/2022-01/Inventory Planner.pbix` | 2022-01 | 302 MB | Legacy shared starter | 302 MB — largest file in `common/`. Only 2022-01 version exists. |
| `common/Retail/KPI Manager/2022-03/KPI Manager.pbix` | 2022-03 | 1.4 MB | Legacy | |
| `common/Retail/KPI Manager/2022-06/KPI Manager.pbix` | 2022-06 | 1.5 MB | Reference (has JSON companion) | Paired with `kpi_manager.json` (CosmosDB report doc — template_version "2022-06", 12-entry glossary incl. AOV/AUR/Conversion %/Returns %/UPT, id `c82414c8-…`, status "Review by Client"). |
| `common/Retail/KPI Manager/2023-10/Retail KPI Manager.pbix` | 2023-10 | 1.5 MB | | |
| `common/Retail/KPI Manager/2023-11/Retail KPI Manager.pbix` | 2023-11 | 1.5 MB | | |
| `common/Retail/KPI Manager/2024-07/KPI Manager.pbix` | 2024-07 | 1.6 MB | **Current shared starter** | Most recent KPI Manager variant. |
| `common/Retail/Product Benchmark/2022-06/Product Benchmark.pbix` + `cosmos_report_template.json` + `Style Guide.pptx` | 2022-06 | 7.4 MB | Shared starter | Only 2022-06 version. JSON companion defines "Book Outlet Campaign Demo" as the report doc (9thco sample). |

**Section-body notes:** `common/Retail/` is ALDC's *retail standard report set* — the starting point when spinning up a new retail client. Cross-reference `[[kit-ace]]`, `[[dish-duer]]`, `[[book-depot]]`, `[[GEP]]` as historical consumers of this starter set. Call out that the last commit to `common/` was **2024-08-13** — the starter set has not been meaningfully updated in ~20 months; treat as stable baseline, not living content.

#### Table 5c — `custom/GEP/` (MOST ACTIVE folder)

Columns: Folder | Last-commit date | Size (LFS) | Filename | Status | Notes

| Folder | Last commit | Size | Filename | Status | Notes |
|---|---|---|---|---|---|
| `custom/GEP/2024_05 Data Model/` | 2024-05 | 480 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2024_07 Data Model/` | 2024-07 | 512 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2024_08 Daily Sales/` | 2024-08 | 3.8 MB | `Daily Sales.pbix` | Snapshot | GEP's daily-sales side-model (distinct from the main Data Model). |
| `custom/GEP/2024_09 Daily Sales/` | 2024-09 | 3.8 MB | `Daily Sales.pbix` | Snapshot | |
| `custom/GEP/2024_09 Data Model/` | 2024-09-29 (`"Remove extra model and update September model with unhidden marketing measures"`) | 184 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2024_10 Data Model/` | 2024-10-21 | 224 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2024_11 Data Model/` | 2024-11 | 244 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2024_12 Data Model/` | 2025-01-08 | 261 MB | `Data Model.pbix` | Snapshot | Last-touched as "Updated Amazon Browse Category / Updated FBA DOC Calculation". |
| `custom/GEP/2025_01 Data Model/` | 2025-01-20 | 266 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2025_01b Data Model/` | 2025-03-05 | 352 MB | `Data Model.pbix` | Snapshot (intra-month b-variant) | The `b` suffix = intra-month second revision; unique to this folder. |
| `custom/GEP/2025_02 Data Model/` | 2025-03-05 | 357 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2025_03 Data Model/` | 2025-03-25 | 353 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2025_04 Data Model/` | 2025-04-15 (`GP-76-asin-granularity-and-sessions-updates`) | 361 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2025_05 Data Model/` | 2025-05-05 (`GP-87`) | 361 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2025_06 Data Model/` | 2025-06-27 | 473 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2025_07 Data Model/` | 2025-07-18 | 639 MB | `Data Model.pbix` | Snapshot | Largest GEP model to date. |
| `custom/GEP/2025_09 Data Model/` | 2025-09-29 | 531 MB | `Data Model.pbix` | Snapshot | |
| `custom/GEP/2025_10 Data Model/` | 2025-10-16 (`Last Sale Date - moved to SQL`) | 542 MB | `Data Model.pbix` | Snapshot | Note "moved to SQL" — confirms SSMS-layer dependency per `[[entities/tools/power-bi]]`. |
| `custom/GEP/2025_12 Data Model/` | 2026-02-11 | 332 MB | `Data Model.pbix` | Snapshot | Multi-month rev cycle: created 2025-12, last-touched 2026-02 ("Update DTC field visibility" / "Add DTC fee"). |
| `custom/GEP/2026_03 Data Model/` | **2026-03-06** (`update power bi model for gp-169`) | 346 MB | `Data Model.pbix` | **CURRENT LIVE MODEL** | Most recently touched file in the repo. Corresponds to [[GP-169]] — execution session should cross-reference the ticket page if it exists. |

**Section-body notes:** GEP is the repo's most active and deepest-versioned client. **20 dated subfolders spanning 23 months.** Monthly-to-bi-monthly cadence. The working pattern is: (1) new month? create `YYYY_MM Data Model/`, (2) copy prior-month `.pbix` in, (3) edit in PBI Desktop + commit. Superseded months are left for rollback. **Net effect:** the `custom/GEP/` folder alone is ~7 GB LFS. Flag in Tech Debt: a ticking retention question — no pruning policy; GEP on its own will exceed 10 GB within a year at this cadence. Commit messages reference GP-ticket IDs (GP-76, GP-87, GP-169, etc.) — cross-reference the `tickets/gep/` wiki pages for any matching IDs the execution session finds. Active authors: `aldc-karenprete`, `aldc-stevendeutekom`, `aldc-braydenmarshall`, `Paul Russell` (only the 2026-03-06 commit is Paul's).

#### Table 5d — `custom/FUSION_92/` (active client)

| Folder | Last commit | Size | Status | Notes |
|---|---|---|---|---|
| `custom/FUSION_92/Original/` | (pre-2024 — first commit) | 3.0 MB | Frozen origin | Earliest Activation Model. |
| `custom/FUSION_92/2024_01/` | 2024-01 | 3.6 MB | Snapshot | |
| `custom/FUSION_92/2024_04/` | 2024-04 | 3.5 MB | Snapshot | |
| `custom/FUSION_92/2024_06/` | 2024-06 | 4.1 MB | Snapshot | |
| `custom/FUSION_92/2024_07/` | 2024-07 | 4.3 MB | Snapshot | |
| `custom/FUSION_92/2024_09/` | 2024-09 | 5.6 MB | Snapshot | |
| `custom/FUSION_92/2024_10/` | 2024-10 | 5.7 MB | Snapshot | |
| `custom/FUSION_92/2024_12/` | 2025-01-03 | 9.8 MB | Snapshot | |
| `custom/FUSION_92/2025_01/` | 2025-01-14 | 13 MB | Snapshot | |
| `custom/FUSION_92/2025_03/` | 2025-03-07 (`Create Activation Model.pbix`) | 13 MB | Snapshot | |
| `custom/FUSION_92/2025_04/` | 2025-04-15 | 14 MB | Snapshot | |
| `custom/FUSION_92/2025_05/` | 2025-12-17 | 14 MB | Snapshot (re-touched in 2025-12) | |
| `custom/FUSION_92/2025_12/` | **2025-12-30** (`Hide new fields in platform table`) | 25 MB | **CURRENT LIVE MODEL** | Every Fusion92 model is named `Activation Model.pbix` — see `[[dax-ai]]` for the Activation Model context. |

**Section-body notes:** Fusion92 is monthly-to-quarterly cadence — 13 total snapshots. File sizes grow steadily (~3 MB → ~25 MB) as fields are added. Most recent is 2025-12. Cross-reference `[[fusion92]]` (active client page) and `[[dax-ai]]` (DAX AI project — the Activation Model is the F92-specific centrepiece). Active authors: `aldc-karenprete`, `aldc-stevendeutekom`.

#### Table 5e — `custom/DISH_DUER/` (largest folder, INACTIVE client)

| Folder | Last commit | Size | Filename | Status | Notes |
|---|---|---|---|---|---|
| `custom/DISH_DUER/Customer Value 2022-01.pbix` | 2022-01 | 24 MB | standalone .pbix | Legacy | |
| `custom/DISH_DUER/Daily Sales - DTC.pbix` | 2022 | 3.0 MB | standalone .pbix | Legacy | |
| `custom/DISH_DUER/Daily Sales - Wholesale.pbix` | 2022 | 3.0 MB | standalone .pbix | Legacy | |
| `custom/DISH_DUER/sales_model_2022_06/` | 2022-06 | 43 MB | `Sales Model.pbix` (+ xlsx test) | Legacy | |
| `custom/DISH_DUER/sales_model_2023_01/` | 2023-01 | 75 MB | `Sales Model.pbix` | Legacy | |
| `custom/DISH_DUER/sales_model_2023_02/` | 2023-02 | 78 MB | `Sales Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2023_03/` | 2023-03 | 313 MB | `Combined Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2023_04/` | 2023-04 | 324 MB | `Combined Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2023_05/` | 2023-05 | 327 MB | `Combined Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2023-06/` | 2023-06 | 510 MB | `Combined Model.pbix` | Legacy (hyphenated folder name — naming inconsistency) | |
| `custom/DISH_DUER/combined_model_2023-07/` | 2023-07 | 466 MB | `Combined Model.pbix` | Legacy (hyphenated) | |
| `custom/DISH_DUER/combined_model_2023_08/` | 2023-08 | 350 MB | `Combined Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2023_09/` | 2023-09 | 426 MB | `Combined Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2023_10/` | 2023-10 | 465 MB | `Combined Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2023_11/` | 2023-11 | 521 MB | `Sales Model (Types).pbix` | Legacy (filename diverges) | |
| `custom/DISH_DUER/combined_model_2024_02/` | 2024-02 | 588 MB | `Sales Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2024_04/` | 2024-04 | 559 MB | `Sales Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2024_06/` | 2024-06 | 591 MB | `Sales Model.pbix` | Legacy | |
| `custom/DISH_DUER/combined_model_2024_08/` | **2024-08-26** | 612 MB | `Sales Model.pbix` | **Latest DISH_DUER model (frozen)** | Last DISH_DUER activity. Client is inactive per `[[dish-duer]]` (page lives in `entities/clients/inactive/`). |
| `custom/DISH_DUER/executive_snapshot/` | 2024-08-13 | 2.6 MB + 137 KB (mobile) | `Executive Snapshot.pbix` + `Executive Snapshot Mobile.pbix` + `.png` | Frozen | Note the `Executive_snapshot.png` preview. |

**Section-body notes:** DISH_DUER is the repo's **biggest client by footprint** (~5.5 GB LFS across 20 subfolders) and also the most **legacy** — last commit 2024-08, client now in `entities/clients/inactive/`. Cross-reference `[[dish-duer]]` explicitly and mark the folder as "Status: legacy (client inactive)". Candidate for archival / removal if LFS bandwidth becomes a cost concern — flag in Tech Debt. Naming inconsistency (`combined_model_2023-06` vs `combined_model_2023_09` vs `sales_model_2022_06`) should be noted once; no need to fix.

#### Table 5f — `custom/KIT_ACE/` (INACTIVE client but still being maintained)

| Folder | Last commit | Size | Status | Notes |
|---|---|---|---|---|
| `custom/KIT_ACE/Daily Sales/` | (pre-2023) | 4.8 MB + 136 KB mobile | `Daily Sales.pbix` + `Daily Sales Mobile.pbix` | Frozen | |
| `custom/KIT_ACE/Finance Model (2021-10)/` | 2021-10 | 83 MB | Frozen origin | |
| `custom/KIT_ACE/Finance Model (2021-11)/` | 2021-11 | 125 MB | Legacy | |
| `custom/KIT_ACE/Finance Model (2022-07)/` | 2022-07 | 99 MB | Legacy | |
| `custom/KIT_ACE/Finance Model (2024-10)/` | 2024-10 | 117 MB | Legacy | |
| `custom/KIT_ACE/Finance Model (2025-05)/` | **2025-06-02** | 118 MB + 147 MB | **CURRENT FINANCE + INVENTORY MODELS** | Folder named `2025-05` but last touched 2025-06; contains both `Finance Model DG1 2022-07.pbix` AND `Inventory Model DG1 2022-07.pbix` (filename retains "2022-07" nominal template version despite content being 2025). Commit-message pair from 2025-06-02: "Add updated finance model that is consistent with previous versions" + "Temp add inventory model" + "Updated inventory balances DAX query". |
| `custom/KIT_ACE/Netsuite Data Search/` | (pre-2025) | 1.7 MB | `Netsuite Data Search.pbix` | Standing reference model | |

**Section-body notes:** Contradiction flag. `[[kit-ace]]` wiki page is in `entities/clients/inactive/` but the repo shows a live 2025-06 commit on the Finance + Inventory models. **Per wiki rule #6 (`flag contradictions, don't silently resolve`)**, the wiki page should add a `> Contradiction:` callout saying: *"The wiki marks KIT_ACE as inactive, but `custom/KIT_ACE/Finance Model (2025-05)/` was last touched 2025-06-02 and `Inventory Model DG1 2022-07.pbix` was added in 2025-06. Either the client is more active than the wiki reflects, or the model is being maintained for a transitioned-out relationship. Needs confirmation."* The execution session should add this callout verbatim. Also note the curious **filename convention**: `Finance Model DG1 2022-07.pbix` continues to carry "2022-07" in the filename even though it's been modified through 2025. Interpret as "template-version stamp" — the filename names the original PBI template version used to build it, not the last-modified date.

#### Table 5g — `custom/BOOK_DEPOT/` (INACTIVE, frozen)

| Folder | Last commit | Size | Status | Notes |
|---|---|---|---|---|
| `custom/BOOK_DEPOT/Sales Model/Sales Model.pbix` | 2022-10 | 298 MB | **Frozen** | Last touched 2022-11-21. |
| `custom/BOOK_DEPOT/Sales Model 2022-10/Sales Model.pbix` | 2022-11 | 305 MB | Frozen | |

**Section-body notes:** Client inactive per `[[book-depot]]` (in `entities/clients/inactive/`). No activity since 2022-11. Candidate for archival. Note: `[[book-depot]]` wiki notes IPSEC VPN requirement (CUST-202) — the `CUST-*` branches on origin (`CUST-303`, `CUST-396`, `CUST-421`, `CUST-461`, `CUST-528`, `cust-457`) likely relate to BOOK_DEPOT + DISH_DUER / KIT_ACE era tickets. Stale branches — flag in Tech Debt.

#### Table 5h — `custom/ALDC_FINANCE/` and `custom/ALDC_SALES/` (internal)

| Path | Last commit | Size | Status | Notes |
|---|---|---|---|---|
| `custom/ALDC_FINANCE/Profitability Model.pbix` | 2024-07-10 | 2.6 MB | Likely legacy (2024-07 last touch) | Internal ALDC profitability reporting. |
| `custom/ALDC_FINANCE/Profitability Model Test.pbix` | 2024-07 | 2.5 MB | Test variant | Paired with prod above. |
| `custom/ALDC_SALES/Netsuite Ops Model.pbix` | **2025-08-08** (`add netsuite sales ops demo`) | 543 MB | Current | Internal ALDC sales ops — likely a demo/sandbox given commit message "sales ops demo". 543 MB — second-largest file in the repo. |

**Section-body notes:** `custom/ALDC_FINANCE/` is anomalous — it's an ALDC-internal model living under `custom/` rather than `internal/`. Flag the naming inconsistency (should arguably be under `internal/` to match `internal/ALDC_ENG/` and `internal/aldc_demo/`). Don't propose a move — document as-is.

#### Table 5i — `internal/`

| Path | Last commit | Size | Status | Notes |
|---|---|---|---|---|
| `internal/ALDC_ENG/Account and Template Summary.pbix` | 2024-12-11 | 293 MB | Legacy | Internal eng reporting on Eclipse accounts + templates (likely pulled from CosmosDB per `[[cosmosdb-schema]]`). |
| `internal/ALDC_ENG/Account Summary Prod Canada DG1.pbix` | 2024-12-11 | 125 MB | Legacy | Per-deployment-group summary. |
| `internal/ALDC_ENG/Account Summary Quality Canada DG1.pbix` | 2024-12-11 | 1.4 MB | Legacy | |
| `internal/ALDC_ENG/Account Summary Test Canada DG1.pbix` | 2024-12-11 | 38 MB | Legacy | |
| `internal/aldc_demo/Architecture.pbix` | pre-2024 | 4.1 MB | Demo | |
| `internal/aldc_demo/Daily Sales.pbix` | pre-2024 | 45 MB | Demo | |
| `internal/aldc_demo/Data Model.pbix` | pre-2024 | 32 MB | Demo | |
| `internal/aldc_demo/Style Guide - Daily Sales*.{png,pptx}` | 2022 | small | Demo style-guide assets | Multiple file variants + a misspelled `Summarzy.png`. |

**Section-body notes:** `internal/ALDC_ENG/` is ALDC's internal Eclipse observability — four "Account Summary" models, one per deployment group (Prod, Quality, Test, Canada DG1) plus a combined. Last touched 2024-12 — note whether this is still maintained; cross-reference `[[deployment-groups]]` (documents Canada DG-Prod2/QA1/Test1/Demo1/Dev DG1–4). The `aldc_demo/` folder holds demo/style-guide artefacts — not a production model, safe to treat as reference material.

#### Table 5j — `sales/` (pre-sales demos)

| Path | Last commit | Size | Status | Notes |
|---|---|---|---|---|
| `sales/9TH_CO/Cluster Analysis/Ninth_Co Sample.pbix` | 2022-08-05 | 5.4 MB | Frozen pre-sales demo | 9thco reference — note: 9thco is the client_owner on several `common/Retail/` CosmosDB report JSONs. |
| `sales/APEX_BRASIL/Export Demo/APEX_BRASIL Export Demo.pbix` | 2022-08-05 | 249 MB | Frozen pre-sales demo | Apex Brasil export demo. Client does not appear in `entities/clients/` — flag as unknown-status prospect. |
| `sales/KIT_ACE/Product Pairing Recommender/Product Pairing Recommender.pbix` + `.pptx` wireframe | (pre-2023) | 31 MB | Frozen pre-sales demo | **Distinct from `custom/KIT_ACE/`** — this is a sales-pitch artefact for a "Product Pairing Recommender" capability never productised. Same client name, different intent. |

**Section-body notes:** `sales/` is effectively a frozen pre-sales-demo graveyard. Last commit 2022-08. Candidate for archival. The `sales/KIT_ACE/` disambiguation from `custom/KIT_ACE/` is important — flag it in the intro to the section.

---

### Section 6 — `## Developer Guide`

**Purpose:** Get a developer from clean clone to edit-and-publish for a `.pbix` file. Medium-length section — the clone-with-LFS story and the publishing workflow are genuinely non-trivial.

**Sub-sections:**

- `### Prerequisites`
  - **Git LFS installed** — `git lfs install` before first clone. Without LFS, the `.pbix` files come down as 134-byte pointer stubs. Note: `brew install git-lfs` on macOS; `choco install git-lfs` on Windows (or download from git-lfs.com); `apt install git-lfs` on Debian/Ubuntu. This is the #1 pitfall for a new dev — the repo's only in-repo documentation (`large file storage.txt`) exists specifically to call this out. Quote its single-sentence content verbatim.
  - **Sufficient disk + bandwidth** — a full clone pulls ~16 GB of LFS objects. For editing one client's models, use **partial LFS fetch**: `git lfs install --skip-smudge && git clone … && cd power_bi && git lfs fetch --include="custom/GEP/**" --exclude=""` (or equivalent per-client). This is the practical developer pattern for avoiding the full 16 GB pull. Document the command.
  - **Power BI Desktop** installed — the **only** editor that can open `.pbix`. **Windows only** — no macOS/Linux native support (Power BI Desktop has no Mac build; a Mac user must use Parallels / remote Windows). Flag this platform limitation explicitly.
  - **Version alignment** — a `.pbix` saved in a newer PBI Desktop version will fail to open in an older one (`"Unable to open the document because it was saved with a newer version of Power BI Desktop"`). Keep PBI Desktop current; the Power BI Desktop team ships roughly monthly. No version is pinned in the repo — there's no `.pbix-version` file or convention.
  - **Snowflake + Azure AD credentials** — to *refresh* or *publish* a model, the dev needs Snowflake credentials (see `[[Snowflake]]`) and an account in the target PBI workspace (per-client — see `[[entities/tools/power-bi]]:56`).

- `### Clone the repo`
  1. `git lfs install` (one-time per machine).
  2. `git clone https://github.com/ALDC-io/power_bi.git` — if you need *everything* (~16 GB, will take a while).
  3. Preferred (selective): `git lfs install --skip-smudge && git clone https://github.com/ALDC-io/power_bi.git && cd power_bi && git lfs fetch --include="custom/<CLIENT>/<MOST_RECENT_FOLDER>/**"` then `git lfs checkout custom/<CLIENT>/<MOST_RECENT_FOLDER>/*.pbix`.
  4. Verify: `git lfs ls-files | head` — each line should show an object ID + filename. If lines show `-` status, run `git lfs pull` to download them.

- `### Edit a `.pbix` file`
  1. Identify the current live model from the **Report Catalogue** above (e.g., for GEP that's `custom/GEP/2026_03 Data Model/Data Model.pbix` as of 2026-04-20).
  2. **Create a new dated folder**, don't overwrite in place: e.g., `cp -r custom/GEP/2026_03\ Data\ Model custom/GEP/2026_04\ Data\ Model` (new month, copy the latest model forward). Older folder retained as rollback.
  3. Open the new `.pbix` in Power BI Desktop.
  4. Edit as needed — adjust M-queries, measures, visuals.
  5. **Refresh the data connection** if changing schema — this requires Snowflake credentials for the relevant environment (test vs prod — see `[[azure-environments]]` + tool page workspace mapping).
  6. Save the `.pbix` (Power BI Desktop saves in-place).
  7. **Commit convention.** Per observed git log — commits are one `.pbix` per commit, short descriptive message, often referencing a Jira ID for GEP (`GP-76-asin-granularity-and-sessions-updates`) or fragment-of-spec for others. Example good messages: "Hide new fields in platform table" (F92), "update power bi model for gp-169" (GEP), "Fix margin calculation" (GEP). Paul does not mass-commit; commits are always small and specific.
  8. `git add` the specific `.pbix` + `git commit -m "…"` + push.
  9. **Do NOT mass-commit** — one `.pbix` per commit is the observed discipline (exceptions: when copying a model from month X to month Y, the first commit may add both; see `Move latest changes to a december folder and restore previous version` from 2025-12-17 which touched 2 files).

- `### Publish to Power BI Service`
  1. In PBI Desktop → File → Publish → pick the correct workspace (per-client; per-env for GEP). See `[[entities/tools/power-bi]]` § Power BI Workspaces for the mapping.
  2. Refresh the dataset in the Service (manual — per tool page § Model Refresh).
  3. For production deploys, follow the full runbook: `[[gep-snowflake-pbi-deployment]]` (GEP-specific) or `[[model-deploy-production]]` (generic). Do not duplicate the runbook here.
  4. After deploy, consider whether client secrets need rotation — see `[[powerbi-secret-refresh]]` (quarterly / 6-month cadence per `[[powerbi-secret-refresh]]`).

- `### Common pitfalls`
  1. **Clone without LFS** — downloads pointer stubs; PBI Desktop fails to open. Run `git lfs install` + `git lfs pull`.
  2. **Full-repo clone on metered bandwidth** — 16 GB pull is the trap. Use selective `git lfs fetch --include=`.
  3. **Opening a `.pbix` on Mac/Linux** — impossible natively; Parallels / Windows VM only. Plan for it.
  4. **PBI Desktop version mismatch** — a teammate on a newer version saves; you can't open. Keep PBI Desktop current.
  5. **Overwriting in place** — the repo convention is new dated folder, not in-place edit. In-place overwrites lose the rollback history.
  6. **Schema drift Snowflake ↔ `.pbix`** — if `REPORT_COMMON` columns change and the `.pbix` is refreshed without matching update, refresh fails. Coordinate with the clients-repo warehouse deploy — see `[[data-pipeline-flow]]` and `[[debugging-warehouse-loads]]`.
  7. **`.gitignore` is a Python boilerplate** — nothing is ignored that a PBI dev cares about (`__pycache__` etc. are irrelevant), but a dev may mistake the presence of `.gitignore` for meaningful config. It's vestigial.
  8. **Dated-folder naming inconsistency** — DISH_DUER uses both `combined_model_2023-06` (hyphen) and `combined_model_2023_09` (underscore); GEP uses `2024_05 Data Model` (space-separated); KIT_ACE uses `Finance Model (2025-05)` (parenthesised). When creating a new dated folder, match the prevailing convention *for that specific client folder*, not a global convention.
  9. **Template in repo vs Nextcloud** — the `templates/*.pbix` files in this repo are **stale** (last 2022-07). Per tool page, canonical templates live in `Nextcloud\Customers\Style Guides`. Don't start from the in-repo template; start from the Nextcloud copy.
  10. **Secret rotation timing** — if the PBI Service App Registration secret is close to expiry during a publish, refresh will fail. Check `[[powerbi-secret-refresh]]` § Current secret expiry dates before publishing.
  11. **Stale `CUST-*` branches on origin** — `CUST-303`, `CUST-396`, `CUST-421`, `CUST-461`, `CUST-528`, `cust-457`. These are old DISH_DUER / KIT_ACE / BOOK_DEPOT era feature branches, never cleaned up. Ignore them unless explicitly working on a matching `CUST-*` ticket (unlikely — DISH_DUER is inactive).
  12. **`.pbix` binary diffs are useless** — `git diff` on a `.pbix` shows a single LFS pointer line change. Reviewing a change = opening both versions in PBI Desktop. No shortcut.

---

### Section 7 — `## Deployment`

**Purpose:** Deploy in the Power BI sense = publish to Power BI Service. Short section because the full runbooks exist elsewhere and should be linked, not duplicated.

**Sub-sections:**

- `### Deployment target — Power BI Service workspaces`
  - No CI/CD. No `.github/workflows/`. No automated publish. Every `.pbix` deploy is a human action in Power BI Desktop (File → Publish).
  - Target workspace is per-client, and for GEP per-environment. See `[[entities/tools/power-bi]]` § Power BI Workspaces for the mapping (GEP: `GEP Test Models` vs `Production`; other clients have their own workspaces per the secret table in `[[powerbi-secret-refresh]]` — DISH_DUER / FUSION92 / GEP / KIT_ACE each have a separate Azure AD App Registration).
  - Git branch does NOT gate deployment — merging to `main` does nothing; a human still clicks Publish.

- `### Deploy steps (authoritative runbooks — link out)`
  - **GEP full deploy:** follow `[[gep-snowflake-pbi-deployment]]` (343 lines — the most complete PBI deploy runbook in the wiki; covers Snowflake + PBI together for GEP).
  - **Generic PBI model deploy:** `[[model-deploy-production]]` (51 lines — 4-step checklist including Excel Analyze and Eclipse posting).
  - **Pre-release verification:** `[[client-release-checklist]]`.
  - **Secret refresh (Azure AD App Registration for PBI service account):** `[[powerbi-secret-refresh]]` — check before publishing if secret is near expiry (6-month cycle).

- `### Rollback`
  - **Model-level rollback:** open the prior dated folder's `.pbix` in PBI Desktop and Publish — overwrites the Service dataset with the older version.
  - **No automated rollback** — rollback is "open older file, hit Publish." Hence the repo's dated-folder-snapshot convention is the rollback mechanism.
  - **No data rollback** — `.pbix` rollback only reverts the semantic model; the Snowflake warehouse state is unaffected. For full-stack rollback see `[[gep-snowflake-pbi-deployment]]`.

- `### No repo-level CI/CD`
  - No `.github/workflows/`. No tests — `.pbix` files aren't testable in the unit-test sense. No linter, no formatter.
  - Unlike the rest of the 2026-04 ALDC portfolio (`[[eclipse_exp]]`, `[[workflows]]`, `[[custom-fusion-92-audience-api]]`, `[[flight-check]]`, `[[prospect-site-template]]` — all of which have PR checks per `[[ai-pr-workflow]]`), this repo has **zero automated gates**. Any commit to `main` is accepted. Note the contrast so readers don't expect `[[ai-pr-workflow]]` to apply here.
  - Note: unlike `[[aldc-scripts]]` where the no-CI-no-tests is a concern for behaviour-affecting scripts, for a binary-artefact repo the lack of CI is conventional — there's no meaningful CI you could add until `.pbix` → `.pbip` migration provides text artefacts to lint.

---

### Section 8 — `## Security & Credentials`

**Purpose:** Record credential-scan findings + surface sensitive identifiers. Short section because a binary-artefact repo has a narrow surface area — credentials are inside the `.pbix` files (opaque), not in committed text.

**Sub-sections:**

- `### Credential scan — results`
  - **Text-file scan is CLEAN.** The 9 text-readable files (`.gitattributes`, `.gitignore`, `large file storage.txt`, 6 JSONs) were grep'd for Slack webhooks (`hooks.slack.com`), Anthropic keys (`sk-ant-`), GitHub PATs (`ghp_`), AWS keys (`AKIA`), Snowflake account URLs, and generic `password`/`secret`/`token`/`key` substrings. Nothing sensitive found. The JSONs contain only ALDC-internal identifiers (CosmosDB `account_id` values like `61c98864` / `8425e311` / `5d556742` / `4dc61c31` — these are client tenant IDs per `[[cosmosdb-schema]]`, not secrets) + CosmosDB system fields (`_rid`, `_self`, `_etag`, `_attachments`, `_ts`).
  - **The `.pbix` binaries are opaque to grep.** A `.pbix` file is a renamed ZIP archive; it can contain embedded M-query strings with connection info (Snowflake hosts, CORE_API URLs, account IDs, report IDs per `[[entities/tools/power-bi]]:90-93`). **Credentials are NOT stored inside `.pbix` in the normal workflow** — PBI Desktop stores credentials in the user's Windows Credential Manager (DESKTOP scope) or in the Service's dataset credential config (SERVICE scope). **However**, the `.pbix` *schema* and *parameter values* (account ID, report ID, host) ARE persisted inside the file. A leaked `.pbix` exposes the warehouse topology, not a password.
  - **Do NOT attempt to unzip + grep `.pbix`** — the ZIPs contain binary model data (`DataModel` internal format is proprietary). The only safe way to inspect is opening in PBI Desktop. Leave the binaries as-is.
- `### Sensitive identifiers that DO appear in text`
  - **CosmosDB account IDs** in the JSON files — `61c98864` (Customer Lifetime Value — 9thco client), `8425e311` (Daily Sales — KIT_ACE client per client_owner email), `5d556742` (KPI Manager — DISH_DUER client per calvin@shopduer.com), `4dc61c31` (Product Benchmark — 9thco client). These are Eclipse account IDs per `[[cosmosdb-schema]]`. Not secrets; documented in other wiki pages. No action needed.
  - **Client-owner contact emails** (Justin Cook / Calvin Roex / Kat Petrova / Karen Prete) in the JSONs. Already semi-public (customer contacts in CosmosDB docs); not secrets, but surface them as "ALDC-internal client contact data" in the page for awareness.
  - **CosmosDB document internal-IDs** (`c82414c8-3907-451b-a8ea-56ce3ba668d6`, `19675a6b-4c24-4f57-a967-2e815b313f1d`, `bab33d17-ee7a-4186-b761-1c5b34859cd1`). Not secrets.
- `### Runtime credentials (used when editing/publishing — not stored in repo)`
  - **Snowflake username + password / keypair** — for `.pbix` model refresh. See `[[Snowflake]]` and `[[vault]]`.
  - **Azure AD / Microsoft 365 login** — to publish to the PBI Service workspace and to refresh datasets. Per `[[powerbi-secret-refresh]]`, the PBI Service itself has per-client App Registrations (DISH_DUER / FUSION92 / GEP / KIT_ACE) with client secrets rotating on a ~6-month cadence; those secrets live in Azure + Django admin, not in this repo.
  - **CORE_API tokens** (per tool page § Report Template) — `CORE_API_CLIENT_TOKEN`, `CORE_API_ACCOUNT_ID`, `CORE_API_REPORT_ID`. Used by the template's glossary/metadata fetch logic. Stored per-model as template parameters (inside the `.pbix`), not in clone-text.
- `### Vault touchpoints`
  - No credentials to extract from this repo. `[[vault/credentials.md]]` should already document the Snowflake + Azure AD credentials via `[[powerbi-secret-refresh]]` — verify the section exists; if not, the gap is in the secret-refresh runbook, not here. Do NOT create vault entries in this session.

---

### Section 9 — `## Tech Debt & Known Issues`

**Purpose:** Consolidate every rough edge the plan surfaced. Medium-length list — the repo is small in code but has several real storage, naming, and freshness issues.

**Content (12 items, in rough priority order):**

1. **No `.pbip` migration.** Every `.pbix` is still the legacy binary format. `.pbip` (Power BI Project) unpacks `.pbix` into a folder of TMDL + JSON (the `Model/` and `Report/` subfolders). `.pbip` is diffable, grep-able, CI-friendly, and is Microsoft's current recommendation for source-controlled Power BI. **Biggest single modernisation opportunity** for this repo. Migration is per-`.pbix` — no bulk converter — but the live-model set is only ~10 files (one per active client + internal). Flag as high-value.
2. **Repo footprint ~16 GB LFS.** Will grow at GEP's 300–600 MB-per-month snapshot cadence. At current pace GEP alone will add ~5 GB/year. **No retention policy** — dated folders never pruned. Need a policy: e.g., "retain last 12 monthly snapshots per client; archive older to a `legacy/` folder or a separate `power_bi_archive` repo."
3. **DISH_DUER is ~5.5 GB and frozen since 2024-08** (client inactive). Prime candidate for archival extraction to `power_bi_archive` (new repo) to drop ~30% of this repo's size.
4. **BOOK_DEPOT frozen since 2022-11** (client inactive). Similarly archivable. Total archivable frozen content: DISH_DUER + BOOK_DEPOT + `sales/` + pre-2024 `common/` + old KIT_ACE Finance Model variants + old GEP ≤ 2025-06 = ~10 GB+.
5. **Stale `CUST-*` branches on origin** (`CUST-303`, `CUST-396`, `CUST-421`, `CUST-461`, `CUST-528`, `cust-457`). From DISH_DUER / KIT_ACE / BOOK_DEPOT era, none matching active work. Delete after a one-week notice.
6. **In-repo `templates/` is stale snapshot.** Canonical templates live in `Nextcloud\Customers\Style Guides` per tool page. The `templates/Eclipse Power BI Template 2022-*.pbix` trio hasn't been touched since 2022-06. Either prune + add a README pointer, or re-sync on template revisions. Currently neither — silent drift.
7. **Naming inconsistency in dated folders.** DISH_DUER uses `-` and `_` interchangeably; KIT_ACE uses `(YYYY-MM)`; GEP uses `YYYY_MM <type>`; FUSION_92 uses `YYYY_MM`. Document the inconsistency; don't rename (would invalidate git history).
8. **`.gitignore` is Python-boilerplate and vestigial.** Either replace with a PBI-relevant ignore list (`.pbix.bak`, PBI Desktop lock files, etc.) or delete.
9. **`KIT_ACE/Finance Model (2025-05)/` last-touched 2025-06-02.** Client is marked inactive in `entities/clients/inactive/kit-ace.md` but the model has 2025-06 activity. **Contradiction** — resolve either by marking KIT_ACE active or by noting the model is being maintained post-client-inactive. Add a `> Contradiction:` callout on the wiki page per wiki rule #6.
10. **KIT_ACE filename convention is frozen at template version** (`Finance Model DG1 2022-07.pbix` keeps "2022-07" regardless of actual last-edit). Confusing; document but don't change.
11. **`ALDC_FINANCE/` lives under `custom/` rather than `internal/`**. Inconsistent with `internal/ALDC_ENG/`. Don't move; document.
12. **`sales/APEX_BRASIL/` + `sales/9TH_CO/`** are prospect-demo artefacts for clients that don't appear in the wiki client index. Unknown if these prospects ever converted. Flag as "unknown-status prospect demos."

---

### Section 10 — `## Future home (platform consolidation)`

**Purpose:** Per boot-prompt platform-consolidation framing. Short section — Power BI is NOT expected to migrate anywhere at the platform level, but storage-location and tooling improvements are worth flagging.

**Content:**

- **Power BI as a tool is staying.** Unlike `[[eclipse]]` / `[[core_api]]` (being replaced by `[[eclipse_exp]]`) or `[[connector]]` (migrating to `[[Prefect]]`), there is no in-flight effort to replace Power BI. It remains the client-facing BI / reporting layer for the foreseeable future.
- **`.pbix` → `.pbip` migration** is the closest thing to a "consolidation" story for this repo. Would make every `.pbix`:
  - Diffable in GitHub's web UI.
  - Lintable / reviewable in CI (`[[ai-pr-workflow]]` could finally apply).
  - Cheaper to store (less LFS binary churn).
  - Collaboration-friendlier (non-overlapping text changes merge cleanly).
  - **Recommendation:** pilot on the GEP Data Model — highest-value target because GEP has the highest commit cadence and the biggest storage footprint.
- **Repo split**: Move frozen client folders (DISH_DUER, BOOK_DEPOT, old GEP, `sales/`, `internal/aldc_demo/`) to a `power_bi_archive` repo. Keeps the primary repo to only live content. Reduces LFS pull cost for new developers by ~60%.
- **Nextcloud `templates/` sync**: Either make this repo's `templates/` a mirror of the Nextcloud copy (maintained discipline) or delete it outright + replace with a README pointer. Current silent-drift state is the worst option.
- **No migration to another repo** is warranted — the Power BI artefact problem is Power-BI-specific and wouldn't be better-served inside `[[clients-repo]]` or `[[eclipse_exp]]`. Keep the repo independent.

---

### Section 11 — `## See Also`

Wikilinks. Must include:

- `[[entities/tools/power-bi|Power BI (tool)]]` — the tool page; authoritative for "how Power BI works" and connection-parameter reference. **The companion page.**
- `[[gep-snowflake-pbi-deployment]]` — full GEP deploy runbook; authoritative for production publishes.
- `[[model-deploy-production]]` — generic model deploy checklist.
- `[[powerbi-secret-refresh]]` — App Registration secret rotation runbook.
- `[[client-release-checklist]]` — pre-release checklist.
- `[[GEP]]` — primary client using this repo (most commits).
- `[[fusion92]]` — active client; `custom/FUSION_92/` owner.
- `[[kit-ace]]` — inactive client with anomalous 2025-06 activity (see Contradiction callout).
- `[[dish-duer]]` — inactive client; largest folder by storage.
- `[[book-depot]]` — inactive client; frozen since 2022-11.
- `[[Snowflake]]` — data source upstream of every `.pbix`.
- `[[SSMS]]` — intermediate SQL Server layer (GEP).
- `[[data-pipeline-flow]]` — end-to-end pipeline including PBI position.
- `[[periodicity]]` — DAX SWITCH pattern used across the models.
- `[[star-schema-convention]]` — warehouse naming that feeds the models.
- `[[cosmosdb-schema]]` — CosmosDB `report` document schema (the JSON companions here are frozen snapshots of those docs).
- `[[clients-repo]]` — warehouse SQL + Eclipse configs; upstream of PBI via `REPORT_COMMON`.
- `[[dax-media-app]]` — parent project for Fusion92 Activation Model.
- `[[dax-ai]]` — DAX AI dashboard project; Fusion92 Activation Model is the centrepiece.
- `[[deployment-groups]]` — for `internal/ALDC_ENG/Account Summary … Canada DG1.pbix` context.
- `[[azure-environments]]` — env-to-subscription mapping relevant for publish targets.
- `[[ai-pr-workflow]]` — the ALDC-wide PR workflow this repo does NOT enforce (contrast).
- `[[vault]]` — runtime credentials pointer.

Should link (softer / ticket-specific):

- `[[tickets/gep/GP-76]]`, `[[tickets/gep/GP-87]]`, `[[tickets/gep/GP-169]]` — referenced in commit messages. The execution session should link only to tickets that *actually exist* in `tickets/gep/`; omit those that don't rather than create stubs. Index.md search + `ls tickets/gep/` to confirm.
- `[[entities/repos/aldc-scripts]]`, `[[entities/repos/workflows]]`, etc. — sibling repos in the doc workstream. Link ONCE if there's a genuine relation (e.g., `ALDC_ENG` Account Summary could relate to `[[workflows]]`'s Snowflake-sync work); otherwise skip.

Do NOT link:

- `[[core_api]]` / `[[eclipse_exp]]` / `[[eclipse]]` / `[[connector]]` / `[[flight-check]]` — unrelated except at distant-pipeline level. Don't force cross-links.
- `[[claude_code_enhanced]]` / `[[prospect-site-template]]` — completely unrelated; omit.
- `[[adm]]` / `[[aspire-north]]` / `[[drop-in-gaming]]` / `[[heartland-dental]]` / `[[indochino]]` / `[[terrayn]]` — no PBI artefacts in this repo for these clients. No link needed.

---

### Judgment calls

- **Single wiki page is correct container.** Everything repo-specific fits in one page; splitting by folder would fragment the Report Catalogue (the centrepiece). Target budget **~750–950 lines**. Hard ceiling 1,100. Longer than `aldc-scripts` (smallest at ~400) and comparable to `workflows` (657) because the per-folder tables in the Report Catalogue are bulky. The cataloguing IS the point — don't cut it.
- **Binary-file problem is the dominant design constraint.** Nearly 100% of the repo by byte-count is opaque. The plan's answer: frame the wiki page around what IS knowable (structure, filenames, dates, sizes, LFS, commit authors + messages, readable JSON companions), explicitly declare what IS NOT knowable without Power BI Desktop, and heavy-link to the tool page + runbooks for anything usage-related. Do NOT attempt to unzip `.pbix` files to read M-queries or TMDL — that path is proprietary binary and will produce garbage.
- **Architecture section is SHORT and EXPLICITLY disclaims** "no code architecture — this is an artefact store." Replaces the usual multi-component architecture writeup with 3-4 paragraphs. Readers looking for "how PBI works" go to the tool page. This mirrors `aldc-scripts`'s approach of replacing Architecture with Script Catalogue — but keeps a short Architecture stub to explicitly set reader expectations (rather than omitting the heading entirely).
- **Data Flow IS included** even though short. A reader who lands on this repo page without knowing ALDC's stack needs orientation. One section with one ASCII diagram + heavy cross-reference is the right weight. Not a duplicate of the tool page — this one lists which `.pbix` in THIS repo maps to which upstream source.
- **Report Catalogue is THE centrepiece.** Per-folder tables (templates, common/Retail, custom/GEP, custom/FUSION_92, custom/DISH_DUER, custom/KIT_ACE, custom/BOOK_DEPOT, custom/ALDC_{FINANCE,SALES}, internal/, sales/). Ten tables total — if this feels too many, the split is exactly right. A single giant table would be unreadable; fewer would collapse meaningful groupings. The tables carry filename, git date, LFS size, status (current/legacy/frozen), and notes — the five columns a reader actually wants when asking "where is the current FUSION_92 model?"
- **Disambiguation is TWO separate pieces:**
  1. **Tool-vs-repo page coexistence** — like `[[cce]]` (project) vs. `[[claude_code_enhanced]]` (repo). Block-quote at the top. Different aliases. The tool page is NOT renamed.
  2. **Intra-repo ambiguities** — `custom/KIT_ACE/` vs. `sales/KIT_ACE/`; in-repo `templates/` vs. Nextcloud canonical; `custom/ALDC_FINANCE/` vs. `internal/ALDC_ENG/`. All flagged inline at the top of the Repo Layout section.
- **Kit & Ace contradiction.** Wiki client index has `kit-ace` in `entities/clients/inactive/` but `custom/KIT_ACE/Finance Model (2025-05)/` was actively maintained through 2025-06. Do NOT silently reclassify the client. Per wiki rule #6, add a `> **Contradiction:**` callout in the Report Catalogue § KIT_ACE table and flag it in Tech Debt. Resolution is for Paul to confirm; execution session does not resolve it.
- **Do NOT create new wiki stub pages.** No stubs for `APEX_BRASIL`, `9TH_CO`, or ticket pages that don't already exist in `tickets/gep/`. Just link to pages that exist.
- **Do NOT extract any credentials to vault.** Text-file scan is clean. The CosmosDB account IDs are identifiers already documented in `[[cosmosdb-schema]]`, not secrets. The `.pbix` binaries may contain connection metadata but are not decompressed here; decompression is out of scope + unsafe.
- **Do NOT modify any `.pbix`, `.pbit`, `.pbip`, `.pptx`, `.xlsx`, `.png`, or `.json` file in the repo** — read-only per boot prompt. Document as-is.
- **Ticket cross-references from commit messages:** GP-76 (`2025-04-15`), GP-87 (`2025-05-05`), GP-169 (`2026-03-06`), plus historical Fusion92 references. Execution session should `ls tickets/gep/` and link only to pages that actually exist. Do NOT create ticket stubs for missing IDs — if the ticket page doesn't exist, flag as a wiki gap in Tech Debt.
- **Git LFS notes are non-optional.** The repo is unusable without LFS. The Developer Guide's first line must establish `git lfs install` as prerequisite #1. Quote the `large file storage.txt` single-sentence content verbatim to anchor the point.
- **Per-client status classifications (Active / Legacy / Frozen / Inactive):**
  - `GEP/` — **Active** (2026-03 commit).
  - `FUSION_92/` — **Active** (2025-12 commit).
  - `KIT_ACE/` — **Ambiguous** (2025-06 commit; client marked inactive in wiki — flag as contradiction).
  - `ALDC_SALES/` — **Active** (2025-08 commit) but internal-demo scope.
  - `ALDC_FINANCE/` — **Legacy** (2024-07 last).
  - `internal/ALDC_ENG/` — **Legacy** (2024-12 last).
  - `common/Retail/` — **Stable baseline** (2024-08 last — treat as intentionally static reference set, not legacy).
  - `DISH_DUER/` — **Inactive legacy** (2024-08 last, client in `inactive/`).
  - `BOOK_DEPOT/` — **Frozen** (2022-11 last, client in `inactive/`).
  - `sales/` — **Frozen** (2022-08 last).
  - `internal/aldc_demo/` — **Frozen** (pre-2024, demo assets).
  - `templates/` — **Stale** (2022-07 last — canonical copies in Nextcloud).
- **Index.md entry wording** — match the pattern of `[[aldc-scripts]]` and other repo entries. Proposed:
  > `- [[entities/repos/power_bi|power_bi (repo)]] — Binary-artefact store for ALDC's Power BI reports. ~94 `.pbix` files + 3 `.pbit` templates + 6 CosmosDB report-JSON companions, Git LFS (~16 GB), no code. Organised `common/` (Retail starter set), `custom/<CLIENT>/` (bespoke, dated snapshots), `internal/`, `sales/` (pre-sales demos), `templates/` (stale; canonical copies in Nextcloud). Active clients: GEP (20 snapshots, 2026-03 latest), Fusion92 (13 snapshots, 2025-12 latest). Legacy: DISH_DUER, BOOK_DEPOT, KIT_ACE, ALDC_FINANCE. No CI/CD; all deploys are manual Publish from Power BI Desktop — see [[gep-snowflake-pbi-deployment]] / [[model-deploy-production]]. For Power-BI-the-tool see [[entities/tools/power-bi|Power BI (tool)]].*`
- **Page length target:** ~750–950 lines; Report Catalogue tables + Developer Guide pitfalls list are the longest content.
- **Tone:** neutral technical. No editorialising on tech-debt items beyond objective observations. Use "legacy" / "frozen" / "inactive" per the classification above, not loaded terms.
- **Naming note.** The repo is `power_bi` (underscore, lowercase) on GitHub. The wiki page slug should be `power_bi.md` to match the repo name. The page title should be `power_bi` (matches slug + repo). The tool-page slug stays `power-bi.md` (hyphenated — already exists). This deliberate slug divergence — `power_bi.md` (repo, underscore) vs `power-bi.md` (tool, hyphen) — matches the file naming on disk for each. Add a one-line explanation in the disambiguation callout.
- **Default branch is `main`** (verified via `git branch`). No `master` to worry about.
- **Cross-reference hygiene** — wikilinks above in Section 11 are categorised must / should / don't. Execution session should follow the categorisation.

### Session Log entry to add (executor should append after writing the page)

```
### 2026-04-20 — power_bi plan session complete

- did: read repo thoroughly — full directory tree (`ls -R` across common/, custom/, internal/, sales/, templates/), `.gitattributes` (single line: `*.pbix filter=lfs diff=lfs merge=lfs -text`), `.gitignore` (Python boilerplate — vestigial), `large file storage.txt` (single-sentence LFS-required notice — the repo's only in-repo documentation), all 6 text-readable JSON files (common/Retail/Customer Lifetime Value/retail_customer_lifetime_value.json — 9thco CosmosDB report doc with 1-entry glossary; common/Retail/Daily Sales/2022-06/daily_sales.json — KIT_ACE CosmosDB doc with 9-entry glossary + 20-key config dict; common/Retail/KPI Manager/2022-06/kpi_manager.json — DISH_DUER doc with 12-entry KPI glossary + CosmosDB system fields; common/Retail/Product Benchmark/2022-06/cosmos_report_template.json — 9thco Book Outlet Campaign Demo skeleton; templates/cosmos_report_template.json — same skeleton duplicated; templates/theme.json — 7-line PBI SlicerTemplate theme with DIN Light font). Ran `git log --all` (353 commits, 2022-03 → 2026-03-06, 7 unique authors: aldc-karenprete, aldc-stevendeutekom, aldc-braydenmarshall, aldc-mustafapaigeer, aldc-seanogrady, Marshall Johnston, Paul Russell). Ran `git lfs ls-files --size` (94 LFS objects, ~16 GB total; largest: DISH_DUER combined_model_2024_06 at 591 MB, ALDC_SALES Netsuite Ops Model at 543 MB, GEP 2025_07 at 639 MB). Ran per-folder last-commit-date analysis (GEP 2026-03, FUSION_92 2025-12, ALDC_SALES 2025-08, KIT_ACE 2025-06, internal/ 2024-12, DISH_DUER 2024-08, ALDC_FINANCE 2024-07, common/ 2024-08, BOOK_DEPOT 2022-11, sales/ 2022-08, templates/ 2022-06). `git branch -a`: main + 6 stale CUST-* branches. Credential scan: clean (no hook URLs, no API keys, no AWS keys, no Anthropic keys in the 9 text files). Cross-read wiki: CLAUDE.md, entities/tools/power-bi.md (129 lines), existing repo pages (aldc-scripts, eclipse_exp, workflows, custom-fusion-92-audience-api, claude_code_enhanced, prospect-site-template), entities/clients/ (GEP, fusion92 active; adm, aspire-north, book-depot, dish-duer, drop-in-gaming, heartland-dental, indochino, kit-ace, terrayn inactive), processes/deployment/{model-deploy-production, gep-snowflake-pbi-deployment, client-release-checklist}.md, processes/operations/powerbi-secret-refresh.md, concepts/architecture/data-pipeline-flow.md (referenced), index.md.
- produced: 11-section plan for new wiki page `entities/repos/power_bi.md` — Intro (identity + two disambiguations: tool-page vs repo-page coexistence, intra-repo ambiguities), Repo layout (full tree + conventions), Architecture (short stub explicitly declaring "no code architecture — binary artefact store"), Data Flow (short orientation + one ASCII diagram + cross-ref to tool page for detail), **Report Catalogue** (centrepiece — 10 per-folder tables: templates/, common/Retail/, custom/GEP/, custom/FUSION_92/, custom/DISH_DUER/, custom/KIT_ACE/, custom/BOOK_DEPOT/, custom/ALDC_{FINANCE,SALES}/, internal/, sales/; every `.pbix` with filename + last-commit-date + LFS size + status + notes), Developer Guide (prereqs incl. Git LFS + selective-fetch pattern + PBI Desktop Windows-only, clone workflow, edit workflow, publish workflow, 12 common pitfalls), Deployment (short — no CI/CD, link to runbooks, rollback = open older file + Publish), Security & Credentials (scan-clean, CosmosDB account IDs are not secrets, `.pbix` binaries opaque + not to be unzipped, runtime creds summary), Tech Debt (12 items incl. .pbip migration, ~16 GB footprint + no retention, archival candidates, stale branches, stale templates/), Future home (no platform migration — PBI stays; .pbip migration + repo split are the improvements), See Also (must/should/don't categorised).
- decided: single wiki page (~750–950 lines) with Report Catalogue as centrepiece; Architecture section present but short (explicit "no code architecture" disclaimer to set reader expectations, mirrors aldc-scripts pattern); Data Flow applicable but compressed with heavy cross-ref to tool page; two-piece disambiguation (tool-page vs repo-page block-quote at top like cce/claude_code_enhanced coexistence + intra-repo ambiguities inline); do NOT attempt to unzip `.pbix` files for M-query extraction (proprietary binary, unsafe); do NOT extract any credentials (scan is clean); do NOT modify any file in the repo; do NOT create stub pages for unknown prospects (APEX_BRASIL, 9TH_CO) or missing ticket pages; add `> Contradiction:` callout for KIT_ACE (wiki-inactive but 2025-06 repo activity) per wiki rule #6; frontmatter aliases do NOT include "Power BI" or "PBI" (reserved for the tool page); slug divergence power_bi.md (repo, underscore) vs power-bi.md (tool, hyphen) is intentional and matches the file naming on each target; no automated gates in the repo (no `.github/workflows/`, no tests) noted as conventional for binary-artefact repo — does NOT warrant [[ai-pr-workflow]] integration until .pbip migration provides text artefacts. Status classifications per folder: GEP Active, FUSION_92 Active, ALDC_SALES Active (internal demo), KIT_ACE Ambiguous, ALDC_FINANCE Legacy, internal/ALDC_ENG/ Legacy, common/Retail/ Stable baseline, DISH_DUER Inactive legacy, BOOK_DEPOT Frozen, sales/ Frozen, internal/aldc_demo/ Frozen, templates/ Stale.
- flagged: (1) no `.pbip` migration — biggest modernisation opportunity; (2) repo at ~16 GB LFS with no retention policy + GEP growing 300–600 MB/month; (3) DISH_DUER ~5.5 GB frozen since 2024-08 (client inactive) — archival candidate; (4) BOOK_DEPOT frozen since 2022-11 — archival candidate; (5) 6 stale `CUST-*` branches on origin (DISH_DUER / KIT_ACE / BOOK_DEPOT era); (6) `templates/` in-repo stale since 2022-07 — canonical copies in Nextcloud; silent drift; (7) naming inconsistency in dated folders (hyphen vs underscore, parentheses, space-separated); (8) `.gitignore` is vestigial Python boilerplate; (9) **KIT_ACE contradiction** — wiki marks client inactive, but `custom/KIT_ACE/Finance Model (2025-05)/` was touched 2025-06-02 — needs Paul to resolve; (10) KIT_ACE filename convention frozen at "DG1 2022-07" template-version stamp regardless of last-edit date; (11) `ALDC_FINANCE/` under `custom/` rather than `internal/` — inconsistent with `ALDC_ENG/`; (12) `sales/APEX_BRASIL/` + `sales/9TH_CO/` are prospect-demos for clients not in wiki index — unknown-status prospects. No credentials to extract. Commit-message references to GP-76, GP-87, GP-169 (and other Jira IDs) — execution session to cross-link only to ticket pages that already exist in `tickets/gep/`.
- next: execution session (Sonnet) — (1) create `entities/repos/power_bi.md` (~750–950 lines) per this plan; (2) add index.md entry under Entities › Repos with the exact blurb proposed in Judgment calls (aliased link form `[[entities/repos/power_bi|power_bi (repo)]]` to coexist with `[[Power BI]]` tool alias); (3) add `> Contradiction:` callout for KIT_ACE active-model vs wiki-inactive-client mismatch in Report Catalogue § KIT_ACE table; (4) verify Jira ticket pages exist before linking (ls `tickets/gep/`) — link only to existing ones, flag missing in Tech Debt; (5) mark Execution ✅ in this tracker row 9; (6) append to log.md. No source-code edits, no vault touches, no stub page creation, no `.pbix` unzipping.
```

---

## Workstream complete

### 2026-04-20 — Integration session complete (Opus) — **WORKSTREAM DONE**

- did: read all 9 new repo pages (`eclipse_exp`, `eclipse`, `flight-check`, `custom-fusion-92-audience-api`, `claude_code_enhanced`, `workflows`, `prospect-site-template`, `aldc-scripts`, `power_bi`) plus the 3 pre-existing integration-critical pages (`core_api`, `connector`, `clients-repo`) and the anchor page `data-pipeline-flow`. Cross-referenced against the 9-repo tracker's approved plans. Built a correct cross-repo mental model before writing.
- produced: `concepts/architecture/repo-integration-map.md` (541 lines). Contents: strategic narrative (eclipse_exp consolidation + Prefect migration + what's NOT being consolidated), 12-repo summary table with tier/current-role/future-state/migration-trigger columns, 3 Mermaid diagrams (current data flow split into 1a core pipeline + 1b DAX Media App stack; current dependency graph; target-state strangler-fig overlay with dashed absorbing-arrows and dotted Prefect-migration arrows), per-repo integration notes (12 blocks), isolated-repos section (claude_code_enhanced, aldc-scripts, power_bi repo, and prospect-site-template-today-but-not-forever), integration tiers explainer, stale-references-to-verify appendix (11 items — forward-looking eclipse_exp webhook not-yet-wired, eclipse.analyticlabs.io vs eclipse.aldc.io parallel deployments, core_api v2 PATCH gap, connector-instance-function-app-vs-Eclipse-instance confusion, committed .env in workflows, aldc-scripts cost-monitoring-likely-dead, KIT_ACE repo-vs-wiki consistency, workflows Prefect speculation, two TODOs in flight-check page, ECLIPSE_URL env gap), see-also. Added `[[repo-integration-map]]` to `index.md` under `Concepts › Architecture`.
- decided: (1) cover 12 repos not 9 — `core_api`, `connector`, `clients-repo` are integration-critical even though not in the queue; (2) 4 Mermaid diagrams instead of a single blob (core pipeline + DAX stack split avoids unreadable density; dependency graph separate from data flow; strangler-fig overlay separate from current-state); (3) dashed arrows for planned absorption, dotted (`==>`) for Prefect migration — visually distinct from solid current-state arrows; (4) stale-references appendix is the right home for forward-looking-but-not-wired claims rather than caveating each mention inline; (5) isolated-repos section is short and honest (4 repos including prospect-site-template's "isolated today, integrated tomorrow" state); (6) integration-tiers section is a discrete block, not embedded in the summary table, so the table stays readable; (7) per-repo notes are one compact block each (~15 lines), not exhaustive — the repo pages are already deep; (8) target-state diagram uses trigger-boxes connected to nodes via dashed arrows to make "what has to happen first" visually explicit.
- flagged: 11 stale-references to reconcile on a future cleanup pass — most important being (a) eclipse_exp's `/api/v1/onboarding/webhooks/prospect-created` webhook is documented but not wired; `build.prospect.aldc.io` status is unknown; (b) `eclipse.md` current-state staleness (Next 15 App Router rewrite lives at `eclipse.analyticlabs.io` parallel to the Next 14 Pages Router at `eclipse.aldc.io` — multiple downstream pages mix references); (c) core_api v2 PATCH gap for `application_metadata` (DV-444); (d) the `aldcprodfnapcore1c03` (connector instance) vs `aldcprodfnapcore1c01` (Eclipse instance) confusion should get mirrored callouts on both pages; (e) `aldc-scripts` live status needs `crontab -l` verification on Server4 before anyone invests in migrating its cost-monitoring scripts.
- next: **Workstream closed.** Tracker moves to archive on next lint. Paul to review the map before it becomes canonical — in particular the target-state diagram's trigger boxes (are they accurate?), and the stale-references appendix (which of the 11 items are worth addressing now vs deferring?).
