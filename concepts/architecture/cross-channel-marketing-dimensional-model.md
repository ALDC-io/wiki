---
title: Cross-channel marketing dimensional model — the external evidence
tags: [architecture, marketing, dimensional-modelling, kimball, power-bi, star-schema]
aliases: [marketing star schema, ad performance fact, cross-channel model]
sources:
  - Kimball Dimensional Modeling Techniques (DW Toolkit 3rd ed.) — read in full via pdftotext
  - fivetran/dbt_ad_reporting (MIT) — model YAML and SQL read directly
  - snowplow/dbt-snowplow-attribution — raw SQL read directly
  - learn.microsoft.com Power BI guidance — raw markdown
created: 2026-08-30
updated: 2026-08-30
---

# Cross-channel marketing dimensional model — the external evidence

Companion to [[cross-channel-marketing-attribution]], which holds **our** tiered measurement law and
locked decisions. This page holds **what the outside world has actually published**, graded, so a
design conversation can separate an industry standard from our own invention.

Gathered 2026-08-30 as the external lane feeding a [[keel]] design pass on the Navira marketing model.

**Basis labels:** `OBSERVED` (I opened the artefact) · `DOCUMENTED` (official doc) · `REPORTED`
(practitioner) · `MARKETED` (vendor claim) · `ASSUMED` (ours, flagged).

---

## ⭐ 0. The headline: there is no canonical cross-channel marketing star schema

This is the finding that should shape how we talk about our own work.

- **Kimball has published nothing on digital marketing or advertising attribution.** `OBSERVED` — the
  complete *Kimball Dimensional Modeling Techniques* PDF was read end to end; the only marketing-titled
  item in the archive is Design Tip #91 *"Marketing the DW/BI System"*, which is about promoting a
  warehouse. **Everything "Kimball-flavoured" for ads is extrapolation from generic techniques.** That
  is legitimate — but say so, rather than putting *"Kimball says"* in front of a client.
- **Every commercial vendor ships wide, denormalised report tables — one per grain — not a star.**
  Fivetran `OBSERVED`, Supermetrics `MARKETED`, Improvado `MARKETED`, Adverity `DOCUMENTED`,
  Funnel `DOCUMENTED, partial`.
- **Fivetran's MIT-licensed `dbt_ad_reporting` is the only publicly readable cross-platform
  normalised model whose *transformation source* you can also read.** `OBSERVED` Treat it as the
  de-facto industry vocabulary. ⚠ **Corrected 2026-08-30** — an earlier draft of this page said it was
  the only readable conformed field list *at all*. That was too strong: Windsor.ai publishes a genuine
  23-field blended cross-connector schema, and Supermetrics publishes per-connector field lists with
  full metadata. What is unique to Fivetran is the readable *transformation*, which is why it remains
  the right thing to build from.

⭐ **So we are not adopting a standard. We are building one.** The defensible move is to take
Fivetran's conformed column names — inheriting the industry vocabulary for free — and impose Kimball
structure on top. This matters directly for [[warehouse-framework]] ambitions.

### ⭐ The number for the scoping conversation

Windsor.ai publishes per-field coverage across its **251 connectors** `OBSERVED` (DOM read in a real
browser, after sibling pages were caught rendering `Loading...`):

| Field | Connectors exposing it | of 251 |
|---|---|---|
| `source` | 251 | 100% |
| `date` | 162 | 65% |
| `account_id` | 149 | 59% |
| `campaign` | 55 | 22% |
| `impressions` | 51 | 20% |
| `spend` | 32 | **13%** |
| `conversions` | 23 | 9% |
| `currency` | 22 | 9% |

⭐ **A vendor with 251 connectors has a real cross-channel spine of 23 fields, and its spend column
covers 13% of them.** When a client hands over a flat column list assuming everything joins to
everything, this is the number that reframes the conversation — measured and published, not asserted.

⚠ **The cost column has four names across vendors** — `spend` (Fivetran, Windsor), `Cost`
(Supermetrics), `costs` (Adverity's own worked example), `ad_spend` (Improvado, unverified). Windsor
carries `spend` **and** `totalcost` as separate fields with different coverage — two unreconciled cost
concepts in one schema. **Zero convergence on the most-used column in the domain.** Pick one, document
it, never alias it.

### Verified negatives — findings, not gaps in the search

1. Kimball has published nothing on marketing/digital attribution.
2. **No** published attribution implementation uses a Kimball bridge table; three independent ones use
   wide per-model columns.
3. **No** published dimensional pattern preserves what a restated ad number looked like on a past
   report date.
4. **No** published guidance on campaign dimensions specifically — SCD choice, or when a retarget
   becomes a new entity.
5. **No** published model handles attribution *model* and attribution *window* as two simultaneous
   axes, despite Meta shipping data in exactly that shape.
6. Fivetran's ad packages — the most-deployed public ad model — have **no** currency standardisation
   and **no** timezone normalisation. Both verified by reading `dbt_project.yml` and `DECISIONLOG.md`.

---

## 1. The bus matrix — one atomic fact per business process

Kimball Rule 2 `OBSERVED`: *"Business processes… represent measurement events. Each process generates
unique performance metrics that become facts within a single atomic fact table."*

| # | Business process | Fact table | Type | Grain |
|---|---|---|---|---|
| 1 | Paid media delivery | `fct_ad_performance_daily` | periodic snapshot | date × platform × account × campaign × ad_group × ad, **at the lowest level that platform emits cost for** |
| 2a–d | Delivery **breakdowns** | `fct_ad_perf_geo_monthly`, `_device_daily`, `_placement_daily`, `_demographic_daily` | periodic snapshot | date × campaign(or ad) × the one breakdown |
| 3 | Search term / keyword | `fct_search_term_daily` | periodic snapshot | date × ad_group × keyword × query |
| 4 | Marketing touchpoint | `fct_marketing_touchpoint` | transaction | one row per touchpoint per identity |
| 5 | Conversion | `fct_conversion` | transaction | one row per conversion event |
| 6 | Attribution credit | `fct_attribution_credit` | transaction | one row per (conversion × touchpoint) |
| 7 | Plan / budget | `fct_marketing_plan_month` | periodic snapshot | month × campaign × channel |

⛔ **The structural decision most people get wrong: rows 2a–2d are separate fact tables, must never be
unioned with row 1, and must never be summed against each other.** Each platform "breakdown" is an
independent *re-aggregation of the same spend*. Evidence `DOCUMENTED`:

- Meta — *"only some permutations of breakdowns are available"*; hourly breakdowns *"do not support
  unique fields, which are any fields prepended with `unique_*`, `reach` or `frequency`"*.
- Google Ads — *"If you include any `segments.keyword.*` field in your SELECT clause, that restricts
  the results to only those rows directly associated with a Search Network keyword ad group
  criterion."* **Your keyword fact will not reconcile to your campaign fact, by design.**
- Fivetran ships geo at **monthly** grain because LinkedIn only provides geography by month; Facebook
  geo rows carry `campaign_name = 'Account-level'` with a **null** `campaign_id`. `OBSERVED`

---

## 2. `fct_ad_performance_daily`

```sql
-- role-playing date FKs, int YYYYMMDD
report_date_key            INT NOT NULL,
-- dimension FKs, NEVER NULL. Special members: 0 Missing, -1 Unknown, -2 N/A, -3 Error
platform_key, account_key, channel_key, currency_key, audit_key      INT NOT NULL,
campaign_key, campaign_durable_key                                   INT NOT NULL,  -- Type 7 pair
ad_group_key, ad_group_durable_key                                   INT NOT NULL,  -- -2 where absent
ad_key, ad_durable_key                                               INT NOT NULL,
objective_status_key                                                 INT NOT NULL,  -- junk dim
-- degenerate dimensions (platform natural keys)
platform_campaign_id, platform_ad_group_id, platform_ad_id           VARCHAR(64),
source_relation                                                      VARCHAR(64),
-- ⭐ GRAIN DECLARATION, MATERIALISED. Not decoration.
grain_level                VARCHAR(12) NOT NULL,  -- 'ad'|'ad_group'|'campaign'|'account'
-- ⭐ which platform REPORT this row came from. Makes breakdown double-counting DETECTABLE.
data_origin_key            INT NOT NULL,
-- ⭐ raw rows processed. Separates a genuine 0 from "nothing was processed".
row_count                  BIGINT NOT NULL,
-- measures: currency pair per Kimball Multiple Currency Facts
spend_local, spend_usd                           DECIMAL(18,6) NOT NULL,
impressions, clicks                              BIGINT        NOT NULL,
conversions_click_dated                          DECIMAL(18,6) NOT NULL,
conv_value_local_click_dated, conv_value_usd_click_dated  DECIMAL(18,6) NOT NULL,
metric_basis               VARCHAR(10) NOT NULL   -- MEASURED | MODELLED | ESTIMATED
```

⛔ **No `ctr`, `cpc`, `cpm`, `cpa`, `roas` columns.** Kimball `OBSERVED`: *"store the fully additive
components of the non-additive measure and sum these components into the final answer set before
calculating the final non-additive fact."* This is already our house rule — the frontend's
`metrics.ts` computes every ratio as `SUM(numerator)/SUM(denominator)`.

**Why `grain_level` earns its place.** Platforms do not share a hierarchy: LinkedIn's *campaign group*
is everyone else's *campaign*, and LinkedIn's *campaign* is everyone else's *ad group* `OBSERVED`.
Meta is Campaign → **Ad Set** → Ad; Snapchat is Campaign → **Ad Squad** → Ad `DOCUMENTED`. The column
makes the honest grain provable, and lets a measure refuse to answer below it.

### ⭐ `data_origin_key` and `row_count` — shipped by Funnel, and the answer to two of our own rules

`OBSERVED` — help.funnel.io built-in fields, verbatim:

> **`Data Origin identifier`** — *"An id that can be used to avoid double counting metrics due to
> adding the same data source with different breakdowns."*

⭐ **This makes the breakdown hazard detectable rather than merely avoided by convention.** It yields a
testable invariant: **any query returning more than one distinct `data_origin_key` for the same spend
is double-counting**, and can be made to *fail* rather than silently return a doubled number. That is
the structural version of the discipline, and it is the one column that turns §1's warning into a
control.

> **`Row Count`** — *"The number of raw data rows processed (considered for the values on the row)."*

⭐ **This is the ZERO vs NOT-RECORDED distinction implemented as a column.** It separates a genuine
zero (rows processed, value was 0) from an absent row (nothing processed). `metric_basis` covers the
MEASURED/MODELLED axis; `row_count` covers the orthogonal *did the instrument see anything* axis.
**Carry both** — they are not redundant.

`grain_level` and `metric_basis` are `ASSUMED` — ours, not published. `data_origin_key` and
`row_count` are `OBSERVED` in a shipping product.

### ⭐ The convergent spine — six vendors, one core, disagreement above it

`OBSERVED` across Fivetran, Supermetrics, Funnel, Windsor, Adverity, Improvado. **Six independent
vendors converge on the same ~12-column daily ad-performance spine and agree on almost nothing above
it:**

`date · platform/source · account_id · account_name · campaign_id · campaign_name · ad_group_id ·
ad_group_name · ad_id · ad_name · impressions · clicks · spend/cost · conversions · conversions_value`

⛔ **Everything above that line is contested.** And the sharpest cross-vendor finding:
**attribution is passed through untouched by every one of them** — nobody normalises it. That is the
domain's biggest correctness hazard, and it is unowned by the tooling, which means it is ours.

| Vendor | What it publishes | Verdict |
|---|---|---|
| **Fivetran `dbt_ad_reporting`** | 9 flat report models, full YAML + SQL readable | ⭐ **build from this** `OBSERVED` |
| **Supermetrics** | 8 per-grain tables (Google Ads); **the only proper currency implementation in the field** | `OBSERVED/DOCUMENTED` |
| **Windsor.ai** | 23 blended fields with per-connector coverage counts | `OBSERVED` (re-verified in a real browser) |
| **Funnel.io** | **only 3 cross-source metrics — Cost, Clicks, Impressions — and no campaign dimension at all.** Harmonisation is a user-authored rules engine, not a schema | `OBSERVED` |
| **Adverity** | **no default target-field list is published.** Six official pages checked | `NOT-VISIBLE`, not a fetch failure |
| **Improvado** | not publicly readable — the dictionary widget renders empty anonymously. Discount *"46,000+ standardized metrics"*; a union of every source's fields is the opposite of a common model | `MARKETED` |
| Snowflake / Databricks / Ads Data Hub | no marketing star schema published. ADH is a **clean room, not a data model** | `ABSENT` |

### The nine Fivetran models, with their grains verbatim

`OBSERVED` — `models/ad_reporting_models.yml`, cross-corroborated against `docs.md` and the raw
`ad_reporting__campaign_report.sql`, which emits exactly the columns the YAML declares.

| Model | Grain, in Fivetran's own words |
|---|---|
| `account_report` | *"Each record represents daily metrics by account."* |
| `campaign_report` | *"…by campaign and account."* |
| `ad_group_report` | *"…by ad group, campaign and account."* |
| `ad_report` | *"…by ad, ad group, campaign and account."* |
| `keyword_report` | *"…by keyword, ad group, campaign and account."* |
| `search_report` | *"…by search query, ad group, campaign and account."* |
| `url_report` | *"…by URL (and if applicable, URL UTM parameters), ad group, campaign and account."* |
| `monthly_campaign_country_report` | *"**monthly** metrics by campaign and country. Country names are standardized to ISO-3166 names."* |
| `monthly_campaign_region_report` | *"**monthly** metrics by campaign and region (state, province, metropolitan area, etc.)"* |

Shared metric tail on **every** model: `clicks, impressions, spend, conversions, conversions_value`.
Every model also carries `source_relation` (the multi-tenant discriminator) and `date_day`.

⭐ **Nine models, nine stated grains, one per grain — and two of them monthly.** This is §3's
supertype/subtype argument as a shipped artefact, and it is the shape to copy: *the grain is in the
model name and in its description*, so a consumer cannot mistake one for another.

### Use Fivetran's conformed measure names

`OBSERVED` from `ad_reporting_models.yml` and `get_query.sql` — identical across 11 platforms after
per-platform `field_mapping`, then `union all`:

`source_relation, date_day, platform, account_id, account_name, campaign_id, campaign_name,
ad_group_id, ad_group_name, ad_id, ad_name, clicks, impressions, spend, conversions, conversions_value`

**Two holes in it, both ours to fix:** no currency (`currency_code` exists in
`google_ads__campaign_report` and is *dropped* from the conformed model — the most-deployed public ad
model sums spend across currencies), and no timezone normalisation.

### Dimensions

| Dimension | SCD | Note |
|---|---|---|
| `dim_date` | 0 | int `YYYYMMDD` PK. **Duplicate per role** — see §5 |
| `dim_channel` | 1 | **Use GA4 Default Channel Group as the conformed taxonomy** `DOCUMENTED` — Google maintains it as a universal non-editable standard |
| `dim_account` | 2 | holds `currency_code`, `time_zone`, both immutable on Google's customer resource |
| `dim_campaign`, `dim_ad_group`, `dim_ad` | **7** | both surrogate and durable key on the fact |
| `dim_geography`, `dim_device`, `dim_placement` | 1 | each attaches to **its own breakdown fact only** |
| `dim_audience` + `bridge_campaign_audience` | 2 | multi-valued; bridge needs effective/expiration stamps |
| `dim_attribution_model` | 1 | only on the unpivoted reporting view, never the base fact |
| `dim_currency`, `dim_objective_status` (junk), `dim_audit` | 1 | — |

---

## 3. Reconciling different platform grains — supertype/subtype

Kimball `OBSERVED`, and it is exactly the right shape here:

> *"Attempts to build a single, consolidated fact table with the union of all possible facts… will fail
> because there can be hundreds of incompatible facts and attributes. The solution is to build a single
> supertype fact table that has the intersection of the facts from all the account types… and then
> systematically build separate fact tables for each of the subtypes."*

So `fct_ad_performance_daily` carries only the **intersection** — spend, impressions, clicks,
conversions, conversion value. Platform-specific metrics (video quartiles, saves, engagements, Quality
Score) go in **subtype facts per platform**. Fivetran does exactly this via `passthrough_metrics`.

⭐ This is the published answer to the question GP-319 settled by instinct. Our **core-10** (impressions,
clicks, cost, sales, CTR, CPC, purchases, cost-per-purchase, ROAS, units) *is* the supertype
intersection, and the 291 source-exclusive metrics *are* the subtypes. **The instinct was right and now
has a citation.**

Where a platform genuinely lacks a level, use special-member surrogate keys — `0` Missing, `-1`
Unknown, `-2` N/A, `-3` Error `DOCUMENTED` — never a NULL FK.

**Conformed *facts* matter as much as conformed dimensions.** Kimball `OBSERVED`: *"If the same
measurement appears in separate fact tables… if they are incompatible, they should be differently
named."* An IAB/MRC viewable impression (50% of pixels, 1 continuous second; 2s video) is not a served
impression. **If the definitions differ, the columns must differ in name.**

---

## 4. Restatement and late-arriving measures

**What the platforms do to you** `DOCUMENTED`: Google Ads conversion adjustments **RESTATE** (*"change
the conversion value, but not the count"*) and **RETRACT** (*"permanently remove a conversion… and
remove it from the conversion count"*); invalid-traffic removal is retroactive, so **spend restates
too**; conversion windows are settable 1–90 days.

**The absorption pattern is a rolling lookback plus partition replacement**, and it is quantified:
dbt microbatch `lookback` default **1**; Fivetran rollback sync, **Facebook default 9 days** (7-day
click + 1-day view + buffer); Fivetran `lookback_window` var default **7**; Supermetrics refresh window
replaces the last N days individually.

⚠ **`dbt_ad_reporting` has no lookback variable and does not need one** — it is `+materialized: table`
and rebuilds completely over source tables the *connector* already rolled back. `OBSERVED`
**If ingestion is not Fivetran, that layer does not exist and the lookback must be built.** This
applies to us directly: Windsor.ai and the Eclipse connector give us no rollback sync.

⛔ **Kimball's "Late Arriving Facts" does not cover this.** It is about finding the right *dimension
keys* for a late row, not about an existing row's *measure* being restated. `OBSERVED`

**Reproducing "what the number looked like on 30 June": no published consensus.** The nearest
Kimball-sanctioned mechanism is Timespan Tracking in Fact Tables — *"a row effective date, row
expiration date, and current row indicator… Although an unusual pattern."* If we need as-of reporting,
label it `ASSUMED`, not adopted.

---

## 5. Currency, timezone, and the date ambiguity

**Currency** — Kimball `OBSERVED`: *"a pair of columns for every financial fact… the true currency of
the transaction, and… a single standard currency… This fact table also must have a currency dimension."*
Microsoft states the consequence: local-currency spend **cannot be summed across currencies** — it is
semi-additive. This is our existing `*_TRANSACTION` / `*_CONSOLIDATED` convention, externally confirmed.

⭐ **Supermetrics ships exactly this, and supplies the two things a bare conversion is missing**
`OBSERVED/DOCUMENTED`: sibling columns `Cost, Cost_eur, Cost_gbp, Cost_usd, Currencycode`, with rates
from a **named source** (fixer.io), applied as the **end-of-day rate at the date of the data** — not
the query-run date — and a stated fallback to the last-known real-time rate when the rate is not yet
available (published 00:05 UTC the following day).

⛔ **Copy the convention, not just the columns.** Without a named rate source and a declared rate-date
convention, `spend_usd` is a number with no basis — which our own analysis gate forbids. This is also
the fix for the estate's open FX item: our exchange-rate feed carry-forwards, stopped 2026-03-03, and
holds corrupt far-future dates, so **always bound `EXCHANGE_DATE`**.

**Timezone** — Kimball prescribes dual date FKs, but this is **inapplicable to daily-aggregated ad
spend** because the underlying timestamp does not exist: *"Ad platforms send pre-aggregated data that
cannot be back-calculated."* `OBSERVED` Meta ships the ambiguity as two breakdowns
(`hourly_stats_aggregated_by_advertiser_time_zone` vs `..._by_audience_time_zone`); Search Ads 360 puts
**two timezones in one row**.

⭐ **The date ambiguity, with the killer citation** `DOCUMENTED`:

> *"Google Ads reports conversions on the ad impression date. Other reporting tools attribute them to
> the conversion date."*

`metrics.conversions` and `metrics.conversions_by_conversion_date` are **two different facts at two
different grains and must not share a column name.** Name them `conversions_click_dated` and
`conversions_event_dated`. Minimum date roles: `report_date`, `click_date`, `conversion_event_date`,
`conversion_attributed_date`.

---

## 6. Attribution without breaking additivity

**The published consensus is not a bridge table.** Three independent open-source implementations
converge on **one row per (conversion × touchpoint), with one pre-computed column per model.**
Snowplow `OBSERVED`:

```sql
case when source_index = 0 then revenue else 0 end                as first_touch_attribution,
case when is_last_element then revenue else 0 end                 as last_touch_attribution,
revenue / nullif(path_length, 0.0)                                as linear_attribution,
case when source_index = 0 then revenue * 0.4
     when is_last_element then revenue * 0.4
     else (revenue * 0.2) / (path_length-2) end                   as position_based_attribution
```

Each column independently sums to total revenue, so cross-model double-counting is prevented **by
construction**. A reporting view then unpivots into `attribution_type` + `attributed_revenue`, at which
point exactly one model must be sliced.

⭐ **Prefer dbt Labs' variant, which stores 0–1 weights rather than allocated currency** `OBSERVED` —
because `sum(weight) per conversion = 1.0` is a **testable invariant** and allocated currency is not.

**Spend and conversions are two facts — drill across, never join.** Kimball `OBSERVED`: *"A BI
application must never issue SQL that joins two fact tables together across the fact table's foreign
keys."* ROAS is `sum(attributed_revenue) / nullif(sum(spend),0)` with **spend joined separately at
channel level, never to the touchpoint fact.**

⚠ **Kimball's bridge table is the textbook answer to the shape and nobody implements it here.** DT #166
confirms bridges over-count *"unless an allocation/weighting factor is assigned"*, but DT #142 — the
only Design Tip with actual bridge SQL — has **no weighting column in its worked example**. The
canonical `(group_key, dimension_key, weighting_factor)` summing to 1.0 is `REPORTED`, not citable to a
Kimball-authored page. **Do not put "Kimball says" in front of a client on that one.**

⛔ **Open problem:** Meta's `action_attribution_windows` is structurally the same hazard — one event,
N differently-attributed values. No published model handles model × window as two axes.
⚠ `UNVERIFIED at field level` — both Meta reference pages 404'd through the fetch layer. If this
becomes load-bearing, check it against a live API response before designing on it.

---

## 7. Slowly-changing campaigns — and the silent industry default

**Type 7 means you do not have to choose** `OBSERVED`. Both the durable key and the surrogate key go on
the fact; two views expose the two perspectives. *"Spend under the name it had at the time"* → surrogate
key. *"All spend for this campaign ever, under its current name"* → durable key.

⛔ **The de-facto industry default is Type 1, and it is a silent choice.** `OBSERVED`, load-bearing:
Fivetran's Google Ads package joins stats to campaign attributes on `campaign_id` alone with **no
date-effective condition**, and filters `where is_most_recent_record = True` — even though the full
history is computed and sitting right there in `stg_google_ads__campaign_history`. **Campaign renames
silently rewrite history in every dashboard built on that package.** Make this choice deliberately.

**Nothing published tells you whether a *retarget* — same ID, materially different audience and
objective — is a Type 2 change or a new entity.** That is a business rule to elicit, not look up.

⚠ **Naming-taxonomy parsing is where a confident wrong answer comes from.** Positional `SPLIT_PART` on
agency-authored names shifts every field by one when a delimiter is missing — **and the row still
parses**. Carry a `taxonomy_parse_status` column (`PARSED | MALFORMED | LEGACY | UNPARSED`) so *"0
campaigns in APAC"* is distinguishable from *"40 campaigns whose region field didn't parse"*. `ASSUMED`
— this is the ZERO-vs-NOT-RECORDED rule applied to a parser.

---

## 8. Power BI — naming the failure correctly

See [[keel]] for the full diagnostic. The essentials:

- **Symptom name, Microsoft's own words** `OBSERVED`: *"The visual displays the same value for each
  grouping."* **Cause class: filter propagation failure.** *"Inert axis"* is our shorthand and is not
  the term of art — using it loses you the vendor documentation that settles the argument.
- **An inert axis means that table is not functioning as a dimension at all.** *"There's no table
  property that modelers set to set the table type… The 'one' side is always a dimension table while
  the 'many' side is always a fact table."*
- ⭐ **Microsoft explicitly diverges from Kimball on role-playing dimensions** `OBSERVED`: *"this design
  works well for relational star schema designs, [but] it doesn't work well for Power BI models…
  **role-playing dimension tables should be duplicated in your model.**"* Two things settle it for a
  marketing model — **RLS filters never propagate for inactive relationships, even with
  `USERELATIONSHIP`**, and a nullable role date produces a spurious BLANK slicer member.
- **Hiding is not a control** — *"live connections allow report authors to show hidden fields in the
  Data pane"*. Use **discourage implicit measures** at model level.
- **Mark as Date Table** — the guidance changed and most online advice is stale. You *do* need it if
  relationships use an int `YYYYMMDD` key, which is what this design recommends. ⚠ Destructive side
  effect: it removes auto-generated date tables and *"any visuals or DAX expressions you previously
  created based on those built-in tables no longer work properly."*
- **Display folders and a dedicated measures table are practitioner convention, not vendor guidance**
  `UNVERIFIED` as Microsoft guidance. Both are documented as *features*; neither is *recommended* on
  any Learn page found. ⛔ **Presenting them as Microsoft guidance would be a fabricated citation.**
- ⚠ The Q&A best-practices page — the best source on friendly naming — carries a **December 2026
  deprecation banner**, though its modelling advice is explicitly framed as general-purpose.

---

## 9. Elicitation — from a flat client field list to facts and dimensions

⛔ **A flat column list is not a business process — it is a flattened report.** Kimball is explicit
that this is the wrong starting point: *"a fact table corresponds to a physical observable event, and
not to the demands of a particular report."*

The four-step process `OBSERVED`: **select the business process → declare the grain → identify the
dimensions → identify the facts**, and *"the grain must be declared before choosing dimensions or
facts… [it] becomes a binding contract on the design."* This is [[keel]]'s Gate 3.

**The triage rules, all published:**
- **The "by" test** `DOCUMENTED`: *"stay alert for the mention of the word* by*… they're telling you
  they need dimensions that have those attributes."*
- **Kimball's numeric tiebreak** `OBSERVED`: *"If the numeric value is used primarily for calculation
  purposes, it likely belongs in the fact table. If a stable numeric value is used predominantly for
  filtering and grouping, it should be treated as a dimension attribute."*
- **Rule 7** `OBSERVED`: *"If content appears as row/column labels or filter options, dimension tables
  should handle it."*
- **Reject the ratios** — CTR, CPC, CPM, CPA, ROAS, CVR come off the list and become semantic-layer
  measures.
- **Fill the bus matrix. The blank cells are the gap list to take back to the client** — this is the
  deliverable that turns their flat list into a scoped conversation.

### ⭐ Kimball publishes the actual worksheet, and it is live

- `https://www.kimballgroup.com/wp-content/uploads/2014/03/Ch08-Physical-Model-Template.xls`
- `https://www.kimballgroup.com/wp-content/uploads/2014/03/Ch07-High-Level-Model-diagram.ppt`

Verified 2026-08-30 — HTTP 200, correct MIME types. Sheets: Schemas, Change Log, Customer, Orders,
**BlankDim, BlankFact**. Three things worth stealing directly:

1. **`Display Name` is a first-class column, separate from `Column Name`.** Physical
   `customer_full_name`, display `Customer Full Name`. **That is the answer to the Power BI naming
   question, and Kimball has shipped it since 2014.** It also answers GP-319's *"the defect is naming"*
   conclusion — the fix is a display layer, not a rename.
2. **`Attribute Group`** (Identifiers / Name and address / Housekeeping) — a display-folder taxonomy in
   all but name.
3. The Orders example carries `UnitPriceUSD`/`ExtendedAmtUSD` and allocation rules as literal rows —
   Multiple Currency Facts and Allocated Facts as spreadsheet entries.

⚠ The **Fact Qualifier Matrix** looks like an elicitation tool and is not — *"the FQM is a tool only to
validate conformity after the first draft of the models have been developed."* `DOCUMENTED`

---

## Caveats on this page

- **The SQLBI citations are the weakest link** — all came back through a page summariser rather than
  raw text. Supporting colour, not load-bearing. Re-verify before client-facing use.
- **The Power BI model-side/measure-side discriminating test is `DERIVED`, not published, and has not
  been run against a deliberately broken model.** Run it once before it becomes a runbook.
- ⚠ **The vendor-schema lane was written off as lost and then returned.** Its findings are folded in
  above (the convergent spine, the nine Fivetran models, Funnel's three metrics, Adverity's
  NOT-VISIBLE field list). Recorded because the near-miss is the lesson: **a lane that has not
  reported is not a lane that found nothing** — the same rule the councils apply to a silent member.
- Two claims on this page were **corrected after first publication** — the "only readable field list"
  overreach in §0, and the Meta attribution-window field structure, now marked `UNVERIFIED`. Both
  corrections came from a second instrument, not from re-reading the first.

## Related

[[cross-channel-marketing-attribution]] · [[star-schema-convention]] · [[navira-metric-dictionary]] ·
[[navira-daily-model-lineage]] · [[fusion92-data-architecture]] · [[keel]]
