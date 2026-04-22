---
tags: [concept, pattern, python, google, oauth, auth, ads]
aliases: [Google OAuth Python, Google Ads OAuth, google-auth-oauthlib usage]
sources: [Confluence TECH/1145143297 (Google OAuth python code, obtain and use tokens)]
created: 2026-04-17
updated: 2026-04-17
---

# Google OAuth in Python

Pattern for obtaining and using Google OAuth tokens in Python, used across ALDC Google-adjacent [[Eclipse]] connectors (Google Ads, Google Analytics, Campaign Manager, DV360, Search Ads, etc). Based on the `google-auth-oauthlib` and `google-ads` libraries.

> **Credentials note**: actual `developer_token`, `customer_id`, `client_secret.json`, and `redirect_uri` values belong in Dashlane / the gitignored `vault/`. Code samples below use placeholders.

## 1. Obtain tokens from a user

Generate an authorization URL the user visits. After they approve, Google redirects back to your redirect URI with the tokens embedded in the query string.

```python
import google.oauth2.credentials
import google_auth_oauthlib.flow

flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    'client_secret.json',                                # downloaded from Google Cloud credentials
    scopes=['https://www.googleapis.com/auth/adwords'],  # scope(s) your app needs
)

flow.redirect_uri = "{{REDIRECT_URL}}"

AUTHORIZATION_URL, state = flow.authorization_url(
    access_type='offline',          # offline → issues a refresh_token
    include_granted_scopes='true',
)

# Send the user to AUTHORIZATION_URL. After they approve, Google redirects to REDIRECT_URL.
```

## 2. Exchange the redirect for tokens

After the redirect, the full response URL contains the authorization code. Pass it to `flow.fetch_token` to exchange for an access token + refresh token.

```python
flow.fetch_token(authorization_response="{{URL_FROM_STEP_1_AFTER_LOGIN}}")
credentials = flow.credentials

credentials.token          # short-lived access token
credentials.refresh_token  # long-lived — use this for automated re-auth
```

Store `refresh_token` securely (Dashlane / vault / an encrypted store). The access token auto-refreshes when needed.

## 3. Use the tokens against a Google API

Example: Google Ads. Build a `Credentials` object from the stored tokens and hand it to the Google Ads client.

```python
from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.credentials import Credentials

# `token` and `refresh_token` retrieved from your vault / store
credentials = Credentials(token=token, refresh_token=refresh_token)

client = GoogleAdsClient(
    developer_token="{{GOOGLE_ADS_DEVELOPER_TOKEN}}",  # from Dashlane
    credentials=credentials,
)
ga_service = client.get_service("GoogleAdsService")

customer_id = "{{GOOGLE_ADS_CUSTOMER_ID}}"  # from Dashlane / client config

query = """
    SELECT
        campaign.id,
        campaign.name
    FROM campaign
    ORDER BY campaign.id
"""

stream = ga_service.search_stream(customer_id=customer_id, query=query)
```

## See Also

- [[Eclipse]] — Google connectors use this pattern (ads, GA, CM, DV360, Search Ads)
- [[fusion92]] — primary consumer of Google-Ads-based Eclipse templates
- [[python-development-standards]] — general Python conventions
- `vault/credentials.md` — where the actual tokens live
