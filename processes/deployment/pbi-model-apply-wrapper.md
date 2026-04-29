---
tags: [process, pbi, xmla, tabular-editor, automation, gep, plan, phase-6, option-a]
aliases: [pbi_model_apply wrapper, PBI model apply wrapper, Option A wrapper, Phase 6 wrapper plan]
sources: [session 2026-04-23 Opus xhigh; [[pbi-xmla-model-changes]]; [[phase6-pbi-automation-plan]]]
created: 2026-04-23
updated: 2026-04-23 (auth corrected — MSAL pre-flight repro confirmed)
---

# PBI Model Apply Wrapper — Implementation Plan (Phase 6 Option A)

Planning document for a thin .NET 8 console wrapper that applies Power BI tabular model
changes via XMLA from a subprocess context, replacing the broken Tabular Editor CLI path
described in [[pbi-xmla-model-changes]]. Produced by Opus 4.7 on 2026-04-23 at `xhigh`
effort. A follow-on Sonnet implementation session reads this file verbatim as its spec.

**Target artefacts (when implementing, NOT in this session):**
- New C# project — `clients/GEP/scripts/pbi_model_apply/` (source + gitignored build output)
- `clients/.claude/commands/gep-feature.md` §G rewrite + one line in Sub-step 1b
- `clients/GEP/scripts/pbi_config.yaml` — add `pbi_model_apply_path` key
- `clients/GEP/tickets/GP-208/pbi_model_script.cs` — two 1-line partition-expression edits

**Branch:** `feature/paulrussell/workflow-automation/gep-scripted-deploy` (existing).

**Core thesis.** The hang diagnosed in [[pbi-xmla-model-changes]] is a property of *the TE3
binary*, not of XMLA write or TOM. The XMLA endpoint is up; bearer-token auth works; TOM's
managed .NET libraries don't need a message loop or a GUI. Build our own console-subsystem
wrapper that calls TOM directly, and run TE3-compatible C# scripts inside it via Roslyn
CSharpScript. The hang goes away because the process the skill spawns is a plain console
EXE with no Chromium, no WebView2, no GUI init — just `Server.Connect()` over HTTPS.

See also:
- [[phase6-pbi-automation-plan]] — parent Phase 6 plan; §G/§H/§I helpers this integrates with
- [[client-workflow-automation]] — workstream tracker; 2026-04-22/23 session log entry
- [[pbi-xmla-model-changes]] — the dead-end diagnosis this plan resolves
- [[potential-tickets]] — "pbi_scan.py requires TE3" entry (closed by this plan)

---

## 1. Technical decision matrix

One row per research question. The **Decision** column is the forcing function for the
wrapper design spec in §3.

| Q | Research question | Answer (evidence) | Decision that falls out |
|---|---|---|---|
| Q1a | NuGet package for XMLA write from .NET console? | `Microsoft.AnalysisServices.NetCore.retail.amd64` (TOM for .NET Core / .NET 6+). The `.amd64` suffix is the Microsoft convention for the x64 native TOM build. This is what Tabular Editor 3 itself references (TE3 is a .NET 8 WPF app). | Target **.NET 8** (LTS, already present on Paul's machine via TE3). Reference `Microsoft.AnalysisServices.NetCore.retail.amd64` ≥ `19.84.0`. Do NOT use `Microsoft.AnalysisServices.retail.amd64` (the .NET Framework variant). |
| Q1b | Does `Server.Connect()` accept the bearer-token connection string without triggering interactive AAD? | **CORRECTED 2026-04-23 (live repro)** — partially. The `User ID=AzureAD;Password=<bearer>` *connection-string syntax* is valid TOM, but the bearer token **source** is critical. `az account get-access-token --resource https://analysis.windows.net/powerbi/api` returns a JWT that PBI REST (§H) accepts, but the PBI XMLA endpoint **rejects** it — that token's `appid` is `04b07795-8ddb-461a-bbee-02f9e1bf7b46` (Microsoft Azure CLI), which is not an approved XMLA client. The correct auth path is **MSAL device-code flow** with PBI public client ID `ea0616ba-638b-4df5-95b9-636659ae5121`, scope `https://analysis.windows.net/powerbi/api/.default`, authority `https://login.microsoftonline.com/<tenant>`. That token (`appid=ea0616ba-...`, `aud=https://analysis.windows.net/powerbi/api`) is accepted. The TOM API to use is `server.AccessToken = new AccessToken(token, DateTimeOffset.UtcNow.AddMinutes(55), null)` + `server.OnAccessTokenExpired` callback — **not** the `User ID`/`Password` connection-string fields. The connection string should be `Data Source=powerbi://...;Initial Catalog=<dataset>` only (no credentials in string). Confirmed live against GEP PPU capacity 2026-04-23. | Wrapper owns MSAL auth internally. **Remove `--token` CLI arg.** Connection string has no credentials. Token acquired via `AcquireTokenWithDeviceCode` on first run; cached to disk at `%LOCALAPPDATA%\pbi_model_apply\msal.cache` via `Microsoft.Identity.Client.Extensions.Msal`; silent re-use within ~1h; re-prompt on expiry. `--clear-token-cache` flag deletes cache and forces re-prompt. NuGet: add `Microsoft.Identity.Client` 4.64.* + `Microsoft.Identity.Client.Extensions.Msal` 4.64.*. |
| Q1c | .NET version required by TOM? | `Microsoft.AnalysisServices.NetCore.retail.amd64` targets .NET Core 3.1 and above. Current stable versions support .NET 6 / 7 / 8. .NET 8 is LTS through Nov 2026. | Target framework: **`net8.0-windows`**. (`-windows` TFM is needed because TOM's OLE DB shim has Windows-only native components; irrelevant for PBI endpoint but keeps publish clean.) |
| Q1d | STA thread required? Does a console app without a pumped message loop work? | TOM on .NET Core uses **managed HTTPS transport** for `powerbi://` data sources — no COM, no OLE DB, no message pump. The TE3 hang is caused by **TE3's own startup code (WebView2 init)**, not TOM. A plain .NET 8 console app calling `Server.Connect()` does not hang from a subprocess context. STA is not required, but `[STAThread]` on Main() is a no-cost safety measure in case any implicit COM init happens. | Wrapper Main uses `[STAThread]`. No message pump. No `Application.DoEvents()`. No WPF / WinForms dependencies. |
| Q1e | Is MSOLAP OLE DB required? | **No** — for `powerbi://` data sources with bearer-token auth, the .NET Core TOM uses HTTPS transport internally. MSOLAP OLE DB would be required only for on-prem SSAS (which GEP does not use). Separately, Paul's machine already has MSOLAP installed (shipped with TE2 and TE3) — belt and braces. | Do NOT include `Provider=MSOLAP;` in the connection string. No runtime install of SQL Server Feature Pack needed. No MSOLAP bundling. |
| Q2a | Can Roslyn `CSharpScript` resolve TOM type references like `Microsoft.AnalysisServices.Tabular.Table`? | Yes. `ScriptOptions.Default.WithReferences(typeof(Model).Assembly, typeof(TabularExtensions).Assembly).WithImports("Microsoft.AnalysisServices.Tabular", "PbiModelApply", "System", "System.Linq", "System.Collections.Generic")` brings the TOM assembly + our extension-method assembly into scope. `Microsoft.AnalysisServices.Tabular` is a managed assembly — no native-reference gymnastics required. | Use Roslyn CSharpScript (`Microsoft.CodeAnalysis.CSharp.Scripting` NuGet) for script execution. Reference TOM + wrapper extensions; import both namespaces implicitly so existing TE scripts work without `using` directives (TE3 scripts have none). |
| Q2b | What is the TE3 scripting API surface used by `pbi_model_script.cs`? How much of it is TE sugar vs. raw TOM? | Audited against TOM 19.x public surface — see §4 below for the line-by-line table. **Most calls are raw TOM**. Only two bits are TE-specific: (i) `Model.AddTable(string)` creates a Table with a default M-backed Partition in one shot; (ii) `partition.Expression = "..."` is a TE-added property that proxies `((MPartitionSource)partition.Source).Expression`. Everything else (`Model.Tables.Contains`, `Model.Tables["X"]`, `table.Columns[...].IsHidden`, `table.Columns[...].FormatString`, `Model.Relationships`, `SingleColumnRelationship.FromTable/ToTable/FromColumn/ToColumn`, `Model.SaveChanges()`) is TOM-native. | Emulation layer is thin: one `AddTable` extension method + one `AddRelationship` extension method + one `SetExpression` extension method on `Partition`. The last one is the only syntactic break from TE3 (C# does not support extension properties). Document the `.Expression = x` → `.SetExpression(x)` delta. |
| Q2c | Can we use TMSL Alter over `Server.Execute()` instead? | Yes technically — TOM exposes `Server.Execute(string tmsl)` which sends XMLA commands over the wire. But expressing "add a table with an M partition + relationship + format strings" as TMSL JSON requires ~100+ lines of nested JSON per table with exact `Sequence`/`createOrReplace` semantics. Verbose, error-prone, and would discard the familiar TE3 C# model. | **Rejected for v1.** Approach 2 (Roslyn + TE emulation) is the chosen path. TMSL stays available via `Model.Database.CreateOrReplace()` if any future script needs it — it's reachable from inside a Roslyn script if required. |
| Q2d | Overall script-execution approach? | See options in §2.1 below. | **Roslyn CSharpScript + TE emulation layer.** Preserves TE3 script muscle memory, keeps the wrapper ~300 LOC, gives legible syntax errors, and lets Paul paste scripts into TE3 GUI interchangeably (with the one `SetExpression` caveat). |
| Q3a | Minimum-friction build & deploy? | See options matrix in §2.2. Self-contained single-file EXE (~60 MB) works but bloats the repo; dotnet-script needs an extra global tool; a global-tool package is overkill for one machine. **Source project + `dotnet build -c Release` once, bin output gitignored.** Build output is ~8 MB (EXE + DLLs). First-time setup is one command. | `clients/GEP/scripts/pbi_model_apply/` is a checked-in C# project. `bin/` and `obj/` are gitignored. One-time setup: `dotnet build -c Release`. Skill invokes `bin/Release/net8.0-windows/pbi_model_apply.exe`. |
| Q3b | Does `Microsoft.AnalysisServices.NetCore.retail.amd64` ship all native DLLs? | Yes. The NuGet package includes the managed TOM assembly plus the one native runtime DLL (`Microsoft.AnalysisServices.Tabular.Native.dll`) for x64. `dotnet build` places them in the output directory automatically. No separate SSAS install required. | No post-install configuration. `dotnet build` produces a self-sufficient output directory. |
| Q3c | Is MSOLAP already installed on Paul's machine? | Yes — both TE2 and TE3 install MSOLAP via their MSI/winget installers. We do not depend on it for `powerbi://`, but it is present if any future edge case needs it. | No-op. |
| Q3d | CLI interface? | **REVISED 2026-04-23** — `--token` removed. Since the wrapper owns MSAL auth internally (per Q1b correction), the token is never a CLI arg. The wrapper acquires, caches, and refreshes the token without caller involvement. | `pbi_model_apply --script <path> --workspace <name> --dataset <name> [--dry-run] [--timeout <sec>] [--verbose] [--clear-token-cache]`. See §3.4 for full contract. |
| Q4a | What is a successful run? | Connect succeeds → load Database/Model → Roslyn-compile script → execute script (script calls `Model.SaveChanges()`) → Disconnect → exit 0. If script omits `SaveChanges()`, wrapper prints a warning but does not auto-save (respect author intent). | See §3.7 exit-code schema. |
| Q4b | Exit-code semantics? | Explicit codes are cheap for the skill to react to and make debugging easier than one-size-fits-all 0/1. | `0` success, `1` script runtime exception, `2` auth/401, `3` connection/unreachable, `4` Roslyn compile error, `5` model locked, `6` invalid CLI args, `99` unexpected. Full schema in §3.7. |
| Q4c | Model-locked behaviour? | TOM surfaces `Microsoft.AnalysisServices.AmoException` with an inner TMSL error when another session holds the exclusive XMLA write lock (typically: Paul has TE3 GUI open on the same dataset). The error message includes "session is blocked" or "model is locked". | Catch `AmoException`; if message matches `"lock"` or `"blocked"` (case-insensitive), exit 5 with message: `"Model is locked by another session. Close TE3 GUI (or any open XMLA session) against <dataset> and retry."` |
| Q4d | Timeout behaviour? | TOM's `Server.ConnectionTimeout` (seconds, default 15) governs connect. Per-op timeouts for SaveChanges are set via `Server.CommandTimeout` (default 0 = infinite for AS-on-prem; PBI Premium enforces its own limits server-side). Large structural SaveChanges can take 30–120s legitimately. | Expose `--timeout <sec>` (default 300). Sets both ConnectionTimeout (capped at `min(30, timeout/10)`) and CommandTimeout (capped at `timeout`). On CLR-side `TimeoutException`: exit 3 with `"Operation timed out after <sec>s"`. |
| Q5a | §G rewrite scope? | Current §G builds a connection string, runs `TabularEditor3.exe /s … /x "…"`. New §G keeps token acquisition (§I) and config reads, but replaces step 4 (command construction) and the TE-path config read with a pbi_model_apply invocation. Steps 5–8 (show command with token redacted, run via Bash, auth-error retry, generic-error handling) stay identical. | See exact text replacement in §6. |
| Q5b | Sub-step 1b text change? | The `APPLY MODEL SCRIPT VIA TE CLI` heading in Sub-step 1b says "Use §G (env = sandbox, script_path = …)". That line is unchanged — the caller contract is stable. Only the section header wording ("via TE CLI") should be softened to "via PBI Model Apply" to avoid lying about the tool. | Rename subsection heading from `APPLY MODEL SCRIPT VIA TE CLI` → `APPLY MODEL SCRIPT`. No other body changes in Sub-step 1b. Same in Sub-step 2's TEST-apply block. |
| Q5c | Config key change? | Add new top-level key `pbi_model_apply_path`. Keep `tabular_editor_path` — `pbi_scan.py` still references it (for the currently-disabled TE3 scan path, and the REST fallback still reads `te_path` for its informational TE2-detected messaging). They are different tools with different roles. | `pbi_config.yaml` gains one key; no other structural change. See §6.2 for the exact YAML diff. |
| Q5d | Does `pbi_scan.py` need the wrapper too? | No. `pbi_scan.py` has a functional REST fallback (DAX `EVALUATE TOPN` + `COUNTROWS` per focus table) and its TE3 path is `if False`-guarded. Scanning is not on the critical path of Sub-step 1b (it's a nice-to-have for Option A/B/C presentation; the GEP naming-convention issue already means the scan misses tables anyway — see [[potential-tickets]]). **Explicitly out of scope for this plan.** | pbi_scan.py untouched. Continues REST-only. |

---

## 2. Chosen approach

### 2.1 Script-execution strategy

**Chosen: Approach 2 — TE scripting API emulation via Roslyn CSharpScript.**

```
┌─ pbi_model_apply.exe (.NET 8, console subsystem) ───────────────┐
│                                                                  │
│  1. Parse CLI args                                               │
│  2. new Server(); server.Connect(bearer-token connection str)    │
│  3. var model = server.Databases[dataset].Model                  │
│  4. var globals = new ScriptGlobals(model)                       │
│  5. scriptText = File.ReadAllText(--script)                      │
│  6. ScriptOptions                                                │
│       .WithReferences(TOM assembly, this assembly)               │
│       .WithImports("Microsoft.AnalysisServices.Tabular",         │
│                    "PbiModelApply", "System", "System.Linq",     │
│                    "System.Collections.Generic")                 │
│  7. await CSharpScript.RunAsync(scriptText, options, globals)    │
│     ├─ globals expose `Model`, `Info/Warning/Error` as fields    │
│     └─ extension methods `AddTable`, `AddRelationship`,          │
│        `SetExpression` resolve via `using PbiModelApply;` import │
│  8. If model.HasLocalChanges after run: warn (script didn't save)│
│  9. server.Disconnect()                                          │
│ 10. exit 0                                                       │
└──────────────────────────────────────────────────────────────────┘
```

**Why not the rejected alternatives:**
- **Approach 1 (Roslyn + raw TOM, no emulation):** forces every script to read/write
  partitions via `((MPartitionSource)p.Source).Expression = …` — ugly and breaks copy-paste
  from TE3 GUI. Costs 1 weekend to save 30 lines of emulation code.
- **Approach 3 (pre-compile scripts into DLLs):** forces a build step per ticket. Breaks
  the "paste script from TE3 GUI into pbi_model_script.cs, commit, run" flow that is the
  entire point of Sub-step 1b.
- **Approach 4 (TMSL JSON):** verbose, error-prone, loses the C# ergonomics. Available via
  `Server.Execute(tmsl)` from inside a Roslyn script for any future edge case that demands
  it; no need to force it at the wrapper boundary.

**Accepted trade-off:** one documented delta from TE3 GUI syntax — partition expression
assignment (see §4). Two lines in the existing GP-208 script must change. All future
scripts should use `.SetExpression("...")` from the start. The skill's drafting template in
Sub-step 1b's PRE-FLIGHT section will be updated to use this form.

### 2.2 Build & deploy strategy

**Chosen: Option iv — checked-in source project, gitignored build output, one-time
`dotnet build -c Release`, skill invokes the compiled EXE.**

| Criterion | Option i (self-contained EXE committed) | Option ii (dotnet global tool) | Option iii (dotnet-script .csx) | Option iv (source project + build) **✓** |
|---|---|---|---|---|
| Binary size in repo | ~60 MB committed | ~0 (consumed via NuGet) | ~5 KB .csx | ~0 (bin/ gitignored) |
| One-time setup | Download or unpack | `dotnet tool install -g` | `dotnet tool install -g dotnet-script` | `dotnet build -c Release` |
| Startup latency | ~200 ms | ~200 ms | ~3–5 s (cold compile per run) | ~200 ms |
| Source review | Difficult (EXE only) | Difficult | Readable .csx | Full C# project, `dotnet build` |
| Debuggable | Hard | Hard | Medium | Easy (`dotnet build --configuration Debug`) |
| Update path | Rebuild + recommit 60 MB | Publish new NuGet | Edit .csx | `git pull && dotnet build` |
| Runtime dep | None (self-contained) | .NET SDK | .NET SDK + dotnet-script | .NET SDK / Runtime 8.0 |
| Source-of-truth | Binary | External NuGet | Script | Repo source |

Option iv wins on all the axes Paul cares about: small git diff, fully auditable source,
fast invocation, easy updates, no new global tool to install. Paul already has .NET SDK
(TE3 is built on it).

**Project layout:**
```
clients/GEP/scripts/pbi_model_apply/
├── pbi_model_apply.csproj          # project file — targets net8.0-windows
├── Program.cs                      # entry point, CLI parsing, orchestration
├── ScriptGlobals.cs                # globals class exposed to Roslyn (Model, Info/Warn/Error)
├── TabularExtensions.cs            # namespace PbiModelApply — AddTable, AddRelationship, SetExpression
├── ExitCodes.cs                    # enum + helpers
├── README.md                       # build + smoke-test instructions
├── .gitignore                      # bin/, obj/
└── (bin/, obj/ — gitignored)
```

**First-time setup (Paul, ~2 min):**
```
cd C:/Users/PaulRussell/repos/clients/GEP/scripts/pbi_model_apply
dotnet build -c Release
```

Output: `bin/Release/net8.0-windows/pbi_model_apply.exe`.

**Skill invocation (absolute path, forward slashes on Windows are fine for bash):**
```
GEP/scripts/pbi_model_apply/bin/Release/net8.0-windows/pbi_model_apply.exe \
    --script GEP/tickets/GP-208/pbi_model_script.cs \
    --workspace "GEP Sandbox Models" \
    --dataset "GEP_Sandbox_Current" \
    --token "<bearer>"
```

---

## 3. Wrapper design spec

Enough detail for a Sonnet implementation session to write the wrapper without ambiguity.

### 3.1 Project file (`pbi_model_apply.csproj`)

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
    <RootNamespace>PbiModelApply</RootNamespace>
    <AssemblyName>pbi_model_apply</AssemblyName>
    <Platforms>x64</Platforms>
    <PlatformTarget>x64</PlatformTarget>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AnalysisServices.NetCore.retail.amd64" Version="19.84.1" />
    <PackageReference Include="Microsoft.CodeAnalysis.CSharp.Scripting" Version="4.11.0" />
    <!-- MSAL for device-code auth (Q1b correction 2026-04-23) -->
    <PackageReference Include="Microsoft.Identity.Client" Version="4.64.*" />
    <PackageReference Include="Microsoft.Identity.Client.Extensions.Msal" Version="4.64.*" />
  </ItemGroup>
</Project>
```

Version notes:
- `19.84.1` is the most recent stable TOM NetCore release as of Nov 2025. If NuGet
  restore reports a newer stable, accept it — TOM is backward-compatible within 19.x.
  If it reports "not found", try `19.84.0` (prior stable). **Do not pin below 19.80** —
  earlier versions had PBI bearer-token quirks.
- `4.11.0` is the stable Roslyn scripting line. Newer versions of `Microsoft.CodeAnalysis.*`
  (4.12+) may move APIs — keep the 4.11 line until tested.

### 3.2 `Program.cs` — entry point and orchestration

Signature (pseudocode; Sonnet writes real C#):

```csharp
namespace PbiModelApply;

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AnalysisServices;             // Server, AmoException, ConnectionInfo
using Microsoft.AnalysisServices.Tabular;     // Model, Database
using Microsoft.CodeAnalysis.CSharp.Scripting;
using Microsoft.CodeAnalysis.Scripting;

public static class Program
{
    [STAThread]
    public static int Main(string[] args)
        => MainAsync(args).GetAwaiter().GetResult();

    private static async Task<int> MainAsync(string[] args)
    {
        CliArgs cli;
        try { cli = CliArgs.Parse(args); }
        catch (ArgumentException ex) {
            Console.Error.WriteLine($"[pbi_model_apply] invalid args: {ex.Message}");
            PrintUsage();
            return (int)ExitCode.InvalidArgs;              // 6
        }

        if (cli.DryRun) {
            return await DryRunAsync(cli);                 // compile-only; no XMLA
        }

        Server? server = null;
        try {
            // TOM gotcha 1 (confirmed 2026-04-23): Server is ambiguous between
            // Microsoft.AnalysisServices.Server and Microsoft.AnalysisServices.Tabular.Server.
            // Use fully-qualified type: Microsoft.AnalysisServices.Tabular.Server
            server = new Microsoft.AnalysisServices.Tabular.Server();
            // TOM gotcha 2 (confirmed 2026-04-23): MSAL token set via AccessToken API,
            // not connection-string Password field. Acquire via AcquireMsalToken() (see §3.2b).
            var (bearerToken, _) = await AcquireMsalTokenAsync(cli);
            server.AccessToken = new Microsoft.AnalysisServices.AccessToken(
                bearerToken, DateTimeOffset.UtcNow.AddMinutes(55), null);
            server.OnAccessTokenExpired = _ => {
                var (t, _) = AcquireMsalTokenAsync(cli).GetAwaiter().GetResult();
                return new Microsoft.AnalysisServices.AccessToken(t, DateTimeOffset.UtcNow.AddMinutes(55), null);
            };
            server.Connect(BuildConnectionString(cli));
            // TOM gotcha 3 (confirmed 2026-04-23): server.Databases[string] indexes by
            // Analysis Services internal ID, NOT display Name. Use LINQ instead.
            var database = server.Databases
                .Cast<Microsoft.AnalysisServices.Tabular.Database>()
                .FirstOrDefault(d => d.Name == cli.Dataset);
            if (database is null) {
                Console.Error.WriteLine($"[pbi_model_apply] dataset not found: {cli.Dataset}");
                return (int)ExitCode.ConnectionError;      // 3
            }
            var model = database.Model;

            var globals = new ScriptGlobals(model);
            var options = BuildScriptOptions(cli);
            var scriptText = await File.ReadAllTextAsync(cli.ScriptPath);

            try {
                await CSharpScript.RunAsync(scriptText, options, globals);
            }
            catch (CompilationErrorException cex) {
                Console.Error.WriteLine("[pbi_model_apply] script compile error:");
                foreach (var d in cex.Diagnostics) Console.Error.WriteLine($"  {d}");
                return (int)ExitCode.CompileError;          // 4
            }
            catch (AmoException aex) when (IsLockError(aex)) {
                Console.Error.WriteLine(
                    "[pbi_model_apply] model is locked by another session. " +
                    "Close TE3 GUI (or any open XMLA session) against " +
                    $"'{cli.Dataset}' and retry. Inner: {aex.Message}");
                return (int)ExitCode.ModelLocked;           // 5
            }

            if (model.HasLocalChanges) {
                Console.Error.WriteLine(
                    "[pbi_model_apply] warning: script ran to completion but " +
                    "did not call Model.SaveChanges(). Changes NOT persisted.");
            }

            return (int)ExitCode.Success;                   // 0
        }
        catch (AmoException aex) when (IsAuthError(aex)) {
            Console.Error.WriteLine($"[pbi_model_apply] auth error: {aex.Message}");
            return (int)ExitCode.AuthError;                 // 2
        }
        catch (AmoException aex) when (IsLockError(aex)) {
            Console.Error.WriteLine(
                "[pbi_model_apply] model is locked by another session. " +
                $"Close TE3 GUI and retry. Inner: {aex.Message}");
            return (int)ExitCode.ModelLocked;               // 5
        }
        catch (Exception ex) when (IsTimeoutOrNetwork(ex)) {
            Console.Error.WriteLine($"[pbi_model_apply] connection error: {ex.Message}");
            return (int)ExitCode.ConnectionError;           // 3
        }
        catch (Exception ex) {
            Console.Error.WriteLine($"[pbi_model_apply] unexpected: {ex.GetType().Name}: {ex.Message}");
            if (cli.Verbose) Console.Error.WriteLine(ex.StackTrace);
            return (int)ExitCode.Unexpected;                // 99
        }
        finally {
            try { server?.Disconnect(); } catch { /* best-effort */ }
        }
    }

    // REVISED 2026-04-23: no credentials in connection string; auth via server.AccessToken API
    private static string BuildConnectionString(CliArgs cli) =>
        $"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{cli.Workspace};" +
        $"Initial Catalog={cli.Dataset}";

    private static ScriptOptions BuildScriptOptions(CliArgs cli) =>
        ScriptOptions.Default
            .WithReferences(
                typeof(Microsoft.AnalysisServices.Tabular.Model).Assembly,
                typeof(TabularExtensions).Assembly)
            .WithImports(
                "System",
                "System.Linq",
                "System.Collections.Generic",
                "Microsoft.AnalysisServices.Tabular",
                "PbiModelApply");

    private static bool IsAuthError(AmoException ex) {
        var m = ex.Message ?? "";
        return m.Contains("401", StringComparison.OrdinalIgnoreCase)
            || m.Contains("unauthorized", StringComparison.OrdinalIgnoreCase)
            || m.Contains("authentication", StringComparison.OrdinalIgnoreCase)
            || m.Contains("access denied", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsLockError(AmoException ex) {
        var m = ex.Message ?? "";
        return m.Contains("lock", StringComparison.OrdinalIgnoreCase)
            || m.Contains("blocked", StringComparison.OrdinalIgnoreCase)
            || m.Contains("exclusive", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsTimeoutOrNetwork(Exception ex) =>
        ex is TimeoutException
     || ex.GetType().FullName?.Contains("Network") == true
     || ex.GetType().FullName?.Contains("Socket") == true
     || (ex.Message?.Contains("timeout", StringComparison.OrdinalIgnoreCase) ?? false);

    private static async Task<int> DryRunAsync(CliArgs cli) {
        var scriptText = await File.ReadAllTextAsync(cli.ScriptPath);
        var options = BuildScriptOptions(cli);
        var script = CSharpScript.Create(scriptText, options, typeof(ScriptGlobals));
        var diags = script.Compile();
        var errors = diags.Where(d => d.Severity == DiagnosticSeverity.Error).ToList();
        if (errors.Count == 0) {
            Console.WriteLine("[pbi_model_apply] dry-run OK — script compiles.");
            return (int)ExitCode.Success;
        }
        Console.Error.WriteLine("[pbi_model_apply] dry-run FAIL — compile errors:");
        foreach (var d in errors) Console.Error.WriteLine($"  {d}");
        return (int)ExitCode.CompileError;
    }

    private static void PrintUsage() {
        Console.Error.WriteLine(
            "usage: pbi_model_apply.exe --script <path> --workspace <name> --dataset <name> --token <bearer>\n" +
            "                           [--dry-run] [--timeout <seconds>] [--verbose]");
    }
}
```

### 3.2b MSAL device-code token acquisition (new — Q1b correction 2026-04-23)

Add a `TokenCache.cs` (or inline in `Program.cs`) with this logic:

```csharp
private const string PbiPublicClientId = "ea0616ba-638b-4df5-95b9-636659ae5121";
private const string TenantId = "e2bae64b-6e5f-4f55-b81c-ada320c7f572";  // aldc.io
private static readonly string[] PbiXmlaScopes =
    { "https://analysis.windows.net/powerbi/api/.default" };
private static readonly string CachePath =
    Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "pbi_model_apply", "msal.cache");

private static async Task<(string token, DateTimeOffset expiry)> AcquireMsalTokenAsync(CliArgs cli)
{
    if (cli.ClearTokenCache && File.Exists(CachePath))
        File.Delete(CachePath);

    var app = PublicClientApplicationBuilder
        .Create(PbiPublicClientId)
        .WithAuthority($"https://login.microsoftonline.com/{TenantId}")
        .WithRedirectUri("http://localhost")
        .Build();

    // Wire up disk cache
    var cacheHelper = await MsalCacheHelper.CreateAsync(
        new StorageCreationPropertiesBuilder("msal.cache", Path.GetDirectoryName(CachePath)!)
            .Build());
    cacheHelper.RegisterCache(app.UserTokenCache);

    // Try silent first; fall back to device-code
    AuthenticationResult result;
    var accounts = await app.GetAccountsAsync();
    try {
        result = await app.AcquireTokenSilent(PbiXmlaScopes, accounts.FirstOrDefault())
            .ExecuteAsync();
    }
    catch (MsalUiRequiredException) {
        result = await app.AcquireTokenWithDeviceCode(PbiXmlaScopes, dc => {
            Console.WriteLine(dc.Message);
            return Task.CompletedTask;
        }).ExecuteAsync();
    }
    return (result.AccessToken, result.ExpiresOn);
}
```

**NuGet:** `Microsoft.Identity.Client` 4.64.* + `Microsoft.Identity.Client.Extensions.Msal` 4.64.*.

**Disk cache location:** `%LOCALAPPDATA%\pbi_model_apply\msal.cache` (auto-created on first run).

**`--clear-token-cache`:** deletes the cache file, forcing a fresh device-code prompt.

### 3.3 `ScriptGlobals.cs` — globals exposed to the Roslyn script

```csharp
namespace PbiModelApply;

using System;
using Microsoft.AnalysisServices.Tabular;

public sealed class ScriptGlobals
{
    public Model Model { get; }

    public ScriptGlobals(Model model) { Model = model; }

    public void Info(string message)    => Console.WriteLine($"[info]    {message}");
    public void Warning(string message) => Console.WriteLine($"[warning] {message}");
    public void Error(string message)   => Console.Error.WriteLine($"[error]  {message}");
}
```

The script sees `Model`, `Info`, `Warning`, `Error` as ambient globals — same syntax as
TE3's scripting panel.

### 3.4 `TabularExtensions.cs` — TE API emulation

```csharp
namespace PbiModelApply;

using Microsoft.AnalysisServices.Tabular;

public static class TabularExtensions
{
    /// <summary>
    /// Creates a new Table with a single default M-backed partition (empty expression).
    /// Matches Tabular Editor 3's Model.AddTable(name) sugar.
    /// Always creates an MPartitionSource — never DAX — to avoid the partition-type
    /// gotcha documented in [[pbi-xmla-model-changes]].
    /// </summary>
    public static Table AddTable(this Model model, string tableName)
    {
        var table = new Table { Name = tableName };
        var partition = new Partition
        {
            Name = tableName,
            Source = new MPartitionSource { Expression = "" }
        };
        table.Partitions.Add(partition);
        model.Tables.Add(table);
        return table;
    }

    /// <summary>
    /// Creates a SingleColumnRelationship (many→one, single cross-filter, active) between
    /// two columns. Matches TE3's Model.AddRelationship(col1, col2) sugar.
    /// </summary>
    public static Relationship AddRelationship(this Model model, Column from, Column to)
    {
        var rel = new SingleColumnRelationship
        {
            FromColumn = from,
            ToColumn = to,
            FromCardinality = RelationshipEndCardinality.Many,
            ToCardinality   = RelationshipEndCardinality.One,
            CrossFilteringBehavior = CrossFilteringBehavior.OneDirection,
            IsActive = true
        };
        model.Relationships.Add(rel);
        return rel;
    }

    /// <summary>
    /// Sets or replaces the M expression on a partition. Replaces Source with a new
    /// MPartitionSource if the existing Source is not an M source (defensive).
    /// Required because C# does not support extension properties — replaces TE3's
    /// `partition.Expression = "..."` direct-property assignment.
    /// </summary>
    public static void SetExpression(this Partition partition, string mExpression)
    {
        if (partition.Source is MPartitionSource mSource)
        {
            mSource.Expression = mExpression;
        }
        else
        {
            partition.Source = new MPartitionSource { Expression = mExpression };
        }
    }
}
```

### 3.5 `ExitCodes.cs`

```csharp
namespace PbiModelApply;

public enum ExitCode
{
    Success        = 0,
    ScriptRuntime  = 1,  // uncaught exception from script body during execution
    AuthError      = 2,  // 401 / unauthorized / access denied from XMLA
    ConnectionError= 3,  // server unreachable, timeout, dataset not found
    CompileError   = 4,  // Roslyn diagnostics with severity Error
    ModelLocked    = 5,  // another XMLA session holds exclusive write lock
    InvalidArgs    = 6,  // CLI parsing failed
    Unexpected     = 99, // catch-all
}
```

### 3.6 `CliArgs` — parsing

Lightweight in Program.cs or its own file. **REVISED 2026-04-23** — `--token` removed; `--clear-token-cache` added.

Required: `--script`, `--workspace`, `--dataset`. Optional: `--dry-run`, `--timeout <int>`, `--verbose`, `--clear-token-cache`. Use simple loop-and-switch parsing; no `System.CommandLine` dependency (keeps the NuGet surface small).

Defensive:
- `--script <path>`: must exist on disk. Otherwise → exit 6.
- `--timeout <int>`: must be > 0. Default 300.
- Unknown flag → exit 6.
- Token is never a CLI arg — wrapper owns MSAL auth internally (see §3.2b).

Token is read from the argv as-is. (Windows process arg visibility is acceptable on Paul's
single-user machine; see §3.8.)

### 3.7 Exit-code schema (contract for the skill)

| Code | Name | Meaning | §G reaction |
|---|---|---|---|
| `0` | Success | Script ran, SaveChanges confirmed (or absent and warned). | Proceed. |
| `1` | ScriptRuntime | Uncaught exception during script execution (TOM error, DAX error, null deref in user code). Message to stderr. | Print stderr. Ask `(retry / skip / abort)`. |
| `2` | AuthError | 401 / "unauthorized" / "access denied" from XMLA. | **REVISED 2026-04-23** — wrapper owns MSAL auth; §I token invalidation no longer applies. Tell Paul: "XMLA auth failed. Try running with `--clear-token-cache` to force fresh device-code login." Ask `(retry-with-clear-cache / skip / abort)`. |
| `3` | ConnectionError | Network / timeout / dataset-not-found. | Print stderr. Ask `(retry / skip / abort)`. Flag for Paul to check VPN / XMLA endpoint. |
| `4` | CompileError | Roslyn diagnostics have severity Error. Script never ran. | Print Roslyn diagnostics verbatim. Tell Paul to fix the script. Do NOT retry — the script is broken. |
| `5` | ModelLocked | Another XMLA session holds exclusive write lock. | Tell Paul to close TE3 GUI. Ask `(retry / abort)`. |
| `6` | InvalidArgs | CLI parse failure. | Print stderr. This is a skill bug (hard fail — escalate). |
| `99` | Unexpected | Caught-all. | Print stderr + stack trace. `(retry / abort)`. |

All error messages go to **stderr** as `[pbi_model_apply] <category>: <message>`. stdout is
reserved for `Info()/Warning()` output from the script (so `Info("added table X")` actually
prints to Paul, not to a suppressed channel).

### 3.8 Token safety (revised 2026-04-23)

- **No token on command line.** The MSAL token is never passed as a CLI arg, env var, or
  printed anywhere. The wrapper acquires it internally; `--verbose` never prints it.
- **Disk cache** at `%LOCALAPPDATA%\pbi_model_apply\msal.cache` — user-private,
  encrypted at rest by the OS credential store via `MsalCacheHelper`. No plaintext token on disk.
- **`--clear-token-cache`** deletes the cache file entirely; next run prompts device code.
- **§G rewrite** (see §6.1) no longer needs step 5 token redaction (no token in the
  command line). Display command is just `pbi_model_apply.exe --script ... --workspace ...
  --dataset ...` — nothing to redact.

---

## 4. TE3 script API compatibility assessment

Line-by-line audit of `GEP/tickets/GP-208/pbi_model_script.cs` against the emulation layer
in §3.4.

| Line / pattern | TE3 call | Raw TOM / our emulation | Verdict |
|---|---|---|---|
| `Model.Tables.Contains("X")` | TOM: `MetadataObjectCollection<Table>.Contains(string)` | Works as-is. | ✅ no change |
| `var t = Model.AddTable("X")` | TE3 sugar | Our extension method `TabularExtensions.AddTable(Model, string)` returns `Table` with default M-backed partition. | ✅ no change |
| `t.Partitions[0].Name = "X"` | TOM: `Partition.Name` | Works as-is. | ✅ no change |
| `t.Partitions[0].Expression = "let … in …"` | **TE3-only** (extension property) | C# can't declare extension properties. Rewrite to `t.Partitions[0].SetExpression("let … in …");` — our extension method. | ⚠️ **2 edits in GP-208**: lines 42 and 57. See §4.1 below. |
| `Model.Tables["X"]` | TOM: indexer | Works. | ✅ no change |
| `factTable.Columns.Contains("X")` | TOM: indexer | Works. | ✅ no change |
| `foreach (var rel in Model.Relationships)` | TOM iteration | Works. | ✅ no change |
| `rel.FromTable.Name` / `rel.ToTable.Name` | TOM: `Relationship` is abstract; `SingleColumnRelationship` has these. The existing script's `foreach` yields `Relationship`, and accesses `FromTable`/`ToTable` on it. **Caveat:** those properties actually live on `SingleColumnRelationship`, not on base `Relationship`. | The existing script relies on TE3's wrapped Relationship exposing FromTable/ToTable at the base. In raw TOM, cast via `rel as SingleColumnRelationship`. **In GP-208 the pattern is:** `rel.FromTable.Name == "INVENTORY_FCT_BALANCE" && rel.ToTable.Name == "Product"`. Need to cast first. | ⚠️ **1 edit in GP-208**: lines 84–92 (the `foreach` block). See §4.1. |
| `Model.AddRelationship(colA, colB)` | TE3 sugar | Our extension method. | ✅ no change |
| `tbl.Columns[col].IsHidden = true` | TOM | Works. | ✅ no change |
| `tbl.Columns[col].FormatString = "#,##0"` | TOM | Works. | ✅ no change |
| `Model.SaveChanges()` | TOM: `Microsoft.AnalysisServices.Tabular.Model.SaveChanges()` exists natively (since TOM 19.x) | Works. | ✅ no change |
| `Info("…")` / `Warning("…")` / `Error("…")` | TE3 scripting output | Our `ScriptGlobals` exposes them. | ✅ no change |
| Local functions at the top level (e.g. `string InventoryFctM(...) => ...`) | TE3 supports; Roslyn supports | Works. | ✅ no change |
| `try { … } catch (Exception ex) { … }` | Standard C# | Works. | ✅ no change |
| `new[] { "A", "B" }` array initialisers | Standard C# | Works. | ✅ no change |

### 4.1 Required edits to `pbi_model_script.cs`

**Edit 1 (line 42) — INVENTORY_FCT_BALANCE partition expression**

Before:
```csharp
t.Partitions[0].Expression = InventoryFctM("INVENTORY_FCT_BALANCE", "Table");
```
After:
```csharp
t.Partitions[0].SetExpression(InventoryFctM("INVENTORY_FCT_BALANCE", "Table"));
```

**Edit 2 (line 57) — EXTRACT_INVENTORY_CURRENT partition expression**

Before:
```csharp
t.Partitions[0].Expression = InventoryFctM("EXTRACT_INVENTORY_CURRENT", "View");
```
After:
```csharp
t.Partitions[0].SetExpression(InventoryFctM("EXTRACT_INVENTORY_CURRENT", "View"));
```

**Edit 3 (lines 84–92) — relationship-exists probe via SingleColumnRelationship cast**

Before:
```csharp
foreach (var rel in Model.Relationships)
{
    if (rel.FromTable.Name == "INVENTORY_FCT_BALANCE"
        && rel.ToTable.Name == "Product")
    {
        relExists = true;
        break;
    }
}
```
After:
```csharp
foreach (var rel in Model.Relationships)
{
    var scr = rel as SingleColumnRelationship;
    if (scr != null
        && scr.FromTable.Name == "INVENTORY_FCT_BALANCE"
        && scr.ToTable.Name == "Product")
    {
        relExists = true;
        break;
    }
}
```

`SingleColumnRelationship` is in `Microsoft.AnalysisServices.Tabular` — already imported
by the Roslyn script options (§3.2). No `using` needed.

All three edits preserve script semantics exactly; no behavioural change.

### 4.2 Template update for the skill's drafting path

Sub-step 1b's PRE-FLIGHT section (in `.claude/commands/gep-feature.md`) has a sample TE
script block shown to Paul when drafting. Update it to use `.SetExpression(...)` from the
start so future drafted scripts don't need this rewrite. See §6.1.

---

## 5. Setup steps for Paul

### 5.1 One-time setup (~5 minutes)

1. **Verify .NET 8 SDK** — Paul almost certainly has it (TE3 ships on .NET 8). Check:
   ```
   dotnet --list-sdks
   ```
   If no `8.0.*` line, install the latest .NET 8 SDK:
   ```
   winget install Microsoft.DotNet.SDK.8
   ```

2. **Build the wrapper** — from the clients repo root:
   ```
   cd GEP/scripts/pbi_model_apply
   dotnet build -c Release
   ```
   Expected first-run output: NuGet restores `Microsoft.AnalysisServices.NetCore.retail.amd64`
   (~30 MB) + `Microsoft.CodeAnalysis.CSharp.Scripting` (~8 MB). Takes 30–90 seconds.
   Success ends with `Build succeeded.` and produces
   `bin/Release/net8.0-windows/pbi_model_apply.exe` (~200 KB EXE + ~30 MB of DLLs in the
   same directory).

3. **Update `pbi_config.yaml`** (one-time) — add the new key. See §6.2 for the diff.

4. **Smoke test** — run a no-op dry-run (wrapper handles MSAL auth internally; browser
   device-code prompt will appear on first run):
   ```
   GEP/scripts/pbi_model_apply/bin/Release/net8.0-windows/pbi_model_apply.exe \
       --script GEP/tickets/GP-208/pbi_model_script.cs \
       --workspace "GEP Sandbox Models" \
       --dataset "GEP_Sandbox_Current" \
       --dry-run
   ```
   On first run: MSAL device-code prompt appears — visit `https://login.microsoft.com/device`
   and enter the code. MSAL caches the token; subsequent runs within ~1h skip the prompt.
   Expected output: `[pbi_model_apply] dry-run OK — script compiles.` and exit 0. If Roslyn
   reports errors, they are actual bugs in the edited GP-208 script; fix per §4.1.

### 5.2 Per-ticket steps

None. The wrapper just works once built.

### 5.3 When to rebuild

- After `git pull` that touches `GEP/scripts/pbi_model_apply/**` — run `dotnet build -c
  Release` again. The skill should print a polite reminder if the EXE is older than the
  source (not in v1 scope — Paul manages this manually).
- After updating NuGet versions — `dotnet restore` then `dotnet build -c Release`.

---

## 6. `gep-feature.md` and `pbi_config.yaml` changes

### 6.1 `.claude/commands/gep-feature.md` — §G full replacement

Replace the entire **§G — Tabular Editor CLI helper** section (current file, lines
~228–252 per the snapshot in the boot procedure) with the following. The heading renames
from "Tabular Editor CLI helper" to "PBI Model Apply helper".

```markdown
### §G — PBI Model Apply helper

Parameters: `env` ∈ {sandbox, test, prod}, `script_path`.

1. Read `GEP/scripts/pbi_config.yaml`. Resolve `workspace_name` from
   `workspaces.<env>.name` and `dataset_name` from `workspaces.<env>.dataset_name`.
   Resolve `pbi_model_apply_path` from the top-level key (relative path from repo root
   to the compiled wrapper EXE).
2. ~~Acquire bearer token via §I.~~ **REVISED 2026-04-23** — wrapper owns MSAL auth
   internally. §I is NOT called before §G. No `--token` arg.
3. Construct command (paths below are relative to the clients repo root; run from
   repo root):
   ```
   "<pbi_model_apply_path>" --script "<script_path>" --workspace "<workspace_name>" --dataset "<dataset_name>"
   ```
   On first run of the day: the wrapper will prompt a browser device-code login. MSAL
   caches the token; subsequent invocations within ~1h are silent.
4. Show the command to Paul. Ask: `(yes / edit-script / skip)` (no token redaction needed
   — no token on the command line).
5. On `yes`: run via Bash. Capture stdout + stderr + exit code.
6. Exit code handling (see pbi_model_apply exit-code schema in
   [[pbi-model-apply-wrapper]] §3.7):
   - `0` — success; proceed.
   - `2` (auth) — invalidate the cached token (§I), re-acquire once, rebuild the
     command, and retry once. If the retry also returns `2`: print stderr and ask
     `(retry / skip / abort)`.
   - `4` (compile error) — print Roslyn diagnostics verbatim; tell Paul the script has
     a syntax error. Do NOT offer retry — the script is broken. Ask `(edit-script / abort)`.
   - `5` (model locked) — tell Paul to close any open TE3 GUI session against the
     dataset. Ask `(retry / abort)`.
   - Any other non-zero (`1`, `3`, `6`, `99`) — print stderr verbatim; ask
     `(retry / skip / abort)`.

The wrapper source is at `GEP/scripts/pbi_model_apply/`. If `<pbi_model_apply_path>`
does not exist on disk, print:
```
⚠️  pbi_model_apply.exe not found at <path>. Build it once with:
    cd GEP/scripts/pbi_model_apply && dotnet build -c Release
```
and ask `(abort / I've built it — retry)`.
```

### 6.2 `GEP/scripts/pbi_config.yaml` — key addition

Add one top-level key. The existing `tabular_editor_path` stays (referenced by
`pbi_scan.py`).

```yaml
# existing keys unchanged
parameter_names:
  compute: SNOWFLAKE_COMPUTE
  database: SNOWFLAKE_DATABASE
  host: SNOWFLAKE_HOST
  role: SNOWFLAKE_ROLE
tabular_editor_path: C:\Program Files\Tabular Editor 3\TabularEditor3.exe
tenant: e2bae64b-6e5f-4f55-b81c-ada320c7f572

# NEW — path to compiled wrapper EXE (relative to clients repo root, forward slashes OK)
pbi_model_apply_path: GEP/scripts/pbi_model_apply/bin/Release/net8.0-windows/pbi_model_apply.exe

workspaces:
  # unchanged
```

### 6.3 Sub-step 1b body text changes

In `.claude/commands/gep-feature.md`:

1. Subsection heading rename:  `**APPLY MODEL SCRIPT VIA TE CLI**` →  `**APPLY MODEL SCRIPT**`
   - (Occurs once in Sub-step 1b; do not change the Sub-step 2 heading
     `APPLY TE SCRIPT TO CLIENT-FACING TEST WORKSPACE` — leave it or rename in parallel,
     see §6.4.)

2. The `PRE-FLIGHT — verify the TE script exists` block contains a sample code template
   shown to Paul when no script exists. Update the partition-expression example so
   drafted scripts use `.SetExpression(...)` from the start:

   Before (current file, around line ~755):
   ```csharp
   Model.Tables["INVENTORY_FCT_BALANCE"].IsHidden = false;
   ```
   (That specific line is fine — no change needed. But add, as part of the same example
   block, a representative "add table with M expression" pattern using the new syntax:)

   Add to the sample block:
   ```csharp
   // Add a new table with an M expression partition:
   var t = Model.AddTable("MY_NEW_TABLE");
   t.Partitions[0].Name = "MY_NEW_TABLE";
   t.Partitions[0].SetExpression("let Source = ... in Source");
   ```

### 6.4 Sub-step 2 TEST-apply block

Current heading: `**APPLY TE SCRIPT TO CLIENT-FACING TEST WORKSPACE**` (plan doc §3.5).
Rename to `**APPLY MODEL SCRIPT TO TEST**` for parity. Body unchanged (still calls §G).

### 6.5 `prod-deployed` — no changes

The prod auto-apply path (Tranche D, per [[phase6-pbi-automation-plan]] §3.7) also calls
§G. Since §G now points at the wrapper instead of TE3, the prod path transparently uses
the wrapper. No Sub-step edits needed.

---

## 7. GP-208 end-to-end validation plan

After the implementation session has built the wrapper and edited the script, run this
sequence to validate against the sandbox dataset. **This is the acceptance test for the
implementation session.**

### 7.1 Preconditions

- `git status` shows the wrapper source + script edits committed on
  `feature/paulrussell/workflow-automation/gep-scripted-deploy`.
- `bin/Release/net8.0-windows/pbi_model_apply.exe` exists (from `dotnet build -c Release`).
- `az login` is current (bearer token acquirable).
- GEP sandbox dataset exists (`workspace_id = 8545f3cb-4e2d-4985-bf31-79066248c9be`,
  `dataset_id = fb41970d-2beb-4ed9-9f82-35c6439b35ea`) — already seeded.
- SANDBOX Snowflake DB `SANDBOX_DG1_GEP_GP208` exists (already deployed per
  [[pbi-xmla-model-changes]] § GP-208 Sub-step 1b Status).
- **No TE3 GUI session is open** on the sandbox dataset.

### 7.2 Step-by-step validation

Run from the clients repo root (`C:/Users/PaulRussell/repos/clients`).

**(a) Build the wrapper**
```bash
cd GEP/scripts/pbi_model_apply && dotnet build -c Release && cd -
```
Expect: `Build succeeded.` + EXE at `bin/Release/net8.0-windows/pbi_model_apply.exe`.

**(b) Dry-run the script — confirms Roslyn compile works on the edited GP-208 script**

**REVISED 2026-04-23** — no `az` token needed; wrapper handles MSAL auth internally.
On first run a browser device-code prompt appears; subsequent runs within ~1h are silent.
```bash
GEP/scripts/pbi_model_apply/bin/Release/net8.0-windows/pbi_model_apply.exe \
    --script GEP/tickets/GP-208/pbi_model_script.cs \
    --workspace "GEP Sandbox Models" \
    --dataset "GEP_Sandbox_Current" \
    --dry-run
```
Expect: `[pbi_model_apply] dry-run OK — script compiles.` exit 0.

**(c) Rebind sandbox to `SANDBOX_DG1_GEP_GP208`** (uses §H, or ad-hoc curl for the test; note: REST still uses `az account get-access-token` via §I — only XMLA uses MSAL):
```bash
TOKEN=$(az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv)
curl -X POST \
  "https://api.powerbi.com/v1.0/myorg/groups/8545f3cb-4e2d-4985-bf31-79066248c9be/datasets/fb41970d-2beb-4ed9-9f82-35c6439b35ea/Default.UpdateParameters" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"updateDetails":[{"name":"SNOWFLAKE_DATABASE","newValue":"SANDBOX_DG1_GEP_GP208"},{"name":"SNOWFLAKE_ROLE","newValue":"SYSADMIN"}]}'
```
Expect: 200 OK (empty body). If pre-Tranche-C sandbox already runs Sub-step 1b, this
happens via §H — running it manually here is only for the acceptance test.

**(d) Apply the model script — THE FAILURE THIS PLAN FIXES** (MSAL handles auth; no --token)
```bash
GEP/scripts/pbi_model_apply/bin/Release/net8.0-windows/pbi_model_apply.exe \
    --script GEP/tickets/GP-208/pbi_model_script.cs \
    --workspace "GEP Sandbox Models" \
    --dataset "GEP_Sandbox_Current"
```
Expect: `[info]` lines for "Added table: INVENTORY_FCT_BALANCE", "Added table:
EXTRACT_INVENTORY_CURRENT", and "SaveChanges() complete.". Exit 0. Total runtime 10–30s.

**(e) Trigger refresh**
```bash
curl -X POST \
  "https://api.powerbi.com/v1.0/myorg/groups/8545f3cb-4e2d-4985-bf31-79066248c9be/datasets/fb41970d-2beb-4ed9-9f82-35c6439b35ea/refreshes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -D /tmp/refresh-headers.txt \
  -d '{"type":"Full","commitMode":"transactional","notifyOption":"NoNotification"}'
REFRESH_ID=$(grep -i '^x-ms-request-id:\|^requestid:' /tmp/refresh-headers.txt | head -1 | cut -d: -f2- | tr -d ' \r\n')
echo "Refresh ID: $REFRESH_ID"
```
Expect: 202 Accepted, refresh ID captured.

**(f) Poll refresh to completion**
```bash
while true; do
  STATUS=$(curl -s \
    "https://api.powerbi.com/v1.0/myorg/groups/8545f3cb-4e2d-4985-bf31-79066248c9be/datasets/fb41970d-2beb-4ed9-9f82-35c6439b35ea/refreshes/$REFRESH_ID" \
    -H "Authorization: Bearer $TOKEN" | python -c "import sys, json; print(json.load(sys.stdin).get('status','?'))")
  echo "$(date): $STATUS"
  [[ "$STATUS" == "Completed" || "$STATUS" == "Failed" || "$STATUS" == "Cancelled" ]] && break
  sleep 20
done
```
Expect: `Completed` within 2–5 minutes.

**(g) Verify rows via DAX executeQueries**
```bash
curl -X POST \
  "https://api.powerbi.com/v1.0/myorg/groups/8545f3cb-4e2d-4985-bf31-79066248c9be/datasets/fb41970d-2beb-4ed9-9f82-35c6439b35ea/executeQueries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"queries":[{"query":"EVALUATE ROW(\"inv_rows\", COUNTROWS(INVENTORY_FCT_BALANCE), \"ext_rows\", COUNTROWS(EXTRACT_INVENTORY_CURRENT))"}]}'
```
Expect: both row counts > 0 (matching the 16,736 rows validated at the Snowflake layer per
[[pbi-xmla-model-changes]] § GP-208 Sub-step 1b Status).

### 7.3 Pass criteria

All of:
- (b) dry-run exit 0
- (d) apply exit 0, stdout shows `Added table` × 2 and `SaveChanges() complete`
- (f) refresh status `Completed`
- (g) both tables have rows > 0

If any step fails, the wrapper is not yet production-ready — do not merge; see §8 fallback.

---

## 8. Fallback plan (if the wrapper fails for an unexpected reason)

If the implementation session finds that TOM on .NET 8 cannot connect to GEP's PPU
XMLA endpoint despite the research above (e.g. an unknown capacity setting, a tenant-level
OAuth restriction, a corrupt TOM package that no known version fixes), the documented
**Option D** fallback is: Paul runs TE3 GUI manually. This is the current workaround from
[[pbi-xmla-model-changes]] § "Workaround: Paul runs TE3 GUI manually" — already tested
and known to work end-to-end. The skill's Sub-step 1b would revert to printing the manual
instructions and stopping, with Paul marking sandbox_validated manually after running the
script in TE3 GUI and refreshing via §H.

Option D is not the primary plan and should NOT be implemented proactively — only invoke
if the wrapper is confirmed broken in a way that isn't fixable within the implementation
session's scope. If it fires, file a new potential ticket in [[potential-tickets]] with
the specific failure mode so it can be investigated separately.

---

## 9. Wiki & tracker updates spec (for the implementation session, NOT this planning session)

Do not edit these files now — the implementation session will handle them after the
wrapper is merged and GP-208 passes validation.

### 9.1 `wiki/processes/deployment/pbi-xmla-model-changes.md`
Add a new section at the top of the "Future fix directions" area:
```markdown
## Resolved by pbi_model_apply wrapper (2026-04-??)

The TE3 CLI subprocess hang was **diagnosed, not fixed** — TE3 itself remains unusable
from a subprocess context. The resolution is a thin .NET 8 console wrapper
(`GEP/scripts/pbi_model_apply/`) that calls TOM directly via Roslyn CSharpScript, running
TE3-compatible C# scripts without launching TE3 at all. See
[[pbi-model-apply-wrapper]] for design; the wrapper ships as part of Phase 6 Option A.
```
Bump `updated:` date.

### 9.2 `wiki/processes/distributed-workflow/active/client-workflow-automation.md`
Append a new session-log entry for the implementation session (not this plan session —
this plan session's entry is added in §10 below).

### 9.3 `wiki/potential-tickets.md`
Move the `pbi_scan.py requires TE3 — TE2 hangs headless` entry from Open to Filed (with
a note: "Subsumed by [[pbi-model-apply-wrapper]]; pbi_scan.py still uses REST fallback;
future TE3-based scan work can ride on top of the wrapper's Roslyn+TOM approach"). Or
leave it Open but cross-link to the wrapper plan — the underlying need to fix
pbi_scan.py's TE3 path is a separate concern that the wrapper enables but does not
complete.

### 9.4 `wiki/processes/distributed-workflow/active/phase6-pbi-automation-plan.md`
Add a note under §3.10 §G: "**Revised 2026-04-23** — TE CLI path replaced by
pbi_model_apply wrapper per [[pbi-model-apply-wrapper]]. Connection-string construction
moves inside the wrapper; caller passes `--workspace`/`--dataset`/`--token` as discrete
args. Same §I token source, same exit-code-driven error handling at §G."

### 9.5 `wiki/index.md`
Under `## Processes > Deployment`, add:
```markdown
- [[pbi-model-apply-wrapper]] — Phase 6 Option A plan: thin .NET 8 console wrapper around TOM that runs TE3-compatible C# scripts via Roslyn. Resolves the TE3 CLI subprocess hang documented in [[pbi-xmla-model-changes]].
```

---

## 10. Planning-session log entry (apply immediately — §9.2 handles the implementation-session entry)

### 10.1 `client-workflow-automation.md` session log entry

Append to the session log section (near the top, above the 2026-04-22/23 entry):

```markdown
### 2026-04-23 — Phase 6 Option A planning session complete ✅ (Opus, xhigh effort)

- produced: [[pbi-model-apply-wrapper]] — authoritative implementation plan for a thin
  .NET 8 console wrapper (`GEP/scripts/pbi_model_apply/`) that applies PBI model scripts
  via TOM directly, replacing the hung TE3 CLI path.
- decisions:
  - **Technology:** .NET 8 console app; `Microsoft.AnalysisServices.NetCore.retail.amd64`
    (TOM) + `Microsoft.CodeAnalysis.CSharp.Scripting` (Roslyn). No MSOLAP, no WebView2,
    no GUI dependency — the thing that makes TE3 hang.
  - **Script API:** TE3 emulation layer (~80 LOC) exposing `AddTable`, `AddRelationship`,
    `SetExpression` extension methods. One documented syntax delta from TE3 GUI scripts:
    partition expression assignment becomes `.SetExpression(...)` because C# lacks
    extension properties. Two line edits in the existing `GP-208/pbi_model_script.cs`;
    future scripts use the new form from the start.
  - **Build/deploy:** source project checked in; `bin/` gitignored; Paul runs
    `dotnet build -c Release` once (~90s first time). Skill invokes
    `bin/Release/net8.0-windows/pbi_model_apply.exe`.
  - **CLI:** `--script / --workspace / --dataset / --token [--dry-run --timeout --verbose]`.
    Explicit exit codes (0 success, 1 script runtime, 2 auth, 3 connection, 4 compile,
    5 model locked, 6 invalid args, 99 unexpected) so §G can react appropriately.
  - **§G rewrite:** command line only — token acquisition, config reads, redaction,
    retry-on-401 all unchanged.
- highest-risk unknowns surfaced to Paul (see §11):
  1. `Microsoft.AnalysisServices.NetCore.retail.amd64` connecting to GEP's PPU XMLA with
     a bearer token — confirmed at the TOM API level, unconfirmed on *this specific
     capacity*; runtime-verifiable in ~30 seconds via dry-run then real apply.
  2. .NET 8 SDK presence on Paul's machine — likely true (TE3 ships .NET 8), but unchecked.
  3. Roslyn CSharpScript resolving extension methods without a `using` directive via
     `ScriptOptions.WithImports` — documented working pattern, no known blocker.
- no code changes in this session (planning only per the boot prompt).
- next: Sonnet implementation session booted from [[pbi-model-apply-wrapper]]. It can
  implement without asking clarifying questions if all three unknowns above resolve
  favourably in the first five minutes.
```

### 10.2 `wiki/log.md`

Append row:

```
| 2026-04-23 | plan | Option A planning session for Phase 6 PBI model apply wrapper complete. Produced [[pbi-model-apply-wrapper]] — authoritative spec for a .NET 8 console wrapper using `Microsoft.AnalysisServices.NetCore.retail.amd64` (TOM) + `Microsoft.CodeAnalysis.CSharp.Scripting` (Roslyn) to apply TE3-compatible C# scripts via XMLA from a subprocess context. Replaces the hung TE3 CLI path. Chose TE3 API emulation layer (extension methods `AddTable`, `AddRelationship`, `SetExpression`) over raw TOM or TMSL JSON to preserve TE3 script muscle memory; one documented syntax delta (partition `.Expression = x` → `.SetExpression(x)` because C# lacks extension properties). Build/deploy: source project at `GEP/scripts/pbi_model_apply/`, `bin/` gitignored, Paul runs `dotnet build -c Release` once. Explicit CLI interface and exit-code schema so §G reacts to auth/compile/lock errors distinctly. Fallback plan: Option D (Paul runs TE3 GUI manually, current workaround) stays documented for the tail case where TOM-on-.NET-8 unexpectedly cannot connect. End-to-end validation against GP-208 sandbox dataset is the acceptance test for the implementation session. Index entry added under Processes → Deployment. |
```

### 10.3 `wiki/index.md`

Under `## Processes > Deployment`, add the line from §9.5 above.

---

## 11. Highest-risk unknowns (for Paul to resolve before implementation session)

These are the calls where the plan makes a reasonable assumption but a wrong assumption
would cost the implementation session hours. All three are resolvable in <5 minutes each.

### 11.1 ✅ RESOLVED 2026-04-23 — GEP PPU capacity + MSAL + TOM on .NET 8 — end-to-end

**Confirmed 2026-04-23** (Sonnet + Paul live repro, `C:\Users\PaulRussell\tom-repro\`):

- `Microsoft.AnalysisServices.NetCore.retail.amd64` v19.84.x on .NET 8 **connects
  successfully** to `powerbi://api.powerbi.com/v1.0/myorg/GEP Sandbox Models`.
- Dataset `GEP_Sandbox_Current` found; model has **32 tables** (first 5 confirmed live).
- **Auth that works:** MSAL device-code with `pbiPublicClientId=ea0616ba-638b-4df5-95b9-636659ae5121`,
  `aud=https://analysis.windows.net/powerbi/api`. Token set via `server.AccessToken` API.
- **Auth that does NOT work:** `az account get-access-token` bearer token — the XMLA
  endpoint rejects it. Token's `appid=04b07795-...` (Azure CLI) is not an approved XMLA
  client. The rejection is silent from the auth perspective but surfaces as
  `AmoException: Authentication failed for all authenticators`. REST (§H) is unaffected —
  `az` tokens work fine for PBI REST calls.

**Implementation notes (confirmed):**
1. `using Microsoft.AnalysisServices` + `using Microsoft.AnalysisServices.Tabular` together
   make `Server` ambiguous. Use `Microsoft.AnalysisServices.Tabular.Server` fully-qualified.
2. `server.Databases["name"]` indexes by internal Analysis Services **ID** (a GUID-like
   string), **not** the display `Name`. Use
   `server.Databases.Cast<Database>().FirstOrDefault(d => d.Name == name)`.
3. `AccessToken` ctor signature: `(string token, DateTimeOffset exp, object userContext)` —
   use `DateTimeOffset`, not `DateTime`.

### 11.2 🟡 .NET 8 SDK presence

**Assumption:** `dotnet --list-sdks` shows an `8.0.*` line.

**Why it's a risk:** TE3 ships .NET 8 *runtime* (bundled), not necessarily the SDK. The
wrapper needs the SDK to `dotnet build`. Lightweight to fix (`winget install
Microsoft.DotNet.SDK.8`), but still a 3–5 minute detour for the implementation session
if it hits this.

**30-second pre-flight:** Paul runs `dotnet --list-sdks`. If no 8.0.* line, install
before the implementation session.

### 11.3 🟡 Roslyn CSharpScript + WithImports resolving extension methods

**Assumption:** `ScriptOptions.Default.WithImports("PbiModelApply")` brings the
`TabularExtensions` static class into scope so `Model.AddTable(...)` resolves without a
`using PbiModelApply;` directive inside the script body. (TE3 scripts have no usings; if
Roslyn requires the script to add `using PbiModelApply;` explicitly, that breaks the
zero-edit-from-TE3 ergonomic.)

**Why it's a risk:** Roslyn's `WithImports` is documented to import namespaces for **all**
member types including extension methods, but the interaction with static-class-defined
extensions in a Roslyn-scripting globals context has known edge cases in older Roslyn
versions. v4.11 should be fine; untested by Paul.

**Mitigation if it fails:** fall back to prepending `using PbiModelApply;` to every
script as it's loaded — one line added by the wrapper, transparent to the script author.
This is a one-line change to `Program.cs` and does not affect the rest of the design.
Only matters for syntactic sugar.

### 11.4 Exact repro snippet (belt & braces — Paul can run this now)

Save as `C:/tmp/tom-repro.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <PlatformTarget>x64</PlatformTarget>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AnalysisServices.NetCore.retail.amd64" Version="19.84.1" />
  </ItemGroup>
</Project>
```

Save as `C:/tmp/Program.cs`:

```csharp
using Microsoft.AnalysisServices.Tabular;

var token = Environment.GetEnvironmentVariable("PBI_TOKEN")
            ?? throw new Exception("set PBI_TOKEN env var");

var conn = "Data Source=powerbi://api.powerbi.com/v1.0/myorg/GEP Sandbox Models;" +
           "Initial Catalog=GEP_Sandbox_Current;" +
           "User ID=AzureAD;" +
           $"Password={token}";

using var server = new Server();
server.Connect(conn);
var db = server.Databases["GEP_Sandbox_Current"];
Console.WriteLine($"Connected. Model has {db.Model.Tables.Count} tables.");
server.Disconnect();
```

Run:
```
cd C:/tmp
export PBI_TOKEN=$(az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv)
dotnet run
```

Expected: `Connected. Model has N tables.` where N ≥ 15.

If that prints cleanly, the implementation session is de-risked — Tranches 3.1–3.8 of
this plan are straight line. If it throws, the exception message is the one thing needed
to decide whether Plan A is still viable or whether the session should pivot to Option B
(direct XMLA SOAP, [[pbi-xmla-model-changes]] § Future fix directions).

---

## 12. What this plan does NOT change

- `pbi_scan.py` stays REST-only (TE3 path remains `if False`-guarded). A future ticket
  can re-enable a scan backend built on the same TOM+Roslyn foundation if it becomes
  worth the cost; that's out of scope here.
- Phase 6 artefact schema — no changes. `script_path`, `script_hash`, `sandbox_validated`,
  etc. all stay as-is.
- Phase 6 Tranche D (prod auto-apply) — same §G call, transparent upgrade.
- `pbi_config.yaml` `tabular_editor_path` stays — `pbi_scan.py` still reads it.
- TE3 GUI as manual workflow — still the documented Option D fallback; manual-deploy
  path unchanged.

---

## See Also

- [[phase6-pbi-automation-plan]] — parent Phase 6 plan; this wrapper replaces §G's
  invocation layer only
- [[client-workflow-automation]] — workstream tracker; 2026-04-23 session log entry
- [[pbi-xmla-model-changes]] — the subprocess-hang diagnosis this plan resolves
- [[potential-tickets]] — "pbi_scan.py requires TE3" entry (loosely related, not closed
  by this plan)
- [[entities/tools/power-bi|Power BI]] — tool reference; XMLA automation section will
  gain a pbi_model_apply pointer post-implementation
- [[GP-208]] — the first ticket to validate the wrapper end-to-end
