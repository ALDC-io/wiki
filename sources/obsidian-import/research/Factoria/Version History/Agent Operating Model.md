# Agent Operating Model for the Autonomous Data Engineering Platform

## Collaboration philosophy

This platform treats “autonomous data engineering” as a **controlled, observable, artefact-driven workflow**, not an unconstrained AI assistant. The operating model is designed to be reliable under live demos and extensible towards production without changing the runner-split architecture.

### Specialist agents, not one “do everything” agent

The system uses a **small set of specialist agents** (Intake, Design, Profiler, Builder, QA, PR) with narrow responsibilities and tightly scoped tool permissions. This makes behaviour more predictable, reduces accidental overreach, and yields clearer UI theatre (“who is doing what”). OpenClaw explicitly supports **per-agent tool restrictions** (allow/deny) and per-agent sandbox configuration for multi-agent setups, which is foundational to this model. citeturn0search0turn0search22

### Strict tool allowlists, immutable interfaces

Agents must **not dynamically invent tools, execution methods, or ad-hoc shell workarounds**. Tools should be defined as JSON-schema functions registered by the platform and controlled via per-agent allow/deny policy. OpenClaw documents that agent tools are configured globally or per-agent under `agents.list[].tools`, with allowlist/denylist controlling what the model can call. citeturn0search19turn0search0

This principle exists to preserve the runner-split security model:

- Agents never run shell commands.
- The **runner** is the only place where dbt / Snowflake CLI / git / GitHub CLI execute.
- Agents access those capabilities only through **API tools** that delegate to the runner’s **allowlisted Job API**.

### Artefact-driven handoffs as the collaboration backbone

Instead of “agent A tells agent B in free text,” each step produces **well-defined artefacts** (design.md, profile reports, run_results.json, QA reports). Subsequent agents consume those artefacts plus ticket metadata. dbt’s own documentation emphasises that `run_results.json` is the canonical record of a completed dbt invocation and contains timing and status for executed nodes, making it a strong contract for QA gating and audit. citeturn1search2turn1search6

This improves:

- **Reliability**: fewer lost details between agents.
- **Debuggability**: you can reproduce failures from artefacts and logs.
- **Auditability**: every step has stored evidence.

### Human approval checkpoints are intentional control points

Two human gates remain non-negotiable for safety and demo clarity:

- **Design Review** (approve the modelling plan before warehouse interaction and file generation).
- **Ready for Review** (approve creation of the PR / external write actions).

### Runner-split security model is enforced by design

OpenClaw’s security guidance is explicit that anything “open” with tools enabled must be locked down with tool policy and sandboxing, and that public exposure or missing authentication must be treated as critical. citeturn0search1  
The operating model therefore assumes:

- **No Snowflake/GitHub secrets** in gateway; only runner holds them.
- **No “exec”/filesystem tools** exposed to agents.
- **API → runner** calls require authentication (bearer token) and strict job allowlists.

## Agent roster

The initial roster keeps the baseline agents you specified and adds one compelling, architecturally consistent agent for tenant provisioning (because the platform’s workflow includes tenant states). This does not change architecture; it assigns clear responsibility for tenant bootstrap steps.

### Tenant Provisioning Agent

**Purpose**  
Turn a tenant provisioning request into a ready tenant workspace (schemas, minimal dbt bootstrap, smoke run).

**Inputs**  
Tenant provisioning ticket, tenant config (Snowflake connection alias, repo URL), provisioning preset.

**Outputs**  
Tenant readiness artefacts (provisioning logs, provisioning report); tenant state transition to `TENANT_READY`.

**Allowed tools**  
- `snowflake_sql`  
- `workspace_write_files` (for tenant-specific config files and runbooks)  
- `dbt_build` (for a smoke build)  
- `publish_artifact`

**Forbidden tools**  
- `git_commit_push`, `gh_create_pr` (provisioning should not open PRs by default)

**Example tasks**  
- Create tenant schemas / roles (via runner job).  
- Bootstrap dbt profile for tenant target.  
- Run smoke build and publish report.

### Intake Agent

**Purpose**  
Normalize the ticket into a structured brief; detect missing requirements; produce clarifying questions.

**Inputs**  
Raw ticket text / form data; tenant context; optional source hints.

**Outputs**  
`intake_summary.md` + structured “ticket brief” (embedded in artefact metadata); either transition to `NEEDS_INFO` or `DESIGN_REVIEW`.

**Allowed tools**  
- `publish_artifact`

**Forbidden tools**  
- `snowflake_sql`, `dbt_compile`, `dbt_build`, `workspace_write_files`, `git_commit_push`, `gh_create_pr`

**Example tasks**  
- Enforce ticket template completeness (grain, keys, sources, acceptance criteria).  
- Ask for missing join keys / incremental requirements.

### Design Agent

**Purpose**  
Create an implementable modelling plan (grain, keys, model list, incremental strategy, tests strategy).

**Inputs**  
Ticket brief from Intake; tenant conventions; prior artefacts.

**Outputs**  
`design.md` + optional `design.json` (structured spec).

**Allowed tools**  
- `publish_artifact`

**Forbidden tools**  
- `snowflake_sql`, `dbt_compile`, `dbt_build`, `workspace_write_files`, `git_commit_push`, `gh_create_pr`

**Example tasks**  
- Define staging → intermediate → fact model breakdown.  
- Define required dbt tests and assumptions.

### Profiler Agent

**Purpose**  
Discover and validate source schemas, key candidates, join integrity, nullability, distributions.

**Inputs**  
Approved design; source table references; tenant connection alias.

**Outputs**  
`profile_report.json` + `profiling.md` summary; profiling logs reference.

**Allowed tools**  
- `snowflake_sql`  
- `publish_artifact`

**Forbidden tools**  
- `workspace_write_files`, `dbt_compile`, `dbt_build`, `git_commit_push`, `gh_create_pr`

**Example tasks**  
- Null rate and cardinality checks on candidate keys.  
- Sampling queries for data sanity and join feasibility.

### Builder Agent

**Purpose**  
Generate dbt model files + schema tests files in workspace, based on design + profiling evidence.

**Inputs**  
Design artefacts; profiler artefacts; dbt project conventions; workspace paths.

**Outputs**  
Generated dbt files under `dbt_changes/` + `build_plan.md` summarising what was created.

**Allowed tools**  
- `workspace_write_files`  
- `dbt_compile` (compile-only validation)  
- `publish_artifact`

**Forbidden tools**  
- `dbt_build`, `git_commit_push`, `gh_create_pr`, `snowflake_sql`

**Example tasks**  
- Create staging models with consistent naming and column typing.  
- Generate `schema.yml` tests (not_null/unique/relationships, etc).

### QA Agent

**Purpose**  
Gate the change set by running dbt and producing a QA report anchored in dbt artefacts.

**Inputs**  
Changed files list; compilation results; tenant target.

**Outputs**  
`qa_report.md`, `run_results.json`, plus pass/fail status.

**Allowed tools**  
- `dbt_build`  
- `publish_artifact`

**Forbidden tools**  
- `workspace_write_files`, `git_commit_push`, `gh_create_pr`, `snowflake_sql` (optional; keep QA deterministic)

**Example tasks**  
- Run `dbt build` for the impacted selection set.  
- Summarise failing nodes from `run_results.json` (dbt documents it as a record of invocation results). citeturn1search2turn1search6

### PR Agent

**Purpose**  
Turn a validated workspace change set into a Git branch and PR with evidence.

**Inputs**  
QA artefacts; changed files list; ticket metadata.

**Outputs**  
PR URL + `pr_summary.md`.

**Allowed tools**  
- `git_commit_push`  
- `gh_create_pr`  
- `publish_artifact`

**Forbidden tools**  
- `snowflake_sql`, `dbt_compile`, `dbt_build`, `workspace_write_files`

**Example tasks**  
- Create branch, commit changes, push.  
- Open PR with test evidence and artefact links.

## Tool permission model

### Agent tool permissions matrix

The matrix below lists the **only** execution-relevant tools exposed to agents. All are implemented as **API tool endpoints** that delegate work to `runner` jobs (agents never call runner directly).

| Agent | snowflake_sql | dbt_compile | dbt_build | workspace_write_files | git_commit_push | gh_create_pr | publish_artifact |
|---|---:|---:|---:|---:|---:|---:|---:|
| Tenant Provisioning | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Intake | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Design | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Profiler | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Builder | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| QA | ❌* | ❌* | ✅ | ❌ | ❌ | ❌ | ✅ |
| PR | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |

\*Optional: you may allow `dbt_compile` to QA if you want QA to run compile-only preflights, but in most cases `dbt_build` is sufficient and simpler.

### Security rationale for these boundaries

- OpenClaw supports per-agent tool restrictions (allow/deny) specifically to run multiple agents with different security profiles. citeturn0search0turn0search22  
- OpenClaw also documents that tools are configured under the platform’s tool policy and can be set per-agent, which enables strict least-privilege “role accounts” for agents. citeturn0search19  
- This matrix prevents privilege escalation patterns such as:
  - Builder generating malicious PRs (Builder lacks git/PR tools).
  - PR agent querying Snowflake or running dbt (PR agent lacks warehouse/dbt tools).
  - Intake/Design touching external systems (both are documentation-only).

## Artefact contracts

The workflow is governed by **artefact contracts**. Orchestrator state transitions require the expected artefacts to exist and be registered.

### Workspace conventions

All artefacts live under a deterministic path:

```text
workspaces/
  tenants/
    <tenant_id>/
      tickets/
        <ticket_id>/
          docs/
          outputs/
          logs/
          dbt_changes/
```

### Required artefacts by agent

| Artefact name | Produced by | Consumed by | Format | Workspace location |
|---|---|---|---|---|
| `docs/intake_summary.md` | Intake | Design, Human | Markdown | `.../docs/intake_summary.md` |
| `docs/design.md` | Design | Profiler, Builder, Human | Markdown | `.../docs/design.md` |
| `outputs/profile_report.json` | Profiler | Builder, QA | JSON | `.../outputs/profile_report.json` |
| `docs/profiling.md` | Profiler | Builder, Human | Markdown | `.../docs/profiling.md` |
| `dbt_changes/models/**` | Builder | QA, PR | SQL | `.../dbt_changes/models/` |
| `dbt_changes/tests/schema.yml` | Builder | QA, PR | YAML | `.../dbt_changes/tests/schema.yml` |
| `outputs/compile_summary.json` | Builder | QA | JSON | `.../outputs/compile_summary.json` |
| `outputs/run_results.json` | QA | PR, Human, Orchestrator | JSON | `.../outputs/run_results.json` |
| `docs/qa_report.md` | QA | PR, Human | Markdown | `.../docs/qa_report.md` |
| `docs/pr_summary.md` | PR | Human | Markdown | `.../docs/pr_summary.md` |

Why this is robust:

- dbt documents `run_results.json` as the output containing node-by-node status and timing for executed nodes, making it a stable QA gate input and PR evidence. citeturn1search2turn1search6  
- Artefacts decouple agents: if an agent crashes or is retried, the next agent can resume from the last valid artefact set rather than relying on conversational memory.

## Collaboration and orchestration flow

### High-level agent collaboration diagram

```mermaid
flowchart TD
  U[User] -->|Ticket created| API[api orchestrator]
  API -->|spawn sessions| GW[gateway OpenClaw]

  GW -->|tool call: publish_artifact| API
  GW -->|tool call: snowflake_sql| API
  GW -->|tool call: dbt_compile| API
  GW -->|tool call: workspace_write_files| API
  GW -->|tool call: dbt_build| API
  GW -->|tool call: git_commit_push| API
  GW -->|tool call: gh_create_pr| API

  API -->|POST /run (allowlisted)| RUN[runner job API]
  RUN -->|exec: dbt/snow/git/gh| EXT[(Snowflake / GitHub)]
  RUN -->|write logs + artefacts| WS[(workspaces)]
  API -->|read artefacts (ro) + event stream| WEB[web UI]

  subgraph Agents
    IA[Intake] --> DA[Design]
    DA -->|Human approval gate| PA[Profiler]
    PA --> BA[Builder]
    BA --> QA[QA]
    QA -->|Human approval gate| PRA[PR]
  end

  GW --- Agents
```

ASCII fallback:

```text
Intake -> Design -> (Human approves) -> Profiler -> Builder -> QA -> (Human approves) -> PR
     \        |              |             |         |           |
      \       v              v             v         v           v
       -> gateway -> api tools -> runner jobs (dbt/snow/git/gh) -> workspaces -> api -> web UI
```

Explanation: Agents collaborate by producing artefacts at each stage; all execution happens through `api` delegating to the runner Job API, never directly from agents.

## Workflow state to agent mapping

This table defines the authoritative “who owns the state” rule. The orchestrator enforces exit conditions noted below.

| Workflow state | Responsible agent | Exit condition | Human approval required |
|---|---|---|---|
| `TENANT_CREATION_REQUESTED` | Tenant Provisioning | Provisioning plan artefact created | No |
| `TENANT_PROVISIONING_RUNNING` | Tenant Provisioning | Provisioning jobs complete + tenant report published | No |
| `TENANT_READY` | Tenant Provisioning | Tenant marked ready in state store | No |
| `TICKET_INTAKE` | Intake | `intake_summary.md` published and ticket brief validated | No |
| `NEEDS_INFO` | Intake | Missing fields resolved and validated | Yes (user supplies info) |
| `DESIGN_REVIEW` | Design | `design.md` published | Yes (Approve design) |
| `PROFILING` | Profiler | `profile_report.json` + `profiling.md` published | No |
| `BUILD` | Builder | dbt files written + compile summary produced | No |
| `QA` | QA | `run_results.json` + `qa_report.md` published | No |
| `READY_FOR_REVIEW` | PR | QA passed + PR draft summary visible | Yes (Approve PR creation) |
| `DONE` | PR | PR URL stored + `pr_summary.md` published | No |
| `FAILED` | Orchestrator (system) | Failure artefacts captured; retry/repair decision logged | Yes (operator decision) |

Note: `FAILED` is intentionally owned by the orchestrator, because it may represent infrastructure or policy failures rather than a single agent’s domain.

## Spawn and termination policy

This section defines how OpenClaw multi-agent orchestration should behave during development.

### Spawn rules

The orchestrator spawns agents deterministically:

- **On state entry**: When a workflow enters a state owned by an agent, the orchestrator starts or resumes the corresponding agent session.
- **On retry**: If a job fails and the retry policy allows it, the same agent is re-run with failure context and prior artefacts.
- **On remediation**: If failure persists, the orchestrator may spawn a dynamic “Repair Agent” (see below).

Session model guidance (strongly recommended for clarity):

- Maintain **one session per (ticket_id, agent_name)** so retries preserve context without cross-contaminating other agents.
- Pass only the minimal context needed: ticket brief + relevant artefacts + tool policy excerpt.

OpenClaw’s multi-agent design explicitly supports separate agent configurations (including tool restrictions) per agent, which aligns with this model. citeturn0search0turn0search22

### Termination rules

An agent run terminates when one of the following occurs:

- **Artefact produced**: the agent has published its required artefacts and the orchestrator has validated them.
- **Exit condition satisfied**: the state’s exit condition is met and recorded.
- **Budget exceeded**: token/time budget exceeded, forcing a controlled failure with logs and partial artefacts.
- **Human gate reached**: if the agent’s purpose is to prepare a human decision, it stops after publishing review artefacts.

### Retry rules

Keep retries conservative and explicit:

- `snowflake_sql` jobs: retry once on transient errors; fail fast on “object not found” (requires human correction in `NEEDS_INFO`).
- `dbt_compile`: retry once if infra/transient; if deterministic compile error persists, route to Builder (or Repair agent if enabled).
- `dbt_build`: retry once; if still failing, transition back to `BUILD` with the failing node list and error excerpts.
- `git_commit_push` / `gh_create_pr`: retry once; if auth/scopes fail, stop and require operator action (credentials/policy).

The key is that retries must not create duplicated external side effects (duplicate branches/PRs). The orchestrator should enforce idempotency via request IDs.

## Optional dynamic agents

These are not required for the initial operating model but fit naturally without changing architecture.

### Repair Agent

**When spawned**  
- After repeated `dbt_build` failure (e.g., two consecutive failures).
- After repeated compile errors when Builder cannot converge.

**Role**  
Diagnose failure from logs + run_results; propose minimal patch; delegate writing via `workspace_write_files`; request re-QA.

**Tool permissions**  
- `workspace_write_files`, `dbt_compile`, `publish_artifact`  
No git/PR tools.

### Performance Optimisation Agent

**When spawned**  
- When QA passes but query runtime exceeds a threshold (from dbt artefacts and logs evidence).

**Role**  
Optimise model SQL (materialisation choice, incremental strategy, clustering keys suggestions) and propose changes.

**Tool permissions**  
- `workspace_write_files`, `dbt_compile`, `publish_artifact`  
Optionally `snowflake_sql` if you allow EXPLAIN plans (keep it tightly controlled).

### Documentation Agent

**When spawned**  
- After QA pass, before PR creation, to enhance docs: model descriptions, column descriptions, and PR narrative.

**Role**  
Improve `schema.yml` descriptions and PR summary while preserving semantics.

**Tool permissions**  
- `workspace_write_files`, `publish_artifact`  
No dbt build, no git/PR tools.

## Security guardrails

This operating model enforces security through overlapping controls (defence-in-depth), aligned with OpenClaw’s emphasis on tool policy and safe exposure.

### Runner-only execution rule

- Only runner executes dbt / Snowflake CLI / git / GitHub CLI.
- Agents must never be granted any tool that enables local shell execution or filesystem access outside the controlled API surface.

### Per-agent tool allowlists

OpenClaw explicitly supports per-agent tool restrictions (allow/deny) in multi-agent setups; this is the mechanism that prevents agents from invoking tools outside their role. citeturn0search0turn0search22  
Because tools are configured and governed at the platform level, agents should not attempt to “invent” capabilities outside the configured tool set. citeturn0search19

### Secrets restricted to runner

- Snowflake private keys/token material and GitHub tokens are only present in runner.
- gateway and api must not have access to those secrets.

### API → runner authentication

- All runner job requests require a bearer token (`runner_auth_token`).
- Runner rejects any request without valid auth and any job not in the allowlist.

### No Docker socket mounting

- The platform must never mount `/var/run/docker.sock` into any container. This prevents privilege escalation from “container compromise” to “host control”.

### Public exposure minimisation

OpenClaw security guidance is explicit: avoid public exposure with tools enabled and fix missing auth or open exposure immediately. citeturn0search1  
For this platform operating model, that translates to:

- runner is not published; internal only.
- gateway and api host ports exist only in dev; in other environments they are behind a reverse proxy and limited by network policy.

## Example end-to-end agent collaboration

This example shows a realistic ticket flowing through the agents, including tool calls and artefacts.

### Ticket

User request:

> “Create `fct_daily_orders` from `RAW.ORDERS` and `RAW.CUSTOMERS`, grain = day, include revenue and order_count by customer_segment. Add tests and open a PR.”

Initial ticket metadata:

- tenant_id: `tenant_retail_001`
- ticket_id: `ticket_0001`
- sources: `RAW.ORDERS`, `RAW.CUSTOMERS`
- acceptance criteria: `dbt build passes`, tests added, docs included.

### Intake Agent (state: `TICKET_INTAKE` → `DESIGN_REVIEW` or `NEEDS_INFO`)

**Actions**
- Validates required fields. If missing join key or date field definition, asks clarifying question.

**Tools used**
- `publish_artifact`

**Artefacts**
- `docs/intake_summary.md` (includes what it understood, missing items, and acceptance criteria rewrite)

**Outputs example (summary)**
- Join key assumption: `orders.customer_id = customers.customer_id`
- Date grain: `orders.order_date` (needs confirmation if timestamp)

If user confirms, orchestrator transitions to `DESIGN_REVIEW`.

### Design Agent (state: `DESIGN_REVIEW`, human gate)

**Actions**
- Defines model plan:
  - `stg_raw__orders`, `stg_raw__customers`
  - `int_orders_enriched` (optional)
  - `fct_daily_orders`

- Defines tests:
  - unique/not_null for keys
  - relationships test `orders.customer_id → customers.customer_id`
  - accepted values for `customer_segment` if enumerated

**Tools used**
- `publish_artifact`

**Artefacts**
- `docs/design.md`

**Human gate**
- User clicks “Approve design”.

### Profiler Agent (state: `PROFILING`)

**Actions**
- Runs profiling queries:
  - counts, null rates for `order_id`, `customer_id`, `order_date`, `order_amount`
  - distinct counts to validate candidate keys
  - relationship check: how many orders have missing customer matches

**Tools used**
- `snowflake_sql` (delegates to runner job)
- `publish_artifact`

**Artefacts**
- `outputs/profile_report.json`
- `docs/profiling.md`

### Builder Agent (state: `BUILD`)

**Actions**
- Generates dbt SQL models + schema tests YAML based on design + profiling evidence.
- Runs compile-only validation.

**Tools used**
- `workspace_write_files` (runner writes generated dbt files into workspace)
- `dbt_compile` (runner compiles; builder inspects compile results)
- `publish_artifact`

**Artefacts**
- `dbt_changes/models/...`
- `dbt_changes/tests/schema.yml`
- `outputs/compile_summary.json`
- Optional `docs/build_plan.md`

### QA Agent (state: `QA`)

**Actions**
- Runs `dbt build` for the affected selection set.
- Parses `run_results.json` and summarises:
  - executed nodes
  - failures (if any)
  - elapsed times

dbt documents that `run_results.json` is produced by dbt invocations and contains status and timing per executed node, making it the canonical QA artefact. citeturn1search2turn1search6

**Tools used**
- `dbt_build`
- `publish_artifact`

**Artefacts**
- `outputs/run_results.json`
- `docs/qa_report.md`

If QA fails, orchestrator loops back to `BUILD` with failure context.

### PR Agent (state: `READY_FOR_REVIEW` → `PR` → `DONE`, human gate)

**Human gate**
- User clicks “Approve PR creation”.

**Actions**
- Creates branch, commits generated changes, opens PR with:
  - summary of intent
  - list of models added/modified
  - QA evidence from `run_results.json` and `qa_report.md`

**Tools used**
- `git_commit_push`
- `gh_create_pr`
- `publish_artifact`

**Artefacts**
- `docs/pr_summary.md` containing PR URL, branch name, file list, QA evidence link references.

### Result

Ticket transitions to `DONE` with PR URL surfaced in UI, plus a complete artefact trail for audit and debugging.

## Operational note on ClawData alignment

This operating model assumes the UI and control plane experience is provided via a FastAPI backend and dashboard that manage OpenClaw agents for data teams—exactly the positioning of the ClawData project. The model above can therefore be implemented as “agent definitions + tool policy + orchestrator state machine + artefact viewer” without altering the runner-split architecture.