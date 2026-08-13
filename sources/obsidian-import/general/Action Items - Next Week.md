SQL Server Setup - blocked

Amazon UK order ticket:
- All tables need to be refreshed in TEST.
- Then re-run cached tables.
- Use new creds - Steven gave me (They're in Dashlane - and below)
	- creds confirmed working
	- need to decide if we have to make a change to the connector or not.
	- cant use existing sellercentral connection
	- Create new connection/template in azure:
		- partner id will stay the same
		- amazon central - uk

```
Client identifier: amzn1.application-oa2-client.e0b209856c784971a5a77488193f4285  
Client secret: <REDACTED — Amazon LWA client_secret; see vault/infra-credentials.md § GEP/Navira Amazon Seller Central (SP-API) — Client Secret Rotation>  
Refresh token: <REDACTED — Amazon LWA refresh token; see vault/infra-credentials.md § GEP/Navira Amazon Ads — EU/UK Auth Refresh Token>
```


new company is added 
added a new csv for adding DTC_FEE to a specific marketplace
we can now quickly modify DTC_FEES and new companies 

Prod Deployment Checklist - deployment list