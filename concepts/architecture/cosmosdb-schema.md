---
tags: [concept, architecture, cosmosdb, core-api, schema, data-model]
aliases: [CosmosDB Schema, CosmosDB Collections, core_api Data Model]
sources: [CORE/893124613, CORE/929103873, CORE/921632769, CORE/937197569, CORE/1050869770, CORE/917700609, CORE/921632782, CORE/902987777, CORE/968163329, CORE/917700622, CORE/928186369]
created: 2026-04-18
updated: 2026-04-18
---

# core_api CosmosDB Schema Reference

> *2021–2022 schema snapshot unless noted. work_template last updated 2024-02-08 and is most current. Verify other collections against actual CosmosDB containers before relying on field lists.*

Document schema reference for [[core_api]]'s [[CosmosDB]] collections. Covers the ETL orchestration domain (account → capacity → connections → templates → partitions → sessions → tasks) plus supporting collections (agent, staff, report).

See [[CosmosDB]] for runtime usage, the stale-template bug, and `patch_item` patterns. See [[core_api]] § Key modules for the API surface that reads/writes these documents.

---

## ETL Orchestration Flow

The core_api orchestrates multi-stage ETL through a chain of CosmosDB documents:

```
account (config + schedule_block)
  └── capacity_provider (vendor instance: Snowflake account, super-user)
        └── capacity (account's assignment: warehouse names, service passwords)
              └── work_template (extract definition: connector, options, partition_scheme, merge_strategy)
                    └── work_partition (instantiated date/key slice, queue state)
                          └── session (single run: events, schema, status)
                                └── session_event (discrete pipeline stages: setup→output→transport→stage→merge)
```

Orthogonal collections:
- **agent** — workers that pick up queue messages from partitions
- **work_connection** — external data source credentials referenced by templates
- **task** — scheduled daemon invocations (e.g., `work/scan`)
- **staff** — notification routing for operational alerts
- **report** — Eclipse UI report metadata

---

## Account Collection

Container: `account`. Partition key: `id`.

Stores all system-required configuration for a single ALDC client account. Primary reference for all account-dependent operations.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string | 8-char hex, auto-generated | `"5d556742"` |
| `short_code` | string | Account code | `"DISH_DUER"` |
| `full_name` | string | Company name | `"Dish & Duer"` |
| `tier` | string | Storage tier | `"XS"` … `"3XL"` |
| `contact` | list[dict] | Client contacts (`name`, `email`, `primary`, `title`) | — |
| `address` | dict | `country`, `locale`, `city`, `address`, `postal_code` | — |
| `contract_periods` | list[dict] | `start_date`, `end_date`, `minimum_fee` (CAD/USD) | — |
| `scan` | boolean | Include in `work_scan()` | `true` |
| `industry` | string | Sector | `"Retail Apparel"` |
| `billing_status` | string | Billing state | `"Current"` |
| `temp_purge` | boolean | Purge staging files after merge | `true` |
| `provider` | string | Cloud platform | `"azure"`, `"aws"`, `"gcp"` |
| `provider_tenant` | string | Cloud tenant ID | UUID |
| `region` | string | Cloud region | `"canada_central"` |
| `master_timezone` | string | IANA timezone | `"America/Vancouver"` |
| `schedule_block` | list[dict] | Blocked hours: `name`, `start` (seconds from midnight), `end` | `{"name":"20:00-04:30","start":72000,"end":16200}` |
| `stage_setup` | boolean | Storage account configured | `true` |
| `invoice_day` | int | Day of month for invoice (1–28) | `1` |
| `invoice_email` | string | Invoice recipient | — |
| `currency` | string | ISO 4217 | `"CAD"` |
| `minimum_fee` | int | Fallback monthly fee | `3500` |
| `tax_details` | list[dict] | `name` (GST/PST/HST), `percentage` (0.0–1.0) | — |

`schedule_block` prevents the core_api from running extraction jobs during specified hours (e.g., month-end close, overnight maintenance).

---

## Capacity Provider Collection

Container: `capacity_provider`. Partition key: `id`.

Vendor-level infrastructure configuration. Shared by multiple accounts — separates provider-level settings (super-user, region, timeouts) from account-level capacity assignments.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string | UUID/hex ID | `"7e59216f4e5d44ea8816b2fce2331312"` |
| `type` | string | Resource type | `"warehouse"`, `"visualization"`, `"stage"` |
| `provider` | string | Vendor | `"snowflake"`, `"powerbi"`, `"azure_blob"` |
| `options` | dict | Vendor-specific config + encrypted credentials | See below |
| `queue_timeout_seconds` | int | Max queue wait before cancel | `1800` (30 min) |
| `query_timeout_seconds` | int | Max query execution before kill | `900` (15 min) |

### options (Snowflake example)

| Field | Description | Example |
|---|---|---|
| `account` | Snowflake account ID | `"og35375"` |
| `provider` | Cloud hosting | `"azure"` |
| `region` | Cloud region | `"canada-central"` |
| `super_role` | Admin role | `"accountadmin"` |
| `super_user` | Fernet-encrypted username | `"gAAAAAB..."` |
| `super_password` | Fernet-encrypted password | `"gAAAAAB..."` |
| `super_warehouse` | Default warehouse | `"COMPUTE_WH"` |

Credentials are Fernet-encrypted using the `ENCRYPTION_KEY` env var — see `vault/infra-credentials.md` § Core API App Registrations for the key per environment. Never log or expose decrypted values.

Timeout strategy: queue timeout kills long-queued jobs to free resources; query timeout kills long-running queries to prevent table locks.

---

## Capacity Collection

Container: `capacity`. Partition key: `account_id`.

Account-specific capacity assignment. References a `capacity_provider` for instance connectivity; holds account-scoped warehouse names and Fernet-encrypted service passwords.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string | UUID | `"ec8be1422a304b319c42c0af5fc0b068"` |
| `account_id` | string | Owner account | `"5d556742"` |
| `capacity_provider_id` | string | → `capacity_provider.id` | UUID |
| `status` | string | `"active"` or `"inactive"` | `"active"` |
| `master` | boolean | Default for this type; one per type per account | `true` |
| `setup` | boolean | Credentials validated; managed by core_api | `true` |
| `options` | dict | Account-scoped config + Fernet-encrypted service passwords | See below |

### options (Snowflake warehouse example)

```json
{
  "warehouse_core":   "COMPUTE_WH",
  "warehouse_report": "COMPUTE_WH",
  "service_password_core":   "{{FERNET_ENCRYPTED}}",
  "service_password_report": "{{FERNET_ENCRYPTED}}"
}
```

`master: true` is auto-managed — only one capacity per type per account may be master.

---

## Agent Collection

Container: `agent`. Partition key: `id`.

Stores agent worker registrations. Agents declare themselves when picking up work from the queue.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string | UUID hex | `"9b833fa37c4e4ada8560c981159b074a"` |
| `connection_authorized` | list[dict] | Scoped connections: `account_id` + `connection_id`. Empty = free agent (any work). | — |
| `datetimestamp_init_utc` | float | Creation timestamp | `1641449415.09` |
| `datetimestamp_update_utc` | float | Last update | `1641608130.17` |

An agent with an empty `connection_authorized` list is available for work from any account. Scoped agents are restricted to listed `account_id` / `connection_id` pairs.

---

## Work Connection Collection

Container: `work_connection`. Partition key: `account_id`.

External data source connection configurations referenced by work templates.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string | UUID | — |
| `account_id` | string | Owner account | `"5d556742"` |
| `name` | string | Human-readable label | `"Snowflake Fivetran Staging (px06888)"` |
| `connection` | dict | Source-specific connectivity (server, database, username, warehouse, **password redacted to vault**) | See below |
| `status` | string | `"active"` or `"inactive"` | `"active"` |
| `max_connection` | int | Max concurrent connections | `2` |

### connection (Snowflake example)

```json
{
  "server":    "px06888.us-central1.gcp.snowflakecomputing.com",
  "database":  "FIVETRAN_DB",
  "username":  "analyticlabs",
  "warehouse": "TRANSFORM_WH",
  "password":  "{{REDACTED — see vault/infra-credentials.md § Fivetran Snowflake}}"
}
```

> Connection passwords may be stored in plain text in CosmosDB (not Fernet-encrypted like capacity credentials). Treat `connection.password` fields as real secrets.

---

## Work Template Collection

Container: `work_template`. Partition key: `account_id`. **Last updated 2024-02-08 — most current schema.**

Defines the extraction framework: source table, destination naming, filters, primary keys, partitioning strategy, and merge behaviour. One template → many work_partition documents.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string | UUID | `"784749ff-1a38-464d-833b-150cf5f88d17"` |
| `account_id` | string | Owner account | `"6e17e11b"` |
| `connection_id` | string | → `work_connection.id` | UUID |
| `connector` | string | Connector/driver type | `"snowflake_v1"`, `"esri_shapefile_v1"` |
| `status` | string | `"active"` or `"inactive"` | `"active"` |
| `topic` | string | Destination schema/topic | `"CLIMATE"` |
| `name` | string | Display name | `"Current Year Fire Data"` |
| `comment` | string | Description | — |
| `options` | dict | Source + destination mapping | See below |
| `retry_default` | int | Default retry interval (seconds) | `7200` |
| `retry_min` | int | Minimum retry interval | `5400` |
| `retry_max` | int | Maximum retry interval | `21600` |
| `retry_doubling` | int | Backoff multiplier | `2` |
| `partition_scheme` | dict | Partitioning strategy | See below |
| `merge_strategy` | string | How new data is applied | `"heap"`, `"add"`, `"full"`, `"version"` |
| `merge_history` | boolean | Record `GLOBAL_HISTORY_TIMESTAMP` boundaries | `true` |
| `datetimestamp_last_utc` | float | Last accessed | — |

### options

```json
{
  "table":      "SOURCE_TABLE_NAME",
  "schema":     "SOURCE_SCHEMA_NAME",
  "category":   "dest_prefix",
  "table_name": "dest_suffix",
  "primary":    ["KEY_FIELD"],
  "fields":     [],
  "filter":     [{"field":"TRANDATE","operator":"greater_equal","value":"2022-01-01"}],
  "delimit_all": false,
  "rest_field":  false
}
```

- `table` / `schema`: case-sensitive for most sources
- `category` + `table_name`: combined to form destination table name (case-insensitive)
- `filter` operators: `equals`, `less`, `less_equal`, `greater`, `greater_equal`, `list` (IN strings), `list_num` (IN numbers)
- `delimit_all`: wrap field names in delimiters (e.g., reserved words like `date`)
- `rest_field`: (CSV only) pull unlisted fields as strings

### partition_scheme

```json
{
  "field": "date",
  "method": "datetime_window_greater_less",
  "options": {
    "bleed_minus": 0,
    "bleed_plus": 0,
    "limit_current": true,
    "min_date": "2020-11-01",
    "utc_offset": -28800,
    "window_type": "month"
  },
  "time_to_live": {"interval": 60, "method": "partition_date"}
}
```

**Methods:**

| Method | Behaviour |
|---|---|
| `datetime_window_greater_less` | Date range sliced by `day`, `month`, or `year` |
| `date_window_equal` | Daily date range |
| `modulus` / `modulus_builtin` | Modulus division on numeric field |
| `list_cross` | Cross product of lists |
| `list_parallel` | Aligned list combination |
| `full` | No partitioning; whole dataset |

`bleed_plus` / `bleed_minus`: extend partition boundaries to overlap adjacent partitions. `limit_current`: don't partition past today. `utc_offset`: timezone offset in seconds.

**TTL:** `interval` = days back to retrieve; data before the TTL window is loaded once and not auto-re-picked.

### merge_strategy

| Strategy | Behaviour |
|---|---|
| `heap` | Insert all rows; no updates |
| `add` | Update existing + insert new; optionally record history chain |
| `full` | Mark old rows deleted + update existing + insert new; optionally record history |
| `version` | Insert-only; assembles current/version chain post-insert *(in development)* |

---

## Work Partition Collection

Container: `work_partition`. Partition key: `account_id`.

Instantiated data partitions representing a specific date/key slice of a work_template's extraction scope. Tracks queue state and retry timing.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string | UUID | `"72953811-87e5-4984-84dc-d48f26aa189e"` |
| `template_id` | string | → `work_template.id` | UUID |
| `account_id` | string | Owner account | `"83148af7"` |
| `connection_id` | string | → `work_connection.id` | UUID |
| `status` | string | `"active"` or `"inactive"` | `"active"` |
| `partition` | dict | Slice definition: `partition_keys` (field + key) + `filter` array | — |
| `in_queue` | boolean | Currently queued | `false` |
| `queue_messages` | list[dict] | `queue_id`, `queue_pop_receipt`, `hash_result` | — |
| `hash_result_last` | string\|null | Hash of last result set for change detection | `null` |
| `run_count` | int | Execution count | `1` |
| `retry_next` | float | Seconds until next retry | `300` |
| `datetimestamp_init_utc` | float | Creation | `1648703843.54` |
| `datetimestamp_last_utc` | float | Last execution | `1649192072.36` |

---

## Task Collection

Container: `task`. Partition key: `task_type`.

Scheduled daemon invocations. Currently only `task_type: "api"` is supported.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string | UUID | — |
| `task_type` | string | Platform target | `"api"` (future: `"portal"`) |
| `name` | string | Description | `"work/scan for ALDC Sandbox account"` |
| `timeout` | int | Timeout seconds (not yet implemented) | `30` |
| `options` | dict | API invocation: `host`, `url_base`, `category_name`, `payload` | See below |
| `accounts` | dict | Account filter (reserved, unused — CORE-325) | `{}` |
| `schedule` | dict | `cron_schedule` (5-field cron) + optional `seconds` | `{"cron_schedule":"* * * * *","seconds":15}` |
| `datetimestamp_init_utc` | int | Creation | — |
| `datetimestamp_last_utc` | int | Last execution | — |
| `datetimestamp_next_utc` | int | Next scheduled execution | — |

### options

```json
{
  "host": "http://localhost:7071",
  "url_base": "v1",
  "category_name": "work/scan",
  "payload": {"account_id": "674fde41", "template_limit": 10, "partition_limit": 40}
}
```

`payload` is optional — only include if the endpoint expects a request body.

---

## Staff Collection

Container: `staff`. Partition key: `id`.

Internal team member metadata for the ALDC notification system. Routes operational alerts by group membership.

| Field | Type | Description |
|---|---|---|
| `id` | string | UUID |
| `first_name` / `last_name` | string | Team member name |
| `preferred_method` | string | Primary channel: `"sms"`, `"email"`, `"pushover"` |
| `groups` | list[string] | `"core_api"`, `"connectors"`, `"portal"`, `"reporting"` |
| `contacts` | list[dict] | `{"type": "sms"/"email"/"pushover", "contact": "<value>"}` |

Staff contacts (phone, email, Pushover tokens) are PII — not stored in this wiki. Manage in the actual CosmosDB staff container.

**Group routing:** `core_api` = extraction/schema errors; `connectors` = API integration issues; `portal` = UI issues; `reporting` = warehouse merge/pipeline failures.

---

## Report Collection

Container: `report`. Partition key: `account_id`.

Metadata for reports displayed in the Eclipse UI.

| Field | Type | Description |
|---|---|---|
| `id` | string | UUID |
| `account_id` | string | Owner account |
| `type` | string | `"power_bi"` etc. |
| `name` | string | Report title (used if `name_custom` is null) |
| `name_custom` | string\|null | Override title for standard reports |
| `industry` | string | Industry category |
| `comment` | string (HTML) | Info panel content |
| `change_notes` | string (HTML) | Changelog |
| `outage` | boolean | Active issue flag |
| `outage_note` | string (HTML) | Issue description |
| `standard` | boolean | Non-customizable report |
| `credits_used` | number | Credits charged |
| `client_owner` | dict | `name`, `contact`, `role` |
| `development_owner` | dict | `name`, `contact`, `role` |
| `glossary` | list[dict] | `key` + `description` (HTML) pairs |
| `status` | string | Workflow gate (e.g., `"Review by Client"`) |
| `datetimestamp_deploy_utc` | int | Deploy timestamp |
| `version` | string | Release string |
| `enabled` | boolean | Visible in Eclipse UI |
| `capacity_type` | string | Source platform (e.g., `"snowflake"`) |

---

## Core ETL Pipeline Documents

Source: Confluence CORE/893124613 (Cosmos Database Principles, 2021–2022).

### Schedule Collection

Container: `container_schedule`. Partition key: `schedule_id` + `account_id`.

Records scheduled extraction jobs. Created by the queue executor per work cycle.

Key fields: `id`, `account_id`, `template_id`, `partition_id`, `queue_id`, `agent_id`, `thread_id`, `connector`, `topic`, `connection` (call_interval, call_max), `status`, `datetimestamp_init_utc`, `datetimestamp_complete_utc`, `duration_init_complete`.

### Schedule Event Collection

Container: `container_schedule_event`. Partition key: `schedule_id` + `account_id`.

Discrete events during a schedule's lifetime (start/end of extract, load, etc.).

Key fields: `schedule_id`, `account_id`, `event`, `status` (`"start"`/`"end"`), `payload`, `datetimestamp_init_utc`, `datetimestamp_update_utc`.

### Schema Collection

Container: `container_schema`. Query keys: `account_id`, `topic`, `category`, `table`, optional `master`, `version`.

Column definitions (name, native dtype, warehouse dtype) for tables staged and merged into Snowflake. The `master` boolean flag marks the default schema for a topic/category/table combination.

> **Key pitfall:** Multiple schema documents can coexist for the same logical template. Eclipse / core_api does not always clean up stale ones — see [[CosmosDB]] § Key pitfall for the stale-template bug.

### Session Collection

Container: `container_session`. Related: `container_session_event`, `container_session_schema`.

Groups all work for a single extraction/load cycle. Tracks events (setup → output → transport → stage → merge) and final schema.

Key fields: `id`, `account_id`, `schedule_id`, `template_id`, `status`, lifecycle timestamps, `events` array, `schema` array, `primary` keys.

**Event types:** `setup` (extraction init), `output` (formatting), `transport` (transfer to staging), `stage` (Snowflake temp table), `merge` (staging → warehouse).

---

## See Also

- [[CosmosDB]] — runtime usage, instances, stale-template bug, `patch_item` patterns
- [[core_api]] — API endpoints that read/write these collections
- [[eclipse]] — Eclipse UI consumes `report` and `capacity` collections
- [[deployment-groups]] — CosmosDB instances per environment (`aldcprodcsdb1c01`, etc.)
- `vault/infra-credentials.md` — Fernet `ENCRYPTION_KEY` per env + Fivetran Snowflake connection credentials
