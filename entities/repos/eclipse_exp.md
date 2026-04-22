---
tags: [entity, repo, eclipse-exp, platform, fastapi, nextjs, multi-tenant]
aliases: [Eclipse EXP, eclipse-exp, eclipse_exp API, ALDC next-gen platform]
sources: [repos/eclipse_exp/README.md, repos/eclipse_exp/CLAUDE.md, repos/eclipse_exp/docs/ARCHITECTURE.md, repos/eclipse_exp/docs/DEPLOYMENT.md, repos/eclipse_exp/docs/TARGET_ARCHITECTURE.md, repos/eclipse_exp/docs/MIGRATION_STRATEGY.md, repos/eclipse_exp/docs/PRINCIPLES.md, repos/eclipse_exp/docs/RUNBOOK.md, repos/eclipse_exp/docs/SECURITY.md, repos/eclipse_exp/docs/API_GUIDE.md, repos/eclipse_exp/docs/ONBOARDING.md, repos/eclipse_exp/app.py, repos/eclipse_exp/Dockerfile, repos/eclipse_exp/supervisord.conf, repos/eclipse_exp/.github/workflows/deploy.yml]
created: 2026-04-20
updated: 2026-04-20
---

# eclipse_exp

Contract-first, AI-native multi-tenant data platform. Lives at `C:\Users\PaulRussell\repos\eclipse_exp`. Deployed at `https://eclipse-exp.aldc.io`. This is ALDC's next-generation platform — the successor to the [[Eclipse]] Next.js UI + [[core_api]] pair — running in parallel via a strangler-fig migration (not a replacement). It is distinct from the legacy [[Eclipse]] repo (current web UI): eclipse_exp bundles a **FastAPI backend AND a Next.js 15 frontend into a single Docker image** managed by supervisord, a deliberate deployment-simplicity choice absent from the legacy split-repo model. Scale: 36 route modules, 87 SQL migrations, 50 connector types, 67 RLS-enabled tables, 3,848 backend + 388 frontend tests.

## Architecture

### Repository layout

| Path | Purpose |
|------|---------|
| `app.py` | FastAPI entry point — middleware stack, lifespan, route registration |
| `auth/` | JWT + API-key authentication, `auth_middleware` tenant resolution |
| `core/config.py` | Pydantic Settings — fails at startup on missing or invalid env vars |
| `core/logging.py` | structlog JSON + asgi-correlation-id per-request IDs |
| `core/rate_limit.py` | slowapi limiter instance |
| `core/worker.py` | `WorkQueueRunner` — `SELECT … FOR UPDATE SKIP LOCKED` task dispatch |
| `core/secrets.py` | Fernet encryption + optional Azure Key Vault backend |
| `core/observability.py` | Prometheus metrics + OpenTelemetry trace setup |
| `core/routes/` | 36 API route modules |
| `core/services/` | Business logic (business_context, semantic_layer) |
| `core/governance/` | Contract governance engine — drift detection, validation |
| `core/rbac/` | 6-role RBAC implementation (20 permissions) |
| `connectors/` | 50 connector types across `rest/`, `odbc/`, `custom/`, `file/`, `odata/` |
| `connectors/base/v2/` | `BaseConnectorV2`, `ConnectorConfig`, `ConnectorResponse`, `DataContract` |
| `api/` | API-level helpers and shared route utilities |
| `onboarding/` | 6-step tenant provisioning orchestrator |
| `agents/` | AI agents (discovery, config_gen, provisioning, activation) |
| `dashboards/` | Dashboard generator, branding, template library |
| `migration/` | Strangler-fig migration machinery (dual-write, cutover, sync) |
| `db/` | asyncpg pool creation with retry + `tenant_connection()` |
| `ingestion/` | Bronze-layer data ingestion pipeline |
| `pipeline/` | Alerting, quality gates, data quality runner |
| `orchestration/` | Cross-pipeline orchestration helpers |
| `contracts/` | Contract definitions, compatibility checks, generator |
| `clients/` | API clients for external services (`zeus_memory.py`, etc.) |
| `sdk/` | Client-facing SDK |
| `dbt/` | dbt models — `staging/`, `intermediate/`, `gold/`, `semantic/` |
| `frontend/` | Next.js 15, `basePath=/internal`, Mantine 8, NextAuth 4, React Query 5 |
| `migrations/` | 87 SQL migration files (numbered, with duplicates — see § Database Schema) |
| `scripts/` | `auto_migrate.py` and other operational scripts |
| `tools/` | Internal CLI tools |
| `ops/` | `alert-rules.yml`, `grafana-dashboard.json` |
| `tests/` | pytest-asyncio test suite |
| `docs/` | ARCHITECTURE.md, DEPLOYMENT.md, SECURITY.md, RUNBOOK.md, etc. |

### Tech stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Backend runtime | Python 3.12, FastAPI ≥0.115 | `Dockerfile` uses `python:3.12-slim` |
| ASGI server | gunicorn + uvicorn workers | 2 workers, 120s timeout (`supervisord.conf`) |
| Database driver | asyncpg ≥0.29 | Pool: min 2, max 10 connections |
| Config | pydantic-settings | Fails at startup on missing required vars |
| Rate limiting | slowapi | 100/min default, 30/min auth endpoints |
| Structured logging | structlog + asgi-correlation-id | JSON output, `correlation_id` on every request |
| Observability | OpenTelemetry (OTLP) + prometheus-fastapi-instrumentator | OTLP enabled when `OTEL_EXPORTER_OTLP_ENDPOINT` set |
| Encryption | cryptography (Fernet) + optional Azure Key Vault | `enc:v1:` prefix on encrypted values |
| Auth | PyJWT (HS256) + MSAL | 1h token expiry; API-key alternative via `X-API-Key` |
| AI | Anthropic SDK | Onboarding chat + AI chat SSE streaming |
| Data (in-process) | pandas, pyarrow, duckdb | DuckDB locally for Gold/semantic reads |
| dbt | dbt-core, DuckDB adapter (dev) / Snowflake adapter (prod) | Staging → intermediate → gold → semantic models |
| Frontend | Next.js 15, `basePath=/internal` | Mantine 8, NextAuth 4, React Query 5, Sentry |
| Process manager | supervisord | Gunicorn on :8080, Next.js node on :3000 |
| Legacy migration | Azure Cosmos SDK | Lazy-loaded; required only for tenant cutover |

### How a request flows

Requests enter gunicorn → FastAPI → middleware stack → route handler → DB → response.

Middleware order (from `app.py`):

1. **`SlowAPIMiddleware`** — rate limits. 100/min default; 30/min for `/api/v1/auth/*`. Raises 429 on breach.
2. **`CorrelationIdMiddleware`** — assigns a UUID `correlation_id` to every request via `asgi-correlation-id`. Propagates in logs and response header.
3. **CORS middleware** — origins from `CORS_ORIGINS` env var. Wildcard (`*`) only when `ENVIRONMENT=development`.
4. **`security_headers_middleware`** — adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, and `Strict-Transport-Security` (non-dev only).
5. **Prometheus auto-instrumentation** — records HTTP metrics at `/metrics`.
6. **`auth_middleware`** — resolves tenant from Bearer JWT or `X-API-Key` header. Public paths bypass auth: `/ping`, `/health`, `/docs`, `/api/v1/auth/*`, `/internal/*`, OAuth callbacks, and the tasks WebSocket endpoint.
7. **Route handler** — acquires DB connection via `tenant_connection(pool, tenant_id)` which issues `SET LOCAL app.tenant_id = $1` inside a transaction. PostgreSQL RLS takes effect automatically from this point.

### Key abstractions

**`Settings` (pydantic-settings, `core/config.py`)** — Single-ton loaded once. Validates `DATABASE_URL` (required) and `ECLIPSE_EXP_JWT_SECRET` (required, min 32 chars — rejects shorter values at startup). All optional vars have safe defaults. Full env var reference in § Developer Guide.

**asyncpg pool + `tenant_connection()` (`db/pool.py`)** — Pool init sets `search_path` to `eclipse_exp, public` on every acquired connection. `tenant_connection(pool, tenant_id)` is an async context manager that wraps each handler in a transaction and issues `SET LOCAL app.tenant_id = $1`. Pool creation retries with exponential backoff (1s / 2s / 4s). Defaults: min 2, max 10 connections, 60s command timeout, 300s max inactive lifetime. A bad pool creation fails after 3 attempts and crashes startup.

**`WorkQueueRunner` (`core/worker.py`)** — Polls the `work_queue` table using `SELECT … FOR UPDATE SKIP LOCKED` so multiple replicas don't double-process jobs. `register_all()` wires task-type → handler: `ingestion`, `ingestion_v2`, `activation`, `cutover`, `dashboard_gen`. Sends an immediate Slack alert on job failure via `pipeline.alerting.send_immediate_failure_alert`.

**Background schedulers** (all started in `app.py` lifespan, gated by `SCHEDULER_ENABLED`):
- `ConnectorScheduler` — polls `work_templates` on cron every `SCHEDULER_POLL_INTERVAL` seconds (default 60), enqueues matched jobs.
- `WorkflowScheduler` — schedules workflow-type jobs.
- `TaskNotifier` — sends daily 6 AM ET Slack DMs.
- `PipelineAlertScheduler` — evaluates pipeline alert rules in the background.

Set `SCHEDULER_ENABLED=false` in `.env` to suppress all four during development.

**Auto-migration on startup (`scripts/auto_migrate.py`)** — Called inside FastAPI `lifespan` before the pool opens to traffic. Applies any pending `migrations/*.sql` files in numeric order, then runs a hard-coded set of `ALTER TABLE IF NOT EXISTS` safety patches for known skipped migrations. **Non-obvious:** migrations run in-process at every cold start, not in a separate CI step. A bad migration blocks startup — inspect the log for the exact SQL that failed.

**`BaseConnectorV2` (`connectors/base/v2/base.py`)** — Contract-first V2 connector pattern. Paired with `ConnectorConfig` (Pydantic), `ConnectorResponse` (DataFrame + metadata), and `DataContract` (columns/PKs/quality rules). 50 connectors split across `rest/` (24), `odbc/` (9), `file/` (2), `custom/` (10), plus OData. Legacy V1 classes (`BaseConnector`, `BaseConnectorFlat`, `BaseConnectorOdbc`) remain for older connectors. `task_type=ingestion` runs V1; `task_type=ingestion_v2` runs the Bronze-layer V2 pipeline. See [[connector-development-standards]].

**`TenantCutover` / `DualWriteConfig` (`migration/`)** — Strangler-fig migration machinery. Lets a tenant dual-write to Cosmos + Postgres, then cut over when verified. Requires `COSMOS_CONNECTION_STRING`. Registered as `task_type=cutover` in the work queue.

**Reverse proxy to Next.js (`app.py:575–630`)** — `/internal/{path:path}` is proxied to `$ECLIPSE_FRONTEND_URL` (defaults to `http://localhost:3000`). Preserves multi-`Set-Cookie` headers for NextAuth. Rewrites absolute `Location` headers through the proxy. This is how a single `eclipse-exp.aldc.io` origin serves both the API (`/api/v1/*`) and the UI (`/internal/*`). Note: `ECLIPSE_FRONTEND_URL` is read directly from the environment in `app.py` — it is **not** in `core/config.py`.

### API surface

Core registered prefixes (from `app.py`):

| Prefix | Purpose |
|--------|---------|
| `/api/v1/auth` | JWT login, token refresh, API key management |
| `/api/v1/accounts` | Tenant account CRUD |
| `/api/v1/datasets` | Dataset registration and metadata |
| `/api/v1/dashboards` | Dashboard CRUD and AI generation |
| `/api/v1/visuals` | Visual component management |
| `/api/v1/data-views` | Filtered data view definitions |
| `/api/v1/rbac` | Roles, permissions, assignments |
| `/api/v1/users` | User management |
| `/api/v1/config` | Tenant configuration |
| `/api/v1/catalog` | Data catalog |
| `/api/v1/prospect-data` | Metrics, funnel, trends, sources |
| `/api/v1/governance` | Contract validation and drift detection |
| `/api/v1/onboarding` | Enterprise provisioning pipeline |
| `/api/v1/self-service` | Self-service onboarding |
| `/api/v1/admin` | Admin-only cross-tenant endpoints |
| `/api/v1/pipeline` | Pipeline management |
| `/api/v1/portal` | Portal data access |
| `/api/v1/ops` | Operational endpoints |
| `/api/v1/filter-metadata` | Filter metadata for UI |
| `/api/v1/integrations` | QBO/TSheets OAuth integrations |
| `/api/v1/tasks` | Kanban task management |
| `/api/v1/tasks/ws` | Kanban WebSocket (auth via query token) |
| `/api/v1/profitability` | Profitability module |
| `/api/v1/business-context` | Business context management |
| `/api/v1/monitors` | Data monitoring |
| `/api/v1/workflows` | Workflow definitions |
| `/api/v1/apps` | App registry / marketplace |
| `/api/v1/connectors/health` | Connector health monitoring |
| `/api/v1/connectors/catalog` | LLM-discoverable connector metadata |
| `/api/v1/flight-checks` | FlightCheck EXP (Fusion92 parallel build) |
| `/api/v1/onboarding-chat` | SSE — AI-driven onboarding chat |
| `/api/v1/ai-chat` | SSE — Claude tenant-aware chat |
| `/api/v1/strategy` | Strategy management |
| `/api/v1/meetings` | Meeting management |
| `/api/v1/management_meetings` | Owner-model meetings (Lori/Marshall/Mike) |
| `/api/v1/sred` | SR&ED tracker |
| `/api/v1/marketing` | Marketing module |
| `/api/v1/strat-map` | Strategy map |
| `/api/v1/health` | Zeus Memory perf dashboard |
| `/api/v1/campaigns` | Graph API email-parsed campaigns |
| `/api/v1/migration` | Legacy Eclipse migration tools |
| `/api/v1/dataViews`, `/signUp`, `/passwordReset` | camelCase compat aliases for legacy Eclipse frontend (`include_in_schema=False`) |
| `/ping`, `/health`, `/metrics` | Liveness, readiness, Prometheus |

### Design decisions worth calling out

**Contract-first** — Contracts in `contracts/` (compatibility, generator, schema) are the source of truth. The governance engine (`core/governance/`) validates schema changes against contracts before they reach data consumers. See `docs/PRINCIPLES.md`.

**RLS from day one** — Every tenant table uses `NULLIF(current_setting('app.tenant_id', true), '') IS NULL OR tenant_id = …::uuid`. Admin endpoints bypass RLS by never setting the GUC. Established in `migrations/019_rls_security.sql`, hardened in `021_rls_safe_tenant_check.sql`, `068_multi_tenant_hardening.sql`, and `078_force_rls_eclipse_app_tables.sql`.

**No `from __future__ import annotations` in route files** — breaks slowapi/FastAPI parameter detection (`CLAUDE.md`). This is a foot-gun: it works in most Python files but silently breaks rate-limit decorators and dependency injection in route modules.

**Single-container unified deployment** — one Docker image runs gunicorn + node via supervisord. Frontend and backend always ship together. Rationale: one CI/CD pipeline, one Azure Container App, one DNS, simpler revision rollback.

**Strangler-fig migration** — legacy Eclipse stays on NextAuth + Cosmos DB; eclipse_exp runs alongside on JWT + Postgres + RLS. Clients migrate via feature flag / DNS redirect. See `docs/MIGRATION_STRATEGY.md`.

**Dual query-engine target** — DuckDB locally, Snowflake in prod for Gold/semantic-layer reads. PostgreSQL is the primary store in all environments.

---

## Data Flow

### Source → Bronze → Silver → Gold → Dashboard

The ten-step platform pipeline (from `docs/ARCHITECTURE.md`):

1. **`Connector.fetch()`** — connector pulls from the external source (API, ODBC, file).
2. **`ConnectorResponse`** — typed DataFrame + metadata returned by the connector.
3. **`DataContract.assert()`** — validates column presence, types, PK constraints, and custom quality rules against the contract definition.
4. **`BronzeWriter`** — writes immutable Parquet to `{tenant}/{connector}/{table}/{timestamp}/data.parquet`. Adds three columns: `_aldc_ingested_at`, `_aldc_source_hash`, `_aldc_tenant_id`. Storage root: `BRONZE_STORAGE_ROOT=/tmp/eclipse_exp/bronze/` (backend: `local`; ADLS is a planned future target).
5. **`SchemaRegistry`** — detects schema drift between runs (new columns, removed columns, type changes).
6. **`QualityGateRunner`** — enforces PK non-null, uniqueness, and any custom quality rules defined in the contract.
7. **dbt staging (Silver)** — `dbt/models/staging/` transforms Bronze Parquet into cleaned Silver tables in PostgreSQL.
8. **`DimensionalModel` (Gold)** — `dbt/models/gold/` builds fact + dimension tables per the ALDC [[star-schema-convention]].
9. **`SemanticLayerService`** — `dbt/models/semantic/` exposes business metrics over Gold tables.
10. **Dashboard API** — `dashboards/generator.py` renders dashboards from the semantic layer. See § Onboarding Pipeline for AI-heuristic layout.

Cross-references: [[data-pipeline-flow]], [[star-schema-convention]], [[accumulating-source-tables]].

### Ingestion triggers

Three paths enqueue ingestion jobs:

1. **Scheduled** — `ConnectorScheduler` polls `work_templates` every `SCHEDULER_POLL_INTERVAL` seconds (default 60). Enqueues a `work_queue` job when a cron expression matches.
2. **Queued** — any process writes directly to `work_queue`; `WorkQueueRunner` picks it up via `SELECT FOR UPDATE SKIP LOCKED`.
3. **Onboarding-triggered** — the provisioning agent queues `activation` + initial `ingestion_v2` jobs after a new tenant is created.

### Storage

Bronze Parquet on local disk (`BRONZE_STORAGE_ROOT`). Silver and Gold in PostgreSQL schema `eclipse_exp`. dbt models in `dbt/models/{staging,intermediate,gold,semantic}/`.

### Dashboard generation

`dashboards/generator.py` + `dashboards/branding.py` + `dashboards/template_library.py`. Layout is AI-heuristic — Claude infers a dashboard layout from the dataset definition and tenant brand colors. Nine business-type templates drive the KPI selection (see § Onboarding Pipeline).

### Out-of-band data paths

| Path | Mechanism | Notes |
|------|-----------|-------|
| `/api/v1/onboarding-chat` | SSE | Claude responses during AI-driven prospect onboarding |
| `/api/v1/ai-chat` | SSE | Tenant-aware Claude chat |
| `/api/v1/tasks/ws` | WebSocket | Real-time kanban; auth via query token, not JWT header |
| `/metrics` | Prometheus scrape | HTTP metrics + custom gauges/counters |
| `audit_logs` table | Fire-and-forget async | Written by `audit_write()` on 62+ write endpoints across 16 route modules |
| Slack | HTTP webhook | Immediate failure alerts from `WorkQueueRunner`; daily 6 AM ET digest from `TaskNotifier` |

---

## Developer Guide

### Prerequisites

- Python 3.12 (mypy config pins `python_version = "3.12"`; Dockerfile uses `python:3.12-slim`)
- Node.js ≥22.0.0 (from `frontend/package.json` engines field)
- PostgreSQL 16 with pgvector extension (`030_vector_embeddings.sql` requires it — use `pgvector/pgvector:pg16`, not vanilla `postgres:16`)
- Docker + Docker Compose (optional, but recommended for full-stack local)

### Environment variables

Canonical schema is `core/config.py` (`Settings` class). All vars read from `.env` via pydantic-settings.

**Required:**

| Variable | Constraint |
|----------|-----------|
| `DATABASE_URL` | Any valid asyncpg connection string |
| `ECLIPSE_EXP_JWT_SECRET` | Min 32 characters — app refuses to start if shorter |

**Key generation commands** (from `docs/DEPLOYMENT.md`):
```bash
# JWT secret
python3 -c "import secrets; print(secrets.token_hex(32))"
# Fernet encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Common optional vars:**

| Variable | Default | Notes |
|----------|---------|-------|
| `ENVIRONMENT` | `production` | Use `development` for wildcard CORS |
| `CORS_ORIGINS` | `https://eclipse.analyticlabs.io,...` | Comma-separated list |
| `ENCRYPTION_KEY` | `""` | Fernet key for connector secrets |
| `AZURE_KEY_VAULT_URL` | `""` | Optional KV backend for secrets |
| `ECLIPSE_API_URL` | `""` | Inbound webhook URL from prospect-builder |
| `ECLIPSE_FRONTEND_URL` | `http://localhost:3000` | Reverse-proxy target for `/internal/*`. **Note:** read directly from env in `app.py`, not in `Settings` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `""` | Enables OpenTelemetry export when set |
| `ANTHROPIC_API_KEY` | `""` | Enables AI onboarding chat + AI chat |
| `ZEUS_API_URL` | `https://zeus.aldc.io` | [[zeus-memory]] integration |
| `ZEUS_ALDC_API_KEY` | `""` | Auth key for Zeus API |
| `COSMOS_CONNECTION_STRING` | `""` | Required for tenant cutover (migration only) |
| `SCHEDULER_ENABLED` | `true` | Set `false` to skip all four schedulers during dev |
| `SCHEDULER_POLL_INTERVAL` | `60` | Seconds between scheduler ticks |
| `BRONZE_STORAGE_ROOT` | `/tmp/eclipse_exp/bronze/` | Local Bronze Parquet path |
| `BRONZE_STORAGE_BACKEND` | `local` | Future: `adls` |
| `RATE_LIMIT_DEFAULT` | `100/minute` | Global API rate limit |
| `RATE_LIMIT_AUTH` | `30/minute` | Auth endpoint rate limit |
| `PBI_*` / `POWERBI_*` | `""` | Per-workspace Power BI service principals |

### Local setup — backend only

```bash
git clone <repo> && cd eclipse_exp

# 1. Create venv
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Pin install (must be first — azure beta package has no pip-resolvable deps)
pip install azure-mgmt-resourcehealth==1.0.0b6

# 3. Full dependencies
pip install -r requirements.txt

# 4. Start Postgres 16 with pgvector
docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg16

# 5. Create .env
cat > .env <<EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
ECLIPSE_EXP_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ENVIRONMENT=development
SCHEDULER_ENABLED=false
EOF

# 6. Start (migrations auto-apply on first boot)
python -m uvicorn app:app --reload --port 8080

# 7. Smoke test
curl http://localhost:8080/ping
# → {"status":"ok","service":"eclipse_exp"}
```

Swagger UI (with Bearer auth button): `http://localhost:8080/docs`.

### Local setup — frontend only

```bash
cd frontend && npm ci
npm run dev       # Next.js dev server on :3000
```

In development, Next.js proxies `/api/v1/*` to `http://127.0.0.1:8081/api/v1/*` (`next.config.mjs`). Run the backend on port **8081** (not 8080) if you want both running simultaneously and Next to forward correctly.

Lint gate before committing: `npm run lint:check` (strict: `--max-warnings=0`) AND `npm run format:check`.

### Local setup — full stack via Docker Compose

```bash
cp .env.example .env   # fill in values per core/config.py + docs/DEPLOYMENT.md
docker-compose up --build
```

App at `http://localhost:8080`. `docker-compose.yml` ships the api service only — pair with a Postgres container or point `DATABASE_URL` at your host's Postgres.

### Running tests

```bash
# Backend (integration tests auto-skip without DATABASE_URL)
pytest

# Backend with DB
DATABASE_URL=postgresql://... pytest

# Verify test count before opening a PR (must only go up)
python3 -m pytest --collect-only -q 2>&1 | tail -3
# Baseline: 3,848 backend tests

# Frontend
cd frontend && npm test
# Baseline: 388 frontend tests
```

**Key fixtures** (root `conftest.py`): `mock_pool`, `mock_conn`, `auth_token(role="owner")`, `auth_headers(role="owner")`.  
**Tenant patching idiom**: `@patch("core.routes.<module>.tenant_connection")`.

`pytest.ini` sets `asyncio_mode=auto`; all async tests work without `@pytest.mark.asyncio`.

### Debugging

**Structured logs** — JSON via structlog. Filter by `correlation_id`:
```bash
cat logs.json | jq 'select(.correlation_id == "<id>")'
```

**Per-tenant filter**:
```bash
jq 'select(.tenant_id == "<tenant-uuid>")' logs.json
```

**Slow requests**:
```bash
jq 'select(.duration_ms > 5000)' logs.json
```

**Pool exhaustion** — `eclipse_db_pool_size` gauge (labels `state=free|used`). When `used==max_size` the pool is exhausted. Recovery: `SELECT * FROM pg_stat_activity WHERE state='active'`; `SELECT pg_terminate_backend(<pid>)` on the offender; restart container if persistent. Full runbook at `docs/RUNBOOK.md`.

**Custom metrics**: `eclipse_onboarding_duration_seconds` (histogram), `eclipse_connector_runs_total` (counter).

### Common pitfalls

| Pitfall | Detail |
|---------|--------|
| `from __future__ import annotations` in route files | Silently breaks slowapi rate-limit decorators and FastAPI parameter detection. Never add to new route modules. |
| Frontend `basePath=/internal` | Use `/tasks` not `/internal/tasks` in links — Next.js auto-prepends `basePath`. Hardcoding causes `/internal/internal/tasks`. |
| API proxy `redirect:"manual"` | Required to preserve the Authorization header through FastAPI 307 redirects. |
| Short JWT secret | App exits at startup: `JWT secret must be at least 32 characters`. |
| Pool creation fails fast | Pool retries 3× with 1s/2s/4s backoff then exits. Start Postgres before the app. |
| Migration auto-apply blocks startup | A bad migration prevents the app from opening traffic. Check logs for the exact failed SQL statement. |
| pgvector required locally | Use `pgvector/pgvector:pg16`, not vanilla `postgres:16`. |
| No emoji flags in the frontend | Render country codes — emoji flags render inconsistently across Linux/Windows fonts. |
| `useSearchParams()` in Next.js | Requires a Suspense boundary — relevant when upgrading from Next.js 15. |

---

## Deployment

### Infra at a glance

| Resource | Value |
|----------|-------|
| Resource group | `rg-zeus-memory-dev` |
| Container App | `eclipse-exp-api` |
| ACR | `acrzeusmemorydev.azurecr.io` |
| Container Apps Environment | `cae-zeus-memory-dev` |
| Public URL | `https://eclipse-exp.aldc.io` |
| DB host | Azure Database for PostgreSQL (name in vault) |
| Runtime base image | `python:3.12-slim`, Node 22 installed, Next.js standalone copied from builder stage |

Cross-references: [[azure-environments]], [[deployment-groups]], [[aldc-naming-convention]].

### Environment model

Single production environment: the `eclipse-exp-api` Container App. There is **no separate staging Container App**. Staging traffic rides on prior Container App revisions — this is materially different from legacy Eclipse, which uses paired staging/production slots (see [[eclipse-azure-deployment]]). For non-trivial changes, test against a previous revision using the `az containerapp revision` commands in § Rollback.

### CI/CD pipeline — push-to-main auto-deploy

Reference: `.github/workflows/deploy.yml`. Five jobs:

1. **`changes`** — uses `dorny/paths-filter` to classify the diff as `backend` and/or `frontend`. Skips unaffected test jobs.

2. **`test-backend`** (backend changes only) — Python 3.12, spins up `pgvector/pgvector:pg16` service, installs dependencies, runs `pip-audit` (non-blocking), runs `pytest` with coverage. CI JWT secret: `ci-test-secret-that-is-at-least-32-characters-long`. Some tests intentionally skipped: `not test_list_accounts_returns_list and not test_lookup_entity_success`.

3. **`lint-frontend`** (frontend changes only) — Node 22, `npm ci`, `npm audit --audit-level=critical`, `tsc --noEmit`, `eslint . --max-warnings=0`, `prettier --check .`, `npm test`.

4. **`deploy`** (main branch only, after tests pass or no tests needed) — Azure login via `AZURE_CREDENTIALS` secret, `az acr login`, `docker build` tagged `:latest` and `:<sha>`, push, `az containerapp update` to the SHA tag, then `curl https://eclipse-exp.aldc.io/health` — fails the job if `status != healthy`. On failure: **automatic rollback** — reactivates the previous active revision.

5. **`load-test`** (post-deploy) — k6 10 VUs for 30s against `/internal/navira`; summary artifact uploaded.

Also present:
- `ai-security-audit.yml` — PR-triggered AI security review on security-relevant paths. Part of [[ai-pr-workflow]].
- `daily-self-improve.yml` — weekly cron (Mon 9 AM PST) — Opus-backed security review + few-shot harvesting, can open PRs.
- `.github/dependabot.yml` — dependency update automation.

### Manual deployment (fallback)

```bash
docker build -t acrzeusmemorydev.azurecr.io/eclipse-exp-api:<tag> -f Dockerfile .
az acr login --name acrzeusmemorydev
docker push acrzeusmemorydev.azurecr.io/eclipse-exp-api:<tag>
az containerapp update \
  --name eclipse-exp-api \
  --resource-group rg-zeus-memory-dev \
  --image acrzeusmemorydev.azurecr.io/eclipse-exp-api:<tag>
```

### Setting and rotating secrets

```bash
az containerapp secret set --name eclipse-exp-api \
  --resource-group rg-zeus-memory-dev \
  --secrets my-secret=<value>
az containerapp update --name eclipse-exp-api \
  --resource-group rg-zeus-memory-dev \
  --set-env-vars MY_SECRET=secretref:my-secret
```

For Fernet key rotation: generate new key → set `ENCRYPTION_KEY_NEW` → re-encrypt all `auth_config` values via `SecretManager.rotate_key()` → swap `ENCRYPTION_KEY` → restart. Full runbook: `docs/RUNBOOK.md`.

### Runtime layout inside the container

supervisord manages two processes:

| Process | Command | Port |
|---------|---------|------|
| gunicorn | `gunicorn app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080 --timeout 120 --access-logfile - --forwarded-allow-ips="*"` | :8080 (external) |
| nextjs | `docker-entrypoint.sh node server.js` (injects env vars into `.env.local` at start) | :3000 (internal only) |

Only `:8080` is exposed externally. `/internal/*` requests are proxied in-process from gunicorn to `http://127.0.0.1:3000`. Dockerfile healthcheck hits `/ping` every 30s (3 retries, 10s timeout).

### Rollback

**Automatic** — failed deploy smoke test (`/health`) re-activates the previous Container App revision.

**Manual**:
```bash
# List revisions
az containerapp revision list -n eclipse-exp-api -g rg-zeus-memory-dev -o table

# Shift all traffic to a prior revision
az containerapp ingress traffic set \
  -n eclipse-exp-api \
  -g rg-zeus-memory-dev \
  --revision-weight <previous-revision-name>=100
```

**Migration rollback** — provisioning transactions are atomic. For manual cleanup, use the `DELETE FROM eclipse_exp.*` chain in `docs/RUNBOOK.md`.

### Observability

| Signal | Mechanism | Key metrics/queries |
|--------|-----------|---------------------|
| Metrics | Prometheus at `/metrics` | `eclipse_db_pool_size{state=free|used}`, `eclipse_onboarding_duration_seconds`, `eclipse_connector_runs_total`, HTTP request metrics |
| Traces | OpenTelemetry OTLP | Enabled when `OTEL_EXPORTER_OTLP_ENDPOINT` set |
| Logs | structlog JSON | Filter by `correlation_id` or `tenant_id`; recipes in `docs/RUNBOOK.md` |
| Dashboards | `ops/grafana-dashboard.json` | Grafana-importable |
| Alert rules | `ops/alert-rules.yml` | Prometheus alerting |
| Slack alerts | Webhook | Job failures (immediate) + daily 6 AM ET digest |

### Health probes

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /ping` | None | Liveness — no DB. Returns `{"status":"ok","service":"eclipse_exp"}` |
| `GET /health` | None | Readiness — executes `SELECT 1`. Returns `healthy` or `degraded`. Used by deploy smoke test and should be Container App readiness probe. |
| `GET /metrics` | None | Prometheus text format |

---

## Security Model

### Authentication

Two mechanisms, both resolved by `auth_middleware`:

- **Bearer JWT** — HS256, 1h expiry, signed with `ECLIPSE_EXP_JWT_SECRET`. Payload carries `tenant_id`, `user_id`, `role`, `team`. Refresh via `POST /api/v1/auth/refresh`.
- **API key** — `X-API-Key` header. Stored as SHA-256 hash in `tenant_api_keys`. In-memory cache after first lookup (`core/cache.py`). Supports expiration dates.

### Authorization (RBAC)

Six-role hierarchy: `viewer < member < editor < admin ≈ superuser < owner`. Twenty permissions covering accounts, datasets, dashboards, visuals, data-views, users, and RBAC assignments. Implementation in `core/rbac/`.

### Tenant isolation via RLS

PostgreSQL schema `eclipse_exp` — 67+ RLS-enabled tables. Every tenant-scoped table has a policy of the form:

```sql
NULLIF(current_setting('app.tenant_id', true), '') IS NULL
  OR tenant_id = current_setting('app.tenant_id')::uuid
```

`tenant_connection()` wraps every handler's DB access in a transaction with `SET LOCAL app.tenant_id = $1`. Admin endpoints deliberately **do not** call `tenant_connection()`, granting intentional cross-tenant access. Pool `init` sets `search_path` on every connection acquire; `RESET ALL` on release.

### Secret management

Fernet symmetric encryption (`ENCRYPTION_KEY`) — values prefixed `enc:v1:` are encrypted. Optional Azure Key Vault backend via `AZURE_KEY_VAULT_URL`. `SecretManager.rotate_key()` handles rotation without downtime.

### TLS

Azure Container Apps terminates TLS at ingress. All PostgreSQL connections use `sslmode=require`. API keys and JWTs are sent only in headers — never in query parameters.

### Audit logging

`audit_write()` fires asynchronously on 62+ write endpoints across 16 route modules. Writes to `audit_logs` table. `UPDATE`/`DELETE` on `audit_logs` blocked by triggers — the table is append-only / immutable.

### Governing principles

Nine principles documented in `docs/PRINCIPLES.md`. The most relevant to day-to-day route coding: **P9 — Tenant Context Is Infrastructure** (tenant isolation is a platform concern, not a per-endpoint concern; use `tenant_connection()`, never inline `tenant_id` filtering in SQL). P3 covers the strangler-fig migration contract.

---

## Database Schema & Migrations

Schema name: `eclipse_exp`. All objects granted to role `eclipse_app`. Migrations live in `migrations/` — 87 SQL files covering number range 001–079 (with 9 duplicate number pairs and one missing number — see below).

**Auto-applied on startup** by `scripts/auto_migrate.py` inside FastAPI `lifespan`. No separate CI migration step. Reruns are safe — `IF NOT EXISTS` guards in all migrations.

**Migration naming rule** (from `CLAUDE.md`): numbered `NNN_description.sql`, must use `IF NOT EXISTS`, must `GRANT` to `eclipse_app`.

**Numbering collisions** — these are documented intentional duplicates (not bugs), but can confuse new developers:

| Shared number | Files |
|---------------|-------|
| 019 | `019_chat.sql`, `019_rls_security.sql` |
| 030 | `030_seed_datasets.sql`, `030_vector_embeddings.sql` |
| 035 | `035_onboarding_demo_app.sql`, `035_seed_test_dataset.sql` |
| 038 | `038_onboarding_demo_app.sql`, `038_patch_test_measures.sql` |
| 039 | `039_fix_test_measures.sql`, `039_onboarding_sessions.sql` |
| 058 | `058_site_stats_app.sql`, `058_validation_checklist_app.sql` |
| 059 | `059_seed_user_vlad.sql`, `059_sred_experiments.sql` |
| 068 | `068_multi_tenant_hardening.sql`, `068_seed_navira_roadmap_app.sql` |
| 069 | `069_julie_olmstead_consulting.sql`, `069_tenant_hardening_v2.sql` |

Number 014 is missing (jumps 013 → 015). Do not renumber — `auto_migrate.py` tracks applied migrations by filename.

**Core tables** (from `docs/ARCHITECTURE.md` + migration scan): `tenants`, `users`, `tenant_api_keys`, `tenant_secrets`, `connector_configs`, `connections`, `work_templates`, `work_queue`, `onboarding_jobs`, `contracts`, `contract_changes`, `quality_gates`, `audit_logs`, `cutover_jobs`, `dual_write_config`, plus later migrations adding tasks, boards, meetings, strategy map state, marketing tables, SRED experiments, vector embeddings (`pgvector`), chat history, and more.

**pgvector requirement** — `030_vector_embeddings.sql` installs the `vector` extension. Local dev must use `pgvector/pgvector:pg16`, not vanilla `postgres:16`.

---

## Onboarding Pipeline

eclipse_exp's flagship user-facing flow: prospect URL in → production tenant out in 6 steps.

### Two entry points

1. **Enterprise onboarding (ALDC-initiated)** — `POST /api/v1/onboarding/provision` with prospect URL + industry hints. Runs the full pipeline asynchronously. Monitor via `GET /api/v1/onboarding/jobs/{job_id}`.
2. **Self-service** — `/api/v1/portal/*` for smaller clients who self-onboard.

### 6-step orchestrator (`onboarding/`)

| Step | Module | Purpose |
|------|--------|---------|
| 1 Discovery | `onboarding/scraper.py` + `agents/discovery.py` | Scrapes prospect URL; AI classifies business type |
| 2 Classification | `onboarding/classifier.py` | Maps inferred signals to one of 9 business types |
| 3 Config generation | `agents/config_gen.py` + `onboarding/templates.py` | Maps inferred data sources to connector configs + KPI templates |
| 4 Validation | `onboarding/validator.py` | Validates generated config against schema and connector availability |
| 5 Provisioning | `agents/provisioning.py` | Atomic DB transaction: creates tenant + account + connections + templates + API key. Rolls back on any failure |
| 6 Activation | `agents/activation.py` | Queues initial `activation` + `ingestion_v2` work queue jobs |

All steps tracked in the `onboarding_jobs` table.

### Business types and KPI templates

| Type | Key Metrics |
|------|-------------|
| `agency` | Revenue, deal count, project delivery, utilisation |
| `ecommerce` | Revenue, order count, AOV, conversion rate, sessions |
| `saas` | MRR, subscriber count, churned count, churned revenue |
| `healthcare` | Visit count, avg wait time |
| `nonprofit` | Total donations, donation count, avg donation, active donors, retention |
| `real_estate` | Sales volume, transaction count, avg days on market |
| `education` | Enrolment count, avg GPA |
| `government` | Request count, avg resolution days |
| `other` | Activity count, total value |

### Webhook path

`POST /api/v1/onboarding/webhooks/prospect-created` — public path (no auth). **Planned integration** — not currently wired. When active, this will be called by the prospect-builder at `build.prospect.aldc.io`, which is the [[prospect-site-template]] repo. Until that cutover, prospect sites are created by cloning `[[prospect-site-template]]` directly (manual clone-and-deploy workflow). See [[prospect-site-template]] for the current process and site catalogue.

---

## Connectors

eclipse_exp hosts 50 connector types covering 4 categories.

### Breakdown

| Category | Count | Directory |
|----------|-------|-----------|
| REST | 24 | `connectors/rest/` (+ `rest/v2/`) |
| ODBC | 9 | `connectors/odbc/` (+ `odbc/v2/`) |
| File | 2 | `connectors/file/` |
| Custom | 10 | `connectors/custom/` (+ `custom/v2/`) |
| OData | ~5 | `connectors/odata/` |

### Full connector inventory

**REST:** alphavantage, amazon_sellercentral, azure_metrics, dor_api, esri_shapefile, exchange_rates_api, google_maps, intuit_tsheets, jira, microsoft_bing_ads, nasa_worldview, nutshell, opendatasoft, openweathermap, phone_burner, qbo_accounting, restcountrieseu, scrape_loblaw, scrape_shopify, scrape_shoppersdrugmart, scrape_wunderground, seller_cloud, shopify_conn, tomtom, windsor_ai.

**ODBC:** athena_s3, cosmosdb, mysql, netsuite_analytics, netsuite_connect, postgresql, redshift, snowflake_conn, sql_server.

**Custom:** amazon_ads, facebook_business, firebase, google_ads, hubspot, mongodb, s3, smartsheet, tradedesk_myreports, viant_dsp_reporting.

### V1 vs V2

Legacy connectors extend `BaseConnector` / `BaseConnectorFlat` / `BaseConnectorOdbc` in `connectors/base/`. Newer connectors extend `BaseConnectorV2` in `connectors/base/v2/`. Each category directory has a `v2/` subdirectory for migrated implementations. Work queue task routing: `task_type=ingestion` → V1 handler; `task_type=ingestion_v2` → Bronze-layer V2 pipeline.

**Key V2 abstractions:** `BaseConnectorV2`, `ConnectorConfig`, `ConnectorResponse`, `DataContract`, `Router` (dispatch by name+topic), `circuit_breaker.py`, `errors.py`.

**Catalog and health endpoints:** `/api/v1/connectors/catalog` (LLM-discoverable metadata), `/api/v1/connectors/health` (monitoring status).

Cross-reference: [[connector-development-standards]] for the canonical V2 implementation pattern. [[connector]] for the separate data-plane runtime (Prefect flows) that complements the in-process connectors here.

---

## Migration from Legacy Eclipse

### Strategy

Strangler-fig: legacy Eclipse clients stay on NextAuth + Cosmos DB; new clients provision on eclipse_exp (JWT + Postgres + RLS). eclipse_exp runs alongside `https://eclipse.analyticlabs.io`. Clients migrate via feature flag or DNS redirect. Full strategy: `docs/MIGRATION_STRATEGY.md` and `docs/CUTOVER.md`.

### Implementation (`migration/`)

| Module | Purpose |
|--------|---------|
| `dual_write.py` / `DualWriteConfig` | Per-tenant flag: write to Cosmos primary + Postgres shadow, or the reverse |
| `data_sync.py` | Verifies data parity between the two stores |
| `cutover.py` / `TenantCutover` | Switches a tenant's primary store. Registered as `task_type=cutover` |
| `migration/routes.py` | `/api/v1/migration/*` REST endpoints |

Requires `COSMOS_CONNECTION_STRING`. The Cosmos client is lazy-loaded in lifespan — without it, migration endpoints fail gracefully but all other eclipse_exp functionality continues normally.

Cross-references: [[eclipse-azure-deployment]] (the legacy deploy path this is replacing), [[data-pipeline-flow]] (platform-wide pipeline this participates in).

---

## See Also

- [[Eclipse]] — legacy Next.js UI this platform succeeds (currently documented as a tool; a repo page for `eclipse` is planned as Plan session #2 in the repo-documentation workstream)
- [[core_api]] — legacy Azure Functions control plane; dual-runs alongside eclipse_exp during the migration period
- [[connector]] — separate data-plane repo (Prefect flows); complements the in-process connectors here
- [[connector-development-standards]] — canonical V2 connector pattern that `connectors/base/v2/` implements
- [[data-pipeline-flow]] — platform-wide data pipeline, from Eclipse/connector sources through to Power BI
- [[star-schema-convention]] — ALDC dimensional modelling conventions; Gold layer follows this
- [[accumulating-source-tables]] — multiple-batch-per-key ingestion pattern relevant to connector runs
- [[azure-environments]] — Azure subscription-to-environment mapping
- [[deployment-groups]] — per-environment Azure resource inventory
- [[aldc-naming-convention]] — Azure resource naming conventions
- [[ai-pr-workflow]] — ALDC PR workflow (Semgrep + TruffleHog + Claude Opus review + PyTestArch) that gates merges
- [[ai-development-project-standard]] — ALDC >50% AI project tracking standard (tokens/cost/time header)
- [[zeus-memory]] — knowledge platform this repo reads/writes via `clients/zeus_memory.py`
- [[postman-collections]] — for interactive exercise of `/api/v1/*` endpoints
- [[prospect-site-template]] — prospect-builder repo that posts to the onboarding webhook
