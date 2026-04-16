Here’s the structured plan for porting the CSV connector into the Prefect pattern (plus the Claude-ready scaffolding).

---

### 1. Current state (what Claude needs to know)

| Area                   | Details                                                                                                                                                                                                               | Files                                                                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Legacy connector logic | `connector/connectors/flatcsv.py` + `connector/base/base_connector_flat.py` implement CSV ingestion with dict-style `options`/`connection`. Not registered with `ConnectorRegistry`, so Prefect never sees it.        | `connector/connectors/flatcsv.py`, `connector/base/base_connector_flat.py`                                                    |
| Prefect bootstrap      | `main.py → DeploymentRunner.serve_local()` registers block schemas (via `ConnectorConnectionBase.register_type_and_schema`) then serves every deployment discovered under `connector/accounts/<account>/deployments`. | `connector/deployment_runner.py`, `connector/accounts/account.py`, `connector/accounts/ALDC_QA/deployments/exchange_rates.py` |
| Outputs                | `BaseConnector.add_response()` handles parquet write, blob upload, Snowflake staging/merge once `run_workflow()` is called from a Prefect flow. Any new connector just needs to return pandas data + metadata.        | `connector/base/base_connector.py`                                                                                            |

Key implication: to Prefect-ize CSV we must (1) wrap the legacy logic in a typed `BaseConnector[...]` subclass, (2) expose a Prefect flow per account, (3) define any connection blocks/options to feed file paths, delimiters, etc.


***Challenge: Should we wrap legacy logic - or would it be better to just re-write with improved logic?***


**Terence's answer:**

For now we should wrap it, not rewrite it. The legacy `FlatCsv` path has a lot of quirky behavior (directory walks, BOM stripping, schema validation, rest‑field handling, ad‑hoc datatype casting) that was added because real customer files were messy. Recreating all of that from scratch without exhaustive fixtures is a great way to break silent edge cases—and we can’t afford to stall the Prefect migration waiting on a full reimplementation.



---

### 2. Migration plan (phases & milestones)

| Phase                                        | Goal                                                               | Concrete Tasks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Primary Files                                                                                                                  |
| -------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **0. Discovery / Config Inventory**          | Capture how CSV sources are configured today.                      | • Identify every account/source that currently instantiates `FlatCsv` (likely via metadata tables or config files outside this repo). <br>• For each, record file location/pattern, delimiter, header flag, required columns, PK, `rest_field` usage, schedule expectations.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Notes (e.g. `notes/projects/PRE-000/discovery.md`)                                                                             |
| **1. Typed Connector (code prep)**           | Re-implement CSV connector as a Prefect-friendly class.            | • Introduce `FlatCsvConnection(ConnectorConnectionBase)` with fields: `location: str`, `file_type: Literal["csv"]` (default), `contains_header: bool`, `delimiter: str = ","`, `quotechar: str = '"'`, maybe `encoding`. <br>• Introduce `FlatCsvField(CamelCaseBaseModel)` (name, datatype enum). <br>• Introduce `FlatCsvOptions(ConnectorOptionsBase)` with: `primary_key: list[str]`, `fields: list[FlatCsvField]`, `rest_field: bool = False`. <br>• Create `FlatCsvConnector(BaseConnector[FlatCsvConnection, FlatCsvOptions])`. Port logic from `BaseConnectorFlat`/`FlatCsv.run`, but keep helpers as private methods. Ensure `run()` accepts `ConnectorRunOptionsEmpty`. <br>• Register connection schema via `ConnectorRegistry` automatically (happens when subclassing `BaseConnector[...]`). | `connector/connectors/flatcsv.py` (rewrite), optionally `connector/base/base_connector_flat.py` (deprecate helpers or inline). |
| **2. Prefect Flow & Deployment per account** | Wire the connector into Prefect for ALDC_QA (template for others). | • Add `connector/accounts/ALDC_QA/deployments/flat_csv.py` (name TBD per data set). Flow skeleton should match ExchangeRates pattern: load connection block (`FlatCsvConnection.aload(account.build_block_id("flat-csv-<slug>"))`), instantiate connector with options from code or block, call `run_workflow()` with `PartitionSchemeFull` (likely) + `MergeScheme` (Insert vs Merge). <br>• Update `ALDC_QA` account metadata if multiple CSV jobs are required (one flow per dataset). <br>• Document block naming convention (e.g. `flat-csv-source-a`).                                                                                                                                                                                                                                              | New deployment file(s).                                                                                                        |
| **3. Block + Secrets Plan**                  | Ensure Prefect has the config needed at runtime.                   | • Decide whether CSV file locations live on disk, S3, or Azure—if local paths, add instructions for operators to mount network shares and create Prefect blocks storing `location` and file settings. <br>• Provide a script/CLI snippet to create the new connection blocks (similar to `setup_account_blocks`). Possibly add helper under `scripts/` to seed connection blocks from YAML.                                                                                                                                                                                                                                                                                                                                                                                                               | `notes/projects/PRE-000/design.md`, maybe new script.                                                                          |
| **4. Tests & QA**                            | Guard the new connector.                                           | • Unit tests for `FlatCsvConnector.run()` covering: single file ingest, directory traversal, `rest_field` flag, datatype casting. (Use temp files via `tmp_path`.) <br>• Integration-ish test that runs `connector.accounts.ALDC_QA.deployments.flat_csv.exchange_flow()` via Prefect’s testing utilities (with small fixture files). <br>• Verify `prefect deployment ls` shows the new deployment and `prefect deployment run ... --params` executes end-to-end (with dry-run storage handler stub or by pointing at a tmp directory).                                                                                                                                                                                                                                                                  | `tests/connectors/test_flat_csv.py` (new), maybe `tests/accounts/test_flat_csv_flow.py`.                                       |
| **5. Rollout to other connectors**           | Reuse the template.                                                | • Once the CSV pattern works, repeat for other legacy connectors (e.g., `smartsheet`, `hubspot`, etc.) by following the same typed-connector + deployment recipe. Capture sequencing + dependencies in PRE-000 notes so Claude can pick them off sequentially.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Notes planning doc.                                                                                                            |

---

### 3. Claude implementation packets

For each coding phase, prep a short “packet” containing: scope statement, relevant paths, acceptance criteria, and run commands. Example for Phase 1:

```
Goal: Rebuild the legacy FlatCsv connector as a Prefect-ready BaseConnector subclass with typed connection/options.

Files to edit:
- connector/connectors/flatcsv.py (introduce FlatCsvConnection, FlatCsvOptions, FlatCsvConnector)
- connector/base/base_connector_flat.py (remove unused logic or convert helpers into static methods on the new class if needed)

Key requirements:
1. FlatCsvConnection extends ConnectorConnectionBase and defines location, file_type ("csv"), contains_header, delimiter, quotechar, optional encoding.
2. FlatCsvOptions extends ConnectorOptionsBase and adds:
   - fields: list[FlatCsvField] where FlatCsvField(name: str, datatype: Literal["str","int","float","datetime"])
   - primary_key: list[str]
   - rest_field: bool = False
3. FlatCsvConnector(BaseConnector[FlatCsvConnection, FlatCsvOptions]) implements run(run_options: ConnectorRunOptions) using the legacy logic:
   - Support reading a directory of CSV files or a single file.
   - Preserve schema validation, datatype casting, and rest_field handling.
   - Always add FILEPATH column at end, uppercase column names before add_response.
4. run() only supports ConnectorRunOptionsEmpty; raise ValueError otherwise.
5. Tests pending (Phase 4), but keep the code testable by isolating file IO (e.g., helper methods that accept a Path).

How to validate:
- poetry/venv: `source .venv/Scripts/activate`
- `python -m pytest tests -k flat_csv` (will be added later; for now run mypy/ruff if configured)
- `python main.py serve-local` should still register ExchangeRates (CSV flow added later).
```

For Phase 2 (flow/deployment) the packet should include:

```
Goal: Add a Prefect deployment for the CSV connector under ALDC_QA.

Files:
- new: connector/accounts/ALDC_QA/deployments/flat_csv.py

Steps:
1. Define account = ALDC_QA_ACCOUNT.
2. Decorate async flow with @account.register_flow(name="<Friendly Name>").
3. Load connection block id via account.build_block_id("flat-csv-<slug>").
4. Instantiate FlatCsvConnector(topic="<TOPIC>", category="<CATEGORY>", options=FlatCsvOptions(...)).
5. Call await connector.run_workflow(...) with MergeScheme/MergeStrategy (probably Insert) and PartitionSchemeFull(field="N/A", ...).
6. Ensure __init__.py auto-discovers the new deployment (no change if file is under deployments/).

Validation:
- `python main.py serve-local`
- Prefect UI should list the new deployment.

Open questions for Paul:
- What topic/category/table names should the CSV flow use?
- What schedule/partition scheme is desired (full refresh vs incremental)?
```

You can clone/adjust that template for Phase 4 (tests) and any future connectors—just swap filenames and acceptance criteria.

---

### 4. Next actions

1. I’ll start a PRE-000 notes stack (`notes/projects/PRE-000/{discovery,design}.md`) capturing the plan + open questions so we don’t lose it.
2. Once you confirm the CSV source details (file path, PK, cadence), we can flesh out the exact options/merge scheme and craft the Phase 1 Claude prompt with real values.
3. After Claude lands Phase 1, we’ll iterate through the remaining phases, reusing the template for additional connectors.

Let me know any specifics about the CSV feed (location, schema, refresh cadence) so I can plug them into the design + prompts.


