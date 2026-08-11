---
tags: [entity, tool, windsor, marketing, data-aggregation, fusion92, gep, navira]
aliases: [Windsor, Windsor.ai]
sources: [CF92/1675001857, CF92/1675919361, clients/GEP/eclipse/templates/windsor/google_ads.json, clients/GEP/eclipse/templates/windsor/meta_ads.json]
created: 2026-04-18
updated: 2026-08-10
---

# Windsor

Windsor.ai is a marketing data aggregation platform used by [[fusion92]] and (from 2026-05) [[GEP]]/Navira. It connects to ad platforms (Facebook Ads, Google Ads, etc.) and exposes a unified data feed that [[Eclipse]] pulls from via the `windsorai_v1` connector. Each pull template declares a `fields` list selecting which Windsor columns to ingest.

## GEP / Navira Usage (2026-05)

GEP pulls Google Ads + Meta via Windsor — templates at `clients/GEP/eclipse/templates/windsor/google_ads.json` and `meta_ads.json`, cloned from Fusion92's proven templates. Creds verified 2026-05-29. Feeds Branches 6 (Google) and 7 (Meta) of `MARKETING_FCT_ACTIVITY`. See [[GP-225]] and [[navira-data-dictionary-phase1a]].

### Field-selection gaps & gotchas

- **Conversion value / revenue must be explicitly selected.** The Fusion92 templates (and the GEP clones) **never selected revenue**: Google carries `conversions` + `roas` but not `conversions_value`; Meta selects only video-view actions, no purchase `actions`/`action_values`. Result: cross-channel ROAS can't be computed until those fields are added. This is a **field-selection gap, not a Windsor capability gap** — Windsor exposes them.
- **Validate field names before adding.** Use `GET https://connectors.windsor.ai/{platform}/fields?api_key={KEY}` (e.g. `/facebook/fields`, `/google_ads/fields`) — returns a JSON array of `{id, name, type, ...}`. **Verified 2026-05-29** for GEP's key: Google revenue = **`conversions_value`** (+ `all_conversions_value`, `conversion_value`, `adnetwork_revenue`, `roas`); Meta purchase = **`actions_purchase`**/**`action_values_purchase`** (variants `actions_omni_purchase`/`action_values_omni_purchase`, `actions_offsite_conversion_fb_pixel_purchase`/`action_values_offsite_conversion_fb_pixel_purchase`). **Non-existent (don't use): `action_value_omni_purchase` (singular), `purchases`, `purchases_value`, `purchase_roas`, `website_purchase_roas`.** Key lives as `WINDSOR_API_KEY` on Function App `func-aldc-cred` (rg `aldcprodrsgpconnector1c`).
- **Row-splitting risk** (called out verbatim in both GEP + Fusion92 template comments): *some combinations of fields cause Windsor to split one logical row into two sharing the same primary key, each with partial data* — this corrupts the Snowflake merge. After adding fields, test a single day grouped by PK for >1 row before activating.
- **Team API key pulls ALL accounts** authenticated in Windsor across clients — so the GEP key also returns Fusion92's accounts (verified 2026-05-29: an unfiltered GEP pull returns **45 Google + 19 Meta** accounts). A per-client account filter must be built in before real activation.
  - **Verified server-side filter syntax (2026-05-29):** `filter=[["account_id","in",["id1","id2"]]]` — the value MUST be a **JSON array**; a comma-separated string 400s (`Invalid value for 'in' operator`). Empirically narrows Google 45→6 and Meta 19→3 to Navira-only. (Windsor docs also list `eq/neq/gt/.../contains`; `in` works despite a docs gap.)
  - **Wired into the connector ([[GP-226]] defense-in-depth):** `windsorai_v1` now reads `options.account_ids` from the template and serializes it into that `filter` param (Gate A — foreign accounts never land). Backed by a warehouse `INNER JOIN SHARED_DIM_ENTITY` on `MARKETING_FCT_ACTIVITY` Branch 6/7 (Gate B — unmapped accounts can't reach the fact). Gate B proven on the `TEST_DG1_GEP_DEV` clone (injected Fusion92 account dropped; Navira rows survive).
  - **Deployment status (2026-06-01):** connector code DEPLOYED — `97979df` FF-merged to `development`, `:development` image built with the filter. Windsor connection + 2 templates CREATED in TEST Cosmos (`aldctestcsdb1c01`/core), `status:inactive`, topic overridden to `GOOGLE_ADS_DEV`/`META_DEV` for isolated validation (conn `8e558ceb…`, ADR-001 linked). **Not yet active** — TEST agent fleet is dormant (TEST uses prod share, doesn't self-ingest), must be revived first. See [[navira-dwh-data-landing]] and [[project_test_prod_share]].

## Authentication & Platform Setup

### Adding Users

Team members must be added in Windsor under the **Manage Account** screen. The initial user is invited by ALDC; subsequent users can be invited by either ALDC or the Fusion92 team.

An invitation email is sent and must be accepted before access is active.

### Granting a Platform Access to Windsor

Example: Facebook Ads.

1. Log into Windsor.
2. Select **Facebook Ads** on the sidebar.
3. Click **Grant Facebook Ads Access**:
   - A Facebook authentication popup opens.
   - **Log in as the user who has ad access to the desired accounts.** This is required — the authenticating user must have permissions to the account data you want Windsor to pull.
   - Edit permissions in the Facebook dialog:
     - Enable: "Access your Page and App Insights" and "Access your Facebook ads and related stats".
     - Disable all other sliders.
     - Leave the permissions box.
   - Continue through any remaining Facebook steps.
4. Once connected, Windsor shows a list of available ad accounts.
5. Tick the box next to each account that should be synced.

## Adding Accounts to Platform Connections

After Windsor is authenticated for a platform, any team member with Windsor access can adjust which accounts Eclipse is authorized to pull data for.

### Managing Accounts

Under **Manage Account**, new users can be added at any time. Once invited and accepted, they can see and toggle accounts across all connected platforms.

To authorize an account: simply tick the box next to the account name in the relevant platform view.

### Troubleshooting: Missing Accounts

If an expected account does not appear in Windsor's account list, the likely causes are:

- The permissions for the authenticating user need adjusting (they lack ad access to that account in the platform).
- Windsor was authenticated with a user who does not have access to the missing account — re-authenticate with a user who does.

---

## ⚠ The silent account-drop failure mode (confirmed once — check this FIRST)

**Windsor accounts disconnect silently, and it surfaces weeks later as "our data stops on date X".** No error, no failed run, no alert. The Eclipse pull keeps succeeding — it just returns fewer accounts.

**Why it is silent:** the Fusion92 pull templates (`linkedin_ads.json`, `linkedin_ads_video_social.json`, the Meta feed) declare **no account list**. They ingest whatever the Windsor API returns, so an account leaving the response is indistinguishable downstream from an account that stopped spending.

> Contrast [[GP-225]]/GP-226: the GEP/Navira templates *do* pin `options.account_ids`, which `windsorai_v1` serialises into a server-side `filter`. That guards against foreign accounts leaking **in**; it does **not** alert when an expected account drops **out**. Neither client has drop-out detection.

### Confirmed instances

| Date | Client / platform | Account(s) | Detected by | Lag |
|---|---|---|---|---|
| 2026-07-21 | [[fusion92]] LinkedIn | 509879445, 502845846, 506641008 (+508272220 on 05-31) | client complaint (Juliann, 2026-08-07) | **17 days** |

Within LinkedIn this is progressive decay — 4 of 5 accounts fell out across three months, one or a few at a time. That pattern is evidenced *for LinkedIn*; do not generalise it to other platforms without the same evidence.

> **⚠ Retracted 2026-08-10: Smile Doctors (Meta `1076840895722327`, 2026-05-22) was previously listed
> here as a second confirmed instance. It is not — it is a wound-down account.** See § *Telling a drop
> from a wind-down* below. [[FU92-415]] assessed it correctly at the time ("campaign lifecycle, not
> connector issue") and was overridden on no evidence. Two sessions then repeated "confirmed twice"
> and treated it as an unresolved incident. **One instance was mistaken for a pattern.**

### Telling a drop from a wind-down (do this before calling anything an incident)

Both look identical at the summary grain — an account with no recent data. They are opposite causes
with opposite owners, and one cheap query separates them:

| | **Dropped from Windsor** | **Wound down** |
|---|---|---|
| Row emission | stops **abruptly**, nothing after the cutoff | **declines** over days/weeks |
| Spend on final days | at or near run-rate | falls to **`$0.00`** |
| `$0.00` rows near the end | none — no rows at all | **many** — the feed is still reporting |
| Campaign count | unchanged right up to the cutoff | collapses first |
| Owner | **client** — re-authorise in Windsor | nobody, it is normal |

The load-bearing signal is that **this feed does emit literal `$0.00` rows for live-but-not-delivering
campaigns**. So an *absence of rows* means no-load; a *presence of `$0.00` rows* means the instrument
is still watching and the campaigns genuinely stopped. Worked examples:

- **LinkedIn `509879445` (a real drop):** 10 rows/day at ~$220/day, then nothing. Final day at 55–61%
  of run-rate — one load caught mid-day, not a taper.
- **Meta `1076840895722327` Smile Doctors (a wind-down):** ~115 campaigns/day at $6k–$20k through
  April; 2026-05-01 collapses to 41 campaigns with **40 of 54 rows at `$0.00`**; then 1 row/day of
  `$0.00` until 05-09. 1,263 zero-spend rows on the account in total.

This is the false-positive class the freshness monitor cannot yet distinguish — tracked in
[[FU92-424]].

### Diagnosis runbook (~10 minutes)

**Step 1 — ingestion or delivery?** Group the raw table by account **and load timestamp**. Aggregating at *platform* grain hides this completely — one healthy account makes the whole platform look current.

```sql
SELECT ACCOUNT_ID, MAX(TO_DATE(DATE)) AS MAX_SPEND_DT,
       MAX(___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___) AS LAST_LOAD, COUNT(*) AS N
FROM LINKEDIN_ADS.CURRENT_LINKEDIN_CAMPAIGN_PERFORMANCE
GROUP BY ACCOUNT_ID ORDER BY MAX_SPEND_DT DESC;
```
Several accounts sharing **one final load timestamp to the millisecond** while others keep loading ⇒ the account scope shrank. Not campaigns ending.

**Step 2 — negative control (this is what makes it conclusive).** Confirm the feed *does* land literal `$0.00` rows when a campaign is live but not delivering:
```sql
SELECT ACCOUNT_ID, COUNT(*) AS ZERO_ROWS, MAX(TO_DATE(DATE)) AS LATEST
FROM LINKEDIN_ADS.CURRENT_LINKEDIN_CAMPAIGN_PERFORMANCE WHERE SPEND = 0 GROUP BY ACCOUNT_ID;
```
If it does (LinkedIn: 450 such rows on one account), the **absence** of rows is positive evidence of no-load rather than no-spend. Without this control you cannot separate the two.

**Step 3 — ask Windsor directly.** The discriminating test, and it names the fix owner:
```bash
KEY=$(az functionapp config appsettings list -n func-aldc-cred -g aldcprodrsgpconnector1c \
      --query "[?name=='WINDSOR_API_KEY'].value" -o tsv)   # never echo it
curl -s "https://connectors.windsor.ai/linkedin?api_key=$KEY&date_from=<pre-cutoff>&date_to=<today>&fields=date,account_id,account_name,spend"
```
Query a window **spanning the cutoff** so the three outcomes separate:

| Result | Meaning | Owner |
|---|---|---|
| Account **absent** entirely | Windsor-side disconnection | **Client** — re-grant in Windsor portal |
| **Present**, rows after cutoff | Windsor serves it; loss is Eclipse-side | **ALDC** — template / schedule |
| **Present**, zero rows after cutoff | "Listed but stale" — platform denies insights | **Client** — re-grant platform permission |

Reference implementation with pre-committed predictions: `clients/FUSION_92/snowflake/scripts/_fu92_windsor_accounts.py` (branch `feature/paulrussell/fu92-flight-actuals-diagnosis`).

### Fix + the backfill trap

Client re-authenticates the platform in Windsor (§ *Granting a Platform Access to Windsor*) as a user with ad access to the missing accounts, then ticks each one.

⚠ **On resume, verify the backfill actually reaches back to the cutoff date.** The Fusion92 LinkedIn template uses `partition_scheme.window_type = month` with a 60-day `time_to_live` on `partition_date`, so monthly partitions *should* re-pull — but if the pull only covers a recent window, the gap between cutoff and reconnection stays **permanently** missing and flights show a hole rather than a tail. Confirm `MAX(DATE)` per account and spot-check a date inside the gap.

**✅ Answered 2026-08-10: the backfill DOES reach back.** Account `509879445` reconnected 20 days after its 07-21 cutoff and came back with *continuous* daily coverage across the whole gap (07-22 → 08-10, 118 rows). The monthly partition scheme re-pulls as designed. Still verify per account — but the expected outcome is a full heal, so a *hole* after reconnection is a genuine finding, not the norm.

⚠ **Do not read a post-reconnection volume drop as a partial backfill without a control.** The same account went 10 rows/day in July to 2 rows/day in August, which looks exactly like a half-filled partition. It wasn't: four campaign groups ended on 07-31 and one ran on unbroken, and the **never-dropped** sibling account dropped at the same month boundary (5 → 3 campaign groups). An account that never disconnected cannot show a backfill artifact — that comparison is what separates "campaigns cycled" from "the pull is short", and it costs one query.

**Clients may reconnect without telling you.** `509879445` came back ~4.5 h after the instruction email with no reply, while its two siblings stayed dark. Re-measure at the start of each session instead of inheriting the previous session's account list.

### Prevention

An account-freshness monitor is **built and deployed** on the [[observability-platform]] obs-jobs runner (2026-08-10, `observability` commit `bdde728`) — Tier 1 account-dark / Tier 2 feed-dark, daily 19:00 UTC. A per-account freshness check — *"any account that loaded yesterday but not today"* — would have caught the 2026-07-21 LinkedIn drop on 2026-07-22 instead of 2026-08-07. **The one confirmed instance was found by the client, not by us.**

> ⚠ **This does NOT close [[FU92-379]]**, despite two sessions claiming it did. FU92-379 is *"Flight Check Data Sync Monitoring"* — about the Flight Check **Azure Function**: invocation logs reporting success while errors were logged, and no alerting when the function fails. The account-freshness monitor addresses neither. FU92-379 remains genuinely unaddressed. Check what a ticket actually says before claiming a piece of work realises it.

Delivery is proven too: the stack runs `OBS_DRY_RUN=false`, and the scheduled run posted real alerts to `#observability-dev` (4 findings, re-posted on the throttle cycle, zero failed POSTs). Deploying it surfaced four separate faults that would each have stopped it running at all; see [[observability-platform]] § *Adding a Plane 3 job* before trusting any similar monitor.

## See Also

- [[fusion92]] — client using Windsor; `windsor` Eclipse connection
- [[GEP]] — Navira Google/Meta via Windsor (2026-05)
- [[GP-225]] — unified marketing schema; the revenue-load gap detail
- [[navira-data-dictionary-phase1a]] — field-level reference + revenue gap
- [[Eclipse]] — pulls data from Windsor
