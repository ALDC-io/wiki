---
tags: [ticket, internal, shipyard, team, culture, ai]
aliases: [SHIP-002, team-pulse]
sources: []
created: 2026-05-04
updated: 2026-05-04
---

# SHIP-002 — Team Pulse: Highs/Lows/Celebrations + Coffee Recognition

Build a tool that synthesizes team activity across Jira, the LLM Wiki, and Zeus Memory to generate a per-team-member and company-wide summary of Highs, Lows, Celebrations, and peer recognition ("buy them a coffee").

## Status

Planned — Research & Tooling lane (sprint-agnostic).

## Vision

A weekly/sprint-end report (and eventually a UI) that answers:
- **What did each person ship this week?** (Highs)
- **What blocked them or went wrong?** (Lows)
- **What deserves a shout-out?** (Celebrations — milestones, heroic fixes, first contributions)
- **Who helped whom?** (Coffee recognition — collaboration, unblocking, knowledge sharing)
- **Company-wide pulse** — cross-team patterns, overall velocity, shared wins, recurring blockers

## Data Sources

| Source | What it provides |
|--------|-----------------|
| **Jira** (all projects) | Tickets completed, status transitions, assignees, sprint data, comments (collaboration signals) |
| **LLM Wiki** | Session logs, standup notes, workplan completions, decision logs, action items completed |
| **Zeus Memory** | `cce_success_log`, `cce_failed_approach`, `cce_decision_log` — captures the nuance Jira misses |
| **Git** (optional) | Commit activity, PR reviews, co-authorship — who's reviewing whose code |

## Per-Team-Member Output

```
## Paul Russell — Week of 2026-05-04

### Highs
- FU92-394: Identified and fixed Viant connector timeout bug (actuals restored for Fusion92)
- GP-217: CI/CD pipeline gated + Azure right-sizing (~$265/mo saved)

### Lows
- FU92-395: DAX permissions bug still open, blocking Fusion92 QA

### Celebrations
- First end-to-end use of new Docker CI pipeline for connector deployment

### Buy a Coffee
- JK — for setting up the Docker CI workflow on workstation-agent that made the Viant fix deployable
```

## Company-Wide Output

```
## ALDC Pulse — Week of 2026-05-04

### Product Updates
What shipped to clients this week and what it enables:
- Fusion92 Viant data pipeline restored — actuals now reporting in DAX after 30-day gap
  → Enables: Fusion92 can finalize monthly QA and resume Viant flight reporting
- Prefect infrastructure right-sized (~$265/mo saved)
  → Enables: sustainable self-hosted Prefect at scale without cloud cost pressure

### Development Updates
What moved forward internally and what it unlocks:
- Docker CI pipeline validated end-to-end on connector repo
  → Enables: automated builds gated behind quality checks — no more manual build.sh deploys
- Jira board restructured with 3 swimlanes (Support / Development / Research & Tooling)
  → Enables: visibility into all work types, support SLAs trackable separately from sprint velocity
- Viant connector hardened with timeout + error handling
  → Enables: connectors can no longer hang indefinitely and block the entire worker queue

### Potential Demos
Ready to show internally or to clients:
- Prefect CI/CD pipeline: quality gate → Docker build → environment promotion (QA → UAT → Prod)
- Operational monitoring: flight_check.py + monitor.py — data freshness, task health, share integrity
- Wiki-driven boot prompts: any team member can resume any workstream cold via copy-paste prompt

### Watch Items
- 2 open Fusion92 support tickets (FU92-394 in-progress, FU92-395 to-do)
- Monthly QA deadline this week

### Product Readiness

Zeus Memory                  ████████░░░░░░░░░░░░  40%
  ✅ Streamlit prototype     ✅ Lululemon use case
  ✅ Zeus API integration     ⬜ Multi-tenant isolation
  ⬜ Drift detection engine   ⬜ Production deployment

Zeus Chat                    ██████░░░░░░░░░░░░░░  30%
  ✅ Core conversation loop   ✅ Memory retrieval
  ⬜ Multi-source grounding   ⬜ Approval workflows
  ⬜ Production deployment    ⬜ Client-facing auth

Eclipse Exp (v2.1)           ████████████░░░░░░░░  60%
  ✅ FastAPI + Next.js 15     ✅ PostgreSQL RLS
  ✅ 50 connectors            ✅ 87 migrations
  ⬜ Strangler-fig cutover    ⬜ AI onboarding

### Celebrations
- New CI/CD pipeline validated end-to-end on connector repo

### Coffee Chain
- Paul → JK (Docker CI setup enabled Viant fix deployment)
```

## Coffee Recognition Logic

Signals that indicate someone deserves a coffee:
- **Unblocked someone** — their PR review/merge unblocked another person's ticket
- **Cross-repo collaboration** — contributed to a ticket outside their primary repo
- **Knowledge sharing** — wiki updates, documented a process, onboarded someone
- **Firefighting** — jumped on a support issue that wasn't their responsibility
- **Invisible work** — infrastructure, tooling, monitoring that prevents future issues

## Implementation Options

### Option A: CLI Tool (MVP)
- Python script in shipyard repo
- Pulls from Jira API + reads wiki files + queries Zeus Memory API
- Outputs markdown report
- Run weekly or on-demand

### Option B: Claude Code Skill
- `/team-pulse` skill that generates the report in-session
- Can be interactive — "generate this week's pulse" or "who should get a coffee this sprint?"

### Option C: UI (Claude Design)
- Dashboard showing team pulse over time
- Coffee leaderboard — who's been recognized most, who hasn't been recognized (gap detection)
- Trend lines on highs/lows per person and company-wide
- Paul may use Claude Design for this

### Recommended Path
A → B → C. Start with the CLI to prove the data synthesis works, wrap it as a skill, then build the UI once the data model is solid.

## Open Questions

- What's the right cadence? Weekly? Per-sprint? On-demand?
- Should the coffee recognition be anonymous or attributed?
- Should this integrate with Slack (post to a channel)?
- Which Jira projects to scan? All, or a configurable list?
- Privacy: should individual lows be visible to everyone or only to the person + their manager?

## Boot Prompt

````
You are building SHIP-002 — Team Pulse, a tool that generates Highs/Lows/Celebrations and Coffee Recognition for ALDC team members.

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this ticket: `C:\Users\PaulRussell\repos\wiki\tickets\gep\SHIP-002.md`
3. Read the Jira board structure: `C:\Users\PaulRussell\repos\wiki\processes\operations\jira-board-structure.md`

Data sources to integrate:
- Jira: use Atlassian MCP tools (cloudId: 239c1bf0-93f4-4201-95fe-ab73ce4a6eff). Scan all projects for completed tickets, transitions, comments.
- Wiki: read standup/, workplan/, log.md, tickets/ for session outcomes
- Zeus Memory: query cce_success_log, cce_failed_approach, cce_decision_log via CCX MCP tools
- Git (optional): git log across repos for commit/PR activity

Team members: JK, Lori, Mike, Paul, Vlad (from session startup hook)

Start with Option A (CLI MVP) — Python script that pulls from all sources and outputs a markdown report. Focus on getting the data synthesis right before worrying about UI.

Paul handles git commits.
````

## See Also

- [[jira-board-structure]] — board swimlanes and team workflow
- [[observability-platform]] — company-wide monitoring (complementary — that's systems health, this is people health)
- [[cce]] — CCE/Zeus Memory integration points
