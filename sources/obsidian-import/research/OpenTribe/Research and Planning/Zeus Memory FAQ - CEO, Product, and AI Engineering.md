# Zeus Memory FAQ: CEO, Product, and AI Engineering

## Purpose

This FAQ is designed for tomorrow’s discussion with the **CEO, Product Owner, and Senior AI Engineer**. It assumes the near-term goal is a narrow prototype around **Lululemon demand forecasting documentation auto-sync**, while staying aligned with the broader Zeus direction: integration-first, not Confluence replacement, with cross-source inputs and near-zero-touch maintenance over time.

---

# CEO FAQ

## 1. Why is this a company and not just a feature inside Confluence, Glean, or an internal AI stack?

Because the value is not “AI helps write docs.” The value is **knowledge integrity across systems**: detecting when reality changed, identifying what became stale, and driving governed updates. That is a workflow and trust problem, not a UI feature.

## 2. Why start with Confluence instead of replacing it?

Because replacing Confluence is the wrong entry motion. Enterprises do not want to rip out a company-wide system to test a new category. The correct wedge is to **keep existing systems trustworthy**, starting with Confluence as the surface teams already use. That is directly consistent with the stated integration-first strategy.

## 3. What is the actual wedge?

**Confluence doc accuracy + auto-sync.**  
That is the sharpest initial wedge because it is visible, painful, and understandable. “Enterprise memory” is too broad. “Cross-source memory graph” is too abstract. “Audit/scoring” is useful for selling in, but it is not the product.

## 4. Why would an enterprise buy this now?

Because stale knowledge creates real cost:

- slower project setup,
- slower onboarding,
- repeated rediscovery,
- decision mistakes from outdated assumptions,
- weak trust in documentation.

The core pain in your brief is not lack of information. It is that information across code, docs, tickets, meetings, and cloud systems falls out of sync and becomes untrustworthy.

## 5. What would make this fail even if the tech works?

Two things:

- it gets sold too broadly as “enterprise AI memory,” so no buyer can place it;
- teams do not trust the updates, so it never becomes part of the operating workflow.

If trust is weak, the product stays “interesting.” It does not become budget-worthy.

---

# Product Owner FAQ

## 1. What is the first lovable workflow?

A change happens in Git/Jira/decision artifacts, Zeus detects that a Confluence page is stale, explains why, drafts a targeted update, and routes it for approval. That is the first workflow worth paying for.

## 2. What exactly is the prototype proving tomorrow?

That Zeus can:

1. ingest mocked Git, Jira, Confluence, and decision inputs,
2. detect a stale section in a forecasting document,
3. explain the drift,
4. propose an updated section,
5. preserve evidence,
6. save the approved result.

That is enough to prove the wedge without pretending the platform is complete.

## 3. What is automated vs what still needs human approval?

For the prototype:

- **automated:** ingestion, impact mapping, drift detection, suggested rewrite
- **human approval required:** final update acceptance

That lines up with the realistic “zero-touch” model you asked for: some categories can be automated more aggressively, but business logic and decision-heavy content should still pass through approval.

## 4. Why Lululemon demand forecasting?

Because it is a strong enterprise example of knowledge that is not just code:

- formulas,
- thresholds,
- assumptions,
- regional exceptions,
- decisions,
- integrations,
- runbooks.

That makes Zeus feel like a serious enterprise product rather than a developer-doc toy. The brief explicitly called for this use case and these knowledge types.

## 5. What are we explicitly not building yet?

Not in the first prototype:

- real Confluence/Jira/Git integrations
- company-wide memory graph
- autonomous production writeback
- full permissions/governance
- migration into Zeus-native storage
- broad enterprise search/chat

That keeps the product focused on one credible workflow instead of a fake platform demo.

---

# Senior AI Engineer FAQ

## 1. How does Zeus know which doc is impacted?

For the prototype, use deterministic mapping first:

- keywords,
- named entities,
- rule names,
- thresholds,
- region references,
- explicit doc-to-rule mappings.

Do not overcomplicate it. The demo should show a believable controlled mapping system, not a magical fully-general reasoner.

## 2. How do we avoid hallucinated doc updates?

By constraining the system:

- only update one section at a time,
- only use visible evidence,
- preserve the original version,
- require approval before save,
- separate deterministic mapping from LLM rewrite generation.

The model helps with explanation and wording. It does not decide truth on its own.

## 3. What is deterministic vs LLM-based?

**Deterministic:**

- file parsing
- entity extraction
- candidate doc mapping
- diff rendering
- version save
- provenance linking

**LLM-assisted:**

- concise stale-reason explanation
- enterprise-friendly rewrite of the affected section
- short evidence summary

That split keeps the system explainable and reduces risk.

## 4. What is the internal data model for the prototype?

Keep it simple:

- **SourceArtifact**
- **DocumentRecord**
- **DriftEvent**
- **ProposedUpdate**
- **ProvenanceRecord**

That is enough to support the demo without prematurely inventing a giant memory ontology.

## 5. What is the hardest technical problem long term?

Not summarization.  
The hardest problem is **high-precision source-to-doc-to-section mapping with trustworthy writeback** across messy enterprise systems.

The real moat will come from:

- integrations,
- provenance,
- workflow control,
- confidence scoring,
- approval policies,
- historical memory objects.

Foundation models will improve. Trust infrastructure and enterprise workflow fit are the harder parts to copy.

---

# Hard Questions You Should Expect

## “Why not just use an audit/scoring product first?”

Use audit/scoring to **land**, not to define the company. It can help prove drift, risk, and ROI, but the enduring product is the maintenance workflow, not the report. The brief explicitly included interest in a pre-audit pipeline, but that is better treated as a sales motion than the core identity.

## “Why not start with code↔doc drift detection instead of Confluence auto-sync?”

Because drift detection alone is diagnostic. It points at pain, but does not complete the workflow. Buyers pay more readily for **resolution**, not just detection.

## “When should Zeus own the source of truth?”

Not now. Start as an overlay. Over time, Zeus can become the system of record for high-value memory objects like decision logs, assumption ledgers, and formula registries. But trying to replace broad documentation systems early is a strategic mistake.

## “What makes this go from useful to mission-critical?”

When teams start depending on Zeus to keep launch docs, model assumptions, runbooks, and project context accurate enough that new work can begin without manual archaeology.

---

# One-Page Positioning Answer

If someone asks, “What is Zeus, in one sentence?” use this:

**Zeus keeps enterprise documentation accurate by detecting when code, tickets, meetings, and operational artifacts change, then proposing traceable updates before stale knowledge slows the business.**

---

# Meeting Reminder

For tomorrow, do not try to defend a full future platform.

Defend this:

- the wedge is sharp,
- the workflow is real,
- the prototype is believable,
- the trust model is sane,
- the path to expansion is obvious.

The next useful artifact is either:

- a **5-minute demo script**, or
- the **Claude prompt pack** tuned to build the prototype fast.