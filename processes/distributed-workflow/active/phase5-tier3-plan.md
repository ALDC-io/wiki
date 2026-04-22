---
tags: [distributed-workflow, active, client-workflow-automation, implementation-plan]
aliases: [Phase 5 Tier 3 Plan]
sources: []
created: 2026-04-21
updated: 2026-04-21
---

# Phase 5 Tier 3 — Implementation Plan

Produced by Opus 4.7 planning session (2026-04-21, effort xhigh).
Sonnet implementation session reads this file verbatim as its spec.

**Target file (only):** `.claude/commands/gep-feature.md`
**Branch:** `feature/paulrussell/workflow-automation/gep-scripted-deploy`

See [[client-workflow-automation]] for workstream context, Phase 5 Tier 3 boot prompt,
and prior phase history.

---

## Preamble — cross-cutting additions

Used by items 7, 8, 11, 12, 13. Implement once, reference from each item.

### A. `cloudId` resolution (new subsection near the top of the skill, between "Paths" and "LIST mode")

Add a short section `## MCP setup` containing:

> Before the first Atlassian MCP call in a session, call
> `getAccessibleAtlassianResources` with no parameters. The response is an array;
> take `resources[0].id` as the `cloudId`. Reuse this value for every subsequent
> Atlassian MCP call this session. Do not re-resolve it per call.
>
> If `getAccessibleAtlassianResources` fails, treat MCP as offline (see §B).

### B. MCP offline / failure helper (same subsection)

Used by items 8, 11, 12:

> Any Atlassian MCP call must be wrapped in a try/except-style guard. On failure
> (network error, auth error, 4xx/5xx, tool-not-available), do not abort the
> stage. Instead:
>
> 1. Print `⚠️  Jira MCP unreachable — <operation description> skipped.`
> 2. Save the intended payload (comment body, transition target, etc.) to
>    `GEP/tickets/<ticket>/_mcp_queued/<ts>_<operation>.md` so Paul can apply it
>    manually later.
> 3. Continue the stage — MCP failures never block a stage transition.
>
> Exception: LIST mode already has its own offline fallback (ticket key prompt);
> keep that wording unchanged.

### C. "Confirm-and-post" comment helper (same subsection)

Referenced by items 11 and 12:

> **Posting a Jira comment — always follow this pattern:**
>
> 1. Draft the full Markdown comment body.
> 2. Show it to Paul in a fenced block.
> 3. Ask: `Post this comment to <ticket>? (yes / edit / skip)`
> 4. On `edit`, incorporate Paul's edits and re-show.
> 5. On `yes`, call `addCommentToJiraIssue` with:
>    - `cloudId` from §A
>    - `issueIdOrKey = <ticket>`
>    - `commentBody = <body>`
>    - `contentFormat = "markdown"`
>    - `responseContentFormat = "markdown"`
> 6. Record the returned comment URL (if any) alongside the artifact entry that
>    triggered the post.
> 7. On MCP failure, follow §B.

### D. Consolidated artifact schema additions

One block — applied once — covering new fields for items 7, 9, 11, 12, 13. Extend
the current `Artifact schema` block to include:

```yaml
pr_url: null                       # set by item 7
pr_created_at: null                # set by item 7
pr_jira_integration: null          # "native" | "via_comment" | null — set by item 13

changes:                           # set by item 9 at scoped stage
  eclipse:
    required: null                 # true | false | null
    description: ""
    completed: false               # flipped at sandbox-deploy gate
    skipped_at: null               # set if Paul overrides the gate
  pbi_model:
    required: null                 # true | false | null
    description: ""
    published: false               # flipped at prod-deployed gate

jira_sync:                         # set by item 8
  last_transition_at: null
  last_transition_target: null
  skipped_reason: null             # "mcp_offline" | "already_in_target" | "paul_declined" | "no_transition_available" | null

comments_posted:                   # set by items 11, 12
  design_summary:
    test_deployed_at: null
    comment_ref: null
  qa_evidence:
    test_deployed_at: null
    test_results_snapshot: null
    prod_deployed_at: null
    prod_results_snapshot: null
```

Under `deploy_history.prod`, also add:
```yaml
    data_dictionary_prompted: null     # set by item 10
    data_dictionary_updated: null      # set by item 10
```

Default value for every new field on a fresh artifact is whatever the schema shows.
Existing artifacts (GP-197, GP-208) are missing these fields; the skill must treat
missing = default.

---

## Item 7 — PR creation step

### 1. Skill file changes

**Location:** Stage `test-deployed`, inserted as a new numbered step between the
current step 3 (PBI smoke-test) and step 4 (client notification). Renumber the old
step 4.

**New step 4 text (verbatim):**

```
4. **PR creation** — raise the PR against `GEP/user-testing` before notifying
   the client.

   Read `branch`, `jira_summary`, `requirements`, and `decisions` from the artifact.
   Draft:

     Title : "<ticket>: <jira_summary>"         (truncate to 72 chars if longer)
     Body  : a markdown document with sections:
               ## Summary
               <jira_summary>
               ## Requirements
               - Data source: <requirements.data_source>
               - Grain: <requirements.grain>
               - Delivery: <requirements.delivery>
               - Business logic: <requirements.business_logic>
               - History scope: <requirements.history_scope>
               ## Decisions
               1. <decision> — _<rationale>_
               2. ...
               ## Validation
               Sandbox: <deploy_history.sandbox.validate_pass>
               TEST:    <deploy_history.test.validate_pass>
               ## Ticket
               <JIRA_BROWSE_URL>/<ticket>

   Write the body to `GEP/tickets/<ticket>/_pr_body.md` (temp file, gitignored
   via pattern — see §5 below).

   Show Paul the full command:

       gh pr create \
         --base GEP/user-testing \
         --head <branch> \
         --title "<title>" \
         --body-file GEP/tickets/<ticket>/_pr_body.md

   Ask: `Run this command? (yes / edit-title / edit-body / skip)`
     - edit-title  → prompt for a new title; redraw command
     - edit-body   → open `_pr_body.md` for Paul to edit; re-read before running
     - skip        → record `pr_url: "[skipped]"` and proceed; do NOT block stage

   On `yes`, run the command via Bash. Capture stdout. The URL is the last line
   of stdout (matches `^https://github.com/`). Record:
     pr_url         = <captured URL>
     pr_created_at  = <ISO-8601 now>
   Delete `_pr_body.md` after successful creation.

   If `gh pr create` exits non-zero:
     - If stderr contains "a pull request for branch ... already exists":
         ask Paul for the existing PR URL; record it; continue.
     - Otherwise print the stderr verbatim and ask Paul how to proceed.

   After `pr_url` is recorded, run the GitHub-integration detection probe
   from item 13 (see that item for the exact procedure).
```

**Also update the old step 4** — remove the "/ PR raised" phrase (now handled above):
```
5. **Client notification** — has the client been notified that the feature is
   ready for UAT in the PBI Test Model? (yes / not yet)
```

### 2. Artifact schema changes

`pr_url`, `pr_created_at` — in Preamble §D.

### 3. MCP calls

None. Pure `gh` CLI + Bash.

### 4. Interactions

- **Item 11** reads `pr_url` to embed in the design summary comment.
- **Item 13**'s GitHub-integration detection runs at the tail of item 7.

### 5. Edge cases

| Case | Handling |
|---|---|
| `branch` is null in artifact | Refuse: `⚠️  No branch recorded. Go back to scoped stage.` |
| `gh` not authenticated | Surface stderr; instruct `gh auth login` |
| PR already exists for branch | Detect from stderr; ask Paul for URL; record |
| Title > 72 chars | Truncate to 69 chars + `...` |
| Paul picks `skip` | Record `pr_url: "[skipped]"` — distinguishable from unset |
| `_pr_body.md` leftover | Overwrite silently. Add `GEP/tickets/*/_pr_body.md` to `.gitignore` in a separate trivial commit before item 7. |

---

## Item 8 — Jira status transitions

### 1. Skill file changes

Add a new reusable procedure to the `## MCP setup` section after §C, call it **§E. Jira status sync procedure**:

```
## Jira status sync (helper)

Called at exactly three transition points:
  - Entering `implementing` (from `scoped` or `feature-update`) → "In Progress"
  - Entering `uat`          (from `test-deployed`)              → "In Review"
  - Entering `complete`     (from `prod-deployed`)              → "Done"

Procedure:

1. Call `getJiraIssue` with cloudId, issueIdOrKey=<ticket>, fields=["status"].
   If it fails → follow §B, then set `jira_sync.skipped_reason = "mcp_offline"`
   and return.

2. Read current status name (`fields.status.name`, case-insensitive).

3. If current status already matches target (case-insensitive):
     Print: `✓ <ticket> already in "<target>" — no Jira transition needed.`
     Set jira_sync.last_transition_at = now; last_transition_target = target;
         skipped_reason = "already_in_target".
     Return.

4. Call `getTransitionsForJiraIssue` (cloudId, issueIdOrKey=<ticket>).
   Find the transition whose `to.name` (case-insensitive) equals the target.

5. If no matching transition:
     Print: `⚠️  No Jira transition available from "<current>" to "<target>".`
     Print the list of available targets.
     Ask: `Choose a target, or type 'skip': `
     On 'skip' → set skipped_reason = "no_transition_available"; return.
     On target → recompute match; if still none, repeat or skip.

6. Show Paul:
       Propose Jira status move for <ticket>:
         <current> → <target>
       Proceed? (yes / skip)

7. On `skip` → set skipped_reason = "paul_declined"; return.

8. On `yes` → call `transitionJiraIssue` with:
       cloudId, issueIdOrKey=<ticket>,
       transition = { "id": "<matched transition id>" }
   On success:
     Print: `✓ <ticket> transitioned: <current> → <target>`
     Record: jira_sync.last_transition_at = ISO-8601 now;
             jira_sync.last_transition_target = <target>;
             jira_sync.skipped_reason = null.
   On failure → follow §B.
```

Insert calls at the three transition points:

- **End of `scoped` stage** (after "Transition to `implementing` once branch and manifest are both in place."):
  Append: `Before transitioning, run Jira status sync with target "In Progress".`
- **End of `test-deployed` stage** (after client notification step):
  Append: `Before transitioning to \`uat\`, run Jira status sync with target "In Review".`
- **End of `prod-deployed` stage** (after recording deploy_history.prod):
  Append: `Before transitioning to \`complete\`, run Jira status sync with target "Done".`
- **`feature-update` → `implementing`** also enters `implementing`. Ticket is likely already "In Progress", so procedure no-ops via step 3. Still call it — cheap and harmless.

### 2. Artifact schema changes

`jira_sync` block — Preamble §D.

### 3. MCP calls

| Tool | Parameters | Failure handling |
|---|---|---|
| `getJiraIssue` | `cloudId`, `issueIdOrKey`, `fields: ["status"]` | §B — skip transition |
| `getTransitionsForJiraIssue` | `cloudId`, `issueIdOrKey` | §B — skip transition |
| `transitionJiraIssue` | `cloudId`, `issueIdOrKey`, `transition: { id: "<id>" }` | §B — record queued; print warning |

### 4. Interactions

Ordering within `test-deployed` after Paul confirms client notified:
`post item-12 QA evidence` → `post item-11 design summary` → `run item-8 Jira transition to In Review` → set stage = uat.

### 5. Edge cases

| Case | Handling |
|---|---|
| MCP completely offline | §B; stage transition proceeds without Jira move |
| Status already target | Step 3 no-ops; `skipped_reason = "already_in_target"` |
| Non-standard workflow status names | Step 5 presents list; Paul picks or skips |
| Multiple transitions lead to same target | Take first match |
| `force` flag used (backward transition) | **No Jira move.** Print: `ℹ️  Skipping Jira transition (force mode — Jira status unchanged).` |

---

## Item 9 — Eclipse/PBI change tracking

### 1. Skill file changes

**Location A — Stage `scoped`, Step 2**

Replace step 2 with:

```
2. **Requirements**: Any revisions before coding begins?

2a. **Eclipse changes** — does this ticket require changes to the Eclipse
    connector (new template, connection auth, schedule, field mappings)?
    (yes / no)
    If yes, ask: `Describe the Eclipse changes in one sentence:`
    Record `changes.eclipse.required = true/false` and
    `changes.eclipse.description = "..."`.

2b. **PBI model changes** — does this ticket require Power BI Desktop model
    changes (new table relationships, new measures, calculated columns,
    visual-level changes that require a PBIX publish)?
    (yes / no)
    If yes, ask: `Describe the PBI model changes in one sentence:`
    Record `changes.pbi_model.required = true/false` and
    `changes.pbi_model.description = "..."`.
```

**Location B — Stage `implementing`, Sub-step 1 (Sandbox deploy)**

Insert a gate at the top of Sub-step 1, before the share health check prompt:

```
**Eclipse precondition check** — before any sandbox deploy, read
`changes.eclipse`:

  - If `changes.eclipse.required == true` AND `changes.eclipse.completed == false`:

      ⛔ Eclipse changes required but not yet confirmed deployed.

      Planned Eclipse work: <changes.eclipse.description>

      The Snowflake sandbox deploy consumes data already produced by the
      Eclipse pipeline. Confirm that:
        1. Eclipse template/connection changes are saved in the connector repo.
        2. Eclipse has been deployed to the environment feeding test/sandbox
           source schemas.
        3. Source data has landed (check latest rows in the source table).

      Are all three done? (yes / not yet / skip-gate)

  - On `yes`:          set `changes.eclipse.completed = true`; continue.
  - On `not yet`:      stop. Do not show the sandbox deploy command.
  - On `skip-gate`:    print warning; set `changes.eclipse.completed = true`
                       AND `changes.eclipse.skipped_at = <ts>`; continue.

  - If `changes.eclipse.required` is null or false: skip this gate silently.
```

**Location C — Stage `prod-deployed`**

Modify the ask list:

```
Ask:
1. Did prod `deploy.py` succeed? Record timestamp.
2. Did prod `validate.py` pass? Record check counts.
3. Any post-deploy findings?

4. **PBI publish gate** — read `changes.pbi_model`:
   - If `changes.pbi_model.required == true`:
       Ask: `Has the PBIX been published to the GEP Production workspace? (yes / not yet)`
       On `yes`: set `changes.pbi_model.published = true`.
       On `not yet`: stop. Do not transition to `complete`. Print:
           ⛔ PBI Desktop publish required before complete.
           Publish the .pbix to the GEP Production workspace, then run
           `/gep-feature <ticket>` again to resume.
   - If `changes.pbi_model.required` is null or false: ask the current
     question verbatim: `4. PBI Desktop publish complete?` (keeps parity
     with existing flow).
```

### 2. Artifact schema changes

`changes.eclipse`, `changes.pbi_model` — Preamble §D.

### 3. MCP calls

None.

### 4. Interactions

Independent of other items. Implement after item 8.

### 5. Edge cases

| Case | Handling |
|---|---|
| Eclipse scope discovered mid-implementation | Paul edits artifact directly OR re-enters scoping with `force`. Document in prompt wording. |
| `changes` block missing (old artifacts GP-197, GP-208) | Treat as `required: null` → no gates fire. Skill proceeds as pre-item-9. |
| `required == true` but Paul wants to override | `skip-gate` option — sets completed=true + skipped_at timestamp. |

---

## Item 10 — Data dictionary update prompt

### 1. Skill file changes

**Location — Stage `prod-deployed`**, add as step 5 (after item 9's PBI gate):

```
5. **Data dictionary update**

   Read `requirements.delivery`. If the string (case-insensitive) contains
   `_FCT_` or `_DIM_`, extract the fully-qualified table name — keep the
   part that matches `<DB>.<SCHEMA>.<TABLE>` or just `<SCHEMA>.<TABLE>`.

   If no match: skip this step silently.

   If match — prompt:

       🗃️  This ticket delivers a new fact/dimension: <TABLE_NAME>

       Update the wiki data dictionary? (yes / skip)

   On `skip`: record `deploy_history.prod.data_dictionary_prompted = true`
             and `data_dictionary_updated = false`; continue.

   On `yes`: read the ticket's validate manifest at
             `GEP/scripts/validate_manifest/<ticket>.yaml` and extract:
               grain             ← requirements.grain from artifact
               primary_key       ← validate_manifest.tables.<table>.primary_key
               key_columns       ← validate_manifest.tables.<table>.key_columns
               date_column       ← validate_manifest.tables.<table>.date_column
               freshness_days    ← validate_manifest.tables.<table>.freshness_days
               product_key_col   ← validate_manifest.tables.<table>.product_key_column (if set)
               data_source       ← requirements.data_source
               business_logic    ← requirements.business_logic

             Show Paul:

               Wiki page to create/update:
                 C:\Users\PaulRussell\repos\wiki\concepts\business-logic\gep\<table_lowercase>.md

               Fields to document:
                 - Grain:          <grain>
                 - Primary key:    <primary_key>
                 - Key columns:    <key_columns>
                 - Date column:    <date_column>
                 - Freshness:      <freshness_days> days
                 - Product join:   <product_key_col or "n/a">
                 - Source(s):      <data_source>
                 - Business logic: <business_logic>

               Cross-links to add:
                 - [[GEP]]
                 - [[star-schema-convention]]
                 - [[<ticket>]]
                 - (whichever source entity page applies, e.g. [[amazon]])

               Run `/ingest` in a wiki session to draft this page, or write
               it manually following wiki/CLAUDE.md conventions. Update
               wiki/index.md after creation.

             Record `deploy_history.prod.data_dictionary_updated = true`
             once Paul confirms the page has been written (ask: `Page
             created/updated? (yes / later)`). On `later`: set false, add
             to a followup list printed at `complete`.
```

### 2. Artifact schema changes

`data_dictionary_prompted`, `data_dictionary_updated` — Preamble §D.

### 3. MCP calls

None.

### 4. Interactions

Fires only at `prod-deployed` after item 12's prod QA evidence comment. Depends on
the validate manifest existing with populated `tables.<name>.*` fields (enforced at
`scoped` stage — already live).

### 5. Edge cases

| Case | Handling |
|---|---|
| `requirements.delivery` has multiple comma-separated tables | Match each; loop per matched table. |
| Validate manifest missing required fields | Placeholders `[not set — populate manually]`; still prompt. |
| `requirements.delivery` mixed case | Case-insensitive matching on `_FCT_` / `_DIM_`. |
| Extracted table name has DB/schema prefix | Strip for the file path; keep full qualified name in page body. |

---

## Item 11 — Design summary comment at `test-deployed`

### 1. Skill file changes

**Location:** Stage `test-deployed`. Final step order becomes:

```
1. deploy.py succeeded?
2. validate.py passed?
3. PBI smoke-test
4. PR creation           (item 7)
5. Design summary comment (item 11)  ← new
6. QA evidence comment   (item 12)  ← new
7. Client notification
8. Jira status sync      (item 8 → "In Review")
9. Transition to `uat`
```

**New step 5 text (verbatim):**

```
5. **Design summary comment** — post a permanent record of the locked design
   on the Jira ticket before client UAT starts.

   Read from artifact:
     jira_summary, branch, pr_url, requirements (all fields),
     decisions (array), open_questions (answered only).

   Draft body (Markdown):

   ```markdown
   ## Design Summary — <ticket>

   **Branch:** `<branch>`
   **PR:** <pr_url or "_not yet raised_">

   ### Locked Requirements
   - **Data source:** <requirements.data_source>
   - **Grain:** <requirements.grain>
   - **Delivery:** `<requirements.delivery>`
   - **Business logic:** <requirements.business_logic>
   - **History scope:** <requirements.history_scope>

   ### Key Decisions
   1. **<decisions[0].decision>**
      _Why:_ <decisions[0].rationale>
      _Alternatives considered:_ <comma-join decisions[0].alternatives_considered or "none documented">
   2. ...

   ### Questions Resolved During Scoping
   - **Q<id>:** <question> — _<answer>_
   - ...
   (omit section if no answered open_questions)

   ---
   _Posted by `/gep-feature` at <ISO-8601 now>._
   ```

   Apply the confirm-and-post helper from §C. On successful post, record:
     comments_posted.design_summary.test_deployed_at = <ISO-8601 now>
     comments_posted.design_summary.comment_ref = <returned id/url>

   If any required artifact field is empty / null: render as `_[not specified]_`
   in the draft. After showing, ask whether to amend the artifact before
   posting; re-draft on amend.
```

### 2. Artifact schema changes

`comments_posted.design_summary` block — Preamble §D.

### 3. MCP calls

`addCommentToJiraIssue` per §C. Failure → §B.

### 4. Interactions

- Hard dependency on item 7 (`pr_url`). Step ordering enforces this.
- Satisfies item 13 — PR URL always embedded at the top of this comment as the permanent Jira-side record.
- Precedes item 12 and item 8 transition.

### 5. Edge cases

| Case | Handling |
|---|---|
| `decisions` empty | Section shows `_No formal design decisions recorded._` |
| `pr_url == "[skipped]"` | `**PR:** _skipped at engineer discretion_` |
| `pr_url == null` | Defensive abort: `⚠️ PR not yet created. Run step 4 first.` |
| Already posted on prior visit | Ask `Post an updated version? (yes / skip)`; append `(revision N)` to heading. |
| MCP offline | §B — `GEP/tickets/<ticket>/_mcp_queued/<ts>_design_summary.md` |

---

## Item 12 — QA evidence comment at `test-deployed` and `prod-deployed`

### 1. Skill file changes

Add a new reusable procedure to `## MCP setup`, call it **§F. QA evidence comment procedure**:

```
## QA evidence comment (helper)

Called at:
  - Stage `test-deployed` step 6 (env = "test")
  - Stage `prod-deployed` step 3b (env = "prod")

Procedure (parameter: env ∈ {test, prod}):

1. Read `deploy_history.<env>.validate_results` from the artifact.
   If null or path does not exist on disk:
     Print: `⚠️  No saved validate results for <env>. Re-run validate.py
            with --save-results, or type the pass/fail counts manually.`
     Ask: `Continue with manual entry? (yes / skip)`
     On skip → return without posting.
     On yes → collect counts from Paul; skip the per-check table.

2. Read the JSON. Expected top-level fields (VERIFY against validate.py source
   before implementing):
     env, database, ticket, git.sha, git.commit_message, timestamp,
     checks[] { name, value, pass }, summary { passed, total }.

   If structure differs: fall back to a generic "validate passed" comment
   linking to the JSON path; print a note for Paul to review validate.py's
   output schema.

3. Determine pass/fail:
     all_passed = (summary.passed == summary.total)

4. If all_passed:
     Draft PASSING template below.
     Apply §C.

5. If NOT all_passed:
     Do NOT auto-draft. Print:

       ⚠️  validate.py on <env> reported <summary.passed>/<summary.total>
           checks passing. Failing checks:

           - <check.name>: <check.value>
           - <check.name>: <check.value>

       Post a findings note on the Jira ticket? (yes / skip)

     On `yes`: draft FINDINGS template below; apply §C.
     On `skip`: return without posting.

6. On successful post, record:
     comments_posted.qa_evidence.<env>_deployed_at = <ISO-8601 now>
     comments_posted.qa_evidence.<env>_results_snapshot = <path to JSON>

PASSING template:

   ## QA Evidence — <ticket> (<ENV uppercase>)

   **Environment:** <env> (<database>)
   **Git:** `<git.sha[:7]>` — <git.commit_message first line>
   **Validated at:** <timestamp>
   **Result:** ✅ <summary.passed>/<summary.total> checks passed

   | Check | Value | Result |
   |---|---|---|
   | <check.name> | <check.value> | ✅ |
   | ...                                                |

   _Full results file:_ `<path relative to repo root>`
   _Posted by `/gep-feature` at <ISO-8601 now>._

FINDINGS template:

   ## QA Findings — <ticket> (<ENV uppercase>)

   **Environment:** <env> (<database>)
   **Git:** `<git.sha[:7]>` — <git.commit_message first line>
   **Validated at:** <timestamp>
   **Result:** ⚠️ <summary.passed>/<summary.total> checks passed —
   <summary.total - summary.passed> failing.

   ### Failing Checks
   | Check | Value | Result |
   |---|---|---|
   | <failing check> | <value> | ❌ |
   | ...                                               |

   ### Passing Checks
   <summary.passed> checks passed — full table in results file.

   _Full results file:_ `<path>`
   _Next step:_ <to be filled in by Paul before posting>
```

**Invocation points:**

- **`test-deployed` step 6** (after item 11's design summary is posted, before client notification):

  ```
  6. **QA evidence comment** — post validate.py results on the Jira ticket.
     Call §F with env = "test".
  ```

- **`prod-deployed` step 3b** (between existing step 3 "post-deploy findings?" and the item 9 PBI publish gate):

  ```
  3b. **QA evidence comment (production)** — call §F with env = "prod".
  ```

### 2. Artifact schema changes

`comments_posted.qa_evidence` — Preamble §D.

### 3. MCP calls

`addCommentToJiraIssue` per §C. Failure → §B.

### 4. Interactions

- Phase 5 Tier 2 `--save-results` — already live.
- `deploy_history.<env>.validate_results` — populated by Sub-step 1/2 of `implementing` — already live.
- Precedes item 8 transition at `test-deployed`; precedes item 9 PBI gate at `prod-deployed`.
- **Sonnet session must verify JSON schema** by reading `GEP/scripts/validate.py` before wiring the field mapping.

### 5. Edge cases

| Case | Handling |
|---|---|
| `validate_results` is null | Step 1 — manual entry fallback or skip |
| JSON structure differs from expectation | Generic fallback comment with JSON path |
| `summary.total == 0` | Treat as failing; use FINDINGS template; warn Paul to review manifest |
| Re-running `test-deployed` after change-request | Ask `Post updated comment? (yes / skip)`; append `(revision N)` |
| Multi-line commit message | First line only; escape pipes |
| `check.value` contains newlines or pipes | Escape pipes `\|`; replace newlines with space |
| Long check table (> ~30 rows) | Truncate to first 20; append `_… <N> more checks._` |
| MCP offline | §B — `_mcp_queued/<ts>_qa_evidence_<env>.md` |

---

## Item 13 — PR remote link on Jira ticket

### 1. Analysis & chosen approach

Available MCP tools for Jira linking:
- `createIssueLink` — **Jira-to-Jira only**. Does NOT create remote web links.
- `getJiraIssueRemoteIssueLinks` — read-only; lists existing remote links.
- No `createRemoteIssueLink` tool is exposed.

Therefore **we cannot programmatically create a remote URL link via MCP**.

Alternatives:
1. **Jira native GitHub integration** — if the Atlassian GitHub app is installed on the ALDC workspace, Jira auto-detects commits/PRs whose branch name or commit message contains the ticket key (e.g. `GP-208`) and surfaces them in the Development panel. Branch naming convention `feature/paulrussell/gp-208/...` already satisfies this.
2. **Embed the PR URL in an ordinary comment** — persistent, searchable, permanent. Done by item 11.

**Decision:** rely on both.
- Native GitHub integration is best-effort (no-op if active; invisible if not).
- Item 11's design summary comment always embeds the PR URL at the top, guaranteeing a permanent record regardless of integration state.

No new MCP calls, no `createIssueLink` usage. Item 13 = documentation + one-time detection probe after PR creation.

### 2. Skill file changes

Inside Item 7's step 4, append a final sub-step:

```
   After `gh pr create` succeeds and `pr_url` is recorded, perform a
   one-time GitHub-integration check:

     - Call `getJiraIssueRemoteIssueLinks` (cloudId, issueIdOrKey=<ticket>).
     - Count links whose `application.type` is "com.atlassian.jira.plugins.github"
       or whose `object.url` contains "github.com".

   Wait up to 60s after PR creation (re-query every 15s) for GitHub
   integration to populate. Then:

     - If any GitHub remote link is found:
         Print: `✓ GitHub integration active — PR surfaced on Jira automatically.`
         Record `pr_jira_integration = "native"`.
     - If none found after 60s:
         Print: `ℹ️  No GitHub integration detected on this workspace.
                PR URL will still appear in the design summary comment
                (step 5) as the permanent record.`
         Record `pr_jira_integration = "via_comment"`.

   Do not fail the step on MCP errors — §B applies (record `null`, skip).
```

Also add a `## Rules` entry:

> 8. **PR URL surfacing on Jira.** Prefer Jira's native GitHub integration
>    (triggered automatically by branch naming). The design summary comment
>    (step 5 at `test-deployed`) always embeds the PR URL as a fallback.
>    Do not use `createIssueLink` — that tool is for Jira-to-Jira links, not
>    remote web URLs.

### 2. Artifact schema changes

`pr_jira_integration` — Preamble §D.

### 3. MCP calls

| Tool | Parameters | Failure handling |
|---|---|---|
| `getJiraIssueRemoteIssueLinks` | `cloudId`, `issueIdOrKey` | §B — record `null`; skip |

### 4. Interactions

- Hard dependency on item 7.
- Reinforces item 11.

### 5. Edge cases

| Case | Handling |
|---|---|
| PR skipped (`pr_url == "[skipped]"`) | Skip integration check; `pr_jira_integration = null` |
| Manual URL entry (PR already existed) | Still run check — native app will have already surfaced it |
| MCP offline | §B — `pr_jira_integration = null`; item 11 comment is the record |
| 60s poll is long | Acceptable — runs while Paul reviews other steps. If problematic, lower to single 15s check. |
| Multiple GitHub links on ticket | Still set `pr_jira_integration = "native"` |

---

## Dependency graph

```
Item 7 (PR create)
   ├── sets pr_url, pr_created_at
   │
   ├──► Item 11 (reads pr_url in design summary body)
   │
   └──► Item 13 (GitHub integration check runs at PR creation)
            │
            └──► reinforces Item 11 as fallback surface

Item 8 (Jira status transitions)
   ├── establishes §E helper procedure
   ├── invoked at scoped→implementing, test-deployed→uat, prod-deployed→complete
   └── no data dependencies

Item 9 (Eclipse/PBI tracking)
   ├── adds scoped-stage Q&A
   └── adds sandbox-deploy gate + prod-deployed gate

Item 10 (Data dictionary)
   ├── reads requirements.delivery (already in artifact)
   └── reads validate_manifest.tables.<name>.*

Item 12 (QA evidence)
   ├── depends on Phase 5 Tier 2 --save-results (already live)
   ├── depends on deploy_history.<env>.validate_results (already live)
   └── reuses §C confirm-and-post helper
```

## Recommended implementation order

| # | Item | Why this order |
|---|---|---|
| 1 | **Preamble §A–§D** | Must land first — §A/§B/§C used by items 8/11/12/13. §D consolidates all artifact additions so schema is updated once. |
| 2 | **Item 8 — Jira status transitions** | Creates §E, the canonical MCP-call-with-confirmation pattern. Items 11/12 easier to write after this exists. |
| 3 | **Item 9 — Eclipse/PBI tracking** | Small, self-contained, no MCP. Exercises new artifact fields (sanity check on §D). |
| 4 | **Item 7 — PR creation** | Gates items 11 and 13. |
| 5 | **Item 13 — PR remote link** | Small addition inside item 7. Do immediately while that stage is fresh. |
| 6 | **Item 11 — Design summary comment** | Reuses §C; reads `pr_url`. |
| 7 | **Item 12 — QA evidence comment** | Biggest item. Done last so §C is well-exercised. Verify validate.py's JSON schema first. |
| 8 | **Item 10 — Data dictionary prompt** | Tailpiece. Standalone, no MCP, only runs at `prod-deployed`. |

Each step = one commit. Suggested commit messages:

1. `refactor(skill): add MCP setup section — cloudId resolution, offline fallback, comment helper, consolidated artifact schema`
2. `feat(skill): Jira status transitions at stage boundaries with offline fallback (item 8)`
3. `feat(skill): Eclipse/PBI change tracking at scoped + sandbox/prod gates (item 9)`
4. `feat(skill): gh pr create step at test-deployed with artifact capture (item 7)`
5. `feat(skill): Jira GitHub-integration detection after PR creation (item 13)`
6. `feat(skill): design summary comment at test-deployed (item 11)`
7. `feat(skill): QA evidence comment at test-deployed and prod-deployed (item 12)`
8. `feat(skill): data dictionary prompt at prod-deployed for new FCT/DIM (item 10)`

## Notes for the Sonnet session

- **Validate manifest schema verification (item 10)** — read one live manifest (e.g. `GEP/scripts/validate_manifest/GP-208.yaml`) to confirm the field names (`tables.<name>.primary_key`, `key_columns`, `date_column`, `freshness_days`, `product_key_column`). Plan assumes Phase 5 Tier 1 schema; confirm before using.
- **validate.py JSON schema verification (item 12)** — read `GEP/scripts/validate.py` and find the `--save-results` writer. Confirm the exact top-level keys and `checks[]` structure before wiring item 12's template. Adjust if different.
- **`gh` CLI behaviour** — `gh pr create --body-file <path>` reads body from file. Path: `GEP/tickets/<ticket>/_pr_body.md`. Add `GEP/tickets/*/_pr_body.md` to `.gitignore` in a trivial pre-item-7 commit.
- **Do not run `git commit`** — per standing rule. Summarise after each edit; Paul stages and commits.

## See Also

- [[client-workflow-automation]] — workstream tracker
- [[workflow-automation]] — design doc
- [[GEP]]
- [[gep-snowflake-pbi-deployment]]
