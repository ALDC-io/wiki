---
tags: [process, operations, power-bi, azure, secrets]
aliases: [Power BI Secret Refresh, PBI Secret Rotation]
sources: [Confluence CORE/1468104706]
created: 2026-04-18
updated: 2026-04-18
---

# Power BI Registration Secret Refresh

Operational procedure for refreshing Power BI client registration secrets in Azure AD and updating them in Django admin. A monthly reminder is maintained in the ALDC support Outlook calendar to check for expiring secrets.

## Current secret expiry dates

| Account | Expiry | Status |
|---|---|---|
| Power BI Registration DISH_DUER | 2025-07-25 | Active |
| Power BI Registration FUSION92 | 2025-07-25 | Active |
| Power BI Registration GEP | 2025-09-10 | Active |
| Power BI Registration KIT_ACE | 2025-07-25 | Active |

> Update this table after each refresh.

## Refresh procedure

### Phase 1: Generate new secret in Azure

1. Azure Portal → **App Registrations** → **All Applications** → search `Power BI`
2. Select the registration for the account to refresh
3. **Client Credentials** → review current secret expiry
4. If expiring within 30 days: **New client secret** → name it incrementally (e.g., `secret-3`) → set expiry **6 months** → **Add**
5. **Copy the secret Value immediately** — masked after page refresh
6. Do NOT navigate away until the secret is copied to all Django environments

Key points:
- Multiple secrets may exist; typically the bottom-most is active
- Secret value is masked except first 3 digits after creation
- If **New client secret** is greyed out: you lack permissions — contact a senior developer

### Phase 2: Update Django admin

For each environment (Test then Prod):

| Env | URL | Login |
|---|---|---|
| Test | `https://eclipse-test.aldc.io/aldc_admin/` | `super@aldc.io` |
| Prod | `https://eclipse.aldc.io/aldc_admin/` | Personal ALDC account |

> **Note:** Trailing `/` on the URL is required.

1. Open Django admin → **Accounts** → select the client account
2. Locate **Power bi client secret** field → replace with new secret value
3. **Save**
4. Repeat for all environments before moving to the next account (avoid losing access to the secret)

### Phase 3: Maintenance

- Update the expiry table above after each refresh
- Verify monthly Outlook reminder is scheduled in ALDC support calendar

## Troubleshooting

| Problem | Fix |
|---|---|
| Accidentally refreshed Azure page before copying secret | Delete incomplete secret, create a new one |
| Unsure which secret is active | Compare first 3 visible digits to current Django value |
| Permission denied in Azure | Request IAM access from a team member |

## See Also

- [[core_api]] — Datasets API uses capacity provider / capacity CosmosDB docs with PBI service client secrets
- [[deployment-groups]] — per-env Django admin URLs
- [[azure-environment-bootstrap]] — app registration setup
