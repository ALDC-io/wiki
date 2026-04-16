1. **Profile coverage check** – confirm every `PROFILE_ID` in the source now surfaces in the fact and shows exactly one currency:

```sql
SELECT PROFILE_ID, CURRENCY_CODE, COUNT(*)
FROM WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY
GROUP BY 1,2
ORDER BY 1;
```

Expect the two known profiles (US, CA) plus any strays flagged as `UNKNOWN_MARKETPLACE`. - **See Results Below**

2. **Marketplace mapping sanity** – verify the profile-based join is 1:1:

```sql
SELECT PROFILE_ID, MARKETPLACE_ID, MARKETPLACE_NAME, COUNT(*)
FROM WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY
GROUP BY 1,2,3
ORDER BY 1;
```

Each profile should map to a single marketplace; any missing map shows up as `UNKNOWN_MARKETPLACE`. - Same issue as previous test highlighted (See results section below)

![[Pasted image 20260227160636.png]]


3. **Fallback detection** – make sure we aren’t silently dropping profiles:

```sql
SELECT PROFILE_ID, COUNT(*)
FROM WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY
WHERE MARKETPLACE_ID = 'UNKNOWN_MARKETPLACE'
GROUP BY 1;
```

You’ll likely see the unexpected `3378484324565094` here; log it so Justin can confirm whether to map it.

![[Pasted image 20260227160731.png]]

4. **Currency vs marketplace sanity** – ensure currency lines up with marketplace names:

```sql
SELECT MARKETPLACE_NAME, CURRENCY_CODE, SUM(COST)
FROM WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY
GROUP BY 1,2;
```

![[Pasted image 20260227160824.png]]


5. **Campaign spot checks** – pick one profile and confirm the campaigns show the right marketplace label:

```sql
SELECT DISTINCT CAMPAIGN_ID, PROFILE_ID, MARKETPLACE_NAME
FROM WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY
WHERE PROFILE_ID = '2874274850477920'
LIMIT 20;
```

![[Pasted image 20260227160914.png]]



If all those queries look good, note the results in `notes/projects/DE-006/testing.md` and the ticket work log, and call out the remaining dependency (MX/BR profiles still absent, so QA should watch for new `UNKNOWN` rows). Let me know if you want me to help run/interpret any of the queries


## Validation Results – 2026‑02‑27**

1. `PROFILE_ID` coverage (`WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY_GP169`):

- `2874274850477920` → USD, row count matches source.
- `410071870980733` → CAD, row count matches source.
- `3378484324565094` → USD (1 row). Not in Justin’s mapping, so it lands on `MARKETPLACE_ID = 'UNKNOWN_MARKETPLACE'`. Flag for stakeholder confirmation.
- No MX/BR profiles present yet.

1. **Marketplace join sanity:**

- US and CA profiles map cleanly to `NULL_NULL_-1_163` (Amazon US) and `NULL_NULL_-1_166` (Amazon CA).
- Only the stray profile shows up as `UNKNOWN_MARKETPLACE`.

1. **Currency vs marketplace:**

- USD spend only appears on Amazon US + the unknown profile.
- CAD spend only appears on Amazon CA.
- No MXN/BRL rows yet.

1. **Campaign spot checks:**

- Sampled US campaigns (`PROFILE_ID = 2874274850477920`): all labeled “Amazon US.”
- Sampled CA campaigns (`PROFILE_ID = 410071870980733`): all labeled “Amazon CA.”

**Action item:** ask Justin whether profile `3378484324565094` should be mapped (likely Amazon US) or excluded. Until then it will stay `UNKNOWN_MARKETPLACE` and QA queries will surface it.



## 2026-03-03

All three QA checks look good and match the prior behavior (Unknown profile = zero cost/sales). Here’s what to capture in `notes/projects/DE-006/testing.md`:

---

### 2026-03-03 — Marketplace profile mapping QA

**Check 1 – Profile → Marketplace sanity**

```sql
SELECT PROFILE_ID, MARKETPLACE_ID, MARKETPLACE_NAME
FROM WAREHOUSE_TEST_PAUL.MARKETING_FCT_ACTIVITY_GP169
GROUP BY 1,2,3
ORDER BY 1;
```

| PROFILE_ID       | MARKETPLACE_ID      | MARKETPLACE_NAME |
| ---------------- | ------------------- | ---------------- |
| 2874274850477920 | NULL_NULL_-1_163    | Amazon US        |
| 3378484324565094 | UNKNOWN_MARKETPLACE | Unknown          |
| 410071870980733  | NULL_NULL_-1_166    | Amazon CA        |

- MX/BR profiles absent because Amazon Ads hasn’t produced rows for them yet.
- `3378484324565094` is the known stray profile → `UNKNOWN_MARKETPLACE`.

**Check 2 – Unknown marketplace audit**

```sql
SELECT PROFILE_ID, COUNT(*) AS row_count
FROM WAREHOUSE_TEST_PAUL.MARKETING_FCT_ACTIVITY_GP169
WHERE MARKETPLACE_ID = 'UNKNOWN_MARKETPLACE'
GROUP BY 1;
```

| PROFILE_ID | ROW_COUNT |
|-------------------|-----------|
| 3378484324565094 | 1 |

- **Expected:** only the stray profile hits the fallback (single row, zero metrics).

**Check 3 – Aggregation**

```sql
SELECT MARKETPLACE_ID, MARKETPLACE_NAME, SUM(COST) AS cost, SUM(SALES_AMOUNT) AS sales
FROM WAREHOUSE_TEST_PAUL.MARKETING_FCT_ACTIVITY_GP169
GROUP BY 1,2
ORDER BY 1;
```

| MARKETPLACE_ID | MARKETPLACE_NAME | COST | SALES |
|--------------------|------------------|-------------|--------------|
| NULL_NULL_-1_163 | Amazon US | 1,799,075.99| 10,156,306.44|
| NULL_NULL_-1_166 | Amazon CA | 66,962.72 | 539,433.00|
| UNKNOWN_MARKETPLACE| Unknown | 0 | 0 |

- Totals unchanged; Unknown profile carries zero spend/sales.

(Optional: attach a screenshot of the Check 3 result if you want visual proof; otherwise the tables above suffice.)

---



### 2026-03-03 — Marketplace mapping QA (WAREHOUSE_TEST_PAUL.MARKETING_FCT_ACTIVITY_GP169)

1. **Profile → marketplace sanity**
```sql
SELECT PROFILE_ID, MARKETPLACE_ID, MARKETPLACE_NAME  
FROM ...GP169  
GROUP BY 1,2,3;
```

```
| PROFILE_ID | MARKETPLACE_ID | MARKETPLACE_NAME |
|-------------------|--------------------|------------------|
| 2874274850477920 | NULL_NULL_-1_163 | Amazon US |
| 3378484324565094 | UNKNOWN_MARKETPLACE| Unknown |
| 410071870980733 | NULL_NULL_-1_166 | Amazon CA |
- MX/BR profiles absent because no source data yet.
- Stray profile `3378484324565094` intentionally unmapped.
```

## ```
2. **Unknown marketplace audit**
```sql
SELECT PROFILE_ID, COUNT(*)  
FROM ...GP169  
WHERE MARKETPLACE_ID = 'UNKNOWN_MARKETPLACE'  
GROUP BY 1;
```

- Only `3378484324565094` (1 row, zero metrics) hits the fallback.

3. **Parity vs. WAREHOUSE.MARKETING_FCT_ACTIVITY**
- Row counts and metric totals match after removing the Display union.
- EXCEPT diff on shared columns returned zero rows:






# 2026-03-06
