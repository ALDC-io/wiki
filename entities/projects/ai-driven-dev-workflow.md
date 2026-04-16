---
tags: [entity, project, ai-dev-flow, agentic-coding, developer-workflow, paperclip]
aliases: [AI-Driven Dev Workflow, ai-dev-flow, ALDC Agentic Coding Guidelines]
sources: [sources/obsidian-import/research/AI-Driven Dev Workflow/ai-dev-flow-v2/differences.md, sources/obsidian-import/research/AI-Driven Dev Workflow/ai-dev-flow-v3/Beads + HumanLayer Research.md, sources/obsidian-import/research/AI-Driven Dev Workflow/ai-dev-flow-v3/Major Improvements - Required.md, sources/obsidian-import/research/AI-Driven Dev Workflow/ai-dev-flow-v3.1-tactical-agentic-framework/ChatGPT - Thinker.md, sources/obsidian-import/research/AI-Driven Dev Workflow/ai-dev-flow-v3.1-tactical-agentic-framework/Claude.md, sources/obsidian-import/research/AI-Driven Dev Workflow/ai-dev-flow-v3.1-tactical-agentic-framework/Current Workflow Guides/Agentic Coding & Development Workflow Guide.md, sources/obsidian-import/research/AI-Driven Dev Workflow/ALDC-Agentic-Coding-Guidelines/ALDC Agentic Coding Guidelines-v0.1.md, sources/obsidian-import/research/AI-Driven Dev Workflow/ALDC-Agentic-Coding-Guidelines/ALDC Guidelines Integration with ai-dev-flow guidelines.md, sources/obsidian-import/research/AI-Driven Dev Workflow/Deep Research Prompt.md, sources/obsidian-import/research/AI-Driven Dev Workflow/MVP Implementation Plan.md]
created: 2026-04-16
updated: 2026-04-16
---

# AI-Driven Dev Workflow

A multi-version research project developing a structured, artifact-driven methodology for AI-assisted software development. The project spans from a personal CLI harness (v2) through a tactical agentic framework (v3.1) to a comprehensive set of ALDC team guidelines for using [[CCE]] in production. The core thesis: the real breakthrough in agentic development is not "more agents" but **better state management**.

## Vision / Goal

Create "the operating system for turning ideas into production-safe code changes." Rather than competing with coding agents directly, this workflow becomes the **workflow spine** that agents plug into -- owning the spec, plan, state machine, guardrails, evidence, handoffs, review trail, and deployment proof.

The strongest positioning: **"Every change is planned, executed, verified, and explainable."**

## Current State

The project has evolved through several versions, each building on the last:

### v2 -- CLI-Based Workflow
The original implementation using a bash CLI wrapper (`ai` command) that orchestrated skills (prompt modules) through a structured lifecycle: `grill-me` -> `write-a-prd` -> `prd-to-plan` -> `tdd` -> `triage-issue`. Integrated with Claude Code via AutoHotkey for UI automation and Obsidian for persistent knowledge storage. Key innovation was treating the workflow as a repeatable SDLC rather than ad-hoc prompting.

### v3 -- Control Graph Research (Beads + HumanLayer)
Research phase incorporating ideas from Beads (durable graph-based memory, dependency-aware work items, formulas/molecules) and HumanLayer (deterministic human oversight, async agent orchestration, parallel worktree swarms). Key proposed feature: **Flow Molecules** -- reusable, graph-backed, human-gated execution templates for classes of development work (CRUD feature, migration, API integration, etc.).

### v3.1 -- Tactical Agentic Framework
The current practical framework defining a dual-tool workflow:
- **ChatGPT** as architecture coach, systems critic, sequencing advisor
- **Claude Code** as repo reader, planner, refactorer, implementer

Core principle: **"Do not let the live chat be the source of truth."** All architecture, migration state, current phase, and next actions live in repo files that agents can re-read at any time.

### ALDC Agentic Coding Guidelines (v0.2)
Production team guidelines for using [[CCE]], incorporating measured data:
- ~33% first-attempt success rate for autonomous Claude Code
- 2.74x security vulnerability rate in AI-co-authored code
- 50% token savings in clean codebases
- 40% context utilization threshold before quality degrades
- 90% improvement with orchestrator-worker multi-agent patterns
- 80% fewer false starts with plan-before-implement discipline

### ALDC Guidelines Integration Plan (v0.7)
A comprehensive integration spec merging the ALDC Guidelines with ai-dev-flow into a production system with:
- **5 agent roles**: devflow-feature (orchestrator), devflow-builder, devflow-reviewer, devflow-qa, devflow-sre
- **Gate/Seal/Publish pipeline**: `devflow orient` -> `devflow gate` -> work -> `devflow seal` -> `devflow publish-artifacts`
- **Iron Law of Verification**: No completion claim is valid without fresh verification evidence
- **Artifact contract**: 9 mandatory artifacts (PRD, Plan, Architecture, TDD Summary, Review Report, QA Evidence, Security Review, Deploy Steps, Verification Manifest)
- **CEO agent** for backlog triage, roster health monitoring, and escalation routing
- **Connector-specific skills** for data pipeline features (schema gates, idempotency, contract tests)

## Key Decisions

1. **Architecture lives in docs, not chat**: State survives compaction and session resets via repo-based files
2. **Separate stable truth from operational truth**: `target-architecture.md` (rarely changes) vs `migration-tracker.yaml` (changes constantly) vs `current-phase.md` (changes every slice)
3. **ChatGPT critiques, Claude executes**: Clear separation of planning/critique vs implementation roles
4. **Enforce by code, not documentation**: Gates return exit codes. Artifacts are validated by schema. Advice that cannot be checked is not a gate.
5. **Single-purpose skills**: A skill does one thing and produces one artifact
6. **Context isolation**: Each agent phase starts clean -- no phase inherits prior context pollution
7. **Artifact-first verification**: Phase completion is defined by artifact presence + content validity, not agent self-report
8. **Model tier routing**: Haiku for search/reading, Sonnet for standard implementation, Opus for architecture/security/complex debugging -- with justification required for Opus usage

## Recommended File System

```
/docs/architecture/     -- stable architecture, ADRs
/planning/              -- migration-tracker.yaml, current-sprint.md, progress-log.md
/.claude/context/       -- architecture-summary.md, current-phase.md, next-actions.md
```

## Standard Development Loop

1. Decide the next slice (scope, out-of-scope, files to change, tests to protect)
2. Make planning files current
3. Give Claude a tightly scoped implementation prompt
4. Review Claude's summary
5. Record the slice in all planning files
6. Only then move on

## Open Questions / Next Steps

- Building the `devflow` CLI (orient, gate, seal, publish-artifacts, metrics commands)
- Implementing the Paperclip integration for issue/subtask management
- Creating the new skills: security-review, architecture-diagrams, code-review, qa, deploy
- Agent refactoring from monolithic devflow-feature to scoped phase agents
- Pilot rollout with one connector feature, then validation with three fully autonomous features
- Longer-term: graph-native feature memory, parallel worktree swarms, Flow Molecules, async decision inbox

## See Also

- [[cce]] -- the enhanced Claude Code system these guidelines operate within
- [[factoria]] -- a related project applying multi-agent orchestration to data engineering specifically
- [[monorepo-research]] -- analysis of how monorepo structure improves agentic development
