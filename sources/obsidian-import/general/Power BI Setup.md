
Download PBI desktop - windows package manager.
SQL Server Managements Studio 22 - 




#power-bi #deployment 

Just want to record the general steps of deploying Changes to the Power BI model.
# Process
- Download the model from GitHub
    - Usually there will be folders for the date that the latest model was saved
- Open it with Power BI Desktop
- Set the environment details
    - This only needs to be done if you are publishing to prod as we keep the details set to test in the model files in GitHub.
    - Go to `Transform Data > Edit Parameters`
    - Update `CORE_API_URL` and `SNOWFLAKE_HOST` with the correct environment (see below)
- Refresh the data
- Save the model somewhere you can delete it easily
    - You have to save in order to publish
    - We want to make sure the saved models that we store in GitHub are always pointing to test
    - Do not publish this copy to GitHub with prod details
- Publish to the Power BI service
    - Make sure the file that you are publishing has the correct name
    - Select the right workspace and model for the client
        - On deploy you should get a warning about overwriting an existing model
        - Ensure that the model is the correct one again and proceed
- Go to the page for the deployed model in Power BI web
    - Check if the refresh has started
        - If it has not refresh it
        - This is a little tricky as some models take a very long time to refresh
            - If it is a small model maybe just refresh either way, but if when you log on the model is refreshing just leave it as it should be a refresh with the model you published
    - Select analyze in excel and check the pivot table to ensure that the published model matches your expectations

## Test Details
- `CORE_API_URL` -- [https://aldctestfnapcore1c01.azurewebsites.net](https://aldctestfnapcore1c01.azurewebsites.net)
- `SNOWFLAKE_HOST` -- og35375.canada-central.azure.snowflakecomputing.com
## Prod Details
- `CORE_API_URL` -- [https://aldcprodfnapcore1c01.azurewebsites.net](https://aldcprodfnapcore1c01.azurewebsites.net)
- `SNOWFLAKE_HOST` -- wj66376.canada-central.azure.snowflakecomputing.com