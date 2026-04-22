---
tags: [entity, tool, connector, google-ads, oauth, google-cloud]
aliases: [Google Ads Connector]
sources: [Confluence CONN/1134100481]
created: 2026-04-18
updated: 2026-04-18
---

# Google Ads Connector

Eclipse connector for Google Ads API. Requires four credentials: Developer Token, OAuth Client ID, OAuth Client Secret, and OAuth Refresh Token.

> **Prefect migration note:** This connector must be rebuilt as a Prefect flow. The four-credential model (Developer Token + OAuth Client ID + Secret + Refresh Token) and the OAuth2 Playground token generation flow are the reference spec. Note: the Developer Token requires a formal application and approval process — allow 1-2 weeks for Basic Access approval.

## Credential Requirements

| Credential | Source |
|---|---|
| Developer Token | Google Ads account (Manager role) → apply via API console |
| OAuth Client ID | Google Cloud Console → Credentials |
| OAuth Client Secret | Google Cloud Console → Credentials |
| OAuth Refresh Token | OAuth2 Playground token exchange |

## Setup Process

### Step 1: Developer Token

1. Log in to Google Ads account (requires Manager role or equivalent)
2. Follow: https://developers.google.com/google-ads/api/docs/get-started/dev-token
3. Initial: **Test Token** (test environment only)
4. Apply for **Basic Access** — requires a reference design document
5. Production timeline: ~1-2 weeks for approval

### Step 2: Google Cloud Console

1. console.cloud.google.com → create/select project
2. Search "Google Ads API" → Enable
3. APIs & Services → OAuth consent screen → select **Internal** (or External if needed) → configure app name + support email

### Step 3: Create OAuth Client ID

APIs & Services → Credentials → Create Credentials → OAuth Client ID → **Desktop Application** → set `http://127.0.0.1` as Authorized JavaScript Origins → save.

### Step 4: Obtain Refresh Token (OAuth2 Playground)

1. Visit https://developers.google.com/oauthplayground
2. Enter Client ID and Client Secret from Step 3
3. Click **Authorize APIs** → log in → grant access
4. Click **Exchange Authorization Code for Tokens**
5. Copy the **Refresh Token**

## Verification Checklist

- [ ] Developer Token
- [ ] OAuth Client ID
- [ ] OAuth Client Secret
- [ ] OAuth Refresh Token

## References

- Developer Token Guide: https://developers.google.com/google-ads/api/docs/get-started/dev-token
- OAuth Cloud Project Setup: https://developers.google.com/google-ads/api/docs/get-started/oauth-cloud-project
- OAuth2 Playground: https://developers.google.com/oauthplayground

## See Also

- [[eclipse]] — connector platform
- [[fusion92]] — primary client using Google Ads connector
- [[connector-development-standards]] — attribute hierarchy and parameter patterns
