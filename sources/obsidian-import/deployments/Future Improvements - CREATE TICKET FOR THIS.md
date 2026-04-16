marketing_fct_activity.sql 
lots of files touched



## Potential changes:

**marketing_fct_activity.sql:**
- Naming convention marketing_fct_activity marketplace_id - Unknown string
	- Confirm if there is an unkown marketplace - does it exist how is it represneted
	- check share_dim_marketplace.sql
**sales_fct_cost.sql:**
- check db for amazon marketplace names
- Can we find a reason for ilike filter not being correct. (in a case where other marketplaces)

**traffic_fct_activity.sql:**
- exchange rate join logic 

**shared_dim_marketplace:**
- check share_dim_marketplace.sql - unknown marketplace

--------------------------------------------------

drop warehouse test paul in prod - maintenance

**Question about Biz report data being incorrect:**

review sku counts traffic_fct_activity
sku count - navac vs GEP as default vendor
Removing one would and allocating to one - will cause over-inflation of the sessions/views values
- because we are removing the sku splitting (down from asin)


Get testing stuff fixed. 
- so the above fix worked
- re-create the power bi pivot table in web power bi


double-check with Lori on monday about email - Fw: Question about Biz Report data being incorrect