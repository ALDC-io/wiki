# 

## Purpose

This prototype architecture is designed to prove one narrow workflow:

**Zeus can ingest change signals from enterprise source systems, detect when documentation is stale, generate a bounded update, preserve provenance, and support human approval before writeback.**

It is intentionally built as an **integration-first overlay**, not a Confluence replacement, which matches the product direction and prototype scope already defined.

---

## Prototype Scope

### Systems represented

- **Confluence-like docs** as local markdown files
- **Git** as PR summary + code diff artifacts
- **Jira** as ticket/epic JSON
- **Decision artifact** as a meeting or approval note
- **Zeus layer** as the logic that detects drift, proposes updates, and stores evidence

### Workflow shown

1. source change occurs
2. Zeus ingests the change
3. Zeus maps the change to likely impacted docs
4. Zeus identifies stale sections
5. Zeus generates an evidence-backed update
6. human reviewer approves or rejects
7. updated doc is saved

---

## Architecture Overview

Source Artifacts  
  ├─ Git PR / diff  
  ├─ Jira ticket / epic  
  ├─ Decision note  
  └─ Existing Confluence-like docs  
          ↓  
Ingestion + Normalization Layer  
          ↓  
Doc Mapping Layer  
          ↓  
Drift Detection Layer  
          ↓  
Update Generation Layer  
          ↓  
Review + Approval Layer  
          ↓  
Writeback + Version Save  
          ↓  
Zeus Provenance Record

---

## Core Components

## 1. Ingestion and Normalization

This layer loads local artifacts and converts them into a common internal structure.

### Inputs

- markdown docs
- JSON tickets
- PR summary / diff text
- decision note text

### Output

Normalized records such as:

- `source_type`
- `artifact_id`
- `timestamp`
- `entities`
- `changed_rules`
- `referenced_systems`

### Goal

Make all source artifacts comparable enough for downstream mapping and reasoning.

---

## 2. Doc Mapping Layer

This layer determines which document or section is most likely affected by a source change.

### Method

Use simple deterministic matching first:

- keywords
- named rules
- thresholds
- region references
- known doc-to-rule mappings
- explicit file-to-doc maps where useful

### Example

If the PR mentions:

- markdown sensitivity threshold
- North America override
- fallback forecast logic

then Zeus maps that to:

- `forecast_assumptions.md`
- specific section: `Markdown-Sensitive SKU Overrides`

### Why deterministic first

For the prototype, deterministic mapping is faster, more explainable, and less likely to create demo noise.

---

## 3. Drift Detection Layer

This layer compares the changed source signals against the current doc text.

### It produces

- impacted document
- impacted section
- stale reason
- evidence list
- confidence score

### Drift examples

- doc says threshold is 0.35, source change shows 0.25
- doc says fallback uses baseline regional forecast, source change shows channel-adjusted fallback
- runbook omits new operational notification step

### Goal

Answer the core question:  
**“Why is this doc no longer accurate?”**

This is the real heart of the prototype.

---

## 4. Update Generation Layer

This layer creates a proposed revised section for the stale doc.

### Inputs

- stale section text
- structured drift reason
- source evidence
- doc context

### Output

- short summary of change
- rewritten section text
- evidence bundle
- confidence score
- review-required flag

### Constraints

- only rewrite one section
- do not invent unsupported facts
- preserve enterprise tone
- keep changes bounded and readable

---

## 5. Review and Approval Layer

This layer represents the human control point.

### Actions

- approve update
- reject update
- inspect source evidence
- compare before/after

### Why it matters

The prototype is not trying to prove full autonomy.  
It is trying to prove **trusted documentation maintenance with human control**, especially for business logic and operational knowledge. That aligns with the realistic “zero-touch” posture already defined: automate low-risk work, keep humans in approval loops for higher-risk semantic changes.

---

## 6. Writeback and Version Save

For the prototype, writeback is local.

### Behavior

- save updated markdown file
- keep original version
- show before/after comparison
- attach evidence summary

### Production analog

In a real system this would write back to:

- Confluence
- Jira comment/task
- GitHub issue/PR note
- Zeus internal memory record

---

## Zeus Internal Data Model

The prototype only needs a small internal model.

## Core entities

### Source Artifact

Represents a Git, Jira, meeting, or doc artifact.

Fields:

- `id`
- `type`
- `content`
- `entities`
- `timestamp`

### Document Record

Represents a monitored Confluence-like doc.

Fields:

- `doc_id`
- `title`
- `sections`
- `owner`
- `version`

### Drift Event

Represents a detected mismatch.

Fields:

- `event_id`
- `doc_id`
- `section`
- `stale_reason`
- `confidence_score`
- `evidence_refs`

### Proposed Update

Represents the generated update.

Fields:

- `update_id`
- `target_doc`
- `target_section`
- `before_text`
- `after_text`
- `review_required`
- `status`

### Provenance Record

Represents traceability.

Fields:

- `source_refs`
- `change_summary`
- `linked_entities`
- `generation_timestamp`

---

## Deterministic vs LLM-Assisted Logic

## Deterministic logic

Use deterministic logic for:

- loading files
- parsing JSON/markdown
- extracting known entities
- matching artifacts to docs
- selecting likely impacted section
- rendering diffs
- saving updated files

## LLM-assisted logic

Use model assistance for:

- concise explanation of why a section is stale
- enterprise-friendly rewrite of stale text
- summarization of supporting evidence

## Why this split is correct

It keeps the core workflow explainable and reduces hallucination risk.  
The model helps where language generation matters; rules handle structure and control.

---

## Guardrails

The prototype should include basic guardrails even though it is not production-grade.

### Required guardrails

- explicit source evidence shown to user
- section-level update only
- approval before save
- confidence score displayed
- original version preserved
- reset / rollback option

### Why these matter

Without provenance and rollback, the demo will feel like an untrusted AI writing docs.  
With them, it feels like a governed maintenance workflow.

---

## Known Risks and Limitations

## Prototype limitations

- source data is mocked
- mappings are narrow and scenario-specific
- confidence score is heuristic
- no real enterprise permissions
- no real Confluence or Jira APIs
- no multi-doc conflict handling
- no autonomous update policies

## Key technical weak points

- source-to-doc mapping can get noisy at scale
- business logic may not be fully reconstructable from artifacts
- decision notes may contain ambiguity that the model flattens

## Why this is still enough

Tomorrow’s goal is not to prove platform completeness.  
It is to prove the wedge:  
**enterprise documentation can be kept current through cross-source drift detection and governed writeback.**

---

## Why This Architecture Is Right for the Prototype

This architecture is deliberately narrow:

- simple enough to build quickly
- credible enough for technical scrutiny
- aligned with the product wedge
- compatible with a future overlay-first enterprise product

It shows a realistic first step toward Zeus as a knowledge integrity layer without pretending the company is already ready to replace systems of record.

---

## One-Sentence Summary

**The Zeus prototype ingests source changes from Git, Jira, docs, and decision artifacts, detects stale documentation, generates a bounded evidence-backed update, and routes it through human approval before writeback**