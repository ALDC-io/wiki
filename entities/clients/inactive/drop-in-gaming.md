---
tags: [entity, client, drop-in-gaming, gaming]
aliases: [DROP_IN, Drop in Gaming, DROP_IN_GAMING]
sources: [Confluence CLIEN/1031110657, Confluence CLIEN/1035927561]
created: 2026-04-18
updated: 2026-04-18
---

# DROP_IN GAMING

Online gaming/tournament platform client. Discovery phase 2022-11.

## Account Details

| Field | Value |
|---|---|
| Short Code | DROP_IN |
| Contact | Sean Hurley |
| Discovery Meeting | 2022-11-08 |
| Attendees | Jason, Tanner, John, Karen |

## Data Sources

- **SQL Server:** Aurora MySQL (serverless, scales with load)
  - Tables: `www_dropingaming_com`, `www_dropingaming_gg`
  - Access: VPN/whitelisting + credentials required
  - Schema delivery: Sean Hurley to provide `information_schema` data

## Reporting Requirements

**Initial Report — User Stats:**

Anchor entity: User

User attributes: Legal Name, Account Username, Email, Registration date, First deposit date, Deposit amounts, Referral code, Total user count.

Tournament attributes (per user): Date/Time, Entry Fee, Game played, Results (place), Amount won, Last login.

Core analytics dimensions: Users, Referral codes, Tournaments, Tournament spend per user.

Note: Client prefers direct API/database connection over third-party aggregators (RIOT/BUYWARE).

## See Also

- [[client-onboarding-checklist]] — standard onboarding process
