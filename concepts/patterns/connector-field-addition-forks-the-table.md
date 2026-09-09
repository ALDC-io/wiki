---
title: Adding a field to a connector pull forks the landed table
tags: [pattern, connectors, prefect, snowflake, schema, gotcha]
aliases: [table fork, field-set equality, match_or_create_schema, versioned table]
sources:
  - prefect-connectors/connector/lib/warehouse/lib.py
  - prefect-connectors/connector/base/base_connector.py
  - aldc-launchpad/docs/evidence/gp319/SWEEP-2026-09-08.md
created: 2026-09-08
updated: 2026-09-08
---

# Adding a field to a connector pull forks the landed table

⛔ **"Just add one field to the pull" is not a small change.** The connector runtime has **no
`ALTER TABLE` path**. A widened field set does not migrate the existing table — it **creates a new
versioned one**, leaving the old rows behind in the old shape.

This is the single most under-costed change in connector work, because the request sounds like a
one-line edit and every estimate treats it as one. Discovered while pricing [[GP-319]]'s raw
pointer/destination column, but it is **not a GP-319 fact** — it applies to every connector and every
client.

`REPO-ONLY` (read from source, 2026-09-08). Live behaviour not exercised in that session.

## The mechanism

1. Schema is **derived from the data that came back**, not declared —
   `connector/base/base_connector.py:880`, `fields=self._get_column_list(response.dataframe)`.
2. The derived set is matched against existing tables by **exact field-set equality** —
   `connector/lib/warehouse/lib.py:292-365`.
3. A changed set matches nothing, so `match_or_create_schema` (`:367-430`) **creates a new versioned
   table**. There is **no `ALTER TABLE` / `ADD COLUMN` anywhere in `connector/lib/warehouse/`.**

## The measured precedent

⭐ In `match_or_create_schema`'s own comment block (`lib.py:388-401`): a **three-day**
`exchangeratesapi` window produced **48 table fragments** on
`QA_DG1_GEP_PREFECT_PR.EXCHANGE_RATES__PR`, **2026-08-14**, from a field declaration short by **four**
columns.

Three days. Four columns. Forty-eight tables.

## What you are left with

- A new versioned table **plus** a `CURRENT_*` union view over the family.
- Existing rows keep the **old shape** until they are re-pulled.
- ⛔ **The primary key is enforced per table, not across the union.** So a row re-pulled into two
  versions **survives twice in the union view** — a silent duplicate that no per-table constraint can
  catch.

That last point is the dangerous one: the duplicate appears in the consumer's view, not in the table
anyone would think to check.

## Then the client-visible surface needs its own edit

Data-share views **enumerate columns**, and `SELECT *` is forbidden — see
`clients/GEP/snowflake/data_share/amazon_ads_sponsored_products.sql:10-12`, with re-sharing on view
change called out at `:3-5`. So the fork is the *first* cost, not the only one.

## The gate to put on any ticket that widens a pull

Before touching anything GEP-facing:

1. **Rehearse against a QA/PR database** and **count the fragments** actually produced.
2. **Prove the `CURRENT_*` union does not double-count** a re-pulled row — construct the re-pull, do
   not reason about it.
3. **Capture rollback.**
4. Only then price the warehouse widening behind it (see [[GP-319]] §3.4 — 7–8 SQL objects, three of
   them hand-deploys with no repo source of truth).

## Related trap — decide which field list is authoritative first

The Windsor field list exists in **two copies that disagree**: Eclipse
(`clients/GEP/eclipse/templates/windsor/google_ads.json:22-45`, 26 fields) versus Prefect
(`connector/accounts/GEP/deployments/windsorai.py:37-65`, 27 — it adds `conversions_value`); Meta 16
versus 18. GEP and [[fusion92]] hold **separate copies**, so it is not per-client parameterised.

⚠ And the repo copy is **not** the deployed config — `GEP/eclipse/connections/windsor.json:6,8` reads
`"api_key": "PLACEHOLDER_INSERT_AFTER_CLIENT_AUTHORIZES"` / `"status": "inactive"`. **Never infer
whether a connector is active from repo Eclipse config.** Which copy is the deploy vehicle is
`NOT-FOUND` in the repos.

## The right question to ask first

**Does the field already land and simply go unread?** That is a view change, not a fork — and it is
surprisingly often true. Two live examples found the same day:

- `AMAZON_ADS.CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT.ADVERTISEDASIN` — landed, and **no
  warehouse object selects it**; the fact reads `ADVERTISEDSKU` instead.
- `AMAZON_ADS.CURRENT_SPONSORED_BRANDS_PURCHASED_PRODUCT_REPORT` — landed in prod **and** non-prod
  with **zero warehouse references**.

⭐ **Check the landed column inventory before costing a connector change.** The cheap answer and the
expensive answer look identical in the request.

## See also

- [[GP-319]] — where this was found, and the pointer-column work it prices
- [[cross-channel-marketing-dimensional-model]] — the conformed-field-set design this feeds
- [[cross-channel-marketing-attribution]] — `final_url` is `AVAILABLE-NOT-REQUESTED` from Windsor, the
  canonical example of a field-selection gap
