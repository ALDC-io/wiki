| Field | Value |

|---|---|

| **Title** | `Marketing ROI — Revenue and Conversions by Campaign and Channel` |

| **Description** | `From five raw source tables, build a gold-layer star schema: deduplicate customers, aggregate campaign spend, join orders to sessions, and compute attributed revenue, conversion rate, and ROI per campaign per month.` |

| **Grain** | `one row per campaign per channel per month` |

| **Metrics** (one per line) | `attributed_revenue: sum of raw_orders.amount_usd where campaign_id matches, excluding refunds and cancellations` *(newline)* `session_count: count of raw_web_sessions` *(newline)* `conversion_rate: sum(converted) / count(session_id)` *(newline)* `campaign_roi: attributed_revenue / sum(raw_campaign_spend.spend_usd) per campaign` |

| **Constraints** (one per line) | `Exclude cancelled and returned orders` *(newline)* `Deduplicate raw_customers by customer_email — keep the row with the latest signup_ts` *(newline)* `Only include sessions from 2023-01-01 onwards` *(newline)* `Attribute revenue to a campaign only when raw_orders.campaign_id is not null` |