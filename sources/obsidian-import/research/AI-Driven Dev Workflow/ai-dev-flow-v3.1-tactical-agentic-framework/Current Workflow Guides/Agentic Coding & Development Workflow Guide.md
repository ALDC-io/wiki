# Agentic Coding & Development Workflow Guide

  

**Version:** 1.0  

**Audience:** Developers building serious software with ChatGPT + Claude Code  

**Purpose:** A practical, reusable operating system for architecture, migration, implementation, and context management across long-running agentic development efforts.


---

## 1. Executive Summary


This workflow is designed for **multi-session, architecture-heavy software development** where:

- the codebase evolves over many context windows
- important decisions must survive compaction and chat resets
- planning quality matters as much as implementation speed
- multiple tools are used intentionally:
  - **ChatGPT** for architecture critique, planning pressure-testing, sequencing, and workflow design
  - **Claude Code** for repo inspection, planning, editing, refactoring, and implementation

  

The central idea is simple:


> **Do not let the live chat be the source of truth.**  

> Put architecture, migration state, current phase, and next actions into repo files that agents can re-read at any time.


This turns agentic development from “smart chat sessions” into a **repeatable engineering system**.


---
 

## 2. Core Principles


### 2.1 Promote state out of chat

Anything that matters beyond the next few messages should live in the repository:

- architecture decisions
- migration plans
- task tracker state
- current phase
- next actions
- progress log
- compaction instructions

  
### 2.2 Separate stable truth from operational truth

Use different files for different levels of volatility:

- **Stable architecture** changes rarely
- **Migration plan** changes occasionally
- **Task tracker / current sprint / next actions** change constantly

  

### 2.3 Use agents for the right jobs

A good split is:

- **ChatGPT**: architecture coach, systems critic, sequencing advisor, workflow designer

- **Claude Code**: repo reader, planner, refactorer, implementer, documentation maintainer
  

### 2.4 Never let planning and implementation blur together

Before non-trivial code changes:

- clarify the next slice
- define scope and out-of-scope
- identify files likely to change
- identify tests/invariants to protect
- update the tracker and current-phase files
  
### 2.5 Protect context quality

Do not rely on one long conversation to hold everything. Claude Code itself recommends concise persistent memory in `CLAUDE.md`, using `/context` to inspect usage, `/compact` with a focus when needed, and hooks to re-anchor after compaction. ([Claude Code docs](https://code.claude.com/docs/en/how-claude-code-works))

  
---

## 3. Tool Roles: ChatGPT vs Claude Code

## ChatGPT

Use ChatGPT for:

- architecture critique
- migration sequencing
- deciding what to build next
- pressure-testing agent structures
- deciding what should be an agent vs workflow vs skill vs deterministic runtime logic
- creating prompts for Claude Code
- reviewing Claude’s plans and summaries
- creating reusable guidance and operating manuals

  

## Claude Code

Use Claude Code for:

- inspecting the repo
- reading the implementation directly
- creating or updating docs in-repo
- writing/refactoring code
- updating planning files after each slice
- executing the plan one slice at a time
- surviving compaction via repo-based operational truth

  

### Rule of thumb

- Ask **ChatGPT**: *“What is the right move?”*
- Ask **Claude Code**: *“Make the move in the repo.”*

---

## 4. Recommended File System for Agentic Development

  
A strong structure is:

```text

/docs/

  architecture/

    README.md

    target-architecture.md

    migration-plan.md

    adr/

      ADR-001-five-agent-roster.md

      ADR-002-workflow-runtime.md

      ADR-003-paperclip-boundary.md

      ADR-004-skill-resolution.md

  

/planning/

  migration-tracker.yaml

  current-sprint.md

  open-questions.md

  progress-log.md

  

/.claude/

  context/

    architecture-summary.md

    current-phase.md

    next-actions.md

```

  

This layout separates:

- **stable architecture**
- **migration strategy**
- **task execution truth**
- **Claude restart context**


---

## 5. What Each File Is For

  
## `docs/architecture/README.md`

### Purpose

Explains how the architecture documentation set is organized.


### Use it for

- orienting a new developer
- explaining which file is stable vs operational
- pointing to ADRs and tracker as source-of-truth layers

  
### Put in it

- file map
- how to use the folder
- where stable decisions live
- where execution truth lives

  
---

  

## `docs/architecture/target-architecture.md`

### Purpose

The **north-star architecture**.

### Use it for

- final target structure
- stable system design
- what should remain true across repo types
 
### Put in it

- durable agent roster
- Paperclip / control-plane boundary
- runtime model
- skill strategy
- config model
- system invariants

  

### Do not put in it

- task status
- daily implementation notes
- temporary blockers


---


## `docs/architecture/migration-plan.md`

### Purpose

The **human-readable roadmap** from current repo state to target architecture.

  

### Use it for

- sequencing
- phase definitions
- rationale for the migration path

  

### Put in it

- keep / change / postpone
- migration strategy
- minimum viable runtime
- durable agent model
- verification strategy
- phased rollout
- top next changes summary


### Do not put in it

- live task status for individual tasks


---


## `docs/architecture/adr/ADR-*.md`

### Purpose

Capture **locked decisions** so they are not re-litigated every session.

### Use them for

- architecture choices with tradeoffs
- documenting alternatives considered
- preserving reasoning after compaction or new chats

  
### Standard ADR structure

- context
- decision
- alternatives considered
- consequences

  

### Example ADRs

- five-agent roster
- workflow runtime
- Paperclip boundary
- skill resolution order

  
---


## `planning/migration-tracker.yaml`

### Purpose

The **operational source of truth**.
 

### Use it for

- current phase

- task status

- dependencies

- priorities

- files affected

- tests required

- success criteria

  

### Put in it

For each task:

- id

- title

- phase

- status

- priority

- owner

- depends_on

- files

- success_criteria

- tests

- notes

  

### Why YAML matters

This file is easy for both humans and agents to inspect. It is the best place to answer:

  

- What is currently in progress?

- What is next?

- What depends on what?

  

---

  

## `planning/current-sprint.md`

### Purpose

Short, current work focus.

  

### Use it for

- what is being worked on now

- what not to touch yet

- current phase exit criteria

  

### Keep it short

This should be a fast-glance document, not a narrative log.

  

---

  

## `planning/open-questions.md`

### Purpose

Holds unresolved decisions that should not be solved accidentally or forgotten.

  

### Put in it

- architecture questions

- sequencing questions

- “maybe later” decisions

- unresolved CI / runtime / overlay questions

  

### Why it matters

Without this file, unresolved questions leak into implementation or get rediscovered in every new chat.

  

---

  

## `planning/progress-log.md`

### Purpose

Append-only execution history.

  

### Put in it

For each completed slice:

- date

- task id

- files changed

- what was delivered

- tests added/updated

- what comes next

  

### Why it matters

This is the best “what just happened?” file after a restart.

  

---

  

## `.claude/context/architecture-summary.md`

### Purpose

Short Claude-facing architecture summary.

  

### Put in it

- target end-state

- migration path

- locked decisions

- things Claude should not re-litigate without new evidence

  

---

  

## `.claude/context/current-phase.md`

### Purpose

Minimal restart surface.

  

### Put in it

- current phase

- current focus

- last completed milestone

- current phase exit criteria

- what is paused

  

---

  

## `.claude/context/next-actions.md`

### Purpose

Immediate implementation queue.

  

### Put in it

- ordered next 5–8 actions

- files likely to change

- dependencies

- tests to protect

  

This is one of the highest-value files in the whole workflow.

  

---

  

## 6. Standard Development Loop

  

Use this loop for every meaningful slice.

  

### Step 1 — Decide the next slice

Use ChatGPT and/or Claude plan mode to define:

  

- the next task

- scope

- out-of-scope

- files likely to change

- tests/invariants to protect

  

### Step 2 — Make the planning files current

Before implementation, make sure:

  

- `migration-tracker.yaml` is correct

- `current-sprint.md` is current

- `current-phase.md` is current

- `next-actions.md` is current

  

### Step 3 — Give Claude a tightly scoped implementation prompt

Good prompts say:

  

- implement one slice only

- here is the scope

- here is what not to touch

- here are the validations

- update planning files when done

  

### Step 4 — Review Claude’s summary

Check:

  

- did it change only what you asked?

- do tests still pass?

- did the planning files get updated?

- is the next step clearer now?

  

### Step 5 — Record the slice

The slice is not done until these are updated:

  

- `migration-tracker.yaml`

- `current-sprint.md`

- `progress-log.md`

- `current-phase.md`

- `next-actions.md`

  

### Step 6 — Only then move on

This prevents drift across context windows.

  

---

  

## 7. Context Management and Compaction

  

This is one of the most important parts of the workflow.

  

Claude Code recommends:

- keeping `CLAUDE.md` concise and durable

- using `/context` to inspect context usage

- using `/compact` with a focus prompt when you want control

- using hooks for post-compaction re-anchoring ([Claude Code docs](https://code.claude.com/docs/en/how-claude-code-works))

  

## 7.1 What to store in chat vs files

### Chat is good for

- exploration

- critique

- temporary reasoning

- one-slice execution

  

### Files are good for

- architecture

- current state

- next actions

- decisions

- progress

  

### Rule

If it matters after compaction, it belongs in a file.

  

---

  

## 7.2 `CLAUDE.md` should contain compact instructions

A good `CLAUDE.md` should include a section like:

  

- what to re-read after compaction

- what to restate after compaction

- what not to preserve

  

This works because Claude Code loads `CLAUDE.md` every session and uses it as persistent project memory. ([Claude Code docs](https://code.claude.com/docs/en/memory))

  

---

  

## 7.3 Hook strategy

The best compaction hook pattern is:

  

- `SessionStart`

- `matcher: "compact"`

- command hook prints a short reminder

  

That reminder should tell Claude to re-read:

- `planning/migration-tracker.yaml`

- `planning/current-sprint.md`

- `.claude/context/current-phase.md`

- `.claude/context/next-actions.md`

- `docs/architecture/target-architecture.md`

  

And then restate:

- current phase

- last completed task

- next task

- likely files to change

- tests/invariants to protect

  

Claude Code’s hooks documentation explicitly supports this pattern. ([Claude Code docs](https://code.claude.com/docs/en/hooks-guide))

  

---

  

## 7.4 Pre-compaction habit

When the session is getting large, do this:

  

1. update tracker and context files

2. optionally run `/context`

3. run `/compact` with a focus if needed

4. after compaction, have Claude restate the current state

  

### Good `/compact` focus prompt

```text

/compact Focus on the current migration phase, last completed task, next task, likely files to change next, and the tests/invariants that must not regress.

```

  

---

  

## 7.5 New chat handoff pattern

When a chat gets slow or bloated, create a compact restart brief.

  

Recommended file:

- `CHAT-HANDOFF.md`

  

### What it should include

- current objective

- current phase and slice

- last completed task

- next task

- locked decisions

- current repo state

- likely files to change next

- tests/invariants to protect

- blockers/open questions

- what not to do yet

  

This is the best single-file handoff to paste into a new chat.

  

---

  

## 8. Prompting Patterns That Work

  

## Planning prompt pattern

Use for architecture or next-slice planning.

  

Include:

- repo/task context

- exact scope

- what not to do yet

- required output format

- need to update planning files

  

## Implementation prompt pattern

Use for one slice only.

  

Include:

- task id

- exact files to touch or likely files to touch

- explicit out-of-scope list

- validations/tests

- planning hygiene requirements

  

## Critique prompt pattern

Use ChatGPT to pressure-test Claude’s plan.

  

Ask:

- what is too conservative?

- what is too risky?

- what is over-engineered?

- what should be agent vs skill vs workflow vs deterministic runtime code?

  

---

  

## 9. Example Real-World Use Cases

  

## Use case 1 — Refactoring a monolithic agent system

**Problem:** A repo has too many permanent agents and unclear orchestration.

  

**Workflow:**

1. ChatGPT critiques the architecture and proposes candidate models.

2. Claude inspects the repo and produces a target architecture + migration path.

3. ADRs are created for the chosen agent roster and runtime model.

4. Migration tracker is seeded with phased tasks.

5. Claude implements slices one at a time.

6. Progress survives compaction because the tracker/context files are current.

  

**Value:** Architecture stops living in chat and becomes executable planning state.

  

---

  

## Use case 2 — Multi-repo development platform

**Problem:** You want one agentic system to work for connectors, applications, warehouses, and agentic repos.

  

**Workflow:**

1. Stable target architecture defines a core runtime and control-plane boundary.

2. Migration plan defines when overlays and skill tiers should arrive.

3. Tracker keeps current rollout visible.

4. Claude implements the shared runtime first, then layered specialization later.

  

**Value:** You avoid designing the system around one repo type too early.

  

---

  

## Use case 3 — Long-running refactor with frequent compaction

**Problem:** Large refactor work regularly hits context limits.

  

**Workflow:**

1. `CLAUDE.md` contains compact instructions.

2. `SessionStart` compact hook re-anchors Claude.

3. `current-phase.md` and `next-actions.md` are updated after every slice.

4. A `CHAT-HANDOFF.md` can be generated for new chat windows.

  

**Value:** Compaction stops being dangerous because the repo contains the real state.

  

---

  

## Use case 4 — Team adoption

**Problem:** More than one developer needs to use the workflow.

  

**Workflow:**

1. Team reads `docs/architecture/README.md` and `target-architecture.md`.

2. ADRs prevent old debates from reopening constantly.

3. `migration-tracker.yaml` is the operational truth.

4. Developers use the same slice discipline and planning hygiene.

  

**Value:** The workflow becomes teachable and repeatable, not personality-driven.

  

---

  

## 10. Common Failure Modes

  

## Failure mode: live chat becomes source of truth

### Symptom

Important decisions exist only in chat.

  

### Fix

Promote them into ADRs, migration plan, or context files.

  

---

  

## Failure mode: tracker and current phase drift apart

### Symptom

Different files imply different next steps.

  

### Fix

Do a reconciliation pass before continuing implementation.

  

---

  

## Failure mode: agents over-implement the next slice

### Symptom

Claude changes more than requested.

  

### Fix

Use tighter prompts with explicit out-of-scope rules.

  

---

  

## Failure mode: architecture gets re-litigated every session

### Symptom

Every new chat restarts old debates.

  

### Fix

Use ADRs and architecture summary docs.

  

---

  

## Failure mode: compaction loses important state

### Symptom

Claude restarts in the wrong phase or picks the wrong next task.

  

### Fix

Update tracker/context files before compaction and use compact instructions + hooks.

  

---

  

## 11. Practical Templates

  

## End-of-slice checklist

Before ending a slice:

  

- [ ] tests pass (or known pre-existing failures are explicitly noted)

- [ ] `migration-tracker.yaml` updated

- [ ] `current-sprint.md` updated

- [ ] `progress-log.md` appended

- [ ] `current-phase.md` updated

- [ ] `next-actions.md` updated

- [ ] next task is clear

  

## Before new chat checklist

- [ ] generate/update `CHAT-HANDOFF.md`

- [ ] verify tracker is current

- [ ] verify current phase is current

- [ ] verify next actions are current

- [ ] verify open blockers are recorded

  

## Before compaction checklist

- [ ] tracker current

- [ ] current phase current

- [ ] next actions current

- [ ] run `/compact` with a focus if needed

- [ ] ask Claude to restate phase / last task / next task

  

---

  

## 12. Recommended Standard for Professional Agentic Development

  

If you want this workflow to feel elite and repeatable, adopt this rule set:

  

1. **Architecture lives in docs, not chat.**

2. **Execution state lives in the tracker, not memory.**

3. **Next actions live in a short file, not in someone’s head.**

4. **Every slice is small, scoped, and validated.**

5. **Compaction is expected and engineered for.**

6. **ChatGPT critiques; Claude executes.**

7. **Decisions are frozen in ADRs.**

8. **Do not start the next slice until the planning files reflect reality.**

  

---

  

## 13. Final Guidance

  

The real breakthrough in agentic development is not “more agents.”

It is **better state management**.

  

The strongest teams do not treat the model session as the system.  

They treat the repository — docs, trackers, ADRs, context files, validations — as the system.

  

That is what makes long-running agentic coding durable, teachable, and safe.

  

---

  

## Appendix A — Suggested Future Additions

  

As your workflow matures, consider adding:

  

- `CHAT-HANDOFF.md` generator prompt

- `CHAT-HANDOFF.yaml` structured handoff

- `devflow doctor` for environment and tracker sanity checks

- `devflow prompt-check` for agent/config hygiene

- CI checks for planning consistency

- linting for tracker/task schema

  

---

  

## Appendix B — Minimal Compaction Reminder

  

A good compaction reminder is:

  

> Re-read the migration tracker, current sprint, current phase, next actions, and target architecture before proceeding. Then restate the current phase, last completed task, next task, likely files to change, and tests/invariants to protect.

  

That is enough.