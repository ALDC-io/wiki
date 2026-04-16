---
tags: [entity, project, cce, claude-code, zeus, agentic-coding, developer-tools]
aliases: [CCE, Claude Code Enhanced]
sources: [sources/obsidian-import/research/CCE/Design & Planning/Current State/Current State - Design.md, sources/obsidian-import/research/CCE/Design & Planning/Current State/Current State - Issues.md, sources/obsidian-import/research/CCE/Hints for Claude Usage.md, sources/obsidian-import/research/CCE/Setup/Zeus Onboarding Doc - Steps.md]
created: 2026-04-16
updated: 2026-04-16
---

# CCE (Claude Code Enhanced)

CCE is ALDC's enhanced layer on top of Claude Code that adds persistent memory, team collaboration, auto-learning, and a skill/hook system powered by [[Zeus Memory]]. It transforms Claude Code from an individual coding assistant into a team-aware, continuously-improving development system.

## Vision / Goal

Make Claude Code a production-grade team development tool by adding the infrastructure that raw Claude Code lacks: persistent cross-session memory, team messaging and presence, automated learning capture, hook-based enforcement of coding standards, and a shared skill library. The guiding philosophy is that "the agent is only as good as the system around it."

## Current State

CCE is actively used within ALDC (as of March-April 2026). The system includes:

- **Zeus Memory integration** for cross-session knowledge persistence and team-wide learning
- **Hook system** (SessionStart, PostToolUse, Stop, SessionEnd) that auto-updates from Zeus, checks inbox, logs tool usage, and captures learnings
- **Team messaging** via `/msg` command surfaced during work sessions
- **Presence/heartbeat** broadcasting (30-second intervals) so team members see who is online
- **Status line** showing task count, pending items, daily learnings, and online users
- **Auto-learn** that captures session metadata (tools used, files modified, duration) to Zeus Memory on session end
- **178 skills** and **14 commands** in the skill library
- **Tool usage logger** with a 50-tool checkpoint for learning capture

The design documents for current state (Design and Issues) exist as placeholders, suggesting ongoing iteration.

## Key Decisions

- **Hook-based enforcement over CLAUDE.md instructions**: Hooks fire deterministically regardless of context state, while CLAUDE.md rules degrade as context fills. Critical rules go in hooks; style guidance stays in CLAUDE.md.
- **Zeus as the central memory store**: All learnings, team messages, task tracking, and hook updates flow through Zeus Memory's API.
- **HMAC-SHA256 verification for hook updates**: All auto-updated hooks from Zeus undergo signature verification, SHA256 integrity checks, syntax validation, and backup of previous versions.
- **Per-session auto-learn**: Every session's work is captured automatically rather than relying on manual documentation.

## Setup

Onboarding involves a quick 5-minute process:
1. Create `~/.env` with Zeus API URL and personal API key
2. Install the auto-updater hook script from the `zeus-memory` GitHub repo
3. Copy the settings.json from the onboarding doc
4. Run the updater script
5. Start Claude Code -- should display `[CCE] Online: <username> ...`

## Open Questions / Next Steps

- Integration with a [[monorepo-research]] structure would make CCE's 178 skills available across all ALDC services, not just the `claude_code_enhanced` repo
- Path-scoped `.claude/rules/` would allow Python rules to stay separate from TypeScript context
- Cross-service agent delegation (spawning parallel Claude agents across packages) is only possible in a monorepo where all code shares one worktree

## See Also

- [[zeus-memory]] -- the backend memory and API service powering CCE
- [[ai-driven-dev-workflow]] -- the broader workflow methodology CCE operates within
- [[monorepo-research]] -- analysis of consolidating repos to maximize CCE benefits
- [[factoria]] -- another ALDC project that uses OpenClaw for agent orchestration
