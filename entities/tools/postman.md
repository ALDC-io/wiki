---
tags: [entity, tool, postman, api, debugging]
aliases: [Postman]
sources: [daily/2026-04-17.md]
created: 2026-04-17
updated: 2026-04-17
---

# Postman

API client used at ALDC for testing and debugging API calls during warehouse load investigations and connector development. Sits alongside [[Eclipse]] and [[core_api]] as the main tool for reproducing and debugging data-source calls locally.

## When Postman is used at ALDC

- **Debugging warehouse loads** — when a load fails, copy the [[Eclipse]] template's API call into Postman, execute it, and inspect the response to isolate whether the problem is on the source side, the connector side, or the warehouse-rebuild function in [[core_api]]
- **Reproducing template failures** — if [[CosmosDB]] holds an older template version that causes a new template to fail, Postman lets you manually fire the old/new call and compare responses
- **Local connector development** — use with [[core_api]] running locally to debug how the warehouse-rebuild functions handle responses (full workflow is still under investigation)

See [[debugging-warehouse-loads]] for the full step-by-step workflow.

## Setup

Full local setup for [[core_api]] work is documented in [[core-api-local-setup]]. Quick version:

1. Install Postman
2. Import **Steven's Dax and Core Collection** (new core — daily driver) and the three env files (`LOCAL`, `QA`, `PROD`) — see [[postman-collections]] for structure and `vault/postman-collections.md` for the raw JSON
3. For local runs, set `aldc_base_url = http://localhost:7071`, `x-function-key = none-for-local`, and pick a real Fusion or GEP `account_id`

## Collections at ALDC

See [[postman-collections]] for the full catalog. TL;DR:

- **Steven's Dax and Core Collection** — new-core daily driver
- **Analytic Labs Control v1 (LAWRENCE)** — old-core reference
- **Fusion Netsuite Sandbox API** — rarely used today

## See Also

- [[postman-collections]] — full collection/endpoint/variable reference
- [[core-api-local-setup]] — step-by-step runbook wiring Postman up to local [[core_api]]
- [[Eclipse]] — where templates live; Postman replays these
- [[core_api]] — hosts the warehouse rebuild functions Postman helps debug
- [[CosmosDB]] — stores Eclipse template/schema documents; source of version-mismatch bugs
- [[debugging-warehouse-loads]] — the operational runbook using Postman
- `vault/postman-collections.md` — collection JSON + env secrets (gitignored)
