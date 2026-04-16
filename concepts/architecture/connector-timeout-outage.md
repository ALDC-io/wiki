---
tags: [concept, architecture, incident, connector, azure, performance]
aliases: [connector timeout, work/pick timeout, Azure Function timeout]
sources: [sources/obsidian-import/work/Bugs/Connector Timeout Outage.md]
created: 2026-04-16
updated: 2026-04-16
---

# Connector Timeout Outage

Post-mortem and resolution for the Azure Function timeout outage affecting `/work/pick` in the core_api. The root cause was a global queue sweep that scaled O(N_accounts x N_connections) on every request.

## Symptom

`/work/pick` Azure Function calls timing out with `FunctionTimeoutAbortException` after hitting the 10-minute hard limit. 5,610 timeouts observed.

## Root Cause

In `repos/core_api/v1/route_work.py`, every call to `/work/pick` executed:

```python
work_size_list = work_size(summarize=False)  # global sweep
connections = remove_non_active_connections(connections, work_size_list)
```

`work_size(summarize=False)` iterated through **every account** and **every connection**, calling `QueueClient.get_queue_properties()` for each. With ~40 accounts x ~25 connections = 1,000 network calls at ~100ms each = 100+ seconds per request — before even attempting to dequeue work.

Concurrency made it worse: each agent thread (dozens) hit `/work/pick` simultaneously, multiplying the queue polls.

## Short-Term Fix

Remove the global `work_size()` sweep and `remove_non_active_connections()`:

```python
# Before: global sweep (expensive)
work_size_list = work_size(summarize=False)
connections = remove_non_active_connections(connections, work_size_list)

# After: filter locally, check queue per-connection (cheap)
connections = [
    c for c in agent.get('connection_authorized', [])
    if c.get("status", "inactive") == "active"
]
```

The per-connection queue check (`get_queue_properties()` + `receive_message()`) already runs after a connection is picked — it just happens on one queue instead of all of them.

**Impact**: `/work/pick` drops from minutes back to sub-second. Empty queues are still skipped (just later, when cheap). All other safety checks (max_connection, work_block, agent authorization, dequeue limits) are unaffected.

## Long-Term Fix (Planned)

1. **Queue-depth caching**: Background timer computes queue depth per connection every N minutes, writes to Cosmos. `/work/pick` reads cached values instead of live polling.

2. **Backpressure**: `work_scan()` / `work_queue_agent()` stops enqueuing when a connection already has N visible messages.

3. **Async warehouse merge**: Move `route_warehouse.warehouse_merge` (Snowflake stored procedure) to Durable Function so HTTP trigger returns immediately.

4. **Connector throttling**: Cap `max_threads` via config or dynamic feedback from cached queue metrics.

## Key Technical Details

- Azure Functions on consumption plan hard-stop at 600s (10 min)
- Connector `thread_timeout` defaults to 1,800s — mismatch with Azure SLA
- Each agent thread calls `/work/pick` in a loop (`executor_master.py` / `executor_single.py`)
- `work_size_account()` creates a new `QueueClient` per connection per call — no connection pooling

## Investigation Contributors

- Terence — initial connector repo and core_api analysis

## See Also

- [[Eclipse]] — the connector platform where this occurred
- [[data-pipeline-flow]] — `/work/pick` is part of the Eclipse → Snowflake pipeline
