
## Demo goal

Show one believable workflow:

**a change happens in Git/Jira/decision inputs, Zeus detects stale forecasting documentation, explains the drift, proposes an update, and preserves traceability before writeback.**

That directly matches the product direction: integration-first, not replacing Confluence, with focus on keeping knowledge current as source systems change.

---

# Core message to land

**Zeus is not another enterprise search tool. It is a knowledge integrity layer that keeps high-value documentation aligned with real operational changes.**

---

# 5-minute flow

## 0:00–0:30 — Open with the problem

### Say

“Most companies do not have a knowledge access problem first. They have a knowledge trust problem. In workflows like demand forecasting, the code changes, Jira moves, decisions get made, but Confluence does not stay current. Zeus is designed to detect that drift and keep documentation aligned without asking the company to replace Confluence.”

### Show

- Home screen of the prototype
- Scenario title:  
    **Lululemon Demand Forecasting Documentation Auto-Sync**

---

## 0:30–1:15 — Set up the business scenario

### Say

“In this example, Lululemon has updated forecasting logic for markdown-sensitive SKUs in North America. That affects model assumptions, override behavior, fallback logic, and operational guidance. The issue is not just in code. The real knowledge is spread across Git, Jira, docs, and decisions.”

### Show

Sidebar or summary panel with:

- Git change
- Jira epic
- decision note
- monitored Confluence-like docs

### Say

“This is exactly the kind of enterprise knowledge that gets lost: formulas, business logic, assumptions, decisions, integrations, and runbooks.”

---

## 1:15–2:00 — Show the stale document

### Say

“Here is the current documentation. It still reflects the previous logic.”

### Show

The existing doc page, ideally:

- `forecast_assumptions.md`  
    or
- the specific stale section inside it

Highlight the stale section.

### Say

“If a new engineer, PM, or planner starts from this page today, they are starting from stale institutional memory. That slows project setup and creates decision risk.”

---

## 2:00–2:45 — Trigger Zeus drift detection

### Say

“Now Zeus ingests the latest source signals.”

### Show

A button or step labeled:

- **Run Drift Detection**  
    or
- **Analyze Source Changes**

Then show:

- impacted doc
- impacted section
- stale reason
- confidence score

### Say

“Zeus is not just saying ‘something changed.’ It is identifying which document is impacted, which section is stale, and why.”

### Good one-line explanation

“The implementation changed, the tracked work completed, and the decision note confirms the new business logic, but the documentation still describes the previous threshold and fallback behavior.”

---

## 2:45–3:30 — Show evidence and provenance

### Say

“This is the trust layer. We do not want a black-box rewrite. Zeus shows the evidence behind the recommendation.”

### Show

Traceability panel with:

- Git PR summary
- Jira epic
- decision note excerpt

### Say

“Every proposed update is linked back to source artifacts. That is the difference between generic AI writing and governed enterprise maintenance.”

This is important because your concept depends on trustworthy auto-maintenance, not fluffy generation.

---

## 3:30–4:15 — Show the proposed update

### Say

“Now Zeus drafts a bounded update to the affected section.”

### Show

Before / after comparison:

- original section
- proposed updated section

### Say

“For tomorrow’s prototype, this is approval-based. Zeus is not trying to act as an unchecked autonomous editor. It is doing the expensive reconciliation work, preserving evidence, and routing the change for review.”

That lines up with the realistic zero-touch model: automate low-risk maintenance, keep humans in higher-risk semantic approval loops.

---

## 4:15–4:45 — Approve and write back

### Say

“If the reviewer approves, Zeus saves the updated version.”

### Show

- click **Approve Update**
- show saved updated doc
- show success state

### Say

“This is the core workflow: source change, drift detection, evidence-backed update, approval, writeback.”

---

## 4:45–5:00 — Close with the wedge

### Say

“The wedge here is not enterprise memory in the abstract. The wedge is keeping high-value documentation accurate as code, tickets, cloud systems, and decisions change. Start as an overlay, prove trust, then expand into broader enterprise memory over time.”

---

# Short presenter notes by audience

## For the CEO

Emphasize:

- this is a trust and execution problem, not just search
- no rip-and-replace required
- clear path from narrow workflow to larger platform

### Line to use

“We are not asking the customer to change systems. We are making their existing system of knowledge trustworthy again.”

---

## For the Product Owner

Emphasize:

- clear user flow
- visible trigger
- bounded scope
- approval-based writeback
- compounding value over time

### Line to use

“The first lovable workflow is simple: something changes, Zeus finds what is now wrong, drafts the fix, and routes it cleanly.”

---

## For the Senior AI Engineer

Emphasize:

- deterministic mapping first
- constrained update generation
- provenance
- rollback
- no fake production claims

### Line to use

“We are using rules for structure and LLMs for explanation and rewrite, not letting the model invent system truth.”

---

# If they interrupt with hard questions

## “Why not just use Glean / Rovo / Confluence AI?”

Say:  
“Those tools help with access and assistance. This workflow is about maintenance and integrity: detecting what became wrong and updating the source with evidence.”

## “Why not replace Confluence eventually?”

Say:  
“Maybe for selected memory objects later. But the right adoption path is overlay-first because customers will not switch systems company-wide just to try this.”

## “Why Lululemon demand forecasting?”

Say:  
“Because it proves this is more than code docs. It covers formulas, assumptions, decisions, runbooks, and operational knowledge across multiple systems.”

---

# What not to say in the demo

Do not say:

- “This will replace Confluence”
- “This works for every enterprise workflow already”
- “This can fully automate all documentation”
- “The model figures everything out automatically”

Those claims weaken trust.

---

# Best final line

**“If Zeus can keep a workflow as messy and high-stakes as retail demand forecasting aligned across Git, Jira, docs, and decisions, then the category is real.”**

If you want, I’ll do the **Claude prompt pack next**, tightened specifically for **Claude Code** so you can start building immediately.