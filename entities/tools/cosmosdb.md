---
tags: [entity, tool, cosmosdb, azure, database, eclipse]
aliases: [CosmosDB, Cosmos DB, Azure CosmosDB]
sources: [daily/2026-04-17.md, entities/tools/eclipse.md, Confluence TECH/1156284418 (Cosmos DB Partial Updates)]
created: 2026-04-17
updated: 2026-04-17
---

# CosmosDB

Azure-hosted NoSQL document database used by ALDC primarily as the runtime store for [[Eclipse]] connection and template configurations. [[core_api]] reads from CosmosDB when serving Eclipse requests; [[connector]] references the same configurations when executing data pulls.

## What CosmosDB stores

- **Eclipse connections** — registered connection configs that mirror the JSON files in `CLIENT/eclipse/connections/` from the [[clients-repo]]
- **Eclipse templates** — registered template configs that mirror `CLIENT/eclipse/templates/SOURCE_NAME/*.json`
- **Schema container** — separate container holding template/schema documents. Multiple documents can exist per logical template (see pitfall below)

## Instances

| Environment | [[Azure]] Subscription | Notes |
|-------------|-----------------------|-------|
| Production (eclipse_prod1c01) | Production 2 | Production Eclipse runs against this |
| Test (eclipse_test1c01) | Quality 1 | Paired with Snowflake non-prod for test |

## Key pitfall: stale templates in the schema container

During warehouse load debugging, an older template document in the `schema` container can cause a newer template to fail. Multiple template/schema documents can coexist for the same logical template, and Eclipse / [[core_api]] does not always clean up the stale one when a new version is registered.

**Symptom:** A template that ran fine yesterday starts returning errors / bad data after a new version is deployed.

**Investigation:** Open the CosmosDB `schema` container, look for multiple documents referencing the same template, identify the stale one.

**Debugging approach:** Use [[Postman]] to reproduce the template call locally against [[core_api]] (exact local workflow still being figured out — open follow-up for Paul).

See [[debugging-warehouse-loads]] for the step-by-step runbook.

## Registration

New Eclipse connections/templates are registered into CosmosDB via the Eclipse admin interface or API as part of the deployment workflow. The JSON files in [[clients-repo]] are source of truth; CosmosDB is the runtime mirror.

## Partial updates (`patch_item`)

Sourced from Confluence TECH/1156284418, ingested 2026-04-17.

Use `patch_item` on the Container Proxy (`func_common.container_*`) to update specific fields of a document without replacing the whole thing. Requires `azure-cosmos >= 4.4.0`.

```python
# Grab both id and partition key
this_account = account_describe(account_id)
this_id = this_account.get('id')

# Partial-update operations list
operations = [
    {"op": "add", "path": "/field_name", "value": new_value},
]

# Execute
func_common.container_something.patch_item(
    item=this_id,
    partition_key=this_id,
    patch_operations=operations,
)
```

### Operations

| Op | Purpose |
|---|---|
| `add` | Add a new field, or append to a list by ending the path with `-` (e.g. `"/list_field/-"`). You can also specify an index instead of `-`. |
| `remove` | Delete a field. Does not take `value`. |
| `set` | Replace or set a field's value. Creates the field if missing. |
| `replace` | Like `set` but **only** if the field already exists. |
| `incr` | Add (or subtract, with negative) to an existing numeric field. |
| `move` | Rarely used internally — see MS docs if a use case comes up. |

Microsoft docs: https://learn.microsoft.com/en-gb/azure/cosmos-db/partial-document-update (Python getting-started: https://learn.microsoft.com/en-gb/azure/cosmos-db/partial-document-update-getting-started?tabs=python)

## See Also

- [[Eclipse]] — primary consumer of CosmosDB configs
- [[core_api]] — reads from CosmosDB at runtime
- [[connector]] — references the same configs during pulls
- [[Azure]] — hosts CosmosDB
- [[Postman]] — used to reproduce template calls while investigating stale-schema bugs
- [[debugging-warehouse-loads]] — runbook that includes CosmosDB inspection
