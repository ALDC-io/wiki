---
tags: [workflow, navira, data-dictionary, phase-1a, google-ads, meta, amazon-ads, api]
aliases: [Navira Data Dictionary, Phase 1A Data Dictionary]
sources: [eclipse_exp/frontend/public/navira/navira-phase1a-data-dictionary.html]
created: 2026-04-27
updated: 2026-05-29
---

# Navira Phase 1A — API Data Dictionary

Field-level API reference for Phase 1A ad platform connectors. Google Ads API v18/v19 | Meta Marketing API v21/v22 | Amazon Advertising API v3.

**Source:** Interactive document at `eclipse_exp/frontend/public/navira/navira-phase1a-data-dictionary.html` with field-level search, collapse/expand per platform, per-field business logic textarea (auto-saves to localStorage), and JSON export.

## Google Ads (GAQL)

### Core Metrics

| Field | Type | Gotcha |
|---|---|---|
| `metrics.impressions` | INT64 | — |
| `metrics.clicks` | INT64 | — |
| `metrics.cost_micros` | INT64 | **CRITICAL: Divide by 1,000,000 for actual currency value.** Snowflake: `NUMBER(18,6)`. |
| `metrics.ctr` | DOUBLE | Ratio (0.0–1.0), multiply by 100 for percentage display |
| `metrics.average_cpc` | DOUBLE | In micros — divide by 1M |
| `metrics.average_cpm` | DOUBLE | In micros — divide by 1M |
| `metrics.interactions` | INT64 | Superset of clicks (includes video views, swipes, etc.) |

### Conversion Metrics

| Field | Type | Gotcha |
|---|---|---|
| `metrics.conversions` | DOUBLE | **Not INT — use `NUMBER(18,6)` in Snowflake.** Fractional due to attribution models. |
| `metrics.conversions_value` | DOUBLE | Revenue attributed to conversions |
| `metrics.all_conversions` | DOUBLE | Includes cross-device + view-through |
| `metrics.all_conversions_value` | DOUBLE | Revenue for all_conversions |
| `metrics.view_through_conversions` | INT64 | **Must NOT be added to `conversions` — double counting.** These are already included in `all_conversions`. |
| `metrics.cost_per_conversion` | DOUBLE | In micros |
| `metrics.value_per_conversion` | DOUBLE | — |

### Dimensions & Segments

| Field | Type | Gotcha |
|---|---|---|
| `segments.date` | DATE | — |
| `segments.device` | ENUM | DESKTOP, MOBILE, TABLET, OTHER |
| `segments.ad_network_type` | ENUM | SEARCH, DISPLAY, YOUTUBE_SEARCH, YOUTUBE_WATCH, etc. |
| `segments.conversion_action_name` | STRING | — |
| `campaign.id` | INT64 | **Use as primary key — `campaign.name` is mutable.** |
| `campaign.name` | STRING | Mutable — can be renamed. Never use as join key. |
| `campaign.advertising_channel_type` | ENUM | SEARCH, DISPLAY, SHOPPING, VIDEO, etc. |
| `ad_group.id` | INT64 | — |
| `ad_group.name` | STRING | — |
| `customer.currency_code` | STRING | **Google does NOT auto-convert currencies across MCC accounts.** Must handle currency normalization in ETL. |

## Meta / Facebook Marketing API

Platform section present in the source document. Key fields follow the same pattern: impressions, clicks, spend, conversions, CTR, CPC, CPM. Meta-specific fields include `actions` (array of action types), `action_values`, `cost_per_action_type`. The Meta API returns spend in account currency (not micros).

> **Full field reference:** See the interactive document at `eclipse_exp/frontend/public/navira/navira-phase1a-data-dictionary.html` — Meta section.

## Amazon Advertising API v3

Three campaign types with separate API sections:

### Sponsored Products (SP)
Standard campaign metrics: impressions, clicks, cost, sales (attributed), ACoS, ROAS. 14-day attribution window by default.

### Sponsored Brands (SB)
Brand awareness metrics: impressions, clicks, cost, new-to-brand orders, new-to-brand sales.

### Sponsored Display (SD)
Display/retargeting metrics: impressions, clicks, cost, DPVR (Detail Page View Rate), purchases.

> **Full field reference:** See the interactive document — Amazon SP/SB/SD sections.

## Implementation Gotchas from Existing ALDC Connectors (2026-04-27 audit)

Field-level findings from reading the production connector implementations in `connector/connector/connectors/`. These supplement the API documentation with real-world edge cases discovered during production operation for Fusion92 and GEP.

### Amazon Ads (`amazon_ads.py`)

- **Report download format is GZIP_JSON:** The connector uses `zlib.decompress(content, wbits=31)` for decompression — faster than `gzip.decompress()` per Python docs. The Prefect implementation should use the same approach (`amazon_ads.py:690-694`).
- **Multi-profile handling:** The connector fetches ALL profiles for the authorized account, then filters — `agency` type profiles are only used for DSP, all others for SP/SB/SD. This is how UK/CA profiles will automatically appear once Navira's account has advertising in those regions (`amazon_ads.py:405-423`).
- **Token refresh during long reports:** Access tokens expire during long report generation waits. The connector implements preemptive refresh when within `TOKEN_REFRESH_THRESHOLD_SECONDS` (15 minutes) of expiry (`amazon_ads.py:643-651`). The Prefect implementation must replicate this.
- **Exponential backoff on report polling:** Report status polling uses exponential backoff with randomized jitter (`amazon_ads.py:636-641`), capped at 5 minutes. Amazon recommends this pattern in their rate-limiting docs.
- **Profile ID injected per-row:** `profile_id` is added to every row of report data at the row level (`amazon_ads.py:760`), not as a column from the API response. This is the join key for multi-profile queries.
- **Five campaign types supported:** SP, SB, SD, Sponsored Television, and DSP. The data dictionary should include Sponsored Television metrics if Navira uses Amazon STV.
- **`campaignBudgetCurrencyCode` field:** Present in all report configs — this is the currency field to preserve alongside the normalized USD value.

### Amazon SP-API (`amazon_sellercentral.py`)

- **Date range gotcha for `GET_SALES_AND_TRAFFIC_REPORT`:** This report type ONLY supports single-day date ranges (`amazon_sellercentral.py:993-1007`). Multi-day ranges cause the API to aggregate data, making it impossible to add the date back as a dimension. The Prefect connector MUST use `PartitionSchemeDateWindow(window_type="day")` for this report type.
- **Inclusive end date behavior:** `GET_SALES_AND_TRAFFIC_REPORT` treats the end date as inclusive. The connector explicitly sets `filter_end_date = filter_start_date` to avoid getting two days of data (`amazon_sellercentral.py:1007`).
- **SKU vs CHILD granularity:** The `asin_granularity` option controls whether `GET_SALES_AND_TRAFFIC_REPORT` groups by SKU or Child ASIN. Different primary keys: `["DATE", "SKU"]` vs `["DATE", "CHILDASIN", "PARENTASIN"]` (`amazon_sellercentral.py:935-940`).
- **Tab-delimited fallback:** Some SP-API reports return tab-delimited text instead of JSON. The connector attempts JSON parse first, then falls back to TSV (`amazon_sellercentral.py:497-517`). The Prefect implementation must handle both formats.
- **Multi-marketplace filter:** Marketplace is a required filter for most categories. The connector supports 19 marketplaces via `sp_api.base.Marketplaces` enum (`amazon_sellercentral.py:69-89`).
- **Rate limiting with exponential backoff:** The connector catches `SellingApiRequestThrottledException` and retries with backoff doubling up to 60 seconds (`amazon_sellercentral.py:184-191`).
- **`accept_previous_reports` option:** When report generation fails with FATAL status, the connector can fall back to a previously completed report within a configurable threshold (`amazon_sellercentral.py:452-477`). Useful for resilience.

### Meta / Facebook (`facebook_business.py`)

- **Nested action fields require special handling:** Facebook returns action metrics as nested arrays: `{"actions": [{"action_type": "video_views", "value": 1234}]}`. The connector flattens these into columns like `actions_video_views` via `flatten_row_with_nested_fields()` (`facebook_business.py:378-399`). The Navira Prefect connector must replicate this flattening.
- **`action_type` and `value` are the nested keys:** Hardcoded as `NESTED_TYPE_FIELD = "action_type"` and `NESTED_VALUE_FIELD = "value"` (`facebook_business.py:107-108`). If Meta changes these field names in a future API version, this breaks.
- **Sleep between API calls is mandatory:** The connector has a configurable `sleep` parameter (default 5 seconds) between campaign insight calls to avoid rate limiting (`facebook_business.py:119, 189`). This is enforced per-campaign, not per-request.
- **Campaign date filtering is client-side:** The API's `time_range` parameter is unreliable for filtering campaigns (known bug noted in comments at `facebook_business.py:529-531`). The connector fetches all campaigns then filters by `start_time`/`stop_time` intersection with the requested window (`facebook_business.py:173-186`).
- **Default fields are not overridable:** The connector enforces that default fields (e.g., `id`, `name`, `account_id` for campaigns) cannot be redeclared in the template's `additional_fields` — it throws an error to prevent merge conflicts with nested field options (`facebook_business.py:493-505`).
- **Spend is in account currency (not micros):** Unlike Google Ads, Meta returns spend in the account's configured currency. The `account_currency` field is included by default in all insight queries.
- **Primary key sort order matters:** Primary keys are sorted alphabetically to ensure consistent ordering across runs (`facebook_business.py:444-452`). Inconsistent PK ordering causes problems with Snowflake merge operations.

## Cross-Platform Notes

- **Currency:** Google Ads uses micros (÷ 1M), Meta uses account currency directly, Amazon uses marketplace currency. Normalize to USD in the ETL with original currency preserved.
- **Attribution windows:** Vary by platform (Google: configurable, Meta: 7-day click / 1-day view default, Amazon: 14-day). **Resolved (2026-05-29, [[GP-225]] / Phase 1A Q3): store raw platform attribution, do NOT normalize.** Prod `MARKETING_FCT_ACTIVITY` already surfaces Amazon on the **30-day** window columns (`PURCHASES30D`/`SALES30D`); Windsor returns Google/Meta on their native windows and can't be re-windowed. **Headline window DECIDED 2026-05-29 (Paul): keep 30d** (matches current warehouse; revisit only if Navira requests).
- **Campaign ID as key:** Always use numeric IDs as primary keys, never campaign names (mutable across all platforms).
- **Retroactive adjustments:** Ad platforms retroactively adjust data for 7–30 days. Design ingestion with configurable lookback window.
- **Rate limiting patterns from production:** All three connectors implement exponential backoff. Amazon Ads caps at 5 minutes, SP-API at 60 seconds, Meta uses a fixed sleep per campaign. The Prefect implementation should use Prefect's built-in retry/backoff decorators where possible, but the SP-API and Amazon Ads connectors need request-level backoff (not flow-level) for pagination and report polling.

## Revenue / Conversion Field Gap via Windsor (2026-05-29)

GEP pulls Google + Meta through [[Windsor]] (`windsorai_v1`). The current GEP templates are 1:1 clones of Fusion92's and inherited the same gap: **conversion value / revenue is not selected.** This — not attribution-window alignment — is the real blocker for cross-channel ROAS.

- **Google** (`templates/windsor/google_ads.json`): carries `conversions` and `roas`, but **not** `conversions_value`. `marketing_fct_activity.sql` Branch 6 loads `CONVERSIONS` and hardcodes `SALES_AMOUNT = 0`. Fix: add `{"name": "conversions_value"}` to the template, map in SQL. (`all_conversions` / `all_conversions_value` available too but double-count view-through — hold back.)
- **Meta** (`templates/windsor/meta_ads.json`): selects **only video-view actions** — no purchase actions, no `action_values`. Branch 7 hardcodes both `CONVERSIONS = 0` and `SALES_AMOUNT = 0`. Fix: add `actions_purchase` (count) + `action_values_purchase` (value) — **field names VERIFIED 2026-05-29** against live `GET https://connectors.windsor.ai/facebook/fields`. Variants: `actions_omni_purchase`/`action_values_omni_purchase` (plural), `actions_offsite_conversion_fb_pixel_purchase`/`action_values_offsite_conversion_fb_pixel_purchase`. **`action_value_omni_purchase`, `purchases`, `purchases_value`, `purchase_roas` do NOT exist — do not use.**
- **Not a Windsor limitation** — Windsor exposes these fields (confirmed in the live catalog); they were never added. Creds verified 2026-05-29.
- ⚠️ **Platform value ≠ actual revenue.** `conversions_value` / `action_values_purchase` are each platform's *own attributed* conversion value (its pixel + its window). They double-count across channels and won't reconcile to `SALES_FCT_*` orders. They give correct *per-channel* ROAS but are NOT a cross-channel source of truth — see [[cross-channel-marketing-attribution]].
- ⚠️ **Row-splitting:** both template comments warn that some Windsor field combinations split rows (same PK, partial data) and corrupt the merge. Test one day grouped by PK before activating. Meta is highest-risk.
- ⚠️ **Cross-client filter:** the team Windsor key pulls all Fusion92 accounts — a per-client account filter is needed in the GEP templates before real-TEST/Eclipse activation.

See [[GP-225]] for the full plan and clone-validation status.

## Business Logic (to be filled by Navira)

The source document includes blank "Navira Business Logic" textarea fields for each API field, intended for the client to document their specific transformation rules (e.g., how to classify campaign types, custom ROAS calculations, spend allocation rules). These should be filled during Phase 1A discovery sessions and updated here as decisions are made.

## See Also

- [[phase-1a-marketing-ad-platforms]] — workflow page for Phase 1A delivery
- [[navira-credentials-access]] — API credential status
- [[google-ads]] — existing ALDC Google Ads connector spec
- [[facebook-ads]] — existing ALDC Facebook/Meta connector spec
- [[amazon-ads]] — existing ALDC Amazon Ads connector spec
- [[star-schema-convention]] — ALDC Snowflake naming conventions (SHA2 keys, field patterns)
