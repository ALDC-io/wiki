---
tags: [process, operations, connector, oauth, token-refresh, bing-ads, meta, facebook]
aliases: [Connector Token Refresh, Bing Ads OAuth Token Regeneration]
sources: [Confluence CONN/1575747585, TECH/1777106945 (Steven Offboarding)]
created: 2026-04-18
updated: 2026-05-21
---

# Connector Token Refresh

Operational runbook for refreshing OAuth tokens across connectors. Full audit completed 2026-05-21.

## Token Refresh Audit (2026-05-21)

| Connector | Client | Auth Type | Expiry | Auto-Refresh | Status |
|---|---|---|---|---|---|
| `microsoft_bing_ads_v1` | Fusion92 | OAuth refresh_token | 90 days | Daily workflow (07:00 UTC) | Covered |
| `facebook_business_v1` | Fusion92 | Long-lived access_token | ~60 days | Daily workflow (08:00 UTC) | Covered ([[FU92-415]]) |
| `amazon_ads_v1` | Fusion92, GEP | OAuth refresh_token | Long-lived | Connector auto-exchanges | Low risk |
| `amazon_sellercentral_v1` | GEP | OAuth refresh_token | Long-lived | Connector auto-exchanges | Low risk |
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

## Trade Desk + Viant — Unknown Lifespan ([[FU92-416]])

Both connectors use non-standard static credentials with undocumented lifespans. Investigation ticket [[FU92-416]] tracks determining whether these need automated refresh.

- **Trade Desk:** `TTD-Auth` header with Base64 token. 2 active templates. Connection `2aa7e056`.
- **Viant DSP:** Basic auth (Base64 of `user:pass`). 2 active templates. Connection `a73a6943`. Connector source explicitly notes: "It is not clear at this time what the life of this token will be."

## See Also

- [[bing-ads]] — Bing Ads connector documentation
- [[facebook-ads]] — Facebook long-lived token (~60 day expiry), operational status
- [[trade-desk]] — Trade Desk connector documentation
- [[FU92-415]] — Meta token refresh automation ticket
- [[FU92-416]] — Trade Desk + Viant auth investigation ticket
