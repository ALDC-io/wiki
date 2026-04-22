---
tags: [distributed-workflow, active, client-workflow-automation, implementation-plan, power-bi]
aliases: [Phase 6 PBI Automation Plan, Phase 6 Plan]
sources: []
created: 2026-04-21
updated: 2026-04-21 (revised after Paul's Q&A — auth path changed from SPN to user OAuth, seed scripted)
---

# Phase 6 — Power BI Model Automation Plan

Produced by Opus 4.7 planning session (2026-04-21, effort xhigh).
A follow-on Sonnet implementation session will read this file verbatim as its spec.

**Target file (only, when implementing):** `.claude/commands/gep-feature.md`
**Branch:** `feature/paulrussell/workflow-automation/gep-scripted-deploy`

See [[client-workflow-automation]] for workstream context, prior phases,
and the blocker ("Multi-feature conflict in TEST / PBI") this phase resolves.

**Core thesis.** XMLA write is the confirmed programmatic channel into GEP's
tabular model. That unlocks scripted model change (Tabular Editor CLI) + scripted
refresh (REST API) against an **isolated sandbox dataset** before anything touches
the shared client-facing TEST workspace. The visual/report-layout layer stays
manual until Microsoft ships visual APIs — this plan does not try to automate it.

---

## 1. Q1 — Technical feasibility matrix

| Option | Capability (model changes) | Capability (refresh / workspace ops) | Confirmed / Blocked | Realistic effort | Role in v1 |
|---|---|---|---|---|---|
| **Tabular Editor CLI** (TE 2 free, TE 3 commercial) via XMLA | ✅ Full — relationships, measures, calculated columns, tables, perspectives, RLS, translations, datasource connection strings via C# script or TMSL/BIM deploy | ❌ Not for refresh | ✅ **CONFIRMED** (XMLA write confirmed for GEP) | LOW–MED (install + one reusable wrapper) | **Primary write path** |
| **pbi-tools** (OSS; `.pbix` ↔ PBIXProj/PBIP/TMDL) | ✅ Round-trips the `.pbix` to disk → Git-friendly TMDL/PBIP source of truth; can also deploy via XMLA | ❌ Not for refresh | ✅ Available (no licence needed) | MED (community-maintained; Windows-only tooling chain) | **v2 stretch** — model-file version control |
| **BIM / TMDL** (JSON / text model definitions) | ✅ Data format — full tabular model definition | ❌ N/A (format, not tool) | ✅ Available | LOW (artefact format) | **v2 stretch** — source-of-truth format for model |
| **Power BI REST API** | ❌ Cannot edit model structure. Partial: `Update Parameters` rebinds connection string if the PBIX uses parameters. `Update Datasources` works for some connectors (Snowflake is supported but quirky). | ✅ Full — workspace CRUD (`Groups - Create/Delete`), `.pbix` import (`Imports - Post Import`), refresh trigger + poll (`Refreshes - Refresh Dataset` + `Get Refresh History`), gateway binding, user/access | ✅ Available (OAuth SPN or user token) | LOW | **Refresh + polling + parameter rebind** |
| **Power BI Deployment Pipelines API** | ❌ Cannot edit in-place | ✅ Stage promotion (`Pipelines - Deploy All / Deploy Selected`), diff between stages | ⚠️ **UNKNOWN for GEP** — requires a pre-configured Deployment Pipeline on the workspace | MED (pipeline setup is one-time admin work; API calls are easy) | **v2 stretch / Level 3** |

**Key non-obvious findings**

1. **Tabular Editor CLI is the *only* confirmed path for model changes.** REST API does not expose model metadata mutations. pbi-tools can also deploy via XMLA but adds tooling surface area for no v1 benefit.
2. **REST API *can* create workspaces** (the design doc §3.2 claim that workspace creation is blocked is outdated as of 2025). `POST /v1.0/myorg/groups` works — but workspace creation requires the workspace be assigned to a Premium / PPU / Fabric capacity to support XMLA write, and each extra workspace consumes capacity. One persistent sandbox workspace is cheaper than per-ticket provisioning.
3. **Tabular Editor 2 (free, .NET Framework) is sufficient** for CLI model scripting. TE 3 (commercial) adds TMDL authoring UX and Best Practice Analyzer but is not required for the CLI path. The skill should assume TE 2 by default; TE 3 is fine if already installed.
4. **Visual-layer changes cannot be automated.** Measures, relationships, calculated columns = XMLA-writable. Visual layout, bookmarks, slicer state, colours = `.pbix` report layer, no public API. The artefact must distinguish these two.
5. **Data-source rebinding has two viable patterns:**
   a. The PBIX already uses **parameterised** connection fields (DB name, warehouse, role). `Update Parameters` REST call flips them to the sandbox Snowflake DB. **Recommended** — cleanest.
   b. The PBIX is hard-coded. TE CLI rewrites the `dataSource.connectionDetails` via script. More invasive.
   The current PBIX parameterisation status is an open question (§5, Q7).
6. **Refresh triggering is fire-and-poll, not synchronous.** REST returns `202 Accepted` with a request ID; the skill must poll `GET /refreshes/{id}` every 15–30s until `status` is `Completed` or `Failed`. Same pattern already used in deploy.py for Snowflake task polling — reuse the mental model.

---

## 2. Q2 — Chosen sandbox isolation model

### Decision

**Option B — dedicated "GEP Sandbox Models" workspace, single persistent dataset, rebound at runtime to the per-ticket Snowflake sandbox DB.**

Rejected: Option A (per-ticket workspace clone), Option C (file-only), Option D (full hybrid with TMDL version control) for v1. Rationale below.

### Shape of the chosen option

One persistent workspace: **`GEP Sandbox Models`**.

One persistent dataset inside it: **`GEP_Sandbox_Current`** — seeded once from a copy of the production `.pbix`, with parameterised Snowflake connection (DB, warehouse, role). All model metadata mirrors the production model as the starting baseline.

Per ticket workflow:

```
  (Snowflake sandbox DB exists: SANDBOX_DG1_GEP_<ticket>)
  ─────────────────────────────────────────────────────────
  1. REST: Update Parameters → point GEP_Sandbox_Current at SANDBOX_DG1_GEP_<ticket>
  2. TE CLI: apply changes.pbi_model.script.cs to the sandbox XMLA endpoint
  3. REST: Refreshes - Refresh Dataset → poll to success
  4. [manual] Paul opens workspace in PBI Service, eyeballs affected visuals
  5. Skill records changes.pbi_model.sandbox_validated = true
  6. [optional] Revert the sandbox dataset back to a clean baseline
     (re-deploy seed model via TE CLI) so the next ticket starts clean
```

### Why not Option A (per-ticket workspace clone)

- Each new workspace consumes capacity. GEP's capacity SKU is finite.
- Workspace provisioning, `.pbix` re-upload, and teardown per ticket adds 5–15 minutes of overhead vs. an API-driven rebind on a persistent dataset.
- The isolation benefit is not per-ticket — it is "separate from client-facing TEST." A single persistent sandbox workspace achieves that cleanly.
- Upgrade path: if parallelism ever demands per-ticket PBI isolation (today's reality is one Paul, one ticket in sandbox at a time — the skill serialises TEST; sandbox is implicitly serialised by who's doing the work), Option B generalises to Option A by spawning ephemeral workspaces through the same REST primitives already in place.

### Why not Option C (file-only)

- Does not catch refresh failures, data-dependent measure errors, relationship cardinality issues that only surface against real data.
- Useful as a pre-check ("does the script compile?") but not sufficient as a standalone sandbox.
- Captured as a **pre-flight step within v1** (run TE CLI with `/d` to compile the script without deploying) — not as the sandbox mechanism.

### Why not Option D (TMDL/BIM version control + sandbox dataset)

- TMDL authoring requires TE 3 or pbi-tools — added tooling.
- v1 scope: get model automation working. Source-of-truth version control is a separate concern best decoupled.
- **Deferred to v2 stretch** — once Level 2 automation is stable, pbi-tools can extract the sandbox dataset to TMDL for Git storage, closing the loop between `.pbix` binaries in `repos/power_bi` and a text source of truth.

### Trade-offs accepted

| Trade-off | Consequence | Mitigation |
|---|---|---|
| Single sandbox dataset, not per-ticket | Two concurrent sandbox runs would collide | Skill serialises work today; if it ever matters, upgrade to Option A (clones) |
| Rebind state is mutable | A prior ticket's model edits stay in the dataset until the next run overwrites them | Always apply the full model script, not incremental edits; script is idempotent against the seed |
| Sandbox dataset is NOT a perfect mirror of production visuals | Paul's eyeball smoke-test in the sandbox workspace won't preview client-facing visuals exactly | Acceptable — the *model* is what's being validated; visual changes are flagged separately (`visual_required`) and go through the existing manual PBI Desktop flow |
| Requires one-time seed | Must create workspace, upload baseline `.pbix`, parameterise connection, grant permissions | One-time setup, documented in §6.1 |

### Alignment with Snowflake sandbox pattern

| Aspect | Snowflake sandbox | PBI sandbox (this plan) |
|---|---|---|
| Granularity | Per-ticket DB clone (`SANDBOX_DG1_GEP_<ticket>`) | Single persistent dataset, rebound per ticket |
| Created | On-demand at Sub-step 1 | Pre-created; reused |
| Torn down | After Sub-step 1 passes (optional, Paul prompted) | Not torn down — reset by next ticket's script |
| Isolation from TEST | Full (separate DB) | Full (separate workspace — client cannot see `GEP Sandbox Models`) |
| Write path | SQL via `snowflake-connector-python` | C# script via Tabular Editor CLI over XMLA |
| Refresh trigger | EXECUTE TASK + poll TASK_HISTORY | REST `Refreshes - Refresh Dataset` + poll `Get Refresh History` |

The **shape** matches; the **granularity** is deliberately coarser because the blast radius of a sandbox collision at PBI is much lower than at Snowflake (no downstream consumers, no data).

---

## 3. Q3 — Workflow integration design

### 3.1 Current stage flow (reference)

```
scoping → scoped → implementing → test-deployed → uat → prod-deployed → complete
                      │
                      ├─ Sub-step 1:  Eclipse gate → Snowflake sandbox deploy + validate → teardown prompt
                      └─ Sub-step 2:  (SQL confirm) → TEST serialisation check → Snowflake TEST deploy + validate
```

### 3.2 Proposed flow with Sub-step 1b

```
scoping → scoped → implementing → test-deployed → uat → prod-deployed → complete
                      │
                      ├─ Sub-step 1:  Eclipse gate → Snowflake sandbox deploy + validate → teardown prompt
                      │
                      ├─ Sub-step 1b: ★ NEW — PBI sandbox model validation
                      │               (gated: changes.pbi_model.required == true)
                      │
                      └─ Sub-step 2:  (SQL confirm) → TEST serialisation check →
                                      Snowflake TEST deploy + validate →
                                      ★ NEW — TE CLI applies model script to TEST workspace + refresh
```

### 3.3 Sub-step 1b — full pseudocode

The spec below is authoritative for the Sonnet implementation session.

```
Sub-step 1b — PBI sandbox model validation
───────────────────────────────────────────

GATE
  if changes.pbi_model.required != true (null | false | absent):
    print "ℹ️  No PBI model changes declared — skipping PBI sandbox validate."
    return  # proceed straight to Sub-step 2

  if changes.pbi_model.sandbox_validated == true AND not forced re-run:
    print "✓ PBI sandbox already validated for this ticket."
    return

PRE-FLIGHT
  Verify artefacts exist on disk:
    - GEP/tickets/<ticket>/pbi_model_script.cs  (the TE C# script)
  If missing:
    print instructions to Paul to draft the script (see 3.4 below), then stop.

  Compile-only check:
    TabularEditor.exe /s pbi_model_script.cs /d NULL
    # Tabular Editor 2 does not support a true --dry-run, but we can target
    # an invalid XMLA URL and inspect stderr for script-compile errors only.
    # Alternative: wrap the user script in a `Model.SaveChanges()` gate and
    # catch DAX/reference errors before connecting.
  On failure: surface the compile error verbatim; do not proceed.

REBIND SANDBOX DATASET TO TICKET'S SNOWFLAKE SANDBOX DB
  POST https://api.powerbi.com/v1.0/myorg/groups/{SANDBOX_WORKSPACE_ID}
        /datasets/{SANDBOX_DATASET_ID}/Default.UpdateParameters
  Body: { "updateDetails": [
    { "name": "SNOWFLAKE_DATABASE", "newValue": "SANDBOX_DG1_GEP_<ticket>" },
    { "name": "SNOWFLAKE_ROLE",     "newValue": "<SANDBOX_ROLE>" }
    # SNOWFLAKE_HOST and SNOWFLAKE_COMPUTE stay pointed at og35375 + COMPUTE_WH —
    # sandbox Snowflake DBs live on the non-prod account, same host as TEST.
  ] }
  On non-2xx: print error; ask "skip to manual?" (yes / abort).

APPLY MODEL SCRIPT VIA TE CLI
  Construct XMLA endpoint:
    <sandbox_xmla> = "powerbi://api.powerbi.com/v1.0/myorg/GEP Sandbox Models"

  Show command:
    TabularEditor.exe \
      /s pbi_model_script.cs \
      /x "Provider=MSOLAP;Data Source=<sandbox_xmla>;Initial Catalog=GEP_Sandbox_Current;User ID=app:<SPN_CLIENT_ID>@<TENANT_ID>;Password=<SECRET>"

  Ask: "Run this command? (yes / edit-script / skip)"
  On yes: run via Bash, capture stdout/stderr.
  On non-zero exit: surface stderr; ask whether to continue or abort.

TRIGGER REFRESH + POLL
  POST .../datasets/{SANDBOX_DATASET_ID}/refreshes
  Body: { "type": "Full", "commitMode": "transactional", "notifyOption": "NoNotification" }
  → capture X-MS-Request-ID header (the refresh request ID)

  Poll every 20s (up to 20 min):
    GET .../datasets/{SANDBOX_DATASET_ID}/refreshes/{refreshId}
    → status ∈ { Unknown, InProgress, Completed, Failed, Cancelled }
  On Completed: proceed.
  On Failed: show serviceExceptionJson; ask "retry / skip / abort".

MANUAL VISUAL CHECK
  Print:
    "✓ Sandbox dataset refreshed. Open GEP Sandbox Models workspace in
     Power BI Service and verify:
       1. Affected measures / relationships / calculated columns render.
       2. No data errors in visuals that depend on the changed model parts.
       3. Row counts look sane (cross-check against Snowflake sandbox validate).

     Sandbox validation result? (pass / fail / retry)"

RECORD OUTCOME
  On pass:
    changes.pbi_model.sandbox_validated = true
    changes.pbi_model.sandbox_applied_at = <ISO-8601 now>
    changes.pbi_model.sandbox_refresh_id = <refreshId>
    changes.pbi_model.sandbox_script_hash = <sha256 of pbi_model_script.cs>
    print "✓ PBI sandbox validated. Proceeding to Sub-step 2 (TEST)."
  On fail:
    changes.pbi_model.sandbox_validated = false
    append failure description to changes.pbi_model.findings[]
    stop — do not proceed to TEST.
  On retry:
    return to REBIND step.
```

### 3.4 How the TE C# script is generated

Two supported patterns, Paul chooses per ticket:

**Pattern 1 — Skill drafts the script from `changes.pbi_model.description`**

The skill prompts:
```
Draft a Tabular Editor C# script for the declared PBI model changes?
Description: <changes.pbi_model.description>
(yes / I'll write it myself / skip)
```

On `yes`, the skill writes `GEP/tickets/<ticket>/pbi_model_script.cs` using a template library:

```csharp
// NEW MEASURE example
Model.Tables["Sales"].AddMeasure(
    "Gross Margin %",
    "DIVIDE([Gross Profit], [Net Sales])",
    "Profitability"
);

// NEW RELATIONSHIP example
Model.AddRelationship(
    Model.Tables["Sales"].Columns["ProductKey"],
    Model.Tables["Product"].Columns["ProductKey"]
);

// NEW CALCULATED COLUMN example
Model.Tables["Product"].AddCalculatedColumn(
    "Category Tier",
    "SWITCH(TRUE(), [Sales] > 1e6, \"A\", [Sales] > 1e5, \"B\", \"C\")"
);

Model.SaveChanges();
```

Paul reviews before execution. The skill NEVER runs a freshly-drafted script without explicit `yes`.

**Pattern 2 — Paul writes the script**

`GEP/tickets/<ticket>/pbi_model_script.cs` is checked in alongside the SQL changes; skill detects its presence and skips the drafting step. This is the preferred pattern for non-trivial changes (multiple measures, complex DAX).

### 3.5 Changes to `Sub-step 2` — TEST deploy

After the existing Snowflake TEST deploy steps, insert:

```
If changes.pbi_model.required == true AND changes.pbi_model.sandbox_validated == true:

  APPLY TE SCRIPT TO CLIENT-FACING TEST WORKSPACE
    - Confirm with Paul: "Apply the same PBI model script to GEP Test Models? (yes / skip)"
    - TabularEditor.exe /s pbi_model_script.cs /x "<test_xmla>;Catalog=<TEST_DATASET_NAME>"
    - Trigger + poll refresh on the TEST dataset (same REST pattern).
    - Record: changes.pbi_model.test_applied_at, test_refresh_id.

If changes.pbi_model.required == true AND NOT sandbox_validated:
  ⛔ block Sub-step 2 — sandbox must pass first.
```

This is the payoff: the same validated script promotes from sandbox to TEST with no model rewrite.

### 3.6 Changes to `test-deployed` step 3 (PBI smoke-test)

Existing language:
> **PBI smoke-test** — prompt Paul to check the Power BI Test Model before notifying the client...

Refine to split into:
- **Automated-already** (new): model changes have already been applied to the TEST dataset in Sub-step 2 and the dataset has been refreshed. Confirm `changes.pbi_model.test_applied_at` is set; if so, skip refresh prompt.
- **Visual check** (unchanged): Paul opens the report, confirms affected visuals render and no regressions. This step stays manual.

The existing step becomes shorter — refresh is already done by the time Paul gets here.

### 3.7 Changes to `prod-deployed` PBI publish gate

Existing gate (Phase 5 Tier 3):
```
If changes.pbi_model.required == true:
  Ask: "Has the PBIX been published to the GEP Production workspace? (yes / not yet)"
```

New conditional auto-publish:
```
If changes.pbi_model.required == true:
  If changes.pbi_model.visual_required == true:
    # Model *and* visual changes — visuals require PBI Desktop republish.
    # Keep manual gate for the visual part; offer to auto-apply model part.
    Ask: "Has the PBIX been published to the GEP Production workspace? (yes / not yet)"
    On yes: set published = true.

  Else (visual_required == false — metadata-only changes):
    Ask: "Apply the PBI model script to the Production workspace via XMLA? (yes / skip to manual)"
    On yes:
      - TabularEditor.exe /s pbi_model_script.cs /x "<prod_xmla>;Catalog=<PROD_DATASET_NAME>"
      - Trigger + poll refresh on the PROD dataset.
      - Record changes.pbi_model.prod_applied_at, prod_refresh_id.
      - Set published = true.
    On skip to manual: fall back to existing manual-publish prompt.
```

The `visual_required` flag is set at `scoped` stage (§3.8 below).

### 3.8 Artifact schema changes

Extend the existing `changes.pbi_model` block (current fields: `required`, `description`, `published`):

```yaml
changes:
  pbi_model:
    required: null                # (existing) true | false | null
    description: ""               # (existing)
    published: false              # (existing)

    # NEW — Phase 6 additions
    visual_required: null         # true | false | null — asked at `scoped`
                                  # false ⇒ prod publish can be automated via TE CLI
                                  # true  ⇒ prod publish stays manual (.pbix republish)

    script_path: null             # relative path to GEP/tickets/<ticket>/pbi_model_script.cs
    script_hash: null             # sha256; recorded after each successful apply so we can
                                  # detect drift if the same script is reapplied later

    sandbox_validated: false      # set after Sub-step 1b passes
    sandbox_applied_at: null      # ISO-8601 timestamp of the TE CLI apply against sandbox
    sandbox_refresh_id: null      # PBI refresh request ID for the sandbox refresh

    test_applied_at: null         # set when script applied to GEP Test Models (Sub-step 2)
    test_refresh_id: null

    prod_applied_at: null         # set at prod-deployed if metadata-only auto-apply ran
    prod_refresh_id: null

    findings: []                  # free-text notes from any sandbox/test/prod apply
```

Config lives in `GEP/scripts/pbi_config.yaml` (gitignored), not in the per-ticket artefact. Revised shape after Q5.8 (in light of Paul's IDE signal pointing at `GEP/scripts/.env`):

```yaml
# GEP/scripts/pbi_config.yaml — gitignored
tenant: "<Paul's Azure AD tenant — filled at A.2>"

tabular_editor_path: "C:\\Program Files (x86)\\Tabular Editor\\TabularEditor.exe"

workspaces:
  sandbox:
    id: "<filled by pbi_seed_sandbox.py>"
    name: "GEP Sandbox Models"
    dataset_id: "<filled by pbi_seed_sandbox.py>"
    dataset_name: "GEP_Sandbox_Current"
  test:
    id: "<Paul fills>"
    name: "GEP Test Models"
    dataset_id: "<Paul fills>"
    dataset_name: "<Paul fills>"
  prod:
    id: "<Paul fills>"
    name: "<Paul fills>"
    dataset_id: "<Paul fills>"
    dataset_name: "<Paul fills>"

parameter_names:                # actual names as they exist in the GEP PBIX
  host: "SNOWFLAKE_HOST"
  compute: "SNOWFLAKE_COMPUTE"
  database: "SNOWFLAKE_DATABASE"  # added by Tranche A.0.6
  role: "SNOWFLAKE_ROLE"          # added by Tranche A.0.6
```

No SPN client ID. No secrets. Bearer token comes from `az` at runtime (§I). The only thing in `GEP/scripts/.env` that needs to change is optionally a `PBI_CONFIG_PATH` override if Paul wants to relocate the config file.

### 3.9 New `scoped` stage question (extends item 2b from Phase 5 Tier 3)

Current prompt (after PBI yes/no):
> If yes, ask: `Describe the PBI model changes in one sentence:`

Add a follow-up:
> `Do these changes include visual / report-layout edits (new pages, visual swaps,
>  bookmark changes, etc.), or are they model-metadata only (measures, relationships,
>  calculated columns)?`
> `(visual-included / metadata-only)`
>
> Set `changes.pbi_model.visual_required = true` on `visual-included`,
> `= false` on `metadata-only`.

Rationale: the payoff of XMLA automation (auto-apply to prod) only applies to metadata-only changes. Flagging at scoping keeps downstream gates honest.

### 3.10 New MCP setup subsections

Add to the existing `## MCP setup` block in `gep-feature.md`:

**§G — Tabular Editor CLI helper**

Parameter: `env` ∈ {sandbox, test, prod}, `script_path`.

1. Resolve XMLA endpoint and catalog name from `pbi_config.workspaces.<env>.name` and `pbi_config.workspaces.<env>.dataset_name` (read from `GEP/scripts/pbi_config.yaml`).
2. Acquire bearer token (§I — shared helper below).
3. Build connection string:
   `Provider=MSOLAP;Data Source=powerbi://api.powerbi.com/v1.0/myorg/<workspace_name>;Initial Catalog=<dataset_name>;User ID=AzureAD;Password=<bearer_token>`
4. Command:
   `"<tabular_editor_path>" /s "<script_path>" /x "<connection_string>"`
5. Show to Paul with the bearer token redacted as `<bearer>` (never print tokens). Ask `(yes / edit-script / skip)`.
6. On `yes`: run via Bash. Capture stdout + stderr + exit code.
7. On non-zero with auth-related stderr (401, "unauthorized"): re-acquire token via §I, retry once.
8. On any other non-zero: print stderr; ask `(retry / skip / abort)`.

**§H — PBI REST helper**

Parameter: one of {`update_parameters`, `refresh_dataset`, `poll_refresh`}, plus target (`env` + payload).

Authentication: acquire bearer token via §I. Pass via `Authorization: Bearer <token>`. Cache token for session; re-acquire once on 401, then fail hard.

- `update_parameters`: `POST groups/{workspace_id}/datasets/{dataset_id}/Default.UpdateParameters`
- `refresh_dataset`: `POST groups/{workspace_id}/datasets/{dataset_id}/refreshes` → capture request ID from `Location` header or `x-ms-request-id`.
- `poll_refresh`: `GET groups/{workspace_id}/datasets/{dataset_id}/refreshes/{request_id}` every 20s until `status ∈ {Completed, Failed, Cancelled}` or 20-min timeout.

On any HTTP error: print response body verbatim; follow §B-style fallback (print warning, save failing payload to `_mcp_queued/`, ask whether to continue). PBI REST failures should NOT block sandbox validation silently — they are different from Jira MCP failures because they are on the critical path, not a side channel. Distinguish the two: §B for Jira (non-blocking), §H for PBI (blocks Sub-step 1b).

**§I — Azure CLI bearer token helper (shared by §G and §H)**

One-shot: returns a PBI access token. Caches in-memory for the session.

1. Run `az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv` via Bash. Capture stdout.
2. On non-zero exit or empty stdout (not logged in):
   ```
   ⚠️  Not logged in to Azure CLI. Run `az login` in a terminal, then retry.
   (retry / abort)
   ```
   On `retry`: re-run. On `abort`: raise — callers (§G, §H) follow their respective failure paths.
3. On success: cache the token in session memory, return it.
4. Callers detect 401 and call `invalidate_token()` + re-invoke §I once before giving up.

Never log or echo the token value. When displaying commands to Paul, always substitute the literal string `<bearer>` for the token in the printed command.

### 3.11 Rule additions (at end of `gep-feature.md`)

Append to the `## Rules` block:

```
9. PBI model changes applied via XMLA are logged by hash. Never re-apply a script
   whose hash does not match the recorded value without prompting Paul — drift
   between artefact and live model is a risk signal.
10. The sandbox dataset is a shared mutable resource. Always re-apply the seed
    baseline (or re-run the full per-ticket script) before assuming state —
    never assume what a prior run left behind.
11. PBI REST failures on the critical path (refresh trigger, parameter update,
    poll) BLOCK the stage. This differs from Jira MCP (§B) which never blocks.
    Follow §H recovery flow: retry / skip-to-manual / abort.
```

---

## 4. Q4 — Recommended automation level

### Recommendation: **Level 2 for v1**

Level 2 = *Skill runs Tabular Editor CLI directly to apply model changes to a sandbox
dataset; triggers REST API refresh; polls until complete; Paul reviews then promotes.*

### Why Level 2, not Level 3

Level 3 requires:
1. A pre-configured **Deployment Pipeline** on the GEP Power BI workspace (sandbox → test → prod stages). Unknown whether this exists — most ALDC engagements haven't set one up. If it doesn't exist, ~half a day of workspace admin work to create it.
2. The sandbox workspace being wired into the pipeline as the dev stage. That is an unusual configuration (Deployment Pipelines are typically set up with dev/test/prod all being client-facing stages, not a private sandbox upstream).
3. Programmatic visual regression — not feasible at all with current Microsoft APIs.

Level 2 achieves 90% of the value (scripted model apply, scripted refresh, sandbox-before-TEST gate) without any of the pipeline setup. The remaining 10% (automated stage promotion) is stretch-worthy but not blocker-worthy. **Paul's eyes on affected visuals remain the final sign-off** until Microsoft ships visual APIs — that gate exists at both Level 2 and Level 3.

### Why Level 2 is a genuine upgrade over Level 1

Level 1 = "skill generates script, Paul runs TE CLI manually." That is basically what the skill could generate today from `changes.pbi_model.description` by writing to a file. The only new primitive Level 2 adds is `Bash("TabularEditor.exe /s ... /x ...")` with the connection string constructed from config, plus PBI REST token + calls. Both are well-supported and have ~80% of the risk of Level 3 at ~20% of the effort.

### Specific v1 tool + call sequence (Level 2)

```
───────────────────────── Sub-step 1b (sandbox) ─────────────────────────
1. [skill]   check gate: changes.pbi_model.required == true
2. [skill]   verify GEP/tickets/<ticket>/pbi_model_script.cs exists
3. [skill]   compile-only lint: TabularEditor.exe /s <script>   (no /x)
4. [REST]    Update Parameters on sandbox dataset → DB=<sandbox DB>
5. [skill]   ask Paul to confirm command
6. [BASH]    TabularEditor.exe /s <script> /x "<sandbox XMLA + SPN>"
7. [REST]    Refreshes - Refresh Dataset on sandbox
8. [REST]    poll Get Refresh History until Completed (20s interval, 20min max)
9. [skill]   prompt Paul for visual pass/fail
10. [skill]  record sandbox_validated, sandbox_applied_at, sandbox_refresh_id

───────────────────────── Sub-step 2 (TEST, new tail) ─────────────────────
11. [skill]  if sandbox_validated == true AND changes.pbi_model.required:
               ask Paul to confirm promotion to TEST
12. [BASH]   TabularEditor.exe /s <script> /x "<test XMLA + SPN>"
13. [REST]   Refreshes - Refresh Dataset on TEST dataset
14. [REST]   poll to Completed
15. [skill]  record test_applied_at, test_refresh_id

───────────────────────── prod-deployed (new conditional) ─────────────────
16. [skill]  if visual_required == false:
               ask Paul to confirm auto-apply to PROD
17. [BASH]   TabularEditor.exe /s <script> /x "<prod XMLA + SPN>"
18. [REST]   Refreshes - Refresh Dataset on PROD
19. [REST]   poll to Completed
20. [skill]  record prod_applied_at, prod_refresh_id; set published = true
```

### v2 stretch goals (explicit, not hidden)

**v2a — Deployment Pipelines integration (Level 3).** Once a Deployment Pipeline is set up on GEP's Power BI, swap steps 12–14 (TE CLI apply to TEST) for `PipelineOperations - Deploy All` from the sandbox stage to test. Same for prod.

**v2b — TMDL version control (Option D from Q2).** Use pbi-tools to extract the sandbox dataset to TMDL after each successful apply. Commit the TMDL to Git alongside the SQL. The `.pbix` file stays in `repos/power_bi` as a binary snapshot but the source-of-truth model is text.

**v2c — Per-ticket workspace clones (Option A from Q2).** If parallel in-flight tickets ever demand per-ticket PBI isolation, upgrade the sandbox primitive from a shared dataset to per-ticket workspaces created on demand via `Groups - Create Group` + `Imports - Post Import`.

**v2d — Visual regression harness.** Use `DAX Studio` or the XMLA endpoint to execute the query plans behind affected visuals and compare to a prior snapshot. Doesn't render visuals but catches DAX-level breakage. Narrower than "does it look right" but broader than "does it refresh."

### Unknowns that would change the recommendation

- **Premium / PPU / Fabric capacity SKU.** If GEP is on Pro only, XMLA write is blocked → Level 2 is infeasible → fall back to Level 1 (generate scripts, Paul runs manually in Tabular Editor with interactive connection). `XMLA write confirmed available` (from the boot prompt) implies Premium-plus — but confirm the SKU in §5.
- **Parameterised PBIX connection fields.** Resolution partially known — Data Source Settings show `og35375.canada-central.azure.snowflakecomputing.com;COMPUTE_WH` directly. Could be a parameter value or hardcoded; confirm via `Manage Parameters` in Desktop before Tranche C (see §5 Q4a). If hardcoded, need TE CLI rewrite of `dataSource.connectionDetails` at apply time. Still Level 2, adds ~20 lines.
- ~~**SPN permissions.**~~ **N/A** — auth changed to user OAuth (§5a); no SPN to permission.
- ~~**SQL Server intermediate layer.**~~ **Resolved 2026-04-21** — no SQL Server intermediate in the GEP PBI data path. See §5 Q4. Wiki pages correcting this added to Tranche E.3.
- **Deployment Pipelines availability.** If already configured, v2a becomes Level 3 v1 instead of v2 stretch.

---

## 5. Open questions for Paul — status after 2026-04-21 Q&A

Four of the nine were answered in the planning session (noted inline below). One
blocker remains (Q4). The shaping questions (6–9) stay open but don't block
Tranche A or B.

1. ✅ **Premium / PPU / Fabric SKU?** — Paul: "I don't know, I think yes." Confirmed-by-implication (XMLA write was confirmed available in the boot prompt, which only exists on Premium/PPU/Fabric). **Action:** Tranche A.1 becomes a 30-second confirmation step in the PBI admin portal rather than a decision.
2. ✅ **Tabular Editor install.** — Paul: "we need to install this, I don't have it." **Action:** Tranche A.2 is an explicit install step; default to **Tabular Editor 2** (free, .NET Framework 4.7.2+). Download from [tabulareditor.com/te2](https://tabulareditor.com/te2) or GitHub releases. Default install path `C:\Program Files (x86)\Tabular Editor\TabularEditor.exe`. No need to evaluate TE 3 for v1.
3. ✅ **Auth — SPN or user OAuth?** — Paul: "I have an AzureAD licence for power bi." Interpreted as: user OAuth via Paul's own Azure AD identity, no separate Service Principal. **Action:** auth path revised below (§5a). Much simpler — no tenant admin work required, no secret to manage. Trade-off: tokens expire ~1h, need periodic re-acquire.
4. ✅ **Current PBIX connection shape.** — Paul checked Data Source Settings on the open PBIX (2026-04-21). Two sources shown: `https://aldctestfnapcore1c01.azurewebsites.net/v1/report/describe` (core_api, for glossary/metadata per `power-bi.md` template conventions) and `og35375.canada-central.azure.snowflakecomputing.com;COMPUTE_WH` (direct Snowflake). **No SQL Server intermediate in the PBI data path.** Interpretation A is correct — the SSMS wiki page and `power-bi.md` data-flow diagram both describe a "SQL Server intermediate DB" that does not actually exist in the GEP PBI flow; those pages are wrong and need correcting (added to Tranche E).
   - "SSMS" in Paul's earlier description is SSMS-as-XMLA-client into the PBI tabular model (Process Partitions on tabular-model partitions), not SSMS into a separate SQL Server DB.
   - **Action:** plan's rebind approach is unchanged — `Update Parameters` flips the Snowflake DB name, PBI imports from Snowflake as before.
4a. ✅ **PBIX parameterisation status — resolved 2026-04-21 with a gap to close.** Paul listed the parameters in the current PBIX:
   - `CORE_API_REPORT_ID` = `25ca82be-ae62-44f7-aff8-b4dcb3d2009b`
   - `CORE_API_ACCOUNT_ID` = `da8904db`
   - `CORE_API_URL` = `https://aldctestfnapcore1c01.azurewebsites.net`
   - `CORE_API_CLIENT_TOKEN` (present)
   - `SNOWFLAKE_HOST` = `og35375.canada-central.azure.snowflakecomputing.com`
   - `SNOWFLAKE_COMPUTE` = `COMPUTE_WH`

   **Gap:** no `SNOWFLAKE_DATABASE` or `SNOWFLAKE_ROLE` parameters. The current DB (`PROD_DG1_GEP` in prod; `TEST_DG1_GEP` in the TEST-pointed working copy) must be hardcoded in individual table M queries, or defaulted at credential-set time. Without `SNOWFLAKE_DATABASE`, per-ticket sandbox DB rebinding via REST `Update Parameters` cannot work — the main mechanism of Sub-step 1b is broken.

   **Two recovery paths:**
   - **Path 1 (recommended, v1 scope) — one-time PBIX parameterisation.** Paul adds `SNOWFLAKE_DATABASE` and `SNOWFLAKE_ROLE` parameters to the production PBIX, rewrites M queries to reference them, saves a new dated `.pbix` in `repos/power_bi/custom/GEP/`, publishes to the Production workspace. ~15 minutes of PBI Desktop work. After this, Tranche C works unchanged.
   - **Path 2 (scope-down) — PBI sandbox always reads TEST data.** Works for measure-only tickets; fails for structural changes (new columns, new tables). Recent GEP tickets GP-200, GP-203, GP-204, GP-208 are all structural → this limit would bite immediately. Not recommended.

   **Action:** Path 1 becomes Tranche A.0.6 (see §6.1). Everything else in the plan unchanged. The seed script (A.1) checks for `SNOWFLAKE_DATABASE` parameter presence via `GET /datasets/{id}/parameters` and errors out with a clear message if missing, so we cannot accidentally skip A.0.6.
4b. ✅ **PBIX per environment — resolved 2026-04-21.** Paul confirmed: "we need to point it to the prod host for the Production Model, this is the TEST PBI Data Model." There are **two separate `.pbix` files**, one per environment. TEST PBI Data Model has `SNOWFLAKE_HOST = og35375...` (non-prod), Production Model has `SNOWFLAKE_HOST = wj66376...` (prod). Env swap is done by maintaining two files, not by flipping a parameter on one file.

   **Implication for plan:** makes A.0.6 much lighter — only the **sandbox seed** needs parameterisation (to allow per-ticket DB rebinding). Live TEST and Production PBIX files stay untouched. Tranches C and D apply the model script to the TEST and Production datasets respectively without any datasource rebinding — each dataset's hardcoded DB (inherited from its source PBIX) stays as-is. The model script changes metadata (measures, relationships, calc columns), not datasource config. Zero risk to actively-deployed models from the parameterisation work.
5. ✅ **Sandbox workspace seed — scripted.** — Paul: "I think it should be scripted." **Action:** Tranche A.4–A.5 become code (a `GEP/scripts/pbi_seed_sandbox.py` helper, see §6.1 below) rather than a manual runbook. Idempotent so it can also be used to reset the sandbox later.
6. 🟡 **Deployment Pipelines availability.** Not answered; still shaping. Only matters for v2a (Level 3). Don't block v1 on it.
7. 🟡 **TMDL vs BIM.** Not answered; v2 only.
8. 🟡 **Config location.** Not explicitly answered, but Paul opened `C:\Users\PaulRussell\repos\clients\GEP\scripts\.env` in his IDE while answering these questions — a strong signal that `pbi_config` env vars should live alongside the existing Snowflake env vars in `GEP/scripts/.env`. **Tentative decision:** use `GEP/scripts/.env` for secrets (nothing highly-secret remains now that SPN is out — just workspace/dataset IDs) and keep workspace/dataset/param names in a new `GEP/scripts/pbi_config.yaml` (gitignored) to avoid polluting `.env` with structured config. Confirm before Tranche B.
9. 🟡 **visual_required edge cases.** Not answered; shaping only. Will refine the prompt wording during Tranche C based on first real use.

### 5a. Revised auth plan (replaces prior SPN-based approach)

User OAuth via Azure CLI bearer token is the v1 auth path:

```
# One-time (per machine):
az login
# (or `az login --use-device-code` if Paul's browser can't open interactively)

# Per skill session (skill invokes, not Paul):
az account get-access-token \
  --resource https://analysis.windows.net/powerbi/api \
  --query accessToken -o tsv
# → JWT bearer token, ~1h lifetime
```

Both TE CLI and PBI REST reuse this one token:

- **TE CLI connection string:**
  `Provider=MSOLAP;Data Source=powerbi://api.powerbi.com/v1.0/myorg/<workspace>;Initial Catalog=<dataset>;User ID=AzureAD;Password=<bearer_token>`
- **PBI REST:**
  `Authorization: Bearer <bearer_token>`

**Token caching:** skill caches the token in memory for the session; on any 401, re-runs `az account get-access-token` and retries once. If that fails, prints `⚠️ Not logged in — run 'az login' and retry` and aborts. No secrets land on disk.

**Prerequisites:** Azure CLI installed (`az --version`). If not installed, Tranche A.0.5 step adds the install.

**Workspace permissions needed:** Paul's user account must be Member or Admin on the sandbox, test, and prod workspaces, and the workspace must allow XMLA write (capacity setting — a one-click toggle by the capacity admin). Since Paul already uses the prod workspace, test membership is assumed; sandbox is fresh so membership is auto-granted by the seed script (Paul will be the workspace creator).

---

## 6. Implementation order

Build in three tranches; each independently shippable.

### 6.1 Tranche A — one-time setup (some manual, mostly scripted per Paul's answer to Q5.5)

> **Status (2026-04-21): ✅ COMPLETE.** Sandbox workspace id `8545f3cb-4e2d-4985-bf31-79066248c9be`, dataset id `fb41970d-2beb-4ed9-9f82-35c6439b35ea`. Azure CLI 2.85.0 + Tabular Editor 2.28.0 installed. XMLA Read/Write smoke-tested via TE against the sandbox dataset — quiet save succeeded. Seed script `pbi_seed_sandbox.py` shipped with two Windows Python fixes added during live run: `shutil.which("az")` for PATHEXT resolution of `az.cmd`, plus a fallback to the default install location (`C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd`) for stale-PATH terminals. `pip install ruamel.yaml` is optional — without it, PyYAML strips config comments on re-write (one-time cosmetic loss; schema preserved in `pbi_config.example.yaml`).
>
> **A.0.6 executed approach (simpler than planned):** the live GEP PBIX has a query called `PARAM_SHORT_CODE` that dynamically resolves the Snowflake DB name via core_api. Rather than rewriting every table query's `Source` step, the live run rewired `PARAM_SHORT_CODE` to return the new `SNOWFLAKE_DATABASE` parameter (one-line M), which kept all 15 downstream table queries unchanged. Only 2 additional M edits were needed for the `Campaign` and `Platform` queries (hardcoded host/DB literals). Total: 3 edits instead of 17. Documented for future reference in the tracker session log.

Revised after Paul's Q&A. SPN is out (Q5.3 → user OAuth); seed is scripted (Q5.5 → `pbi_seed_sandbox.py`).

**A.0 — Prerequisites (Paul, ~10 minutes)**

A.0.1. Confirm Premium/PPU/Fabric capacity SKU in the Power BI admin portal (capacity settings → XMLA endpoint = Read Write).
A.0.2. Install Azure CLI if not present: `winget install Microsoft.AzureCLI` (or download from Microsoft). Run `az login` once.
A.0.3. Download and install **Tabular Editor 2** from tabulareditor.com/te2 (free, MSI installer, ~15 MB). Default path `C:\Program Files (x86)\Tabular Editor\TabularEditor.exe`.
A.0.4. Create the `GEP Sandbox Models` workspace in Power BI Service (Workspaces → New workspace → name = `GEP Sandbox Models`, assign to the same capacity as GEP Test Models). Record the workspace GUID from the URL.
A.0.5. Download the current production `.pbix` to `GEP/scripts/_pbi_seed/GEP_Sandbox_Template.pbix` (one-time, gitignored — binary artefacts stay in `repos/power_bi`, not `clients`).

A.0.6. **One-time seed PBIX parameterisation (~15 min, PBI Desktop work).** Only the sandbox seed file gets parameterised — live TEST and Production PBIX files stay untouched. The seed starts from a copy of the TEST PBI Data Model (not Production) because TEST's `SNOWFLAKE_HOST` already points at `og35375` which is also where sandbox Snowflake DBs live. Steps:
   1. Copy the TEST PBI Data Model's `.pbix` to `GEP/scripts/_pbi_seed/GEP_Sandbox_Template.pbix` (from A.0.5). **Do not modify the live TEST file.**
   2. Open the copy (`GEP_Sandbox_Template.pbix`) in Power BI Desktop.
   3. Home → Transform data → Manage Parameters → New Parameter:
      - `SNOWFLAKE_DATABASE` (Text, current value `TEST_DG1_GEP` — the seed defaults to TEST data until a sandbox run rebinds it)
      - `SNOWFLAKE_ROLE` (Text, current value `SYSADMIN` — confirmed 2026-04-21 as the role Paul uses in TEST. SYSADMIN has USAGE on zero-copy cloned sandbox DBs by default, so the same role value works for sandbox rebinding without further grants)
   4. For every query that references Snowflake (typically starting `Source = Snowflake.Databases(SNOWFLAKE_HOST, SNOWFLAKE_COMPUTE){[Name="TEST_DG1_GEP"]}[Data]`), replace the hardcoded DB name with the parameter: `Source = Snowflake.Databases(SNOWFLAKE_HOST, SNOWFLAKE_COMPUTE, [Role=SNOWFLAKE_ROLE]){[Name=SNOWFLAKE_DATABASE]}[Data]`.
   5. Save the `.pbix`. **Do NOT publish** — the seed script (A.1) handles the upload to the `GEP Sandbox Models` workspace.
   6. Verify in Desktop that refresh still works (connects to TEST, pulls data) before handing off to the seed script.

   **Zero risk to actively-deployed models** — this is a brand-new seed file, the live TEST and Production PBIX files are not touched.

   This is a one-time setup; no further PBIX parameterisation work is required in v1.

**A.1 — Scripted seed (new deliverable: `GEP/scripts/pbi_seed_sandbox.py`)**

Idempotent Python script that takes `--pbix <path>` + `--workspace-id <guid>` and:
1. Acquires bearer token via `az account get-access-token`.
2. Uploads the `.pbix` to the workspace via `POST /v1.0/myorg/groups/{workspace_id}/imports?datasetDisplayName=GEP_Sandbox_Current&nameConflict=CreateOrOverwrite`.
3. Polls `GET /imports/{import_id}` until `importState == "Succeeded"`.
4. Extracts the created dataset ID.
5. **Verify required parameters exist** via `GET /datasets/{id}/parameters`. Required: `SNOWFLAKE_HOST`, `SNOWFLAKE_COMPUTE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_ROLE`. If any missing:
   - Print: "Missing PBIX parameters: <list>. Complete Tranche A.0.6 (one-time parameterisation) before running the seed."
   - Exit non-zero.
6. Write discovered IDs (`sandbox_workspace_id`, `sandbox_dataset_id`) to `GEP/scripts/pbi_config.yaml`.

**A.2 — Config file (new deliverable: `GEP/scripts/pbi_config.yaml`)**

Gitignored. Populated partly by the seed script, partly by Paul:

```yaml
tenant: "aldc.onmicrosoft.com"  # or whatever GEP's PBI tenant is

tabular_editor_path: "C:\\Program Files (x86)\\Tabular Editor\\TabularEditor.exe"

workspaces:
  sandbox:
    id: "<filled by pbi_seed_sandbox.py>"
    name: "GEP Sandbox Models"
    dataset_id: "<filled by pbi_seed_sandbox.py>"
    dataset_name: "GEP_Sandbox_Current"
  test:
    id: "<Paul fills — from Power BI Service URL of GEP Test Models>"
    name: "GEP Test Models"
    dataset_id: "<Paul fills — from dataset settings page URL>"
    dataset_name: "<Paul fills — actual semantic model name>"
  prod:
    id: "<Paul fills>"
    name: "<Paul fills>"
    dataset_id: "<Paul fills>"
    dataset_name: "<Paul fills>"

parameter_names:          # names of PBIX parameters for connection rebinding
  database: "SnowflakeDatabase"
  warehouse: "SnowflakeWarehouse"
  role: "SnowflakeRole"
```

No secrets in this file — the bearer token comes from `az` at runtime.

**A.3 — Smoke test (Paul runs, ~5 minutes)**

A.3.1. `az login` (if not already).
A.3.2. `python GEP/scripts/pbi_seed_sandbox.py --pbix <path> --workspace-id <guid>` — verify sandbox dataset is created and `pbi_config.yaml` is populated.
A.3.3. Launch Tabular Editor 2 → File → Open → From DB... → paste the XMLA endpoint `powerbi://api.powerbi.com/v1.0/myorg/GEP Sandbox Models` → authenticate interactively → confirm the model opens and shows the expected tables.
A.3.4. Make a trivial change (e.g. add and immediately remove a description on any measure), save, confirm XMLA write works end-to-end.

**Stops here if A.0.1 (capacity) or A.3.4 (XMLA write) fails.** v1 falls back to Level 1 (generate scripts, Paul runs manually with interactive auth).

### 6.2 Tranche B — skill primitives (one PR, no behaviour change yet)

> **Status (2026-04-21): ✅ COMPLETE.** Sonnet subagent wrote §G/§H/§I to `.claude/commands/gep-feature.md`, added Phase 6 artefact-schema fields, and added rules 9–11 — all per plan spec verbatim. Behaviour unchanged. Ready to be called by Tranche C.

B.1. Add `§G — Tabular Editor CLI helper` to `## MCP setup` section of `gep-feature.md`.
B.2. Add `§H — PBI REST helper` to `## MCP setup` section.
B.3. Add Phase 6 fields to artefact schema block (`visual_required`, `script_path`, `script_hash`, `sandbox_validated`, `sandbox_applied_at`, `sandbox_refresh_id`, `test_applied_at`, `test_refresh_id`, `prod_applied_at`, `prod_refresh_id`, `findings`).
B.4. Add `pbi_config` to the skill config section (or a new config file, per Q5.8).
B.5. Add rules 9–11 to `## Rules`.

**No behaviour change yet** — these are helpers referenced by later steps. Commit, validate against existing ticket flow (should be a no-op).

### 6.3 Tranche C — Sub-step 1b and TEST tail (main behaviour change)

C.1. Extend the `scoped` stage PBI question to capture `visual_required` (§3.9).
C.2. Insert Sub-step 1b into the `implementing` stage (§3.3).
C.3. Extend Sub-step 2 TEST deploy with the TE CLI apply + refresh tail (§3.5).
C.4. Refine `test-deployed` step 3 to note that refresh is already done (§3.6).

Dry-run: use the next low-risk GEP ticket that has a simple PBI model change (ideally a single measure addition). Run end-to-end. Surface gaps to the tracker as Phase 6 hardening items, same as the Phase 4 dry-run cycle.

### 6.4 Tranche D — `prod-deployed` conditional auto-apply

D.1. Extend `prod-deployed` PBI publish gate with the `visual_required` branch (§3.7).

Deliberately last because it writes to production. Ship after Tranches B + C have been dogfooded on TEST through at least one ticket.

### 6.5 Tranche E — docs and wiki

E.1. New wiki page `concepts/patterns/pbi-xmla-automation.md` (analogous to `sandbox-feature-delivery.md`).
E.2. Update `entities/tools/power-bi.md` with an "XMLA automation" section linking to the new pattern page. **Also correct the data-flow section** — the current page says "data usually passes through a SQL Server layer"; Paul's 2026-04-21 Data Source check confirms GEP connects directly Snowflake → PBI (+ core_api for glossary metadata). Remove the `Snowflake → SQL Server → Power BI` diagram or reframe it as "legacy/alternate path used rarely."
E.3. **Correct `entities/tools/SSMS.md`** — the §Where SSMS fits in the pipeline section describes an intermediate SQL Server DB that does not exist in the GEP path. Rewrite as "SSMS is used as a client into the Power BI tabular model over XMLA" (which is what the §Partition Refresh section actually documents). Contradicts Steven's KT note but matches current observed reality; flag as correction per wiki rule #6.
E.4. Update `processes/deployment/gep-snowflake-pbi-deployment.md` to note that PBI model changes for the GEP workspace are now XMLA-scripted.
E.5. Update `workflow-automation.md` §2.4 and §3.6 to reflect that the PBI manual-half has been reduced to visual-only changes.
E.6. Close out the "Multi-feature conflict in TEST / PBI" blocker with a link to `pbi-xmla-automation.md`.

---

## 7. What this plan does NOT change

- **Visual / report-layout edits** (pages, visuals, bookmarks, slicer state, colours) remain manual via Power BI Desktop and PBIX publish. No public API exists to automate them. The `visual_required` flag surfaces the split.
- **Deployment Pipelines setup** — out of scope. If v2a is pursued, a separate workstream.
- **Fusion92 or other clients** — Phase 6 is GEP-specific. The pattern (TE CLI + PBI REST + sandbox workspace) generalises cleanly, but that's a later multi-client refactor.
- **PBI refresh *monitoring*** — this plan triggers and polls; it does not add long-running refresh-failure alerting. That's v2 ops.
- **pbi-tools adoption** — this plan does not install or use pbi-tools in v1. v2b introduces it for TMDL extraction.

---

## See Also

- [[client-workflow-automation]] — workstream tracker
- [[workflow-automation]] — parent design doc (§3.2 and §3.6 on PBI constraints; Phase 6 resolves the manual-half identified there)
- [[entities/tools/power-bi|Power BI]] — tool reference; will gain an XMLA automation section
- [[gep-snowflake-pbi-deployment]] — current runbook; will be annotated once v1 ships
- [[sandbox-feature-delivery]] — the Snowflake sandbox pattern this plan mirrors at the PBI layer
- [[GEP]] — client entity
