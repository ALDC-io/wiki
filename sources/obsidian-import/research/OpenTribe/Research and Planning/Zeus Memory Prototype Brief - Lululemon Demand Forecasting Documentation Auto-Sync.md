# Zeus Memory Prototype Brief: Lululemon Demand Forecasting Documentation Auto-Sync

## Purpose

This prototype exists to prove one narrow point:

**Zeus can detect when enterprise documentation is stale, explain why it is stale, and propose a traceable update after a real-world source change.**

For tomorrow, this is **not** a platform demo. It is a focused proof that Zeus can operate as an integration-first knowledge integrity layer rather than trying to replace Confluence on day one. The scenario uses Lululemon and a demand forecasting workflow, with inputs spanning Git, Jira, Confluence, and decision artifacts.

---

## Prototype Objective

Demonstrate a simple end-to-end workflow where:

1. a forecasting rule changes,
2. Zeus identifies which documentation is affected,
3. Zeus explains the drift,
4. Zeus drafts an updated doc section,
5. Zeus shows supporting evidence,
6. a reviewer approves the change,
7. the updated document is saved.

The prototype should make the product wedge obvious:

**Confluence doc accuracy + auto-sync, powered by cross-source drift detection.**

---

## Demo Scenario

Lululemon has an internal demand forecasting workflow used for planning, allocation, and operational coordination. A business-logic change is introduced for **markdown-sensitive SKUs in North America**, affecting thresholds, override behavior, fallback forecast handling, and downstream operational expectations. This is exactly the kind of high-value enterprise knowledge the broader concept is supposed to preserve: formulas, business logic, assumptions, decisions, integrations, and operational know-how.

The prototype shows how Zeus handles that change when it appears across multiple systems:

- **Git** contains the implementation change
- **Jira** contains the tracked initiative or completion signal
- **Confluence-like docs** contain the stale knowledge
- **a meeting/decision note** provides business context and approval logic

---

## What the Prototype Must Prove

### Primary proof

Zeus can keep documentation aligned with operational reality as source systems change.

### Secondary proof

Zeus is not just retrieval. It can:

- ingest multiple source signals,
- detect documentation drift,
- generate a bounded update,
- preserve provenance,
- support human approval before writeback.

### What success looks like in the room

The CEO should understand the wedge in under two minutes.  
The Product Owner should understand the workflow in under five minutes.  
The Senior AI Engineer should see that the architecture is simple, credible, and not hand-wavy.

---

## Scope

## In scope

A single-project prototype using local mocked artifacts that simulate:

- one Confluence-like forecasting document set,
- one Git change event,
- one Jira artifact,
- one meeting or decision note,
- one drift-detection flow,
- one update-generation flow,
- one approval step,
- one saved updated document.

## Out of scope

- real Confluence integration
- real Jira integration
- real Git provider integration
- full enterprise permissions model
- full memory graph
- migration from Confluence into Zeus-native storage
- broad enterprise search/chat
- autonomous production writeback
- company-wide multi-team workflows

This prototype is intentionally narrow because the broader concept is too large to prove tomorrow. The point is to validate the near-term wedge, not the full platform vision.

---

## Prototype Inputs

The prototype should use local files that simulate the following source types:

### 1. Confluence-like docs

Example files:

- `demand_forecasting_overview.md`
- `forecast_assumptions.md`
- `forecast_runbook.md`

These should reflect the current documented state, but include at least one stale section.

### 2. Git change artifact

Example files:

- `pr_1042_summary.json`
- `feature_logic_diff.txt`

These should indicate a meaningful business-logic change affecting threshold behavior, fallback rules, and operational handling.

### 3. Jira artifact

Example file:

- `epic_forecast_override_update.json`

This should indicate the tracked workstream and its status.

### 4. Meeting / decision artifact

Example file:

- `merch_planning_decision_2026_04_05.md`

This should capture the rationale or approval that makes the documentation update credible.

---

## Core User Flow

### Step 1: Load current state

The user opens the prototype and sees:

- the current doc,
- the incoming source changes,
- a short summary of the Lululemon scenario.

### Step 2: Detect impacted documentation

Zeus analyzes the source changes and identifies:

- which document is affected,
- which section is stale,
- why it is stale.

### Step 3: Show evidence

Zeus displays the supporting evidence:

- Git change summary,
- Jira linkage,
- meeting/decision note excerpt.

### Step 4: Generate a proposed update

Zeus drafts an updated section for the stale documentation.

### Step 5: Human review

The user approves or rejects the proposed update.

### Step 6: Save updated version

The system saves and displays the updated document.

This flow is meant to represent a realistic first step toward near-zero-touch documentation, with human approval preserved for sensitive changes.

---

## Required Outputs

For the demo, Zeus should produce a structured output containing:

- impacted document
- impacted section
- stale reason
- evidence/provenance
- proposed updated text
- confidence score
- review mode status
- updated saved version

The UI should clearly show:

- **Before**
- **What changed**
- **Why the doc is stale**
- **Suggested update**
- **After**
- **Traceability**

---

## Product Behavior Rules

## Deterministic where possible

Use deterministic or heuristic logic for:

- file loading,
- source parsing,
- candidate doc mapping,
- section selection,
- diff rendering,
- save/update flow.

## LLM-assisted where useful

Use model assistance for:

- concise drift explanation,
- rewrite of the stale section,
- short rationale summary.

## Conservative update behavior

The prototype should only update:

- one section at a time,
- only when evidence is visible,
- only after a human approval step.

This aligns with the broader requirement to define realistic “zero-touch” modes and guardrails rather than pretending everything can be fully automated safely today.

---

## Success Criteria

The prototype is successful if it does all of the following:

### Functional success

- identifies the correct impacted doc
- identifies the correct stale section
- explains the drift clearly
- produces a believable update
- saves the approved version

### Product success

- makes the wedge obvious
- feels like a real workflow, not a toy chatbot
- shows why integration-first is the right starting point

### Audience success

- CEO sees a commercial wedge
- Product Owner sees a concrete user flow
- Senior AI Engineer sees credible system boundaries and guardrails

---

## What Is Real vs Mocked

## Real

- the product thesis
- the workflow shape
- the systems involved
- the document/update problem
- the need for provenance and trust

## Mocked

- source artifacts
- integration events
- Confluence/Jira/Git data
- writeback behavior
- confidence scoring
- policy/governance behavior

Be explicit about this in the meeting. A believable mocked workflow is better than a fake “fully integrated” demo.

---

## Key Risks in the Prototype

### 1. Overbuilding

The biggest risk is trying to simulate too much enterprise complexity and losing the core story.

### 2. Weak drift logic

If Zeus cannot clearly explain why the doc is stale, the demo collapses.

### 3. No provenance visibility

If the audience cannot see where the update came from, trust drops immediately.

### 4. Vague business logic

If the Lululemon example is too generic, the demo feels fake.

### 5. Chatbot drift

If the prototype feels like “ask AI a question” instead of “maintain enterprise knowledge,” it misses the point.

---

## Recommended Build Shape

For tomorrow, the fastest believable implementation is:

- **Python**
- **Streamlit**
- **local mocked files**
- **one narrow scenario**
- **one approval-based update loop**

That is enough to show the product’s near-term value without pretending the platform is already complete.