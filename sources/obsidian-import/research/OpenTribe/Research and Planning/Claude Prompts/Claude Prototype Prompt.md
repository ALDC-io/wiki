You are acting as a senior product engineer and rapid prototyper.

Build a SIMPLE local prototype for a product called Zeus Memory.

Goal:
Create a prototype that shows how Zeus detects stale enterprise documentation and proposes updates after changes in source systems.

Demo scenario:
Use a Lululemon demand forecasting example. The prototype should simulate a change to forecasting business logic and show how Zeus identifies impacted docs, explains the drift, and drafts an updated Confluence-like document section.

Constraints:
- This is for an internal executive/product/AI engineering presentation tomorrow.
- Optimize for clarity and believability, not completeness.
- Do NOT build real integrations to Confluence, Jira, or GitHub.
- Use mocked local files.
- Use Python + Streamlit.
- Keep the code simple and runnable locally.
- Build only what is necessary for a 5-minute demo.

Prototype capabilities:
1. Load local source artifacts:
   - Confluence-like markdown docs
   - Git PR summary / diff
   - Jira ticket JSON
   - Optional meeting decision note
2. Detect which doc(s) are impacted by a source change
3. Show why the existing doc is stale
4. Generate a proposed updated section
5. Show provenance/evidence from the source artifacts
6. Let the user approve the update
7. Save and display the updated version

Deliverables:
- repo structure
- implementation plan
- minimal architecture
- code files
- mocked sample data
- instructions to run locally

Important:
- Keep the UX very simple
- Use one project only
- Use one believable business-logic change
- Prefer deterministic rules for source-to-doc mapping where possible
- Use the LLM only for drift explanation and doc rewrite generation

First output:
1. the proposed file structure
2. the data model
3. the step-by-step implementation plan
4. then generate the code