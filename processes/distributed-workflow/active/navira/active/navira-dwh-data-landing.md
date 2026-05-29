---
tags: [workflow, navira, gep, snowflake, marketing, windsor, schema-design]
aliases: [Navira DWH Data Landing, Marketing Schema Design]
created: 2026-05-28
updated: 2026-05-29
---

# Navira DWH Data Landing — Marketing Schema + Entity Segmentation

Replaces Phase 0 (Prefect Foundation) as the active priority. Uses existing Eclipse pipeline to get Google Ads, Meta/Facebook, and agency customer data flowing into Snowflake.

## Tickets

| Ticket | Summary | Status | Notes |
|---|---|---|---|
| GP-225 | Unified Marketing Schema Design | In Progress | Mock data + warehouse views in TEST_DG1_GEP_DEV |
| GP-226 | Windsor Google Ads + Meta | In Progress | **Connected 2026-05-29** — Navira authorized 6 Google + 3 Meta accounts (co-user). Real data validated → ENTITY_CODE='NAVIRA', 0 UNKNOWN, schema 1:1. Windsor conn/templates still placeholder+inactive (code-only). Next: Fusion92 filter → activate Eclipse into TEST → add revenue fields (Tier 1). Google/Meta are SPEND-ONLY today. |
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

## Next Session (pick up here) — PLAN-FIRST implementation

Environment (2026-05-29): build in an **isolated DEV schema in TEST_DG1_GEP**; **Fusion92 filter is the hard first step** before any Eclipse activation. (Full boot prompt held by Paul.)

1. **Fusion92 cross-tenant filter (FIRST)** — scope the Windsor pull/warehouse to the tenant's own account_ids; isolation test asserting zero cross-tenant rows. Hard prerequisite for #2. See [[project_windsor_fusion92_filter]].
2. **Activate Eclipse Windsor connector → TEST** — real UUID + api_key (`0fc1eaa029746a95d27c94abff39f324c47a`) in `windsor.json`; activate `templates/windsor/{google_ads,meta_ads}.json`; confirm real data lands in `TEST_DG1_GEP.GOOGLE_ADS`/`META`, Navira-only.
3. **Tier 1 — Windsor revenue fields (GP-225)** — add `conversions_value` (Google) + `actions_purchase`/`action_values_purchase` (Meta — verified names); update mock SQL; set Branch 6/7 SALES_AMOUNT/CONVERSIONS. ⚠️ row-split test grouped by PK before activation (Meta high-risk).
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
