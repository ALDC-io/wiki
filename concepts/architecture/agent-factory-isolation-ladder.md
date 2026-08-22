---
tags: [architecture, spec, agent-factory, sandbox, snowflake, credentials, security, research]
aliases: [isolation ladder, T0 T1 T2, agent sandbox tiers, credential broker, ephemeral clone]
sources: [github.com/ALDC-io/agent-factory@feat/readiness-generator, agent-factory/docs/specs/architecture-v0.md, code.claude.com/docs/en/sandboxing, github.com/anthropic-experimental/sandbox-runtime, docs.snowflake.com/en/user-guide/object-clone]
created: 2026-08-22
updated: 2026-08-22
---

# Agent Factory — the Isolation Ladder and the Credential Boundary

**§5 and §6 of [[agent-factory-spec|Agent Factory — Design Spec v1]]**, split out because together
they run to four hundred lines and because they are the half of the design that decides *blast
radius*. Section numbering is continuous with the parent spec, so a reference to §9.6 or §14.3 is on
one of the sibling pages.

The one-sentence version: **an agent's isolation tier is chosen by what its task touches, and the
axis that matters for data work is not the kernel — it is the credential.**

Every claim is tiered — `MEASURED` · `DOCUMENTED` · `DOCUMENTED*` · `REPORTED` · `REASONED` · `BET`.
⚠ **`DOCUMENTED*` means a vendor reference page reached through a search index and never opened.**
See §18.2 on the parent page, and re-verify before staking a decision.

---

## 5. The isolation ladder — tier by what the task touches, not by what the agent is

**The load-bearing idea in this spec.** It survived the research pass. Its *headline consequence*
did not, and §5.7 is where it dies.

> An agent's isolation tier is chosen by **what its task touches**, declared in the AgentSpec,
> **admitted** by the DECIDE plane and **constructed** by the launcher.

⭐ **The opening claim, promoted from where it was buried in the control-plane answer:** *compute
isolation and credential blast radius are different problems. A Firecracker VM can perfectly
isolate the host and still allow the code inside it to delete every Azure resource that its
credential legitimately authorises.* `REPORTED`

For data work the credential is the axis that matters, and the generic sandbox literature answers
the other question. **A perfect microVM holding the operator's Snowflake password has the blast
radius of the whole warehouse.** That is why §6 is not an appendix to this section — it is the more
important half.

### 5.1 The four columns, and the fourth is what makes a tier arguable

| Tier | Environment | May touch | **What the workload cannot do to the control itself** |
|---|---|---|---|
| **T0** | worktree + sandbox runtime, `allowedDomains: []` | repo files only. No egress, no DB verbs, no warehouse variables in the environment | cannot restore egress: the network namespace is removed (Linux) / the kernel fence is keyed on a different account SID (Windows) |
| **T1** | sandbox + allowlisted egress + **read-only** warehouse role, credential held by a broker | repo + `SELECT` on real data | cannot mint a DDL credential — it was never issued, and the agent holds no secret to trade up with |
| **T2** | as T1, plus an **ephemeral clone *database*** and a role whose DDL grants stop at the clone | repo + full DDL/DML **inside the clone only** | cannot reach production objects: the role has no grant there, and the reaper that drops the clone runs on Snowflake's scheduler, not the agent's |

Two consequences survive intact. The third — the headline — does not.

1. **The dangerous verb is contained by construction, not by prompt.** *"Do not touch prod"* in a
   prompt is a **request**; a role with no grant on prod is a **control**. Formally this is
   capability-based security: the token names **verbs**, never an identity. `REASONED`
2. **Promotion out of a clone is an APPROVE-plane act** — and against a clone it becomes a
   **clone→real diff, mechanically producible from a T2 run** rather than assembled by hand.
3. ⛔ ~~*T2 removes the file-conflict cap for data work.*~~ **Retracted.** See §5.7.

### 5.2 ⚠ The T1 row must not over-claim, and the vendor says so

An egress allowlist **is not a confidentiality boundary**. Verbatim, from Anthropic's own security
limitations:

> *"Because the proxy makes its allow decision from the client-supplied hostname without inspecting
> TLS, code running inside the sandbox can potentially use **domain fronting** or similar techniques
> to reach hosts outside the allowlist."* — and *"Allowing broad domains such as `github.com` can
> create paths for data exfiltration."* `DOCUMENTED`

So T1's allowlist **contains accident and misconfiguration and is a speed bump against a determined
exfiltrator**. TLS termination does not close it either: the docs are explicit that it *"does not
add content filtering."* A tier that over-claims is worse than one that under-claims, because the
over-claim is the part that gets relied on.

Bypassability ranks cleanly, and only the last row is a control:

| Mechanism | Can the workload defeat it? |
|---|---|
| Proxy environment variables only | **Yes, trivially** — `unset HTTPS_PROXY` |
| DNS / FQDN allowlisting | **Yes** — connect to a literal IP, or use DoH |
| `iptables` **inside the container's own netns** | **Yes, if it holds `NET_ADMIN`** — and Anthropic's own reference devcontainer grants exactly that |
| A fence in a namespace or principal the workload **is not** | **No** |

⚠ **Budget for allowlist churn.** An allowlist right for connector migration is wrong for the next
ticket, and the failure mode is a **silent research gap, not an error**: a blocked host returns
nothing and the agent moves on. (Every `DOCUMENTED*` tag in the research behind this spec exists
because exactly that happened — the research sandbox blocked `docs.snowflake.com`.) T1 needs the
refusal surfaced into the agent's own transcript, and a standing "add a host" path, or it will be
switched off within a month.

### 5.3 ⭐ Containers on Windows are not required — an open risk, settled

The strawman listed *"T1/T2 assume containers on Windows via WSL2, unmeasured, start-up cost a
guess"* as a live risk. **Struck**, and replaced with a smaller one.

- **Claude Code's built-in Bash sandbox does not support native Windows** — *"The sandbox … runs on
  macOS, Linux, and WSL2. **Native Windows is not supported.**"* `DOCUMENTED`. So the MEASURED
  *"sandboxing: none"* is not an oversight; there was nothing to switch on.
- **`@anthropic-ai/sandbox-runtime` has a native Windows alpha needing neither WSL2 nor a
  container.** The sandboxed process runs under a dedicated `srt-sandbox` local account with a
  **Windows Filtering Platform egress fence keyed on that account's SID** and per-session ACEs on
  filesystem paths. Verbatim: *"a process that strips its proxy environment and connects directly is
  **blocked at the kernel**."* And running under a distinct SID *"structurally closes the
  surrogate-spawn class of escape"* — Task Scheduler, parent-process attribute reassignment, BITS,
  out-of-process COM. `DOCUMENTED`

**The replacement risk is smaller and cheap to close:** the Windows runtime is **alpha, unproven on
this machine**, the install is a one-time elevated step, and schannel's revocation checks go out
under the caller's token and are blocked by the fence — so schannel tools fail with
`CRYPT_E_REVOCATION_OFFLINE` until revocation is disabled per tool (`curl --ssl-no-revoke`,
`git -c http.schannelCheckRevoke=false`). **One afternoon settles it.**

Two pieces of folklore to stop repeating: *"WSL2 is a VM so it is a hard boundary"* is
**unverified** — there is published VM-escape work under the WSL2 backend that nobody here has
read. And **start-up cost is the wrong axis to choose on**: at a 45-minute run budget the difference
between a 150 ms microVM and a 2 s container is 0.07% of the run. Choose on identity and egress.

### 5.4 The tier is an input to construction, never a predicate that is evaluated

The strawman said the tier is *"enforced by the DECIDE plane"*. Wrong verb, and the distinction is
the whole control:

> **DECIDE *admits*. The launcher *constructs*.** A control plane that **checks** a tier is
> admission control; a launcher that **builds** the sandbox, the allowlist and the credential
> *from* the tier is the only version an agent cannot argue its way past.

The vendor draws exactly this line: permission decisions are evaluated before a command runs, *"[but]
the operating system enforces the sandbox boundary on the running process, so it holds regardless of
what the model chose to run and even if an allowed command does more than its name suggests."*
`DOCUMENTED`

**The rule: a T1 agent must have no code path to a T2 verb, because the T2 credential was never
minted and the T2 host was never in the allowlist.**

The pattern has a name worth stealing wholesale — **Kubernetes Pod Security Admission**: three named
levels declared as a label, enforced by a built-in admission controller, in three modes —
`enforce` / `audit` / `warn`. `DOCUMENTED*` **`audit` mode is how a refusal count becomes non-zero
without breaking anyone's day** (§5.9).

Implementation, cheapest honest version for one Windows machine:

- The launcher reads `tier:` and selects **one of three pre-built, immutable profiles**. It never
  merges a per-run override. The **resolved profile's hash goes into the run audit**, and a mismatch
  between declared tier and resolved profile is a refusal event.
- Pin it so a repository cannot relax it: managed settings + `allowManagedDomainsOnly` +
  `strictAllowlist`. The documented behaviour that mask entries *"are all ignored in a repository's
  `.claude/settings.json`"* is the correct pinning, not a limitation.
- **The test of whether the tier abstraction is right:** *if moving to cloud requires editing the
  AgentSpec, the tier was a deployment detail, not a capability.* Moving to Azure Container Apps
  Jobs should change only the launcher's target, the identity (managed identity + Snowflake workload
  identity federation instead of a broker-held key) and what "profile" resolves to — never the spec.
  `BET`

### 5.5 T2, in detail — cheap, yes; **schema-granular, no**

⭐ **The single most actionable finding in the whole research pass: §4 said "clone schema". It must
be "clone *database*".**

ALDC's warehouse DDL is **schema-qualified and database-*un*qualified** —
`CREATE OR REPLACE TABLE WAREHOUSE.X AS SELECT …` — and the estate states the resolution rule
outright: derived warehouse references are *"unprefixed, resolves to current DB, not via share"*.

- A **schema** clone leaves the hard-coded `WAREHOUSE.` prefix pointing at the **real** schema. The
  sandbox is a **no-op** — worse than absent, because it reads as isolation.
- A **database** clone plus `USE DATABASE` redirects every unqualified write, while fully-qualified
  `PROD_DG1_GEP.*` share reads keep resolving correctly.

```sql
CREATE TRANSIENT DATABASE agent_<run_id> CLONE TEST_DG1_GEP;
USE DATABASE agent_<run_id>;
```

This estate is, by luck, exactly the right shape for database-granular cloning and exactly the wrong
shape for schema-granular cloning. **And the mechanism is not speculative — it already runs in
production here** (`CREATE DATABASE QA_DG1_GEP_PREFECT CLONE TEST_DG1_GEP;`). `REPORTED`

**What is genuinely cheap** (`DOCUMENTED*` throughout — vendor reference pages reached through a
search index, not opened; **re-check each with one SQL probe before building on it**):

| | |
|---|---|
| Creation | metadata only — *"a new set of metadata pointing to the same micro-partitions"*, copy-on-write on modification |
| Warehouse credits at creation | **zero** — cloning is *"entirely metadata operations, meaning they use only cloud services compute"* |
| Storage at creation | *"close to zero"*; accrues only for micro-partitions unique to the clone |
| Consistency | an omitted `AT`/`BEFORE` is set internally to the statement's start timestamp |

**What bites, and none of it is in the strawman:**

- **Cloning is not instantaneous and does not lock the source.** A clone does not reflect DML applied
  while the clone is still running.
- **A clone loses the source's prior history** — you cannot Time Travel a clone back past its
  creation.
- **Grants on the cloned *container* are not copied**; grants on *child* objects are. Use
  `COPY GRANTS`.
- **Not cloned at all:** external tables (a cloned row-access policy can survive while the external
  table it guards does not), internal named stages unless `INCLUDE INTERNAL STAGES`, files in table
  stages, pipes on internal stages. **Streams clone but their unconsumed records are inaccessible.
  Tasks clone suspended. Temporary tables cannot be cloned.**
- ⚠ **Views are the load-bearing case.** Cloned as *definitions*: **unqualified** references resolve
  inside the clone; **fully-qualified** references keep pointing at the originals. That is precisely
  what makes the database-granular design work — and precisely what would make a careless
  fully-qualified rewrite silently escape the sandbox.
- **A long-lived clone pins source bytes the source has already deleted**, and *"storage bytes are
  always owned by, and therefore billed to, the table where the bytes were initially added"* — so
  the *source's* owner pays. A clone held open across a nightly `CREATE OR REPLACE` rebuild pins a
  whole extra generation of that fact.

### 5.6 Shares — half the worry was wrong, and there is a live defect in a written plan

**An imported (share) database cannot be cloned. Full stop.** *"Creating a clone of an imported
database or any schemas/tables in the database is not permitted."* `DOCUMENTED*`

**But that is not the shape of this estate's dependency, and it does not block T2.** `TEST_DG1_GEP`
is a *local* database whose views reference `PROD_DG1_GEP.*` — the inbound share. Cloning it clones
view definitions whose fully-qualified names keep resolving through the share.

Three consequences, and the first is a defect in a plan someone will otherwise execute:

1. ⛔ **`GP-219 step 6` as written is not executable.** *"Clone `PROD_DG1_GEP.<sellercloud_schema>`
   into a sandbox in `QA_DG1_GEP_PREFECT` via prod data share"* will **fail** if `PROD_DG1_GEP` is
   the imported share database, and must be a `CREATE TABLE … AS SELECT` — a real copy costing
   warehouse compute and full storage, not a zero-copy clone. **One statement settles it:**
   `CREATE TRANSIENT SCHEMA scratch.probe CLONE PROD_DG1_GEP.SELLERCLOUD_SQL;` — expect failure. Run
   it before anyone plans a reconciliation around the word "clone".
2. ⚠ **T2 gives write isolation, not read determinism.** Everything upstream of the share is live and
   shared across all clones — and this estate has measured that share going **stale for 42 days**
   undetected, and objects **dropping out of it mid-day**. So a T2 run's evidence bundle must **pin
   what it read** (a source watermark and a row count per shared source), or a re-run is not
   comparable to the original.
3. ⛔ **Promotion out of a clone silently breaks the *outbound* share.** `CREATE OR REPLACE` without
   `COPY GRANTS` produces a new object with no grants — it drops out of the share. The estate already
   carries this as a standing release-checklist item *and* as a real recurring incident. It becomes
   an **APPROVE-plane gate**, not a checklist line.

### 5.7 ⛔ The ceiling does not rise — "data work does not conflict" loses, and here are seven edges

The strawman tagged this `BET`. It loses.

| # | Conflict edge | Does a clone remove it? |
|---:|---|---|
| 1 | **Same repo file** — the DDL is a `.sql` file, and the task-DAG JSON and build-order doc are single global artefacts | **No.** T2 isolates the *runtime*, not the *source* |
| 2 | **Same target object name/type** — a real estate failure: `Object 'EXTRACT_WAREHOUSE_METADATA' already exists as TABLE` | Within a clone yes; **at promotion, no** |
| 3 | **Shared dimension tables** — two clones hold two copies, both agents pass in isolation | **No — it *defers* it, which is worse**, because both runs report green |
| 4 | **Shared compute** — one X-Small `COMPUTE_WH`, `MAX_CONCURRENCY_LEVEL` 8, **no multi-cluster on Standard Edition**, every fact a full `CREATE OR REPLACE TABLE AS SELECT` with zero incremental patterns | **No — and §5.8 says you should deliberately *share* the warehouse** |
| 5 | **The live inbound share** — one moving, occasionally-broken dependency for every clone | **No** |
| 6 | **The outbound share at promotion** — `COPY GRANTS` + a re-share check against one shared list | **No** — an APPROVE-plane edge |
| 7 | **Shared state store** — SQLMesh, a mature product, uses **optimistic locking on environment state**: two branches planning against one environment, the second fails and must rebase | **No** — whatever tracks which clone belongs to which run is itself contended |

**Net: T2 removes edge 2 within a run and defers edge 3. It removes none of 1, 4, 5, 6, 7.** So the
strawman's headline is wrong twice — the file cap is edge 1 and T2 does not touch it, and the
ceiling that replaces it is edge 4, a **compute** cap.

```
T2 ceiling  =  min( file-conflict independent set , warehouse concurrency budget )
            ≈  2–3  on one X-Small warehouse running full-rebuild DDL
```

⭐ **So T2 may not raise the ceiling above 3 at all** without provisioning more compute — which is a
**money decision for the DECIDE plane, not a free consequence of cloning.** `DERIVED`

**It is a testable prediction, and it should be tested before anything is built on it:** run 1, 2, 3
and 4 concurrent full-rebuild agents on one XS warehouse and plot wall clock against queued time. If
wall clock goes superlinear at 3, the ceiling is confirmed and the headline claim is dead for good.

### 5.8 Cost — the bill is not storage, it is the 60-second resume

| Estate fact | Value |
|---|---|
| Storage vs compute | 1.59 TB ≈ **$37/mo** against **~$3,090/mo** compute — storage is **~2% of spend** |
| Warehouse | one shared X-Small `COMPUTE_WH` per account, 1 credit/hour |
| Idle share of prod compute | **~60%** |
| Measured cost of a 180 s poller | **7.14 credits/day ≈ $460/mo** for *13 minutes of query work per fortnight* |

`REPORTED` — the estate's own cost analysis, measured against live `ACCOUNT_USAGE`.

**Clone storage divergence is a rounding error here.** What moves the bill is the documented rule
that *"each time a warehouse is started or resumed, the warehouse is billed for 1 minute's worth of
usage."*

`DERIVED` — an agent is a poller with better manners: ~200 statements over 45 minutes, most gaps
exceeding `AUTO_SUSPEND`, bills up to ~200 minutes ≈ **3.3 credits ≈ $7.50 per run**, nearly all
idle. **Three agents on three warehouses pay that three times; three agents sharing one warehouse
pay it roughly once**, because their resumes overlap. So the economically correct T2 design is *one
shared X-Small agent warehouse* — which is exactly what creates conflict edge 4. The cheap design
and the parallel design are in direct tension, and that tension is the real T2 finding.

⚠ **Non-obvious: the cheaper the warehouse gets, the more cloning costs.** Cloud-services credits are
free only up to 10% of that day's warehouse credits. Non-prod now burns ~2.5 warehouse credits/day,
so the free allowance is **~0.25 credits/day**. Thrashing clone-create/clone-drop on a deliberately
quiet account is the one way to make a "free" metadata operation bill. Check the metering history
after the first week of T2.

**What can actually bound a runaway agent** — ranked by how exact it is:

| # | Control | Verdict |
|---:|---|---|
| 1 | `STATEMENT_TIMEOUT_IN_SECONDS` **on the agent's user** | **The only precise control.** Default **172800 s (48 hours)**. *"The lowest non-zero value is enforced"*, so a session cannot raise it |
| 2 | Role with `USAGE` on exactly one X-Small warehouse, no `MODIFY`, no `CREATE WAREHOUSE` | Structural. Caps burn at 1 credit/h; Standard Edition has no multi-cluster to scale out with |
| 3 | `ALTER USER <agent> ABORT ALL QUERIES` | **This is the kill switch.** Grant the DECIDE plane `OPERATE` on the agent warehouse |
| 4 | `LOCK_TIMEOUT` | Default **43200 s (12 h)** — an agent can sit blocked for half a day. Lower it |
| 5 | Resource monitors | *"Not intended for strictly controlling consumption on an hourly basis"*; *"may take some time to suspend… even when the action is Suspend Immediate"*. Warehouse-wide, so on a shared warehouse it kills every agent at once |
| 6 | Per-user quotas / budgets | **Cannot help — block enforcement explicitly does not apply to warehouses** |

⛔ **Therefore `budget: {warehouse_credits: 2}` is telemetry, not a control** — and by the spec's own
rule (*a field nothing reads is worse than no field*), it must either be enforced by (1)–(3) or
labelled as telemetry in the AgentSpec.

⚠ **And a cost governor must not read `ACCOUNT_USAGE`:** its metering history lags **up to 180
minutes** (cloud-services columns up to 6 hours) and query history up to 45. **Information Schema
has no latency.** A governor reading `ACCOUNT_USAGE` learns about a runaway three hours late.

### 5.9 Teardown is a control, not a step — and the estate already watched the promise fail

**"The agent drops it on exit" is exactly the class of promise this programme rejects.** Snowflake
gives you nothing native: there is **no TTL**, and every practitioner guide builds the same
three-part workaround — a tag or an ownership key, a transient object, and a scheduled task.

⛔ **The estate has already measured the promise failing.** The existing sandbox pattern specifies
teardown as *"`deploy.py --teardown` drops `WAREHOUSE_TEST_X`, or manually after the feature is
validated"* — a promise — and it was not kept: three orphaned dev schemas
(`WAREHOUSE_TEST_GP226`, `WAREHOUSE_TEST_NAVIRA_ROADMAP`, `WAREHOUSE_TEST_GP226_TEAM`), **two of
which are now referenced by a production model that the daily Data Model reads.** `REPORTED`

> **A sandbox that outlives its ticket does not merely waste storage — it becomes load-bearing.**
> That is the strongest single argument for making teardown a control.

Four rules follow:

1. **The reaper is a Snowflake task, not a host process.** It must survive the agent, the container
   and the operator's laptop being shut. The estate reached the same conclusion for cost alerting
   after measuring the problem — an external scheduler *"runs in local Docker on a workstation…
   would have missed this entire incident during any week it was off"* — and the argument applies
   *more* forcefully here, where the isolation unit is a git worktree on that same laptop.
2. **Key it on object ownership, not naming.** A naming convention is a promise wearing a uniform,
   and dbt Cloud's documented failure mode is exactly a prefix mismatch. `SHOW DATABASES` → drop
   everything owned by the T2 role older than N hours is a key the agent cannot forge. (Object tags
   would also work, but the vendor docs returned **contradictory** answers on whether tagging needs
   Enterprise Edition, and this account is Standard. Ownership is edition-independent.)
3. **Make the tail cheap in case the reaper is late.** `CREATE TRANSIENT DATABASE … CLONE
   <permanent>` is permitted and gives tables with **no Fail-safe**; with `DATA_RETENTION_TIME_IN_DAYS
   = 0` the storage tail of an abandoned clone goes from *1 + 7 days* to *~0*.
4. **A failed sweep is an error, not a warning.** SQLMesh's janitor defaults
   `warn_on_delete_failure` to **False** for exactly this reason. Its `environment_ttl` default of
   *one week* is far too long for an agent clone — hours, not days — but the shape is right: TTL, a
   sweeper, and a loud failure when the sweep cannot complete.

⛔ **No clone is created before the thing that drops it exists.** That ordering is not a preference;
it is the lesson of the two orphans that are now production dependencies.

### 5.10 Adopt or build

**Build, and build small.** The closest prior art by a distance is **SQLMesh virtual data
environments** — environments as pointers to fingerprinted model snapshots, a virtual update that
*"imposes no additional runtime overhead or cost"*, and dev previews targeting *"shallow (a.k.a.
'zero-copy') clones of production tables"*. `DOCUMENTED`. It solves T2 **more completely than this
spec does.**

And adopting it means rewriting every warehouse `.sql` as a SQLMesh model *and* replacing the
Eclipse task-DAG JSON — a warehouse-framework migration, bigger than the thing it enables, and
already ruled out (§15). **Steal four mechanisms instead:** fingerprint→physical-table so a rebuild
is addressed by content; environment-as-pointer; the janitor semantics in §5.9; optimistic locking
on shared state. From dbt Cloud, steal the **drop-on-PR-close trigger** — event-driven beats a TTL.
Do not buy Datafold: its OSS `data-diff` was **deprecated in May 2024**, and the estate already does
the 80% case by hand (*"row counts within < 1% variance vs legacy"*) — formalise that.

⭐ **The gap worth naming: no productised system anywhere gives an *LLM agent* a warehouse clone
with enforced teardown.** The 2026 agent-sandbox literature is filesystem- and microVM-shaped and
treats database isolation as an aspiration. So T2 is a real gap, and this estate is unusually
well-placed to fill it because the clone half already works here.

### 5.11 What is actually built today

**Nothing.** `MEASURED` — agents run as the operator, on the operator's Windows machine, with the
operator's credentials; no dry-run gate, no row-count diff, no rollback capture. T0's isolation is a
git worktree, which isolates *files* and nothing else: **a T0 agent today can reach the network and
holds every credential the operator holds.** T0 as specified above does not exist either.

⭐ **But T2's server-side half needs no container to start.** A role with no grant on the real
database, a clone, a statement timeout and a reaper are entirely server-side — buildable, and
**watchable refusing something**, before any sandbox runtime exists. That is why §14 splits it.

### 5.12 ⛔ The first drill — and the gate that would certify itself

The most copyable artefact in the whole research pass is eleven lines of shell in Anthropic's own
devcontainer: a **two-sided assertion at sandbox boot** that refuses to finish booting if either
side is wrong — a blocked host is reachable, **or** an allowed host is not. `DOCUMENTED`

```bash
if curl --connect-timeout 5 https://example.com >/dev/null 2>&1; then
    echo "ERROR: Firewall verification failed - was able to reach https://example.com"; exit 1
...
if ! curl --connect-timeout 5 https://api.github.com/zen >/dev/null 2>&1; then
    echo "ERROR: Firewall verification failed - unable to reach https://api.github.com"; exit 1
```

A negative control **and** a positive control, on every run, non-zero exit on failure. Copy it per
tier — including a T2 version that attempts a write against the *real* database and requires the
refusal.

⛔ **But not into gate `refuses` as currently written.** `factory/readiness.py::g_gates_can_refuse`
counts *any* all-time event whose type contains the substring `reject`, with **no distinction
between a refusal provoked on purpose and one that happened because something real was attempted.**
Satisfy it with boot-time drills and you have built **a gate that certifies itself** — the exact
shape of the 233-diagnoses-0-fixes agent and the loop that recorded its own 1.6% and never adjusted.
`MEASURED`

**The fix is small and non-negotiable: two counters, not one.**

- `refusals_organic` — a control said no to something the agent actually tried
- `refusals_drilled` — a deliberate negative control, carrying a `drill_id`

Require **both** non-zero, and **FAIL when the newest drill is older than the measurement window**,
not only when the count is zero. *A stale drill and a never-run drill are the same evidence.*
---

## 6. Capability and credentials — the plane the generic sandbox literature does not address

**Credentials are the whole job.** A data agent needs warehouse, API and vault access by
definition, so every sandbox story that assumes *"no network, no secrets"* answers a different
question than this one. The tier ladder in §5 is only a control if the credential attached to each
tier is a *different principal with different grants* — otherwise T1 and T2 are the same tier
wearing different labels.

### 6.1 The three rules

1. **The operator's credential is never the agent's credential.** Today it is. `MEASURED`
2. **Per-secret grant stays human** (I6). No tier self-serves a credential; a tier *requests*, a
   human *grants*, and both the grant and the refusal are recorded.
3. **A grant is scoped and expires.** A credential that outlives the run it was issued for is a
   standing grant with extra steps.

### 6.2 What this buys that a prompt cannot

The estate's blast-radius problem is not the filesystem. `git revert` does not undo a `CREATE OR
REPLACE` that stripped ownership and a share grant, and it does not un-invoice a client against a
number that silently changed. A role with no grant on production is the only version of *"do not
touch prod"* that is a control rather than a request.

**And it is measurable in a way a prompt is not:** a refused verb produces an audit event; a prompt
that worked and a prompt that was ignored look identical.

### 6.3 The broker — the agent stops holding a credential at all

⭐ **The single highest-value change in the sandbox programme is not T1's container. It is that the
agent holds no credential, and a broker outside the sandbox holds it and injects it on egress.**

This is not speculative. Three independent products converged on the same shape, and two can be
quoted directly: `DOCUMENTED`

| | The mechanism |
|---|---|
| Claude Code `sandbox.credentials` masking | *"the sandboxed command sees a per-session sentinel value instead of the real one … When a request leaves the sandbox for one of them, the sandbox proxy replaces the sentinel with the real value. The command and anything it logs never hold the real credential, but its requests still authenticate."* |
| Claude Code on the web | *"a separate proxy holds your GitHub token outside the sandbox while issuing scoped credentials for repository access inside it"* |
| Docker Sandboxes | the proxy injects stored credentials so *"the agent inside the sandbox never sees the raw key, only a placeholder"* |

**So I6 — per-secret grant stays human — survives and gets stronger.** With masking, the human
approves a **host**, not a secret handover, and the agent never holds the value. Two documented
constraints to build around: masking **requires TLS termination at the proxy**, and mask entries are
honoured only from user, managed or `--settings` scope — *"`mask` entries … are all ignored in a
repository's `.claude/settings.json`"*, which is exactly the right pinning.

**The generalisable name is the PDP/PEP split**: the *decision* point is a separate principal from
the *enforcement* point, and the enforcement point sits on the data path. Combined with capability
tokens, the agent presents a token naming **verbs**, never a credential naming an **identity**.

### 6.4 Snowflake has hard floors, and one default that makes T1 a lie

| Mechanism | Not the operator | Exactly one role | Expires | Mintable per run |
|---|---|---|---|---|
| **Key-pair (JWT)** | yes | not on its own | **JWT capped at 60 min**; the private key is long-lived | only if a broker holds the key |
| **PAT** | yes | **yes** — `ROLE_RESTRICTION` | ⛔ **minimum lifetime 1 day** | no — day granularity |
| **Snowflake OAuth** | yes | via scopes | **600 s, non-configurable** | yes |
| **External OAuth (Entra)** | yes | yes, if `EXTERNAL_OAUTH_ANY_ROLE_MODE = DISABLE` | per IdP; Entra defaults 60–90 min | yes |
| **Workload identity federation** | yes | via the bound user's role | **no credential at all** | n/a |
| **Vault dynamic secret** | yes — *a new Snowflake user per lease* | yes | default TTL **1 h**, max 24 h | **yes** |

`DOCUMENTED*` throughout — see §18.2 on what that tier means.

⛔ **The default that makes "T1 = read-only warehouse role" false.** Snowflake behaviour bundle
**2024_08** changed `DEFAULT_SECONDARY_ROLES` to default to `ALL`, and with `USE SECONDARY ROLES
ALL` *"the command doesn't validate role grants up front… the active secondary roles are determined
dynamically when each SQL statement executes."* **The effective privilege is the union of everything
the agent's user has been granted.** Two fixes, and do both: set `DEFAULT_SECONDARY_ROLES = ()` on
the agent user, **and** use a role-restricted PAT — with a restriction, *"secondary roles are not
used, even if `DEFAULT_SECONDARY_ROLES` is set to `('ALL')`."*

⚠ **Workload identity federation is the right end state and is not adoptable on the laptop.** WIF
binds to a workload's *platform* identity — AWS IAM, Entra, GCP service accounts, Kubernetes, GitHub
Actions. **A process on a bare Windows laptop has none.** WIF is therefore a reason to move the
T1/T2 runner onto Azure Container Apps Jobs with one user-assigned managed identity per tier ×
tenant; it is not a thing to wait for.

⚠ **Snowflake is retiring single-factor password sign-in**, and the milestone dates came back
**contested** across sources. If a deadline is live now this is a schedule input, not a
nice-to-have — §18.3.

### 6.5 The stack, cheapest first

| # | Step | Cost |
|---:|---|---|
| 1 | **The egress proxy holds the secrets and injects them** — masking + `injectHosts` + TLS termination | **~zero — it is configuration.** This alone ends *"agents run with the operator's credentials"* |
| 2 | **A local broker with its own identity** (~200 lines): holds the key-pair private key; checks the run's declared tier against a static table; mints a 60-minute JWT for that tier's role, or a role-restricted PAT it revokes on exit; **appends `granted` and `refused` to an append-only log** | days |
| 3 | **Azure managed identity + Snowflake WIF**, once the runner is off the laptop | weeks |
| 4 | Vault / OpenBao — only when the number of distinct secrets makes hand-rolling worse than operating a server | later |
| 5 | Teleport / SPIRE — **not for four people on one Windows machine** | never, at this size |

Steps 1 and 2 add **no marginal infrastructure** — both run on the same box. The real cost is
allowlist churn (§5.2).

⭐ **Step 2's refusal log is the point, not a side effect.** It is where gate `refuses` finally gets
an *organic* refusal to count, as opposed to a drilled one (§5.12).

### 6.6 What proves a deny actually denies

| Practice | What it gives |
|---|---|
| **Two-sided boot assertion** | the copyable artefact — §5.12 |
| **`opa test` coverage** | machine-checkable *"this deny has never fired"*: *"If the line refers to the head of a rule, the body of the rule was never true"* |
| **OpenFGA assertions** | store the `false` cases beside the model and run them in CI |
| **Pod Security Admission `audit` / `warn` modes** | run the policy non-enforcing and count what it *would have* refused — the cheapest honest route to a non-zero refusal count |
| **Security chaos engineering** | the named control-efficacy metrics are literally *"egress blocks, IAM denies, and segmentation hits"* |
| **Google DiRT** | annual multi-day drills *"to find vulnerabilities in critical systems and business processes by intentionally causing failures in them"* |

`DOCUMENTED*` / `REPORTED`. The estate already owns the principle at unit-test level —
`tests/test_evaluator_isolation.py`: *"a boundary nobody has watched reject something is a diagram,
not a control."* **The gap is that the principle stops at the unit tests and never reaches the
runtime gates.**

---

## See Also

[[agent-factory-spec]] · [[agent-factory-certification]] · [[agent-factory]] · [[orchestrator]] ·
[[prefect-connectors]] · [[snowflake-cost-analysis]] · [[sandbox-feature-delivery]] ·
[[snowflake-environment-provisioning]] · [[vacuous-verification]]
