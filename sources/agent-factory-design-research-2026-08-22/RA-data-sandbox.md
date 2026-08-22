# R-A — Is the T2 ephemeral data sandbox real, cheap and safe?

**Brief:** settle `docs/specs/architecture-v0.md` §7.1 (and the §7.2 counter-claim) with primary sources.
**Date:** 2026-08-22.

> **Evidence-channel caveat, stated up front because it changes how you should read every `DOCUMENTED`
> tag below.** This session's egress proxy **blocks `docs.snowflake.com`** (and `docs.snowflake.cn`,
> `docs.getdbt.com`, `tobikodata.com`, `interworks.com`, `medium.com`, `select.dev`, `en.wikipedia.org`,
> `docs.coalesce.io` — everything except `github.com` / `raw.githubusercontent.com` that I tried).
> Snowflake reference-doc content below was surfaced **through the search tool**, which reads the page
> and renders it; I could not open the page and verify the sentence in its surrounding context. I mark
> these `DOCUMENTED*` — vendor reference doc, retrieved indirectly. Anything I could open directly
> (GitHub-hosted docs, SQLMesh, dbt docs source, issue threads) is plain `DOCUMENTED`. Estate facts come
> from `/home/user/wiki`, which I read but did not write to. **Every `DOCUMENTED*` claim below should be
> re-checked with a one-line SQL probe or a browser before anything is built on it.** Two of them
> (object-tagging edition requirement) already came back self-contradictory — see §4.

---

## 1. Verdict

**T2 is real and cheap, but the spec has the granularity wrong, the enforcement mechanism wrong, and the
concurrency conclusion wrong.** Zero-copy cloning is genuinely metadata-only at creation — zero warehouse
credits, near-zero storage until divergence — and this estate *already runs the pattern in production*
(`CREATE DATABASE QA_DG1_GEP_PREFECT CLONE TEST_DG1_GEP;`), so the mechanism is not speculative. But:
**(a)** §4 says "clone **schema**", and a schema clone does not isolate this estate, because ALDC's
warehouse DDL is schema-qualified and *database*-unqualified (`CREATE OR REPLACE TABLE WAREHOUSE.X …`) —
it must be a **database** clone plus `USE DATABASE`, or the writes land in the real schema;
**(b)** the share worry in §7.1 is half right and half wrong — an *imported* (share) database genuinely
cannot be cloned, which breaks a step already written into the GP-219 plan, but the *local* database whose
views reference the share clones fine and the fully-qualified `PROD_DG1_GEP.*` references keep resolving
through the share, so a T2 clone is a **live** read of a moving dependency, not a snapshot;
**(c)** cost is not the problem — this estate's Snowflake storage is ~2% of spend and the real burn is the
60-second minimum billing per warehouse resume, which makes *per-agent warehouses* the expensive design and
a *shared* warehouse the cheap one — which puts a hard conflict edge right back where §7.2 says there is none;
**(d)** nothing in Snowflake enforces teardown — there is no native TTL, resource monitors cannot kill a
query with useful latency, and per-user quota blocks explicitly do not apply to warehouses; the only exact
controls are `STATEMENT_TIMEOUT_IN_SECONDS`, a role with USAGE on exactly one X-Small warehouse, and an
external `ALTER USER … ABORT ALL QUERIES`. **§7.1's fear ("if T2 is not cheap, §4 collapses") is not what
happens. §4 does not collapse on cost. It collapses on the claim in §7.2 — "two agents in two clones
conflict on nothing" is false, and I can name seven edges.**

---

## 2. What the evidence says

### 2.1 Clone semantics — what is actually cheap

| Claim | Tier | Evidence |
|---|---|---|
| Cloning copies metadata only; the clone references the source's micro-partitions | `DOCUMENTED*` | Snowflake *Cloning considerations*: "creating a new set of metadata pointing to the same micro-partitions"; copy-on-write on modification. [object-clone] |
| Storage cost at creation ≈ 0; accrues only for micro-partitions unique to the clone | `DOCUMENTED*` | "Storage cost of a clone equals the storage used by micro-partitions that exist only in the clone… initially, this cost is close to zero." [object-clone] |
| Cloning uses **no virtual warehouse** — it is a cloud-services-only DDL operation | `DOCUMENTED*` | *Understanding compute cost*: "DDL operations, particularly cloning, are entirely metadata operations, meaning they use only cloud services compute." |
| **Cloning is NOT instantaneous and does NOT lock the source** | `DOCUMENTED*` | *CREATE … CLONE*: "cloning is not instantaneous, particularly for large objects (databases, schemas, tables), and does not lock the object being cloned." A clone does not reflect DML applied while the clone is still running. |
| Consistency is nonetheless pinned: an omitted `AT`/`BEFORE` is set internally to the statement's start timestamp | `DOCUMENTED*` | *CREATE … CLONE*: "the cloning operation internally sets the AT clause value as the timestamp when the statement was initiated." |
| Clones **lose the source's prior history** — you cannot Time Travel a clone back past its creation | `DOCUMENTED*` | *Time Travel*: "historical data for the table clone begins at the time/point when the clone was created." |
| Grants on the *cloned container* are NOT copied; grants on *child objects* ARE | `DOCUMENTED*` | *object-clone*: "When you clone a source object such as a database, grants of privileges on the database are not copied to its clones. Privilege grants on all child objects… are copied to the clones." Use `COPY GRANTS` for the object itself. |

**Not cloned / cloned-with-caveats** (all `DOCUMENTED*`, from *Cloning considerations*):

| Object | Behaviour |
|---|---|
| External tables | **Not** cloned. A cloned row-access policy can survive while the external table it guards does not — "the policy in the cloned database refers to a table that is not present in the cloned database". |
| Internal named stages | **Not** cloned unless `INCLUDE INTERNAL STAGES` is given. Table stages are cloned as objects but **files in them are not copied**. |
| Pipes | Pipes referencing an **internal** stage are **not** cloned; pipes referencing an **external** stage **are**. `COPY GRANTS` needed to carry pipe ownership. |
| Streams | Cloned, but **unconsumed records in the clone's streams are inaccessible**. |
| Tasks | Cloned **suspended by default**. |
| Temporary tables | Cannot be cloned at all. |
| Sequences, tags, foreign keys | Cloned; FKs re-point at the cloned PK when both tables are in the cloned container. |
| **Views** | Cloned as definitions. **Unqualified** references resolve inside the clone; **fully-qualified** references keep pointing at the original objects. This is the load-bearing one — see §2.2 and §3. |

**Table type.** `DOCUMENTED*` — **permanent → transient clone is allowed**; **transient → permanent is not**
("you cannot clone a transient table to a permanent table"; `CREATE TRANSIENT TABLE foo CLONE bar COPY GRANTS;`
is given as valid syntax). This matters: `CREATE TRANSIENT DATABASE … CLONE <permanent db>` gives a clone whose
tables have **no Fail-safe**, capping the storage tail of an abandoned clone at ≤1 day of Time Travel on this
account's Standard Edition. Confirming evidence that the *reverse* direction bites in practice: **SQLMesh
issue #4079** — "Transient object cannot be cloned to a permanent object" — its Snowflake adapter emitted
`CREATE OR REPLACE TABLE` against a transient source and had to be taught to emit `CREATE OR REPLACE TRANSIENT
TABLE` (fixed in PR #4155). `DOCUMENTED` (I read the issue).

**The pinning cost nobody mentions.** `DOCUMENTED*` — `SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS.RETAINED_FOR_CLONE_BYTES`
exists precisely because "deleted bytes… no longer in Time Travel or Fail-safe, but still retained because clones
of the table reference the bytes". And "storage bytes are always owned by, and therefore billed to, the table where
the bytes were initially added". So a long-lived clone **pins source bytes that the source has already deleted**,
and the source's owner pays. A clone held open across a nightly `CREATE OR REPLACE TABLE` rebuild pins a whole
extra generation of that fact. This is the Snowflake analogue of the Delta Lake shallow-clone hazard
(`REPORTED`, Databricks: running `VACUUM` on the source makes shallow-clone reads raise `FileNotFoundException`)
— same coupling, opposite symptom: Delta breaks the clone, Snowflake bills the source.

### 2.2 Clones and shares — §7.1's specific worry, settled

**An imported (share) database cannot be cloned. Full stop.** `DOCUMENTED*` — *Consume imported data*:
"Creating a clone of an imported database or any schemas/tables in the database is not permitted."
Also: imported DBs are read-only, cannot be replicated, do not support Time Travel, and "properties, such as
TRANSIENT and DATA_RETENTION_TIME_IN_DAYS, do not apply".

**But that is not the shape of this estate's dependency, and it does not block T2.** The wiki records that
`TEST_DG1_GEP` is a *local* database on `OG35375` whose views reference `PROD_DG1_GEP.*` — the inbound share
mounted by GP-207. Cloning `TEST_DG1_GEP` clones view *definitions*; those definitions carry fully-qualified
`PROD_DG1_GEP.…` names, which keep resolving through the share subject to the cloning role's `IMPORTED PRIVILEGES`.
The estate already relies on this: `CREATE DATABASE QA_DG1_GEP_PREFECT CLONE TEST_DG1_GEP;` — annotated
"(inherits schemas + prod data share)" (`REPORTED`, `processes/distributed-workflow/active/navira/active/phase-0-prefect-foundation.md:195`).
That parenthetical is loose wording for a mechanism that does work.

**Three consequences that are *not* in the spec:**

1. **A concrete, falsifiable defect already written into the plan.** The same file, line 243 (and line 720),
   instructs: *"clone `PROD_DG1_GEP.<sellercloud_schema>` into a sandbox in `QA_DG1_GEP_PREFECT` via prod data
   share"* as GP-219 step 6. If `PROD_DG1_GEP` on `OG35375` is the imported share database, **that `CLONE` will
   fail** and must be a `CREATE TABLE … AS SELECT` — a real copy that costs warehouse compute and full storage,
   not a zero-copy clone. `REASONED` from the `DOCUMENTED*` limitation. **One statement settles it**:
   `CREATE TRANSIENT SCHEMA scratch.probe CLONE PROD_DG1_GEP.SELLERCLOUD_SQL;` — expect failure. Run it before
   anyone plans a reconciliation around the word "clone".
2. **A T2 clone is not a snapshot of the raw sources.** Everything upstream of the share is live and shared
   across all clones. The wiki records the share going *stale for 42 days* undetected (`CURRENT_MAIN_INVENTORY_PANDL`
   frozen at 2026-03-05 for 42 days, GP-208) and objects *dropping out of the share mid-day*
   (`CURRENT_REPORT_ALL_ORDERS_UK`, present 06:00 PDT, gone by 13:26 PDT, 2026-04-21). So two agents in two clones
   are reading the same moving, occasionally-broken dependency. **T2 gives write isolation, not read determinism.**
   A T2 run's evidence bundle must therefore pin what it read (`MAX(___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___)`
   and a row count per shared source), or a re-run is not comparable to the original.
3. **Promotion out of a clone silently breaks the *outbound* share.** `DOCUMENTED*` — *CREATE TABLE*: `COPY GRANTS`
   "copies all privileges, except OWNERSHIP, from the existing table to the new table… If the existing table was
   shared to another account, the replacement table is also shared." Without it, the replacement is a new object
   with no grants — it drops out of the share. The estate has this as a standing checklist item —
   *"`CREATE OR REPLACE TABLE/VIEW` removes them from the share… re-share the affected objects (FUSION_92 and
   DISH_DUER as of 2025-03-14)"* (`processes/deployment/client-release-checklist.md:30,39`) — and as a real
   incident. `DOCUMENTED*` + estate `REPORTED` agree exactly. **This is an APPROVE-plane requirement, not a
   nicety.**

### 2.3 Compute cost, honestly — and what can actually kill a runaway agent

**The estate's own numbers** (`REPORTED`, `concepts/architecture/snowflake-cost-analysis.md`, measured against
live `ACCOUNT_USAGE` 2026-07-28/29):

| Fact | Value |
|---|---|
| Edition / region / price | Standard, `AZURE_CANADACENTRAL`, **~$2.00–2.25 USD/credit** |
| Warehouse | one shared `COMPUTE_WH` per account, **X-Small = 1 credit/hour**, `AUTO_SUSPEND` 300→60 |
| Prod compute | 23.7 credits/day billed against **9.5 h/day** of query work → **~60% idle** |
| Non-prod compute | 24.1 → **~2.5 credits/day** after the fix; 93% idle before |
| Storage | 1.59 TB ≈ **$37/mo** vs **~$3,090/mo compute** → storage is **~2% of spend** |
| Fail-safe amplification | `PROD_DG1_GEP` holds **0.412 TB Fail-safe against 0.114 TB active** (3.6×), from hourly `CREATE OR REPLACE` |
| Resource monitors in place | **none** on either `COMPUTE_WH`; only a 2-credit/day cap on the reader account |

**So: clone storage divergence is a rounding error in this estate.** The `TRANSIENT`-facts lever across the
whole estate was measured at **~$9/mo**. An agent's clone will not move the bill through storage.

**What *does* move the bill is the 60-second minimum resume, and it is measured here.** `DOCUMENTED*`:
"Each time a warehouse is started or resumed, the warehouse is billed for 1 minute's worth of usage." The
estate measured what that costs a sporadic client: a Cube.dev poller hitting the warehouse every 180 s cost
**7.14 credits/day (~$460/mo) for 13 minutes of actual query work per fortnight** — ~405 resumes/day.

`DERIVED` — an agent is a poller with better manners. An agent session issuing ~200 statements over 45 minutes,
most gaps exceeding `AUTO_SUSPEND=60`, bills up to ~200 minutes ≈ **3.3 credits ≈ $7.50 per run**, nearly all
idle. **Three agents each on their own warehouse pay this three times; three agents sharing one warehouse pay
it roughly once, because their resumes overlap.** The economically correct T2 design is therefore *one shared
X-Small agent warehouse*, which is exactly what creates the compute conflict edge in §2.6. The AgentSpec's
`budget: {warehouse_credits: 2}` ≈ 2 h of X-Small ≈ **$4.50** — a sane number, but see below for what enforces it.

**Also non-obvious: the cheaper the warehouse gets, the more cloning costs.** `DOCUMENTED*` — cloud-services
credits are "charged only if the daily consumption of cloud services exceeds 10% of the daily usage of virtual
warehouses", calculated daily in UTC, and DDL/cloning is *entirely* cloud services. Non-prod now burns ~2.5
warehouse credits/day, so the free cloud-services allowance there is **~0.25 credits/day (~$0.55)**. Thrashing
clone-create/clone-drop on a deliberately-quiet account is the one way to make a "free" metadata operation bill.
`DERIVED`. Worth a `METERING_DAILY_HISTORY` check after the first week of T2, not a reason to avoid T2.

**The control ladder — what can bound an agent, ranked by how exact it is** (all `DOCUMENTED*`):

| # | Control | Granularity | Latency | Verdict |
|---|---|---|---|---|
| 1 | `STATEMENT_TIMEOUT_IN_SECONDS` on the agent's **user** | one statement | exact, at the second | **The only precise control.** Default 172800 (2 days). Settable at account/user/session/warehouse; **"the lowest non-zero value is enforced"**, so setting it on the user cannot be raised by the agent's session. Set this. |
| 2 | Role has USAGE on exactly one X-Small warehouse, **no `MODIFY`, no `CREATE WAREHOUSE`** | burn rate | structural | Caps burn at 1 credit/h/cluster. On **Standard Edition multi-cluster is unavailable**, so it cannot scale out either. A grant, not a request — the §4 argument, correctly applied. |
| 3 | `ALTER USER <agent> ABORT ALL QUERIES` / `ALTER WAREHOUSE … ABORT ALL QUERIES` | all of a user's / warehouse's queries | immediate | **This is the kill switch**, not the resource monitor. `SYSTEM$CANCEL_ALL_QUERIES` on another user needs OWNERSHIP on that user or OPERATE/OWNERSHIP on the warehouse — "the ACCOUNTADMIN role is not necessarily granted any of these". Grant the DECIDE plane OPERATE on the agent warehouse. |
| 4 | `STATEMENT_QUEUED_TIMEOUT_IN_SECONDS`, `LOCK_TIMEOUT` | queueing / locking | exact | `LOCK_TIMEOUT` default **43200 s (12 h)** — an agent can sit blocked for half a day by default. Lower it. |
| 5 | Resource monitor `SUSPEND` / `SUSPEND_IMMEDIATE` | per-warehouse, per-interval | **coarse and lagging** | See below. |
| 6 | Budgets / per-user quotas | per-user | minutes | **Cannot block warehouse spend at all** — see below. |

**Can a resource monitor kill a runaway agent query? Effectively no.** `DOCUMENTED*`, *Working with resource
monitors*, three sentences that settle it:
- "Resource monitors are **not intended for strictly controlling consumption on an hourly basis**… nor for
  setting precise limits on credit usage (i.e. down to the level of individual credits)."
- "the assigned warehouses **may take some time to suspend or disable, even when the action is Suspend
  Immediate**, thereby consuming additional credits."
- `SUSPEND` (not `_IMMEDIATE`) "waits for currently executing queries to finish… the warehouse continues to
  consume credits even after the quota is reached."
- Snowflake's own recommendation is to **build in a buffer** — "set a threshold to 90% instead of 100%".

`SUSPEND_IMMEDIATE` *does* cancel running statements — so it is a real control, just an imprecise, lagging,
**warehouse-wide** one. On a shared agent warehouse it suspends every agent at once. That is a shared-fate
coupling, i.e. another conflict edge (§2.6, edge 4).

**Budgets cannot help.** `DOCUMENTED*`, *Per-user quotas*: "warehouse scopes show custom actions only, because
**block enforcement doesn't apply to warehouses**. Block enforcement supports only the AI domains… Warehouse
spend can be tracked in a separate quota, but block enforcement doesn't apply to warehouses." And even where it
does apply: "enforcement is evaluated within minutes of a spend event rather than at request time, [so] a user
may briefly continue past their limit until the block lands."

**Telemetry is lagged, which matters for a cost governor.** `DOCUMENTED*` —
`ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY` latency **up to 180 minutes** (the `CREDITS_USED_CLOUD_SERVICES`
column **up to 6 hours**); `ACCOUNT_USAGE.QUERY_HISTORY` **up to 45 minutes**; **Information Schema views have
no latency**. A governor that reads `ACCOUNT_USAGE` learns about a runaway three hours late. Read the
`INFORMATION_SCHEMA.QUERY_HISTORY` table function instead. The estate independently hit this — its cost analysis
has a whole subsection on checking the metering watermark before believing a low number.

### 2.4 Prior art — what already productises this, and adopt-vs-build

| System | Does it solve "an agent may safely mutate data"? | Cost | Adoptable here? |
|---|---|---|---|
| **SQLMesh virtual data environments** — *closest to T2 by a distance* | **Yes, and more completely than the spec's T2.** Environments are "a collection of references to model snapshots"; each model *variant* gets its own physical table keyed by a fingerprint; environments hold only pointers. A **virtual update** — pointer swap when nothing needs recomputing — "imposes no additional runtime overhead or cost". Dev previews target "shallow (a.k.a. 'zero-copy') clones of production tables for engines that support them" (Snowflake does) or temp tables otherwise. `DOCUMENTED` (repo docs, read directly). | OSS. Tobiko Cloud is paid. | **Adopt the mechanisms, not the tool.** Adopting SQLMesh means rewriting `clients/*/snowflake/warehouse/**/*.sql` as SQLMesh models *and* replacing the Eclipse task-DAG JSON. That is a warehouse-framework migration, which `SYNTHESIS.md` rules out. **Steal four things:** fingerprint→physical-table so a rebuild is addressed by content; environment-as-pointer; `environment_ttl`/janitor (§2.5); optimistic locking on shared state (§2.6). |
| **dbt Cloud CI — `defer` + `state:modified`** | Partly. Builds only changed nodes; unselected upstreams resolve to production. Documented caveat is exactly the T2 hazard: "you may simultaneously query production and development datasets… development-specific filters might not exist in production, yielding more data than intended". `DOCUMENTED` (docs source read directly). | dbt Cloud paid tiers. | **No** — ALDC does not use dbt. But the **drop-on-PR-close trigger** is directly copyable and is *better than a TTL* because it is event-driven (§2.5). |
| **Recce** | No — it is a *review* surface (lineage, row-count/value/top-K/histogram diffs, checklists) over two dbt environments. `DOCUMENTED` (README read directly). | OSS + paid Cloud. | No (dbt-bound). Its **checklist artefact** is the right shape for the PROVE plane's evidence bundle. |
| **Datafold data-diff** | The technique (clone-vs-real row/value diff) *is* the T2 promotion evidence. | **OSS version deprecated May 2024** — "Datafold is no longer actively supporting or developing open source data-diff". Cloud from ~$799. `REPORTED`. | **Build the thin version.** The estate already does the 80% case — GP-219's acceptance is "row counts within < 1% variance vs legacy", using `COUNT(*)` + `SUM(<key_metric>)`. Formalise that, don't buy it. |
| **Y42 virtual data builds** | Yes, for humans: "automatic cloning of environments every time you create a new branch… you always work in an isolated zero-copy cloned environment". `REPORTED` (vendor blog). | Proprietary platform. | No. Useful only as proof the pattern is **productised and unoriginal** — which is a reason to build it small, not a reason to buy. |
| **lakeFS / Project Nessie / Delta shallow clone** | Yes, at the object-storage / Iceberg layer. Nessie: catalog-level Git branching, **"conflict detection is table level"**, merge rejected wholesale on conflict. `REPORTED`. | OSS. | **No** — ALDC's warehouse is native Snowflake tables, not Iceberg/S3. lakeFS lists Spark/Hive/Athena/DuckDB/Presto, not Snowflake. Keep Nessie's **table-level conflict detection** as the model for §2.6's conflict graph. |
| **Snowflake dev/test DB cloning** | This *is* T2. | Native. | **This is the answer, and the estate already runs it.** |

**Verdict on adopt-vs-build:** build, and build small. Everything above that would drop in cleanly requires
first migrating ALDC's warehouse layer to dbt or SQLMesh — a bigger change than the thing being enabled, and
one the prior research explicitly defers. The T2 surface that actually needs code is three pieces:
a provisioning statement, a **reaper task inside Snowflake**, and a diff. Steal SQLMesh's janitor semantics
and dbt Cloud's drop-on-close trigger rather than either codebase.

**The gap worth naming:** I found **no** productised system that gives an *LLM agent* a warehouse clone with
enforced teardown. The 2026 agent-sandbox literature is filesystem/microVM-shaped (Firecracker, gVisor, V8
isolates; E2B/Modal/Daytona) and treats "database isolation" as an aspiration — "instantly clone and isolate
environments… utilise copy-on-write" `REPORTED`, vendor blog, no implementation. So T2 is a real gap, and the
estate is unusually well-placed to fill it because the clone half already works here.

### 2.5 Teardown — the unenforced promise, and what actually enforces it

**"The agent drops it on exit" is exactly the class of promise this programme rejects, and the estate has
already measured it failing.** `REPORTED` (`snowflake-cost-analysis.md` §4): sprawl in
`aldc-launchpad/warehouse_ops/` — 42 rollback / 14 shadow / clone scripts, per-run timestamped Lectric clones,
a whole-DB clone script, `_RB`/`_SHADOW`/`_BEFORE` copies from seven tickets, and **orphaned dev schemas
`WAREHOUSE_TEST_GP226`, `WAREHOUSE_TEST_NAVIRA_ROADMAP`, `WAREHOUSE_TEST_GP226_TEAM`**. The existing sandbox
pattern (`concepts/patterns/sandbox-feature-delivery.md`) specifies teardown as *"`deploy.py --teardown` drops
`WAREHOUSE_TEST_X`, or manually after the feature is validated"* — i.e. a promise — and the promise was not kept.

**Worse than sprawl: two of the orphans leaked into live production dependencies.** `WAREHOUSE_TEST_GP226` and
`_NAVIRA_ROADMAP` are referenced by `clients/GEP/snowflake/warehouse/marketing_fct_activity_consolidated.sql`,
and the daily Data Model reads them — the wiki's own instruction is *"reclassify, do not blind-drop"*. **A
sandbox that outlives its ticket does not merely waste storage; it becomes load-bearing.** That is the strongest
single argument in this whole report for making teardown a control rather than a step.

**Snowflake gives you nothing native.** `REPORTED` (multiple practitioner writeups, consistent; no vendor doc
found asserting a TTL and none found denying one — **could not verify** a native mechanism, and its absence is
consistent with every implementation guide building the same three-part workaround): *"Snowflake does not
support TTL natively, but it can be achieved by using Tagging, Transient Table, Stored Procedure and Tasks"* —
a scheduled task every 5–15 minutes that drops expired objects.

**What survives the agent process dying.** The reaper must be a **Snowflake task**, not a host process. This is
not my inference alone — the estate reached the same conclusion for cost alerting after measuring the problem:
*"put the highest-value alert **inside Snowflake** as a serverless task with `SYSTEM$SEND_EMAIL` — no external
host, no credentials, no availability gap"*, written specifically because the observability scheduler *"runs in
local Docker on a workstation… would have missed this entire incident during any week it was off"*. The same
argument applies verbatim to a clone reaper, and it applies **more** forcefully to the agent factory, whose
isolation unit is currently *a git worktree on the operator's Windows machine*.

**Key the reaper on something the agent cannot rename.** `DOCUMENTED*` — dbt Cloud drops
`DBT_CLOUD_PR_<job_id>_<pr_number>` schemas on PR close/merge, and its documented failure mode is precisely a
naming mismatch: *"if temporary schemas aren't dropping… you have overridden the `generate_schema_name` macro
and it isn't using `dbt_cloud_pr_` as the prefix"*. A naming convention is a promise wearing a uniform. Prefer
**object ownership**: the T2 role can only create objects owned by roles it holds, so
`SHOW DATABASES` → drop everything owned by `AGENT_T2_ROLE` whose `created_on` is older than N hours is a key
the agent cannot forge. (Object tags would also work and are what the practitioner pattern uses — but see §4:
I got **contradictory** answers on whether object tagging needs Enterprise Edition, and this account is Standard.
Ownership is edition-independent, so prefer it regardless.)

**Prior art's TTL numbers** (`DOCUMENTED`, SQLMesh config reference, read directly):
`environment_ttl` default **`in 1 week`**; `snapshot_ttl` default **`in 1 week`**; `sqlmesh janitor` runs
on demand with `--ignore-ttl` and `--force-delete`; `warn_on_delete_failure` defaults to **False**, i.e. a
failed drop is an **error**, not a warning. A week is far too long for an agent clone — hours, not days —
but the defaults tell you the shape: TTL + a sweeper + a loud failure when the sweep cannot complete.

**Make the tail cheap anyway, in case the reaper is late.** Create the clone as
`CREATE TRANSIENT DATABASE … CLONE <permanent>` (permitted; §2.1) with `DATA_RETENTION_TIME_IN_DAYS = 0`.
`DOCUMENTED*`: transient objects have **no Fail-safe period** and a Time Travel window of 0 or 1 day; permanent
tables carry a **non-configurable 7-day Fail-safe** that keeps billing after the drop, and this account's
Standard Edition caps Time Travel at 1 day anyway. That turns an abandoned clone's storage tail from
*1 + 7 days* into *~0*.

### 2.6 The §7.2 counter-claim — "data work does not conflict" is false

§7.2 flags this as `BET`. It loses. Here is the conflict graph for T2 data work, with what each edge is grounded in.

| # | Edge | Does a clone remove it? | Evidence |
|---|---|---|---|
| 1 | **Same repo file.** The DDL is a `.sql` file in `clients/GEP/snowflake/warehouse/`. Two agents editing one fact's SQL, or the shared task-DAG JSON (`task_warehouse_orderline.json`, root `TASK_WAREHOUSE_ORDERLINE_0`, 24×/day), or the build-order doc, conflict exactly as code lanes do. | **No.** T2 isolates the *runtime*, not the *source*. | `REPORTED` — estate file inventory; `concepts/patterns/circular-dependency-build-order.md` is a single global artefact. |
| 2 | **Same target object name / type.** Documented estate failure: `Object 'EXTRACT_WAREHOUSE_METADATA' already exists as TABLE` — a `CREATE OR REPLACE SECURE VIEW` at `extract_warehouse_metadata.sql:109` colliding with the hourly task that materialises the same name as a physical table. | **Within a clone, yes. At promotion, no** — both agents converge on `REPORT_COMMON`/`WAREHOUSE`. | `REPORTED` — `gep-snowflake-pbi-deployment.md:341`. |
| 3 | **Shared dimension tables** (`SHARED_DIM_PRODUCT`, `SHARED_DIM_PERIODICITY`). Two clones hold two copies; both agents pass in isolation; the incompatibility surfaces only at merge. | **No — it *defers* it**, which is worse than removing it, because both runs report green. | `REPORTED` — `concepts/architecture/star-schema-convention.md`, `concepts/business-logic/periodicity.md`. |
| 4 | **Shared compute.** One `COMPUTE_WH` per account, X-Small, `MAX_CONCURRENCY_LEVEL` default **8**, **no multi-cluster on Standard Edition** (Enterprise feature), and every fact is a full `CREATE OR REPLACE TABLE … AS SELECT` with zero incremental patterns. Concurrent agents queue and spill. A `SUSPEND_IMMEDIATE` monitor on that warehouse kills all of them together. | **No — and §2.3 says you should deliberately *share* the warehouse**, because per-agent warehouses multiply the 60-second-resume tax. | `DOCUMENTED*` (concurrency, editions) + `REPORTED` (estate: "One shared `COMPUTE_WH` per account"; "Zero incremental patterns"). |
| 5 | **The live inbound share.** All clones read one moving, occasionally-broken dependency (42-day freeze; mid-day object dropout). | **No.** | `REPORTED` — §2.2. |
| 6 | **The outbound share at promotion.** Every promoted `CREATE OR REPLACE` needs `COPY GRANTS` and a re-share check against a single shared list of shared objects. | **No** — this is an APPROVE-plane edge. | `DOCUMENTED*` + `REPORTED` — §2.2. |
| 7 | **Shared state store.** Prior art proves this edge is real even in a mature product: SQLMesh uses **optimistic locking on environment state** — two branches planning against one environment, the second fails and must rebase; and a state migration concurrent with a plan application "may lead to unexpected results, lost data intervals and even corrupted state". | **No** — whatever tracks which clone belongs to which run is itself contended. | `REPORTED` (practitioner writeup) + `DOCUMENTED` (SQLMesh issue #1383). |

**Net.** T2 removes edge 2 *within a run* and defers edge 3. It removes none of 1, 4, 5, 6, 7. So §4's
consequence 1 — *"T2 removes the file-conflict cap for data work… the 3-lane ceiling applies to T0 code lanes
and does not generalise"* — is wrong twice: the file cap is edge 1 and T2 does not touch it, and the ceiling
that replaces it is edge 4, a **compute** cap. `DERIVED`: the T2 ceiling is
`min(file-conflict independent set, warehouse concurrency budget)`, and on one X-Small warehouse running
full-rebuild DDL that budget is **plausibly 2–3** — i.e. **T2 may not raise the ceiling above 3 at all here**
without provisioning more compute, which is a money decision for the DECIDE plane, not a free consequence of
cloning. That is a testable prediction: run 1, 2, 3, 4 concurrent full-rebuild agents on one XS warehouse and
plot wall clock and `LOCK_WAIT_HISTORY` / queued time. If wall clock goes superlinear at 3, the ceiling is
confirmed and §4's headline claim is dead.

---

## 3. What this changes in the spec

Concrete edits to `github.com/ALDC-io/agent-factory`:

1. **`docs/specs/architecture-v0.md` §4, T2 row — change "clone schema" to "clone database."**
   `CREATE TRANSIENT DATABASE agent_<run_id> CLONE TEST_DG1_GEP;` + `USE DATABASE agent_<run_id>;`.
   **Reason (the single most actionable finding here):** ALDC warehouse DDL is *schema*-qualified and
   *database*-unqualified — `CREATE OR REPLACE TABLE WAREHOUSE.X AS SELECT …`,
   `CREATE OR REPLACE SECURE VIEW WAREHOUSE_SOURCE.<name> AS …` — and the wiki states the resolution rule
   explicitly: derived warehouse references are *"unprefixed, resolves to current DB, not via share"*
   (`snowflake-data-share-refresh.md`). A **schema** clone leaves the hard-coded `WAREHOUSE.` prefix pointing
   at the real schema and the sandbox is a no-op. A **database** clone redirects every unqualified write while
   leaving the fully-qualified `PROD_DG1_GEP.*` share reads correctly pointing at the real (read-only) share.
   This estate's SQL is, by luck, exactly the right shape for database-granular cloning and exactly the wrong
   shape for schema-granular cloning.

2. **§4 consequence 1 — retract it.** Replace *"Two agents in two clone schemas conflict on nothing"* with the
   seven-edge table from §2.6 and the ceiling formula
   `min(file-conflict independent set, warehouse concurrency budget)`. Retag from `DERIVED` to `REASONED`,
   with the 1/2/3/4-agent experiment named as what would make it `MEASURED`.

3. **§4 T2 row, "Cost" cell** — currently *"clone is cheap; compute is not"*. Make it precise:
   *clone creation = 0 warehouse credits, non-zero cloud-services credits (free only up to 10% of that day's
   warehouse credits — ~0.25 credits/day on non-prod); validation compute is dominated by the 60-second
   minimum per warehouse resume, measured at 7.14 credits/day for one 180 s poller in this estate.*

4. **§5 `AgentSpec` — `budget.warehouse_credits: 2` has no enforcer. Add the fields that do:**
   ```yaml
   tier: T2
   warehouse: AGENT_WH_XS          # role has USAGE only; no MODIFY, no CREATE WAREHOUSE
   statement_timeout_s: 900        # set on the agent USER; lowest non-zero wins
   lock_timeout_s: 300             # default is 43200 (12h)
   clone: {granularity: database, source: TEST_DG1_GEP, transient: true, retention_days: 0}
   budget: {tokens: 400k, wall_clock: 45m, warehouse_credits: 2}   # credits = telemetry, NOT a control
   ```
   And write down *why* `warehouse_credits` is telemetry: per-user quota block enforcement **does not apply to
   warehouses**, and resource monitors are documented as unsuitable for precise or hourly control. The kill
   switch is `ALTER USER <agent> ABORT ALL QUERIES` issued by the DECIDE plane, which needs OPERATE on the
   agent warehouse. §5's own rule — *"a spec with a field nothing reads is worse than no field… every field
   needs a test asserting it reaches the process"* — applies to `warehouse_credits` today.

5. **§7.1 — mark settled, and replace the worry.** The clone is cheap; the share does not misbehave the way
   feared. Substitute the two real share findings: (a) an **imported** share DB cannot be cloned, which
   invalidates GP-219 step 6 as written in
   `processes/distributed-workflow/active/navira/active/phase-0-prefect-foundation.md:243`; (b) promotion
   needs `COPY GRANTS` + a re-share check or objects silently leave the outbound share.

6. **§8 sequence — insert 6a *before* 6: "reaper task inside Snowflake."** A Snowflake task + stored procedure
   that drops every database owned by the T2 agent role older than N hours, running on Snowflake's own
   scheduler so it survives the agent, the container, and the operator's laptop being shut. **No clone should
   be created before the thing that drops it exists** — the estate has three orphaned sandbox schemas and two
   of them are now read by a production model.

7. **§9 "What this does not change" — add a fourth bullet.** *Promotion out of a clone uses
   `CREATE OR REPLACE … COPY GRANTS` and re-verifies share membership afterwards.* This is the estate's
   existing release checklist, promoted from a human checklist to a machine gate — which is exactly the
   "mechanically producible evidence" §4 consequence 3 asks for, and it is the one gate with a documented
   recurring failure to point at.

8. **`factory/claims.py`** — §6 records it as *"refuses overlap, does not auto-expire"*. Two changes: add
   `warehouse` as a claimable resource (edge 4 is real and needs scheduling), and note that the T2 clone is
   the first resource where **auto-expiry is the whole point**, so the claims TTL and the Snowflake reaper
   should share one deadline rather than being two independent promises.

9. **`factory/lanes.py` docstring** — it says *"The binding constraint is **file locality**, not the dependency
   graph."* For T2 that becomes *file locality **and** warehouse concurrency*. The file is explicit that lane
   grouping is `ASSUMED`; T2 adds a second assumed dimension that should be labelled the same way.

10. **T2 does not need the container to start.** §7.4 flags Windows/WSL containers as unmeasured, and §8
    sequences T2 (item 6) after the container (item 4). But the clone-and-role half of T2 is entirely
    server-side: a role with no grant on the real database, plus a clone, plus a statement timeout. That can
    be built and *watched refusing something* — feeding the `refuses` gate, currently **0 of 22** — before any
    container exists. Suggest splitting item 6 into **6a reaper**, **6b clone + scoped role (no container)**,
    **6c container-hosted T2**.

---

## 4. What I could not settle

- **Verbatim Snowflake wording.** `docs.snowflake.com` is egress-blocked from this session. Every
  `DOCUMENTED*` claim is the search tool's rendering of the reference page, not a quote I verified in context.
  **What would settle it:** open the four pages from an unblocked machine — `user-guide/object-clone`,
  `sql-reference/sql/create-clone`, `user-guide/resource-monitors`, `user-guide/data-share-consumers` — or run
  the probes in the next bullet.
- **Object tagging and Snowflake Edition — a live contradiction.** One search of the vendor docs returned
  *"All accounts can now create and set object tags regardless of the account's edition"*; another returned
  *"Object tagging requires Enterprise Edition or higher"*. This account is **Standard**. I could not resolve
  it and I am not going to guess. It only matters if the reaper keys on tags — which is why §2.5 recommends
  keying on **object ownership** instead, which is edition-independent. `SHOW TAGS;` on `OG35375` settles it
  in one statement.
- **Whether `PROD_DG1_GEP` on `OG35375` is an imported share database.** My §2.2 conclusion — that the GP-219
  step-6 `CLONE` is not executable — depends on it. Everything in the wiki points that way ("GP-207 inbound
  share — mounted permanently", "configured manually in the Snowflake **prod** UI (not defined in the repo)"),
  but I did not run `SHOW DATABASES` to see the `origin` column. **One statement settles it:**
  `SHOW DATABASES LIKE 'PROD_DG1_GEP';` — a non-empty `origin` means imported, means no clone.
- **Actual clone wall-clock at this estate's scale.** Docs say cloning is "not instantaneous, particularly for
  large objects" but give no number, and `TEST_DG1_GEP`'s object count is unknown to me. If a database clone
  takes minutes, T2's start-up cost is a real scheduling input. **Settle it:** time
  `CREATE TRANSIENT DATABASE probe CLONE TEST_DG1_GEP;` once, then `DROP DATABASE probe;`. Cost: one DDL
  statement, no warehouse.
- **The T2 concurrency ceiling.** §2.6 predicts 2–3 on one X-Small; it is `DERIVED`, not measured. **Settle
  it:** run 1/2/3/4 concurrent full-rebuild agents against the shared XS and plot wall clock, queued time
  (`INFORMATION_SCHEMA.QUERY_HISTORY`) and `LOCK_WAIT_HISTORY`. This is the single measurement that decides
  whether T2 raises the ceiling at all — and it is cheap, because everything runs against clones.
- **`SUSPEND_IMMEDIATE`'s real latency.** Docs say "may take some time" and refuse a number. I found no
  vendor or practitioner figure. **Could not verify.** Since §2.3 concludes the monitor is not the kill switch
  anyway, this is a nice-to-know; if someone wants it, provoke it once and read `WAREHOUSE_EVENTS_HISTORY`.
- **Whether promotion actually needs a re-share for *views* as well as tables.** The `COPY GRANTS` sentence I
  retrieved is from `CREATE TABLE`; the estate's checklist says "table/view" and the 2026-04-21 incident was a
  table. `CREATE VIEW` also supports `COPY GRANTS` but I did not verify the shared-object sentence for views.
- **Cost of the reaper itself.** A serverless task firing every 5–15 minutes costs credits. I did not price
  it. Given non-prod runs at ~2.5 credits/day, a 15-minute serverless sweep is not obviously negligible against
  that base and should be measured before the cadence is chosen.

---

## 5. Sources

**Snowflake reference documentation** (retrieved via search index; direct fetch blocked by egress policy):
- https://docs.snowflake.com/en/user-guide/object-clone — Cloning considerations
- https://docs.snowflake.com/en/sql-reference/sql/create-clone — CREATE `<object>` … CLONE
- https://docs.snowflake.com/en/sql-reference/sql/create-table — CREATE TABLE (`COPY GRANTS`, shared objects)
- https://docs.snowflake.com/en/user-guide/data-share-consumers — Consume imported data
- https://docs.snowflake.com/en/user-guide/data-sharing-intro — About Secure Data Sharing
- https://docs.snowflake.com/en/user-guide/resource-monitors — Working with resource monitors
- https://docs.snowflake.com/en/sql-reference/sql/create-resource-monitor — CREATE RESOURCE MONITOR
- https://docs.snowflake.com/en/user-guide/budgets/per-user-quotas — Per-user quotas
- https://docs.snowflake.com/en/user-guide/cost-controlling-controls — Cost controls for warehouses
- https://docs.snowflake.com/en/user-guide/cost-understanding-compute — Understanding compute cost (cloud services 10%)
- https://docs.snowflake.com/en/sql-reference/parameters — STATEMENT_TIMEOUT_IN_SECONDS, LOCK_TIMEOUT, MAX_CONCURRENCY_LEVEL
- https://docs.snowflake.com/en/user-guide/performance-query-warehouse-max-concurrency — Limiting concurrently running queries
- https://docs.snowflake.com/en/sql-reference/transactions — Transactions and locking
- https://docs.snowflake.com/en/sql-reference/functions/system_cancel_all_queries — SYSTEM$CANCEL_ALL_QUERIES
- https://docs.snowflake.com/en/user-guide/warehouses-overview — Warehouse sizes / credits per hour
- https://docs.snowflake.com/en/user-guide/warehouses-multicluster — Multi-cluster (Enterprise only)
- https://docs.snowflake.com/en/user-guide/intro-editions — Snowflake editions
- https://docs.snowflake.com/en/user-guide/data-time-travel — Time Travel (Standard = 0 or 1 day)
- https://docs.snowflake.com/en/user-guide/data-failsafe — Fail-safe (non-configurable 7 days)
- https://docs.snowflake.com/en/user-guide/tables-temp-transient — Temporary and transient tables
- https://docs.snowflake.com/en/user-guide/data-cdp-storage-costs — Time Travel and Fail-safe storage costs
- https://docs.snowflake.com/en/sql-reference/account-usage/table_storage_metrics — RETAINED_FOR_CLONE_BYTES
- https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_metering_history — 180 min latency
- https://docs.snowflake.com/en/sql-reference/account-usage/query_history — 45 min latency
- https://docs.snowflake.com/en/user-guide/object-tagging/introduction — object tagging (edition requirement **contradictory**)

**Read directly (unblocked):**
- https://github.com/TobikoData/sqlmesh — SQLMesh
- https://raw.githubusercontent.com/TobikoData/sqlmesh/main/docs/concepts/environments.md — virtual environments
- https://raw.githubusercontent.com/TobikoData/sqlmesh/main/docs/concepts/plans.md — virtual update vs backfill
- https://raw.githubusercontent.com/TobikoData/sqlmesh/main/docs/reference/configuration.md — `environment_ttl`, `snapshot_ttl`, janitor
- https://github.com/TobikoData/sqlmesh/issues/4079 — "Transient object cannot be cloned to a permanent object"
- https://github.com/TobikoData/sqlmesh/issues/1383 — state migration vs concurrent plan application
- https://raw.githubusercontent.com/dbt-labs/docs.getdbt.com/current/website/docs/reference/node-selection/defer.md — dbt defer
- https://raw.githubusercontent.com/DataRecce/recce/main/README.md — Recce
- https://raw.githubusercontent.com/datafold/data-diff/master/README.md — data-diff (deprecated May 2024)
- https://raw.githubusercontent.com/treeverse/lakeFS/master/README.md — lakeFS

**Secondary / practitioner (`REPORTED`):**
- https://docs.getdbt.com/docs/deploy/ci-jobs — dbt Cloud CI temporary schemas `DBT_CLOUD_PR_<job>_<pr>`
- https://github.com/dbt-labs/dbt-core/issues/3189 — PR temporary schema not removed at PR close
- https://www.y42.com/blog/virtual-data-builds-one-data-warehouse-environment-for-every-git-commit — Y42 per-branch clones
- https://docs.databricks.com/aws/en/delta/clone — Delta SHALLOW CLONE + VACUUM hazard
- https://projectnessie.org/ — Nessie table-level conflict detection
- https://sqlmesh.readthedocs.io/en/stable/reference/cli/ — `sqlmesh janitor`
- https://www.datafold.com/blog/the-lowdown-open-source-data-diff-vs-datafold-cloud/ — data-diff status/pricing
- https://medium.com/snowflake/kill-those-snowflake-tables-3e202d51e557 — tag + task + proc TTL pattern

**Estate (read-only, `/home/user/wiki` and `/home/user/agent-factory`):**
- `concepts/architecture/snowflake-cost-analysis.md` — measured credit/storage baseline, sandbox sprawl, orphan leak
- `concepts/architecture/snowflake-data-share-refresh.md` — share refresh, 42-day freeze, unprefixed resolution rule
- `concepts/patterns/sandbox-feature-delivery.md` — the existing per-feature schema pattern and its teardown promise
- `processes/deployment/client-release-checklist.md` — `CREATE OR REPLACE` drops objects from the share; re-share step
- `processes/deployment/gep-snowflake-pbi-deployment.md` — share gaps, mid-day dropout, view-vs-table name collision
- `processes/distributed-workflow/active/navira/active/phase-0-prefect-foundation.md` — GP-248 clone commands; GP-219 step 6
- `/home/user/agent-factory/docs/specs/architecture-v0.md`, `factory/lanes.py`, `blueprints/windsorai_gep.yaml`
