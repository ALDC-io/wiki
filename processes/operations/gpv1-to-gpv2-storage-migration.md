---
tags: [process, operations, azure, storage, migration, runbook, retirement]
aliases: [GPv1 GPv2 migration, storage account upgrade, GPv1 retirement, XTKT-BW8]
sources: [Azure Service Health advisory XTKT-BW8]
created: 2026-06-11
updated: 2026-06-11
---

# GPv1 → GPv2 Storage Account Migration (Azure retirement, deadline 2026-10-13)

Runbook for migrating ALDC's legacy **general-purpose v1** (`Kind: Storage`) Azure
storage accounts to **general-purpose v2** (`Kind: StorageV2`) ahead of Microsoft's
retirement. Tracking ID **XTKT-BW8** (Azure portal → Service Health → Health advisories).

## Why this matters

- **2026-10-13:** Microsoft retires GPv1 / blob-only storage accounts.
- **After the deadline:** any remaining GPv1 account is **auto-migrated** to GPv2 — *"may
  result in higher billing costs."* Migrating manually first lets us verify each account
  and control timing instead of taking an uncontrolled flip on prod.
- **New GPv1 creation is blocked** from 2026-10-13.
- **Databricks-managed accounts are out of scope** — Microsoft migrates those itself, on
  its own schedule, with separate notifications. Our one Databricks account
  (`dbstorageghioaqwue3tuq`, Dev) is already StorageV2 anyway, so this is moot for us.

## The migration itself (what it actually is)

GPv1 → GPv2 is an **in-place upgrade**, not a data move:
- Same account name, same endpoints, same keys, same connection strings — **nothing
  downstream needs to be reconfigured** (connector configs, Function `AzureWebJobsStorage`,
  Snowflake ingest queries, portal blob references all keep working).
- **One-way and irreversible** — you cannot downgrade GPv2 back to GPv1.
- Effectively instant, no data egress, no downtime for the data plane.
- Command:
  ```bash
  az storage account update -n <account> -g <rg> --subscription "<sub>" --upgrade-to-v2
  # verify
  az storage account show -n <account> -g <rg> --subscription "<sub>" --query kind -o tsv  # -> StorageV2
  ```
  (Portal equivalent: Storage account → **Configuration** → "Upgrade to GPv2".)

**Billing caveat:** GPv2 prices transactions per-operation; storage-at-rest is cheaper.
For these small LRS accounts (≤2.6 GB, low transaction volume) the net change is
negligible. There is no tier/redundancy decision to make at upgrade time — it preserves
the existing SKU.

## Permissions

The upgrade needs `Microsoft.Storage/storageAccounts/write`. Paul has **read/developer in
Production 2, not owner** (see [[Azure]] § Access). The **prod** accounts will likely need
an org-admin (Sean / Vlad / Mike) to execute or to grant a temporary role — same bottleneck
pattern as the clients-repo CODEOWNERS lock. Dev/Test/QA may already be writable; confirm
per subscription before the deadline, not at it.

## Inventory & orphan triage (captured 2026-06-11)

Signals: `UsedCapacity` (data at rest) + `Transactions` over the prior 7 days +
creation time + name/tag. **20 GPv1 accounts** across 4 subscriptions.

### Tier A — LIVE, must migrate (active, real data + traffic)

| Account | Sub | Data | 7d tx | Role / risk |
|---|---|---|---|---|
| `aldcprodstaccore1c01` | Production 2 | 2.6 GB | live | **prod core_api `AzureWebJobsStorage` + connector transport — HIGH RISK, do last, smoke-test** |
| `aldcprodfnapf921c01` | Production 2 | 674 MB | live | **prod Fusion92 function-app backing — HIGH RISK** |
| `aldcqastaccore1c01` | Quality 1 | 832 MB | live | QA core_api |
| `aldcteststaccore1c01` | Test 1 | 248 MB | live | test core_api |
| `aldcteststaccore1c03` | Test 1 | 241 MB | 2992 | test core_api (active) |
| `aldctestfnapf921c01` | Test 1 | 17 MB | live | test Fusion92 function backing |
| `aldctestfnaptrigger8d5a` | Test 1 | 7 MB | live | test function-trigger backing |
| `aldcdevstaccore1c01` | Development 2 | 121 MB | live | dev core_api (DG1) |
| `aldcdevstaccore2c01` | Development 2 | 121 MB | live | dev core_api (DG2) |
| `aldcdevstaccore3c01` | Development 2 | 77 MB | live | dev core_api (DG3) |
| `aldcdevfnapfusion2c01` | Development 2 | 7 MB | live | dev Fusion92 function backing |

### Tier B — IDLE with data, verify → migrate or delete

Data present but **0 transactions in 7 days** → superseded instances. Confirm nothing
reads them (check for a paired live `...c01`/`...c03`), then either migrate (safe) or
delete (reclaim). Default to **migrate** if ownership is unclear — deletion is the
irreversible move, not the upgrade.

| Account | Sub | Data | 7d tx | Note |
|---|---|---|---|---|
| `aldcprodstaccore1c02` | Production 2 | 1.0 GB | 0 | old prod core instance 02 — verify before any delete |
| `aldcteststaccore1c02` | Test 1 | 210 MB | 0 | old test core instance 02 |

### Tier C — auto-provisioned / likely orphan (low value)

Auto-named hex-suffix accounts, ~1.4–7 MB, only background/heartbeat transactions. This is
the fingerprint of **Azure Cloud Shell** storage and/or **function deployment-artifact**
accounts. Either migrate in bulk (zero app risk) or delete after confirming origin (Cloud
Shell ones simply regenerate on next use).

| Account | Sub | Data | 7d tx | Note |
|---|---|---|---|---|
| `aldcprodrsgp1cad02` | Production 2 | 7 MB | 416 | confirm Cloud Shell / deploy artifacts |
| `aldcprodrsgp1c93f9` | Production 2 | 1.4 MB | 817 | likely Cloud Shell |
| `aldcprodrsgp1e9a0f` | Production 2 | ~0 | 509 | near-empty; eastus |
| `aldctestrsgp1ea34e` | Test 1 | 1.4 MB | 352 | likely Cloud Shell; eastus |
| `aldctestrsgp1cafd0` | Test 1 | 1.4 MB | 351 | likely Cloud Shell |
| `aldcqarsgp1ca59b` | Quality 1 | 1.4 MB | 0 | likely Cloud Shell — idle |
| `aldcdevfnapfusion2c02` | Development 2 | 841 B | 0 | **near-empty + idle — strong delete candidate** (paired with live `...2c01`) |

## Execution order (low blast-radius first)

1. **Tier C (delete candidates):** confirm origin; delete `aldcdevfnapfusion2c02` and any
   confirmed Cloud Shell accounts (or leave Cloud Shell to auto-migrate — harmless). This
   shrinks the real work-list.
2. **Dev** (`aldcdevstaccore1c01/2c01/3c01`, `aldcdevfnapfusion2c01`) — upgrade, smoke-test a
   connector pull + function start.
3. **Test** (`aldcteststaccore1c01/03`, `aldctestfnapf921c01`, `aldctestfnaptrigger8d5a`) —
   upgrade, verify Eclipse/core_api + Fusion92 function still run.
4. **QA** (`aldcqastaccore1c01`).
5. **Tier B:** decide migrate-vs-delete on `...c02` idle accounts with an owner in the loop.
6. **Prod, last, in a window, one at a time:**
   - `aldcprodfnapf921c01` → confirm Fusion92 prod function still triggers + writes.
   - `aldcprodstaccore1c01` → confirm core_api healthy, connector → blob → Snowflake ingest
     path intact, no Function host restart errors. This is the highest-risk account
     (`AzureWebJobsStorage` for prod core_api) — have the org-admin execute, watch Function
     logs immediately after.

## Verification per account (evidence gate)

After each upgrade:
- `az storage account show ... --query kind` → `StorageV2`.
- For function-backing accounts: function app **still Running**, no `AzureWebJobsStorage`
  host errors in the next invocation.
- For `staccore`/connector accounts: next connector pull lands in blob and Snowflake ingest
  succeeds (no break in the transport-layer path described in [[Azure]] §
  "Storage Accounts").

## Re-run the inventory query

```bash
for sub in "Development 2" "Test 1" "Quality 1" "Production 2"; do
  az storage account list --subscription "$sub" \
    --query "[?kind=='Storage'].{name:name, rg:resourceGroup, loc:primaryLocation}" -o table
done
```
When this returns empty for all four subscriptions, the migration is complete.

## See Also

- [[Azure]] — subscription model, storage-account roles, access/ownership state
- [[credential-exchange-function-deploy]] — uses `aldcteststac1cda8904db` (already GPv2)
- [[Snowflake]] — consumer of the connector → blob transport layer
