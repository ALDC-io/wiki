---
tags: [concept, architecture, fusion92, flight-check, platform-ids, advertising]
aliases: [Platform ID Mapping, Fusion92 Platform IDs]
sources: [CF92/1669300225, FU92-429 (2026-08-28, measured in PROD_DG1_FUSION_92)]
created: 2026-04-18
updated: 2026-08-28
---

# Fusion92 Platform ID Mapping

Reference for how advertising platform identifiers map to the three ID fields used in [[flight-check]]: **Platform Account ID**, **Platform Campaign ID**, and **Platform Order ID**. These IDs drive data matching between flights and platform performance data in [[Snowflake]], Power BI models, and dashboards.

## ID Field Mappings by Platform

| Platform | Account ID | Campaign ID | Order ID |
|----------|-----------|-------------|----------|
| Advantage 360 (Soapbox) | Advertiser ID | Campaign ID | *Unused* |
| Amazon DSP | Advertiser ID | Order ID | *Unused* |
| Google Ads | Account ID | Campaign ID | *Unused* |
| Google Search Ads (SA360) | Account ID | Campaign ID | *Unused* |
| Google Campaign Manager (CM360) | Advertiser ID | Campaign ID | *Unused* |
| Google Display Video (DV360) | Advertiser ID | Campaign ID | Insertion Order ID |
| LinkedIn | Account ID | Campaign Group ID | Campaign ID |
| Meta (Facebook) | Account ID | Campaign ID | Ad Set ID |
| Microsoft (Bing) | Account ID | Campaign ID | *Unused* |
| Trade Desk | Advertiser ID | Campaign ID | *Unused* |
| Viant | Advertiser ID | Campaign ID | Order ID |

*Greyed-out platforms in Confluence (no longer active) still have historic data; the mappings above still apply for that data.*

## ID Entry Rules

### Format

IDs entered in Flight Check must be comma-separated with optional spaces:

| Format | Valid? |
|--------|--------|
| `12345, 45678, 89012` | ✅ |
| `12345,45678,89012` | ✅ |
| `123-456-789, 456-789-0123` | ✅ |
| `12345 45678 89012` (spaces only) | ❌ |
| `[12345] [45678] [89012]` (brackets) | ❌ |
| `"12345","45678","89012"` (quotes) | ❌ |

### Matching Logic

- **All required IDs must be present** for a flight to match platform data. A missing required ID means no match.
  - Example: a Viant flight with only Account ID + Campaign ID (missing Order ID) will not match.
- **Unused ID fields are ignored** during matching even if populated.
  - Example: a Google Ads flight with an Order ID still matches using only Account ID + Campaign ID.

### Overlapping Flights

If two or more flights share the same IDs and their date ranges overlap, platform spend is split evenly across all matching flights. Flight-level spend will not reflect exact values (account/campaign-level totals remain accurate).

> Example: Platform has $100 spend for a campaign on July 1. Four flights share the same account + campaign IDs and all ran in July → each flight shows $25.

This is why platforms that support Order ID equivalents (e.g. DV360 Insertion Order ID, LinkedIn Campaign ID, Viant Order ID) should have those populated — they ensure 1:1 flight-to-data matching.

### ⚠ Clearing ALL THREE IDs does not release a flight — the Smartsheet fallback

**Proven on FU92-429, 2026-08-28.** Removing every platform ID from a DAX flight is the *one* action
that makes the warehouse quietly substitute that flight's **Smartsheet** platform IDs — so the flight
keeps matching direct spend, keeps reporting `source = direct`, and the metrics table stays read-only.
The user's edit persists and syncs correctly; it just has no effect on the outcome.

The mechanism is `FUSION_92/snowflake/warehouse/shared_dim_flight.sql`:

```sql
-- :28-33  HAS_PLATFORM_IDS is TRUE if ANY of the three DAX IDs is non-NULL
-- :163-166
IFF(HAS_PLATFORM_IDS, DAX_FLIGHTS.PLATFORM_ACCOUNT_ID,  SMARTSHEET_FLIGHTS.PLATFORM_AD_ACCOUNT_ID) AS PLATFORM_ACCOUNT_ID,
IFF(HAS_PLATFORM_IDS, DAX_FLIGHTS.PLATFORM_CAMPAIGN_ID, SMARTSHEET_FLIGHTS.PLATFORM_CAMPAIGN_ID)   AS PLATFORM_CAMPAIGN_ID,
IFF(HAS_PLATFORM_IDS, DAX_FLIGHTS.PLATFORM_ORDER_ID,    SMARTSHEET_FLIGHTS.PLATFORM_ORDER_ID)      AS PLATFORM_ORDER_ID,
```

Because `HAS_PLATFORM_IDS` is an `OR` across the three fields, clearing **one or two** IDs behaves as
the user expects. Clearing **all three** arms the fallback. The observed shape (flight `1FVO2`):

| Layer | `PLATFORM_ACCOUNT_ID` |
|---|---|
| `WAREHOUSE_UTILITY.DAX_FLIGHT_CHECK_FLIGHTS` (what the user cleared) | `NULL` |
| `WAREHOUSE.SHARED_DIM_FLIGHT` (post-`IFF`) | `738-725-0037,F1047D8L` |
| `WAREHOUSE_UTILITY.ALL_SMARTSHEETS` (the source) | `738-725-0037,F1047D8L` |

Tell: the dim row's `PLATFORM_ID` reads `Dax-…` while its platform IDs are Smartsheet-sourced.

**⛔ Do not "fix" this by changing the `IFF`.** Two reasons, both measured:

1. **The warehouse cannot distinguish a deliberate clear from a flight that never had DAX IDs** —
   both are three NULLs. There is no signal to branch on. Any fix needs a *new explicit* one (e.g. a
   per-flight "manual metrics entry" override), which is a product decision.
2. **677 flights depend on the fallback** — every flight with all-NULL DAX IDs that carries `Direct-`
   rows has Smartsheet IDs being substituted, zero unexplained. Changing the `IFF` breaks 677 to fix 1.

**Workaround** (derived from code; verify on the rendered surface before promising it): clear the
platform IDs on the **Smartsheet** row too. The `IFF` then substitutes NULLs → no direct match →
`source` falls to `smartsheet` → and if the flight ends after `LAST_SMARTSHEET_YEAR`
(`flight-check/lib/dates.ts:3`, currently **2025**) the metrics table becomes manually editable.

**Where the label is decided** — useful because it is *not* where people look. The classifier never
reads the platform-ID fields at all: `dax_api/jobs/lib/calculations.py:247`
`is_direct = any(f.source == SnowflakeSource.direct for f in snowflake_metrics)`, fed by rows keyed on
`FLIGHT_ID`. Editing `calculations.py` ships a no-op that reads as a fix.

#### ✅ Resolution — the explicit signal exists now (`manual_metrics_entry`)

The "new explicit signal" predicted above was built on 2026-08-28: a `manual_metrics_entry: bool`
on the flight document (`workflows` @ `667355a`, **not deployed**). When set, direct rows are dropped
in `build_metrics_table` *before* the source-priority ladder runs, so the flight behaves exactly like
one that never matched direct spend and falls through to Smartsheet → mixed → Dax.

Two things worth carrying forward:

- **⭐ No warehouse change was needed.** The flag lives on the Cosmos flight document and is read by
  the DAX API, which already holds it. So the 677-flight `shared_dim_flight.sql` change came *off*
  the critical path entirely. When a derived value needs an override, check whether the override can
  live at the layer that already has the document before touching the shared dimension.
- **Two code paths decide the label, not one.** `build_metrics_table` serves Job Details;
  `build_grouped_metrics_table` serves the **Job List** from pre-aggregated rows. Guarding only the
  first makes a flight read as manual on one screen and "API Direct" on the other. Any change to
  source classification must touch both.

Still blocked on product decisions (who may set it; what happens to already-matched metrics; whether
it is reversible), so there is no UI yet.

### Freshness — an ID change is not visible immediately

Platform-ID edits reach the warehouse only via the sync timers, which run **hours 10–23 UTC only**
(`0 20,50 10-23 * * *`) plus a 09:10 UTC reconcile — a **10h30m nightly blackout (23:50 → 10:20 UTC)**,
Pacific-aligned while Fusion92 is Central. Dynamic-table lag is on top. **Do not diagnose an ID-matching
problem inside that window** — "not fixed" and "not yet synced" are the same observation there. See
[[dax-media-app]] § Architecture and FU92-430.

## Google Ads vs SA360 Precedence

When Google Ads and Google Search Ads (SA360) both report on the same campaigns, **Google Ads data takes precedence over SA360**.

## See Also

- [[fusion92]] — client; active platform connections and their statuses
- [[flight-check]] — operational process that uses these IDs for data validation
- [[Snowflake]] — where matched platform data lands
