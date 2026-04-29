---
tags: [entity, tool, prefect, v3, reference, api, concepts]
aliases: [Prefect v3 Reference, Prefect Docs Reference]
sources: [github.com/prefecthq/prefect docs/v3 (concepts: flows, tasks, deployments, blocks, work-pools, schedules, states)]
created: 2026-04-27
updated: 2026-04-27
---

# Prefect v3 — Core Concepts Reference

Quick-reference for ALDC developers building [[Prefect]] connectors. Extracted from the official Prefect v3 docs (GitHub `prefecthq/prefect`). For ALDC-specific deployment architecture, see [[Prefect]]. For development patterns (retries, caching, testing, etc.), see [[prefect-v3-patterns]].

---

## Flows

A flow is a Python function decorated with `@flow`. It is the top-level unit of work — the entry point for orchestration.

```python
from prefect import flow

@flow
def my_connector_flow(account_id: str, lookback_days: int = 7):
    # pull data, transform, load
    ...
```

### Flow decorator parameters

| Parameter | Description |
|---|---|
| `name` | Display name (default: function name) |
| `description` | Markdown description (default: docstring) |
| `retries` | Number of retries on failure |
| `retry_delay_seconds` | Wait between retries (int, list, or `exponential_backoff()`) |
| `timeout_seconds` | Max runtime — marks as failed if exceeded |
| `task_runner` | Task runner for `.submit()` calls (default: `ThreadPoolTaskRunner`) |
| `flow_run_name` | Template string or callable for run names (e.g., `"sync-{account_id}"`) |
| `validate_parameters` | Pydantic validation of inputs (default: `True`) |
| `log_prints` | Capture `print()` as Prefect logs (default: `False`) |
| `version` | Arbitrary version string (auto-populated from git hash if unset) |

### Subflows

Flows can call other flows (child/nested flows). Each child flow run has its own UI representation linked to the parent. Child flows block the parent until complete. For concurrent subflows, use `asyncio.gather`.

### Final state determination

- Returns normally → `Completed`
- Raises exception → `Failed`
- Returns a `PrefectFuture` → state determined by the future's resolution
- Returns a manually created `State` → that state is used
- Infrastructure crash (OOM, SIGTERM) → `Crashed`

---

## Tasks

Tasks are decorated with `@task`. They are atomic units of work within a flow — cacheable, retryable, and concurrent-capable.

```python
from prefect import task

@task(retries=3, retry_delay_seconds=10)
def fetch_api_data(endpoint: str, params: dict) -> dict:
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    return response.json()
```

### Task decorator parameters

| Parameter | Description |
|---|---|
| `name` | Display name |
| `retries` | Retry count on failure |
| `retry_delay_seconds` | Delay between retries (int, list, or `exponential_backoff()`) |
| `retry_condition_fn` | Callable `(task, task_run, state) -> bool` for conditional retry |
| `retry_jitter_factor` | Random jitter added to delays (avoids thundering herd) |
| `timeout_seconds` | Max runtime. **Caveat:** with `ThreadPoolTaskRunner`, cannot interrupt blocking I/O |
| `cache_key_fn` | Custom cache key function `(context, params) -> str` |
| `cache_policy` | Built-in policy: `INPUTS`, `TASK_SOURCE`, `DEFAULT`, `NO_CACHE` (combinable with `+`) |
| `cache_expiration` | `timedelta` for cache validity |
| `tags` | Set of tags for grouping |
| `log_prints` | Capture `print()` as logs |

### Three ways to call a task

| Method | Blocks? | Returns | Use case |
|---|---|---|---|
| `task()` | Yes | Result | Sequential execution |
| `task.submit()` | No | `PrefectFuture` | Concurrent execution within a flow |
| `task.map(iterable)` | No | List of `PrefectFuture` | Parallel map over items |

**Futures must be resolved** before the flow returns — via `.result()`, `.wait()`, `wait(futures)`, or by returning them from the flow.

### Data dependencies

When a `PrefectFuture` is passed as input to another task, Prefect automatically waits for it to resolve. For explicit ordering without data deps, use `wait_for=[future_a, future_b]`.

---

## Blocks

Blocks store typed configuration — most commonly **credentials** for external systems. Values of `SecretStr` fields are encrypted at rest.

```python
from prefect_snowflake import SnowflakeCredentials

# Save
creds = SnowflakeCredentials(account="wj66376", user="...", password="...")
creds.save("navira-snowflake-prod", overwrite=True)

# Load (in a flow)
creds = SnowflakeCredentials.load("navira-snowflake-prod")
```

### ALDC-relevant block types

| Block | Package | Use |
|---|---|---|
| `Secret` | built-in | Generic secret string (API keys) |
| `SnowflakeCredentials` | `prefect-snowflake` | Snowflake auth |
| `SnowflakeConnector` | `prefect-snowflake` | Snowflake queries |
| `AzureContainerInstanceCredentials` | `prefect-azure` | ACI work pool auth |
| `AzureBlobStorageCredentials` | `prefect-azure` | Azure Storage access |
| `S3Bucket` | `prefect-aws` | S3 storage |
| `GCPCredentials` | `prefect-gcp` | GCP auth |
| `DockerRegistryCredentials` | `prefect-docker` | GHCR/ACR auth |
| `SlackWebhook` | built-in | Alert notifications |

### Block lifecycle

- Blocks can be created/updated in the UI or via Python SDK
- Saving a block auto-registers its type with Prefect server
- Updating a block value propagates to all flows that load it — no redeployment needed
- ALDC auto-creates Snowflake credential blocks during deployment with placeholder passwords (see [[Prefect]] § Deployment architecture)

---

## Work Pools

Work pools bridge Prefect orchestration and execution infrastructure. ALDC uses **Azure Container Instances** type.

### Work pool types (relevant to ALDC)

| Type | Worker needed? | Description |
|---|---|---|
| **Docker** | Yes | Runs flows as local Docker containers |
| **Azure Container Instances** | Yes (hybrid) | Ephemeral ACI containers per flow run |
| **Azure Container Instances (Push)** | No | Prefect Cloud submits directly to ACI |
| **Process** | Yes | Local subprocess execution |

### Work queues

Each pool has a default queue. Additional queues enable priority and concurrency control:

| Queue | Priority | Concurrency | Use |
|---|---|---|---|
| `critical` | 1 (highest) | 1 | Urgent backfills |
| `high` | 5 | 3 | Important scheduled runs |
| `default` | 10 | unlimited | Regular runs |

### Environment switching (ALDC pattern)

ALDC uses `ENVIRONMENT_LEVEL` + `ENVIRONMENT_DEPLOYMENT_GROUP` env vars on the work pool to select Snowflake target + Azure storage account. To run one deployment against a different env, create a second work pool with different env vars. See [[Prefect]] § Switching environments.

### CLI commands

```bash
prefect work-pool create --type docker my-pool
prefect work-pool ls
prefect work-pool inspect my-pool
prefect work-pool pause/resume my-pool
prefect work-pool set-concurrency-limit 5 my-pool
prefect work-pool update --base-job-template template.json my-pool
```

---

## Deployments

A deployment is a server-side representation of a flow — stores metadata for remote orchestration (when, where, how).

### Two deployment models

| Method | Infrastructure | Use case |
|---|---|---|
| `flow.serve()` | Static (long-running process) | Simple, dev, testing |
| `flow.deploy()` | Dynamic (work pool) | Production, ephemeral infra, cost optimization |

### `flow.deploy()` key parameters

```python
my_flow.deploy(
    name="my-deployment",
    work_pool_name="my-work-pool",
    image="my-registry/my-image:tag",  # Docker image with flow code
    build=True,       # Build image (False to skip)
    push=True,        # Push to registry (False for local)
    cron="0 8 * * *", # Schedule (or interval=, rrule=, schedules=[])
    parameters={"key": "default_value"},
    job_variables={"env": {"MY_VAR": "value"}},  # Override work pool defaults
)
```

### Remote code storage (alternative to baking into image)

```python
flow.from_source(
    source="https://github.com/ALDC-io/connector.git",
    entrypoint="connector/accounts/ALDC_QA/deployments/exchange_rates.py:my_flow"
).deploy(name="my-deploy", work_pool_name="my-pool")
```

Supports: Git repos, S3 (`s3://`), GCS (`gs://`), Azure Blob (`az://`).

### Deployment schema (key fields)

| Field | Description |
|---|---|
| `name` | Unique per flow ID. Referenced as `{FLOW_NAME}/{DEPLOYMENT_NAME}` |
| `entrypoint` | `path/to/file.py:function_name` or `module.path:function_name` |
| `work_pool_name` | Target work pool |
| `job_variables` | Override work pool base job template (env vars, image, resources) |
| `concurrency_limit` | Max concurrent runs. `collision_strategy`: `ENQUEUE` (default) or `CANCEL_NEW` |
| `schedules` | List of schedule objects |
| `parameters` | Default parameter values |
| `tags` | Inherited by flow runs |

### Deploy multiple flows at once

```python
from prefect import deploy

deploy(
    flow_a.to_deployment("deploy-a"),
    flow_b.to_deployment("deploy-b"),
    image="my-image:tag",
    work_pool_name="my-pool",
)
```

---

## Schedules

Three schedule types, all supporting timezone-aware DST handling:

### Cron

```python
flow.deploy(..., cron="0 8 * * *")  # Daily at 8 AM
flow.deploy(..., cron="*/30 * * * *")  # Every 30 minutes
```

| Property | Description |
|---|---|
| `cron` | Standard cron string (via `croniter`) |
| `timezone` | IANA timezone (e.g., `"America/Chicago"`) |
| `day_or` | `True` (default): day-of-month OR day-of-week. `False`: AND logic |

### Interval

```python
flow.deploy(..., interval=3600)  # Every hour (seconds)
flow.deploy(..., interval="PT1H30M")  # ISO 8601 duration
```

DST note: intervals < 24h follow UTC; intervals >= 24h follow DST (clock-hour stays constant).

### RRule

```python
flow.deploy(..., rrule="FREQ=WEEKLY;BYDAY=MO,WE,FR;BYHOUR=9")
```

For complex calendar logic (last weekday of month, every other Tuesday, etc.).

---

## States

Every flow/task run transitions through states. Key states:

| State | Type | Terminal? | Meaning |
|---|---|---|---|
| `Scheduled` | SCHEDULED | No | Waiting for scheduled time |
| `Pending` | PENDING | No | Submitted, waiting for infra |
| `Running` | RUNNING | No | Executing |
| `Completed` | COMPLETED | Yes | Success |
| `Failed` | FAILED | Yes | Exception raised, no retries left |
| `Crashed` | CRASHED | Yes | Infrastructure issue (OOM, SIGTERM, evicted pod) |
| `Cancelled` | CANCELLED | Yes | User-cancelled |
| `Cached` | COMPLETED | Yes | Result loaded from cache |
| `AwaitingRetry` | SCHEDULED | No | Failed with retries remaining |
| `Late` | SCHEDULED | No | Scheduled time passed, not picked up (check worker health) |

### Key transitions to watch

- **Scheduled → Late**: No worker picked up the run. Check: workers healthy? Polling correct pool/queue? Concurrency limited?
- **Pending → Crashed**: Worker failed to create infrastructure, code not found, or import errors.
- **Running → Crashed**: Not a code exception — likely OOM, evicted container, or timeout.

---

## See Also

- [[Prefect]] — ALDC-specific deployment architecture, Azure resources, env switching
- [[prefect-v3-patterns]] — Development patterns (retries, caching, testing, Docker/ACI)
- [[connector-development-standards]] — ALDC canonical connector pattern
- [[connector]] — connector repo (Prefect flows live here)
