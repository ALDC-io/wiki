## The best next step is not a grab-bag of features

After reviewing **Beads** and **HumanLayer**, the strongest move is to turn ai-dev-flow into a **stateful agent control plane** rather than just a workflow launcher. Beads brings the missing **persistent task graph / memory substrate**: dependency-aware work items, ready queues, hash-safe IDs, formulas, gates, and message threads. HumanLayer brings the missing **human-control substrate**: deterministic approval for high-stakes actions, human-as-tool workflows, async escalation, and parallel agent orchestration across worktrees and remote workers. ([Steve Yegge](https://steveyegge.github.io/beads/reference/faq "FAQ | Beads Documentation"))

So the flagship addition I’d build is:

# **ai-dev-flow Control Graph**

### A graph-based, human-gated, multi-agent execution layer for shipping features safely

This would combine your earlier roadmap ideas—resumable state, GitHub-native flows, guardrails, and a UI—with the best primitives from Beads and HumanLayer. Instead of `ai feature` producing markdown and `ai tdd` launching one session, every feature becomes a **living graph** of artifacts, tasks, gates, agents, and evidence.

---

## What each repo contributes

### From Beads

Beads is effectively a durable memory and coordination layer for coding agents: git/Dolt-backed structured issue storage, hash-based IDs, dependency-aware `ready` selection, graph links, formulas, gates, message threads, and semantics for multi-agent concurrency. That is exactly what ai-dev-flow is missing once work gets larger than one linear feature plan. ([GitHub](https://github.com/steveyegge/beads "GitHub - steveyegge/beads: Beads - A memory upgrade for your coding agent · GitHub"))

### From HumanLayer

HumanLayer’s core value is that risky agent actions should not rely on model judgment alone; they should be wrapped in **deterministic human oversight**. Its docs also point toward outer-loop/autonomous agents, async human consultation, and orchestration of multiple coding sessions in parallel with worktrees and cloud workers. That is exactly what ai-dev-flow needs to become team-safe and truly differentiated. ([GitHub](https://github.com/humanlayer/humanlayer "GitHub - humanlayer/humanlayer: The best way to get AI coding agents to solve hard problems in complex codebases. · GitHub"))

---

# The flagship feature

## **Control Graph: the feature becomes the product unit**

Today in ai-dev-flow, a feature is mostly a folder with PRD, diagram, plan, and logs. In the upgraded model, a feature becomes a graph object with:

- artifact nodes: PRD, diagram, plan, evidence, deploy log
    
- work nodes: slices, subtasks, blockers, discovered work
    
- human gates: approvals, questions, review checkpoints
    
- execution nodes: agent sessions, worktrees, CI runs, deploy attempts
    
- communication nodes: agent-to-human threads, decision records, escalation trails
    

This is the fusion of Beads’ graph memory and HumanLayer’s gated human loop, wrapped around ai-dev-flow’s stage pipeline.

---

## The most valuable new features to add

## 1. **Graph-native feature memory**

Replace the current mostly file-based linear workflow with a persistent feature graph.

### What it does

When `ai feature "x"` runs, it would still produce PRD/diagram/plan, but it would also create graph nodes for:

- plan phases
    
- acceptance criteria
    
- open questions
    
- discovered tasks
    
- blockers
    
- dependencies between tasks and artifacts
    

Beads proves that dependency-aware ready queues, graph links, and hash-safe IDs are useful for long-horizon agent work. ai-dev-flow should adopt that model so the system can actually reason about what is ready, blocked, superseded, or waiting for review. ([GitHub](https://github.com/steveyegge/beads "GitHub - steveyegge/beads: Beads - A memory upgrade for your coding agent · GitHub"))

### High-level integration with ai-dev-flow

- `ai feature` writes markdown **and** creates graph nodes
    
- `ai run` reads the graph, not just flat state
    
- `ai loop` picks the next **ready** node instead of just the next feature slug
    
- `qa/evidence.md` becomes a rendered view of graph state rather than a separate side artifact
    

---

## 2. **Human gates**

This is the single most important HumanLayer-inspired feature.

### What it does

Any high-stakes operation becomes a gate:

- destructive git operations
    
- schema migrations
    
- production deploys
    
- emailing/posting on behalf of the team
    
- editing secrets/config
    
- merging when evidence is incomplete
    
- changing requirements mid-flight
    

HumanLayer’s core thesis is that these tools should be wrapped so oversight is deterministic, not advisory. ai-dev-flow already has primitive git guardrails; this would generalize that into a full gate engine.

### High-level integration

- every plan phase can declare required gates
    
- gates can resolve through terminal, web UI, Slack, or GitHub comment
    
- `ai run` pauses and persists state at the gate
    
- `ai resume` continues from the exact node after approval
    
- gate decisions are stored in the graph and linked into evidence artifacts
    

This turns ai-dev-flow from “AI workflow helper” into a system teams can actually trust.

---

## 3. **Parallel worktree swarms**

This is the HumanLayer “multi-Claude” idea, but grounded in ai-dev-flow planning.

### What it does

Once the graph exists, the system can identify independent ready nodes and spawn them in parallel:

- API slice in one worktree
    
- UI slice in another
    
- tests/eval in a third
    
- docs/migration prep in a fourth
    

HumanLayer explicitly pitches parallel Claude sessions, worktrees, and remote cloud workers. Beads supplies the missing graph logic for deciding which tasks are actually ready and conflict-safe. ([GitHub](https://github.com/humanlayer/humanlayer "GitHub - humanlayer/humanlayer: The best way to get AI coding agents to solve hard problems in complex codebases. · GitHub"))

### High-level integration

- new command: `ai swarm <slug>`
    
- ai-dev-flow splits the plan into graph tasks
    
- scheduler launches isolated worktrees per ready task
    
- each agent claims a task atomically
    
- merge orchestration waits for required dependencies and approvals
    
- evidence rolls up per branch, then per feature
    

This would make ai-dev-flow feel fundamentally more advanced than a single-agent TDD launcher. ([Steve Yegge](https://steveyegge.github.io/beads/reference/faq "FAQ | Beads Documentation"))

---

## 4. **Formula-driven workflows**

This is a subtle but very powerful Beads idea.

### What it does

Beads supports formulas and molecules: declarative templates for repeatable workflows. ai-dev-flow should adopt this concept for feature classes:

- CRUD feature
    
- API integration
    
- migration + backfill
    
- auth/permissions change
    
- ETL flow
    
- incident fix
    
- refactor with no user-facing changes
    

Instead of every `ai feature` starting from scratch, the system would instantiate a feature molecule with:

- default plan skeleton
    
- common gates
    
- QA suites
    
- evidence requirements
    
- risk checklist
    
- review path ([Steve Yegge](https://steveyegge.github.io/beads/reference/faq "FAQ | Beads Documentation"))
    

### High-level integration

- extend `devflow.yaml` with `feature_templates`
    
- `ai feature --template migration`
    
- graph gets pre-populated with template nodes and gates
    
- agents still adapt the implementation, but the operational skeleton is standardized
    

This would make ai-dev-flow dramatically better for teams and repeated workflows. ([Steve Yegge](https://steveyegge.github.io/beads/reference/faq "FAQ | Beads Documentation"))

---

## 5. **Async decision inbox**

This is where Beads’ message/thread model and HumanLayer’s async human consultation really click.

### What it does

Agents should be able to:

- ask a maintainer a focused question
    
- request a decision with context
    
- surface two or three options
    
- wait asynchronously
    
- resume when the answer arrives
    

Instead of dumping questions into chat history, ai-dev-flow would create a message node attached to the feature graph. Beads already has message issue types and threading; HumanLayer’s model explicitly supports agents contacting humans across channels for help, feedback, and approvals.

### High-level integration

- `ai ask <slug>` creates a decision thread
    
- threads appear in terminal and UI inbox
    
- Slack/email/GitHub replies attach back to the same node
    
- blocked tasks auto-resume when the answer satisfies the gate
    

This would make ai-dev-flow feel alive, not just scripted.

---

## 6. **Outer-loop feature execution**

This is the most ambitious HumanLayer-inspired upgrade.

### What it does

HumanLayer’s docs talk about outer-loop agents: systems that run over time, pause, wait, resume, and manage their own schedules. ai-dev-flow should take that seriously. A feature should not be one terminal session; it should be a durable process that can:

- pause at approval
    
- wait for CI
    
- wait for code review
    
- wait for a human answer
    
- wake up on event
    
- continue with updated context
    

Beads gates plus ai-dev-flow state plus HumanLayer’s async-human model together create this capability. ([Steve Yegge](https://steveyegge.github.io/beads/reference/faq "FAQ | Beads Documentation"))

### High-level integration

- daemon/service keeps graph state durable
    
- event listeners watch CI, GitHub, timers, approvals
    
- `ai run` becomes “start or continue execution”
    
- `ai status` shows sleeping/running/blocked/awaiting-human/awaiting-ci
    

This is the shift from a CLI tool to a real agent control plane. ([GitHub](https://github.com/humanlayer?utm_source=chatgpt.com "HumanLayer · GitHub"))

---

## 7. **Memory decay + learning loop**

This is one of the most elegant Beads ideas and fits ai-dev-flow perfectly.

### What it does

Beads explicitly mentions semantic “memory decay” to summarize closed work and save context. ai-dev-flow should do the same:

- compress closed subtasks
    
- preserve decisions, risks, and outcomes
    
- keep only active graph detail hot
    
- surface past similar features as reusable context
    

That lets future agent sessions inherit lessons without dragging old noise into the context window.

### High-level integration

- closed feature branches get summarized into reusable memory cards
    
- next `ai feature` can search prior cards
    
- formulas evolve from successful past runs
    
- evidence artifacts become training material for future workflow templates
    

This makes ai-dev-flow self-improving in a practical way.

---

# The most innovative composite feature

## **Flow Molecules**

If you want one standout, “extremely innovative” feature, I would build this first.

### What it is

A **Flow Molecule** is a reusable, graph-backed, human-gated execution object for a class of development work.

Example:

- “Add OAuth provider”
    
- “Roll out schema migration”
    
- “Implement data sync pipeline”
    
- “Refactor service boundary”
    
- “Fix production incident”
    

Each molecule contains:

- graph structure of expected tasks
    
- required artifacts
    
- default human gates
    
- parallelization hints
    
- QA/deploy/evidence requirements
    
- escalation policy
    
- memory of prior runs
    

Beads gives you formulas, molecules, gates, graph structure, and ready queues. HumanLayer gives you human oversight, async consultation, and multi-agent orchestration. ai-dev-flow gives you the artifact pipeline, feature lifecycle, and evidence model. The fused result is something neither project currently offers on its own. ([Steve Yegge](https://steveyegge.github.io/beads/reference/faq "FAQ | Beads Documentation"))

### Why this is special

It would let a team say:

> “Run the migration molecule for tenant billing.”

And the system would know:

- what artifacts to generate
    
- what subtasks can be parallelized
    
- when human approval is mandatory
    
- what tests and evidence must exist
    
- how to pause and resume safely
    
- how to summarize the run afterward
    

That is genuinely a step toward **production AI software delivery**, not just better prompting.

---

# How I would integrate this into the current commands

## `ai feature`

Still interviews and writes artifacts, but now also:

- creates graph nodes
    
- maps plan phases to executable tasks
    
- assigns default molecule/template
    
- registers required gates and evidence paths
    

## `ai tdd`

Instead of one monolithic Claude handoff:

- claims a ready task node
    
- launches in a dedicated worktree/session
    
- reports output back into the graph
    
- opens a gate if it hits a high-stakes action or ambiguity
    

## `ai run`

Becomes a graph executor:

- select ready nodes
    
- run automated nodes
    
- sleep at gates
    
- wake on events
    
- update status/evidence continuously
    

## `ai loop`

Stops being “iterate feature list in priority order” and becomes:

- portfolio scheduler across many feature graphs
    
- choose next ready feature/task based on priority, blockers, and human availability
    
- maximize throughput without losing control ([Steve Yegge](https://steveyegge.github.io/beads/reference/faq "FAQ | Beads Documentation"))
    

## New commands I would add

- `ai graph <slug>` — visualize task/gate/artifact graph
    
- `ai swarm <slug>` — launch parallel worktree agents
    
- `ai approve <gate-id>` — resolve a human gate
    
- `ai inbox` — show pending questions and approvals
    
- `ai resume <slug>` — continue blocked/sleeping work
    
- `ai template new <molecule>` — create reusable formulas
    
- `ai learn <slug>` — summarize completed feature into reusable memory
    

---

# Priority order

## Build in this order

### 1. Graph-native state

Without this, the rest is orchestration theater. Use the Beads-inspired model first.

### 2. Human gates

This is the minimum viable trust layer. Use the HumanLayer-inspired approval model second.

### 3. Parallel worktree execution

Only after the graph can safely identify ready nodes. ([GitHub](https://github.com/humanlayer/humanlayer "GitHub - humanlayer/humanlayer: The best way to get AI coding agents to solve hard problems in complex codebases. · GitHub"))

### 4. Async inbox and resumability

This turns the system durable.

### 5. Flow molecules/templates

This is where team leverage starts compounding. ([Steve Yegge](https://steveyegge.github.io/beads/reference/faq "FAQ | Beads Documentation"))

### 6. UI control plane

Then build the visual layer over it.

---

# Final take

Beads and HumanLayer point in two halves of the same direction:

- **Beads:** agents need durable structured memory and dependency-aware work graphs.
    
- **HumanLayer:** agents need deterministic human oversight and async orchestration to do valuable work safely.
    

ai-dev-flow already has the missing third half:

- a good artifact-driven lifecycle with PRD, plan, QA, deploy, and evidence.
    

Put together, the winning product is:

## **ai-dev-flow as the operating system for graph-based, human-gated, multi-agent software delivery.**

That is much more ambitious—and much more defensible—than a better Claude wrapper.

I can turn this into a **concrete v1/v2 feature spec** next, with exact new commands, storage model, and UI screens.