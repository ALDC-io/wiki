---
tags: [project, neurospect, trading, ai, platform]
aliases: [NeuroSpect, neurospect-platform]
created: 2026-05-15
updated: 2026-05-17
---

# NeuroSpect

AI trading intelligence platform for ICT/Smart Money Concepts traders. Data-foundation-first architecture evolving from a deployed trading journal + AI coach into a full research, backtesting, scoring, and automation platform.

## Status

- **Phase:** 0 (Marketing + Demo) in progress, v3 roadmap restructured 2026-05-15
- **Repo:** `C:\Users\PaulRussell\repos\neurospect` (monorepo)
- **Team:** Paul (full-stack), Vlad (TBD)
- **Deployed:** API on Render, App on Cloudflare Pages, Marketing on CDN
- **Linear:** NEU workspace, 23 tickets

## Product Hierarchy (v3)

```
NeuroSpect (company / product brand)
├── Trader Workspace         — Journal, analytics, behavior metrics
├── Prop Shield              — Prop firm rule tracking, tilt lockouts
├── ICT Event Engine         — Programmable ICT event detection
├── EdgeLab                  — Event-driven backtesting, features
├── NeuroSpect Mentor        — AI coaching, RAG citations, trade review
├── Edge Forensics           — Loss patterns → testable hypotheses
├── NeuroCore                — Knowledge/retrieval (hybrid 3-signal search)
├── NSLM                     — ICT-aware language model
├── NeuroGraph               — Persistent trading intelligence graph
├── NeuroScore               — Risk-adjusted trader ranking
├── NeuroFund Elite          — Company-sponsored rewards/eligibility
├── NeuroQuant               — Production model layer
└── NeuroTrader Agent        — Shadow → Paper → Live automation
```

## Roadmap (v3 — 13 phases)

| Phase | Name | Status |
|---|---|---|
| 0 | Marketing + Demo | in_progress |
| 1 | Trading Data Foundation | not_started |
| 2 | Trader Workspace | not_started |
| 3 | Prop Shield (FIRST REVENUE) | not_started |
| 3-NG | NeuroGraph (plan mode first) | not_started |
| 4 | ICT Event Intelligence | not_started |
| 5 | EdgeLab Core (5A/5B/5C) | not_started |
| 6 | AI Trade Review + RAG | not_started |
| 7 | Edge Forensics | not_started |
| 8 | NeuroScore + Leaderboard | not_started |
| 9 | NeuroFund Elite Rewards | not_started |
| 10 | Allocation Watchlist | not_started |
| 11 | Advanced ML Research | not_started |

Build order: `data → risk → events → backtesting → AI → forensics → scoring → rewards → ML`

Critical path to first revenue: Phase 0 → 1 → 2 → 3 (~16 weeks)

## What's Built (deployed, production)

- Trade journal with 100+ ICT-specific fields, 17 enums
- 7 analytics endpoints (summary, by-setup, by-session, by-instrument, etc.)
- Claude AI coaching (Anthropic SDK, prompt caching)
- Tradovate REST integration (auth + fills)
- Discord OAuth + JWT auth
- Cloudflare R2 screenshot storage
- 36K-line ICT wiki (111 files, 5 course modules, 7 entry models)
- React 18 marketing site with interactive demos
- Orchestrator UI (12-tab command center with session API)

## v3 Restructure (2026-05-15)

Major roadmap pivot from coaching-first (v2) to data-foundation-first (v3):
- 17 phases → 13 phases, Track C eliminated (compliance embedded per-phase)
- 7 new components added (Trader Workspace, Prop Shield, ICT Event Engine, Edge Forensics, NeuroGraph, NeuroScore, NeuroFund Elite)
- NeuroFund Elite: compliance-safe rewards program (NOT pooled capital)
- 15 slash commands created for phase execution
- Orchestrator with autonomous Pipeline execution (parallel Claude sessions)
- NeuroGraph: persistent trading intelligence graph positioned after Phase 2

## Key Decisions

- **Data first, AI later:** Verified trading data foundation before RAG/coaching. RAG moved from Phase 1 to Phase 6.
- **Prop Shield as paid wedge:** Prop firm rule protection monetizable before AI coaching.
- **NeuroFund compliance:** Approved: "company-sponsored rewards funded from revenue." Forbidden: "pooled capital," "subscriber money invested."
- **NeuroGraph early:** Positioned after Phase 2 (plan mode first) so all downstream phases benefit from accumulated intelligence.
- **Autonomous pipeline:** Orchestrator spawns `claude -p` sessions with full slash command context injected.

## Related

- Orchestrator: `platform/orchestrator/` (http://localhost:8766)
- Slash commands: `.claude/commands/ns-phase*.md`
- Wiki: `neurospect/wiki/`
- Marketing: `neurospect/neurospect-ui/`
