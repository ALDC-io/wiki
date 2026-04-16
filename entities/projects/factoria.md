---
tags: [entity, project, factoria, autonomous-data-engineering, openclaw, dbt, multi-agent]
aliases: [Factoria]
sources: [sources/obsidian-import/research/Factoria/Design & Planning/Agent Operating Model (Revised).md, sources/obsidian-import/research/Factoria/Design & Planning/Autonomous Data Engineering Hackathon Blueprint.md, sources/obsidian-import/research/Factoria/Design & Planning/Autonomous Data Engineering Platform Handbook with Runner-Split Docker Architecture.md, sources/obsidian-import/research/Factoria/Design & Planning/System Data Model.md, sources/obsidian-import/research/Factoria/Design & Planning/Technical Diagrams - Diagram Pack.md, sources/obsidian-import/research/Factoria/Gems from the AI.md, sources/obsidian-import/research/Factoria/Implementation/Decisions.md, sources/obsidian-import/research/Factoria/Implementation/Issues.md, sources/obsidian-import/research/Factoria/Implementation/OpenClaw Integration.md, sources/obsidian-import/research/Factoria/Milestones/Factoria v0.3 Runtime.md, sources/obsidian-import/research/Factoria/Milestones/orchestration introspection tools.md, sources/obsidian-import/research/Factoria/POAS/2026-03-06 - POA.md, sources/obsidian-import/research/Factoria/Product Branding/Names Slogans.md, sources/obsidian-import/research/Factoria/Version History/Agent Operating Model.md, sources/obsidian-import/research/Factoria/Version History/Hackathon - Idea 1.md, sources/obsidian-import/research/Factoria/Version History/Project Kick-off steps.md]
created: 2026-04-16
updated: 2026-04-16
---

# Factoria

Factoria is an autonomous data engineering platform that turns data engineering tickets into working dbt model changes, validated by QA, and delivered as GitHub pull requests -- all orchestrated by specialist AI agents. The name references the historical meaning of "trading outpost or manufacturing hub," mapping to a data platform producing analytics assets.

**Tagline**: "From ticket to fact table." / "Autonomous analytics engineering."

## Vision / Goal

Build a controlled, artefact-driven workflow where a user submits a data engineering request and the system autonomously handles the full lifecycle: intake normalization, design planning, source profiling, dbt model generation, QA testing, and PR creation. Two human approval gates (Design Review and Ready-for-Review) ensure safety without sacrificing autonomy.

The platform is built on [[OpenClaw]] as the agent runtime and uses a "runner-split" Docker architecture where agents never execute shell commands directly -- only a dedicated Runner container holds credentials and executes dbt, [[Snowflake]] CLI, git, and GitHub CLI.

## Current State

As of early April 2026, Factoria has reached **v0.3 Runtime** with the following capabilities:

- **Core Runtime**: Ticket API, WorkflowRun lifecycle, orchestrator state machine, AgentRunner, OpenClaw gateway integration
- **Execution Tracking**: AgentSession tracking, WorkflowEvent append-only event log, idempotent completion handling
- **Workspace Runtime**: Per-run workspace isolation, artifact creation and registry
- **State Machine**: TICKET_INTAKE and DESIGN_REVIEW states executing with IntakeAgent and DesignAgent producing `intake.md` and `design.md` artifacts
- **Orchestration Introspection**: Three production-grade tools -- static workflow graph, runtime execution graph, and workflow run inspector
- **Docker**: FastAPI orchestrator and OpenClaw Gateway containers running with networking and permissions configured

The OpenClaw gateway runs successfully inside Docker (`ws://127.0.0.1:18789`), with the API reaching it via the internal Docker network.

## Architecture

### Four-Service Docker Architecture

| Service | Port | Role |
|---------|------|------|
| **web** (Next.js) | 3000 | UI: Kanban tickets, agent activity, artifact viewer |
| **api** (FastAPI) | 8000 | Control plane: workflow engine, tool gateway, event stream |
| **gateway** (OpenClaw) | 18789 | Agent runtime: sessions, routing, streaming |
| **runner** | 9000 (internal) | Execution boundary: dbt, snow, git, gh -- the ONLY place commands run |

### Trust Boundaries

- Runner is the only container with Snowflake/GitHub credentials
- API mounts workspaces read-only; Runner mounts read-write
- No Docker socket mounting anywhere
- All containers run as non-root with read-only filesystems and dropped capabilities
- API authenticates to Runner via bearer token

### Tool Invocation Chain

Agent (OpenClaw session) -> Gateway tool call -> API tool endpoint -> Runner Job API -> execution + artifacts -> API event stream -> Web UI

### Agent Roster

Seven specialist agents with strict per-agent tool allowlists:

| Agent | Purpose | Key Tools |
|-------|---------|-----------|
| Tenant Provisioning | Bootstrap analytics environment | snowflake_sql, workspace_write, dbt_build (smoke) |
| Intake | Normalize ticket, detect gaps | publish_artifact only |
| Design | Create modeling plan | publish_artifact only |
| Profiler | Profile sources via SQL | snowflake_sql, publish_artifact |
| Builder | Generate dbt models + tests | workspace_write, dbt_compile, publish_artifact |
| QA | Run dbt build/test, produce QA report | dbt_build, publish_artifact |
| PR | Create branch, commit, open PR | git_commit_push, gh_create_pr, publish_artifact |

## Key Decisions

1. **Runner-split is non-negotiable**: Agents never run shell commands. All execution goes through Runner's allowlisted Job API. This is the primary security boundary.
2. **Artefact-driven handoffs**: Each agent produces well-defined artifacts (design.md, profile_report.json, run_results.json, etc.) rather than relying on conversational memory between agents.
3. **Event-driven orchestration**: Moved from synchronous advance-after-agent to event-driven architecture where agents complete asynchronously and emit completion events.
4. **State handler pattern**: State-to-function mapping (`STATE_AGENT_MAP`) instead of if/else chains for clean agent routing.
5. **Workflow-run-aware from day 1**: Every ticket creation generates a `trace_id` and explicit `attempt` number for clean retries and correlation.
6. **Workspace isolation per run**: Each workflow run gets its own workspace directory to prevent compile logs, QA logs, and artifacts from different runs corrupting each other.
7. **SQLite now, Postgres later**: SQLite for local dev with schema designed for Postgres compatibility in production.
8. **Deterministic dbt selection sets**: The orchestrator (not agents) computes and enforces `--select` scope for dbt operations. QA must never run unconstrained builds.

## Data Model

Core entities: Tenants, Tickets, WorkflowRuns, WorkflowEvents (append-only), Artifacts, RunnerJobs, AgentSessions, GateApprovals, SelectionSets. All support trace_id correlation and idempotent operations via request_id uniqueness.

## Workflow States

`TENANT_CREATION_REQUESTED` -> `TENANT_PROVISIONING_RUNNING` -> `TENANT_READY` -> `TICKET_INTAKE` -> `NEEDS_INFO` / `DESIGN_REVIEW` (human gate) -> `PROFILING` -> `BUILD` -> `QA` -> `READY_FOR_REVIEW` (human gate) -> `PR_CREATION` -> `DONE` / `FAILED`

## Version History

| Version | Milestone |
|---------|-----------|
| v0.1 | Platform skeleton |
| v0.2 | Workflow engine |
| v0.3 | Runtime layer (OpenClaw integration, agent sessions, artifact registry) |
| v0.4 (next) | Agent execution layer -- AgentRunner connecting workflow engine to OpenClaw agents |
| v0.5 | Runner execution boundary |
| v0.6 | Artifact management |
| v0.7 | UI / Kanban |

## Origin

Started as a hackathon idea at ALDC: an autonomous data engineering workflow using [[OpenClaw]] and ClawData as the agent runtime, with a Kanban UI showing visible agent activity. The initial concept combined "Demo Tenant-in-a-Box Provisioner" with "Ticket-to-PR Data Modelling Autopilot" into one continuous demo story.

## Open Questions / Next Steps

- Implementing the Agent Runner (~150 lines) to connect the workflow engine to OpenClaw agents for autonomous execution
- Adding the Runner execution container for dbt/snow/git/gh isolation
- Building the Kanban UI with React Flow for agent interaction graph visualization
- OpenTelemetry instrumentation for trace-per-ticket observability
- Optional dynamic agents: Repair Agent (for repeated failures), Performance Optimization Agent, Documentation Agent

## See Also

- [[openclaw]] -- the agent runtime powering Factoria's multi-agent system
- [[cce]] -- ALDC's enhanced Claude Code system (separate from Factoria's agent approach)
- [[monorepo-research]] -- analysis that includes Factoria in the proposed monorepo structure
