---
tags: [concept, pattern, power-bi, xmla, tom, automation, gep]
aliases: [PBI XMLA automation, TOM model automation, pbi_model_apply pattern]
sources: [entities/projects/workflow-automation.md, processes/distributed-workflow/active/phase6-pbi-automation-plan.md, processes/deployment/pbi-xmla-model-changes.md, GP-208 validation session 2026-04-24]
created: 2026-04-24
updated: 2026-04-25
---

# PBI XMLA Model Automation

A pattern for making programmatic, idempotent metadata changes to a Power BI semantic model from code, validating them against a sandbox dataset before touching client-facing environments. Replaces the manual "open PBI Desktop → edit → republish" loop for metadata-only changes (tables, columns, relationships, measures, calculated columns, format strings).

> **Origin**: designed as Phase 6 of the GEP workflow automation ([[phase6-pbi-automation-plan]]), validated end-to-end against GP-208 on 2026-04-24. Extracted here as a reusable pattern.

> **Scope**: metadata only. Visual layer (pages, visuals, bookmarks, slicer state, colours) is not automatable via XMLA — Microsoft has no public API. Visual changes continue to require PBI Desktop.

---

## The Problem

Hand-maintaining a Power BI semantic model is slow, un-reviewable, and untested:

- Engineer opens the `.pbix` in PBI Desktop, edits tables/relationships, saves, publishes to the Service.
- No Git diff — changes live only in the binary `.pbix`.
- No sandbox — the first place changes are visible is the client-facing TEST workspace (shared with UAT).
- No automation hook — PR / CI cannot apply or validate model changes.

For GEP's scripted-deploy flow, this left the PBI half as the last manual stage. A broken PBI model edit could reach the shared TEST workspace while a client was mid-UAT on an unrelated feature.

---

## The Pattern

Three primitives working together:

1. **`pbi_model_apply.exe`** — .NET 8 console wrapper around the TOM library. Runs TE3-compatible C# scripts via Roslyn CSharpScript over an XMLA connection. MSAL device-code auth (cached ~1h). Replaces TE3 CLI (which hangs under any subprocess — see [[pbi-xmla-model-changes]] § TE3 CLI Findings).
2. **`pbi_generate_columns.py`** — emits TOM `DataColumn` definitions from Snowflake `INFORMATION_SCHEMA.COLUMNS`. TOM does **not** auto-discover column schema from M queries (only PBI Desktop does); columns must be predefined in metadata before `SaveChanges()`. Output is a C# fragment that a per-ticket script `#load`s.
3. **Persistent sandbox dataset** — one workspace (`GEP Sandbox Models`), one dataset (`GEP_Sandbox_Current`), rebound at runtime to the per-ticket Snowflake sandbox DB via REST `Update Parameters`. No per-ticket PBI workspace provisioning.

```
Snowflake sandbox (SANDBOX_DG1_GEP_<ticket>)
        │
        ├── INFORMATION_SCHEMA.COLUMNS ───► pbi_generate_columns.py
        │                                         ↓ (emits)
        │                                   pbi_model_columns.cs  (DataColumn fragment)
        │                                         ↓ (#load)
        └── M-query sources ─────────────► pbi_model_script.cs  (per-ticket, hand-authored)
                                                  ↓ (CSharpScript)
                                           pbi_model_apply.exe  → XMLA write
                                                  ↓
                                           Sandbox dataset (GEP_Sandbox_Current)
                                                  ↓ (REST UpdateParameters → sandbox DB)
                                                  ↓ (REST POST /refreshes + poll)
                                           Columns populated; DAX verifies rows.
```

---

## Required Pieces

### 1. Wrapper (`GEP/scripts/pbi_model_apply/`)

A .NET 8 console project. Dependencies:

- `Microsoft.AnalysisServices.NetCore.retail.amd64` (TOM)
- `Microsoft.CodeAnalysis.CSharp.Scripting` (Roslyn)
- `Microsoft.Identity.Client` + `Microsoft.Identity.Client.Extensions.Msal` (device-code auth + disk cache)

Key design decisions:
- **Auth**: MSAL device-code with the PBI public client ID `ea0616ba-638b-4df5-95b9-636659ae5121`. Azure CLI tokens (`az account get-access-token`) are **rejected** by the PBI XMLA endpoint — their `appid=04b07795-...` is not an approved XMLA client.
- **Script API**: TE3-compatible via extension methods in `TabularExtensions.cs` (`Model.AddTable`, `Model.AddRelationship`, `partition.SetExpression`). One syntax delta from TE3 GUI: use `.SetExpression("...")` not `.Expression = "..."` because C# has no extension properties.
- **Partition Mode**: `AddTable()` explicitly sets `Mode = ModeType.Import`. `ModeType.Default` refreshes to Completed but leaves tables empty.
- **`#load` support**: `ScriptOptions` uses `SourceFileResolver` scoped to the script's directory. Per-ticket scripts can include generator-emitted fragments.
- **Exit codes**: discrete (0 success, 1 script runtime, 2 auth, 3 connection, 4 compile, 5 model locked, 6 invalid args, 99 unexpected). Callers react distinctly.

### 2. Column generator (`GEP/scripts/pbi_generate_columns.py`)

Mirrors `deploy.py` conventions (`.env` loader, Snowflake account mapping by env). Usage:

```
python pbi_generate_columns.py \
  --env sandbox --ticket GP-208 \
  --tables INVENTORY_FCT_BALANCE,EXTRACT_INVENTORY_CURRENT \
  --out GEP/tickets/GP-208/pbi_model_columns.cs
```

Emits one `void AddColumns_<TABLE>(Table t)` function per target table, with `DataColumn` entries mapped from Snowflake types via the table in [[pbi-xmla-model-changes]] § TOM Schema-Discovery Constraint.

### 3. Per-ticket script (`GEP/tickets/<ticket>/pbi_model_script.cs`)

```csharp
#load "pbi_model_columns.cs"   // generator output; keeps schema separate from logic

string InventoryFctM(string name, string kind = "Table") =>
    "let " +
    "  Source = Snowflake.Databases(SNOWFLAKE_HOST,SNOWFLAKE_COMPUTE)," +
    "  Tenant_Database = Source{[Name=PARAM_SHORT_CODE,Kind=\"Database\"]}[Data]," +
    "  WAREHOUSE_Schema = Tenant_Database{[Name=\"WAREHOUSE\",Kind=\"Schema\"]}[Data]," +
    $"  RESULTANT_VIEW = WAREHOUSE_Schema{{[Name=\"{name}\",Kind=\"{kind}\"]}}[Data] " +
    "in RESULTANT_VIEW";

// Drop-if-exists so reruns are idempotent against any starting state.
if (Model.Tables.Contains("INVENTORY_FCT_BALANCE"))
    Model.Tables.Remove(Model.Tables["INVENTORY_FCT_BALANCE"]);

var t = Model.AddTable("INVENTORY_FCT_BALANCE");
AddColumns_INVENTORY_FCT_BALANCE(t);                              // ← from generator
t.Partitions[0].SetExpression(InventoryFctM("INVENTORY_FCT_BALANCE", "Table"));

Model.SaveChanges();
```

### 4. Workflow glue

The `/gep-feature` skill's Sub-step 1b invokes:
1. Generator (if new tables) → `pbi_model_columns.cs`.
2. `pbi_model_apply.exe --dry-run` → Roslyn compile check (catches script errors before XMLA connection).
3. REST `UpdateParameters` → rebind sandbox dataset to per-ticket Snowflake DB.
4. `pbi_model_apply.exe` → applies model metadata.
5. REST `POST /refreshes` + poll.
6. **Validation links emitted** (sandbox only, 2026-04-25): after §G exit-0 and §H poll Completed, skill prints:
   - Workspace: `https://app.powerbi.com/groups/<workspace_id>/list`
   - Dataset: `https://app.powerbi.com/groups/<workspace_id>/datasets/<dataset_id>/details`
   - Per-table refresh status from `objects[]` in the REST response.
7. Manual visual check → sets `sandbox_validated: true` in artifact.
8. On sandbox pass: same script re-applied to the client-facing TEST workspace dataset.

See [[phase6-pbi-automation-plan]] §3.3 for the full pseudocode and gate conditions.

---

## What This Pattern Does Not Cover

- **Visual / report-layout edits.** Pages, visuals, bookmarks, slicer state, colours — no public API. `changes.pbi_model.visual_required = true` in the artifact keeps these on the manual PBI Desktop republish path.
- **Schema inference from M.** TOM doesn't do it. Hand-define columns (tedious) or use `pbi_generate_columns.py` (recommended). Regenerate when the Snowflake schema changes.
- **Workspace provisioning at scale.** A single persistent sandbox workspace is the design choice, not per-ticket clones. See [[phase6-pbi-automation-plan]] §2 for the rejected alternatives.
- **Credential rotation.** PBI dataset credentials are set once at seed time; this pattern assumes they remain valid. See [[powerbi-secret-refresh]].

---

## Applying to a New Client

Prerequisites (one-time, per-client):
1. PBI capacity supports XMLA write (Premium / PPU / Fabric).
2. Tabular Editor **not required** — `pbi_model_apply` replaces TE3 CLI.
3. Azure CLI installed and `az login` completed (for REST calls — `az` tokens do work for REST, only XMLA rejects them).
4. A persistent sandbox workspace exists (created manually in PBI Service; assign to the same capacity as the client-facing TEST workspace).
5. A seed `.pbix` uploaded to the sandbox workspace with `SNOWFLAKE_DATABASE` + `SNOWFLAKE_ROLE` parameters added (so REST `UpdateParameters` can rebind per ticket). See [[phase6-pbi-automation-plan]] §6.1.
6. `pbi_config.yaml` populated with workspace / dataset IDs per env.

Per-ticket workflow:
1. Deploy SQL to the Snowflake sandbox DB (via `deploy.py --env sandbox`).
2. Run `pbi_generate_columns.py` for any new tables.
3. Author or extend `pbi_model_script.cs` in the ticket folder.
4. Run `pbi_model_apply.exe` against sandbox; trigger refresh; verify rows via DAX.
5. Promote the same script to the client-facing TEST dataset.
6. For metadata-only changes: optionally auto-apply to prod (Tranche D of [[phase6-pbi-automation-plan]]).

---

## Relationship to the Snowflake Sandbox Pattern

| Aspect | Snowflake (see [[sandbox-feature-delivery]]) | PBI (this pattern) |
|---|---|---|
| Granularity | Per-ticket DB clone | Single persistent dataset, rebound per ticket |
| Created | On-demand at deploy time | One-time seed, reused |
| Torn down | Prompted after sandbox validate | Not torn down — reset by next ticket's script |
| Isolation from shared TEST | Full (separate DB) | Full (separate workspace — client cannot see sandbox) |
| Write path | SQL via `snowflake-connector-python` | C# scripts via `pbi_model_apply.exe` over XMLA |
| Refresh trigger | `EXECUTE TASK` + poll `TASK_HISTORY` | REST `POST /refreshes` + poll `GET /refreshes/{id}` |

The shape matches deliberately — the `/gep-feature` skill's Sub-step 1 (Snowflake) and Sub-step 1b (PBI) mirror each other.

---

## Related Tooling

- `GEP/scripts/pbi_model_apply/` — the wrapper (source in this repo; build with `dotnet build -c Release`).
- `GEP/scripts/pbi_generate_columns.py` — column generator.
- `GEP/scripts/pbi_seed_sandbox.py` — one-time sandbox workspace + dataset seed (see [[phase6-pbi-automation-plan]] §6.1).
- `GEP/scripts/pbi_scan.py` — read-only model scanner (REST DAX fallback; TE3 path disabled until a headless scanner exists).

---

## See Also

- [[pbi-xmla-model-changes]] — hands-on reference: TOM schema-discovery constraint, Mode gotcha, drop-if-exists pattern, Snowflake→TOM type map
- [[pbi-model-apply-wrapper]] — implementation plan + design rationale for the wrapper
- [[phase6-pbi-automation-plan]] — full Phase 6 plan (sandbox isolation model, workflow integration, §G/§H/§I helpers)
- [[sandbox-feature-delivery]] — the Snowflake sandbox pattern this mirrors
- [[workflow-automation]] — parent design doc
- [[gep-snowflake-pbi-deployment]] — runbook; annotated with the new XMLA path
- [[entities/tools/power-bi|Power BI]] — tool reference
- [[GP-208]] — first ticket validated end-to-end with this pattern (2026-04-24)
