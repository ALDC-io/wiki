---
tags: [process, operations, connector, oauth, token-refresh, bing-ads, meta, facebook, amazon-spapi]
aliases: [Connector Token Refresh, Bing Ads OAuth Token Regeneration]
sources: [Confluence CONN/1575747585, TECH/1777106945 (Steven Offboarding)]
created: 2026-04-18
updated: 2026-07-06
---

# Connector Token Refresh

Operational runbook for refreshing OAuth tokens across connectors. Full audit completed 2026-05-21.

## Token Refresh Audit (2026-05-21)

| Connector | Client | Auth Type | Expiry | Auto-Refresh | Status |
|---|---|---|---|---|---|
| `microsoft_bing_ads_v1` | Fusion92 | OAuth refresh_token | 90 days | Daily workflow (07:00 UTC) | Covered |
| `facebook_business_v1` | Fusion92 | Long-lived access_token | ~60 days | Daily workflow (08:00 UTC) | Covered ([[FU92-415]]) |
| `amazon_ads_v1` | Fusion92, GEP | OAuth refresh_token | Long-lived | Connector auto-exchanges | Low risk |
| `amazon_sellercentral_v1` | GEP | LWA refresh_token + **client_secret** | Long-lived | Connector auto-exchanges | US client secret rotated 2026-07-06 (see below) |
| `windsorai_v1` | Fusion92 | Static API key | Never | Windsor manages OAuth | No risk |
| `trade_desk_my_reports_v1` | Fusion92 | Static auth_token | **Unknown** | None | [[FU92-416]] |
| `viant_dsp_reporting_v1` | Fusion92 | Basic auth | **Unknown** | None | [[FU92-416]] |

## Microsoft Advertising (Bing Ads) — 90-day refresh

Bing Ads OAuth refresh tokens expire 90 days after generation. An automated refresh workflow runs daily, but when it fails the manual process below is required.

### Automated Refresh Workflow

Deployed in the **Fusion workflow function app** ([[workflows|workflows repo]] — `F92_workflow_app`) for each environment.

**Prerequisites:**
- Account and connection ID present in the environment's Fusion variables
- Microsoft Ads connection document present in that environment's CosmosDB

**Behaviour:** Runs daily at 07:00 UTC. Retrieves refresh token from CosmosDB connection document → obtains new token via token endpoint → updates connection document if successful.

> **Diagnostic tip (from Steven Offboarding):** If Microsoft Ads data stops showing up in the Fusion warehouse, the **first thing to check** is whether this automated token refresh workflow is running successfully in the [[workflows|Dax API]] function app.

### Manual Process (When Automated Refresh Fails)

#### Step 1: Request Consent URL from Fusion

Provide this URL to the Fusion contact. Coordinate in real-time (call or Teams) — the authorization code in the redirect URL is short-lived.

```
https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=98fe3659-b606-4550-9b16-c5e51a792618&response_type=code&redirect_uri=https://login.microsoftonline.com/common/oauth2/nativeclient&response_mode=query&scope=openid%20offline_access%20https%3A%2F%2Fads.microsoft.com%2Fmsads.manage&state=8675309
```

> If the Fusion employee lacks required permissions, a popup goes to Fusion IT for approval. Once approved they receive the redirect URL.

#### Step 2: Receive Authorization Code

Fusion pastes the full redirect URL. Extract the `code=` parameter value.

#### Step 3: Exchange Code for Refresh Token (PowerShell)

Get client secret from Dashlane: **"Microsoft Ads Application - Eclipse Secret 2024-03-28"**

```powershell
$clientId = "98fe3659-b606-4550-9b16-c5e51a792618"
$clientSecret = ""  # Insert from Dashlane

$code = Read-Host "Paste the full redirect URL here:"
$code = $code -match 'code=(.*)\&'; $code = $Matches[1]

# Exchange authorization code
$response = Invoke-WebRequest https://login.microsoftonline.com/common/oauth2/v2.0/token `
  -ContentType application/x-www-form-urlencoded -Method POST `
  -Body "client_id=$clientId&client_secret=$clientSecret&scope=https://ads.microsoft.com/msads.manage%20offline_access&code=$code&grant_type=authorization_code&redirect_uri=https%3A%2F%2Flogin.microsoftonline.com%2Fcommon%2Foauth2%2Fnativeclient"
$oauthTokens = ($response.Content | ConvertFrom-Json)

# Confirm with one refresh cycle
$response = Invoke-WebRequest https://login.microsoftonline.com/common/oauth2/v2.0/token `
  -ContentType application/x-www-form-urlencoded -Method POST `
  -Body "client_id=$clientId&client_secret=$clientSecret&scope=https://ads.microsoft.com/msads.manage%20offline_access&grant_type=refresh_token&refresh_token=$($oauthTokens.refresh_token)"
$oauthTokens = ($response.Content | ConvertFrom-Json)
Write-Output "New refresh token: " $oauthTokens.refresh_token
```

Use the **final** refresh token output (from the second call).

#### Step 4: Update Dashlane

Update **"Fusion Microsoft Ads Refresh Token"** in Dashlane with the new token.

#### Step 5: Validate

```powershell
$accessToken = "";       # From step 3 output
$developerToken = "";    # From current CosmosDB connection document

[xml]$getUserRequest = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v13="https://bingads.microsoft.com/Customer/v13"><soapenv:Header><v13:DeveloperToken>{0}</v13:DeveloperToken><v13:AuthenticationToken>{1}</v13:AuthenticationToken></soapenv:Header><soapenv:Body><v13:GetUserRequest><v13:UserId xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/></v13:GetUserRequest></soapenv:Body></soapenv:Envelope>' -f $developerToken, $accessToken

$headers = @{"SOAPAction" = "GetUser"}
$uri = "https://clientcenter.api.bingads.microsoft.com/Api/CustomerManagement/v13/CustomerManagementService.svc"
$response = Invoke-WebRequest $uri -Method post -ContentType 'text/xml' -Body $getUserRequest -Headers $headers
Write-Output $response.Content
```

A successful XML response confirms the token is working.

## Meta / Facebook Ads — ~60-day refresh

Meta long-lived access tokens expire approximately every 60 days. An automated refresh workflow runs daily, deployed as part of [[FU92-415]].

### Automated Refresh Workflow

Deployed in the **Fusion workflow function app** ([[workflows|workflows repo]] — `F92_workflow_app`).

- **Timer:** `f92_refresh_meta_ads_token` — daily at 08:00 UTC (1 AM PST)
- **Workflow:** `workflows/meta_ads.py` — `MetaAdsTokenRefreshWorkflow`
- **Connection:** `1df7d48a-2deb-4477-b9b0-31f654d27152` (Meta Ads, account `0fc00e34`)
- **Env var:** `META_ADS_CONNECTION_ID` must be set in Function App config

**Behaviour:** Reads `app_id`, `appsecret`, `access_token` from CosmosDB connection doc → calls Meta Graph API `fb_exchange_token` endpoint → writes new token back → logs days until expiry.

**Constraint:** Meta tokens can only be refreshed when they are at least 24 hours old. Daily refresh keeps the token continuously alive.

### Manual Process (When Automated Refresh Fails)

#### Step 1: Generate a temporary access token

1. Go to https://developers.facebook.com → App Dashboard → Tools → Graph API Explorer
2. Select the ALDC app (App ID: `812919267215628`)
3. Generate a User Access Token with `ads_read` permission
4. Copy the temporary token

#### Step 2: Exchange for long-lived token

```python
import requests

response = requests.get(
    "https://graph.facebook.com/v21.0/oauth/access_token",
    params={
        "grant_type": "fb_exchange_token",
        "client_id": "812919267215628",
        "client_secret": "<appsecret from meta.json>",
        "fb_exchange_token": "<temporary_token>",
    },
)
new_token = response.json()["access_token"]
print(f"New token: {new_token}")
print(f"Expires in: {response.json().get('expires_in', 'unknown')} seconds")
```

#### Step 3: Update CosmosDB connection document

Use Postman or the script at `aldc-launchpad/scripts/_sync_meta_templates.py` (adapt for connection update):

```
POST {{core_api_url}}work/connectionupdate
{
    "account_id": "0fc00e34",
    "connection": "1df7d48a-2deb-4477-b9b0-31f654d27152",
    "document": {
        "connection": {
            "app_id": "812919267215628",
            "appsecret": "<appsecret>",
            "access_token": "<new_long_lived_token>"
        }
    }
}
```

#### Step 4: Validate

Wait for the next scheduled connector run, or trigger manually. Check that data appears in `PROD_DG1_FUSION_92.META.*` tables.

## Amazon Seller Central (SP-API) — Client Secret Rotation

The Seller Central (SP-API) connector authenticates with an **LWA app client secret** (`client_secret`) plus a per-app `refresh_token`. Unlike Ads, the secret is stored **inline in the connection document** (both prod Cosmos and the repo JSON). When Amazon issues a new client secret for the app, it must be pushed to the live Cosmos connection doc — editing the repo JSON alone does **not** rotate the runtime credential (Eclipse reads the connection from Cosmos).

> **GEP/Navira has two separate Seller Central apps** (confirmed 2026-07-06). Each has its own `client_identifier`, `client_secret`, and `refresh_token` — a secret only authenticates its own app (Amazon enforces the `client_id`↔`client_secret` pairing), so rotate the correct one:
>
> | Connection | Cosmos ID | App (`client_identifier`) | Data scope |
> |---|---|---|---|
> | **US / NA** "Amazon Seller Central" | `b21192a3-2a6d-4ab0-9516-ac94572660b0` | `amzn1.application-oa2-client.4bd6969a…` | US/CA/MX/BR orders |
> | **UK / EU** "Amazon Seller Central - UK" | `22669b98-b61e-4278-a8fd-b7e5a2bd5023` | `amzn1.application-oa2-client.e0b20985…` | UK/EU orders (Cosmos-only; not in repo) |
>
> Both are account `da8904db`, partner `A3VJEVLAWT2I1E`. Ad data is separate again — the single `Amazon Ads API` connection (`66627ed9`), whose secret lives in env `AMAZON_ADS_CLIENT_SECRET`, not the connection doc.

### Evidence-gated rotation runbook

1. **Validate the new secret (auth layer).** Exchange the *live* refresh token for an access token with the new secret against the correct region endpoint (US/NA: `https://api.amazon.com/auth/o2/token`). A returned `access_token` = the secret is valid **and** provably belongs to that app (wrong-app secret → `invalid_client`).
2. **Read the live Cosmos doc first** (`work/connectiondescribe`) — capture the current secret as the rollback value, and the *live* refresh token (the repo copy may be drifted). Confirm the live secret is the one you expect to replace.
3. **Prove data reach (consumer layer), not just auth.** Mint a token with the *old/live* secret and with the *new* secret, call `getMarketplaceParticipations` on each regional endpoint (`sellingpartnerapi-na/eu/fe`), and diff the reachable marketplace set. Identical set = the swap cannot drop data (the secret only authenticates the app; the refresh-token grant fixes the seller/marketplace scope).
4. **Write to Cosmos** via `work/connectionupdate`, sending the **complete** `connection` object (the update replaces that key wholesale — partial sends drop fields like the refresh token).
5. **Re-read + smoke test.** Re-describe the doc, then mint a token from the *stored* runtime credential and call `getMarketplaceParticipations` — proves the deployed credential works end-to-end.
6. **Reconcile the repo** (`clients/GEP/eclipse/connections/amazon_seller_central.json`) + vault to match live. **Retire the old secret in the Amazon Developer console** only after the smoke test passes (it's the live rollback until then).

`work/connectionupdate` semantics: top-level key merge, per-key wholesale replace, type must match (dict→dict). See `core_api/v1/route_work.py:work_connection_update`.

### Rotation log

| Date | App | Connection | New secret | Prior (rollback) | Evidence |
|---|---|---|---|---|---|
| 2026-07-06 | US Seller Central `…4bd6969a` | `b21192a3…` (prod Cosmos) | `…4832878c…fa57f9` | `…268754ac…005c42` | Auth ✓ (HTTP 200); data-reach diff ✓ (identical 8 US/NA marketplaces old vs new); post-write smoke test ✓. Repo had drifted on secret **and** refresh token — both reconciled to live. Full record in `vault/infra-credentials.md`. |

> **Security debt — secret is still committed to the `clients` repo.** This rotation is like-for-like; it does not remove the secret from git. The proper fix (KV holds values → repo holds only references → runtime resolves from Key Vault → purge git history) is tracked under **ALDC-302** (parent incident, In Progress): **ALDC-318** (rotate ad-platform/Amazon tokens), **ALDC-319** (migrate active secrets to Key Vault + sanitize files at HEAD), **ALDC-320** (git-history purge), plus the GEP-scoped design ticket **GP-280**. Confirmed 2026-07-06: **neither `core_api` nor the `connector` repo has any Key Vault integration** — secrets are read inline from CosmosDB, so KV runtime-resolution is net-new code, and it must land *before* the repo files are sanitized (ALDC-319 coupling constraint). Precedent for the KV layout: Lectric SP-API creds live in `aldc-vault-prod` as `lectric--amazon-spapi--*` (naming `{client_code}--{provider}--{credential_type}`).

## ⭐ The rule this runbook exists to enforce (learned the expensive way, 2026-09-03/04)

**A credential refresh needs a watched success signal, not a log line.** Three concurrent Fusion92
outages, three different silent-failure mechanisms, one identical outcome — nobody acted for weeks:

| Outage | Mechanism | Silent for |
|---|---|---|
| [[FU92-427]] Trade Desk | alerted **31 times** to Slack; templates outside `critical: []` so default severity, read as noise | 29 days |
| [[FU92-431]] Microsoft Ads | timer catches every exception and calls `logging.error` — nothing alerts, retries, or escalates | ~5 months |
| FU92-432 Viant R&F | alerting since 2026-04-25, never escalated | 4+ months |

Three corollaries, each paid for:

1. **Creating a secret in the provider is not a rotation.** FU92-431: a new Azure AD secret was
   created 2026-05-22T19:17:37Z and a refresh token minted **59 seconds later** — but the Function
   App's `MICROSOFT_ADS_CLIENT_SECRET` was never updated. The app kept presenting the *expired*
   secret, failed daily for 90 days, and the fresh token died of inactivity unused.
   **→ Rotation checklist must end with: update every consumer's configuration, then prove the
   consumer used it.**
2. **When an audit finds an unknown expiry, ship the staleness alarm FIRST and investigate second.**
   [[FU92-416]]'s 2026-05-21 audit was correct and thorough; its first Trade Desk step was
   *"check CosmosDB `_ts` on connection doc `2aa7e056` to determine token age"* — one query that
   returns 2025-08-05 and puts a dated wall on the calendar eleven weeks out. It was never run,
   because the output was a *Medium investigation ticket* rather than a dated risk. Worse, the
   audit's own alarm phase was scoped **last, behind the investigation** — so the one control that
   did *not* depend on knowing the answer was gated on knowing the answer.
3. **An emergency rotation must record its issue date and computed expiry somewhere with a
   calendar.** The 2025-08-05 Trade Desk fix worked perfectly and left behind nothing that could
   warn us. It recurred to the hour, twelve months later.

## Trade Desk — 365-day lifespan (**ANSWERED** 2026-09-03, [[FU92-427]])

**The `TTD-Auth` token lifespan is 365 days.** Proven by three independent instruments after the
token expired and took the connector down for 29 days:

- Cosmos `work_connection/2aa7e056…` `_ts` = `1754427269` → written **2025-08-05T20:54:29Z**
- The token's own embedded protobuf issuance field → **2025-08-05T20:45:51Z** (it is a base64
  protobuf, not an opaque string — 58 bytes, field 1.1 is a 100 ns-since-epoch issuance stamp)
- git `clients@f31f0113` *"Add new Trade Desk Token."* → **2025-08-05T21:14:37Z**

+365 days lands **inside** the observed bracket (last success 16:22:56Z, first 401 22:24:18Z on
2026-08-05). **Expired, not revoked** — nothing else lands on an anniversary to within 90 minutes.

This was the **second annual instance**; the same outage ran 2025-08-01→08-05 and was fixed by
minting a replacement, which set the 2026 timer.

### Gotchas worth keeping

- **There is no code anywhere in the estate that calls `/v3/authentication`.** Every token has been
  minted by hand through the partner portal. There is no prior art to copy for automated refresh.
- **TTD issues a short-lived (~24h) *and* a long-lived form.** Confirm the token-lifetime parameter
  while logged in — minting the short form by accident re-breaks the feed the next day.
- **The credential was absent from Key Vault, every repo, and the wiki vault** (all three measured
  with proven-live instruments). It had not survived the original engineer's offboarding.
- **Recovery self-arms.** TTL retirement is gated on a *completed* run (`route_work.py:1259`), so
  nothing retires during an outage — stuck partitions stay `active`/`in_queue` and retry themselves
  once a token works. The 2025 outage recovered **12/12** dates with `schedule_id` unchanged.
- ⛔ **Never `work_template_delete` to repoint a `schedule_id`** — it calls `warehouse_reset`, which
  issues `DROP TABLE`. That is 14.6M rows / 935 days on the Performance template. Use
  `work_template_update` only.
- 🔴 **The live prod token is committed in plaintext** to
  `clients/FUSION_92/eclipse/connections/trade_desk_my_reports.json` (repo value == prod value,
  verified by hash). Editing that file rotates nothing — Eclipse reads Cosmos.
- **Next expiry: 365 days after whatever date the replacement is minted.** Diarise it.

## Viant — measured healthy, lifespan still unknown

Measured 2026-09-03: `viant_dsp_reporting_v1` is **healthy** — Campaign Performance 40/40 complete,
Campaign ROAS 40/40, Conversion Report 39/40 (one report-polling timeout, unrelated to auth). No auth
error anywhere. So [[FU92-416]]'s pairing of Trade Desk with Viant does **not** currently hold.

Caveat: healthy ≠ has refresh logic. Connection `a73a6943…` has been unchanged for ~24 months. One
`connectiondescribe` on its `_ts` would settle whether it is on the same annual clock — the identical
five-minute check that would have prevented [[FU92-427]].

## Trade Desk + Viant — original investigation ticket ([[FU92-416]])

Both connectors use non-standard static credentials with undocumented lifespans. Investigation ticket [[FU92-416]] tracks determining whether these need automated refresh.

- **Trade Desk:** `TTD-Auth` header with Base64 token. 2 active templates. Connection `2aa7e056`.
- **Viant DSP:** Basic auth (Base64 of `user:pass`). 2 active templates. Connection `a73a6943`. Connector source explicitly notes: "It is not clear at this time what the life of this token will be."

## See Also

- [[bing-ads]] — Bing Ads connector documentation
- [[facebook-ads]] — Facebook long-lived token (~60 day expiry), operational status
- [[trade-desk]] — Trade Desk connector documentation
- [[FU92-415]] — Meta token refresh automation ticket
- [[FU92-416]] — Trade Desk + Viant auth investigation ticket
