Ticket Link: https://analyticlabsdc.atlassian.net/browse/GP-169

## Description

[REQ-624](https://eclipse.aldc.io/service_request/45b2b20d-7890-4350-9164-8cb495852754/ "https://eclipse.aldc.io/service_request/45b2b20d-7890-4350-9164-8cb495852754/")

Currently, any measures coming from Marketing Activity fact do not have a relationship with Marketplace Name.

This is because Marketplace Name is based on a combo of Channel Name & Company Name & nothing we have access to from Sponsored Brands, Sponsored Products reports contain that info.

GEP can’t run the same marketing campaign across two marketplaces - they have to create two campaigns.

GEP to review how their campaigns are attributed to a channel (like [amazon.co](http://amazon.com/ "http://amazon.com")m or a[mazon.ca)](http://amazon.ca/ "http://amazon.ca")


*See comments - for notes related to design & implementation considerations*


## Ticket Information

- **Ticket**: GP-169 / DE-006 — Marketing Activity ↔ Marketplace attribution (REQ-624)
- **Branch**: feature/paulrussell/GP-169/establish-relationship-between-marketplace-names-and-marketing
- **Environment**: DEV only (client approval pending before PROD)
- **Stakeholder update (2026-02-27)**:
	- Justin confirmed Amazon profile IDs are one-to-one with country/currency (and therefore marketplace):
	- 2874274850477920 → US / USD
	- 410071870980733 → CA / CAD
	- 1359269695432602 → MX / MXN
	- 2944710254877284 → BR / BRL
	- Use profile_id to map Marketing Activity facts to the correct marketplace rather than inferring from channel/company.
- **Dependencies**:
	- Source tables: `TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_*` reports (Brands, Products, Display).
	- Warehouse target: `repos/clients/GEP/snowflake/warehouse/marketing_fct_activity.sql` (WAREHOUSE_SOURCE + WAREHOUSE views).
	- Marketplace dimension: `TEST_DG1_GEP.WAREHOUSE.SHARED_DIM_MARKETPLACE`.


