---
tags: [process, deployment, azure, bootstrap, infrastructure, powershell]
aliases: [Complete Environment Deployment, Azure Environment Bootstrap, end-to-end deployment, deployment.ps1]
sources: [Confluence INFRA/959086593 (Complete Environment Deployment end-to-end), CORE/891813889 (Creating app registration for Core)]
created: 2026-04-17
updated: 2026-04-18
---

# Azure Environment Bootstrap (end-to-end)

End-to-end runbook for standing up a new [[Azure]] environment for ALDC: subscription → Function App → Portal web app → first client + agent. Based on Powershell scripts in the `Infrastructure` GitHub repo. Sourced from a 2022 Confluence walkthrough; some steps may have drifted — confirm against the current Infrastructure repo before running.

> **Scope**: this is for bringing up a whole new ALDC subscription / deployment group. For onboarding a client into an existing environment, use [[new-client-setup]]. For ongoing web-app deploys, see [[eclipse-azure-deployment]].

> **Credentials**: redacted placeholders below point at `vault/infra-credentials.md` (gitignored). Fill them in from there.

## Prerequisites

- Access to the `Infrastructure` Powershell repo on GitHub
- Azure Powershell module:
  ```powershell
  Install-Module -Name Az -Scope CurrentUser -Repository PSGallery -Force
  ```
  ([Microsoft docs](https://docs.microsoft.com/en-us/powershell/azure/install-az-ps))
- VS Code with the Powershell extension
- Three files per environment (copy/edit from the Infrastructure repo):
  1. `deployment.ps1` (edit)
  2. `configuration_api.ps1` (create new)
  3. `configuration_portal.ps1` (create new)

## Connect to Azure

```powershell
Connect-AzAccount
# Sign in with your Azure credentials

Get-AzSubscription
# Lists accessible subscriptions with IDs

Select-AzureSubscription -SubscriptionName "<Subscription Name>"
# Or: Select-AzureSubscription -SubscriptionId "<subscription-id>"
```

Reference subscription IDs (all in tenant `e2bae64b-6e5f-4f55-b81c-ada320c7f572`):

| Subscription | ID | State |
|---|---|---|
| Development 1 | `e23c2c14-d469-4d3e-9265-6bfeb9c158f8` | Disabled |
| Test 1 | `6969113c-ad7c-47da-8684-4795c635c959` | Enabled |
| Production 1 | `74165d9f-db8b-45eb-a10f-b4338a907db5` | Enabled (legacy) |
| Demo 1 | `4dc1c55f-5df5-48e7-8f49-151c97af48be` | Enabled |
| Development 2 | `f60ac9ba-9ed9-4d36-b3d1-06e4bdabd204` | Enabled |
| Production 2 | `6389f755-3ff7-488a-a56c-7ea8297730bc` | Enabled (**primary prod**) |

See [[azure-environments]] for the full subscription-to-environment model.

## 1. Edit and run `deployment.ps1`

Stands up the base Azure resources for the environment.

```powershell
$subscription_id   = "<from table above>"
$environment_level = "<dev|test|demo|prod|qa|stg|supt>"
$postgres_password = "<set new — document on the env's deployment page>"
$synapse_password  = "<set new — document on the env's deployment page>"
$deployment_group  = "1"      # maps to your resource group (see aldc-naming-convention)
$region_character  = "c"      # c = Canada (default)
$function_sequence = "01"     # unique within the resource group
$user_id           = "<your Azure Object ID>"
```

> `$user_id` = Azure Portal → Users → your account → **Object ID**.

Run via the VS Code Powershell extension (play button, top right). Watch for error messages.

All resources it provisions follow [[aldc-naming-convention]] — e.g. `aldc<env><type>core<group>c<seq>`.

## 2. Create an app registration

Follow Confluence CORE/891813889 (not yet migrated) — covers:

- Creating the app registration in Azure AD
- Capturing `client_id`, `value`, `secret_id` (document on the env's deployment page — and copy into `vault/infra-credentials.md`)
- Assigning roles on the subscription

## 3. Edit and run `configuration_api.ps1`

Wires env vars that the Function App (core_api) will read at runtime.

```powershell
$deployment_group  = '1'
$environment_level = "<env>"
$region_character  = "c"
$function_sequence = "01"
```

Values to set in the config body:

| Variable | Source |
|---|---|
| `COSMOS_KEY` | CosmosDB → Keys → Primary Key (or Secondary) |
| `ENCRYPTION_KEY` | 32-char string, base64-encoded (e.g. `Thequickbrownfoxjumpsoverthelazy` → `VGhlcXVpY2ticm93bmZveGp1bXBzb3ZlcnRoZWxhenk=`; tool: [base64encode.org](https://www.base64encode.org/)) |
| `MASTER_CLIENT_ID` / `MASTER_CLIENT_SECRET` | Default bearer creds — see `vault/infra-credentials.md` § MASTER API bearer |
| `STORAGE_SAS1`, `STORAGE_SAS2` | Storage Account Queue → Access Keys (e.g. on `aldcdevstacqueue2c01`) |
| `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` | From step 2's app registration. Example values (**likely stale**) in `vault/infra-credentials.md` § Azure service-principal example |

Run the script; then deploy the core_api Function App.

## 4. Bring up Function App, storage, and capacity

After the Function App deploys:

1. Import the client's JSON into CosmosDB using the import button:
   - `account` (from [[clients-repo]])
   - `capacity`
   - `connection`(s)
   - `template`(s)
2. In [[Postman]], set `aldc_base_url`, `bearer_token`, `account_id` for the new env (see [[postman-collections]])
3. Run these endpoints **in order**:
   1. `setup/azurestorage` — creates blob storage for parquet files
   2. `capacity/createprovider` — stores credentials required by `setup/capacity`
   3. `setup/capacity` — creates Snowflake tables + credentials
4. Grant Snowflake access to the new storage account:
   - Storage account (e.g. `aldcdevstac{CLIENT_ID}`) → Access Control (IAM) → Add role assignment
   - Role: **Storage Blob Contributor**
   - Member: the Snowflake service principal
     - `SnowflakePACInt0121` — non-prod
     - `SnowflakePACInt0213` — prod

## 5. Authorizations for agent and portal

Run in order (check the Postman body to hit the right `authorization_id`):

1. `authorization/create` — initial CosmosDB document describing the authorization
2. `authorization/enable` — enables it (defaults to false after creation)
3. `authorization/addaccount` — which account(s) this authorization can work on
4. `authorization/addservice` — which core_api functions it can call
5. `authorization/newsecret` — generates the secret to build a bearer token from. **Save the response** — needed for the agent or portal
6. `agent/create` (optional) — creates the agent record (needs `account_id` + `connection_id`)

## 6. Build and run a connector agent

Once authorization is set up:

1. Pull the [[connector]] repo
2. Copy to `c:/aldc/`:
   - `config/` · `connector/` · `core/` · `helper/`
   - `executor_master.py` · `executor_single.py` · `requirements.txt`
3. Open `executor_master.py` — confirm it points at the correct config in `config/`
4. In that config: set `agent_id` + the `authorization` from step 5
5. `pip install -r requirements.txt`
6. Trigger `work_scan` to populate the queue
7. `python executor_master.py`

See [[connector-docker-deployment]] for the preferred containerized variant.

## 7. Edit and run `configuration_portal.ps1`

Equivalent wiring for the Portal web app.

```powershell
$deployment_group  = '2'
$environment_level = "dev"
$region_character  = "c"
$sequence          = "01"
$subscription_id   = "<from Get-AzSubscription>"
```

Values to set:

| Variable | Source |
|---|---|
| `CORE_API_TOKEN` | Build from `encode_bearer` in [[Postman]] using an existing env's `client_id` + `secret` |
| `STORAGE_ACCOUNT_KEY` | Portal's Storage Account → Access keys (e.g. `aldcdevstacportal2c01`) |

Run the script. Watch for errors.

Final step: Postgres configuration + Django settings updates (requires Django knowledge — source doc is light on detail here).

## App Registration Setup for RBAC

Source: Confluence CORE/891813889 (Creating app registration for Core, 2022-05-02).

> *2021–2022 walkthrough — verify current patterns against the `Infrastructure` repo. Managed identities or federated credentials may supersede client-secret approach for newer environments.*

For Azure service principal authentication via `ClientSecretCredential`, you need four values: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID`.

### Obtain AZURE_TENANT_ID

Azure Portal → **Azure Active Directory** → **Overview** → copy Tenant ID.

### Obtain AZURE_SUBSCRIPTION_ID

Azure Portal → **Subscriptions** → copy Subscription ID.

### Register New App (AZURE_CLIENT_ID)

1. Azure Portal → **App registrations** → **+ New registration**
2. Name (e.g. `core-api-prod-automation`), leave redirect URI blank → **Register**
3. On Overview page, copy **Application (client) ID** → this is `AZURE_CLIENT_ID`

### Generate Client Secret (AZURE_CLIENT_SECRET)

1. App Overview → **Certificates & secrets** → **Client secrets** → **+ New client secret**
2. Copy the **Value** field immediately (not "Secret ID") — it is masked after you leave the page

### Grant Contributor Role

1. Azure Portal → **Subscriptions** → select subscription → **Access control (IAM)**
2. **+ Add** → **Add role assignment** → Role: `Contributor` → Assign to the app above
3. If access denied, request from subscription owner

### Integration notes

These app registrations feed `AZURE_CLIENT_ID`/`AZURE_CLIENT_SECRET` in each environment's `local.settings.json`. Per-environment values are in `vault/infra-credentials.md` § Core API App Registrations. Referenced by CORE-279.

## See Also

- [[aldc-naming-convention]] — explains the resource names this runbook produces
- [[Azure]] — subscription model + named resources per env
- [[azure-environments]] — env-to-subscription mapping
- [[core_api]] — what the Function App serves
- [[Eclipse]] — the platform Portal + core_api back
- [[Postman]] / [[postman-collections]] — used to drive the setup endpoints
- [[connector]] — the agent repo
- [[connector-docker-deployment]] — Docker-based agent deploy (preferred over bare-VM build)
- [[new-client-setup]] — onboarding a client into an existing env
- [[eclipse-azure-deployment]] — ongoing web-app deployments after bootstrap
- `vault/infra-credentials.md` — MASTER bearer creds + Azure SP + per-env Core API App Registrations
- `vault/core-api-local-settings.md` — reference `local.settings.json`
