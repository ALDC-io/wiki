---
tags: [process, deployment, release, checklist, client]
aliases: [Release Checklist, Client Release, Production Deploy Checklist]
sources: [Confluence TECH/1361903625 (Release checklist)]
created: 2026-04-17
updated: 2026-04-17
---

# Client Release Checklist

Generic deployment checklist for shipping a client change to production. Applies to any client; for the **GEP-specific** end-to-end walkthrough with phase-level detail and per-pitfall debugging, see [[gep-snowflake-pbi-deployment]].

## Pre-deploy — branch + code review

- [ ] Code is in the client's `user-testing` branch (e.g. `FUSION_92/user-testing`) — see [[git-branching-strategy]]
- [ ] Code has been internally tested, reviewed, and **client-approved**
- [ ] If the deploy requires connector code changes, deploy the connector agents to production — see [[connector-docker-deployment]]
- [ ] Compare documents in **Cosmos Test** against GitHub; resolve discrepancies
- [ ] If changes are needed: create a branch off `user-testing`, make the change, merge back into `user-testing`

## CosmosDB sync (prod)

- [ ] Copy new/modified **connection** documents from GitHub into **Production** [[CosmosDB]]; confirm they appear in [[Eclipse]]
- [ ] Copy new/modified **template** documents from GitHub into Production CosmosDB; confirm in Eclipse
- [ ] Pull data for all new templates (and modified templates as necessary); confirm the pulls succeed
- [ ] Reload historical data and run a warehouse reset **only if absolutely necessary**

## Snowflake

> **Data-share gotcha**: before any SQL view/table updates, capture the list of shared objects — `CREATE OR REPLACE TABLE/VIEW` removes them from the share. See [[snowflake-data-share-refresh]].

- [ ] For every modified table/view: check whether it participates in any data share
- [ ] Record the full list of shared objects (you'll re-share after the updates)
- [ ] Update all modified SQL files in [[Snowflake]]; run sanity queries
- [ ] If task scripts changed: hit the **graph refresh** button in Snowflake

## Re-share + downstream

- [ ] If the client has a data share set up (FUSION_92 and DISH_DUER as of 2025-03-14), **re-share** the affected objects to the share — they were dropped by the view/table replace
- [ ] Deploy any necessary [[Power BI]] models and reports
- [ ] If historical data needs reprocessing, requeue historical partitions in [[SSMS]] (SQL Server)

## Post-deploy — git + ticket hygiene

- [ ] Merge the client's `user-testing` branch into `main`
- [ ] If additional hotfixes were made on `user-testing` during testing, merge `user-testing` → `<CLIENT>/development` so dev catches up
- [ ] Update the Jira ticket with affected objects
- [ ] Update **Deployment Date** in the Service Item
- [ ] Update **Service Item Status**
- [ ] Update **Service Request Status**
- [ ] Add customer-facing comment on the Service Request (e.g. "Deployed to production YYYY-MM-DD")

## See Also

- [[model-deploy-production]] — generic production model deployment checklist (connections/templates, Snowflake views, PBI publish, client access grant)
- [[gep-snowflake-pbi-deployment]] — GEP-specific end-to-end deployment with per-phase pitfalls
- [[git-branching-strategy]] — `<CLIENT>/development` → `user-testing` → `main` model
- [[connector-docker-deployment]] — connector agent deploy
- [[snowflake-data-share-refresh]] — why shared objects drop on `CREATE OR REPLACE`
- [[data-share-pattern]] — Snowflake-to-Snowflake share setup
- [[debugging-warehouse-loads]] — runbook if template data isn't landing
- [[Power BI]] — model/report deploy target
- [[SSMS]] — historical-partition requeue
