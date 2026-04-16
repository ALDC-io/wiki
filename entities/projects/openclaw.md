---
tags: [entity, project, openclaw, agent-runtime, reference-material]
aliases: [OpenClaw, ClawData]
sources: [sources/obsidian-import/research/OpenClaw/Articles.md]
created: 2026-04-16
updated: 2026-04-16
---

# OpenClaw

OpenClaw is an open-source agent runtime and gateway that ALDC uses as the foundation for multi-agent orchestration in projects like [[Factoria]]. It provides session management, agent routing, per-agent tool restrictions (allow/deny), streaming output, and an always-on gateway architecture.

## Vision / Goal

Provide a production-grade agent runtime for data engineering workflows, with particular strengths in multi-agent isolation, deterministic tool policy enforcement, and session-based orchestration.

## Current State

OpenClaw is used as a dependency/foundation in ALDC projects rather than being an ALDC-developed product. The research folder contains reference articles about OpenClaw and related concepts:

- [OpenClaw, ClawData, and What AI Agents Mean for the Future of Data Engineering](https://medium.com/@kppavan1510/openclaw-clawdata-and-what-ai-agents-mean-for-the-future-of-data-engineering-4d6011f4b3e9) -- overview of OpenClaw's positioning for data teams
- [Lean DAO Company Framework](https://www.linkedin.com/pulse/lean-dao-company-framework-humans-ai-humanoid-workers-jakub-polec-mm5af/) -- related framework for human + AI organizational structures

## Role in ALDC Projects

### In Factoria
OpenClaw serves as the agent runtime providing:
- **Gateway** on port 18789 (WebSocket + HTTP) for agent sessions
- **Per-agent tool allow/deny policies** enforced at runtime (not just in prompts)
- **Session management** with stable session keys per ticket for persistent context
- **Streaming output** via Server-Sent Events for "live typing" UI theatre
- **Tool invocation** via `POST /tools/invoke` gated by gateway auth and tool policy
- **Agent-to-agent communication** via Session Tools (list sessions, fetch history, send messages)

### ClawData
ClawData is the companion project -- "an easy-to-use dashboard and FastAPI backend for managing OpenClaw agents built for data teams." It includes:
- FastAPI backend + Next.js UI
- Agent configuration, chat, skills browsing, and cost tracking
- Skills directory with data engineering skill definitions
- Templates directory with Jinja2 templates for dbt and other artifacts
- Docker quick-start with SQLite persistence

Factoria's architecture extends ClawData with tenant provisioning and ticket-to-PR automation modules.

## Key Capabilities

- **Multi-agent isolation**: Per-agent sandboxes and tool allow/deny lists for clear security boundaries
- **Channel routing**: Rules pick one agent per inbound message using bindings and fallbacks
- **OpenAI-compatible endpoints**: `/v1/chat/completions` and `/v1/responses` with stable user strings for session key derivation
- **Security model**: Trust boundaries between operators (control-plane access), users (restricted access), and adversarial isolation (separate gateways per trust boundary)

## Open Questions / Next Steps

- Monitoring OpenClaw releases for new features relevant to Factoria
- Evaluating whether to contribute upstream improvements from Factoria integration work
- Assessing OpenClaw's roadmap alignment with ALDC's multi-agent requirements

## See Also

- [[factoria]] -- the primary ALDC project built on OpenClaw
- [[cce]] -- uses a different approach (hooks + Zeus Memory) rather than OpenClaw
