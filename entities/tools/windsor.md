---
tags: [entity, tool, windsor, marketing, data-aggregation, fusion92, gep, navira]
aliases: [Windsor, Windsor.ai]
sources: [CF92/1675001857, CF92/1675919361, clients/GEP/eclipse/templates/windsor/google_ads.json, clients/GEP/eclipse/templates/windsor/meta_ads.json]
created: 2026-04-18
updated: 2026-05-29
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

## See Also

- [[fusion92]] — client using Windsor; `windsor` Eclipse connection
- [[GEP]] — Navira Google/Meta via Windsor (2026-05)
- [[GP-225]] — unified marketing schema; the revenue-load gap detail
- [[navira-data-dictionary-phase1a]] — field-level reference + revenue gap
- [[Eclipse]] — pulls data from Windsor
