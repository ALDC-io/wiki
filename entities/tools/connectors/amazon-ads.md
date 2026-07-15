---
tags: [entity, tool, connector, amazon-ads, amazon-dsp, oauth]
aliases: [Amazon Ads Connector, Amazon DSP Connector]
sources: [Confluence CONN/1298792450]
created: 2026-04-18
updated: 2026-07-15
---

# Amazon Ads and Amazon DSP Connector

Eclipse connector for Amazon Advertising (Sponsored Products/Brands/Display) and Amazon DSP. Uses a centralized ALDC "Login with Amazon" OAuth application — ALDC maintains the OAuth app and individual clients authorize through it.

> **Prefect migration note:** This connector must be rebuilt as a Prefect flow. The multi-tenant OAuth pattern (centralized ALDC app + per-client refresh tokens) is the reference model. **Known limitation:** Advertiser IDs for DSP must currently be hardcoded in templates — the Advertiser endpoint is in beta. The Prefect implementation should poll for beta release and implement dynamic advertiser ID discovery when available.

## Account & Shared Credentials

- **ALDC Amazon Developer email**: support@aldc.io
- **Client ID**: Dashlane Secrets → "Login with Amazon Client ID"
- **Client Secret**: Dashlane Secrets → "Login with Amazon Client Secret"

> These shared credentials are used for all client integrations via the centralized OAuth app.

## Client-Specific Credentials

Each client has an individual **Refresh Token** stored in Dashlane Secrets in the appropriate client group.

## Authorization Flow (New Client Setup)

### Step 1: Send Authorization URL to Client

```
https://www.amazon.com/ap/oa?client_id=amzn1.application-oa2-client.3d6735ea7ce54f5395aa1850dc39d878&scope=advertising::campaign_management&response_type=code&redirect_uri=https://amazon.com
```

### Step 2: Client Grants Consent

Client opens URL → logs in with Amazon account → grants ALDC permission → receives authorization code (in redirect URL).

### Step 3: Exchange Code for Refresh Token

```python
import requests

response = requests.post(
    "https://api.amazon.com/auth/o2/token",
    data={
        "grant_type": "authorization_code",
        "code": "<authorization_code_from_client>",
        "client_id": "<CLIENT_ID_FROM_DASHLANE>",
        "client_secret": "<CLIENT_SECRET_FROM_DASHLANE>"
    }
)
refresh_token = response.json()["refresh_token"]
```

### Step 4: Store Refresh Token

Add to Dashlane Secrets with name `{client_name}_amazon_refresh_token` → share with appropriate client group.

### Step 5: Test

Use Amazon Ads Postman collection to verify the refresh token works (list campaigns endpoint).

## Regional Endpoints (Non-US)

For UK/EU authorization, use regional endpoints instead of the US defaults:

| Region | Auth URL domain | Token exchange endpoint | Profiles endpoint |
|---|---|---|---|
| US (NA) | `amazon.com` | `https://api.amazon.com/auth/o2/token` | `https://advertising-api.amazon.com/v2/profiles` |
| UK/EU | `amazon.co.uk` | `https://api.amazon.co.uk/auth/o2/token` | `https://advertising-api-eu.amazon.com/v2/profiles` |

Using the wrong endpoint for code exchange will silently fail or return US-only profiles. See `scripts/gp221_uk_token_exchange.ps1` in aldc-shipyard for a working UK exchange script.

### GEP/Navira Active Profiles

| Region | Profile ID | Currency | Account | Seller ID | Marketplace ID |
|---|---|---|---|---|---|
| UK | `1236242149887729` | GBP | Global Ecom UK | `AC8RG0YC8GJ0U` | `A1F83G8C2ARO7P` |

12 EU profiles total (UK, DE, FR, IT, ES, NL, SE, PL, IE, BE, AE, SA) under "Global Ecom UK" / "Global Ecom Trading Networks". Token exchanged 2026-05-08. **This 2026-05-08 refresh token is a superset** — it covers the 12 EU marketplaces **plus** the existing US/CA/BR/MX, so one connection (`66627ed9`) can serve both NA and UK/EU templates.

### Connector EU support ([[GP-257]], PR #125 `d00fc39`)

`connector/amazon_ads.py` was NA-only until GP-257. Added two options:
- **`region`** (`NA` default = no-op; `EU` re-points LWA host → `api.amazon.co.uk` and Ads host → `advertising-api-eu.amazon.com`; `FE` → `.co.jp`/`-fe`). Region map: `REGION_ENDPOINTS`.
- **`profile_ids`** — list filter to scope a pull to specific profiles (e.g. `["1236242149887729"]` for UK-only).

`refresh_token` comes from the connection; `client_secret` from env `AMAZON_ADS_CLIENT_SECRET`. Merged to `development` (`:development` image = `40430ed`); connector prod branch = **`master`** (deferred). **Proven end-to-end through real [[Eclipse]] dispatch 2026-06-11** — UK GBP data landed to `TEST_DG1_GEP.AMAZON_ADS`, exact-match to the sandbox, 0 regression. See [[GP-257]] for the dispatch pattern + the backfill visibility-timeout gotcha.

### Attribution product ([[GP-287]], 2026-07-15) — off-Amazon media → Amazon conversions

`amazon_ads.py` gained an `ATTRIBUTION` product (`options.amazon_ads_product: "attribution"`, category `performance_report`) — measures Google/Meta ads driving Amazon orders. **It uses a DISTINCT API** (`/attribution/*`, cursor-paginated on `cursorId`), NOT the `/reporting/reports` flow, so it is handled by `run_attribution()`: per profile `GET /attribution/advertisers` → paginate `POST /attribution/report`. Dates → `YYYYMMDD`; metrics template-overridable via `options.attribution_metrics`. Branch `feature/amazon-attribution-connector`; image `agent-dcgeneral:attribution`. **Deployed + canary-validated LIVE in TEST** (landed `AMAZON_ADS.ATTRIBUTION_PERFORMANCE_REPORT`).

Gotchas learned building it:
- **`RestSimple.Transact()` raises on ANY non-200** — status handling must be in `except` (inspect `_response_code`), not after the call. A **403 on `/attribution/advertisers`** = that profile is not authorized for Amazon Attribution (GEP's **BR** profile) → catch + skip, don't abort the whole multi-profile run.
- **PERFORMANCE reportType rejects `attributedNewToBrand*` metrics** (HTTP 400 "Invalid metric") — keep them out of the PERFORMANCE list (may be PRODUCTS-only).
- **Shared-account scoping:** the `66627ed9` conn serves multiple GEP clients (advertisers GlobalEcom / The Super Savers / Falls River). Scope to Navira's `profile_id`s (US `2874274850477920` is the only one carrying attribution data) — either downstream in the warehouse (MARKETPLACE_PROFILE_MAP) **or** at pull-time via the existing **`profile_ids`** template option (cleaner; avoids landing other clients' data + their vendor-profile edge cases).
- **Landed shape:** UPPERCASE VARCHAR; `Click-throughs`→`CLICK_THROUGHS`; `DATE`='YYYYMMDD'; no NTB columns; publisher values include `Youtube`/`GlobalPR` (map Youtube→GOOGLE).

## Known Limitations

### DSP Advertiser IDs — Manual Management

Amazon DSP advertiser IDs must be manually specified in report templates because the Advertiser discovery endpoint is in beta:

- https://advertising.amazon.com/API/docs/en-us/dsp-advertiser

**Impact:** When Fusion92 adds new advertisers in the Amazon Ads console, templates must be updated manually with the new advertiser IDs.

**Prefect action item:** Monitor beta endpoint release; implement dynamic advertiser discovery once available.

## API References

- Getting Started: https://advertising.amazon.com/API/docs/en-us/guides/get-started/overview
- Amazon Ads Postman Collection: available from the API documentation (recommended for setup and testing)

## See Also

- [[eclipse]] — connector platform
- [[fusion92]] — primary client using Amazon Ads/DSP connector
- [[connector-development-standards]] — attribute hierarchy and parameter patterns
