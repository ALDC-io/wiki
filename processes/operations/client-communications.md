---
tags: [process, operations, client-management, communications, email-templates]
aliases: [Client Notifications, Outage Emails, Client Communications]
sources: [Confluence CLIEN/1260978177, Confluence CLIEN/1260584963, Confluence CLIEN/1027637253]
created: 2026-04-18
updated: 2026-04-18
---

# Client Communications

Standard email templates for consistent client-facing messaging. All support notifications should be sent from `support@aldc.io`.

## Outage / Maintenance Notification

Use when a production upgrade or maintenance window will cause a service interruption.

```
Subject: Production Upgrade: <Day Date> <Time> <TZ>

Good morning,

A production upgrade is scheduled to commence @ <time> <TZ> this afternoon.

Services will be temporarily unavailable while the upgrade is underway.

If you have any questions, please feel free to reach out.

Cheers,
<Name>
```

## Data Model Access Email

Sent to clients when they are granted access to a new PBI Excel model. Adjust `<ALDC_EMAIL>` and `<TEMP_PASSWORD>` per the credentials provisioned in Microsoft 365 — see [[Power BI]] § Granting Excel Model Access for the full provisioning procedure.

```
You should have already received a registration email to Eclipse (https://eclipse.aldc.io/).

After you've set up your password, when you log into Eclipse, you should be able to access 
the Data Model as an option on the left hand side of the screen.

Alternatively, you'll also be able to update/use a version of the model that has been 
shared to you by a colleague.

Once you click on the Data Model in Eclipse (or open a shared file), Excel will prompt you 
for a login. This login is separate from Eclipse — it relies on an account we've created 
for you within our tenant.

To access the Excel Model, use:
  Username: <ALDC_EMAIL>
  Password: <TEMP_PASSWORD>

You will need to use the Excel "profile" feature to switch between your existing O365 
tenant. On subsequent logins, ensure you are logged in with this account.

You will need to download the MS Authenticator app and set your password on first login.

Once the model is initially downloaded, it can be saved locally and will refresh with 
updated data when reopened.

Let us know if you run into any access issues.
```

## See Also

- [[Power BI]] § Granting Excel Model Access — provisioning the ALDC tenant credentials referenced above
- [[client-onboarding-checklist]] — broader onboarding process that triggers this email
- [[client-deactivation]] — includes revoking these access credentials
