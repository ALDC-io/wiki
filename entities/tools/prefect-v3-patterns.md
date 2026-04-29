---
tags: [entity, tool, prefect, v3, patterns, howto, development]
aliases: [Prefect v3 Patterns, Prefect How-To]
sources: [github.com/prefecthq/prefect docs/v3 (how-to-guides: workflows, deployments, deployment_infra, configuration)]
created: 2026-04-27
updated: 2026-04-27
---

# Prefect v3 — Development Patterns

Practical patterns for building ALDC connectors with Prefect v3. For core concepts (flows, tasks, blocks, etc.), see [[prefect-v3-reference]]. For ALDC-specific deployment architecture, see [[Prefect]].

---

## Retries & Error Handling

### Basic retries

```python
@task(retries=3, retry_delay_seconds=10)
def fetch_api_data(endpoint: str) -> dict:
    ...
```

### Exponential backoff with jitter

```python
from prefect.tasks import exponential_backoff

@task(
    retries=4,
    retry_delay_seconds=exponential_backoff(backoff_factor=5),
    retry_jitter_factor=3,  # avoids thundering herd
)
def call_rate_limited_api():
    ...
```

### Conditional retry (skip on 401/404)

```python
def retry_on_transient(task, task_run, state) -> bool:
    try:
        state.result()
    except httpx.HTTPStatusError as exc:
        return exc.response.status_code not in [401, 404]
    except httpx.ConnectError:
        return False
    except:
        return True

@task(retries=3, retry_delay_seconds=[1, 5, 30], retry_condition_fn=retry_on_transient)
def api_call():
    ...
```

### Variable delay list

```python
@task(retries=3, retry_delay_seconds=[1, 10, 60])
def flaky_task():
    ...
```

### Global defaults

```bash
prefect config set PREFECT_TASK_DEFAULT_RETRIES=2
prefect config set PREFECT_TASK_DEFAULT_RETRY_DELAY_SECONDS="1,10,100"
```

### Flow-level retries

Flows also accept `retries` and `retry_delay_seconds`. The entire flow re-executes from the beginning. With `on_failure` hooks, the hook fires only after all retries are exhausted.

### Manual retry (CLI)

```bash
prefect flow-run ls --state FAILED
prefect flow-run retry <run-name-or-id>
```

---

## Caching

Caching lets a task return a stored result without re-executing. **Requires result persistence:**

```bash
prefect config set PREFECT_RESULTS_PERSIST_BY_DEFAULT=true
```

### Built-in cache policies

| Policy | Cache key includes | Use case |
|---|---|---|
| `DEFAULT` | inputs + task source + run ID | Same task, same inputs, same flow run |
| `INPUTS` | inputs only | Same task, same inputs, any run |
| `TASK_SOURCE` | task source code only | Re-run detection |
| `FLOW_PARAMETERS` | parent flow parameters only | Flow-level dedup |
| `NO_CACHE` | nothing | Disable caching |

### Composing policies

```python
from prefect.cache_policies import INPUTS, TASK_SOURCE

@task(cache_policy=INPUTS + TASK_SOURCE)
def expensive_transform(data: dict):
    ...
```

### Ignoring specific inputs

```python
@task(cache_policy=INPUTS - "debug")
def my_task(x: int, debug: bool = False):
    ...  # debug flag doesn't affect cache key
```

### Cache expiration

```python
from datetime import timedelta

@task(cache_policy=INPUTS, cache_expiration=timedelta(hours=1))
def hourly_data_pull():
    ...
```

### Force refresh

```python
@task(cache_policy=INPUTS, refresh_cache=True)
def always_fresh():
    ...
```

Global: `prefect config set PREFECT_TASKS_REFRESH_CACHE=true`

### Distributed cache (shared storage)

```python
from prefect_aws import S3Bucket

s3 = S3Bucket.load("my-cache-bucket")

@task(cache_policy=INPUTS, result_storage=s3)
def shared_cache_task(x: int):
    return x + 42
```

---

## Concurrency & Parallelism

### Submit tasks concurrently

```python
from prefect import flow, task
from prefect.futures import wait

@flow
def parallel_flow():
    futures = [process_item.submit(item) for item in items]
    done, not_done = wait(futures)
    results = [f.result() for f in done if f.state.is_completed()]
```

### Map over an iterable

```python
@flow
def map_flow():
    futures = process_item.map(items)  # parallel map
    results = futures.result()  # bulk resolve
```

### Unmapped arguments (static values alongside mapped)

```python
from prefect import unmapped

futures = process.map(items, unmapped(config))  # config is NOT iterated
```

### Task runners

| Runner | Execution model | Use case |
|---|---|---|
| `ThreadPoolTaskRunner(max_workers=N)` | Concurrent threads | Default. I/O-bound tasks. |
| `ProcessPoolTaskRunner` | Separate processes | CPU-bound. Reliable timeouts on blocking ops. |
| `DaskTaskRunner` | Distributed (Dask) | Large-scale distributed. `prefect[dask]` |
| `RayTaskRunner` | Distributed (Ray) | Large-scale distributed. `prefect[ray]` |

```python
from prefect.task_runners import ThreadPoolTaskRunner

@flow(task_runner=ThreadPoolTaskRunner(max_workers=4))
def concurrent_flow():
    ...
```

### State dependencies (ordering without data flow)

```python
@flow
def ordered_flow():
    a = setup.submit()
    b = validate.submit(wait_for=[a])
    c = load.submit(wait_for=[b])
```

### Handling failures in concurrent work

```python
futures = process.map(items)
done, not_done = wait(futures)

for f in done:
    if f.state.is_completed():
        results.append(f.result())
    else:
        errors.append(f.state)
```

---

## Logging

### Prefect run logger

```python
from prefect.logging import get_run_logger

@task
def my_task():
    logger = get_run_logger()
    logger.info("Processing started")
    logger.warning("Rate limit approaching")
```

Logs are sent to Prefect backend and visible in the UI. Supports standard Python levels (DEBUG, INFO, WARNING, ERROR).

### Capture print statements

```python
@flow(log_prints=True)
def my_flow():
    print("This appears in Prefect UI logs")  # inherited by nested tasks
```

Global: `prefect config set PREFECT_LOGGING_LOG_PRINTS=True`

### Logging from subprocesses

```python
from prefect.context import with_context

def worker_fn(item):
    logger = get_run_logger()
    logger.info(f"Processing {item}")
    return item * 2

@task
def parallel_task(items):
    with multiprocessing.Pool() as pool:
        return pool.map(with_context(worker_fn), items)
```

### Logging from state change hooks

Hooks run outside the flow/task context — use `flow_run_logger` instead of `get_run_logger`:

```python
from prefect.logging.loggers import flow_run_logger

def on_failure_hook(flow, flow_run, state):
    logger = flow_run_logger(flow_run, flow)
    logger.error(f"Flow failed: {state.message}")
```

---

## Secrets & Configuration

### Secret blocks

```python
from prefect.blocks.system import Secret

# Store
Secret(value="my-api-key").save("navira-google-ads-token", overwrite=True)

# Load
api_key = Secret.load("navira-google-ads-token").get()
```

### Integration credential blocks

```python
from prefect_snowflake import SnowflakeCredentials

creds = SnowflakeCredentials.load("navira-snowflake-prod")
conn = creds.get_connection()
```

### Variables (non-sensitive config)

```python
from prefect.variables import Variable

Variable.set("navira_lookback_days", 7)
days = Variable.get("navira_lookback_days", default=7)
```

Variables are **not encrypted** — use for non-sensitive values only. Cacheable, max 5000 chars.

### Variables in `prefect.yaml`

```yaml
pull:
  - prefect.deployments.steps.git_clone:
      branch: "{{ prefect.variables.deployment_branch }}"
```

### Settings management

```bash
prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect config view --show-defaults
prefect profile create dev && prefect profile use dev
```

Project-level settings via `prefect.toml` or `.env` file in project directory.

---

## State Change Hooks

### Available hooks

| Hook | Flow | Task | Fires when |
|---|---|---|---|
| `on_completion` | Yes | Yes | Run completes successfully |
| `on_failure` | Yes | Yes | Run fails (after all retries exhausted) |
| `on_cancellation` | Yes | No | Flow run cancelled |
| `on_crashed` | Yes | No | Flow run crashed (infra issue) |
| `on_running` | Yes | Yes | Run starts executing (before body runs) |

### Failure notification example

```python
@flow(retries=2)
def my_flow():
    ...

@my_flow.on_failure
def notify(flow, flow_run, state):
    slack = SlackWebhook.load("alerts")
    slack.notify(f"{flow_run.name} failed: {state.message}")
```

Hooks run **client-side** — not guaranteed if infrastructure crashes. For robust notifications, use Prefect Automations.

---

## Docker & ACI Deployment

### Docker work pool (local/on-prem)

```bash
prefect work-pool create --type docker my-pool
prefect worker start --pool my-pool
```

### Deploy with image baking

```python
my_flow.deploy(
    name="my-deploy",
    work_pool_name="my-pool",
    image="ghcr.io/aldc-io/connector:latest",
    push=False,  # True to push to registry
)
```

### Use existing image (skip build)

```python
my_flow.deploy(
    name="my-deploy",
    work_pool_name="my-pool",
    image="ghcr.io/aldc-io/connector:latest",
    build=False,  # Use pre-built image
    push=False,
)
```

### Custom Dockerfile

```python
from prefect.docker import DockerImage

my_flow.deploy(
    name="my-deploy",
    work_pool_name="my-pool",
    image=DockerImage(name="my-image", tag="v1", dockerfile="Dockerfile"),
)
```

### Runtime pip installs (without rebuilding image)

```python
my_flow.deploy(
    ...,
    job_variables={"env": {"EXTRA_PIP_PACKAGES": "boto3 requests"}},
)
```

### Azure Container Instances (ALDC production pattern)

ALDC uses ACI work pools. Key notes:

- **Push work pools** (Prefect Cloud): no worker needed, Prefect submits directly to ACI
- **Hybrid work pools**: require a worker process (`prefect worker start --pool my-aci-pool`)
- ACI requires `platform="linux/amd64"` in `DockerImage` (arm64 will fail)
- Flow runs limited to **24 hours** on push work pools
- Provisioning creates: resource group, app registration, service principal, ACR, managed identity, `AzureContainerInstanceCredentials` block

```bash
# Auto-provision ACI infrastructure (Prefect Cloud)
prefect work-pool create --type azure-container-instance:push --provision-infra my-aci-pool
```

For ALDC's existing ACI setup, see [[Prefect]] § Azure resources (production).

---

## Testing

### Test harness (temporary database)

```python
from prefect.testing.utilities import prefect_test_harness

# pytest fixture (session-scoped — recommended)
@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    with prefect_test_harness():
        yield

def test_my_flow():
    result = my_flow()
    assert result == expected
```

The harness creates a temporary SQLite DB + ephemeral API server. Full state tracking, result persistence, and API interactions work normally.

### Test the function directly (bypass engine)

```python
def test_my_task():
    assert my_task.fn(42) == 84  # Skips retries, logging, state tracking
```

If the task uses `get_run_logger()`, wrap with:
```python
from prefect.logging import disable_run_logger

with disable_run_logger():
    result = my_task.fn(42)
```

### Async tests

```python
@pytest.mark.asyncio
async def test_async_flow():
    result = await my_async_flow()
    assert result == "expected"
```

### Parallel test processes (pytest-xdist)

Each worker creates its own `prefect_test_harness` — no conflicts (separate ports + SQLite DBs).

---

## Quick Reference — ALDC Connector Checklist

When building a new Prefect connector for the Navira integration or any other client:

1. **Define the flow** with `@flow` — parameters for account_id, lookback_days, etc.
2. **Break into tasks** with `@task` — one per logical step (fetch, transform, load)
3. **Add retries** — `retries=3, retry_delay_seconds=exponential_backoff(backoff_factor=5)` for API calls
4. **Store credentials** in Blocks — `Secret` for API keys, `SnowflakeCredentials` for DW access
5. **Use `log_prints=True`** or `get_run_logger()` for observability
6. **Deploy** with `flow.deploy()` targeting the ALDC ACI work pool
7. **Set a schedule** — `cron=`, `interval=`, or `rrule=`
8. **Override env vars** via `job_variables` for environment switching (see [[Prefect]] § Switching environments)
9. **Test** with `prefect_test_harness` and `.fn()` for unit tests
10. **Follow** [[connector-development-standards]] for the ALDC-specific attribute hierarchy and patterns

---

## See Also

- [[prefect-v3-reference]] — core concepts (flows, tasks, blocks, work pools, deployments, schedules, states)
- [[Prefect]] — ALDC-specific architecture, Azure resources, env switching, migration context
- [[connector-development-standards]] — ALDC canonical Prefect connector pattern
- [[connector]] — connector repo where Prefect flows live (`operation-fiasco` branch)
- [[navira/README|Navira Roadmap]] — upcoming connector work using these patterns
