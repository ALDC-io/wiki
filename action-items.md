---
tags: [action-items, todo, index]
updated: 2026-04-20
last_rescan: 2026-04-17
---



# Action Items

Central registry of things Paul still needs to do. Populated automatically when daily notes are ingested (explicit `type: action` notes and prose-detected items) and manually when you add a line directly.

## How items get here

1. **Explicit** — any `## Note` block tagged `type: action` becomes a line item. Guaranteed capture.
2. **Heuristic** — during `ingest today's notes`, Claude scans each note body for natural-language action phrases ("need to", "remember to", "follow up", "confirm", imperatives with a clear actor, etc.) and adds anything that looks actionable.
3. **Manual** — write a line directly in **Open** below. Use the same format for consistency.
4. **Rescan** — ask Claude to "rescan action items" to sweep all historical daily files for items that were missed.

## Format

```
- [ ] Description of what needs doing — from [[YYYY-MM-DD]] · ref: [[target-page]] · added YYYY-MM-DD
```

- `[[YYYY-MM-DD]]` is the backlink to the source daily file (Obsidian will render this as a clickable link)
- `ref:` is optional — use a `[[wikilink]]` to the related ticket, tool, concept, or client page if there's an obvious anchor
- `added` is the date the item entered this file — sort key for the Open list

## Completion (manual in Phase 1)

When done:
1. Toggle the checkbox: `- [ ]` → `- [x]`
2. Append ` · completed YYYY-MM-DD` to the line
3. Move the line from **Open** down to **Done**

Claude does not auto-complete items in this version. If you find yourself wanting that, ask and we'll add a `type: action-done` convention.

## Idempotency

On re-ingest or rescan, each extracted action is compared semantically against existing items sourced from the same daily file. Matching on intent rather than exact text — minor paraphrasing still counts as a duplicate. This keeps re-runs safe even though a single note can produce multiple distinct actions (which each need their own idempotency check).

---

## Open

- [ ] 🚨 **SECURITY** — Rotate 3 GEP Prefect Snowflake service account passwords (QA/TEST/PROD `*_DG1_PREFECT_SVC_DA8904DB`) — committed to git history in `prefect-connectors` PR #1 (`register_gep_blocks.py`). Non-prod: run `scripts/reset_passwords.py` on og35375. Prod: manual rotation on wj66376 via `PROD_DG1_CORE_ADMIN`. Also rotate the Prefect admin auth string (`PREFECT_API_AUTH_STRING`) committed in `create_tier_workers.ps1`. After rotation: update `vault/infra-credentials.md`, re-register blocks with new passwords via env vars. — ref: [[GP-218]] · added 2026-05-02
- [ ] 🚨 **SECURITY** — Rotate Fusion92 Cosmos DB keys (prod + dev + test) — all three environments exposed in `workflows/fusion_92/F92_notification_cron_update/.env` committed to git. Extract complete — see `vault/infra-credentials.md` § Fusion92 — Cosmos DB. Consider rewriting git history to remove the file (Paul's call). Add `.env` to `F92_notification_cron_update/.gitignore` — from [[workflows]] · ref: [[fusion92]] · added 2026-04-20
- [ ] 🚨 **SECURITY** — Scrub real secrets from `daily/2026-04-17.md` (pasted `local.settings.json` + PROD Postman env with live bearer tokens, CosmosDB keys, storage SAS, GPT key, Mailjet secret, workflow keys). Either redact the values or add `daily/` to `.gitignore` before next commit — from [[2026-04-17]] · ref: [[core_api]] · added 2026-04-17
- [ ] 🚨 **SECURITY** — Rotate credentials that were shared over Slack per Steven's note ("I should not be pasting it in slack lol"): service principal secret (`AZURE_CLIENT_ID=191bc893...`), CosmosDB account keys (prod/qa/test), storage SAS tokens, GPT key, Mailjet secret, `MASTER_CLIENT_SECRET` — from [[2026-04-17]] · ref: [[core_api]] · added 2026-04-17
- [ ] Physically complete the [[core-api-local-setup]] runbook: install Python 3.11, Azure Functions Core Tools, Azure VS Code extension, drop `local.settings.json` from vault, run `func start`, fire a Postman request against `http://localhost:7071` — from [[2026-04-17]] · ref: [[core-api-local-setup]] · added 2026-04-17
- [ ] Confirm the **test-env** core_api function app name (not captured in Steven's `local.settings.json`) — from [[2026-04-17]] · ref: [[azure-environments]] · added 2026-04-17
- [ ] Investigate what the **Fusion Workflows** section in Steven's Postman collection does — Steven's own note: "not sure what this does, don't think it is used often" — from [[2026-04-17]] · ref: [[postman-collections]] · added 2026-04-17
- [ ] Verify the service principal in `local.settings.json` (`AZURE_CLIENT_ID=191bc893...`) still has prod CosmosDB + storage access after Brayden's handoff — from [[2026-04-17]] · ref: [[core_api]] · added 2026-04-17
- [ ] Deepen understanding of the [[core_api]] repo so warehouse-rebuild functions can be edited confidently — from [[2026-04-17]] · ref: [[core_api]] · added 2026-04-17
- [ ] Follow up with Brayden to request Azure **owner** permissions (Brayden needs to reach out to Sean) — from [[2026-04-17]] · ref: [[Azure]] · added 2026-04-17
- [ ] Review per-client [[Confluence]] pages for [[SSMS]] setup, login, and job schedules — from [[2026-04-17]] · ref: [[SSMS]] · added 2026-04-17
- [ ] Pull the detailed Snowflake → SQL Server → PBI dataflow diagram from [[Confluence]] into this wiki — from [[2026-04-17]] · ref: [[data-pipeline-flow]] · added 2026-04-17
- [ ] Clarify the exact responsibility split between [[core_api]] and [[connector]] in the [[Prefect]] world (today's note: "connection through PBI — not core_api anymore" needs unpacking) — from [[2026-04-17]] · ref: [[connector]] · added 2026-04-17
- [ ] **GP-208 blocker** — discuss Sellercloud share staleness (frozen since 2026-03-05 07:01 PST) with another engineer; determine producer-side ownership and whether a warehouse/share reset is needed — ref: [[GP-208]] · added 2026-04-16
- [ ] **GP-208 blocker** — investigate what happened on 2026-03-05 07:01 PST to freeze the Sellercloud share (deploy? config change? producer failure?) — ref: [[GP-208]] · added 2026-04-16
- [ ] **GP-208 blocker** — decide whether to file a separate Jira ticket for the Sellercloud freshness incident since blast radius extends beyond GP-208 — ref: [[GP-208]] · added 2026-04-16
- [ ] Once Sellercloud share is restored: rerun TEST fact + extract, re-run QA queries Q1/Q3/Q7a/Q7, then resume GP-208 deploy plan steps 4–9 — ref: [[GP-208]] · added 2026-04-16
- [ ] Add Snowflake freshness monitor for shared raw sources — alert when `DAYS_STALE > N` to avoid future silent 40+ day freezes — ref: [[snowflake-data-share-refresh]] · added 2026-04-16
- [ ] Update [[accumulating-source-tables]] to distinguish "latest per key" (history facts) vs "latest global batch" (current-snapshot facts) — surfaced by GP-208 FBA CTE bug — ref: [[accumulating-source-tables]] · added 2026-04-16
- [ ] Confirm whether Eclipse templates still pull from galactica SQL server (Calendar, Financial Currency, Exchange Rates suspected) — from [[2026-04-16]] · ref: [[knowledge-transfer-log]] · added 2026-04-16
- [ ] Decide whether to deactivate Financial Currency template (confirm it's no longer in use) — from [[2026-04-16]] · ref: [[knowledge-transfer-log]] · added 2026-04-16
- [ ] Decommission galactica on-prem SQL server VM once confirmed unused — from [[2026-04-16]] · ref: [[knowledge-transfer-log]] · added 2026-04-16
- [ ] Obtain IP and VM access for the support host — from [[2026-04-16]] · ref: [[knowledge-transfer-log]] · added 2026-04-16
- [ ] Follow up with Brayden for support host VM access and credentials/IPs list — from [[2026-04-16]] · ref: [[knowledge-transfer-log]] · added 2026-04-16
- [ ] Decommission unused dev and qa docker hosts (keep prod and support) — from [[2026-04-16]] · ref: [[connector-docker-deployment]] · added 2026-04-16
- [ ] Research the best way to extract Confluence pages/spaces for ingestion into llmwiki — from [[2026-04-16]] · added 2026-04-16
- [ ] Integrate existing Confluence infrastructure/clients/networking notes into llmwiki — from [[2026-04-16]] · added 2026-04-16
- [ ] Refactor `marketing_fct_activity.sql` to include product_id and eliminate unknown brands in the PBI model — from [[2026-04-16]] · ref: [[GEP]] · added 2026-04-16
- [ ] GP-199: determine which Amazon API endpoint to use (Amazon Ads vs Selling Partner) — from [[2026-04-16]] · added 2026-04-16
- [ ] Put the Power BI model in GitHub after every manual deployment (easy-to-forget step) — from [[2026-04-16]] · ref: [[gep-snowflake-pbi-deployment]] · added 2026-04-16

## Done

- [x] Figure out the local [[Postman]] → [[core_api]] debug workflow — from [[2026-04-17]] · ref: [[debugging-warehouse-loads]] · added 2026-04-17 · completed 2026-04-17 (documented end-to-end in [[core-api-local-setup]])
- [x] Get the environment file for local-host connections — from [[2026-04-17]] · ref: [[azure-environments]] · added 2026-04-17 · completed 2026-04-17 (Steven shared his `local.settings.json`; stored in `vault/core-api-local-settings.md`)
- [x] Install and configure [[Postman]] for API testing / debugging (collection + variable structure) — from [[2026-04-17]] · ref: [[Postman]] · added 2026-04-17 · completed 2026-04-17 (collections + env files captured in [[postman-collections]] and `vault/postman-collections.md`; physical install tracked separately above)
