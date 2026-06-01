---
tags: [entity, tool, eclipse, connector, etl]
aliases: [Eclipse, Eclipse Connector, ALDC Connector]
sources: [clients repo eclipse/ directories, connector repo, daily/2026-04-17.md, Confluence TECH/1191575556 (Eclipse 2.0)]
created: 2026-04-16
updated: 2026-04-17
---

# Eclipse

ALDC's proprietary connector platform for data ingestion. Eclipse pulls data from source systems (APIs, databases, files) and loads it into [[Snowflake]]. Configuration is JSON-based, living in the [[clients-repo]].

## Core Concepts

### Connections
JSON files in `CLIENT/eclipse/connections/` that hold authentication credentials for a data source.

```
connections/
├── amazon_seller_central.json   # OAuth tokens, client ID/secret
├── sellercloud_sql.json         # SQL Server uid/pwd
├── budget.json                  # CSV file config
└── ...
```

Each connection defines: server/host, auth type (API key, OAuth, SQL credentials), and any source-specific config.

### Templates
JSON files in `CLIENT/eclipse/templates/SOURCE_NAME/` that define what data to pull from a connected source.

```
templates/
├── amazon/
│   ├── all_orders_report.json
│   ├── inventory_report.json
│   └── sales_and_traffic_report.json
├── sellercloud_sql/
│   ├── order.json
│   ├── product.json
│   └── inventory_pandl.json
└── supplement/
    ├── budget.json
    ├── currency.json
    └── calendar.json
```

Templates specify: source table/endpoint, columns to extract, filters, scheduling params (like `min_date`), and how data maps to Snowflake tables.

**Supplement templates** are special — they pull from CSV files or reference data, not live APIs.

### Tasks
Scheduled execution of templates. Tasks define when and how often Eclipse pulls data. Tasks are managed in the Eclipse UI or via CosmosDB.

### Capacity / Dataset
`capacity.json` and related configs define the Eclipse account's capacity allocation and data model structure.

## Data Landing Pattern

Eclipse loads data into Snowflake source schemas using a `CURRENT_*` table naming pattern:

```
PROD_DG1_GEP.AMAZON.CURRENT_REPORT_FBA_INVENTORY
PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_INVENTORY_PANDL
PROD_DG1_GEP.SUPPLEMENT.CURRENT_TIME_CALENDAR
```

The `CURRENT_` prefix indicates the latest snapshot. Some also maintain `HISTORY_` prefixed tables for full history. The `___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___` column tracks when each snapshot was captured.

## Registration Workflow

When adding a new connection + template:

1. **Create connection JSON** in `CLIENT/eclipse/connections/`
2. **Create template JSON(s)** in `CLIENT/eclipse/templates/SOURCE_NAME/`
3. **Register in CosmosDB** — connection and template must be registered via the Eclipse admin interface or API
4. **Create/resume task** — schedule the template execution
5. **Verify data landing** — check that `CURRENT_*` tables appear in the correct Snowflake source schema

See [[gep-snowflake-pbi-deployment]] for the full deployment walkthrough including Eclipse registration.

## Connector Runtime

The Eclipse connector runs as a Docker container on VMs. The runtime:
- Reads connection + template configs from CosmosDB
- Executes data pulls on schedule
- Handles pagination, rate limiting, retries
- Loads data into Snowflake via stage + COPY INTO

The runtime code lives in the `connector` repo (`C:\Users\PaulRussell\repos\connector`).

## Eclipse Environments

| Environment | CosmosDB Instance | Notes |
|-------------|-------------------|-------|
| Production | `eclipse_prod1c01` | Production connectors |
| Test | `eclipse_test1c01` | Testing/development |

Connection configs for both are in `ALDC_ENG/eclipse/connections/`.

## Scale (in clients repo)

- 150+ connections across 19 clients
- 300+ templates defining data pulls
- Major connection types: Snowflake, SQL Server, REST APIs (Amazon, Meta, Google, etc.), CSV files, MongoDB, Firebase

## Eclipse 2 framework decisions (WIP)

> The Next.js UI repo that implements these decisions lives at [[entities/repos/eclipse|eclipse (repo)]]. See that page for architecture, dev guide, and deployment details.

Sourced from Confluence TECH/1191575556 (Eclipse 2.0, Brayden). Marked "PAGE IN PROGRESS" in the source; last edited 2024-04-04. Ingested 2026-04-17 — status may have drifted. Treat as the 2024 planning snapshot, not settled truth.

Eclipse 2 is the Node-based rebuild of the platform (Eclipse 1 is the legacy portal web app — see [[Azure]] for the app-service split). The source page states the intent to eventually fold this content into a Development Standards page split into **Core / Portal / Agent** sections.

### Decided (in the source doc)

| Area | Decision |
|---|---|
| Styling | Tailwind CSS (easier to customize than Bootstrap) |
| Component style | Function-based React components (better fit for Hooks) |
| Rendering | Client-side by default; server-side where performance demands |
| Indentation | 4-space (explicitly replacing the 2-space Metl style) |
| Identifier style | camelCase |
| Docstring format | JSDoc-style `@param {type} : description` / `@return {type} : description` |

### Open debates / undecided

- **JS vs TS** — Helio strongly recommends JS; Brayden strongly recommends TS. JSDoc + linter proposed as a middle ground.
- **IDE** — Helio: JetBrains WebStorm (~$8/user/mo). Lawrence: VS Code.
- **Package manager** — NPM (Helio: "speed difference is negligible").
- **Testing framework** — candidates listed: Jest, Vitest, Testing, Cypress. No decision.
- **Postman replacement** — "find something to replace Postman" noted as an open task.
- **Swagger execution tooling** — "research" (tools that take Swagger docs and execute them).
- **Database alternatives to Postgres** — evaluating multi-region support for full failover.
- **@return docstring requirement** — unresolved whether it's mandatory or optional.

### Planned but not built

- **Error handling**: verbose error logs using dictionaries; native error handling; Slack integration; try/catch on all API calls; devs-only bug-log document (split per day); email on critical portal errors.
- **Caching**: Redis via Azure Redis service; evaluating multi-region support for API + webservice.

### Mentioned as adjacent/reference tools

Brayden's note about tools that overlap with or compete with what Eclipse 2 aims to build: Segment, Amplitude, Metabase (slight competitor), Better Stack, Lightdash (slight competitor).

## Eclipse 2.0 Application Framework Patterns

> Apps built on this framework (e.g. [[dax-media-app]]) embed inside the [[entities/repos/eclipse|eclipse (repo)]] portal via the iframe app loader (`pages/application/[...slug].tsx`).

*Source: CF92/1254883340 — architectural design notes for apps built on Eclipse 2.0 (e.g. [[dax-media-app]])*

Key patterns used when building Eclipse 2.0-based applications:

- **Permissions & Groups** — Named permission categories assigned to users and groups. Sub-form functional changes based on assigned permissions (e.g. hide/show fields per role).
- **Form & Dataset Management** — Form layout configuration + styling. Distinction between native app data (writable) and Linked (Snowflake) data (read-only).
- **Workflow & Action Triggers** — Automated workflows triggered by user actions and system events.
- **Search** — Full-text and filtered search across application data.
- **Sidebar & Navigation** — Context-aware sidebar; sub-screen navigation; form-to-form flows; hierarchical screen organization.

## Connector Development Standards

*Source: Confluence CONN/424280065*

> **Prefect migration note:** The attribute hierarchy, parameter schemas, and response structure below are the foundational interface contract that Prefect connector flows must preserve when replacing Eclipse connectors.

### Attribute Hierarchy

Maps directly to Snowflake DDL. Acceptable characters: A-Z, 0-9, underscore. Lowercase is uppercased in Snowflake.

| Level | Description | Example |
|---|---|---|
| **Connector** | Class name + version. Does not appear in warehouse. | `googleanalytics_v4` |
| **Topic** | Data source instance. Appears as Snowflake schema. | `GOOGLE_ANALYTICS_CANADA` |
| **Category** | Queryable dataset within source (API endpoint, DB schema). | `TRAFFIC` |
| **Table** | Table within the collection. | `USAGE` |

**Snowflake naming pattern:** `{CLIENT_SHORT_NAME}.{TOPIC}.{CATEGORY}_{TABLE}`

*Example:* `ACME_MFG.GOOGLE_ANALYTICS.TRAFFIC_USAGE`

### Connector Interface

#### Initialisation

```python
connector_instance = Connector(name, connection, options)
```

**`connection` dict** — physical connection parameters (API keys, DB host/port/user/pass).

**`options` dict** — query parameters composed by the scheduler:
```python
{"symbols": ["CAD", "AUD"], "start_date": "2021-01-01", "end_date": "2021-01-05"}
```

#### Response Structure

Returns a list of dicts, one per table:
```python
[{"connector": str, "category": str, "collection": str, "table": str,
  "dataframe": pd.DataFrame, "rowcount": int, "bytes": int}]
```

### Base Classes

- `base_connector.py` — root base class
- `base_connector_rest.py` — REST API connectors
- `base_connector_odbc.py` — ODBC connectors (Query Mode: direct SQL; Table Mode: component-based query with field filtering + schema support)
- `base_connector_flatfile.py` — flat file connectors

### Code Layout

```
connector_project/
├── _connector_test.py
└── connector/
    ├── __init__.py
    ├── connector_file.py
    └── base/
        ├── base_connector.py
        ├── base_connector_rest.py
        ├── base_connector_odbc.py
        └── base_connector_flatfile.py
```

### Development Workflow

1. Copy an existing connector or `_template_REST.py`
2. Add logic; register class in `__init__.py` + pass-through function
3. Test with `_connector_test.py` (outputs CSV/JSON per table)
4. Delete test CSV/JSON files before committing to GitHub

## Recovery & Incident Notes

When an outage (power/network/agent restart) kills templates mid-run, see the
[[eclipse-incident-response]] runbook (triage → canary re-trigger → warehouse verify).

**Zombie / queue gotcha (single-`full`-partition templates).** A `partition_scheme.method:
full` template that is power-killed mid-run goes `zombie`, leaving its single `work_partition`
with un-acked `queue_messages` and `in_queue: true`. It does **not** auto-recover on schedule —
re-trigger manually, and expect a few minutes of queue-drain before the re-run lands (latency,
not a wedge — verify the agent is healthy first: a working agent shows many `complete` runs in
`schedule`). Data is never corrupted: these loads write a new versioned `MAIN_…_N` table and
repoint the `CURRENT_MAIN_…` view atomically, so a killed run wrote nothing and the live table
keeps the last-good snapshot. Note `in_queue: true` alone is **not** a blocker — partitioned
templates (one partition/day) normally carry many. (Established 2026-06-01, ALDC-244.)

## See Also

- [[eclipse-incident-response]] — outage recovery runbook (triage, canary, zombie gotcha)
- [[clients-repo]] — where Eclipse configs live (source of truth)
- [[data-pipeline-flow]] — Eclipse's role in the full pipeline
- [[Snowflake]] — where Eclipse loads data
- [[connector]] — the Eclipse runtime codebase (data plane)
- [[core_api]] — Eclipse's backend API service (control plane)
- [[CosmosDB]] — runtime store for Eclipse connections and templates
- [[eclipse-azure-deployment]] — Eclipse app deployment runbook (staging slot + swap)
- [[debugging-warehouse-loads]] — what to do when an Eclipse template's data isn't landing
- [[google-analytics]] / [[facebook-ads]] / [[bing-ads]] / [[google-ads]] / [[amazon-ads]] / [[trade-desk]] — per-platform connector docs
