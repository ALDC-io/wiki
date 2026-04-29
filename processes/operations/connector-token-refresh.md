---
tags: [process, operations, connector, oauth, token-refresh, bing-ads]
aliases: [Connector Token Refresh, Bing Ads OAuth Token Regeneration]
sources: [Confluence CONN/1575747585, TECH/1777106945 (Steven Offboarding)]
created: 2026-04-18
updated: 2026-04-27
---

# Connector Token Refresh

Operational runbook for refreshing OAuth tokens across connectors. Currently documented for Microsoft Advertising (Bing Ads). Other connectors with token expiry: [[facebook-ads]] (60-day long-lived token).

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

## See Also

- [[bing-ads]] — Bing Ads connector documentation
- [[facebook-ads]] — Facebook long-lived token (~60 day expiry)
