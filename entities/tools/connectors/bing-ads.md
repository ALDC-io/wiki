---
tags: [entity, tool, connector, bing-ads, microsoft-advertising, oauth, azure]
aliases: [Bing Ads Connector, Microsoft Advertising Connector]
sources: [Confluence CONN/1132560386, Confluence CONN/1575747585]
created: 2026-04-18
updated: 2026-04-18
---

# Bing Ads (Microsoft Advertising) Connector

Eclipse connector for Microsoft Advertising (formerly Bing Ads). Uses Azure App Registration OAuth2 with organizational consent. Refresh tokens expire after 90 days — an automated daily refresh workflow is deployed in the Fusion function app.

> **Prefect migration note:** This connector must be rebuilt as a Prefect flow. The OAuth credential flow (Client ID, Client Secret, refresh token stored in CosmosDB connection document), the 90-day token expiry lifecycle, and the automated daily refresh pattern are the reference spec for the Prefect implementation. The existing automated refresh workflow is a strong candidate for a Prefect task.

## Credential Requirements

| Credential | Source |
|---|---|
| `client_id` | Azure Portal → App Registration overview |
| `client_secret` | Azure Portal → Certificates & secrets (copy immediately — not shown again) |
| `refresh_token` | OAuth consent flow → exchanged via PowerShell script |

**ALDC OAuth Client ID:** `98fe3659-b606-4550-9b16-c5e51a792618`

## Azure App Registration Setup

### Step 1: Create Registration

1. portal.azure.com → search "App Registration" → New Registration
2. Set name, account type; leave redirect URI blank
3. Click Register → copy **Client ID**

### Step 2: Configure Authentication

Authentication → Add a platform → Mobile and desktop applications → select `https://login.microsoftonline.com/common/oauth2/nativeclient` → Advanced settings → enable "Allow public client flows" → Save

### Step 3: Add API Permissions

API Permissions → Add a permission → APIs my organization uses → search "Microsoft ad" → select **Microsoft Advertising API Service** → add `ads.manage` and `msads.manage`

### Step 4: Create Client Secret

Certificates & secrets → New client secret → set 12-month expiry → Add → **copy value immediately**

## OAuth Consent Flow

Provide this authorization URL to the client (substituting client_id):

```
https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=98fe3659-b606-4550-9b16-c5e51a792618&response_type=code&redirect_uri=https://login.microsoftonline.com/common/oauth2/nativeclient&response_mode=query&scope=openid%20offline_access%20https%3A%2F%2Fads.microsoft.com%2Fmsads.manage&state=8675309
```

Client grants consent → browser redirects to a blank page → copy full URL → extract `code=` parameter.

## Token Exchange (PowerShell)

Client secret stored in Dashlane as **"Microsoft Ads Application - Eclipse Secret 2024-03-28"**.

```powershell
$clientId = "98fe3659-b606-4550-9b16-c5e51a792618"
$clientSecret = ""  # Insert from Dashlane

$code = Read-Host "Paste the full redirect URL here:"
$code = $code -match 'code=(.*)\&'; $code = $Matches[1]

$response = Invoke-WebRequest https://login.microsoftonline.com/common/oauth2/v2.0/token `
  -ContentType application/x-www-form-urlencoded -Method POST `
  -Body "client_id=$clientId&client_secret=$clientSecret&scope=https://ads.microsoft.com/msads.manage%20offline_access&code=$code&grant_type=authorization_code&redirect_uri=https%3A%2F%2Flogin.microsoftonline.com%2Fcommon%2Foauth2%2Fnativeclient"

$oauthTokens = ($response.Content | ConvertFrom-Json)
Write-Output "Refresh token: " $oauthTokens.refresh_token

# Confirm with a second refresh
$response = Invoke-WebRequest https://login.microsoftonline.com/common/oauth2/v2.0/token `
  -ContentType application/x-www-form-urlencoded -Method POST `
  -Body "client_id=$clientId&client_secret=$clientSecret&scope=https://ads.microsoft.com/msads.manage%20offline_access&grant_type=refresh_token&refresh_token=$($oauthTokens.refresh_token)"

$oauthTokens = ($response.Content | ConvertFrom-Json)
Write-Output "Final refresh token: " $oauthTokens.refresh_token
```

Store the **final** refresh token output in Dashlane as **"Fusion Microsoft Ads Refresh Token"**.

## Token Refresh Runbook

See [[connector-token-refresh]] for the full operational runbook including the automated daily refresh workflow and validation steps.

## Key Notes

- Refresh tokens expire 90 days after generation
- If client lacks permissions during consent, Azure AD prompts IT approval — use real-time comms (call/Teams chat) since the authorization code URL is short-lived
- Automated daily refresh runs at midnight via Fusion workflow function app

## API References

- Getting Started: https://learn.microsoft.com/en-us/advertising/guides/get-started?view=bingads-13
- FAQ & Authentication: https://learn.microsoft.com/en-us/advertising/guides/faq?view=bingads-13

## See Also

- [[connector-token-refresh]] — operational token refresh runbook
- [[eclipse]] — connector platform
- [[fusion92]] — primary client using Bing Ads connector
