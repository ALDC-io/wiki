---
tags: [entity, tool, connector, facebook, meta, marketing-api, oauth]
aliases: [Facebook Marketing API Connector, Meta Ads Connector, Facebook Ads Connector]
sources: [Confluence CONN/898695196, Confluence CONN/899645489]
created: 2026-04-18
updated: 2026-05-21
---

# Facebook Marketing API Connector

Eclipse connector for Facebook/Meta Marketing API. Uses long-lived OAuth access tokens obtained through a 5-step credential setup.

> **Prefect migration note:** This connector must be rebuilt as a Prefect flow. The 5-credential requirement (app_id, app_secret, ad_account_id, access_token, long_lived_access_token), the OAuth2 exchange process, and the Facebook Business SDK object hierarchy (AdAccount → Campaign → AdSet → Ad) are the reference spec for the Prefect implementation. Long-lived tokens expire ~60 days and need automated refresh logic.

## ALDC Account Credentials

- **Username**: support@aldc.io
- **Password**: `{{FB_SUPPORT_ACCOUNT_PASSWORD}}` — see `vault/infra-credentials.md` § Facebook Marketing API
- **Sandbox Access Token**: `{{FB_SANDBOX_ACCESS_TOKEN}}` — see `vault/infra-credentials.md` § Facebook Marketing API

## Object Hierarchy

```
Business Account
└── Ad Accounts  (identified as act_{ad_account_id})
    └── Campaigns
        └── Ad Sets
            └── Ads
```

**Edges** (relationship queries): Ad Account → Campaigns → AdSets → Ads  
**Endpoints**: `/owned_ad_accounts`, `/act_*/adsets`

## Credential Requirements

| Credential | Source |
|---|---|
| `app_id` | Meta for Developers → app dashboard |
| `app_secret` | Meta for Developers → Settings → Basic |
| `ad_account_id` | Ads Manager → left sidebar → Ad Account ID (without `act_` prefix) |
| `access_token` (temporary) | Graph API Explorer → Generate Access Token |
| `long_lived_access_token` | Exchanged via token endpoint (see setup) |

## Setup Process

### Step 1: Create App

1. Ensure your Facebook account has access to the target Facebook Business Account
2. Create a Meta Developer account at https://developers.facebook.com
3. Create a new Facebook App → get **app_id** and **app_secret** from Settings → Basic

### Step 2: Get Ad Account ID

1. Open Ads Manager → profile icon → select Business Account
2. Ad Account ID appears next to "Campaigns" dropdown

### Step 3: Assign App to Business

Ads Manager → hamburger menu → All tools → Business settings → Apps → Add → provide app_id

### Step 4: Generate Temporary Access Token

Meta for Developers → app dashboard → Tools → Graph API Explorer → Generate Access Token

### Step 5: Exchange for Long-Lived Token

```python
import requests

graph_api_version = "v12.0"
app_id = "<app_id>"
app_secret = "<app_secret>"
access_token = "<temporary_access_token>"

response = requests.get(
    f'https://graph.facebook.com/{graph_api_version}/oauth/access_token'
    f'?grant_type=fb_exchange_token'
    f'&client_id={app_id}'
    f'&client_secret={app_secret}'
    f'&fb_exchange_token={access_token}'
)
long_lived_token = response.json()['access_token']
```

## Facebook Business SDK

```bash
pip install facebook_business
```

```python
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

FacebookAdsApi.init(app_id=app_id, app_secret=app_secret, access_token=long_lived_token)
my_account = AdAccount(f'act_{ad_account_id}')
campaigns = my_account.get_campaigns()
```

## Operational Status (2026-05-21)

### Fusion92 — Two data paths

| Path | Connector | Accounts | Status |
|---|---|---|---|
| Windsor (`windsorai_v1`) | `ad_insights_windsor.json` | BCBSM x3 + ~20 others | **Active** — daily, current through today |
| Direct API (`facebook_business_v1`) | Per-account templates | RBA, CCCU, PCU | RBA active; CCCU/PCU set to **inactive** (no campaigns since Nov 2023) |

- **Windsor table:** `META.CURRENT_FACEBOOK_AD_INSIGHTS` — 1.9M rows, $1.2M May spend
- **Direct tables:** `META.CURRENT_AD_SET_{account}_AD_SET_INSIGHTS` — only RBA actively loading
- **Utility table:** `WAREHOUSE_UTILITY.ALL_META_AD_SET_INSIGHTS` unions both paths

### Token status

- **Windsor:** OAuth managed by Windsor.ai — no ALDC action needed
- **Direct API:** Long-lived token in Eclipse connection `1df7d48a` (`meta.json`) — **no auto-refresh, expires ~60 days**
- **Jira:** [[FU92-415]] — Token refresh automation ticket (precedent: [[FU92-246]] MS Ads refresh)

### Known issues

- April 2026 25-day loading gap ([[FU92-398]]) caused by Viant queue blockage disabling all Fusion schedules + expired token. Fully resolved, no data loss.
- CCCU and PCU accounts stopped running Meta campaigns in Nov 2023. Templates set to inactive 2026-05-21.

## Key Notes

- Long-lived tokens expire ~60 days — requires refresh logic in Prefect
- Ad Account IDs must use `act_` prefix in API calls
- Business SDK provides object-oriented access to the Graph API

## API References

- Campaign Structure: https://developers.facebook.com/docs/marketing-api/campaign-structure
- Access Tokens: https://developers.facebook.com/docs/facebook-login/access-tokens/#apptokens
- Token Refresh: https://developers.facebook.com/docs/facebook-login/access-tokens/refreshing
- Business SDK: https://developers.facebook.com/docs/business-sdk/getting-started/#python

## See Also

- [[eclipse]] — connector platform
- [[fusion92]] — primary client using Facebook Marketing API connector
- [[connector-development-standards]] — attribute hierarchy and parameter patterns
