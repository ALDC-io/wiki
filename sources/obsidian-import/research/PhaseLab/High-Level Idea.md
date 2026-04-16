Yes — this is possible, but only if you treat it as a **controlled engineering system**, not just “let agents code in sandboxes.”

## The core idea

You want two layers:

### 1. **Phase Lab**

The product-facing interface for:

- generating variants
    
- comparing them
    
- selecting winners
    
- refining directions
    

### 2. **A repo-agnostic execution engine**

The production-oriented layer for:

- cloning repos
    
- understanding project constraints
    
- making changes safely
    
- running tests and checks
    
- producing merge-ready outputs
    

That second layer should probably be its **own repo**.

---

# Recommended repo name

## **phase-forge**

Why this works:

- fits with **Phase Lab**
    
- sounds production-oriented
    
- implies building, not just exploring
    
- repo agnostic
    
- good for internal and external positioning
    

## Positioning

**Phase Forge** is the execution engine that applies controlled, testable, production-quality changes to real codebases in isolated agent sandboxes.

---

# What it is for

**Phase Forge** is a repo-agnostic agent sandbox system that can:

- run against real repositories
    
- understand the repo’s constraints
    
- make scoped code changes
    
- run quality gates
    
- validate outputs
    
- return reviewable, merge-ready variants
    

It is the bridge between:

- **prototype exploration**
    
- and
    
- **real production implementation**
    

---

# The value of it

## For management / product teams

They can generate ideas quickly without blocking engineering.

## For engineering

Those ideas do not have to die as throwaway prototypes.

## For the business

You get:

- faster iteration
    
- less rework
    
- better consistency
    
- safer experimentation
    
- repeatable delivery workflows across repos
    

## The real value

It lets your team move from:

> “someone mocked up a concept”

to:

> “we have a guarded, testable implementation path for that concept”

---

# Can guardrails make management-generated work production quality?

## Honest answer

**Not automatically.**

You cannot guarantee production quality just by asking an agent nicely.

## But you can get very close by enforcing gates

The right model is:

> **Agents generate**  
> **Systems verify**  
> **Humans approve**

So the output becomes “production-eligible” only if it passes mandatory checks.

---

# Production-quality guardrails

These should be **hard gates**, not suggestions.

## 1. Repo contract

Each repo must define:

- package manager
    
- build command
    
- test commands
    
- lint/typecheck commands
    
- preview/start command
    
- required environment assumptions
    
- forbidden paths
    
- ownership rules
    

Example:

```yaml
repo:
  name: eclipse-web
  language: typescript
  package_manager: pnpm

commands:
  install: pnpm install --frozen-lockfile
  build: pnpm build
  lint: pnpm lint
  typecheck: pnpm typecheck
  test: pnpm test
  preview: pnpm dev

constraints:
  forbidden_paths:
    - infra/
    - migrations/
  max_files_changed: 25
  require_tests_for_changed_logic: true
```

## 2. Change scope rules

Every run should declare:

- target feature
    
- allowed directories
    
- allowed change types
    
- expected outputs
    

## 3. Mandatory verification pipeline

Every sandbox run should execute:

- install
    
- format
    
- lint
    
- typecheck
    
- unit tests
    
- integration tests where possible
    
- preview health check
    
- screenshot capture
    
- diff summary
    

## 4. Policy checks

Use static rules such as:

- no secrets
    
- no unsafe dependency additions
    
- no forbidden network calls
    
- no direct schema changes unless approved
    
- no bypass of auth or permission layers
    

## 5. Code review summary

Each run should produce:

- changed files
    
- reasoning summary
    
- risk summary
    
- test results
    
- rollback notes
    

## 6. Human approval

No direct merge by default.  
Variants should become:

- PRs
    
- patch bundles
    
- review branches
    

---

# Snowflake support

Yes, but do it in phases.

## Best approach

### Phase 1: Snapshot mode

For a feature, extract only the needed data into:

- JSON
    
- CSV
    
- DuckDB
    
- SQLite
    
- API snapshots
    

Use that inside the sandbox.

This is the safest and fastest route.

### Phase 2: Read-only data mode

Allow sandboxes to use:

- read-only Snowflake credentials
    
- restricted schemas/views
    
- query limits
    
- logging/audit
    

### Phase 3: Feature data packages

Define a feature setup file that states:

- schemas needed
    
- tables/views needed
    
- columns needed
    
- joins
    
- filters
    
- sample sizes
    
- masking rules
    
- supporting artifacts
    

That gives each sandbox the **minimum viable world** needed for the feature.

---

# What is already implemented in Phase Lab

Phase Lab already gives you a strong front-end workflow:

## Working today

- brief input
    
- canonical spec generation
    
- design lane generation
    
- multi-variant generation
    
- SSE live progress
    
- screenshots
    
- evaluator scoring
    
- recommendation
    
- human review
    
- selection
    
- notes
    
- refinement
    
- persistence
    
- recent run history
    
- child refinement runs
    
- preview rendering
    

## What it currently is

Phase Lab is already a **good prototype exploration product**.

## What it is not yet

It is not yet:

- repo-backed
    
- production-gated
    
- cross-repo
    
- data-aware at the warehouse level
    

That is where **Phase Forge** comes in.

---

# How to make it repo agnostic

The key is to stop hardcoding assumptions and move to a **repo adapter contract**.

## Step 1: Introduce a repo manifest

Every supported repo should define a file like:

```yaml
phase-forge.yaml:
  repo_type: web-app
  framework: nextjs
  language: typescript

  install: pnpm install --frozen-lockfile
  build: pnpm build
  lint: pnpm lint
  typecheck: pnpm typecheck
  test: pnpm test
  preview: pnpm dev

  entry_points:
    - apps/web
    - src

  quality_gates:
    require_build: true
    require_lint: true
    require_typecheck: true
    require_tests: true

  sandbox:
    package_manager_cache: true
    node_version: 20
```

## Step 2: Create repo adapters

Start with adapters for:

- Next.js / React
    
- Vite / React
    
- Node API
    
- Monorepo TypeScript
    

## Step 3: Separate generation from execution

The system should have four stages:

### A. Understand

Read repo manifest, docs, target feature scope.

### B. Plan

Generate a scoped implementation plan.

### C. Execute

Run in isolated sandboxes.

### D. Verify

Run mandatory gates.

## Step 4: Make outputs standardized

Every run should output:

- patch or branch
    
- screenshots
    
- logs
    
- test results
    
- review summary
    
- artifact bundle
    

---

# Recommended architecture

## Product layer

### Phase Lab

For:

- prototyping
    
- comparison
    
- review
    
- refinement
    

## Execution layer

### Phase Forge

For:

- repo ingestion
    
- sandbox execution
    
- code change generation
    
- quality verification
    
- PR/patch output
    

## Future context/compliance layer

- OpenTribe for context
    
- CPMA for policy/compliance
    

---

# Technical architecture

```text
User request
  -> Phase Lab UI
  -> Run planner
  -> Repo adapter
  -> Sandbox orchestrator
  -> Agent execution
  -> Verification pipeline
  -> Artifact store
  -> Review UI
```

## Core services

### 1. Run planner

Builds:

- task scope
    
- repo scope
    
- variant plan
    
- guardrail profile
    

### 2. Repo adapter

Normalizes:

- commands
    
- file layout
    
- framework behavior
    
- quality gates
    

### 3. Sandbox orchestrator

Creates:

- N isolated runs
    
- environment setup
    
- preview URLs
    
- lifecycle tracking
    

### 4. Verification engine

Runs:

- lint
    
- tests
    
- build
    
- screenshots
    
- health checks
    

### 5. Artifact store

Persists:

- source diff
    
- logs
    
- previews
    
- screenshots
    
- test reports
    
- summaries
    

---

# Roadmap

## Phase 0 — Current state

Phase Lab is already demo-ready for prototype exploration.

## Phase 1 — Real preview fidelity

- finish true React preview rendering
    
- ensure screenshots reflect actual generated UI
    
- tighten evaluator trust
    

## Phase 2 — Repo-backed mode for one repo

Target one internal repo first.  
Deliver:

- repo manifest
    
- sandbox clone/setup
    
- scoped changes
    
- build/lint/typecheck/test gates
    
- preview output
    

## Phase 3 — Production-quality gates

Add:

- patch summaries
    
- forbidden path checks
    
- max diff size
    
- test coverage expectations
    
- PR-ready output
    

## Phase 4 — Repo-agnostic engine

Support multiple repos through:

- repo manifest
    
- repo adapters
    
- standard artifact format
    

## Phase 5 — Feature data packages

Add feature-scoped data setup for:

- snapshots
    
- fixtures
    
- supporting docs
    
- optional Snowflake extracts
    

## Phase 6 — Snowflake-aware mode

Add:

- read-only safe connections
    
- warehouse guardrails
    
- approved views
    
- query limits
    
- audit logs
    

## Phase 7 — Cross-product integration

Phase Lab uses:

- OpenTribe context
    
- CPMA compliance
    
- Phase Forge execution
    

---

# Practical first target

Do **not** try to make this work on every repo immediately.

Start with:

## One repo

Pick:

- a React/Next.js repo
    
- good tests
    
- good build scripts
    
- known team ownership
    

Then prove:

- same repo
    
- two UI variants
    
- both pass gates
    
- both preview
    
- one gets chosen
    
- one becomes a PR candidate
    

That will validate the whole model.

---

# Suggested repo statement

## Repo name

**phase-forge**

## Description

A repo-agnostic agent sandbox execution engine for generating, verifying, and comparing production-quality code variants across real repositories.

## Short purpose

Turns prototype ideas into guarded, testable, merge-ready implementation variants.

---

# Final recommendation

## Keep the separation clean

- **Phase Lab** = interface for exploration
    
- **Phase Forge** = production execution engine
    

That is a strong architecture and a strong product story.

## Your next real milestone

Build **repo-backed mode for one real app repo**, with:

- manifest
    
- scoped changes
    
- mandatory gates
    
- preview
    
- artifact output
    

That is the step that turns this from a prototype tool into a serious internal platform.

If you want, I can turn this into a polished `README.md` and `roadmap.md` for the new repo.