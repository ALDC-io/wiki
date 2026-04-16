### Project init prompt:

ai new-project "PRE-000 Prefect connector migration" $'Ticket: Convert the CSV connector to Prefect-compatible Nextcloud ingest, then repeat for every legacy connector.\n\nContext:\n- Repo: repos/connector\n- Legacy connectors live under connector/connectors/*.py (BaseConnector-based)\n- Prefect-style reference: connector/accounts/ALDC_QA/deployments/exchange_rates.py (senior dev example)\n- Nextcloud REST references: docs/references/file_handler.md, docs/references/client.md, docs/references/file_specification.md (copied from DIOS repo)\n\nAcceptance criteria:\n1. First feature: replace flatcsv.py with a \"Nextcloud\" connector that hits the Nextcloud REST API (not local files), while preserving all current encoding/BOM handling logic from FlatCsv/BaseConnectorFlat.\n2. Every migrated connector must produce Prefect flows/blocks identical to the reference implementation (register via Account.register_flow, honor MergeScheme + PartitionScheme, reuse block IDs).\n3. Capture shared migration steps/prompts so the remaining 20–30 connectors follow the same template.\n\nConnectors to plan (one feature per connector, unless it makes sense to group):\n- alphavantage.py\n- amazon_ads.py\n- amazon_sellercentral.py\n- athena_s3.py\n- azure_metrics.py\n- cosmosdb.py\n- dor.py\n- esri_shapefile.py\n- exchangeratesapi.py\n- facebook_business.py\n- feedtherobot.py\n- firebase.py\n- flatcsv.py (becomes nextcloud_connector)\n- googleanalytics.py\n- google_maps.py\n- hubspot.py\n- jira.py\n- microsoft_bing_ads.py\n- mongodb.py\n- mysql.py\n- nasa_worldview.py\n- netsuite_analytics.py\n- netsuite_connect.py\n- newsapiorg.py\n- nutshell.py\n- opendatasoft.py\n- openweathermap.py\n- phoneburner.py\n- postgresql.py\n- redshift.py\n- restcountrieseu.py\n- s3.py\n- scrape_loblaw.py\n- scrape_shopify_v1.py\n- scrape_shoppersdrugmart.py\n- scrape_wunderground_v1.py\n- seller_cloud.py\n- shopify_conn.py\n- smartsheet.py\n- snowflake.py\n- sqlserver.py\n- tomtom.py\n- trade_desk_my_reports.py\n- tsheets.py\n- twitter.py\n- viant_dsp_reporting.py\n- windsorai.py\n\nFocus deliverables:\n- Feature stubs in features/<slug/>.md capturing requirements + blockers for each connector.\n- Highlight the CSV→Nextcloud feature as highest priority.\n- Call out shared risks (Nextcloud auth, encoding parity, Prefect deployment scaffolding) that affect every connector.'



## Integrate ai-dev-flow


ai new-project generate feature stubs for all the connectors:

● The workflow is complete. The next step is to run each feature through its own detailed planning cycle, in dependency
  order:

  1. ai feature "nextcloud-csv"           ← start here; establishes Nextcloud auth + Prefect pattern
  2. ai feature "migration-scaffold"      ← extract the template from what nextcloud-csv produces
  3. ai feature "financial-connectors"    ← lowest risk; closest to the exchange_rates.py reference
  4. ai feature "sql-connectors"
  5. ai feature "aws-connectors"
  6. ai feature "nosql-connectors"
  7. ai feature "netsuite-connectors"
  8. ai feature "ecommerce-connectors"
  9. ai feature "crm-connectors"
  10. ai feature "ad-platform-connectors"
  11. ai feature "analytics-platform-connectors"
  12. ai feature "geo-weather-connectors"
  13. ai feature "scrape-connectors"
  14. ai feature "misc-api-connectors"    ← resolve dor/feedtherobot questions first



# Grilling questions

  **Question:** 
  Should NextcloudCsvConnection use the same basic-auth approach (host, user, password) as the existing
  NextcloudFileHandler, or do you need app-token or OAuth2 support?
**Decision:**
- sticking with same approach for now



--
  The existing NextcloudFileHandler.list_files() returns files in a directory, but there's no read_file() /
  get_file_contents() method on it — only write_file() and list_files(). The nextcloud library does have a
  get_file_contents() method on the client.

  My recommendation: the connector calls nextcloud_client.get_file_contents(path) directly (returning bytes), decodes to
  string, and feeds it to csv.DictReader via io.StringIO — no changes to NextcloudFileHandler.

  Question: Should the connector read file contents directly via the nextcloud library client (not through
  NextcloudFileHandler), or do you want NextcloudFileHandler extended with a read_file() method first?

**Reasoning:**
NextcloudFileHandler is a write/move/delete handler — its job is managing file lifecycle for output operations (uploading
  results, organizing directories). Reading CSV source data is a different responsibility. Mixing it in would violate
  single-responsibility and make NextcloudFileHandler harder to reason about.



**● Question 5 of ~8**

  Looking at the exchange_rates.py deployment, it uses PartitionSchemeDateExact — meaning each run targets a specific date
  partition and data is keyed by date. CSV files from Nextcloud don't inherently have a date dimension; they're static
  snapshots that get replaced or updated.

  My recommendation: use PartitionSchemeFull for the reference deployment — a full replace on each run, no date windowing.
  This is the simplest correct default for file-based sources where the file IS the dataset.

  Question: Should the reference deployment use PartitionSchemeFull (full replace each run), or does your Nextcloud CSV use
  case require date-based partitioning?







# Running the connector
```
/Client_Tenants/ALDC_QA/TEST_FILES/MARKETPLACE_NAME_TEST/MARKETPLACE_NAME_prefect_test_file.csv
```

fa$tR0cket$!


save_block.py
temp script to run once before start prefect and running nextcloud connector

```python
import asyncio

from connector.connectors.nextcloudcsv import NextcloudCsvConnection

  
  

async def save_block():

    conn = NextcloudCsvConnection(

        host="cloud.aldc.io",

        user="paul.russell@aldc.io",

        password="fa$tR0cket$!",

        path="/Client_Tenants/ALDC_QA/TEST_FILES/MARKETPLACE_NAME_TEST/MARKETPLACE_NAME_prefect_test_file.csv",

    )

    await conn.save("nextcloud-csv-aldc-qa", overwrite=True)

  
  

asyncio.run(save_block())
```


  set NEXTCLOUD_HOST='cloud.aldc.io'
  set NEXTCLOUD_USER='paul.russell@aldc.io'
  set NEXTCLOUD_PASSWORD='fa$tR0cket$!'
  set NEXTCLOUD_TEST_CSV_PATH='/Client_Tenants/ALDC_QA/TEST_FILES/MARKETPLACE_NAME_TEST/MARKETPLACE_NAME_prefect_test_file.csv'


CSV columns:
```csv
MARKETPLACE_NAME,CHANNEL_NAME,COMPANY_NAME,NOTES,APPLY_DISCOUNT_TO_NET,DTC_FEE_RATE
```




Test runner command:
PYTHONPATH=. .venv/Scripts/python tests/test_connectors/nextcloudcsv.py


issue fix:

❯ it seems to be adding prefix to my path - [debug] path='C:/Program Files/Git/Client_Tenants/ALDC_QA/TEST_FILES/MARKETPLACE_NAME_TEST/MARKETPLACE_NAME_prefect_test_file.csv' is_directory=False

● Git Bash is converting the leading / to C:/Program Files/Git/. It's a known MSYS2 path translation issue. Prefix the command with MSYS_NO_PATHCONV=1 to disable it:

  MSYS_NO_PATHCONV=1 PYTHONPATH=. .venv/Scripts/python -m tests.test_connectors.nextcloudcsv