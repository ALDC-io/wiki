
-- Check 1: Confirm US + CA data is flowing (and no extra marketplaces slipped in)
SELECT
    m.marketplace_name,
    COUNT(*) AS row_count,
    SUM(ordered_product_sales) AS summed_sales
FROM warehouse_source.traffic_fct_activity v
JOIN warehouse.shared_dim_marketplace m
    ON v.marketplace_key = m.marketplace_key
    WHERE m.marketplace_name IN ('Amazon US', 'Amazon CA')
    GROUP BY 1
    ORDER BY 1;

Output:
- Looks as expected

|   |   |   |
|---|---|---|
|MARKETPLACE_NAME|ROW_COUNT|SUMMED_SALES|
|Amazon CA|1404120|1394516.20767693|
|Amazon US|6770879|60725720.44|


