---
tags: [workflow, navira, gep, snowflake, marketing, windsor, schema-design]
aliases: [Navira DWH Data Landing, Marketing Schema Design]
created: 2026-05-28
updated: 2026-06-01
---

# Navira DWH Data Landing — Marketing Schema + Entity Segmentation

Replaces Phase 0 (Prefect Foundation) as the active priority. Uses existing Eclipse pipeline to get Google Ads, Meta/Facebook, and agency customer data flowing into Snowflake.

## Tickets

| Ticket | Summary | Status | Notes |
|---|---|---|---|
| GP-225 | Unified Marketing Schema Design | In Progress | Mock data + warehouse views in TEST_DG1_GEP_DEV. **2026-06-01 (pm-2): Tier-1 revenue DONE in DEV** — added Windsor `conversions_value` (Google) + `actions_purchase`/`action_values_purchase` (Meta) to templates + DEV fact Branch 6/7; row-split test PASS (no PK fan-out, spend stable); DEV fact now COST $29,339 + SALES $115,533, reconciled to live API (−0.18% spend / −1.96% revenue = attribution lag, no double-count). |
| GP-226 | Windsor Google Ads + Meta | In Progress | **Connected 2026-05-29** — Navira authorized 6 Google + 3 Meta accounts (co-user). Real data validated → ENTITY_CODE='NAVIRA', 0 UNKNOWN, schema 1:1. **Fusion92 cross-tenant gates BUILT + Gate B PROVEN 2026-05-29**. **2026-06-01 (am) activation prep DONE:** connector code deployed (`:development` image built w/ `account_ids` filter); Windsor conn + 2 templates created in TEST Cosmos, `inactive`, topic→`*_DEV` (conn `8e558ceb…`, ADR-001 linked). **2026-06-01 (pm) — TEST Eclipse orchestration model mapped + Write #1 done:** fleet dormancy **proven at consumer layer** (no TEST raw landing write since 2026-03-03/03-12; cloud scheduler/requeue alive but executors dead). Enqueue→pick→land model verified in `core_api`: `work_scan` (gated by acct `scan=true` + `schedule_block` window) creates partitions + enqueues to the connection's Azure Storage Queue; `/work/pick` is scoped by the **agent's `connection_authorized`** list. **Write #1 (gated, applied):** created Windsor-scoped agent `gep-windsor-test` (authorized for ONLY conn `8e558ceb` → cannot drain the 46-template GEP backlog) + flipped the 2 templates `active`, bounded `min_date 2026-05-25` (~7 Google daily + ~1–2 Meta monthly, vs ~520 from 2024-01-01). `schedule_block` = "Small Evening Window" 18:00–00:00 ET (`work_block`); lift = toggle `schedule_block`↔`_schedule_block`. **NEXT (workstation):** lift block → `work/scan` scoped to our 2 template_ids → run `gep-windsor-test` executor on `:development` → land `*_DEV` → restore block → DEV fact (`WAREHOUSE_TEST_GP226`) + isolation test (NAVIRA-only; live fact stays 807,585). SPEND-ONLY today. |
| GP-222 | Amazon Ads UK/CA + Sponsored Display | In Progress | Stays on Eclipse, not Prefect |
| GP-254 | Lectric eBikes Integration — Agency Test | In Progress (Development) | **First agency SP-API customer.** Creds validated (US/CA/MX/BR) under new public solution app — resolves I-1. Eclipse conn + 4 templates + staging fact built (code only). Segmentation design validated on TEST_DG1_GEP_DEV clone w/ mock data. |

## Testing Strategy / Build Environment

**Updated 2026-05-29 — clone-only is LIFTED.** Initial design + Lectric/Windsor segmentation were validated in the `TEST_DG1_GEP_DEV` clone (og35375) with mock then real data. Now that real Google/Meta data is available and the clone fundamentally can't exercise the Eclipse ingestion path (Eclipse never writes to the clone), the build moves to the **real `TEST_DG1_GEP`**:

- **Build in an isolated DEV schema** inside TEST_DG1_GEP (e.g. `MARKETING_DEV`) — do NOT mutate the live `WAREHOUSE`/`REPORT_COMMON` objects that PBI / Navira UAT read until validated, then **promote**.
- **Raw data lands in the real Eclipse target schemas** in TEST (`GOOGLE_ADS` / `META` / `AMAZON_LECTRIC`).
- **Eclipse connector activation into TEST is in-scope this cycle — but the [[project_windsor_fusion92_filter|Fusion92 cross-tenant filter]] MUST be built + tested FIRST.** One ALDC Windsor key pulls ALL clients' accounts (39 Google + 18 Meta Fusion92 accounts seen); leakage into the shared test warehouse is the catastrophic-failure mode.
- The `TEST_DG1_GEP_DEV` clone remains available as a throwaway scratchpad.

Promotion: DEV schema in TEST_DG1_GEP (validate) → live `WAREHOUSE`/`REPORT_COMMON` in TEST_DG1_GEP → PROD_DG1_GEP.

## Design Decisions

- **Entity segmentation — two paths, one ENTITY_CODE**:
  - **Marketing** (Google/Meta/Amazon Ads): rows carry platform account ids → `SHARED_DIM_ENTITY` CSV-map join on PLATFORM+ACCOUNT_ID. Built in MARKETING_FCT_ACTIVITY Branches 6/7.
  - **Sales** (Amazon SP-API): all-orders report has NO seller/account column → segment by **landing schema** (`AMAZON_<ENTITY>`) + `ENTITY_CODE` literal in the fact. The CSV map does NOT apply to sales.
  - **Scaling**: per-agency UNION branches in fact views won't scale; replace with a generated view (proc scanning INFORMATION_SCHEMA for `AMAZON_*` schemas) once agency #2 lands. Build explicitly for one agency now.
  - Values: NAVIRA, LECTRIC, etc.
- **Agency model**: Lectric onboards under a NEW public SP-API solution app (`amzn1.sp.solution.…`), separate from GEP's private app (partner `A3VJEVLAWT2I1E`). Each agency customer = own Eclipse connection + own `AMAZON_<ENTITY>` topic/schema; data shares the GEP warehouse (account da8904db), segmented by ENTITY_CODE. No per-agency DB.
- **Marketing schema**: Extend existing MARKETING_FCT_ACTIVITY with UNION ALL branches for Google Ads, Meta, and Sponsored Display (alongside existing Amazon SB/SP).
- **Windsor data landing**: New GOOGLE_ADS and META schemas. Table names match Eclipse convention: {topic}.{category}_{table}.
- **Platform detail fact**: New MARKETING_FCT_PLATFORM_DETAIL for platform-specific KPIs (ROAS, reach, impression share, etc.).
- **Cross-channel ROAS — tiered model** (locked 2026-05-29, see [[cross-channel-marketing-attribution]]): per-channel ROAS from platform-attributed value (Tier 1, via [[GP-225]] Windsor field fix) is *not* a source of truth — it double-counts and won't reconcile to orders. Source of truth = **blended MER + Amazon product-grounding**, denominator = actual `SALES_FCT_*` orders, built as a `REPORT_COMMON.MARKETING_EFFICIENCY` reconciliation view (a Phase-1 build beyond GP-225). Decisions: MER = headline metric · reporting currency **USD** · Amazon window **30d** · Google/Meta product linkage **deferred to gated Phase 2**.

## Files Created/Modified (clients repo)

### New
- `GEP/snowflake/mock/mock_google_ads_raw.sql`
- `GEP/snowflake/mock/mock_meta_raw.sql`
- `GEP/snowflake/mock/mock_entity_mapping.sql`
- `GEP/snowflake/warehouse/shared_dim_entity.sql`
- `GEP/snowflake/warehouse/marketing_fct_platform_detail.sql`
- `GEP/eclipse/connections/windsor.json`
- `GEP/eclipse/templates/windsor/google_ads.json`
- `GEP/eclipse/templates/windsor/meta_ads.json`

### New (2026-05-28 — Lectric agency onboarding, GP-254)
- `GEP/eclipse/connections/amazon_seller_central_lectric.json` — Lectric LWA creds (inline; ⚠️ security debt), account_id da8904db
- `GEP/eclipse/templates/amazon_lectric/all_orders_report_{us,ca,mx,br}.json` — topic `AMAZON_LECTRIC`, connector `amazon_sellercentral_v1`
- `GEP/snowflake/warehouse/sales_fct_lectric_amazon_orderline.sql` — self-contained, ENTITY_CODE='LECTRIC', reads AMAZON_LECTRIC.CURRENT_REPORT_ALL_ORDERS_*
- `GEP/snowflake/mock/mock_lectric_amazon_raw.sql` — mock all-orders for clone validation (Eclipse never writes to clone)
- `aldc-launchpad/scripts/_deploy_lectric_clone.py` — clone deploy+validate (local-only)
- Vault: `lectric--amazon-spapi--*` propagated to aldc-vault-{dev,test,qa,prod}

### Modified (2026-05-28)
- `GEP/snowflake/mock/mock_entity_mapping.sql` — removed wrong Google/Meta Lectric placeholders; documented sales=schema-based segmentation

### Modified
- `GEP/snowflake/warehouse/marketing_dim_platform.sql` — added Google Ads, Meta, SD
- `GEP/snowflake/warehouse/marketing_dim_campaign.sql` — added Google/Meta/SD campaigns
- `GEP/snowflake/warehouse/marketing_fct_activity.sql` — 7 branches + ENTITY_CODE + UK profile

## Session Log

| Date | Summary |
|---|---|
| 2026-05-28 | Initial design. Created mock data, warehouse views, Eclipse templates. Feature branch: `feature/paulrussell/gp-225/marketing-schema-design` |
| 2026-05-28 (pm) | Re-scoped GP tickets (Prefect shelved). **Lectric agency SP-API onboarding (GP-254):** validated creds (US/CA/MX/BR, new public solution app), propagated secrets to all env vaults, built Eclipse conn + 4 templates + staging fact + mock, **validated segmentation on TEST_DG1_GEP_DEV clone with mock data** (ENTITY_CODE='LECTRIC', multi-currency, cancelled filter ties out). Client confirmation email sent. Jira GP-254/225/226 commented. |
| 2026-05-29 | **Navira Windsor connected** (GP-226): authorized 6 Google + 3 Meta accounts on the call; pulled REAL data → loaded to clone → validated ENTITY_CODE='NAVIRA', 0 UNKNOWN, schema 1:1. Confirmed **spend-only** (revenue=0; ROAS needs Windsor conversion-value fields — see [[cross-channel-marketing-attribution]]). Confirmed **one ALDC Windsor key returns all clients' accounts** → Fusion92 filter required. **Decision: lift clone-only → build in isolated DEV schema in TEST_DG1_GEP; activate Eclipse after Fusion92 filter.** Full-fact deploy blocked by GP-199 extract DDL not in repo. Jira GP-226 commented. |
| 2026-05-29 (pm) | **Fusion92 gates built + proven; branch/Jira setup; ticket triage** (Opus, plan-first). Branches: `clients` `feature/paulrussell/gp-225/marketing-efficiency-model` (off GEP/development + Lectric files + GP-199 asin_map DDL); `connector` `feature/paulrussell/gp-226/windsor-account-filter`. **Fusion92 defense-in-depth (decided: connector + warehouse):** Gate A — verified Windsor `filter=[["account_id","in",[...]]]` (JSON-array; 45→6 Google, 19→3 Meta), wired `windsorai_v1` `options.account_ids`→filter + added account_ids to both templates; Gate B — Branch 6/7 `LEFT JOIN`→`INNER JOIN SHARED_DIM_ENTITY`. **Gate B PROVEN on clone** (injected Fusion92 acct dropped, Navira 1350 rows survive). Tracked isolation test `GEP/snowflake/scripts/gp226_fusion92_isolation.sql`. Fixed mocks to real Navira ids. **Jira:** rewrote GP-225/226/222/230/231 descriptions (Prefect→Eclipse/tiered-attribution reality), stripped `prefect` labels, relabelled+updated GP-254/265/199, moved GP-225/230/231/265→Development; created **GP-277** (MARKETING_EFFICIENCY). Investigated deploy mechanics (see Next Session). |
| 2026-06-01 (pm-2) | **Validation pull → shortest backfill → GP-225 Tier-1 revenue** (Opus, gated; block lifted only at run-time, restored after each pull). **Bounded pull (c0–c3):** lifted block → scoped scan → ran `gep-windsor-test` executor on workstation → landed `GOOGLE_ADS_DEV`/`META_DEV` → restored. All **6 isolation checks PASS**, Navira-only (Gate A proven end-to-end on landed data), nothing-else-ran (other raw schemas unchanged since 2026-03-12), no-regression (live passthrough has 0 Google/Meta rows). **Shortest backfill (c4):** both sources from `min_date 2026-04-01` (~61 Google daily + 3 Meta monthly; 64 merges, 0 errors); fact 1,760 rows. **GP-225 Tier-1:** revenue fields added (row-split test PASS, spend-stable) → DEV fact COST $29,339 + SALES $115,533, reconciled to API within attribution-lag tolerance. **Mechanics learned:** `work_activate` TRICKLES partition creation (1→3→9→+10/scan; backfill = loop scan+drain); workstation SSH = install pubkey + `BatchMode` (ControlMaster mux flaky); Windsor history — Google to 2021 (acct 389), **Meta only 2026-04-20+ (Bridgford has none; 37-mo API cap)**. **PITFALL:** dropping the landing schema + `max_threads=3` raced Eclipse's schema versioning → orphaned `GOOGLE_ADS_CAMPAIGN_{2,3,4}`, no `CURRENT_` view; recovered with a DEV-only PK-dedupe consolidation view (verified disjoint PKs, reconciled to API). **Correct fix:** don't drop the landing schema to re-land, or land first partition at `max_threads=1`. State clean, block ENFORCED. |
| 2026-06-01 (pm) | **TEST Eclipse orchestration mapped + Write #1 (scoped agent + activation) applied** (Opus, gated). Read-only probes: (a) fleet dormancy **proven at consumer layer** — no TEST raw landing-table write since 2026-03-03/03-12 despite cloud scheduler re-queuing partitions today 11:19Z (scheduler/requeue alive, **executors dead**); (b) GEP runs **46 active templates** + other accounts (NetSuite/Viant/LinkedIn/PCG) → reviving the persistent fleet would drain the whole multi-account backlog (rejected). Mapped enqueue→pick→land in `core_api`: `work_scan` (gated by acct `scan=true` + `schedule_block`) → `work_activate` creates partitions per `min_date` → enqueue to the connection's Azure Storage Queue; `/work/pick` scoped by **agent `connection_authorized`** (active conns only). `schedule_block`="Small Evening Window" 18:00–00:00 **ET** → `work_block` (blocks BOTH scan + pick); lift = `account_change_block_status` toggles `schedule_block`↔`_schedule_block`. `/v1/work/scan` is a callable endpoint (agent creds suffice — same `check_auth_service("work")` gate as pick) accepting `template_id`+`partition_limit` → surgical Windsor-only enqueue. **Write #1 (applied + verified):** `_deploy_windsor_cosmos_test.py --apply --agent --activate --min-date 2026-05-25` → created agent `gep-windsor-test` (conn `8e558ceb` only; conn `agent_authorized=null` so our agent may pick) + 2 templates `active`, topic `*_DEV`, bounded. Rollback `--delete --agent-delete`. **No data landed yet** (block still in force = no execution). New scripts (local, not committed): `_probe_test_executors.py`, `_probe_test_partitions.py`, `_probe_test_landing_recency.py`, `_probe_schedule_block.py`, `_probe_account_block.py`, `_probe_gep_window.py`, `_probe_agent_pk.py`, `_verify_write1.py`, `_verify_conn_authz.py`; extended `_deploy_windsor_cosmos_test.py` (--agent/--activate/--min-date). **NEXT = workstation run** (see Next Session). |
| 2026-06-01 | **Windsor activation prep — 2 of 3 deploys done; topology discovered** (Opus, gated: rollback+approval before every deploy). **① Connector code DEPLOYED:** FF-merged `97979df`→`development`, `docker-publish.yml` built `:development` image w/ Gate A `account_ids` filter (rollback pt `4318bb1`). **② Cosmos config STAGED inactive:** scoped reconciler-grade deploy script (`_deploy_windsor_cosmos_test.py` — git JSON source, ADR-001 assert, `topic→*_DEV` override, plan/apply/delete) created conn `8e558ceb…` + 2 templates in TEST Cosmos (`aldctestcsdb1c01`/core, RG `aldctestrsgp1c`, sub Test 1), Google→`GOOGLE_ADS_DEV`/Meta→`META_DEV`, all inactive. **KEY DISCOVERY:** `TEST…WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY` is a **passthrough to PROD** (807,585 rows) — PBI test model reads PROD's fact; dev SQL never deployed to TEST/PROD; raw pull is INERT to PBI; promotion = PROD-level change (separate ticket). No GOOGLE_ADS/META schemas in TEST; SHARED_DIM_ENTITY + EXTRACT_AMAZON_* absent → DEV fact is marketing-only. **TEST doesn't self-ingest (prod share) → test agent fleet dormant** → must verify/revive before activating. DEV-build + isolation harness authored (`_gp226_dev_build.sql` → `WAREHOUSE_TEST_GP226`, `_gp226_dev_isolation.sql`, `_check_test_agent_status.py`). |

## Next Session (pick up here) — PLAN-FIRST implementation

Environment (2026-05-29): build in an **isolated DEV schema in TEST_DG1_GEP**; **Fusion92 filter is the hard first step** before any Eclipse activation. (Full boot prompt held by Paul.)

1. ✅ **Fusion92 cross-tenant filter — BUILT + Gate B PROVEN (2026-05-29).** Defense-in-depth: Gate A connector `account_ids`→Windsor `filter` (committed `connector` 97979df) + templates; Gate B warehouse INNER JOIN (committed `clients` 7d1bf177). Tracked test `GEP/snowflake/scripts/gp226_fusion92_isolation.sql`. Remaining = the **end-to-end test on landed data**, which happens at activation (step 2). See [[project_windsor_fusion92_filter]].
2. **✅ DEPLOYS ①, ② & Write #1 DONE (2026-06-01).** ① Connector `:development` image w/ Gate A filter. ② Windsor conn + 2 templates staged. **Write #1:** scoped agent `gep-windsor-test` + 2 templates `active`, topic `*_DEV`, `min_date 2026-05-25`. **✅ c0–c4 DONE (2026-06-01 pm-2)** — bounded validation pull + shortest backfill (both sources from `2026-04-01`) landed + validated (6/6 isolation PASS, Navira-only, no-regression). Original runbook kept below for reference:**
   - **(c0) Lift the block** (Write #2): toggle GEP `schedule_block`→`_schedule_block` (currently 18:00–00:00 ET blocks scan+pick). Reversible. Safety: execution is gated by agent authorization, so only `gep-windsor-test` (Windsor-only) can run — **do NOT wake `dcgeneral`/the fleet**; only scan **our 2 template_ids**.
   - **(c1) Scan (enqueue) on workstation** — for each template_id (`5a452874…` Google, `bbcd741b…` Meta): `docker run --rm -e agent_id=gep-windsor-test <img> python3 -c "from core import Core,ConfigHandler; print(Core(ConfigHandler('./config/config.json').get_local_configuration()).get_api('/work/scan',{'account_id':'da8904db','template_id':'<id>','partition_limit':10}))"`. Expect ~7 Google + ~1–2 Meta partitions.
   - **(c2) Run scoped executor** — `docker run --rm -e agent_id=gep-windsor-test -e loop=TRUE -e max_threads=1 -e verbose=TRUE -e sleep=15 <img> python3 -u executor_master.py`; stop when it prints `NO WORK ~~~ SLEEPING`. Overrides the image CMD `/app/scripts/run.sh` (fine for Windsor — HTTPS + blob + Snowflake, no VPN/ODBC). Lands in `GOOGLE_ADS_DEV`/`META_DEV`.
   - **(c3) Restore the block**; build DEV fact (`_gp226_dev_build.sql` → `WAREHOUSE_TEST_GP226`) → `_gp226_dev_isolation.sql` (all 6 PASS, NAVIRA-only). No-PBI proof: live passthrough fact stays **807,585** rows. **Promotion to the live/PROD fact = separate ticket** (PROD-level; passthrough). See [[project_test_prod_share]], [[project_windsor_fusion92_filter]].
   - **(c4) Then widen `min_date` for full historical backfill** — first probe Windsor API data availability per platform/account (Meta limited ~13mo w/ breakdowns; Google further back) to set min_date to what's retrievable. Re-scan + re-run scoped.
3. **✅ Tier 1 — Windsor revenue fields (GP-225) — DONE in DEV (2026-06-01 pm-2).** Added `conversions_value` (Google) + `actions_purchase`/`action_values_purchase` (Meta) to templates + DEV fact Branch 6/7. Row-split test PASS (no PK fan-out, spend stable). DEV fact COST $29,339 + SALES $115,533, reconciled to API. **Remaining:** update committed mock SQL to match; commit template revenue-field additions (clients branch, ask Paul); a clean single-version re-land to retire the SRC consolidation shim.
4. **Phase 1 — `REPORT_COMMON.MARKETING_EFFICIENCY`** (in DEV schema) — all-channel blended MER (Tier 2) + Amazon product-grounded (Tier 3 via `SHARED_DIM_PRODUCT_BASE`); spend ⨝ `SALES_FCT_*`; USD consolidation; ENTITY_CODE multi-tenant + isolation test. File the new ticket. See [[cross-channel-marketing-attribution]].
5. **Agency (Lectric)** — activate Seller-Central Eclipse into TEST (same filter discipline); derive per-entity product dim from the all-orders report; fold into the model (T2 now, Amazon T3 once product dim exists).
6. **Adjust yesterday's implementation** — mock data + Lectric design (`sales_fct_lectric_amazon_orderline`, `mock_lectric_amazon_raw`) for the DEV-in-TEST + Tier 2/3 model.
7. **Unblock GP-199 extract DDL into repo** — `EXTRACT_AMAZON_ADS_SB_AD_ASIN_MAP`/`_DAILY_SPEND` exist only in PROD; GET_DDL on prod account wj66376 → commit so the unified fact is reproducible in TEST/DEV.

**Loose ends:** uncommitted `mock_entity_mapping.sql` real-IDs update (land on a GP-225/226 branch); Eclipse connection inline-cred → Key-Vault migration (tech debt).

## See Also

- [[phase-1a-marketing-ad-platforms]] — original Phase 1A tracker (still valid for ticket context)
- [[navira-data-dictionary-phase1a]] — API field reference
- [[navira-credentials-access]] — credential status
- [[cross-channel-marketing-attribution]] — tiered measurement model; the MARKETING_EFFICIENCY reconciliation view
- [[GP-225]] — unified marketing schema; Windsor revenue-field fix (Tier 1)
