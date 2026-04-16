

Applied the following changes:

1. **Case-insensitive discount flag**
    
    sqlCopyCopied!
    
    ```sql
    (LOWER(COALESCE(APPLY_DISCOUNT_TO_NET, '')) = 'yes') :: BOOLEAN AS APPLY_DISCOUNT_TO_NET_FLAG
    ```
    
    So “yes/Yes/YES” (or any cased variant) will flip the flag; blanks/nulls evaluate to FALSE.
    
2. **Flexible DTC fee parsing**
    
    - In the subselect I parse the raw CSV string once:
        
        
        ```sql
        TRY_TO_NUMBER(REGEXP_REPLACE(DTC_FEE_RATE, '[^0-9\.-]', '')) AS DTC_FEE_RATE_NUM
        ```
        
        (the regex strips out `%`, spaces, etc.)
    - The exposed column normalizes it to a proportion: values ≥ 1 (e.g., `3`, `3%`) are divided by 100, values between 0 and 1 are left as-is, and NULL/garbage defaults to 0.
        
        
        ```sql
        COALESCE(IFF(DTC_FEE_RATE_NUM >= 1, DTC_FEE_RATE_NUM / 100, DTC_FEE_RATE_NUM), 0) AS DTC_FEE_RATE_PCT
        ```






create a testing template - so we don't impact the connection that is currently in use

make csv in ALDC QA - test_files
copy marketplace_name folder into the folder above - put new csv file in this folder for testing

needs to be done in prod - so new file and folder should be created

create a connection - supplement marketplace name - rename slightly
- create new one in azure
- prodcsdbcsdb1c01 - go here
- data explorer
- work_connection, work_template
	- click items - will get all connections
	- Copy id from eclipse and find id 
- copy connection details - without id


change path to new marketplace csv 


**Other notes:**
Do folder copy and file adjusting first
then go to azure to create the template
new item in work_template and in work_connection


**PR change:**
for amazon is marketplace filtering
if amazon orders come through do their orders map to advertising map to amazon uk.

