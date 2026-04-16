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
Client secret: amzn1.oa2-cs.v1.7f5e361ec0ce9308c4f5759f5ad59dee03a18cacfca9de910f295edb88cc5343  
Refresh token: Atzr|IwEBIBZRztpw7uQI92XQAttJBJ3Axr759LMdEEJThAUS03N7634hSu4KMlQW9o8yQ2su059K8HU7BvJfLiYii_ewv75yw1qx8tkpMAHeyawj34M7g9a4w0CDgcEXUYzvJo-f2WoF1-H7flOiaRtv-kjyla_TfV2HS4-3CZZHLXujBKjLIWLmL8ndydNh9UgXG2t2UUMiiGmzMUskDeP8xPYqHvdnEae-Iz3-qbtOSMyvvukbVw9zm2b0uBCGKT2tXxgRpUyBFF_RiORudBKQQup5U2w0NizVFa2P7DY9z4l0RSwfOqa9QTNecm_iUKNIn_-4At8
```


new company is added 
added a new csv for adding DTC_FEE to a specific marketplace
we can now quickly modify DTC_FEES and new companies 

Prod Deployment Checklist - deployment list