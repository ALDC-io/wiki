---
tags: [concept, architecture, fusion92, flight-check, platform-ids, advertising]
aliases: [Platform ID Mapping, Fusion92 Platform IDs]
sources: [CF92/1669300225]
created: 2026-04-18
updated: 2026-04-18
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

## Google Ads vs SA360 Precedence

When Google Ads and Google Search Ads (SA360) both report on the same campaigns, **Google Ads data takes precedence over SA360**.

## See Also

- [[fusion92]] — client; active platform connections and their statuses
- [[flight-check]] — operational process that uses these IDs for data validation
- [[Snowflake]] — where matched platform data lands
