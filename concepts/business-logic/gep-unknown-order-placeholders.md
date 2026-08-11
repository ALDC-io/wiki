---
tags: [business-logic, gep, navira, power-bi, snowflake, order-count]
aliases: [UNK orders, Unknown orders, Gross Order Count UNK, no-sale ad spend placeholders]
sources: [conversation 2026-06-25, warehouse_ops/_phase3_staged/sales_fct_orderline.sql, pbi_ops/_all_measures_expr.json]
created: 2026-06-25
updated: 2026-06-25
---

# GEP — "Unknown" (UNK_) order placeholders & the Gross Order Count fix

[[GEP]]/Navira's sales fact carries synthetic **"Unknown" order placeholders** that exist to park
**advertising spend which did not result in a sale**, so that spend isn't lost to cost/margin. These rows
are by design — but the **Gross Order Count** measure was counting them as real orders. Fixed 2026-06-25
(TEST deployed; PROD pending client sign-off). Tracked as **ALDC-490**.

## What the placeholders are

In `WAREHOUSE.SALES_FCT_ORDERLINE` there is a `UNION ALL` branch — *"Unknown orders from cost allocation"*
(`warehouse_ops/_phase3_staged/sales_fct_orderline.sql`) — that pulls from `WAREHOUSE.SALES_FCT_COST`
where `ATTRIBUTION_TYPE = 'No Match'`. Each such row:

- `LINE_STATUS = 'Unknown'`, `ORDER_ID = 'UNK_<date>_<currency>'` (one bucket per day per currency: USD + CAD)
- **0** for every sales / quantity column
- carries the real `PRODUCT_/BRAND_/NOSALE_ADVERTISING_FEE_*` (the no-sale ad spend it exists to hold)

In PROD: **456,142 lines / 1,509 distinct orders**, continuous **2024-06-01 → present**, carrying ~**$406K**
of ad fees. They are a deliberate cost-completeness mechanism — keep them.

## The bug

The order-count root measure (`Sales Measures[_BASE_ACT_SALE_GROS_OC]`) was:

```dax
DISTINCTCOUNT('Order Line'[ORDER_KEY])
```

Each placeholder carries a distinct `ORDER_KEY`, so the distinct-count swept them in — every `UNK_` row
showed **Gross Order Count = 1** despite 0 sales/units. **Long-standing, not a regression:** the measure
has carried this definition since **2024-05-16** and placeholders have existed since 2024-06. It stayed
invisible because it's ~0.05% of orders (1,509 of ~2.7M); it only surfaced when Navira built a view that
isolates the Unknown rows. *The placeholders are by design; counting them as orders was not.*

## The fix

```dax
CALCULATE(
    DISTINCTCOUNT('Order Line'[ORDER_KEY]),
    KEEPFILTERS('Order Line'[Line Status] <> "Unknown")
)
```

- One root measure; cascades to all **19** Order Count periodicity variants (C/YTD/MTD/QTD/WTD/prior-year/
  YoY-%) plus **AOV**, **Units per Transaction**, and the **Agency rollups**. No other measure raw-counts
  `ORDER_KEY`.
- `KEEPFILTERS` is deliberate: an "Unknown" row then reads **0** rather than leaking the all-orders total;
  grand total and every real-status row are unchanged.
- Model column is the display name **`Line Status`** (not the warehouse `LINE_STATUS`).

## Validated impact (consumer-layer DAX)

| Model | Order Count before → after | Unknown row | Gross Sales / Qty |
|---|---|---|---|
| PROD `74a529b3` (GEP Prod Models / "Data Model") | 2,747,824 → 2,746,315 (−1,509) | 1,509 → 0 | unchanged |
| TEST `66151728` (GEP Test Models / "Data Model") | 2,752,624 → 2,751,115 (−1,509) | 1,509 → 0 | unchanged |

**No-regression proof:** the grand total drops by *exactly* the distinct Unknown count → zero `ORDER_KEY`
overlap between Unknown and real orders, so only the phantoms are removed.

## Deploy / rollback

Deployed via `pbi_ops/cli.py measures create "<workspace>" "Data Model" --table "Sales Measures"
--name "_BASE_ACT_SALE_GROS_OC" --expression "<fixed DAX>"`. Rollback = same command with the original
`DISTINCTCOUNT('Order Line'[ORDER_KEY])`. TEST rollback saved at
`aldc-launchpad/pbi_ops/_BASE_ACT_SALE_GROS_OC_ROLLBACK_TEST_66151728.txt`. PROD deploy pending Navira
sign-off (comparison workbook sent to Heather Tabor).

## ⚠ These placeholders also close a CIRCULAR DEPENDENCY (found [[GP-322]], 2026-08-10)

The same `ATTRIBUTION_TYPE = 'No Match'` rows are read into **`WAREHOUSE_SOURCE.SALES_DIM_ORDER`** as
well as into `SALES_FCT_ORDERLINE` — the dimension appends them as *"unallocated cost order"* rows. But
`SALES_FCT_COST`'s own ad-cost **allocation denominator** joins that dimension. So:

```
SALES_FCT_COST ──▶ SALES_DIM_ORDER ──▶ SALES_FCT_COST
```

Snowflake breaks the cycle by build order, materialising the fact at **06:02:32** and the dimension at
**06:02:48** — so the allocation divides each day's ad spend by an order list that is **24 hours stale**.
Result: the allocated ad-cost columns are inflated on the trailing ~3 days of every build (the newest day
by up to ~27×), which **understates net margin** by the same amount. It self-heals; closed months are fine.

⇒ **Do not "simplify" this dimension arm without reading [[circular-dependency-build-order]] first.** The
placeholders are still a deliberate and correct cost-completeness mechanism — the defect is not that they
exist, it is that the dimension carrying them is *also an input to the fact that produces them*. The
remedy on [[GP-322]] leaves these rows untouched and instead repoints the denominator at
`SALES_DIM_ORDER_BASE`, which does not contain them.

**Second-order effect worth knowing:** because starved buckets fall through the allocation's
`ORDER_LINE_COUNT > 0` gate into the No-Match branch, the *count* of `UNK_` rows is itself inflated on
those trailing days (GP-322 measured ~1,270 extra August rows carrying ~$2,326). So a `UNK_` row count
taken on a current month is not a stable figure.

## See Also

- [[GEP]] — the client
- [[periodicity]] — the SWITCH/`_BASE_*` periodicity pattern these Order Count variants follow
- [[Power BI]] / [[pbi-xmla-automation]] — how the measure was read/edited via XMLA + TOM
- [[star-schema-convention]] — `SALES_FCT_ORDERLINE` / cost-allocation grain
- [[processes/distributed-workflow/active/navira/README|navira]] — Navira workstream
