---
tags: [entity, repo, power_bi, powerbi, pbix, reports, retail, lfs, git-lfs, binary-artefacts]
aliases: [power_bi, power_bi repo, ALDC power_bi repo, pbix repo, pbix-artifact-repo, power-bi-repo]
sources:
  - repos/power_bi/.gitattributes
  - repos/power_bi/.gitignore
  - "repos/power_bi/large file storage.txt"
  - repos/power_bi/common/Retail/Customer Lifetime Value/retail_customer_lifetime_value.json
  - "repos/power_bi/common/Retail/Daily Sales/2022-06/daily_sales.json"
  - "repos/power_bi/common/Retail/KPI Manager/2022-06/kpi_manager.json"
  - "repos/power_bi/common/Retail/Product Benchmark/2022-06/cosmos_report_template.json"
  - repos/power_bi/templates/cosmos_report_template.json
  - repos/power_bi/templates/theme.json
  - "repos/power_bi git log --all (353 commits, 2022-03 to 2026-03-06)"
  - "repos/power_bi git lfs ls-files (94 LFS objects)"
created: 2026-04-20
updated: 2026-04-20
---

# power_bi (repo)

> **Disambiguation — two separate pages cover "Power BI" in the wiki:**
>
> - **[[entities/repos/power_bi|power_bi (repo)]]** (this page) — the GitHub-hosted artefact store `ALDC-io/power_bi.git` containing the actual `.pbix` files. Its layout, its LFS story, its git cadence, what reports live where, which client folders are live vs. legacy, how a developer clones-edits-publishes.
> - **[[entities/tools/power-bi|Power BI (tool)]]** — the Microsoft product itself. Data flow diagrams, workspace config, model refresh process, connection parameters, report template conventions, granting Excel access. All usage-level content lives there, not here.
>
> **Slug note:** `power_bi.md` (underscore — repo name) vs. `power-bi.md` (hyphen — tool page). The divergence is intentional and matches the file-naming on each target. An Obsidian wikilink using `[[Power BI]]` resolves to the tool page; `[[entities/repos/power_bi]]` resolves to this repo page.

The `power_bi` repo is the binary-artefact store for ALDC's Power BI reports — 94 `.pbix` files, 3 `.pbit` template files, a handful of `.pptx` style guides, 6 CosmosDB `report`-document JSON companions, and 1 `theme.json`, organised under `common/`, `custom/`, `internal/`, `sales/`, and `templates/`. There is no source code. Everything is LFS-backed. Git remote: `https://github.com/ALDC-io/power_bi.git`. Default branch: `main`. The repo has accumulated 353 commits across 7 unique authors since 2022-03; its total LFS footprint is approximately 16 GB. The two actively maintained client folders are `custom/GEP/` (most recent commit 2026-03-06, 20 dated snapshots, ~7 GB) and `custom/FUSION_92/` (most recent commit 2025-12-30, 13 dated snapshots); the other client folders are legacy, frozen, or inactive. For everything about how Power BI the tool works — connection parameters, workspace mapping, model refresh — see [[entities/tools/power-bi|Power BI (tool)]].

---

## Repo layout

```
power_bi/
├── .gitattributes                  # one line: *.pbix filter=lfs diff=lfs merge=lfs -text
├── .gitignore                      # boilerplate Python gitignore (vestigial — no Python here)
├── large file storage.txt          # ONE-LINE note: LFS required. Repo's only in-repo doc.
├── common/
│   └── Retail/                     # ALDC Retail standard report set (starting point for new retail clients)
│       ├── Customer Lifetime Value/    # 1 .pbix (820 KB) + .pptx style guide + CosmosDB report JSON
│       ├── Daily Sales/                # 3 dated subfolders: 2022-01, 2022-03, 2022-06
│       ├── Finance Model/              # 1 .pbix (260 MB) + Date Logic Checker.xlsx
│       ├── Inventory Planner/          # 1 dated subfolder: 2022-01
│       ├── KPI Manager/                # 5 dated subfolders: 2022-03, 2022-06, 2023-10, 2023-11, 2024-07
│       └── Product Benchmark/          # 1 dated subfolder: 2022-06
├── custom/                         # Per-client bespoke models
│   ├── ALDC_FINANCE/               # 2 .pbix (Profitability Model + test); last commit 2024-07
│   ├── ALDC_SALES/                 # 1 .pbix — Netsuite Ops Model (543 MB); last commit 2025-08-08
│   ├── BOOK_DEPOT/                 # 2 dated sales-model subfolders (~300 MB each); last commit 2022-11
│   ├── DISH_DUER/                  # 20 dated combined_model_* / sales_model_* subfolders + executive_snapshot + 3 standalone .pbix; ~5.5 GB total; last commit 2024-08-26 (client inactive)
│   ├── FUSION_92/                  # 13 dated subfolders (2024_01 … 2025_12 + Original); all named "Activation Model.pbix"; last commit 2025-12-30 (active client)
│   ├── GEP/                        # 20 dated subfolders (2024_05 … 2026_03 "Data Model" + 2× Daily Sales); last commit 2026-03-06 (active client)
│   └── KIT_ACE/                    # 7 subfolders: Daily Sales, Finance Model (2021-10 / 2021-11 / 2022-07 / 2024-10 / 2025-05), Netsuite Data Search; last commit 2025-06-02 (client inactive per wiki — see § Report Catalogue for contradiction callout)
├── internal/                       # ALDC-internal models (not client-facing)
│   ├── ALDC_ENG/                   # 4 .pbix — Account Summary (Prod/Quality/Test) + Account and Template Summary; last commit 2024-12-11
│   └── aldc_demo/                  # 3 .pbix (Architecture, Daily Sales, Data Model) + 6 style-guide .pptx/.png; demo assets
├── sales/                          # Pre-sales prospect demos (one-off, frozen)
│   ├── 9TH_CO/Cluster Analysis/           # 1 .pbix — Ninth_Co Sample; last commit 2022-08-05
│   ├── APEX_BRASIL/Export Demo/           # 1 .pbix — APEX_BRASIL Export Demo (249 MB); last commit 2022-08-05
│   └── KIT_ACE/Product Pairing Recommender/  # 1 .pbix + .pptx wireframe — pre-sales demo for KIT_ACE (distinct from live custom/KIT_ACE/ reports)
└── templates/                      # Power BI template .pbix files + theme
    ├── Eclipse Power BI Template 2022-03.pbix      # ~820 KB (stale — canonical in Nextcloud)
    ├── Eclipse Power BI Template 2022-06.pbix      # ~820 KB (stale)
    ├── Eclipse Power BI Template 2022-07.pbix      # ~823 KB (stale)
    ├── Style Guide.pptx                            # Template style guide
    ├── cosmos_report_template.json                 # Skeleton CosmosDB report document
    └── theme.json                                  # PBI visual theme (SlicerTemplate, DIN Light fonts)
```

### Folder conventions

**Four top-level roles:**

| Folder | Role |
|---|---|
| `common/` | Shared starter content — the Retail standard report set. Used as the starting point when spinning up a new retail client. |
| `custom/<CLIENT>/` | Per-client bespoke models. Each client is a subfolder. |
| `internal/` | ALDC-staff-only models (eng observability, demo assets). |
| `sales/` | Pre-sales prospect demos — one-off, mostly frozen. |
| `templates/` | PBI template `.pbix` files + theme JSON. Stale in-repo snapshot; canonical copies live in `Nextcloud\Customers\Style Guides`. |

**Dated-folder snapshot convention:** Inside `custom/GEP/`, `custom/FUSION_92/`, `custom/DISH_DUER/`, and `custom/KIT_ACE/Finance Model (…)/`, most subfolders are named `YYYY_MM` or `(YYYY-MM)`. The most-recent dated folder in each client is the live/current model; older dated folders are frozen snapshots retained for rollback and comparison. This is a **manual snapshot convention**, not a git feature — operators create a new dated folder when cutting a new model revision.

**Intra-repo name collisions worth noting:**

- `custom/KIT_ACE/` holds live production models. `sales/KIT_ACE/` is a frozen pre-sales "Product Pairing Recommender" demo — completely different artefact.
- `templates/` in this repo is a stale snapshot. `Nextcloud\Customers\Style Guides` is the canonical, live template location.
- `custom/ALDC_FINANCE/` is an internal ALDC model placed under `custom/` rather than `internal/` — an inconsistency with `internal/ALDC_ENG/`.

**Naming inconsistencies (documented as-is; do not rename):**

- DISH_DUER uses both `combined_model_2023-06` (hyphen) and `combined_model_2023_09` (underscore).
- KIT_ACE uses `Finance Model (YYYY-MM)` with parentheses.
- GEP uses `YYYY_MM Data Model` with a space-separated type suffix.
- GEP has a `2025_01b Data Model` folder — the `b` suffix is an intra-month second revision; unique to that folder.

No `docs/`, no `README.md`, no `.github/`, no CI, no workflows, no tests, no scripts. The only in-repo documentation is `large file storage.txt`, a one-sentence file: *"Large file storage MUST be enabled on the client where you intend to use this repository — https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage"*

`.gitignore` is a boilerplate Python gitignore (ignoring `__pycache__`, `*.py[cod]`, `.venv`, etc.) — inherited from a template, vestigial since no Python lives here.

---

## Architecture

**There is no code architecture in this repo.** `power_bi` is a binary artefact store. Architecture at the `.pbix` level — semantic model tables, measures, calculated columns, visuals — lives inside each binary and is only inspectable by opening the file in Power BI Desktop. Nothing here is grep-able, diffable, or CI-testable in the conventional sense.

**The repo's organising principle is the folder hierarchy.** Five top-level directories (`common/`, `custom/`, `internal/`, `sales/`, `templates/`) partition artefacts by role. Within each client folder, dated subfolders function as a manual snapshot history — an operator copies the current model into a new `YYYY_MM` folder when cutting a revision.

**No in-repo semantic model diff.** Because `.pbix` is binary, `git diff` on a `.pbix` returns a single LFS pointer line change. Reviewing a change requires opening both versions in PBI Desktop side-by-side. This is a well-known `.pbix` limitation; the migration to `.pbip` (Power BI Project folder format) is the industry-standard fix and is the biggest modernisation opportunity for this repo — see § Tech Debt.

**Three repo-level design decisions:**

1. **Folder-per-client under `custom/`** rather than branch-per-client. Switching between clients is a filesystem `cd`, not a `git checkout`. Simpler for Power BI analysts who understand folders better than branches.
2. **Dated-snapshot folders** (`YYYY_MM`) rather than git tags or branches for version history. Trade-off: lower cognitive overhead for non-engineer operators; cost is repo bloat (every snapshot is a full new LFS object — hundreds of MB per revision).
3. **All `.pbix` on LFS from day one.** `.gitattributes` contains exactly one line: `*.pbix filter=lfs diff=lfs merge=lfs -text`. Without this the repo would be unusable on GitHub (1 GB file-size limit without LFS).

**Tech stack at the repo level:** Git + Git LFS (GitHub-hosted). Nothing else. All Power-BI-the-tool stack information (desktop version, PBI Service, workspaces, gateway, datasets, refresh) belongs on [[entities/tools/power-bi|Power BI (tool)]] — this page links out rather than repeat.

---

## Data Flow

`power_bi` sits in the middle of the ALDC data pipeline — downstream of Snowflake and upstream of the Power BI Service.

```
Snowflake REPORT_COMMON.*       ◄── warehouse deploy (clients repo § snowflake/)
        │
        ▼
(optional) SQL Server + SSMS    ◄── GEP partition runs (custom/GEP/*.pbix)
        │
        ▼
.pbix semantic model            ◄── THIS REPO (common/ + custom/ + internal/)
        │                           Per-file Snowflake-connector M-queries
        │                           Per-file CosmosDB-fed Glossary + report-id
        │                           (cosmos_report_template.json / daily_sales.json / …)
        ▼
Power BI Service workspace      ◄── Publish (via Power BI Desktop, manual)
        │                           GEP: "GEP Test Models" + "Production"
        │                           FUSION92: Fusion92-specific workspace
        ▼
Client user in Excel or web     ◄── tool page § Granting Excel Model Access
```

**Inbound data sources per `.pbix` group:**

- **Snowflake `REPORT_COMMON.*` views** — the majority of models (GEP, Fusion92, KIT_ACE, DISH_DUER). The native Power BI Snowflake connector; M-query source is environment-specific (see tool page § Connection Parameters).
- **Intermediate SQL Server via [[SSMS]]** — GEP only, for partition and reprocessing runs. The GEP `Data Model.pbix` files in `custom/GEP/20YY_MM Data Model/` may point at a SQL Server intermediate layer rather than Snowflake directly (per tool page: "data usually passes through a SQL Server layer edited via SSMS in between").
- **NetSuite direct** — ALDC_SALES, ALDC_FINANCE, KIT_ACE Finance Model, KIT_ACE Netsuite Data Search. Direct ODBC or REST ingestion; not via Snowflake.
- **CosmosDB report document** — not a data source for the model's row data, but the source of the PBI template's Glossary entries (per tool page § Report Template). The 6 `*.json` files committed to this repo are frozen snapshots of those CosmosDB documents.

**Outbound:** `.pbix` files do not "flow out" from the repo — a developer opens the file in PBI Desktop and clicks File → Publish. For production deploy runbooks see [[gep-snowflake-pbi-deployment]] (GEP-specific) and [[model-deploy-production]] (generic). Do not replicate runbook steps here.

**Secret refresh** — [[powerbi-secret-refresh]] documents Azure AD client-secret rotation for the DISH_DUER / FUSION92 / GEP / KIT_ACE Power BI App Registrations. Those secrets are used by the PBI Service, not the `.pbix` files themselves, but the runbook is relevant to anyone publishing to these workspaces.

For the full ALDC data pipeline context, see [[data-pipeline-flow]].

---

## Report Catalogue

The centrepiece section. Per-folder, per-`.pbix` inventory. Sizes are from `git lfs ls-files --size`; last-commit dates are from `git log --pretty=format:"%ad" --date=short -- <path>`. Status classifications: **Active** (recent meaningful commits), **Snapshot** (frozen but retained for rollback), **Stable baseline** (static reference set), **Legacy** (superseded, client active or unknown), **Frozen** (client inactive or demo), **Stale** (superseded by Nextcloud or similar).

### Table 5a — `templates/`

| File | Last modified | LFS size | Status | Notes |
|---|---|---|---|---|
| `templates/Eclipse Power BI Template 2022-03.pbix` | 2022-03 | 820 KB | **Stale** | Canonical templates live in `Nextcloud\Customers\Style Guides`. |
| `templates/Eclipse Power BI Template 2022-06.pbix` | 2022-06 | 820 KB | Stale | Same — superseded by Nextcloud copy. |
| `templates/Eclipse Power BI Template 2022-07.pbix` | 2022-07 | 823 KB | Stale | Same. Most recent in-repo template; still 4 years old. |
| `templates/Style Guide.pptx` | 2022 | small | Reference | Style-guide deck; non-LFS. |
| `templates/cosmos_report_template.json` | 2022 | ~1.4 KB | Readable | Skeleton CosmosDB report document. Contains "Book Outlet Campaign Demo" as its literal example — a 9thco demo JSON reused as skeleton. |
| `templates/theme.json` | 2022 | ~356 B | Readable | PBI visual theme — `SlicerTemplate`, DIN Light font family, black-on-white. |

**Note:** the in-repo `templates/` folder is a stale snapshot. **Start from the Nextcloud copy, not from these files.** See § Tech Debt item 6.

### Table 5b — `common/Retail/`

The ALDC retail standard report set — starting point when spinning up a new retail client. Last folder-level commit: 2024-08-13. Treat as a stable baseline, not living content.

| Path | Last commit | LFS size | Status | Notes |
|---|---|---|---|---|
| `common/Retail/Customer Lifetime Value/Retail - Customer Lifetime Value.pbix` | 2023-03 | 820 KB | Stable baseline | Paired with `retail_customer_lifetime_value.json` (CosmosDB doc: name "Customer Lifetime Value", industry "Retail", client_owner Justin Cook @ 9thco.com, dev_owner Sean O'Grady, 1-entry glossary). |
| `common/Retail/Daily Sales/2022-01/Daily Sales.pbix` | 2022-01 | 4.1 MB | Legacy | Superseded by 2022-06 variant. |
| `common/Retail/Daily Sales/2022-03/Daily Sales.pbix` | 2022-03 | 1.3 MB | Legacy | Superseded by 2022-06. |
| `common/Retail/Daily Sales/2022-06/Daily Sales.pbix` | 2022-06 | 4.4 MB | **Current shared starter** | Paired with `daily_sales.json` (CosmosDB doc: template_version "2022-06", 9-entry glossary, 20-key config dict, status "In Progress"). |
| `common/Retail/Daily Sales/2022-06/Daily Sales Mobile.pbix` | 2022-06 | 139 KB | Current shared starter (mobile) | Mobile variant of the 2022-06 Daily Sales report. |
| `common/Retail/Finance Model/Finance Model.pbix` | 2022-era | 260 MB | Stable baseline | Large file. Paired with `Date Logic Checker.xlsx`. |
| `common/Retail/Inventory Planner/2022-01/Inventory Planner.pbix` | 2022-01 | 302 MB | Stable baseline | Largest file in `common/`. Only 2022-01 version exists. |
| `common/Retail/KPI Manager/2022-03/KPI Manager.pbix` | 2022-03 | 1.4 MB | Legacy | Superseded by 2022-06 and later. |
| `common/Retail/KPI Manager/2022-06/KPI Manager.pbix` | 2022-06 | 1.5 MB | Reference (has JSON companion) | Paired with `kpi_manager.json` (CosmosDB doc: 12-entry glossary incl. AOV / AUR / Conversion % / Returns % / UPT, status "Review by Client"). |
| `common/Retail/KPI Manager/2023-10/Retail KPI Manager.pbix` | 2023-10 | 1.5 MB | Stable baseline | |
| `common/Retail/KPI Manager/2023-11/Retail KPI Manager.pbix` | 2023-11 | 1.5 MB | Stable baseline | |
| `common/Retail/KPI Manager/2024-07/KPI Manager.pbix` | 2024-07 | 1.6 MB | **Current shared starter** | Most recent KPI Manager variant; last meaningful revision in this folder. |
| `common/Retail/Product Benchmark/2022-06/Product Benchmark.pbix` | 2022-06 | 7.4 MB | Stable baseline | Paired with `cosmos_report_template.json` (9thco "Book Outlet Campaign Demo") + `Style Guide.pptx`. |

Historical consumers of this starter set include [[kit-ace]], [[dish-duer]], [[book-depot]], and [[GEP]].

### Table 5c — `custom/GEP/` (most active folder)

GEP is the repo's most active and deepest-versioned client: 20 dated subfolders spanning 23 months, monthly-to-bi-monthly cadence, ~7 GB LFS total. The working pattern: create `YYYY_MM Data Model/`, copy prior-month `.pbix` in, edit in PBI Desktop, commit. Superseded months are kept for rollback. Commit messages often reference GP-ticket IDs.

| Folder | Last commit | LFS size | Status | Notes |
|---|---|---|---|---|
| `custom/GEP/2024_05 Data Model/` | 2024-05 | 480 MB | Snapshot | |
| `custom/GEP/2024_07 Data Model/` | 2024-07 | 512 MB | Snapshot | |
| `custom/GEP/2024_08 Daily Sales/` | 2024-08 | 3.8 MB | Snapshot | GEP's daily-sales side-model (distinct from the main Data Model). |
| `custom/GEP/2024_09 Daily Sales/` | 2024-09 | 3.8 MB | Snapshot | |
| `custom/GEP/2024_09 Data Model/` | 2024-09 | 184 MB | Snapshot | "Remove extra model and update September model with unhidden marketing measures." |
| `custom/GEP/2024_10 Data Model/` | 2024-10 | 224 MB | Snapshot | |
| `custom/GEP/2024_11 Data Model/` | 2024-11 | 244 MB | Snapshot | |
| `custom/GEP/2024_12 Data Model/` | 2025-01 | 261 MB | Snapshot | Last-touched Jan 2025 — multi-month rev cycle. |
| `custom/GEP/2025_01 Data Model/` | 2025-01 | 266 MB | Snapshot | |
| `custom/GEP/2025_01b Data Model/` | 2025-03 | 352 MB | Snapshot (intra-month b-variant) | The `b` suffix = second revision within the same month; unique to this folder. |
| `custom/GEP/2025_02 Data Model/` | 2025-03 | 357 MB | Snapshot | |
| `custom/GEP/2025_03 Data Model/` | 2025-03 | 353 MB | Snapshot | |
| `custom/GEP/2025_04 Data Model/` | 2025-04 | 361 MB | Snapshot | Commit: `GP-76-asin-granularity-and-sessions-updates`. Cross-ref: [[tickets/gep/GP-197]] — GP-76 page does not exist in wiki (wiki gap). |
| `custom/GEP/2025_05 Data Model/` | 2025-05 | 361 MB | Snapshot | Commit: `GP-87`. GP-87 page does not exist in wiki (wiki gap). |
| `custom/GEP/2025_06 Data Model/` | 2025-06 | 473 MB | Snapshot | |
| `custom/GEP/2025_07 Data Model/` | 2025-07 | 639 MB | Snapshot | Largest GEP model to date. |
| `custom/GEP/2025_09 Data Model/` | 2025-09 | 531 MB | Snapshot | |
| `custom/GEP/2025_10 Data Model/` | 2025-10 | 542 MB | Snapshot | Commit: "Last Sale Date — moved to SQL." Confirms SSMS-layer dependency. |
| `custom/GEP/2025_12 Data Model/` | 2026-02 | 332 MB | Snapshot | Created 2025-12; last-touched 2026-02 ("Update DTC field visibility" / "Add DTC fee"). |
| `custom/GEP/2026_03 Data Model/` | **2026-03-06** | 346 MB | **CURRENT LIVE MODEL** | Most recently touched file in the entire repo. Commit: "update power bi model for gp-169." Cross-ref: [[tickets/gep/GP-169]]. Author: Paul Russell. |

Active authors on `custom/GEP/`: `aldc-karenprete`, `aldc-stevendeutekom`, `aldc-braydenmarshall`, `Paul Russell` (only the 2026-03-06 commit is Paul's). Cross-reference [[GEP]] (client page).

### Table 5d — `custom/FUSION_92/` (active client)

13 total snapshots; monthly-to-quarterly cadence. All models are named `Activation Model.pbix`. File sizes grow steadily (~3 MB → ~25 MB) as fields are added. Cross-reference [[fusion92]] and [[dax-ai]] (DAX AI dashboard — Activation Model is the centrepiece).

| Folder | Last commit | LFS size | Status | Notes |
|---|---|---|---|---|
| `custom/FUSION_92/Original/` | 2024-01 | 3.0 MB | Frozen origin | Earliest Activation Model. |
| `custom/FUSION_92/2024_01/` | 2024-01 | 3.6 MB | Snapshot | |
| `custom/FUSION_92/2024_04/` | 2024-04 | 3.5 MB | Snapshot | |
| `custom/FUSION_92/2024_06/` | 2024-06 | 4.1 MB | Snapshot | |
| `custom/FUSION_92/2024_07/` | 2024-07 | 4.3 MB | Snapshot | |
| `custom/FUSION_92/2024_09/` | 2024-09 | 5.6 MB | Snapshot | |
| `custom/FUSION_92/2024_10/` | 2024-10 | 5.7 MB | Snapshot | |
| `custom/FUSION_92/2024_12/` | 2025-01 | 9.8 MB | Snapshot | |
| `custom/FUSION_92/2025_01/` | 2025-01 | 13 MB | Snapshot | |
| `custom/FUSION_92/2025_03/` | 2025-03 | 13 MB | Snapshot | |
| `custom/FUSION_92/2025_04/` | 2025-04 | 14 MB | Snapshot | |
| `custom/FUSION_92/2025_05/` | 2025-12 | 14 MB | Snapshot (re-touched 2025-12) | Folder name `2025_05`; last commit Dec 2025. |
| `custom/FUSION_92/2025_12/` | **2025-12-30** | 25 MB | **CURRENT LIVE MODEL** | Commit: "Hide new fields in platform table." |

Active authors: `aldc-karenprete`, `aldc-stevendeutekom`.

### Table 5e — `custom/DISH_DUER/` (largest folder, inactive client)

DISH_DUER is the repo's largest client by LFS footprint (~5.5 GB across 20 subfolders) and also the most legacy — last commit 2024-08-26, client now in `entities/clients/inactive/`. See [[dish-duer]]. **Archival candidate.** Note naming inconsistency between `combined_model_2023-06` (hyphen) and later `combined_model_2023_09` (underscore).

| Folder | Last commit | LFS size | Filename | Status |
|---|---|---|---|---|
| `custom/DISH_DUER/Customer Value 2022-01.pbix` | 2022-01 | 24 MB | standalone .pbix | Frozen |
| `custom/DISH_DUER/Daily Sales - DTC.pbix` | 2022 | 3.0 MB | standalone .pbix | Frozen |
| `custom/DISH_DUER/Daily Sales - Wholesale.pbix` | 2022 | 3.0 MB | standalone .pbix | Frozen |
| `custom/DISH_DUER/sales_model_2022_06/` | 2022-06 | 43 MB | `Sales Model.pbix` | Frozen |
| `custom/DISH_DUER/sales_model_2023_01/` | 2023-01 | 75 MB | `Sales Model.pbix` | Frozen |
| `custom/DISH_DUER/sales_model_2023_02/` | 2023-02 | 78 MB | `Sales Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2023_03/` | 2023-03 | 313 MB | `Combined Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2023_04/` | 2023-04 | 324 MB | `Combined Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2023_05/` | 2023-05 | 327 MB | `Combined Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2023-06/` | 2023-06 | 510 MB | `Combined Model.pbix` | Frozen (hyphenated folder name — naming inconsistency) |
| `custom/DISH_DUER/combined_model_2023-07/` | 2023-07 | 466 MB | `Combined Model.pbix` | Frozen (hyphenated) |
| `custom/DISH_DUER/combined_model_2023_08/` | 2023-08 | 350 MB | `Combined Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2023_09/` | 2023-09 | 426 MB | `Combined Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2023_10/` | 2023-10 | 465 MB | `Combined Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2023_11/` | 2023-11 | 521 MB | `Sales Model (Types).pbix` | Frozen (filename diverges from folder-series) |
| `custom/DISH_DUER/combined_model_2024_02/` | 2024-02 | 588 MB | `Sales Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2024_04/` | 2024-04 | 559 MB | `Sales Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2024_06/` | 2024-06 | 591 MB | `Sales Model.pbix` | Frozen |
| `custom/DISH_DUER/combined_model_2024_08/` | **2024-08-26** | 612 MB | `Sales Model.pbix` | **Latest DISH_DUER model (frozen)** — last DISH_DUER activity |
| `custom/DISH_DUER/executive_snapshot/` | 2024-08 | 2.6 MB + 137 KB (mobile) | `Executive Snapshot.pbix` + `Executive Snapshot Mobile.pbix` | Frozen |

### Table 5f — `custom/KIT_ACE/` (legacy client — see contradiction note)

> **Status: legacy / frozen (confirmed).** Paul Russell confirmed 2026-04-20: KIT_ACE is an **inactive** client — the 2025-06 repo activity (last Finance + Inventory Model commit) reflects the final report update before the client went inactive. Reports are retained in the repo but are not actively maintained. Same legacy/frozen classification as DISH_DUER and BOOK_DEPOT. The wiki client page `entities/clients/inactive/kit-ace.md` is correctly classified as inactive; no update to that page is needed.

**Filename convention note:** `Finance Model DG1 2022-07.pbix` retains "2022-07" in the filename even though the file was modified through 2025. Interpret as a "template-version stamp" — the filename names the original PBI template version, not the last-modified date.

| Folder | Last commit | LFS size | Status | Notes |
|---|---|---|---|---|
| `custom/KIT_ACE/Daily Sales/Daily Sales.pbix` + `Daily Sales Mobile.pbix` | 2024-05 | 4.8 MB + 136 KB | Frozen | |
| `custom/KIT_ACE/Finance Model (2021-10)/Finance Model.pbix` | 2021-10 | 83 MB | Frozen origin | Earliest Finance Model. |
| `custom/KIT_ACE/Finance Model (2021-11)/Finance Model 20211014.pbix` | 2021-11 | 125 MB | Frozen | |
| `custom/KIT_ACE/Finance Model (2022-07)/Finance Model DG1 2022-07.pbix` | 2022-07 | 99 MB | Frozen | |
| `custom/KIT_ACE/Finance Model (2024-10)/Finance Model DG1 2022-07.pbix` | 2024-10 | 117 MB | Frozen | |
| `custom/KIT_ACE/Finance Model (2025-05)/Finance Model DG1 2022-07.pbix` + `Inventory Model DG1 2022-07.pbix` | **2025-06-02** | 118 MB + 147 MB | **Frozen (last update before client went inactive)** | Last report update before KIT_ACE went inactive (confirmed Paul, 2026-04-20). Contains both Finance and Inventory models. |
| `custom/KIT_ACE/Netsuite Data Search/Netsuite Data Search.pbix` | 2024-04 | 1.7 MB | Frozen | Standing NetSuite reference model. |

### Table 5g — `custom/BOOK_DEPOT/` (inactive, frozen)

Client inactive per [[book-depot]] (in `entities/clients/inactive/`). No activity since 2022-11-21. Archival candidate.

| Folder | Last commit | LFS size | Status | Notes |
|---|---|---|---|---|
| `custom/BOOK_DEPOT/Sales Model/Sales Model.pbix` | 2022-10 | 298 MB | **Frozen** | |
| `custom/BOOK_DEPOT/Sales Model 2022-10/Sales Model.pbix` | 2022-11 | 305 MB | **Frozen** | Latest BOOK_DEPOT model; last touched 2022-11-21. |

### Table 5h — `custom/ALDC_FINANCE/` and `custom/ALDC_SALES/` (internal)

| Path | Last commit | LFS size | Status | Notes |
|---|---|---|---|---|
| `custom/ALDC_FINANCE/Profitability Model.pbix` | 2024-07-10 | 2.6 MB | **Legacy** | Internal ALDC profitability reporting. |
| `custom/ALDC_FINANCE/Profitability Model Test.pbix` | 2024-07 | 2.5 MB | Legacy | Test variant paired with above. |
| `custom/ALDC_SALES/Netsuite Ops Model.pbix` | **2025-08-08** | 543 MB | **Active (internal)** | Internal ALDC sales ops. Commit: "add netsuite sales ops demo." 543 MB — second-largest file in the repo after GEP 2025_07. |

Note: `custom/ALDC_FINANCE/` is an ALDC-internal model living under `custom/` rather than `internal/`. Inconsistent with `internal/ALDC_ENG/`. Documented as-is; do not move.

### Table 5i — `internal/`

| Path | Last commit | LFS size | Status | Notes |
|---|---|---|---|---|
| `internal/ALDC_ENG/Account and Template Summary.pbix` | 2024-12-11 | 293 MB | **Legacy** | Internal eng observability — Eclipse accounts + templates (likely reads from CosmosDB per [[cosmosdb-schema]]). |
| `internal/ALDC_ENG/Account Summary Prod Canada DG1.pbix` | 2024-12-11 | 125 MB | Legacy | Per-deployment-group summary. See [[deployment-groups]]. |
| `internal/ALDC_ENG/Account Summary Quality Canada DG1.pbix` | 2024-12-11 | 1.4 MB | Legacy | |
| `internal/ALDC_ENG/Account Summary Test Canada DG1.pbix` | 2024-12-11 | 38 MB | Legacy | |
| `internal/aldc_demo/Architecture.pbix` | pre-2024 | 4.1 MB | **Frozen (demo)** | |
| `internal/aldc_demo/Daily Sales.pbix` | pre-2024 | 45 MB | Frozen (demo) | |
| `internal/aldc_demo/Data Model.pbix` | pre-2024 | 32 MB | Frozen (demo) | |
| `internal/aldc_demo/Style Guide - Daily Sales*.{png,pptx}` | 2022 | small | Demo style-guide assets | Multiple file variants; includes a misspelled `Style Guide - Daily Sales - Summarzy.png`. |

### Table 5j — `sales/` (pre-sales demos, frozen)

`sales/` is a frozen pre-sales-demo graveyard. Last commit 2022-08. **Important:** `sales/KIT_ACE/` holds a pre-sales "Product Pairing Recommender" pitch artefact — entirely distinct from the live production models in `custom/KIT_ACE/`.

| Path | Last commit | LFS size | Status | Notes |
|---|---|---|---|---|
| `sales/9TH_CO/Cluster Analysis/Ninth_Co Sample.pbix` | 2022-08-05 | 5.4 MB | **Frozen** | Pre-sales demo. Note: 9thco is `client_owner` on several `common/Retail/` CosmosDB JSON docs. |
| `sales/APEX_BRASIL/Export Demo/APEX_BRASIL Export Demo.pbix` | 2022-08-05 | 249 MB | **Frozen** | Prospect-demo. APEX_BRASIL does not appear in the wiki client index — unknown-status prospect. |
| `sales/KIT_ACE/Product Pairing Recommender/Product Pairing Recommender.pbix` + `.pptx` wireframe | 2022-08 | 31 MB | **Frozen** | Pre-sales pitch for a "Product Pairing Recommender" capability never productised. Distinct from `custom/KIT_ACE/`. |

---

## Developer Guide

### Prerequisites

| Requirement | Notes |
|---|---|
| **Git LFS** | **#1 prerequisite.** Run `git lfs install` (one-time per machine) before cloning. Without it, `.pbix` files download as 134-byte pointer stubs. PBI Desktop cannot open stubs. The repo's only in-repo documentation exists specifically to call this out — `large file storage.txt`: *"Large file storage MUST be enabled on the client where you intend to use this repository."* |
| **Sufficient disk + bandwidth** | A full clone pulls ~16 GB of LFS objects. Use selective fetch for single-client work (see § Clone). |
| **Power BI Desktop** | The **only** editor that can open `.pbix`. **Windows only** — no native macOS or Linux support. Mac developers must use Parallels / a Windows VM. |
| **PBI Desktop version currency** | A `.pbix` saved in a newer PBI Desktop version cannot be opened in an older one. Keep PBI Desktop current (roughly monthly releases). No version is pinned in the repo. |
| **Snowflake + Azure AD credentials** | Required to refresh data connections and publish to the PBI Service. See [[Snowflake]] and [[entities/tools/power-bi|Power BI (tool)]] § Power BI Workspaces. |

### Clone the repo

```bash
# Option 1 — full clone (~16 GB LFS, will take a while)
git lfs install
git clone https://github.com/ALDC-io/power_bi.git

# Option 2 — preferred: selective LFS fetch (one client at a time)
git lfs install --skip-smudge
git clone https://github.com/ALDC-io/power_bi.git
cd power_bi
git lfs fetch --include="custom/GEP/**" --exclude=""
git lfs checkout custom/GEP/2026_03\ Data\ Model/Data\ Model.pbix
```

Verify after clone: `git lfs ls-files | head` — each line should show an object ID + `*` (downloaded) or `-` (pointer stub only). If lines show `-`, run `git lfs pull` for those files.

### Edit a `.pbix` file

1. Identify the current live model from the Report Catalogue above (e.g., GEP current = `custom/GEP/2026_03 Data Model/Data Model.pbix`).
2. **Create a new dated folder, don't overwrite in place.** For GEP: `cp -r "custom/GEP/2026_03 Data Model" "custom/GEP/2026_04 Data Model"`. Older folder is retained as rollback. Match the prevailing date-folder naming convention for that client.
3. Open the new `.pbix` in Power BI Desktop.
4. Edit as needed — adjust M-queries, measures, visuals, calculated columns.
5. **Refresh the data connection** if changing schema. This requires Snowflake credentials for the relevant environment (test vs prod). See [[azure-environments]] + tool page workspace mapping.
6. Save the `.pbix` (Power BI Desktop saves in-place to the file).
7. **Commit convention.** One `.pbix` per commit, short descriptive message, often referencing a Jira ticket ID for GEP. Examples from git log: `"Hide new fields in platform table"` (F92), `"update power bi model for gp-169"` (GEP), `"Fix margin calculation"` (GEP).
8. `git add` the specific `.pbix` + `git commit -m "..."` + push.

### Publish to Power BI Service

1. PBI Desktop → File → Publish → select the correct workspace (per-client; per-environment for GEP). See [[entities/tools/power-bi|Power BI (tool)]] § Power BI Workspaces.
2. Refresh the dataset in the Service (manual — per tool page § Model Refresh).
3. For production deploys follow the full runbook: [[gep-snowflake-pbi-deployment]] (GEP) or [[model-deploy-production]] (generic).
4. Before publishing, verify the App Registration client secret is not near expiry — see [[powerbi-secret-refresh]].

### Common pitfalls

1. **Clone without `git lfs install`** — downloads pointer stubs; PBI Desktop fails to open with a cryptic error. Run `git lfs install` + `git lfs pull` to recover.
2. **Full-repo clone on metered or slow connection** — 16 GB pull. Use `git lfs install --skip-smudge` + selective `git lfs fetch --include=` for single-client workflows.
3. **Opening a `.pbix` on macOS/Linux** — impossible natively. Requires Parallels or a Windows VM. Plan for it before starting.
4. **PBI Desktop version mismatch** — a teammate saves on a newer version; you can't open the file. Keep PBI Desktop updated.
5. **Overwriting a `.pbix` in place** — repo convention is new dated folder, not in-place edit. In-place overwrites lose the rollback history the dated-folder pattern provides.
6. **Schema drift Snowflake ↔ `.pbix`** — if `REPORT_COMMON` columns change and the `.pbix` is refreshed without a matching model update, refresh fails. Coordinate with the clients-repo warehouse deploy. See [[data-pipeline-flow]] and [[debugging-warehouse-loads]].
7. **`.gitignore` is Python boilerplate** — everything it ignores (`__pycache__`, `.venv`, etc.) is irrelevant to a PBI developer. Don't mistake its presence for meaningful config.
8. **Dated-folder naming inconsistency** — DISH_DUER uses both hyphen and underscore; GEP uses space-separated type suffix; KIT_ACE uses parentheses. When creating a new folder, match the prevailing convention for **that specific client folder**, not a global rule.
9. **Templates in repo vs Nextcloud** — `templates/*.pbix` files are stale (last 2022-07). Per tool page, canonical templates live in `Nextcloud\Customers\Style Guides`. Do not start from the in-repo template.
10. **Secret rotation timing** — if the PBI Service App Registration secret is close to expiry when you publish, refresh will fail. Check [[powerbi-secret-refresh]] § Current secret expiry dates before publishing.
11. **Stale `CUST-*` branches on origin** — `CUST-303`, `CUST-396`, `CUST-421`, `CUST-461`, `CUST-528`, `cust-457`. These are old DISH_DUER / KIT_ACE / BOOK_DEPOT era feature branches, never cleaned up. Ignore unless explicitly working a matching ticket (unlikely — those clients are inactive).
12. **`.pbix` binary diffs are unreadable** — `git diff` on a `.pbix` shows a single LFS pointer line change. Reviewing a change requires opening both versions in PBI Desktop. No shortcut until `.pbip` migration.

---

## Deployment

### Deployment target — Power BI Service workspaces

There is no CI/CD. No `.github/workflows/`. No automated publish pipeline. Every `.pbix` deploy is a human action: File → Publish in Power BI Desktop, followed by a manual dataset refresh in the Service.

Target workspace is per-client. For GEP it is also per-environment:

| Environment | Workspace | Branch/trigger |
|---|---|---|
| GEP user-testing | `GEP Test Models` | manual (from `GEP/user-testing` branch equivalent) |
| GEP production | `Production` | manual (from `main`) |
| Fusion92 | Fusion92 workspace | manual |
| Other clients | Per-client workspace | manual |

Details per [[entities/tools/power-bi|Power BI (tool)]] § Power BI Workspaces and [[powerbi-secret-refresh]] (per-client App Registration table). **Git branch does not gate deployment** — merging to `main` triggers nothing; a human must still click Publish.

### Authoritative deploy runbooks

| Scope | Runbook |
|---|---|
| GEP full deploy (Snowflake + PBI) | [[gep-snowflake-pbi-deployment]] — 343 lines, most complete runbook |
| Generic PBI model deploy | [[model-deploy-production]] — 4-step checklist incl. Excel Analyze and Eclipse posting |
| Pre-release verification | [[client-release-checklist]] |
| Azure AD App Registration secret rotation | [[powerbi-secret-refresh]] — check before publishing if secret nearing 6-month expiry |

### Rollback

**Model-level rollback:** open the prior dated folder's `.pbix` in PBI Desktop and Publish — overwrites the Service dataset with the older version. The repo's dated-folder-snapshot convention is the rollback mechanism.

**No automated rollback.** Rollback = "open older file, click Publish."

**No data rollback.** `.pbix` rollback reverts only the semantic model; Snowflake warehouse state is unaffected. For full-stack rollback see [[gep-snowflake-pbi-deployment]].

### No repo-level CI/CD

No `.github/workflows/`. No unit tests — `.pbix` binaries are not testable without opening them in PBI Desktop. No linter, no formatter.

Unlike the rest of the 2026-04 ALDC portfolio (`eclipse_exp`, `workflows`, `custom-fusion-92-audience-api`, `flight-check`, `prospect-site-template` — all with PR checks per [[ai-pr-workflow]]), this repo has **zero automated gates**. Any commit to `main` is accepted. This is conventional for a binary-artefact repo — there is no meaningful CI to add until `.pbip` migration provides text artefacts to lint and diff.

---

## Security & Credentials

### Credential scan — results

**Text-file scan: CLEAN.** The 9 text-readable files (`.gitattributes`, `.gitignore`, `large file storage.txt`, 6 JSON files) were grep'd for Slack webhooks (`hooks.slack.com`), Anthropic keys (`sk-ant-`), GitHub PATs (`ghp_`), AWS keys (`AKIA`), and other credential patterns. No sensitive values found in any text file.

**Binary `.pbix` files matched grep patterns as binary noise.** The `grep -rE` scan returned matches on several `.pbix` binaries (DISH_DUER + GEP). These are false positives — the search patterns appear coincidentally in the binary model-data content inside the ZIP archive. **`.pbix` files should not be unzipped to investigate** — the internal `DataModel` format is proprietary binary and will produce garbage output. The only safe inspection path is opening in PBI Desktop.

**What `.pbix` files DO contain** (not grep-able, not secrets): Snowflake host + warehouse M-query connection parameters, CORE_API template parameter values (`CORE_API_URL`, `CORE_API_ACCOUNT_ID`, `CORE_API_REPORT_ID`), and semantic model schema. **Credentials are NOT stored inside `.pbix`** in the normal workflow — PBI Desktop stores credentials in Windows Credential Manager (desktop scope) or in the Service's dataset credential config (service scope). A leaked `.pbix` exposes warehouse topology, not a password.

### Sensitive identifiers in text files (not secrets)

The 4 CosmosDB report JSON files contain ALDC-internal identifiers:

| Identifier | File | Type | Action needed |
|---|---|---|---|
| `account_id: "61c98864"` | `retail_customer_lifetime_value.json` | Eclipse account ID (9thco / Customer Lifetime Value) | None — not a secret |
| `account_id: "8425e311"` | `daily_sales.json` | Eclipse account ID (KIT_ACE / Daily Sales) | None |
| `account_id: "5d556742"` | `kpi_manager.json` | Eclipse account ID (DISH_DUER / KPI Manager) | None |
| `account_id: "4dc61c31"` | `cosmos_report_template.json` | Eclipse account ID (9thco / Product Benchmark) | None |
| Client-owner emails | All 4 JSONs | Contact info (Justin Cook, Kat Petrova, Calvin Roex, Karen Prete) | ALDC-internal client contact data; not secrets |
| CosmosDB document IDs | `daily_sales.json`, `kpi_manager.json` | Internal CosmosDB UUIDs | Not secrets — per [[cosmosdb-schema]] |

### Runtime credentials (not stored in repo)

| Credential | Purpose | Storage |
|---|---|---|
| Snowflake username + password / keypair | `.pbix` model data refresh | See [[Snowflake]] + [[vault]] |
| Azure AD / Microsoft 365 login | Publish to PBI Service workspace | Per-user; per-client App Registration per [[powerbi-secret-refresh]] |
| CORE_API token params | Template glossary + metadata fetch | Per-model template parameters inside the `.pbix` (not committed as text) |

No credentials to extract to vault from this repo. If vault entries for Snowflake + PBI workspace credentials are missing, that gap is in the secret-refresh runbook, not here.

---

## Tech Debt & Known Issues

1. **No `.pbip` migration (biggest modernisation opportunity).** Every `.pbix` is the legacy binary format. `.pbip` (Power BI Project folder format) unpacks `.pbix` into a folder of TMDL + JSON — diffable, grep-able, CI-friendly. Microsoft's current recommendation for source-controlled Power BI. Migration is per-model (no bulk converter), but the live-model set is only ~10 files. Until `.pbip` is adopted: no meaningful PR review, no [[ai-pr-workflow]] integration, no CI lint. Recommend piloting on `custom/GEP/` — highest-value target.

2. **Repo footprint ~16 GB LFS with no retention policy.** GEP grows at 300–600 MB per monthly snapshot. At current cadence GEP alone adds ~5 GB/year. No dated folders are ever pruned. Recommended policy: retain last 12 monthly snapshots per client; archive older to a `legacy/` branch or a separate `power_bi_archive` repo.

3. **DISH_DUER ~5.5 GB frozen since 2024-08 (client inactive).** Prime candidate for archival extraction to `power_bi_archive` (new repo). Would reduce this repo's size by ~30%.

4. **BOOK_DEPOT frozen since 2022-11 (client inactive).** Similarly archivable. Total archivable frozen content (DISH_DUER + BOOK_DEPOT + `sales/` + pre-2024 `common/` + old KIT_ACE Finance Model variants + old GEP ≤ 2025-06) is ~10 GB+.

5. **6 stale `CUST-*` branches on origin.** `CUST-303`, `CUST-396`, `CUST-421`, `CUST-461`, `CUST-528`, `cust-457` — from the DISH_DUER / KIT_ACE / BOOK_DEPOT era; none matching active work. Should be deleted after a one-week notice to the team.

6. **In-repo `templates/` is a stale snapshot (last 2022-07).** Canonical templates live in `Nextcloud\Customers\Style Guides`. The `templates/*.pbix` trio is 4 years behind. Either prune + add a README pointer, or re-sync on every template revision. Currently neither — silent drift.

7. **Naming inconsistency in dated folders.** DISH_DUER uses `-` and `_` interchangeably; KIT_ACE uses `(YYYY-MM)` parentheses; GEP uses `YYYY_MM <type>` with space; FUSION_92 uses `YYYY_MM`. Document the inconsistency; renaming would invalidate git history.

8. **`.gitignore` is Python boilerplate and vestigial.** Either replace with a PBI-relevant ignore list (`.pbix.bak`, PBI Desktop lock files, etc.) or delete. Currently ignores nothing a PBI developer cares about.

9. **`ALDC_FINANCE/` under `custom/` rather than `internal/`.** Inconsistent with `internal/ALDC_ENG/`. Don't move without updating git history implications; document as-is.

10. **KIT_ACE filename convention frozen at template-version stamp.** `Finance Model DG1 2022-07.pbix` retains "2022-07" regardless of actual last-edit date (modified through 2025). Confusing; document but don't rename.

11. **`sales/APEX_BRASIL/` + `sales/9TH_CO/`** are prospect-demo artefacts for clients not in the wiki client index. Unknown if these prospects ever converted. Flag as "unknown-status prospect demos." Archival candidates alongside BOOK_DEPOT.

12. **Missing wiki ticket pages for commit-referenced Jira IDs.** Git log references `GP-76` (2025-04 commit) and `GP-87` (2025-05 commit). Neither exists as a wiki ticket page in `tickets/gep/`. Pages for GP-169, GP-197, GP-200, GP-203, GP-204, GP-207, GP-208 do exist. Create GP-76 and GP-87 stubs if those tickets become relevant to future sessions.

---

## Future home (platform consolidation)

**Power BI as a tool is staying.** Unlike [[Eclipse]] / [[core_api]] (being replaced by [[eclipse_exp]]) or [[connector]] (migrating to [[Prefect]]), there is no in-flight effort to replace Power BI. It remains the client-facing BI and reporting layer for the foreseeable future.

**`.pbix` → `.pbip` migration** is the closest thing to a "consolidation" story for this repo. Migrating to `.pbip` would make every model:

- Diffable in GitHub's web UI (TMDL + JSON are text).
- Lintable / reviewable in CI ([[ai-pr-workflow]] could finally apply).
- Cheaper to store in LFS (text changes are smaller binary diffs).
- Collaboration-friendlier (non-overlapping text changes merge cleanly).

Recommended pilot: `custom/GEP/2026_03 Data Model/Data Model.pbix` — highest-value target given GEP's commit cadence and storage footprint. Note this is a significant project, not a quick fix — do not treat this note as a specific proposal.

**Repo split** (`power_bi_archive`): Moving frozen client folders (DISH_DUER, BOOK_DEPOT, `sales/`, `internal/aldc_demo/`, old GEP snapshots) to a `power_bi_archive` repo would keep the primary repo to live content only and reduce LFS pull cost for new developers by an estimated 60%. Again, a significant project — document here as direction, not a committed plan.

**Nextcloud `templates/` sync**: Either maintain the in-repo `templates/` as a mirror of the Nextcloud copy (requires discipline on every template revision), or delete the in-repo copies and replace with a README pointer. The current silent-drift state is the worst option.

**No migration to another repo** is warranted. The Power BI artefact storage problem is Power-BI-specific and is not better served inside [[clients-repo]] or [[eclipse_exp]]. Keep the repo independent.

---

## See Also

### Must read (directly related)

- [[entities/tools/power-bi|Power BI (tool)]] — **The companion page.** How PBI works, connection parameters, workspaces, model refresh, granting Excel access. All usage-level content. Read this before the repo page if you're new to the ALDC PBI stack.
- [[gep-snowflake-pbi-deployment]] — Full GEP deploy runbook (Snowflake + PBI together). Authoritative for production GEP publishes.
- [[model-deploy-production]] — Generic PBI model deploy checklist.
- [[powerbi-secret-refresh]] — Azure AD App Registration secret rotation runbook. Check before publishing.
- [[client-release-checklist]] — Pre-release verification checklist.

### Active clients using this repo

- [[GEP]] — Primary and most active client. `custom/GEP/` has the highest commit cadence (2026-03 latest).
- [[fusion92]] — Active client. `custom/FUSION_92/` (2025-12 latest). Activation Model is the centrepiece of [[dax-ai]].

### Legacy / inactive clients

- [[kit-ace]] — Inactive client. `custom/KIT_ACE/` reports retained but not maintained (last update 2025-06 before client went inactive).
- [[dish-duer]] — Inactive client. `custom/DISH_DUER/` is the largest folder by storage (~5.5 GB); frozen since 2024-08.
- [[book-depot]] — Inactive client. `custom/BOOK_DEPOT/` frozen since 2022-11.

### Pipeline + data

- [[Snowflake]] — Data source upstream of every `.pbix`. Report common views are the PBI consumption layer.
- [[SSMS]] — Intermediate SQL Server layer used for GEP partition and reprocessing runs.
- [[data-pipeline-flow]] — End-to-end ALDC pipeline including PBI's position.
- [[star-schema-convention]] — Warehouse naming convention that feeds `REPORT_COMMON` views into PBI.
- [[cosmosdb-schema]] — CosmosDB `report` document schema (the 6 JSON files in this repo are frozen snapshots).
- [[clients-repo]] — Warehouse SQL + Eclipse configs; upstream of PBI via `REPORT_COMMON` views.
- [[periodicity]] — DAX SWITCH pattern used across the report models.

### Projects

- [[dax-ai]] — DAX AI dashboard project; Fusion92 Activation Model is the centrepiece.
- [[dax-media-app]] — Parent project for Fusion92 Activation Model context.
- [[deployment-groups]] — Context for `internal/ALDC_ENG/Account Summary ... Canada DG1.pbix` files.
- [[azure-environments]] — Subscription mapping relevant for publish workspace targets.

### Operations + process

- [[ai-pr-workflow]] — The ALDC-wide PR workflow this repo does **NOT** enforce (contrast explicitly). Applicable only after `.pbip` migration provides text artefacts.
- [[vault]] — Runtime credential reference (Snowflake + PBI workspace credentials).

### Ticket cross-references (from commit messages)

- [[tickets/gep/GP-169]] — referenced in 2026-03-06 commit ("update power bi model for gp-169"). Page exists.
- GP-76, GP-87 — referenced in 2025-04 and 2025-05 commits respectively. **No wiki pages exist** — see Tech Debt item 12.
