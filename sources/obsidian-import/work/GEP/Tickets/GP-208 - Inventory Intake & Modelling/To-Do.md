implement using warehosue column to filter by warehouse instead of full outer join
instead of missing record for no inventory - may have to ensure row exists and fill in the zero details. in case product stock out detection required day-by-day.

may not be able to bring date columns into the PBI Model 
- need research this.

current view runs task to populate historical inventory table.
run hourly to add to historical inventory table from view.



may need to individually calculate columns that create derived columns
- from looking at sample inventory csv


Do another pass and come up with a question what is the goal of this inventory?
the core functionality / goals.
- come up with different solutions or design solutions to ask user

Deep dive on inventory_fct_balance.sql 
-  replace full outer join with warehouse column
- check if net new columns can be found from any inv sources

FBA Manage Inventory - amazon report api we use currently.
Confirm the reports they are using - **Question for Client**

[https://developer-docs.amazon.com/sp-api/docs/welcome](https://developer-docs.amazon.com/sp-api/docs/welcome)



hard part here will be able get historical inventory in efficient way.
- add a task warehouse historical inventory
	- to insert current inv into a historical table/view ? potentially
	- need to think about idempotency/ failback/rollback
- add inventory snapshot do DATA_SHARE
	- This should have current inventory and historical inventory.




**extract_sales_detail - view:**
- missing fees
- re-write the view
- 




**Note:**
- First thing I can do is unhide inventory in PBI model and see how it  comes through and confirm correctness.
- going into sellercloud to see how the inv columns are calculated logically
- CUST-761 - old ticket with original requirements.

