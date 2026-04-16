
**Connector Initial Pass by Terence:**


I dug through the connector repo we have and the only knobs it exposes to Azure Queue load are the ones in `executor_master.py`/`executor_single.py`: every process in the pool (size = `max_threads` from config/env) immediately calls `/work/pick`, runs the entire `Schedule.extract` pipeline, and then loops forever unless `loop` is set to false. There’s no awareness of “schedule blocks” or queue saturation in the agent itself—the only throttling is that random stagger at start-up and the `sleep` delay when `get_work` returns nothing. So if `max_threads` is cranked up or `loop` stays true, we’re guaranteed a burst of concurrent `/work/pick` calls that hammer the Azure Function, even while a block is in place.

Two other observations from the code: (1) the agent’s `thread_timeout` defaults to 1,800 s, but Azure Functions on a consumption plan hard-stop at 600 s—the failures you’re seeing are exactly WebJobs killing `Functions.v1` after 10 minutes while the agent is still mid-call to `/warehouse/*`. Dropping the connector-side timeout to <600 s (and/or splitting the long-running stages) will keep us from holding a function open past its SLA. (2) Every work item runs staging + merge synchronously via `self.core.get_api('/warehouse/…')`, so a single heavy dataset ties up one function instance for the full run; reducing `max_threads`, increasing `sleep` when no work is available, or temporarily setting `loop=false` so the supervisor re-launches workers on demand are the only quick mitigations available from this repo.

I don’t have the `core_api` repo locally, so I can’t confirm whether the schedule block logic or queue dequeue visibility are configured correctly on that side. If you want me to trace the actual Azure Function implementation (how `/work/pick`, `/schedule/*`, and `/warehouse/*` behave under load), please drop that repo into the workspace and I’ll keep digging.



**Core API Initial Pass by Terence:**

**What’s actually timing out**

Every call to `POST /v1/work/pick` ends up inside `route_work.work_pick_agent` (repos/core_api/v1/route_work.py). At the very top of that function (around line 700) we do:

```python
work_size_list = work_size(summarize=False)
```

`work_size()` without an `account_id` parameter iterates over **every** account and **every** connection, and for each one calls `QueueClient.get_queue_properties()` to fetch the approximate message count (see `work_size` + `work_size_account` ~lines 1040‑1115). 

In other words, every agent thread that asks for work forces the Function App to poll _all_ queues in the tenant before it even looks at its own authorized connections. With a few dozen accounts/connections this already takes seconds; with hundreds it can easily chew through all 10 minutes and the Function host kills the request (the timeout you’re seeing 5,610 times). The queue backlog and schedule block just make this worse because agents keep polling, which multiplies those O(N_accounts × N_connections) queue calls.

**Quick fix**

Short-circuit that global queue sweep so `work_pick_agent` only touches the queues it actually cares about:

1. In `route_work.work_pick_agent` remove the unscoped `work_size_list = work_size(summarize=False)` call (or at least guard it).
2. Drop the subsequent `remove_non_active_connections(connections, work_size_list)` call (or change it to call `work_size(account_id=conn.get('account_id'), summarize=False)` _after_ a connection is chosen and cache the result per account). We already fetch `queue_size = queue_client.get_queue_properties()` once we’ve picked a connection, so the extra global sweep isn’t needed to skip empty queues.

That single change turns each `/work/pick` into “look up agent → grab one connection → read that queue once,” which brings execution time back to a few hundred milliseconds and keeps the Function well inside its 10‑minute budget without touching the connector threads or the schedule block logic.

**Long‑term fix**

Use cached/back-pressured queue metrics instead of live per-request scans:

- Move the expensive `work_size` logic into a background timer (or Durable Function/activity) that runs every minute, computes queue depth per connection, and writes it to Cosmos (`work_connection` or a new `work_queue_metrics` container).
- Have `work_pick_agent` read those cached counts (or rely on Cosmos flags like `partition.in_queue`) when it needs to filter empty queues; only hit Azure Queue Storage for the specific connection it’s about to dequeue from.
- While you’re there, add queue-depth thresholds to `work_scan`/`work_queue_agent` so we stop enqueuing new partitions when a connection already has N visible messages—this prevents the backlog that triggered the schedule block in the first place and gives you real backpressure.

If we still see occasional >10‑minute requests after removing the global sweep, the next heavyweight candidate is `route_warehouse.warehouse_merge` (stored-procedure call that blocks until Snowflake finishes). For that, the long-term fix would be to run merges via a Durable Function (enqueue work, return immediately, let an activity function watch Snowflake) so the HTTP trigger isn’t forced to sit idle for minutes.



# Short Term Fix:

### Short-term fix (apply now)

All changes live in `repos/core_api/v1/route_work.py`. The goal is to stop `/work/pick` from sweeping every queue in the tenant on every request.

```diff
diff --git a/v1/route_work.py b/v1/route_work.py
@@
- agent = route_agent.agent_describe(agent_id)
- connections = agent.get('connection_authorized', [])
- received_message = None
- account_work_block = None
- work_size_list = work_size(summarize=False)
-
- # quick fix to filter only active connections
- connections_active = []
- for connection in connections:
- if connection.get("status", "inactive") == "active":
- connections_active.append(connection)
-
- connections = connections_active
+ agent = route_agent.agent_describe(agent_id)
+ received_message = None
+ account_work_block = None
+
+ # Keep only active, authorized connections; queue depth checks happen lazily per connection.
+ connections = [
+ connection for connection in agent.get('connection_authorized', [])
+ if connection.get("status", "inactive") == "active"
+ ]
@@
- connections = remove_non_active_connections(connections, work_size_list)
conn = func_common.pick_connection(connections)
@@
- all_connections = remove_non_active_connections(all_connections, work_size_list)
conn = func_common.pick_connection(all_connections)
@@
-def remove_non_active_connections(connections, connection_size_list):
- """
- Removes any connection on the connections list if that connection does not have any active work size found on it
- Args:
- connections (list): Connections list. Just the ID
- connection_size_list (list of dictionaries): Work size for every connection
- """
- remove_from_connections_list = []
- good_connections_list = []
- for connection_size in connection_size_list:
- for connection in connections:
- if connection_size.get("connection_id") == connection.get("id") and connection_size.get("size") <= 0:
- remove_from_connections_list.append(connection.get("id"))
- for i in range(0, len(connections)):
- if connections[i].get("id") in remove_from_connections_list:
- continue
- else:
- good_connections_list.append(connections[i])
- return good_connections_list
```

*What this does*:
- **Drops the global `work_size(summarize=False)` call (which was polling every account/connection queue).**
- Removes the filtering helper that depended on those global metrics.
- Keeps only “active” connections via a cheap list comprehension; per-connection queue depth is already checked later when we actually fetch from Azure Queue Storage.

After editing, redeploy/restart the Function (or let Azure pick up the change) and watch the `/work/pick` latency drop from minutes back to sub‑second.

---

### Long-term fix outline

1. **Queue-depth caching / backpressure**
- Add a timer/Durable Function that calls `work_size_account(account_id, summarize=False)` once every N minutes per account and writes the results into Cosmos (new `work_queue_metrics` container or an attribute on `work_connection` docs).
- Modify `work_pick_agent` to read that cached value (or rely on the `partition.in_queue` flag) instead of hitting Azure Queue Storage for every connection; fall back to a live check only when the cache is stale.
- Update `work_scan()` / `work_queue_agent()` to consult the same metrics before enqueuing more partitions so we stop flooding a connection whose queue is already above a defined threshold.

2. **Async/long-running operations**
- The stored-procedure path inside `route_warehouse.warehouse_merge` can still exceed 10 minutes when Snowflake is busy. Move that work into an async pipeline (e.g., Durable Function, Azure Queue-triggered worker, or background task) so the HTTP trigger only schedules the merge and returns immediately, while a worker monitors Snowflake and updates schedule/session state.

3. **Connector throttles**
- Optional but helpful: enforce per-account/per-connection concurrency limits in `executor_master.py` (e.g., cap `max_threads` via config or dynamic feedback from the cached queue metrics) so agents back off automatically when queue depth climbs or when an account is under `work_block`.

Implementing those pieces gives you backpressure, cheaper `/work/pick` calls, and a path for truly long-running operations without ever touching the 10‑minute Azure Function ceiling again. Let me know if you want help drafting those changes once the quick fix is in.



# In plain english

1. **What `/work/pick` is supposed to do:** every agent call should grab one of its authorized connections, peek that connection’s Azure queue, and hand back the next work item. That should take a few hundred milliseconds.
    
2. **What the current code is doing:** before looking at the agent’s connections, `work_pick_agent` called `work_size(summarize=False)` (route_work.py) to build `work_size_list`. That function loops through _every account_ and _every connection_ and calls `QueueClient.get_queue_properties()` for each just to see how many messages might be in the queue. Only after that global sweep finished did we use `remove_non_active_connections()` to drop empty queues from the agent’s list.
    
3. **Why its blowing up:** with dozens of accounts and hundreds of connections, that “pre-flight” scan takes minutes. Because `/work/pick` is an HTTP-triggered Azure Function with a 10‑minute hard limit, those requests routinely hit the ceiling and were killed (`FunctionTimeoutAbortException`). 
	1. **The helper wasn’t evil per se—it just forced an O(N_accounts × N_connections) queue poll on every request.**
    
4. **What we should change:** we remove the `remove_non_active_connections()` call and the `work_size(...)` sweep that fed it. Instead, we filter out inactive connections locally and let the existing per-connection queue check (the `queue_client.get_queue_properties()` and `receive_message()` after a connection is chosen) decide whether to keep looping. So we still skip dead connections and we still refuse to work on blocked accounts, but we no longer pay the price of polling every queue before we even pick one.
    
5. **Impact:** Non-active (status != “active”) connections stay excluded. Active connections with empty queues might get picked, but they’re discarded immediately after the per-connection queue read—which is cheap. In return, `/work/pick` drops back under a second, the Function stops timing out, and Azure Queue Storage doesn’t get hammered by thousands of redundant `GetQueueProperties` calls.
    



# Polling 

- **What a single poll costs:** every call to `queue_client.get_queue_properties()` is a network roundtrip to Azure Storage that returns the approximate message count for one queue. With reasonable latency (say 80‑150 ms) that’s fine when you’re only checking the one queue you’re about to dequeue from.
    
- **What `work_size(summarize=False)` does:** it loops through every active account, grabs every connection under that account, builds a connection string, and runs `get_queue_properties()` for each one. So if you have 2 accounts × 25 connections, that’s ~1,000 network calls per `/work/pick`. At 100 ms apiece you’ve already burned 100 s before you even pick a queue.
    
- **Concurrency makes it worse:** each agent thread (there can be dozens) hits `/work/pick`, so those thousand polls are happening in parallel across threads. Azure Queue Storage handles it, but the Function host thread is blocked waiting for all of them to finish. Stack enough of those calls and you chew through the 10‑minute limit.
    
- **Impact on `work_pick_agent`:** the function can’t return a work item until the global poll completes, so the agent sits idle, the Azure Function invocation timer keeps ticking, and once it crosses 600 s the runtime throws `FunctionTimeoutAbortException`. Meanwhile you still have zero work items because you never made it to the actual `receive_message()` call.
    

By removing the global poll we go back to the cheap case: we only pay for the queue we’re about to dequeue from (plus one `receive_message()`), so `/work/pick` spends milliseconds instead of minutes in network I/O.




# Walkthrough Code:

Here’s the smoking gun straight from `repos/core_api/v1/route_work.py`—this runs **every time** `/work/pick` is called:

```python
def work_pick_agent(...):
...
work_size_list = work_size(summarize=False) # ← global sweep
...
connections = remove_non_active_connections(connections, work_size_list)
```

And `work_size(summarize=False)` is defined a few hundred lines lower:

```python
def work_size(account_id = None, summarize = True):
count_total = 0
response_list = []

if account_id == None:
accounts = account_list()
for account in accounts:
work_size_return = work_size_account(account.get("id"), summarize)
...
else:
work_size_return = work_size_account(account_id, summarize)
...

def work_size_account(account_id, summarize):
count_total = 0
response_list = []
account = account_describe(account_id)
account_connections = work_connection_list(account_id)
for connection in account_connections:
queue_id = connection.get("id")
...
queue_client = QueueClient.from_connection_string(connect_str, queue_id)
properties = queue_client.get_queue_properties() # ← network call per connection
queue_size = properties.approximate_message_count
...
```

So on every `/work/pick` call we:

1. Enumerate *all* accounts (`account_list()`).
2. For each account, enumerate *all* connections (`work_connection_list()`).
3. For each connection, instantiate a `QueueClient` and hit Azure with `get_queue_properties()`.

With 40 accounts × 25 connections, that inner loop runs 1,000 times per request before we even try to `receive_message()` from the agent’s own queue, which is why the Function blows past its 10‑minute limit. Removing the call to `work_size()` (and the downstream `remove_non_active_connections`) stops this global sweep.


# Why work_size() is redundant

Because the information `work_size()` was gathering is redundant:

- We only needed queue depth to avoid picking connections whose queues were already empty. But after a connection is chosen we already run:

```python
queue_size = queue_client.get_queue_properties().approximate_message_count
if queue_size > 0:
received_message = queue_client.receive_message(...)
else:
continue # pick another connection
```

That per-connection check still runs, so we don’t risk handing out “empty” work items.

- Non-active connections (`connection["status"] != "active"`) are filtered out locally; we don’t need global queue stats to know which connections are disabled.
    
- All other safety checks (`max_connection`, `work_block`, agent authorization, dequeue limits) don’t depend on `work_size_list` at all, so their behavior is unchanged.
    

So dropping `work_size()` removes a massive amount of unnecessary polling while preserving the actual business logic: we still refuse inactive connections, we still skip empty queues (just later, when it’s cheap), and we still enforce every other gate the same way. The only thing lost is an expensive optimization that no longer makes sense at our scale.




# How are connections removed and why we don't need to check (all accounts X all connections?

That loop filters out **inactive** connections (status flag ≠ “active”). `remove_non_active_connections()` was doing something different: it used the giant `work_size_list` to drop connections whose queue depth was already zero. 

Since we now check queue depth immediately after we pick a connection (and skip it if the queue is empty), we no longer need that upfront, very expensive pre-filter. So yes—you still have the status-based filter, and the queue-depth filter now happens on-demand instead of via `remove_non_active_connections()`.