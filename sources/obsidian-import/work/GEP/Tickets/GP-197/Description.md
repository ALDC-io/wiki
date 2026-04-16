The fact cost table for GEP filters order lines out so that we only apply fees to order lines that are sold through Amazon. This prevents allocating ad fees to marketplaces that are not part of the ad campaign.

However, when this was done we had only a few marketplaces and we hardcoded a list of them `('Amazon US', 'Amazon CA', 'Amazon Mexico')` for filtering. The difficulty with this is that over time GEP has added at least `Amazon UK` to their Amazon marketplaces and any products sold on that marketplace will not be included in the split of advertising fees.

This is an oversight on our part and should be altered to use a more consistent method of filtering the orders based on the marketplace. Potentially we should be able to match using `like ‘Amazon%’` to capture all Amazon Marketplaces, but we should confirm that this will work based of the current list of marketplaces etc.

