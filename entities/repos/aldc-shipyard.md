---
tags: [entity, repo, automation, aldc, workflow-automation, shipyard]
aliases: [aldc-shipyard, shipyard repo, workflow automation repo]
sources: [processes/distributed-workflow/active/client-workflow-automation.md (Phase 7 design + Tranche H dogfood 2026-04-26)]
created: 2026-04-26
updated: 2026-04-29
---

# aldc-shipyard repo

> Renamed from `aldc-automation` on 2026-04-29. All references updated across repo, wiki, and `/gep-feature` skill.

Dedicated ALDC repo at `C:\Users\PaulRussell\repos\aldc-shipyard\` for client-workflow-automation infrastructure: deploy/validate scripts, PBI XMLA tooling, per-client manifests, and cross-repo configuration. Decoupled from `clients` and `connector` CI/CD branch chains so automation can iterate freely without polluting production environment branches.

> **Status (2026-04-29)**: **Implementation complete — Tranche H dogfood shipped.** Repo scaffolded, scripts migrated and refactored, `gep-feature` skill moved to user level and updated. Full GP-208 workflow ran end-to-end including rollback. See [[client-workflow-automation]] for session history.

## One-time machine setup

Run once after cloning on a new machine:
```
python scripts/setup.py
```
Handles: `.env` (Snowflake creds), `config/gep.yaml` (repo paths), `clients/GEP/pbi_config.yaml` (PBI workspace GUIDs — test/prod), `pbi_model_apply.exe` (dotnet build). Idempotent — skips steps already complete.

## Multi-root VS Code workspace

`aldc-shipyard.code-workspace` opens both `aldc-shipyard` and `clients` in one VS Code window. Open at session start for any feature work:
```
code aldc-shipyard.code-workspace
```

## Why a separate repo

Decided 2026-04-26 after the Tranche G dogfood (2026-04-26) hit a recurring dual-branch problem: deploy/validate scripts on `feature/.../workflow-automation`, SQL + ticket artifacts on `GP-208`. Switching branches mid-session removes scripts from disk; not switching means the scripts run against stale ticket artifacts. The fix is to take automation off feature branches in `clients` entirely.

Rationale:

- **Decoupled lifecycle** — automation iterates fast; `clients` and `connector` CI/CD chains stay clean.
- **Neutral ground for multi-repo orchestration** — scripts coordinate `clients`, `connector`, and `power_bi`; they don't belong to any one of them.
- **Scalable to other clients** — Fusion92 and future clients get config entries, not forks of `clients`.
- **No CI/CD risk** — break, redesign, and experiment freely without touching production branch chains.
- **Branch-agnostic** — scripts can target any feature branch in `clients` without checking it out.

## Repo layout

```
aldc-shipyard/
├── .env                              # gitignored — Snowflake creds (singleton, all clients)
├── .gitignore
├── README.md
├── config/
│   ├── gep.example.yaml              # committed — schema documentation
│   └── gep.yaml                      # gitignored — real machine-local values
├── scripts/
│   ├── deploy.py                     # Snowflake deploy (--client gep --env sandbox|test|prod)
│   ├── validate.py                   # Snowflake validation harness
│   ├── pbi_generate_columns.py       # TOM column-def emitter
│   ├── pbi_scan.py                   # PBI model scanner
│   ├── pbi_seed_sandbox.py           # Sandbox workspace bootstrapper
│   ├── data-share-capacity-query.py
│   └── pbi_model_apply/              # .NET XMLA wrapper
│       ├── *.cs                      # Program, ScriptGlobals, ExitCodes, TabularExtensions
│       ├── pbi_model_apply.csproj
│       ├── bin/                      # gitignored
│       └── obj/                      # gitignored
└── clients/
    └── GEP/
        ├── deploy_manifest/          # GP-208.yaml, GP-BENCH-01.yaml, ...
        ├── validate_manifest/        # GP-208.yaml, ...
        ├── pbi_config.example.yaml   # committed — schema documentation
        └── pbi_config.yaml           # gitignored — real PBI workspace/dataset GUIDs
```

## What lives where

| Layer | Location | Why |
|---|---|---|
| Skill (orchestrator) | `~/.claude/commands/gep-feature.md` | User-level, repo-agnostic |
| Scripts (deploy, validate, pbi_*) | `aldc-shipyard/scripts/` | Multi-repo neutral ground, off CI/CD chain |
| Manifests (deploy/validate YAML) | `aldc-shipyard/clients/<client>/` | Tooling artifacts; evolve with scripts |
| Cross-repo config | `aldc-shipyard/config/<client>.yaml` | Points scripts at correct local repos |
| Local PBI secrets | `aldc-shipyard/clients/<client>/pbi_config.yaml` | Gitignored, machine-local |
| Snowflake creds | `aldc-shipyard/.env` | Gitignored singleton |
| SQL files | `clients` repo (feature branch) | Part of the feature PR |
| Ticket artifacts (`artifact.yaml`, `notes.md`, `pbi_model_script.cs`, `pbi_model_columns.cs`, `rollback/`) | `clients/GEP/tickets/<ticket>/` (feature branch) | Belong with the SQL they describe; reviewed in the feature PR |

## Configuration model

Three layers of config, each with a clear owner:

### `.env` (shipyard repo root, gitignored, singleton)

Snowflake credentials shared across all clients on the same machine.

```
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_ACCOUNT=...
# optional:
SNOWFLAKE_ROLE=SYSADMIN
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_AUTHENTICATOR=snowflake
```

### `config/<client>.yaml` (gitignored, per-client, per-machine)

Structural config + machine-local repo paths. Two-file pattern: `gep.example.yaml` is committed as schema documentation; `gep.yaml` is gitignored and holds the real values.

```yaml
client: GEP

repos:
  clients: "C:/Users/PaulRussell/repos/clients"      # machine-local
  connector: "C:/Users/PaulRussell/repos/connector"  # optional until used
  power_bi: "C:/Users/PaulRussell/repos/power_bi"    # optional until used

clients_layout:                                      # paths inside repos.clients
  client_root: "GEP"
  warehouse_sql_dir: "GEP/snowflake/warehouse"
  tickets_dir: "GEP/tickets"

automation_layout:                                   # paths inside aldc-shipyard
  deploy_manifest_dir: "clients/GEP/deploy_manifest"
  validate_manifest_dir: "clients/GEP/validate_manifest"
  pbi_config_path: "clients/GEP/pbi_config.yaml"

snowflake:
  account_var: "SNOWFLAKE_ACCOUNT"                   # env var name; value in .env
  envs:
    sandbox:
      database_template: "SANDBOX_DG1_GEP_{ticket}"
      schema_template: "WAREHOUSE_TEST_{ticket}"
    test:
      database: "TEST_DG1_GEP"
      schema_template: "WAREHOUSE_TEST_{ticket}"
    prod:
      database: "PROD_DG1_GEP"
      schema: "WAREHOUSE"
  task_chain: "TASK_WAREHOUSE_ORDERLINE_0"
```

### `clients/<client>/pbi_config.yaml` (gitignored)

PBI workspace + dataset GUIDs and parameter names. Schema unchanged from current — see existing `pbi_config.example.yaml`. Sandbox IDs auto-populated by `pbi_seed_sandbox.py`; test/prod IDs filled by hand.

## Path resolution

The skill (`~/.claude/commands/gep-feature.md`) resolves the shipyard repo path via env-var-with-convention:

```bash
SHIPYARD_HOME="${ALDC_SHIPYARD_HOME:-$HOME/repos/aldc-shipyard}"
```

- Default: `~/repos/aldc-shipyard` (matches Paul's repo convention).
- Escape hatch: set `ALDC_SHIPYARD_HOME` env var to override.

Scripts themselves resolve their own repo location via `Path(__file__).resolve().parent.parent` (scripts live one level deep at `scripts/`), then accept `--client gep` to find the matching `config/gep.yaml`. No env var pollution at the script layer.

Skill-emitted invocations look like:

```
python "$SHIPYARD_HOME/scripts/deploy.py"   --client gep --env sandbox --ticket GP-208 --check-share
python "$SHIPYARD_HOME/scripts/validate.py" --client gep --env sandbox --ticket GP-208 --save-results
```

## Connector integration pattern (sketch only — not built)

When connector deploy steps land:

- Connector scripts go in `aldc-shipyard/scripts/` with conventional naming (`connector_deploy.py`, `connector_validate.py`). Flat scripts dir; no subfolders until the count justifies it.
- Per-client connector manifests at `aldc-shipyard/clients/<client>/connector_manifest/`, parallel to `deploy_manifest/`.
- `config/<client>.yaml` grows a `connector:` section (`docker_image`, `prefect_workspace`, etc.) when needed. `repos.connector` is already there.
- Likely a separate Claude Code skill (`connector-feature.md`) — connector lifecycle is Docker/Prefect-shaped, fundamentally different from the Snowflake+PBI shape `gep-feature` orchestrates. Don't grow `gep-feature.md` to cover both. Decision deferred to when the work actually arrives.

This isn't a build commitment — just enough structure for the addition not to require a restructure.

## See Also

- [[client-workflow-automation]] — workstream tracker, Phase 7 design session log
- [[workflow-automation]] — project-level design doc
- [[clients-repo]] — what stays here (SQL + ticket artifacts on feature branches)
- [[connector]] — future home for connector deploy steps via this repo's scripts
- [[entities/repos/power_bi|power_bi (repo)]] — `.pbix` binary store; `pbi_seed_sandbox.py` drops a seed `.pbix` from here
- [[gep-snowflake-pbi-deployment]] — manual runbook this automation replaces
- [[pbi-xmla-automation]] — XMLA wrapper that lives at `aldc-shipyard/scripts/pbi_model_apply/`
- [[phase6-pbi-automation-plan]] — Tranche G dogfood that surfaced the dual-branch problem
- [[GEP]] — first client; canonical case for the automation
