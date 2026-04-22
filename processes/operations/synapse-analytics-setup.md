---
tags: [process, operations, synapse, cosmosdb, azure, analytics]
aliases: [Synapse Analytics Setup, Synapse Link Setup]
sources: [Confluence CORE/960397353]
created: 2026-04-18
updated: 2026-04-18
---

# Synapse Analytics Workspace Setup

> *Sourced from CORE Confluence (2022-06) — verify current state.*

How to connect Azure Synapse Analytics to CosmosDB Analytical Store (Synapse Link) for serverless SQL querying of core_api collections.

## Prerequisites

- Synapse Workspace provisioned (note: ARM Owner role is NOT sufficient — permissions must be granted inside Synapse Studio)
- Synapse Link enabled on target CosmosDB containers (turn on per-container in the Azure Portal)
- CosmosDB read-only key for the server credential

## 1. Grant permissions in Synapse Studio

If you hit "Failed to Load / 403" errors:

1. Open Synapse Studio
2. **Manage → Access Control**
3. Add the user with appropriate workspace role (Studio-level, not ARM-level)

## 2. Create linked service

1. Synapse Studio → **Manage → Linked Services → New**
2. Choose **Azure Cosmos DB (SQL API)**
3. Configure: CosmosDB account name, database (`core`), Direct connection mode
4. Containers now appear under **Data → Linked**

## 3. Create server credential

Allows the serverless SQL pool to authenticate against CosmosDB:

```sql
CREATE CREDENTIAL [<cosmos_account_name>]
WITH IDENTITY = 'Cosmos DB',
SECRET = '<cosmos_read_only_key>';
```

## 4. Create database and views

Create a database in the serverless SQL pool (from the **Data** tab), then author views using `OPENROWSET`:

### Example: Account view

```sql
CREATE OR ALTER VIEW ALDC_ACCOUNT AS
SELECT *
FROM OPENROWSET(
  PROVIDER = 'CosmosDB',
  CONNECTION = 'Account=aldctestcsdb1c01;Database=core',
  OBJECT = 'account',
  SERVER_CREDENTIAL = 'aldctestcsdb1c01'
)
WITH (
  id           VARCHAR(256),
  tier         VARCHAR(256),
  short_code   VARCHAR(256),
  full_name    VARCHAR(256),
  environment  VARCHAR(256),
  scan         VARCHAR(256),
  industry     VARCHAR(256),
  billing_status VARCHAR(256),
  master_timezone VARCHAR(256),
  provider     VARCHAR(256),
  provider_tenant VARCHAR(256),
  region       VARCHAR(256),
  address      VARCHAR(256),
  country      VARCHAR(256) '$.address.country',
  contact      VARCHAR(256)
) AS [account]
CROSS APPLY OPENJSON(contact)
WITH (
  name  VARCHAR(100),
  email VARCHAR(100)
) AS a;
```

Adapt `OBJECT`, `SERVER_CREDENTIAL`, and the `WITH` clause for other collections (capacity, work_template, etc.).

## Troubleshooting

| Symptom | Fix |
|---|---|
| Containers not visible | Verify Synapse Link is enabled on the CosmosDB container |
| Permission denied / 403 | Grant permissions in Synapse Studio (not ARM) |
| Slow queries | Use analytical store partitioning for large containers |

## See Also

- [[cosmosdb-schema]] — collection schemas for constructing `WITH` clauses
- [[CosmosDB]] — CosmosDB instances per environment
- [[deployment-groups]] — environment resource names (e.g., `aldctestcsdb1c01`)
