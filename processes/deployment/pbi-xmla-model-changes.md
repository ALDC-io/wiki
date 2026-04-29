---
tags: [process, pbi, xmla, tabular-editor, automation, gep, tom]
aliases: [PBI XMLA model changes, Tabular Editor CLI, TE3 headless, TOM schema discovery]
sources: [GP-208 Sub-step 1b sessions 2026-04-22/23 and 2026-04-24]
created: 2026-04-23
updated: 2026-04-25
---

# PBI Model Changes via XMLA / Tabular Editor

How to apply metadata-only Power BI model changes (new tables, measures, relationships,
column formatting) programmatically via XMLA. The project moved from Tabular Editor 3 (TE3)
CLI to a purpose-built .NET wrapper (`pbi_model_apply`, see [[pbi-model-apply-wrapper]])
after the TE3 CLI path was proven unrunnable from subprocess contexts.

## Current Status (2026-04-24)

Two distinct findings now drive the automation design:

1. **TE3 CLI headless mode does not work from subprocess context** (2026-04-22/23). Resolved
   by replacing TE3 CLI with the `pbi_model_apply` .NET 8 wrapper (see
   [[pbi-model-apply-wrapper]] and the session log in [[client-workflow-automation]]).
   Wrapper uses TOM + Roslyn CSharpScript directly, no WebView2, no GUI subsystem.

2. **TOM does NOT auto-discover column schema from M queries** (2026-04-24, new root-cause
   finding). Tables created via `Model.AddTable()` + M partition + `Model.SaveChanges()` have
   no user columns. REST refresh reports `Completed` but tables remain empty and DAX queries
   fail with `AnalysisServicesErrorCode 3241804132`. Only Power BI Desktop's Power Query
   editor does M-query schema inference; TOM/XMLA/REST all assume predefined columns. See
   § TOM Schema-Discovery Constraint below. Chosen resolution: `pbi_generate_columns.py`
   (Option B; in progress 2026-04-24) generates `DataColumn` definitions from Snowflake
   `INFORMATION_SCHEMA.COLUMNS` and emits them as C# fragments to include in the model
   script before `AddTable()` calls.

## Architecture

Current (post 2026-04-24 pivot to `pbi_model_apply` wrapper):

```
gep-feature §G helper
  → pbi_model_apply.exe --script <.cs> --workspace <name> --dataset <name>
  → MSAL device-code auth (PBI public client ea0616ba-...; cached ~1h)
  → TOM + Microsoft.AnalysisServices.Tabular.Server.Connect(...)
  → CSharpScript.RunAsync(...) runs TE3-compatible script body
       (Model.AddTable / AddRelationship / SetExpression / SaveChanges)
  → Model.SaveChanges() persists metadata via XMLA
  → [separately] REST POST /refreshes + poll GET /refreshes/{id} to populate data
```

Legacy (deprecated; see § TE3 CLI Findings):

```
gep-feature §G helper (pre-2026-04-23)
  → TabularEditor3.exe /s <script.cs> /x <connection_string>     ← hangs from subprocess
  → XMLA endpoint
```

## TOM Schema-Discovery Constraint

**TOM does not auto-discover column schema from M queries.** This is the root cause of the
"table refreshes with no columns" symptom seen 2026-04-22/23 and re-confirmed 2026-04-24.

### What Power BI Desktop does that TOM does not

Power BI Desktop has two schema-discovery hooks that have no TOM equivalent:

1. **Power Query preview.** When you author an M query in the PQ editor, Desktop samples the
   data source (reads first rows) to infer column names and types, then persists those as
   `DataColumn` metadata on the table.
2. **Apply-time schema commit.** On "Apply", Desktop writes the discovered columns into the
   model metadata before the table is published to the server.

By the time Desktop publishes a PBIX, every table already has its columns defined. Refresh
then populates data into those pre-defined columns.

### What fails when TOM is the author

When tables are authored via TOM (wrapper, TE3 GUI scripting, SSMS scripting), the sequence is:

1. `new Table { Name = "X" }` — creates a Table with zero DataColumn objects.
2. `table.Partitions.Add(new Partition { Source = new MPartitionSource { Expression = "..." }})` —
   partition exists but has no schema.
3. `model.Tables.Add(table)` + `model.SaveChanges()` — metadata persisted with 0 user columns
   (only the auto-generated `RowNumberColumn`).
4. REST `POST /refreshes` with `type: Full` — partition "Completes" but has no column
   metadata to populate, so data lands nowhere.
5. DAX queries fail with `AnalysisServicesErrorCode 3241804132`:
   `Table '<X>' cannot be used in computations because it does not have any columns.`

### Workarounds that do NOT work (tested 2026-04-24)

- `partition.RequestRefresh(RefreshType.Full) + model.SaveChanges()` — does not populate columns.
- REST `type: Full` refresh — partition status `Completed`, table still schemaless.
- Multiple back-to-back refreshes — no change.
- `Mode=ModeType.Import` on the partition (required but insufficient — see next section for
  the Mode gotcha).

### Workaround that DOES work: predefine columns before SaveChanges

Explicitly define `DataColumn` objects on the table BEFORE `model.SaveChanges()`:

```csharp
var t = new Table { Name = "INVENTORY_FCT_BALANCE" };
t.Columns.Add(new DataColumn {
    Name = "PRODUCT_ID", SourceColumn = "PRODUCT_ID", DataType = DataType.String
});
t.Columns.Add(new DataColumn {
    Name = "BALANCE_DATE", SourceColumn = "BALANCE_DATE", DataType = DataType.DateTime
});
// ... one entry per expected column
t.Partitions.Add(new Partition {
    Name = "INVENTORY_FCT_BALANCE",
    Mode = ModeType.Import,
    Source = new MPartitionSource { Expression = "<M query>" }
});
model.Tables.Add(t);
model.SaveChanges();
// → REST refresh now populates data into the pre-defined columns.
```

### Chosen solution: `pbi_generate_columns.py`

Hand-authoring 20–50 `DataColumn` entries per new table is tedious and error-prone. The Phase 6
solution is a Python helper that queries Snowflake `INFORMATION_SCHEMA.COLUMNS` for the target
tables and emits the C# fragment automatically. Paste the fragment into the model script before
any `Model.AddTable(...)` call for that table.

Type mapping (Snowflake → TOM `DataType`):
| Snowflake data type | TOM `DataType` |
|---|---|
| `TEXT`, `VARCHAR`, `CHAR` | `String` |
| `NUMBER`, `DECIMAL`, `NUMERIC` (non-integer) | `Double` |
| `NUMBER(*, 0)`, `BIGINT`, `INT` | `Int64` |
| `FLOAT`, `DOUBLE`, `REAL` | `Double` |
| `BOOLEAN` | `Boolean` |
| `DATE`, `TIMESTAMP_*`, `DATETIME` | `DateTime` |
| `BINARY`, `VARBINARY` | `Binary` |

See [[client-workflow-automation]] 2026-04-24 session log for the full decision + rejected alternatives.

## Partition Mode gotcha (fixed in `pbi_model_apply`)

Separate from the schema-discovery issue, partitions created via TOM must explicitly set
`Mode = ModeType.Import`. `ModeType.Default` inherits from the model but does NOT trigger
schema-or-data processing correctly in REST-triggered refresh scenarios — partitions report
`Completed` with no effect. Working GEP tables all have `Mode = Import` explicitly.

Fixed in `pbi_model_apply/TabularExtensions.cs` 2026-04-24:
```csharp
var partition = new Partition
{
    Name = tableName,
    Mode = ModeType.Import,                                     // ← explicit, not Default
    Source = new MPartitionSource { Expression = "" }
};
```

## Drop-if-exists pattern for model scripts

TOM's `Table.Delete()` (TE3 GUI sugar) does NOT exist in raw TOM. Use the collection-level
`Remove`:

```csharp
if (Model.Tables.Contains("MY_TABLE"))
{
    Model.Tables.Remove(Model.Tables["MY_TABLE"]);
}
// ... then add fresh
```

This pattern is required any time a script re-runs against state where the target table may
already exist with stale / broken metadata (e.g. from a prior failed attempt). Applied to
`pbi_model_script.cs` for GP-208 on 2026-04-24.

### Critical addition — drop relationships before dropping the table (2026-04-25)

**TOM does NOT cascade-delete relationships when a table is removed.** If a
`SingleColumnRelationship` exists in `Model.Relationships` that references the table being
dropped, `Model.SaveChanges()` will fail with:

```
OperationException: Relationship points to deleted table '<table_name>'.
```

**Fix:** collect and remove all relationships referencing the table BEFORE calling
`Model.Tables.Remove()`:

```csharp
if (Model.Tables.Contains("MY_TABLE"))
{
    // Remove referencing relationships first — TOM does not cascade-delete them.
    var relsToRemove = new List<Relationship>();
    foreach (var rel in Model.Relationships)
    {
        var scr = rel as SingleColumnRelationship;
        if (scr != null && (scr.FromTable.Name == "MY_TABLE"
                          || scr.ToTable.Name == "MY_TABLE"))
            relsToRemove.Add(rel);
    }
    foreach (var rel in relsToRemove)
        Model.Relationships.Remove(rel);

    Model.Tables.Remove(Model.Tables["MY_TABLE"]);
}
// ... then add fresh table and re-create relationships as needed
```

This pattern is required in **every** drop-if-exists block for any table that may have
existing relationships. The two-list approach (collect first, then remove) is necessary
because modifying `Model.Relationships` while iterating over it causes a runtime error.

First surfaced during the Tranche F cold-run of `pbi_model_script.cs` (2026-04-25).
See [[client-workflow-automation]] 2026-04-25 session log for full details.



## TE3 CLI Findings (GP-208, 2026-04-22/23) — historical

> **Superseded 2026-04-24** by `pbi_model_apply` wrapper. Retained for context on why the wrapper
> was built. If you are looking for the current automation path, see § Architecture and
> [[pbi-model-apply-wrapper]].

### Problem: TE3 hangs when launched as a subprocess

TE3 (`TabularEditor3.exe`) is compiled as a **Windows GUI subsystem** app (PE subsystem 2).
GUI apps need a Windows message loop to process async events. When launched as a child
process of Claude Code (bash, PowerShell, Python subprocess), the message loop is never
pumped and TE3 hangs indefinitely — no timeout, no error, just silence.

**Confirmed behaviors:**
| Launch method | Result |
|---|---|
| `subprocess.run` (Python, 30–300s) | Timeout — Chrome/WebView2 unregister error on kill |
| `Start-Process -Wait` (PowerShell, 90s) | Timeout — same Chrome cleanup error |
| `& $te /s script /x conn` (Paul's terminal) | Returns immediately (async GUI launch), no output |
| TE3 GUI opened by Paul, C# script pasted manually | Works ✅ |

**Root cause:** TE3 uses WebView2 (Chromium-based browser) for AAD authentication and
other UI features. Even in CLI mode, this requires a desktop message loop to complete.
Running from any subprocess that doesn't drive a message pump causes a hang.

**Symptoms of the hang:**
- TE3 application log shows exactly 3 lines then stops:
  ```
  Preferences successfully loaded: UiPreferences.json
  Preferences successfully loaded: Preferences.json
  Preferences not found. Using defaults.
  ```
- No connection-phase log entries ever appear
- Process remains running until killed

### Workaround: Paul runs TE3 GUI manually

1. Open TE3: `C:\Program Files\Tabular Editor 3\TabularEditor3.exe`
2. File → Open from DB → `powerbi://api.powerbi.com/v1.0/myorg/<workspace>` → `<dataset>`
3. Authenticate in browser popup (AAD) — this caches the MSAL token
4. View → Scripting → paste script → Run (F5)
5. Save model: Ctrl+Alt+S
6. Close TE3 before triggering dataset refresh via REST API

**Important:** TE3 must be **closed** before triggering a Power BI dataset refresh.
An open TE3 session holds an exclusive XMLA write lock; the refresh will fail with an
auth/session error while it's open.

### Future fix directions

- **Option A:** Find a way to pump the Windows message loop from a subprocess (e.g.
  a thin .NET console wrapper that calls `Application.DoEvents()` in a loop)
- **Option B:** Use the Power BI REST API directly for model changes via XMLA HTTP
  (the XMLA endpoint for Premium supports SOAP over HTTP, bypassing the need for TE3)
- **Option C:** Write a dedicated console-subsystem wrapper around TE3's TOM libraries
  that does model changes without the GUI framework

See [[potential-tickets]] → "pbi_scan.py requires TE3" and related entries.

---

## GEP Model Conventions

### M Expression format (confirmed 2026-04-23 from Marketplace + Inventory Balance tables)

```m
let
    Source = Snowflake.Databases(SNOWFLAKE_HOST,SNOWFLAKE_COMPUTE),
    Tenant_Database = Source{[Name=PARAM_SHORT_CODE,Kind="Database"]}[Data],
    WAREHOUSE_Schema = Tenant_Database{[Name="WAREHOUSE",Kind="Schema"]}[Data],
    RESULTANT_VIEW = WAREHOUSE_Schema{[Name="<TABLE_NAME>",Kind="<Table|View>"]}[Data]
in
    RESULTANT_VIEW
```

**Key parameters:**
- `SNOWFLAKE_HOST`, `SNOWFLAKE_COMPUTE` — bare identifiers (no `#""` quotes)
- `PARAM_SHORT_CODE` — GEP model's per-environment database parameter. This is NOT the
  same as `SNOWFLAKE_DATABASE` (the REST API-updatable parameter). `PARAM_SHORT_CODE`
  is an internal M parameter. The two may be linked via a shared expression.
- `Kind="Table"` for physical tables (e.g. `INVENTORY_FCT_BALANCE` materialized by task chain)
- `Kind="View"` for views (e.g. `EXTRACT_INVENTORY_CURRENT` in WAREHOUSE schema)

**Common mistake:** Using `#"SNOWFLAKE_DATABASE"` as the database parameter instead of
`PARAM_SHORT_CODE` — this creates a new unrecognized data source connection that fails to
refresh despite the overall dataset refresh showing "Completed".

### Partition type

When adding tables via TE3 C# scripting (`Model.AddTable()`), the default partition type
may be DAX/Calculated rather than M Query. Pasting an M expression into a DAX partition
silently fails during refresh — the table "has no columns" after refresh completes.

**In TE3 GUI: always verify the partition type is "M Query" before pasting an M expression.**
If it shows DAX/Calculated, change the type first.

### Table naming convention

GEP PBI model uses **user-friendly Title Case display names**, not Snowflake identifiers:
- `Order Line` (not `ORDER_LINE`)
- `Inventory Balance` (not `INVENTORY_FCT_BALANCE`)
- `Marketplace` (not `SHARED_DIM_MARKETPLACE`)

When adding new tables via TE3, use the display name as the table name.
The M expression uses the Snowflake table name internally (in `RESULTANT_VIEW` step).

---

## GP-208 Sub-step 1b Status (as of 2026-04-24)

**Goal:** Add `INVENTORY_FCT_BALANCE` and `EXTRACT_INVENTORY_CURRENT` to the GEP Sandbox
Models dataset and verify they refresh from `SANDBOX_DG1_GEP_GP208.WAREHOUSE`.

**Completed:**
- ✅ Sandbox Snowflake deploy (deploy.py + validate.py: 9/9 checks, 16,736 rows)
- ✅ Sandbox dataset rebound to `SANDBOX_DG1_GEP_GP208` via REST API (`/parameters` verified 2026-04-24)
- ✅ `pbi_model_apply.exe` wrapper replaces TE3 CLI (committed 2026-04-24)
- ✅ `Mode=ModeType.Import` fix applied in `TabularExtensions.AddTable()` (committed 2026-04-24)
- ✅ Drop-if-exists hardening applied to `pbi_model_script.cs` (committed 2026-04-24)
- ✅ Root-cause identified for "no columns" — see § TOM Schema-Discovery Constraint above

**Completed (2026-04-24 session, end-to-end):**
- ✅ `GEP/scripts/pbi_generate_columns.py` — generator built; queries Snowflake
  `INFORMATION_SCHEMA.COLUMNS`, emits `void AddColumns_<TABLE>(Table t)` functions.
  27 cols for `INVENTORY_FCT_BALANCE`, 32 for `EXTRACT_INVENTORY_CURRENT`.
- ✅ `pbi_model_apply` wrapper — added `#load` directive support via
  `SourceFileResolver`; per-ticket scripts can include generator output cleanly.
- ✅ `pbi_model_script.cs` — wired to `#load "pbi_model_columns.cs"` + calls
  `AddColumns_*(t)` after each `Model.AddTable(...)`.
- ✅ End-to-end refresh + DAX verification:
  - `INVENTORY_FCT_BALANCE`: **16,736 rows** — exact match with Snowflake validate.
  - `EXTRACT_INVENTORY_CURRENT`: **16,560 rows** — extract inner-joins SHARED_DIM_PRODUCT.
  - PRODUCT_KEY relationship auto-created on same pass (columns exist at check time).
- ✅ `changes.pbi_model.sandbox_validated = true` set in GP-208 artifact, with
  `sandbox_applied_at: 2026-04-24T18:32:00Z`, `sandbox_refresh_id: ad9f66d5-...`,
  and per-table `sandbox_row_counts`.

**Historical — resolved / invalidated:**
- ~~"Partition type likely wrong (DAX instead of M Query)"~~ — never the problem; the wrapper
  always creates `MPartitionSource` partitions. Confirmed via `_diag_partitions.cs`.
- ~~"M expression has wrong Snowflake parameter"~~ — `PARAM_SHORT_CODE` is correct and has
  always been used (confirmed by reading `Inventory Balance` partition expression).
- ~~"Run script manually in TE3 GUI"~~ — superseded by `pbi_model_apply.exe` wrapper.

## See Also

- [[pbi-model-apply-wrapper]] — canonical plan + implementation reference for the wrapper
- [[client-workflow-automation]] — session log with full GP-208 execution history
- [[gep-snowflake-pbi-deployment]] — full GEP deployment runbook
- [[GP-208]] — ticket this was discovered during
- [[potential-tickets]] — TE3 CLI hang + naming convention + pbi_scan.py entries
- [[GEP]] — client entity
