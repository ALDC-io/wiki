---
tags: [process, deployment, production, power-bi, snowflake]
aliases: [Model Deploy to Production, Production Deployment]
sources: [Confluence CLIEN/1244561414]
created: 2026-04-18
updated: 2026-04-18
---

# Model Deploy to Production

Checklist for deploying a new or updated data model to production. The specific example below is from a 2024 Fusion92 deployment (CUST-760), but the pattern is generic.

## Step 1 — Connections and Templates into Production

For each data source integration, ensure the connection and template are in production and tested. Example from Fusion92 deployment:

| Integration | Connection | Template | Tested | Branch / PR |
|---|---|---|---|---|
| Smartsheets (CUST-760) | [ ] | [x] | [ ] | clients/pull/135 |
| Flight Check / Google Firebase (CUST-556) | [x] | [x] | [ ] | clients/pull/136 |
| Google Ads — Windsor (CUST-672) | [x] | [x] | [ ] | clients/pull/138 |
| Google DV360 — Windsor (CUST-672) | [x] | [x] | [ ] | clients/pull/138 |
| Google Campaign Manager — Windsor (CUST-672) | [x] | [x] | [ ] | clients/pull/138 |
| Meta Ads (CUST-593) | [x] | [x] | [ ] | clients/pull/137 |

## Step 2 — Deploy Data Warehouse Views to Production

- [ ] Create views in Snowflake Production (merge branch to `main`, run warehouse deploy)
- [ ] Smoke test views in Snowflake — confirm data is flowing through

## Step 3 — Test the Activation Model

- [ ] Add report document to Azure Prod (CosmosDB report collection)
- [ ] Confirm model refresh works and pulls data
- [ ] Publish model in Prod PBI workspace
- [ ] Create About Page in Analyze Excel
- [ ] Smoke test the model in Excel (navigate, filter, verify data)
- [ ] Post Excel model file to Eclipse Prod

## Step 4 — Grant Production Access to Client Users

- [ ] Send invites to authorized client users (coordinate with Account Manager for the user list)

## See Also

- [[gep-snowflake-pbi-deployment]] — full GEP-specific deploy runbook (Snowflake → PBI)
- [[client-release-checklist]] — generic pre-release checklist
- [[Power BI]] — PBI workspace management and model refresh
- [[Snowflake]] — warehouse view deploy
- [[eclipse]] — posting model to Eclipse
- [[fusion92]] — Fusion92 client context (original deployment example)
