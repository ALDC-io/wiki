---
tags: [entity, client, book-depot, wholesale, retail]
aliases: [BOOK_DEPOT]
sources: [Confluence CLIEN/972488707, Confluence CLIEN/1013972993]
created: 2026-04-18
updated: 2026-04-18
---

# BOOK_DEPOT

Wholesale book distributor client. Uses standard ALDC Retail Dimensional Model.

## Account Details

| Field | Value |
|---|---|
| Full Name | Book Depot |
| Short Code | BOOK_DEPOT |
| Primary Contact | Mark Van Vliet, Director — `mark@bookdepot.com` |
| Technical Contact | Derek Teeuwsen, VP of IT — `derek@bookdepot.com` |
| Address | 67 Front Street North, Thorold, Ontario L2V 1X3, Canada |
| Industry | Wholesale |
| Tenant Location | Canada |
| Warehouse Provider | Snowflake |
| Reporting Provider | Power BI |

**Note:** Connectivity requires an **IPSEC VPN** — setup documented in JIRA CUST-202.

## Data Model

Standard ALDC Retail Dimensional Model:

| Object | Type |
|---|---|
| `SHARED_DIM_ORDER_HEADER` | Dimension |
| `SHARED_DIM_CUSTOMER` | Dimension |
| `SHARED_DIM_ITEM` | Dimension |
| `SHARED_DIM_LOCATION` | Dimension |
| `SHARED_FCT_ORDER_LINE` | Fact |

## See Also

- [[star-schema-convention]] — ALDC dimensional model conventions
- [[dish-duer]] — similar retail client with more detailed model docs
