---
tags: [process, operations, client-management, deactivation]
aliases: [Client Deactivation, Deactivation Checklist]
sources: [Confluence CLIEN/1414594561]
created: 2026-04-18
updated: 2026-04-18
---

# Client Deactivation Checklist

Steps to deactivate a client account. Run these in both **Test** and **Production** unless otherwise noted.

## User Accounts (Postgres)

- [ ] Set all users for the account inactive: `UPDATE app_user SET is_active = false WHERE active_account_id = <id>;`
- [ ] Verify account ID is correct — wrong ID will affect ALL users on ALL accounts
- [ ] Confirm account IDs differ between Test and Production

```sql
SELECT * FROM app_account;
SELECT * FROM app_user WHERE app_user.active_account_id = 16;
UPDATE app_user SET is_active = false WHERE app_user.active_account_id = 16;
```

## Eclipse

- [ ] Delete `work/scan` and any additional tasks
- [ ] Update account document
- [ ] Set `scan` flag → FALSE
- [ ] Set `revenue` flag → FALSE
- [ ] Set billing status → DEACTIVATED
- [ ] Disable any account-specific automated emails (e.g. the Duer Executive Snapshot — see [[executive-snapshot-email]])

## Snowflake

- [ ] Disable all table caching tasks
- [ ] Revoke all data shares

## Credentials (Dashlane)

- [ ] Remove any client-shared login credentials

## Power BI / Excel

- [ ] Disable model refreshes
- [ ] Disable report refreshes
- [ ] In Microsoft 365 Admin Centre: delete active users → revokes licenses and removes from security groups

## Invoicing

- [ ] Enter a Stop Date on each monthly Service Item so recurring fees stop accruing

## Service Requests / Service Items

- [ ] Resolve all outstanding Service Items to Completed or Cancelled
- [ ] Resolve all outstanding Service Requests to Completed or Declined

## NextCloud

- [ ] Revoke client user access

## See Also

- [[client-invoicing]] — enter Stop Date on each monthly Service Item to halt recurring fees
- [[client-onboarding-checklist]] — counterpart for onboarding
- [[executive-snapshot-email]] — automated email that may need disabling
- [[nextcloud]] — NextCloud user management
- [[Power BI]] — model and report refresh management
