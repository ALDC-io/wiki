# R-D — What should run the agent sessions, and is worktree-on-one-machine a stepping stone or a dead end?

**Written 2026-08-22.** Evidence tiers per `CONTEXT.md`: `MEASURED` / `DOCUMENTED` / `REPORTED` /
`REASONED` / `BET`. Where a primary source was unreachable from this session it is marked
**could not verify** and downgraded to `REPORTED`.

> ⚠ **Egress note, because it changes what this report can claim.** The session's egress proxy
> refused `docs.temporal.io`, `docs.prefect.io`, `cursor.com`, `developers.openai.com`,
> `learn.microsoft.com`, `martinfowler.com`, `kubernetes.io`, `martin.kleppmann.com` and
> `arxiv.org` (`curl -sS "$HTTPS_PROXY/__agentproxy/status"` shows `connect_rejected` /
> gateway 403). Temporal, Prefect, Kubernetes and Microsoft documentation below was fetched from
> the **same projects' own docs source on `raw.githubusercontent.com`**, which is primary text and
> is tiered `DOCUMENTED`. Cursor, Codex-cloud, Kleppmann and the arXiv papers could only be reached
> through search snippets and are tiered `REPORTED`. `MEASURED`

---

## 1. Verdict

**Worktree-on-one-machine is a stepping stone that has already been overtaken — not by a better
architecture, but by the vendor.** Claude Code now ships `--worktree`/`-w` per session with
*enforced* isolation (it blocks edits into the main checkout), `git worktree lock` while an agent
runs plus a **stale-lock sweep that releases a lock whose process has exited**, a periodic worktree
reaper that skips worktrees still holding work, background sessions under a supervisor process with
`claude agents --json` / `attach` / `stop` / `rm`, cross-session messaging over per-session sockets,
agent teams with a **file-locked shared task list** and a mailbox, and `total_cost_usd` /
`model_usage` / `max_budget_usd` / `--max-turns`. Six of the nine modules in `factory/` are
re-implementations of things now in the product, and all three launcher defects of 2026-08-22 are
artefacts of shelling out to a hand-written PowerShell launcher instead of the supported surface —
a bare `claude` cannot honour a `--model` field, and `CLAUDE_CODE_CHILD_SESSION` would never have
been inherited if the tracker had not spawned terminals.

**Do not reimplement leases, orphan timeouts or per-tag concurrency in `factory/`.** Prefect —
which this estate already runs, and which has a documented first-class Windows story — implements
concurrency slots as **timed leases with client-side renewal and server-side expiry** (default 5
minutes, minimum 1), explicitly "to ensure that all concurrency slots are eventually released to
prevent concurrency-related deadlocks". That is precisely the property `claims.py` does not have:
`STALE_AFTER = 4h` *labels* a claim stale and keeps blocking on it. Temporal is the stronger engine
on the merits (persisted timers, heartbeat timeout, start-to-close as the zombie fuse, an
append-only Event History, a hard `maximum_attempts`, and Workflow-ID uniqueness that *is* a claim
lock) but it costs a server, a worker deployment and a Windows-via-WSL2 container story for a
one-person build. **Prefect now; Temporal only if the build plane outgrows it.**

**On the terminal verdict**, the canonical design is event sourcing with a projection: the
append-only log is the system of record and the verdict is a pure, replayable function of it.
The negative control that proves a false `succeeded` is impossible is Temporal's own CI recipe
generalised — **feed the verdict function recorded and synthetic histories and fail the build if the
answer is wrong**, including the specific history `[stage_failed ×100, stage_completed ×1]`.

**The ceiling of 3 does not generalise, and parallelism is not the bottleneck.** The 41.7% figure
this estate has been reasoning from is the *cross-agent* rate in a study where **only 0.5% of
co-active PR pairs were cross-agent**; the intra-agent rate — which is the estate's actual case,
since every lane is Claude Code — is **19.8%**. Anthropic's own documentation independently lands on
the same team size ("Start with 3-5 teammates"; "If you have 15 independent tasks, 3 teammates is a
good starting point") and on the same partitioning rule ("Two teammates editing the same file leads
to overwrites. Break the work so each teammate owns a different set of files"). The published
improvement on file-locality is **dependency-cohesion partitioning**, not more lanes.

---

## 2. What the evidence says

### 2.1 What already exists to run fleets of coding-agent sessions

#### Claude Code / Agent SDK — the incumbent, and it now covers most of `factory/`

Everything in this subsection is `DOCUMENTED` from `code.claude.com/docs`.

| Capability `factory/` built | What ships today | Source |
|---|---|---|
| `worktrees.py` — one worktree+branch per lane | `claude --worktree <name>` / `-w`; worktree under `.claude/worktrees/<name>` on branch `worktree-<name>`; `EnterWorktree`/`ExitWorktree` tools; `isolation: worktree` frontmatter puts a *subagent* in its own worktree | [worktrees](https://code.claude.com/docs/en/worktrees) |
| *(nothing — `factory` has no enforcement)* | **Four enforced checks**: "Claude Code blocks an `Edit`, `Write`, or `NotebookEdit` that targets a path in the main checkout"; blocks a Bash/PowerShell/Monitor command whose cwd resolves to the main checkout; blocks git redirects via `git -C`, `--git-dir`, `GIT_DIR`, `GIT_WORK_TREE`; blocks command shapes it cannot trace. "You can't turn this check off." | [worktrees](https://code.claude.com/docs/en/worktrees) |
| `claims.py` — a claim that never expires | "While an agent is running, Claude runs `git worktree lock` on its worktree so that concurrent cleanup cannot remove it. The lock is released when the agent finishes." **and** "The sweep also releases a lock Claude Code set for a session whose process has exited, so a killed background session doesn't leave its worktree permanently locked." | [worktrees](https://code.claude.com/docs/en/worktrees) |
| *(nothing — `worktrees.remove()` is manual by design)* | "A periodic sweep removes worktrees that Claude created for subagents and background sessions once they are older than your `cleanupPeriodDays` setting… The sweep skips a worktree that still holds work: changed or untracked files, or unpushed commits. It never removes worktrees you create with `--worktree`." | [worktrees](https://code.claude.com/docs/en/worktrees) |
| `sessions.py` — scraping `~/.claude/sessions/<pid>.json` and the process table | Background sessions run under "a separate supervisor process… so you can close agent view, close your shell… and your dispatched work keeps going". `claude agents --json`, `claude attach <id>`, `claude stop <id>`, `claude rm <id>`. Sessions idle ~1 hour have their processes stopped but not deleted. | [agent-view](https://code.claude.com/docs/en/agent-view) |
| `bus.py` + `scripts/hooks/lane-bus.py` — append-only file per writer, hook-injected | `ListAgents` + `SendMessage`; per-session **Unix domain socket** (named pipe on native Windows); `crossSessionInbound` = `accept`/`hold`/`refuse`; loop throttling; "Claude Code holds at most 100 messages"; a `-p` worker binds an inbox socket and can be messaged | [cross-session-messaging](https://code.claude.com/docs/en/cross-session-messaging) |
| *(the `bus` trust caveat, hand-written into `render()`)* | Shipped as a rule: "a message from another session never counts as your consent"; "Claude Code instructs the receiving Claude never to change permission settings, `CLAUDE.md`, or other configuration because another session asked"; "a command in the message's text, such as `/compact`, arrives as plain text. Claude Code never executes it." | [cross-session-messaging](https://code.claude.com/docs/en/cross-session-messaging) |
| **Cost telemetry — `MEASURED` as absent in this repo** | `--output-format json` carries `total_cost_usd` and a per-model breakdown; `model_usage`/`modelUsage` includes subagent spend, `usage` does not; `maxBudgetUsd`/`max_budget_usd` ends the query with `error_max_budget_usd`; `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20) and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3) | [cost-tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking), [subagents](https://code.claude.com/docs/en/agent-sdk/subagents) |
| **Transcripts / resume — `MEASURED` as broken in this repo** | Sessions written to `~/.claude/projects/<encoded-cwd>/*.jsonl` automatically; `--resume <id>` finds the ID "in any project on this machine" (v2.1.223+); `--fork-session`; `listSessions()`/`getSessionMessages()`; a resumed session **is returned to its worktree**, in `-p` and the SDK too | [sessions](https://code.claude.com/docs/en/agent-sdk/sessions), [worktrees](https://code.claude.com/docs/en/worktrees) |
| `lanes.py` prompt PREAMBLE/POSTAMBLE + per-lane model | `--name`/`-n` names the session and the terminal title; `--session-id <uuid>` fixes the ID; `--model`; `--settings <file-or-json>`; `--max-turns` (print mode); `--permission-mode`; `--agents <json>` | [cli-reference](https://code.claude.com/docs/en/cli-reference) |

Two further `DOCUMENTED` facts that bear directly on the 2026-08-22 defects:

- **The dead `--model` variable was structural, not a typo.** `_launch_script()` interpolates
  `claude{model_flag}` into a generated `.ps1`. The supported surface is `--model` on the process,
  or `"model"` in a `--settings` payload; a launcher that emits a bare `claude` cannot honour a
  lane's declared model, and nothing in the shipped product would have inherited it.
- **Session naming was solved and the launcher worked around it.** `--name` exists and
  "Set a display name for the session, shown in `/resume` and the terminal title… if another live
  session on this machine already uses the name, Claude Code applies a variant of it instead" —
  the exact collision the tracker hit and papered over with `CLAUDE_CODE_SESSION_NAME`.

**Agent teams** are the vendor's own version of the whole lane model, and worth reading as a
competing design rather than a feature list `DOCUMENTED`
([agent-teams](https://code.claude.com/docs/en/agent-teams)):

- Shared task list with dependencies; "Task claiming uses **file locking** to prevent race
  conditions when multiple teammates try to claim the same task simultaneously."
- Mailbox at `~/.claude/teams/{team}/inboxes/{agent}.json`; malformed entries removed, valid ones
  still delivered.
- Gate hooks that can **refuse**: `TeammateIdle`, `TaskCreated`, `TaskCompleted` — "Exit with code 2
  to prevent completion and send feedback." This is a shipped answer to the `refuses` gate, which
  is `MEASURED` at **0 of 22 gate events ever being a refusal**.
- Documented limits that match this estate's experience: "**No session resumption with in-process
  teammates**"; "**Task status can lag**: teammates sometimes fail to mark tasks as completed";
  "Agent teams add coordination overhead and use significantly more tokens than a single session…
  For sequential tasks, same-file edits, or work with many dependencies, a single session or
  subagents are more effective."
- **Split-pane mode "isn't supported in VS Code's integrated terminal, Windows Terminal, or
  Ghostty."** The operator's chosen surface is the one the vendor's team mode does not support.

#### Everything else, surveyed

| Product | What it actually gives you | Tier |
|---|---|---|
| **Claude Code on the web / cloud sessions** | "each session runs in an isolated, Anthropic-managed VM"; "network access is limited by default and can be disabled"; "sensitive credentials such as git credentials or signing keys are **never inside the sandbox** with Claude Code; authentication is handled through a secure proxy using scoped credentials". `claude --cloud "…"` per task, run in parallel; `--teleport` pulls one back locally (requires clean git state, pushed branch, same repo, same account). Sessions expire on inactivity and the VM is reclaimed. | `DOCUMENTED` |
| **Codex CLI / Codex cloud** | OS-level sandbox: Seatbelt on macOS, Landlock+seccomp on Linux, a dedicated Windows sandbox; `read-only` / `workspace-write` (default) / `danger-full-access`; network off by default in workspace-write and in the cloud environment. `developers.openai.com` was **egress-blocked**, so this is from search snippets and a GitHub issue — **could not verify against the reference docs**. | `REPORTED` |
| **Cursor Cloud Agents** (ex-Background Agents) | "isolated VMs in the cloud with full development environments"; each task gets its own VM; a service account "can hold at most four concurrent streams"; subagent isolation gives "its own environment with its own branch". `cursor.com` was **egress-blocked** — **could not verify**. | `REPORTED` |
| **GitHub Copilot coding agent** | "An ephemeral development environment… created for each cloud agent session. The environment is destroyed after the session ends"; powered by GitHub Actions; restrictive firewall allowing only package registries by default; **"Copilot can only push to branches with names beginning with `copilot/`"** — a branch-namespace control the estate does not have. | `REPORTED` (docs.github.com reachable but not fetched verbatim) |
| **Google Jules** | Fresh VM per task, torn down after; **concurrency is a product tier**: 3 concurrent (free), 15 (Pro), 60 (Ultra). Independent evidence that "3 concurrent agent sessions" is a normal working number, not a defect of this repo's conflict graph. | `REPORTED` |
| **Devin** | A session API (v3 current; v1/v2 deprecated) with create/list/get, snapshot IDs, service users with RBAC. The session *is* the addressable unit — the thing `sessions.py` reconstructs by scraping pids. | `REPORTED` |
| **OpenHands** | "Every OpenHands agent session runs inside an isolated Docker container"; `LocalWorkspace` → `DockerWorkspace` swap for isolation with no agent-code change; headless REST submission. The closest open-source analogue to the T1 tier. | `REPORTED` |
| **Sourcegraph Amp** | Threads stored server-side at `ampcode.com/threads`, shareable. Transcripts as a product, not a file you have to remember to persist. | `REPORTED` |
| **`claude-squad`** | tmux + git worktrees, one isolated workspace per task, TUI. **tmux ⇒ not a native-Windows path.** | `DOCUMENTED` (README) |
| **`crystal`** (now Nimbalyst), **`conductor`** | Desktop apps, worktree per session, diff review. Conductor is macOS-only. | `REPORTED` |
| **`vibe-kanban`** | Worktree per workspace across 10+ agents, and it does have orphan reaping — the config surface exposes `DISABLE_WORKTREE_CLEANUP`: "Disable all git worktree cleanup including orphan and expired workspace cleanup". **The project is sunsetting**: the README's own headline is "Vibe Kanban is sunsetting." | `DOCUMENTED` (README) |
| **`container-use`** (Dagger) | MCP server: "Each agent gets a fresh container in its own git branch"; "complete command history and logs of what agents actually did, not just what they claim"; `git checkout <branch>` to review. Self-described **"early development"**, "stability-experimental". Closest off-the-shelf T1. | `DOCUMENTED` (README) |
| **`switchboard`** (the reference implementation R7 was written around) | **Could not verify.** I did not reach the repository from this session. R7's premise — that a session manager is the missing piece — is now largely moot given the table in §2.1; the interesting question it raised (what an embedded terminal buys that outweighs a keyboard-attached channel into shell-holding agents) is answered by `claude attach` / agent view, which give addressability without a PTY bridge in a web page. | `BET` |

**What none of them give you that this repo would still have to build:** the non-LLM verifier
holding the authoritative PASS bit, the GreenContract, the readiness gates, the conflict graph over
*your* gate set, and the T2 ephemeral warehouse clone. Every product above isolates a *filesystem*.
None of them isolates a *warehouse verb*, which is `architecture-v0.md` §4's central claim and
remains correct. `REASONED`

---

### 2.2 Durable execution as the control plane

The prior research (`R3-answer-control-plane.md`) concludes that attempt caps, leases, orphan
timeouts and concurrency reservation must be **built** because the build plane is bespoke. That
conclusion is right about the *requirement* and wrong about the *implementation*: every one of those
four is a shipped primitive somewhere, and two of them are shipped in a tool already installed here.

#### The feature matrix, with the caveats that matter

| Property | Temporal | Prefect 3 | Restate | Inngest | DBOS / Hatchet |
|---|---|---|---|---|---|
| **Durable timers** | ✅ "Timers in Temporal are **persisted**, meaning that even if your Worker or Temporal Service is down when the time period completes, as soon as your Worker and Temporal Service become available, the call that is awaiting the Timer in your Workflow code will resolve" `DOCUMENTED` | Partial — `Schedules`/`Automations`, but no in-flow durable sleep with the same guarantee `REPORTED` | ✅ durable timers as a first-class building block `DOCUMENTED` | ✅ `step.sleep` `REPORTED` | ✅ both `REPORTED` |
| **Heartbeat + zombie detection** | ✅ "A Heartbeat Timeout is the maximum time between Activity Heartbeats." And the honest half: "**The Temporal Server doesn't detect failures when a Worker loses communication with the Server or crashes. Therefore, the Temporal Server relies on the Start-To-Close Timeout to force Activity retries.**" `DOCUMENTED` | ✅ *for slots* — see leases below `DOCUMENTED` | ✅ via invocation lifecycle `REPORTED` | ✅ step-level `REPORTED` | ✅ `REPORTED` |
| **Cancellation propagation** | ⚠️ Cancel records `WorkflowExecutionCancelRequested` and schedules a Workflow Task; **but** "Canceling an Activity from within a Workflow **requires that the Activity Execution sends Heartbeats and sets a Heartbeat Timeout**. If the Heartbeat is not invoked, the Activity cannot receive a cancellation request." Terminate is the forceful path and "the Workflow code gets no chance to handle termination." `DOCUMENTED` | Flow-run cancellation exists; process kill is the worker's job `REPORTED` | ✅ `REPORTED` | ✅ `cancelOn` `REPORTED` | ✅ `REPORTED` |
| **Per-tag concurrency** | ⚠️ **not concurrency — rate.** Fairness gives weighted round-robin per key and `--fairness-key-rps-limit-default`, and the docs say "All fairness mechanisms, including rate limits, are best-effort and probabilistic… accuracy decreases with more unique keys used." The *concurrency* primitive is Workflow-ID uniqueness (below). `DOCUMENTED` | ✅ **exactly this.** "You can specify a maximum number of concurrent task runs in a `Running` state for tasks with a given tag"; "If a task has multiple tags, it will run only if **all** tags have available concurrency"; "Setting a tag's concurrency limit to 0 causes immediate abortion of any task runs with that tag." `DOCUMENTED` | ✅ per-key Virtual Object lock `REPORTED` | ✅ **concurrency keys** — "a concurrency key is an expression which evaluates to a string… used as the concurrency queue name"; limits apply per unique key value; multiple limits per function; `env`/`account` scopes `DOCUMENTED` | ✅ both `REPORTED` |
| **Retry cap with a hard ceiling** | ✅ but **the default is the trap**: "Specifies the maximum number of execution attempts that can be made in the presence of failures. **The default is unlimited. Setting the value to 0 also means unlimited.**" And: "Unlike Activities, Workflow Executions do not retry by default." `DOCUMENTED` | Task `retries=` per task; no server-side hard ceiling above it `REPORTED` | ✅ `REPORTED` | ✅ `REPORTED` | ✅ `REPORTED` |
| **Append-only event history** | ✅ **"An append-only log of Events for your application."** "durably persisted by the Temporal service, enabling seamless recovery of your application state from crashes or failures. It also serves as an audit log for debugging." `DOCUMENTED` | Prefect keeps run states + events, but the terminal state is a stored field, not a derived projection `REPORTED` | ✅ journal `DOCUMENTED` | ✅ step memoization, not full replay `REPORTED` | ✅ both `REPORTED` |
| **A claim/lease that expires** | ✅ **"Temporal guarantees that there can be at most one Workflow Execution with a given ID running at any point in time"** — a Workflow ID *is* `claims.py`, enforced by a server, with `WorkflowIdReusePolicy` and `WorkflowIdConflictPolicy` `DOCUMENTED` | ✅ **timed leases, quoted in full below** `DOCUMENTED` | ✅ "Virtual Objects have an intrinsic lock per key… at most one request can run at the same time for a given key" `REPORTED` | ✅ per-key queue `DOCUMENTED` | ✅ `REPORTED` |

#### The single most useful quote in this report

Prefect's global concurrency limits — which since 3.4.19 back tag-based limits too — are leases:

> **Timed leases.** "Each time a concurrency slot is occupied, a countdown begins on the server.
> The length of this countdown is known as the concurrency slot's **lease duration**. While a
> concurrency slot is occupied, the Prefect client periodically notifies the server that the slot
> is still in use and restarts the countdown.
>
> If the countdown concludes before the lease has been renewed, the concurrency slot is released.
>
> **Lease expiration typically occurs when a process occupying a slot exits unexpectedly and is
> unable to notify the server that the slot should be released. This system exists to ensure that
> all concurrency slots are eventually released to prevent concurrency-related deadlocks.**
>
> The default lease duration is 5 minutes, but custom durations with a minimum of 1 minute can be
> supplied to the concurrency context manager."
>
> — `docs/v3/concepts/global-concurrency-limits.mdx`, PrefectHQ/prefect `DOCUMENTED`

And it has the failure-mode switch this estate keeps discovering it needs:

> "**Strict mode (`strict=True`)**: If lease renewal fails, execution stops immediately with an
> error. This ensures that operations only proceed when concurrency enforcement can be guaranteed."
> — same file `DOCUMENTED`

`strict=True` is a fail-closed control that can be *watched refusing something*: kill the renewal
path and the run must stop. That is a gate event that is a refusal, which is `MEASURED` at 0 of 22
today.

#### Is reimplementing this in `factory/` a mistake?

**Yes, for leases, orphan timeouts, per-tag concurrency and retry caps. No, for the verdict.**
`REASONED`

- `claims.py` is 150 lines that implement the *wrong half* of a lease. It has the store, the TTL
  constant and the human message; it deliberately omits expiry ("a control that quietly expires is
  one you cannot reason about"). That reasoning is sound about *silent* expiry and unsound about
  expiry as such: the fix is a lease that expires **and records the expiry as an event**, which is
  neither silent nor manual. Prefect gives you the server-side half for free and you keep the loud
  message.
- `finish.py`'s hardest-won rule — "A failed push must NOT release the claim" — is
  `MEASURED` correct and is *also* the classic durable-execution invariant (do not release a
  reservation until the terminal observation is recorded). It survives adoption unchanged.
- What must stay bespoke: the GreenContract, the readiness gates, and the projection that computes
  the verdict. No engine knows what "done" means here. `REASONED`

#### What adoption actually costs

- **Prefect: near zero.** Already in the estate (it runs the *data* connectors). Windows is a
  documented first-class target: "Prefect provides first-class Windows support with native
  PowerShell integration and full feature parity with other platforms… Prefect automatically
  detects PowerShell and uses it as the default shell on Windows"; UNC paths and mapped drives
  supported for `PREFECT_HOME`. `DOCUMENTED`
  ⚠ **Do not let this recreate the plane confusion.** `docs/evidence/false-succeeded-mechanism.md`
  is `MEASURED`: `orchestrator/pipelines.py` does not import Prefect, and two research answers
  wrongly blamed it. Using Prefect's *concurrency-limit API* as a lease server for the build plane
  is a different thing from running build stages as Prefect flows. Adopt the former; the latter
  reintroduces the exact ambiguity, because a Prefect `COMPLETED` is not a contract PASS.
- **Temporal: real.** A server (Postgres/MySQL + Elasticsearch for advanced visibility), a worker
  process, SDK-shaped code, and on Windows the self-hosted service is a Docker/WSL2 deployment —
  the docs describe Docker Compose / Kubernetes / manual and do not document a native Windows
  server. `REPORTED` (`docs.temporal.io` egress-blocked). For a one-person build with **9 of 30
  readiness gates passing** and **1 eval case**, that is the wrong week to spend. `BET`
- **Restate / DBOS / Inngest / Hatchet:** each solves a subset well (Restate's per-key single-writer
  is the cleanest claim primitive I found; Inngest's concurrency keys are the cleanest per-tag
  limiter). All of them are a *new* dependency for an estate that already has one that does the job.
  `BET`

**One caution that applies to all of them, and is the reason not to treat adoption as the fix:**
adopting Temporal does **not** by itself repair the false `succeeded`. A Temporal Workflow that
retried an Activity 100 times and succeeded on the 101st also closes as `WorkflowExecutionCompleted`.
The difference is that the 100 `ActivityTaskFailed` events are *in the history the verdict can be
computed from*, and a status field is not. The engine gives you the log; you still have to write the
projection. `DOCUMENTED` + `REASONED`

---

### 2.3 Terminal verdict from an append-only history

#### The canonical design

Event sourcing, with the verdict as a projection. Microsoft's pattern page states it plainly:

> "Instead of storing only the current state of the data in a relational database, store the full
> series of actions taken on an object in an append-only store. **The store acts as the system of
> record** that you can use to materialize the domain objects."
>
> "Applications **derive** the current state of an entity by replaying all the events in its stream.
> This process is known as *rehydration*."
>
> "Applications typically implement materialized views because it's costly to read and replay
> events. **Materialized views are read-only projections of the event store** that are optimized for
> querying."
>
> — `docs/patterns/event-sourcing.md`, MicrosoftDocs/architecture-center `DOCUMENTED`

And the honest cost, which the same page leads with:

> "Event sourcing is a complex pattern that introduces significant trade-offs… **For most systems
> and most parts of a system, traditional data management is sufficient.**" `DOCUMENTED`

Two corollaries that map onto the measured defect:

- **Never mutate; compensate.** "The event store is the permanent source of information, so you
  should never update the event data. The only way to update an entity or undo a change is to add a
  **compensating event**." That directly forbids `orchestrator/pipelines.py:1766`'s
  `if pipeline["status"] in ("failed",): pipeline["status"] = "running"`. A restart is an *event*
  (`RESTART_REQUESTED`), not an overwrite of the previous answer. `DOCUMENTED` + `MEASURED`
- **Eventual consistency is the price.** The projection lags the log. For a verdict, that is fine —
  the verdict is only read at terminal closure — but it means the projection must never be the
  thing an in-flight decision consults. `REASONED`

**Concretely, for the build plane:**

```
verdict(history) -> PASS | FAIL | UNMEASURABLE | NOT_RUN     # a pure function, no I/O

FAIL          if any (stage, attempt) in history ended failed and no later attempt of that
              stage both succeeded AND was explicitly re-certified   # retry is not erasure
NOT_RUN       if a required stage has no attempt event at all
UNMEASURABLE  if a required stage has attempts but no measurement event
PASS          only if every required stage has a measurement event, and first_attempt_ok
              is recorded alongside so "passed on attempt 1" and "passed on attempt 101"
              are different rows
```

The four verdicts stay uncollapsed (per `SYNTHESIS.md`), and `first_attempt_ok` is the field that
makes retry-independent reliability measurable — which the evidence doc identifies as trivially
separable in the audit trail and impossible in `pipeline["stages"]`. `REASONED`

#### The negative control — concrete test shapes

The established practice is Temporal's replay-in-CI recipe, which is exactly a negative control over
a history-derived function:

> "When you test changes to your Workflow Definitions, we recommend doing the following as part of
> your CI checks: 1. Determine which Workflow Types or Task Queues… will be targeted… 2. **Download
> the Event Histories of a representative set of recent open and closed Workflows**… 3. **Run the
> Event Histories through replay.** 4. **Fail CI if any error is encountered during replay.**"
>
> — `docs/develop/python/best-practices/testing-suite.mdx`, temporalio/documentation `DOCUMENTED`

Generalised to the verdict function, five test shapes. Each names what it catches and how to make it
fire on purpose. `REASONED`

| # | Shape | The history you feed it | Must assert | Fires on purpose by |
|---|---|---|---|---|
| **N1** | **The 101st-attempt control** | `[stage_started, stage_failed] × 100, [stage_started, stage_completed] × 1` for one required stage | `verdict != PASS`, and `first_attempt_ok == False` | Deleting the "no later attempt erases an earlier failure" clause — the test must go red |
| **N2** | **The restart-over-a-failed-log control** | history ends `stage_failed`; then `RESTART_REQUESTED`; no terminal event | `verdict == NOT_RUN` or `UNMEASURABLE`, never `PASS`, and never a stored `running` that outlives the log — this is `pipe_29b8edf6` | Re-adding the `failed → running` overwrite |
| **N3** | **Property: monotonic non-erasure** | property-based (Hypothesis) over random valid histories; for any history `h` and any appended event `e`, if `verdict(h) == FAIL` then `verdict(h + [e]) != PASS` unless `e` is an explicit `RECERTIFIED` event | the property holds for 1000 generated histories | Removing the `RECERTIFIED` requirement |
| **N4** | **Replay of real histories** | every audit trail in `.data/` and every recorded orchestrator run (`MEASURED`: 14 runs, 3 of which finished with no human) | `verdict(history)` is recomputable, and **for the run that currently reads `succeeded` over 115 failures it must now read FAIL** | This one already fires — it is the regression test for the defect |
| **N5** | **`continue_on_failure` audit** | any history where a stage carrying `continue_on_failure` failed | the verdict is `PASS` only if a *policy record* naming that stage and a reason exists in the history; otherwise `UNMEASURABLE` | Setting the flag on a stage with no policy record — must refuse |

**The property that makes a false `succeeded` impossible is N3, not N1.** N1 catches the one case you
already know about; N3 says *no appended event can turn FAIL into PASS*, which is the invariant.
`BET` — I believe this is the right invariant, but "unless `e` is an explicit `RECERTIFIED` event"
is a hole that a careless recertification path could drive through, and that path needs its own gate.

**A caution against over-adopting event sourcing.** The estate does not need CQRS, an event bus, or
rehydrated aggregates. It needs one pure function over an append-only file it already writes. The
Microsoft page's own warning applies: adopt the projection, not the architecture. `REASONED`

---

### 2.4 Orphan reaping and leases

#### Documented practice

**Kubernetes Lease** — the reference shape of the record:

> "Distributed systems often have a need for _leases_, which provide a mechanism to lock shared
> resources and coordinate activity between members of a set."
> "For every `Node`, there is a `Lease` object with a matching name… every kubelet heartbeat is an
> **update** request to this `Lease` object, updating the `spec.renewTime` field for the Lease. The
> Kubernetes control plane uses the time stamp of this field to determine the availability of this
> `Node`."
> "Kubernetes also uses Leases to ensure only one instance of a component is running at any given
> time."
>
> — `content/en/docs/concepts/architecture/leases.md`, kubernetes/website `DOCUMENTED`

Note the field set: `holderIdentity`, `leaseDurationSeconds`, `renewTime`, `acquireTime`,
`leaseTransitions`. `claims.py` has `since` and `who` — no duration, no renewal, no transition
count. `MEASURED`

Also note the *fast-release* path, which is what `finish.py` should be: with the
`ControllerManagerReleaseLeaderElectionLockOnExit` gate, "the `kube-controller-manager` **actively
releases its leader election lock during leader transitions, rather than waiting for the lock's TTL
to expire**." A clean exit releases; the TTL is only the backstop. `DOCUMENTED`

**ZooKeeper ephemeral znodes** — the strongest version, and the one that removes the "is it alive?"
question entirely: an ephemeral znode "exists as long as the session that created the znode is
active, and when the session ends the znode is deleted"; expirations happen when the cluster does not
hear from the client within the session timeout, at which point "the cluster will delete any/all
ephemeral nodes owned by that session and immediately notify any/all connected clients of the
change"; the client heartbeats at roughly ⅓ of the timeout. `REPORTED` (zookeeper.apache.org text via
search; the guide's markdown source did not contain the phrase in the copy I fetched — **could not
verify verbatim**).

**Kleppmann, fencing tokens** — the reason a TTL alone is not enough: a lease can expire while the
holder is paused (GC, page fault, network delay) and the holder does not know; the fix is a
**monotonically increasing fencing token** issued with the lock and checked by the resource, so a
stale holder's write is rejected. His criticism of Redlock is that it "does not have any facility for
generating fencing tokens" and makes dangerous timing assumptions. He distinguishes locks for
*efficiency* (best-effort is fine) from locks for *correctness* (use a real consensus system).
`REPORTED` — martin.kleppmann.com and its PDF mirror were both **egress-blocked**; quotes are from
search snippets and I could not read the original in this session.

#### The correct design for `claims.py`

`REASONED`, built from the above.

```
Claim = {
  lane, holder_id, epoch,            # epoch is the fencing token: monotonic, per-lane
  acquired_at, lease_seconds, renew_at,
  pid, session_id                    # the addressable session, not just a pid
}
```

1. **Lease, not label.** `lease_seconds` default ~120s, renewed by the running session. Expiry
   releases the slot. This is the Prefect shape, and it is the one property `claims.py`
   deliberately lacks — `MEASURED`: on 2026-08-22 three lanes finished and "the claim stayed held
   for four hours (blocking relaunch)", per `finish.py`'s own docstring.
2. **Expiry is an event, not a silence.** Write `CLAIM_EXPIRED{lane, holder, epoch, last_renew}` to
   the append-only log. This keeps the module's original virtue — a control you can reason about —
   while removing the four-hour block. It also feeds §2.3's history.
3. **Fencing token.** `epoch` increments on every acquisition. `finish.py` refuses a push/release
   whose epoch is not the current one. This is what stops the 2026-08-22 incident *for real*: the
   `MEASURED` failure was `finish()` releasing `control-plane` while its session was alive, a
   relaunch seeing a free lane, and "three control-plane sessions sharing one worktree and one
   branch. Nothing collided, which was luck rather than a control." A stale finisher holding epoch
   3 cannot release a claim at epoch 4.
4. **Liveness comes from the session registry, not the process table.** `sessions.py`'s instinct is
   right ("liveness must be checked against the process table, not against the file's existence")
   and its instrument is now obsolete: `claude agents --json` is the `DOCUMENTED` list, and the
   supervisor already stops idle processes after ~1 hour. Prefer the supported list; keep the
   `None ≠ empty set` distinction, which is genuinely good and is the same distinction as
   `UNMEASURABLE ≠ FAIL`.
5. **Best-effort or correctness?** By Kleppmann's split, a lane claim is an *efficiency* lock —
   two agents in one worktree is expensive, not corrupting, because git is the real arbiter. So a
   single-node lease plus a fencing token is proportionate; a consensus system is not. `BET`

**One thing to delete rather than fix:** if lanes move to `claude --worktree`, points 1–4 are
partly redundant — `git worktree lock` plus the stale-lock sweep is a lease with process-exit
release, `DOCUMENTED`. Keep `claims.py` only for the thing git cannot express: *two different lanes*
that must not run together because they touch the same file. That is a conflict-graph claim, not a
worktree claim, and it is the one genuinely bespoke piece.

---

### 2.5 Does the ceiling of 3 generalise?

#### The 41.7% number is the wrong half of the study

`REPORTED` — arXiv 2607.04697, "AI Agent Pull Requests on GitHub: Frequency, Structure, and Merge
Conflict Rates" (AIDev-pop: **33,596 PRs across 2,807 repositories**). arxiv.org was
**egress-blocked**; numbers below are from search snippets of the abstract and I could not read the
paper.

| Finding | Number |
|---|---|
| Repositories with co-active agent-authored PR pairs (exact temporal overlap) | 40.2% |
| Share of all agent PRs that are in a co-active pair | 79.4% |
| **Textual conflict rate, cross-agent pairs** | **41.7%** |
| **Textual conflict rate, intra-agent pairs** | **19.8%** (non-overlapping 95% CIs) |
| **Share of co-active pairs that are cross-agent** | **0.5%** |
| Conflicted files that are source code, not dependency manifests | 84.4% |
| Conflicts that are structural (modify/delete, add/add) | ~42% |

**This matters more than any other number in this report.** `lanes.py`, `worktrees.py` and
`local_tracker.py` all carry the 41.7% figure in their docstrings as the justification for
worktree-per-lane. Every lane in this estate runs Claude Code. That is the **intra-agent** cell:
**19.8%**, less than half, and drawn from the 99.5% of co-active pairs the headline number is *not*
about. The worktree decision is still right — 19.8% is not nothing, and ~42% structural means git's
merge cannot save you — but the argument is roughly half as strong as the repo states, and a
docstring citing 41.7% for a fleet of identical agents is a number used outside its stratum.
`REPORTED` + `REASONED`

#### Is file-locality the right frame?

Partly. Two independent sources say the frame is right and the *partition* is wrong.

- **Anthropic, documented:** "**Avoid file conflicts.** Two teammates editing the same file leads to
  overwrites. Break the work so each teammate owns a different set of files." — file locality is the
  vendor's own rule. `DOCUMENTED`
- **The published improvement is dependency cohesion, not file disjointness.** "When Parallelism
  Pays Off: Cohesion-Aware Task Partitioning for Multi-Agent Coding" (arXiv 2606.00953) formalises
  orchestration as a **graph partitioning problem** capturing the communication-to-computation
  trade-off, builds dependency graphs from static analysis, **isolates structural hub files**, and
  partitions by community detection. Across 28 real-world tasks on DevEval and CodeProjectEval it
  reports up to **+14.0% pass rate, 2.10× wall-clock speedup, −35% API cost** versus sequential,
  file-based-parallel, and Claude Code with Agent Teams — "with the largest gains on the most
  dependency-dense projects." `REPORTED` (**could not verify** — arXiv blocked)

  Read against `lanes.py`: the module's own docstring admits "the *grouping into lanes* is ASSUMED
  — a judgement about which gates touch the same files, made by reading them." The paper says
  derive it from a dependency graph and *isolate the hubs*. In this repo the hub is
  `orchestrator/pipelines.py` — the file two lanes collide on. Isolating the hub (one lane owns it,
  everything else is partitioned around it) is a cheap, testable change to `_touch_set()` /
  `conflicts()` that does not require adopting anything.

#### Is parallelism the bottleneck? No.

- **Prior research, already settled and not re-litigated:** multi-agent averaged **−3.5% across 180
  configs**; sequential tasks degraded **39–70%** (`SYNTHESIS.md`).
- **Corroborating, from this pass:** "All 28 multi-agent configurations tested showed degradation
  relative to single-agent baselines, ranging from **−4.4% to −35.3%**"; "even at the smallest team
  size (k=2), multi-agent systems already lose 15–49% of single-agent performance." `REPORTED`
  (search snippets; **could not verify** — arXiv blocked). Note these are *task-performance*
  numbers, not throughput; the Co-Coder result above shows throughput gains are real when the
  partition is right. The two are not in conflict: partitioning badly costs you both.
- **Anthropic's own sizing advice matches the measured ceiling exactly:** "Start with 3-5 teammates
  for most workflows… **If you have 15 independent tasks, 3 teammates is a good starting point.**
  Scale up only when the work genuinely benefits… Three focused teammates often outperform five
  scattered ones." `DOCUMENTED`
- **The estate's own numbers say the bottleneck is elsewhere.** `MEASURED`: **9 of 30** readiness
  gates pass; the eval corpus is **1 case, 0 strata** against a needed **29** for a 10%-prevalence
  blind spot; **0 of 15** agent version-hash dimensions covered; **0 of 22** gate events were ever a
  refusal; **3 of 14** orchestrator runs finished with no human. Going from 3 lanes to 6 multiplies
  a pipeline whose verdict cannot yet be trusted. **The honest answer is that parallelism is not the
  bottleneck; measurement is.** `REASONED`
- **Merge queues and stacked PRs are the wrong tool at this scale.** A merge queue serialises merges
  against an up-to-date base with speculative merge commits and batching (`REPORTED`,
  docs.github.com / Mergify / Trunk). It solves *"CI passed against a stale base"* for a team with
  more merge candidates than CI capacity. Here `finish.py` **never merges** by design and a human
  decides; there is no queue to serialise. Revisit if and when merges become automated. `REASONED`

**Better lever than more lanes, ranked:** (1) instrument cost — it is `MEASURED` at zero and is
hours of work now that `total_cost_usd` is a documented field; (2) isolate the hub file in
`conflicts()`; (3) grow the corpus. `BET`

---

### 2.6 Remote / cloud sessions

`DOCUMENTED` unless marked.

**What changes.** Cloud sessions give, for free, three of the four things the isolation ladder was
going to be built to provide:

- **Per-session isolation:** "each session runs in an isolated, Anthropic-managed VM."
- **Egress control:** "network access is limited by default and can be disabled." (With the honest
  caveat the docs themselves state: "When running with network access disabled, Claude Code can
  still communicate with the Anthropic API, which may allow data to exit the VM.")
- **Credential separation:** "sensitive credentials such as git credentials or signing keys are
  **never inside the sandbox** with Claude Code; authentication is handled through a secure proxy
  using scoped credentials." This is the single strongest answer to the estate's `MEASURED`
  condition — *"agents run as the user with the user's credentials"*.

**Effect on the ladder in `architecture-v0.md` §4:**

- **T0 gets harder to justify.** T0 is "worktree, repo files only, no egress, no DB verbs" — but the
  Bash sandbox that would enforce "no egress" **does not exist on the operator's OS**: "The sandbox
  is built into Claude Code and runs on macOS, Linux, and WSL2. **Native Windows is not supported.**
  On Windows, run Claude Code inside a WSL2 distribution." So on Windows, T0 is a *convention*, not
  a control — the same category error as a claim that does not expire. A cloud session enforces
  what T0 only asks for.
- **T1 gets much easier.** T1 is "container, egress allowlist, read-only warehouse role". A cloud
  environment with restricted network access plus a read-only Snowflake role is T1, with no
  container work and no WSL2 story. `REASONED`
- **T2 is unaffected.** The ephemeral zero-copy clone lives in Snowflake, not in the sandbox. Where
  the agent runs is orthogonal — which is a point *for* §4's central claim that the tier is chosen
  by what a task *touches*. `REASONED`
- **A control the estate does not have, for free elsewhere:** Copilot's "Copilot can only push to
  branches with names beginning with `copilot/`" is a namespace fence enforced by the forge. The
  equivalent here — a server-side rule that agent branches must match `lane/*` and cannot touch
  `main` — is cheap and is a refusal that can be watched. `REPORTED` + `REASONED`

**Does it kill the worktree model?** No, it demotes it. `BET`

- A cloud session **clones the GitHub remote at your current branch, not your local checkout** —
  "push first if you have local commits." A worktree with uncommitted work is invisible to it.
- `--teleport` pulls a cloud session back locally and requires: clean git state, the same repository
  (not a fork), the branch pushed to the remote, and the same account. So the round trip is
  *branch-mediated*, exactly like `finish.py`'s push-then-hand-off.
- Worktrees survive as the **local** unit — for reviewing, for teleported sessions, and for the
  hub-file lane that has to stay local. They stop being the isolation boundary.

**Two costs that are easy to miss:**

- **Rate limits, not compute, become the cap.** "Claude Code on the web shares rate limits with all
  other Claude and Claude Code usage within your account. **Running multiple tasks in parallel
  consumes more rate limits proportionately.** There is no separate compute charge for the cloud
  VM." The ceiling moves from a file-conflict graph to an account quota — which the estate has hit
  before, `MEASURED` (the 10-core cloud quota incident in R3).
- **Sessions in containers cannot message each other across the boundary.** "A container has its own
  filesystem, so a session inside it and a session on the host can't reach each other… A session
  inside WSL 2 and a native Windows session on the same computer can't reach each other either."
  So a mixed local/WSL2/cloud fleet loses the local socket bus and must go through Remote Control
  (Anthropic servers) or an out-of-band channel. `bus.py`'s design — "the lanes are processes on one
  machine and the channel dies with them" — is correct *and* is the assumption that breaks first
  when sessions move off the machine.

---

## 3. What this changes in the spec

Concrete, ordered by effect on time-to-one-certifiable-end-to-end-run. File paths are in
`github.com/ALDC-io/agent-factory`.

**1. `scripts/local_tracker.py` — stop generating PowerShell; launch through the supported surface.**
Replace `_launch_script()`/`launch_command()` with `claude --worktree <lane> --name "<lane> · <title>"
--model <lane.model> --settings <lane-settings.json>` (or the SDK). This deletes the class of defect
that produced all three of 2026-08-22's silent failures: a bare `claude` cannot honour a model field,
`CLAUDE_CODE_CHILD_SESSION` is not inherited if you do not spawn a shell, and `--name` already does
collision handling. **Every field in a lane spec needs a test asserting it reaches the process** —
`architecture-v0.md` §5 already says this; this is where it bites. `MEASURED` + `DOCUMENTED`

**2. `factory/claims.py` — make the lease expire, and record the expiry.** Add `lease_seconds`,
`renew_at`, `epoch` (fencing token) and a `CLAIM_EXPIRED` event. Keep the loud refusal message; drop
the four-hour block. Back it with a Prefect global concurrency limit named `lane:<id>` if you want
the server-side half without writing it — `strict=True` gives you a fail-closed control you can
watch refuse. Narrow the module's scope to **cross-lane file conflicts only**; `git worktree lock`
plus the stale-lock sweep covers same-lane. `DOCUMENTED`

**3. `factory/finish.py` — check the fencing token before releasing.** `checks()` must include
"the claim's epoch is still mine". This is the direct repair for the `MEASURED` three-sessions-in-one-
worktree incident, which `sessions.py`'s docstring correctly calls luck rather than a control.
Keep "a failed push must NOT release the claim" exactly as written. `REASONED`

**4. New: `factory/verdict.py` — a pure `verdict(history)` function, plus `tests/test_verdict.py`
carrying negative controls N1–N5 from §2.3.** N4 replays the 14 recorded orchestrator runs and must
turn the run that reads `succeeded` over 115 failures into FAIL. This is the highest-value single
item in the report, because it is the defect the whole programme exists to catch, it needs no new
dependency, and it produces the first gate event that is a refusal. `MEASURED` + `REASONED`

**5. `factory/lanes.py` — fix the citation and isolate the hub.** The 41.7% figure in the docstrings
of `lanes.py`, `worktrees.py` and `local_tracker.py` is the cross-agent rate; the estate's case is
intra-agent at **19.8%**, and cross-agent pairs are 0.5% of co-active pairs. Correct it (per rule #6,
as a `> **Contradiction**:` callout rather than a silent overwrite) and add the hub-isolation rule to
`_touch_set()`/`conflicts()`: one lane owns `orchestrator/pipelines.py`, the rest partition around it.
`REPORTED`

**6. `docs/specs/architecture-v0.md` §7.5 — answer the open question.** "Whether worktree-on-one-
machine is the right abstraction" resolves to: **a stepping stone whose successor is already shipped**.
§4's ladder survives intact (tiers are chosen by what a task touches). §3's plane diagram survives.
What changes is that the RUN plane's T0 and T1 rows should name `claude --worktree` and a cloud
environment respectively, and §7.4's "T1/T2 assume containers on Windows via WSL" should record the
`DOCUMENTED` fact that the Bash sandbox has **no native-Windows support at all**, so T0's "no egress"
is currently unenforceable on the operator's machine.

**7. `docs/research/R7-session-manager.md` — do not dispatch it as written.** Its §1–3 (agent-team
configuration surface, optimising a team, a queue per team) are now partly answered by shipped
features: `agents` definitions with `tools`/`model`/`maxTurns`/`permissionMode`, the agent-teams
shared task list with dependencies, and `TaskCreated`/`TaskCompleted`/`TeammateIdle` gate hooks. Its
§4 (bounded autonomy) and §5 (the interface) are still open and are the parts worth asking. Its
premise — that Switchboard is the reference implementation — is a hypothesis I **could not verify**
and that the shipped feature set has largely overtaken. `DOCUMENTED` + `BET`

**8. Do not adopt Temporal yet.** Record the decision and the trigger. Adopt when: (a) the build
plane needs durable timers across process restarts, or (b) more than one machine runs stages, or
(c) attempt caps must be enforced somewhere the agent cannot edit. Until then Prefect's concurrency
API supplies the lease and the per-tag limit, and `verdict.py` supplies the thing no engine
supplies. ⚠ Keep the plane distinction from `docs/evidence/false-succeeded-mechanism.md` explicit in
whatever is written: **using Prefect as a lease server is not running build stages as Prefect flows,
and a Prefect `COMPLETED` is never a contract PASS.** `REASONED`

---

## 4. What I could not settle

1. **Switchboard.** I never reached the repository. R7's central artefact is unexamined, and the
   estate's own rule — an object named by a handoff is a hypothesis until you walk it — applies. One
   `git clone` settles it.
2. **The arXiv papers.** 2607.04697 (the 41.7%/19.8% study), 2606.00953 (cohesion-aware
   partitioning) and 2608.16801 (coordination measurement) were all **egress-blocked**. Every number
   I quote from them is a search snippet of an abstract. The 19.8% figure in particular is now
   load-bearing for a spec change; **read the paper before acting on §3 item 5.** A PDF from any
   reachable mirror settles it.
3. **Kleppmann verbatim.** Both the blog and its PDF mirror were blocked. The fencing-token argument
   is well known enough that I am confident in the substance, but I did not read it in this session.
4. **Whether the estate's installed Claude Code has these features.** Every capability in §2.1 has a
   minimum version (`--worktree` isolation checks v2.1.206+, cross-session messaging v2.1.234+ on
   native Windows, the stale-lock sweep v2.1.210+, `--resume` cross-directory v2.1.223+). I did not
   check `claude --version` on the operator's machine. If it is older, half of §3 item 1 is not yet
   available and the finding is "upgrade first".
5. **Whether `claude --worktree` composes with the conflict graph.** The vendor's worktree is
   per-*session*; the estate's claim is per-*lane pair that shares a file*. I believe they compose
   (worktree for same-lane, `claims.py` for cross-lane) but I did not test it, and
   `worktree.baseRef` defaults to `"fresh"` (the remote default branch) while this repo works on
   `feat/readiness-generator` — so `"head"` is almost certainly required and untested here.
6. **Cursor and Codex primary docs.** Both blocked. My characterisation of Codex's sandbox modes and
   Cursor's per-VM isolation is from snippets; treat the table rows as `REPORTED`.
7. **Cost of a Prefect concurrency limit as a lease server.** I did not measure the latency of a
   slot acquire/renew round trip against a local Prefect server, and `local_tracker.py` is already
   `MEASURED` at 8–45s per page because one gate shells out to pytest. Adding a network call to the
   claim path may or may not matter; a stopwatch settles it.
8. **The 3-lane number itself.** `parallel_set()` is honest that it is greedy, not a true maximum
   independent set ("with five lanes the difference is nil"). With hub isolation the graph changes
   shape and the greedy/optimal gap may stop being nil. Worth recomputing after §3 item 5.

---

## 5. Sources

**Claude Code / Agent SDK (fetched, primary)**
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/cli-reference
- https://code.claude.com/docs/en/agent-sdk/sessions
- https://code.claude.com/docs/en/agent-sdk/cost-tracking
- https://code.claude.com/docs/en/agent-sdk/subagents
- https://code.claude.com/docs/en/worktrees
- https://code.claude.com/docs/en/agent-teams
- https://code.claude.com/docs/en/agent-view
- https://code.claude.com/docs/en/cross-session-messaging
- https://code.claude.com/docs/en/sandboxing
- https://code.claude.com/docs/en/claude-code-on-the-web

**Durable execution (docs source fetched from GitHub raw; rendered sites egress-blocked)**
- https://raw.githubusercontent.com/temporalio/documentation/main/docs/encyclopedia/retry-policies.mdx
- https://raw.githubusercontent.com/temporalio/documentation/main/docs/encyclopedia/detecting-activity-failures.mdx
- https://raw.githubusercontent.com/temporalio/documentation/main/docs/encyclopedia/workflow/workflow-execution/workflowid-runid.mdx
- https://raw.githubusercontent.com/temporalio/documentation/main/docs/encyclopedia/workflow/workflow-execution/event.mdx
- https://raw.githubusercontent.com/temporalio/documentation/main/docs/encyclopedia/workflow/workflow-execution/timers-delays.mdx
- https://raw.githubusercontent.com/temporalio/documentation/main/docs/develop/python/workflows/cancellation.mdx
- https://raw.githubusercontent.com/temporalio/documentation/main/docs/develop/python/best-practices/testing-suite.mdx
- https://raw.githubusercontent.com/temporalio/documentation/main/docs/design-patterns/fairness.mdx
- https://raw.githubusercontent.com/PrefectHQ/prefect/main/docs/v3/concepts/global-concurrency-limits.mdx
- https://raw.githubusercontent.com/PrefectHQ/prefect/main/docs/v3/concepts/tag-based-concurrency-limits.mdx
- https://raw.githubusercontent.com/PrefectHQ/prefect/main/docs/v3/how-to-guides/self-hosted/server-windows.mdx
- https://raw.githubusercontent.com/inngest/website/main/pages/docs/guides/concurrency.mdx
- https://raw.githubusercontent.com/restatedev/documentation/main/docs/concepts/durable_building_blocks.mdx

**Event sourcing / leases**
- https://raw.githubusercontent.com/MicrosoftDocs/architecture-center/main/docs/patterns/event-sourcing.md
- https://raw.githubusercontent.com/MicrosoftDocs/architecture-center/main/docs/patterns/cqrs.md
- https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/concepts/architecture/leases.md
- https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html — **blocked, not read**
- https://zookeeper.apache.org/doc/r3.5.9/zookeeperProgrammers.html — **snippets only**

**Fleet managers (READMEs fetched)**
- https://raw.githubusercontent.com/dagger/container-use/main/README.md
- https://raw.githubusercontent.com/smtg-ai/claude-squad/main/README.md
- https://raw.githubusercontent.com/stravu/crystal/main/README.md
- https://raw.githubusercontent.com/BloopAI/vibe-kanban/main/README.md

**Papers (abstracts via search; arxiv.org blocked)**
- https://arxiv.org/abs/2607.04697 — AI Agent Pull Requests on GitHub: Frequency, Structure, and Merge Conflict Rates
- https://arxiv.org/abs/2606.00953 — When Parallelism Pays Off: Cohesion-Aware Task Partitioning for Multi-Agent Coding
- https://arxiv.org/abs/2608.16801 — When Agents Coordinate: Measuring Coordination in Multi-Agent AI Coding
- https://arxiv.org/abs/2604.03551 — AgenticFlict: A Large-Scale Dataset of Merge Conflicts in AI Coding Agent PRs

**Other vendors (search snippets; primary docs egress-blocked)**
- https://developers.openai.com/codex/agent-approvals-security · https://github.com/openai/codex
- https://cursor.com/docs/cloud-agent
- https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent
- https://jules.google/docs/usage-limits/
- https://docs.devin.ai/api-reference/v3/sessions/post-organizations-sessions
- https://docs.openhands.dev/sdk/guides/agent-server/docker-sandbox

**Repository (read, not modified)**
- `/home/user/agent-factory/factory/{lanes,claims,worktrees,bus,finish,sessions}.py`
- `/home/user/agent-factory/scripts/local_tracker.py`, `scripts/hooks/lane-bus.py`
- `/home/user/agent-factory/docs/research/R7-session-manager.md`
- `/home/user/agent-factory/docs/evidence/false-succeeded-mechanism.md`
- `/home/user/agent-factory/docs/evidence/machine-local-state-2026-08-22.md`
- `/home/user/agent-factory/docs/specs/architecture-v0.md`
- `/home/user/agent-factory/docs/research/answers/R3-answer-control-plane.md`
