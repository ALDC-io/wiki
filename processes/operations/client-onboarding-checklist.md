---
tags: [process, operations, client-management, onboarding]
aliases: [Client Onboarding, Onboarding Checklist]
sources: [Confluence CLIEN/439025665]
created: 2026-04-18
updated: 2026-04-18
---

# Client Onboarding Checklist

Used during the onboarding phase for each new client. Copy and fill in for each client engagement.

## Knowledge Transfer from Sales

Required information to collect:

| Field | Details |
|---|---|
| Full Company Name | e.g. `Kit and Ace Technical Apparel Inc.` |
| Primary Contact | Name + email |
| Technical Contact | Name + email |
| Industry Type | e.g. `Retail Apparel` |
| Time Zone | HQ timezone |
| Invoice Day | Day of month for billing |
| Minimum Fee | Per contract |
| Contract Link | |
| Profitability Model link | |

## Technical Start-Up Details

| Field | Details |
|---|---|
| Tenant Location | e.g. `Canada` |
| Short Code | e.g. `DISH_DUER` |
| Account ID | CosmosDB account ID |
| Warehouse Provider | e.g. `Snowflake` |
| Reporting Provider | e.g. `Eclipse Dashboards, Power BI Embedded` |
| Client Repository | GitHub branch |
| Account Document | CosmosDB document ID |

Technical information needed:
- **Short Code** for the company (e.g. `KIT_ACE`)
- **Region** — storage-provider region code (e.g. `canada_east`)
- **Provider** — storage provider for client document details
- **Tier** — storage capacity size

## Documentation

### Initial Prioritization

| Aspect | Details |
|---|---|
| Client Stated Goal | |
| Elements to be viewed | |
| Data Locations | |

### Minimum Requirements

- Signed SaaS Contract (including SoW for Evaluation / Integration Phase)

### Eclipse Setup Tasks

- Account: users, groups
- Storage Account
- Capacity
- Tasks: `work/scan`, `schedule/zombies`, `session/zombies`

## Data Connections

For each data source, collect:

| Field | Details |
|---|---|
| Location | Cloud or On-Premise. On-prem: prefer SSH tunnel over VPN. Client must set up SSH receiver on their network. |
| Product / Service Name | e.g. NetSuite, SQL Server, Custom REST API, Oracle, Google Ads |
| Locator | IP address or service/account name |
| Credentials | Username/password, keyfile, API key, or service account |
| IP Whitelisting | If required, client whitelists ALDC IPs — see [[deployment-groups]] § Virtual Hosts for ALDC IP list (was CORE/800489527) |
| Access Testing | Confirm with client that credentials have been tested at required access level |
| Sources Required | Tables / views / endpoints needed for Eclipse onboarding |

## Onboard Schedule Tasks

- [ ] Build onboard schedule
- [ ] Review existing data warehouse, inventory items to migrate
- [ ] Review reports to be built/rebuilt and hosted by ALDC
- [ ] Identify and request required tokens / credentials
- [ ] Review current data usage; discuss optimizations and Tabular compromises
- [ ] If in contract: review suitability of Power BI Embedded vs. Azure Analysis Services
- [ ] Review total data size (current requirements only)
- [ ] Signoff on Evaluation SoW

## See Also

- [[client-invoicing]] — invoicing models and gate setup; configure on contract start
- [[client-deactivation]] — counterpart checklist at end of engagement
- [[client-vm-setup]] — if client needs a VM for model access
- [[client-communications]] — email templates for model access notification
- [[deployment-groups]] — ALDC IP addresses for client whitelisting
- [[eclipse]] — Eclipse setup (account, capacity, tasks)
- [[nextcloud]] — grant client NextCloud access if needed
