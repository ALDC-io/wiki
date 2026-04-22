---
tags: [entity, tool, mailjet, email, notifications]
aliases: [Mailjet, Mailjet Email]
sources: [Confluence CORE/926285825]
created: 2026-04-18
updated: 2026-04-18
---

# Mailjet

Email delivery service used by [[core_api]] for operational notifications. Free plan: 6,000 emails/month.

## Account

- **Service URL:** https://app.mailjet.com
- **Email:** `mailjet@aldc.io`
- **Account password:** `vault/infra-credentials.md` § External services credentials
- **Plan:** Free (ALDC sub-account — NOT the master Analytic Labs account)

**Only `@aldc.io` domain is permitted as sender.** All outbound emails must use this domain.

## API credentials

Stored in `vault/infra-credentials.md` § External services credentials. Two key sets exist (Set 1 + Set 2); Set 1 is the primary ALDC sub-account.

Also available as env vars `MAILJET_KEY` / `MAILJET_SECRET` in [[core_api]] — see [[core_api]] § Environment Variables.

## Python integration

```python
from mailjet_rest import Client

mailjet = Client(auth=(api_key, api_secret), version='v3.1')

data = {
  'Messages': [{
    "From": {"Email": "mailjet@aldc.io", "Name": "ALDC"},
    "To": [{"Email": "recipient@aldc.io", "Name": "Recipient"}],
    "Subject": "Notification subject",
    "TextPart": "Plain text body",
    "HTMLPart": "<p>HTML body</p>"
  }]
}

result = mailjet.send.create(data=data)
```

## See Also

- [[core_api]] § Notification Module — Mailjet is an alternative to Twilio SMS / Pushover for email delivery
- `vault/infra-credentials.md` § External services credentials — API keys + account password
