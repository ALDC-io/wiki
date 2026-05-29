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

## Next Session (pick up here)

**Guardrail:** all DWH changes deploy to **TEST_DG1_GEP_DEV clone only** right now — NOT real TEST_DG1_GEP. Eclipse connection/templates stay code-only until a separately-approved deploy.

1. **Navira Google/Meta via Windsor (GP-226)** — data expected ~2026-05-29. Before it flows: (a) generate real UUID for `windsor.json`, wire + activate `templates/windsor/{google_ads,meta_ads}.json`; (b) populate real Navira account IDs in entity CSV supplement (Google MCC `728-582-8945` — verify MCC vs child id Windsor lands; real Meta `act_…`); (c) Windsor field verification. Meta branch hardcodes USD + CONVERSIONS=0 — revisit.
2. **Commit Lectric work** to a feature branch in clients repo (Paul approves first).
3. **Gated:** deploy Lectric Eclipse conn+templates to real Eclipse → TEST_DG1_GEP; then full dimensional integration (Lectric product/brand/cost dims) as its own phase.
4. **Tech debt:** migrate Eclipse connection inline creds → Key-Vault injection.

## See Also

- [[phase-1a-marketing-ad-platforms]] — original Phase 1A tracker (still valid for ticket context)
- [[navira-data-dictionary-phase1a]] — API field reference
- [[navira-credentials-access]] — credential status
- [[cross-channel-marketing-attribution]] — tiered measurement model; the MARKETING_EFFICIENCY reconciliation view
- [[GP-225]] — unified marketing schema; Windsor revenue-field fix (Tier 1)
