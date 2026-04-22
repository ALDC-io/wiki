---
tags: [process, deployment, setup, onboarding, python, vscode, docker, power-bi]
aliases: [Environment Setup, Laptop Setup, Developer Onboarding, Machine Setup]
sources: [sources/obsidian-import/general/Laptop Setup.md, sources/obsidian-import/general/Power BI Setup.md, sources/obsidian-import/general/Python & VSCode Setup.md, sources/obsidian-import/general/Docker -Core Connectors - VMs.md]
created: 2026-04-16
updated: 2026-04-17
---

# Environment Setup -- New Developer / Machine

Complete setup guide for a new ALDC development machine. Covers tooling, repos, Python environment, [[Snowflake]] connectivity, [[Power BI]] Desktop, Docker agents, and VM access.

> **Before running this**: complete [[employee-onboarding]] first. That page covers account access (M365, Slack, GitHub, Jira, Eclipse, Snowflake, Azure permissions). This page assumes those accounts and permissions are in place.

## Prerequisites

- Windows 11 machine with admin access
- ALDC GitHub organization membership
- Dashlane access (for credentials)
- Okta SSO configured (for [[Snowflake]] web login)
- Service account credentials for [[Power BI]] (in Dashlane)

## Steps

### 1. Core Software Installation

Install the following:

1. **Git** -- verify with `git --version`
2. **Python 3.12** -- verify with `python --version`
3. **VS Code**
4. **Power BI Desktop** -- install via Windows Package Manager (`winget`)
5. **SQL Server Management Studio (SSMS) 22** -- needed for SellerCloud VPN-connected databases
6. **SnowSQL** -- Snowflake CLI, more reliable than the VS Code extension for SSO auth

### 2. VS Code Setup

**Extensions to install:**
- Python
- Pylance
- Snowflake (optional -- may have SSO auth issues, see Known Issues below)
- AI integration tools (as preferred)

**Interpreter configuration:**
- After creating a project venv, set the interpreter to `.venv\Scripts\python.exe` in VS Code

### 3. Clone Repositories

```bash
git clone <clients-repo-url>
git clone <connector-repo-url>
```

Key repos (located at `C:\Users\PaulRussell\repos\`):
- **[[clients-repo]]** -- Per-client [[Eclipse]] configs + [[Snowflake]] warehouse SQL (primary repo)
- **connector** -- The [[Eclipse]] connector runtime (Docker-based)
- **core_api** -- ALDC's core API service

### 4. Python Virtual Environment (for connector repo)

```bash
cd connector
python -m venv .venv
```

**Activate (Git Bash):**
```bash
source .venv/Scripts/activate
```

**Activate (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Upgrade core tooling first** (prevents many build failures):
```bash
python -m pip install --upgrade pip setuptools wheel
```

**Install dependencies:**
```bash
pip install -r requirements-no-pyarrow.txt
```

> **Known issue:** The repo pins `pyarrow==5.0.0` which does NOT support Python 3.12 and will fail to build from source. Use the `requirements-no-pyarrow.txt` file. If pyarrow is needed later, coordinate with the team to upgrade.

**Verify environment:**
```bash
python -c "import pandas, numpy; print('env ok')"
```

### 5. Git Hygiene

Ensure `.gitignore` includes:
```
.venv/
venv/
__pycache__/
*.pyc
```

This prevents thousands of virtual environment files from appearing in source control. If you previously saw many unexpected changes after activating a venv, this is likely the cause.

### 6. Environment Variables

Create a `.env` file in the connector repo root (already git-ignored):

```
SNOWFLAKE_ACCOUNT=og35375.canada-central.azure
SNOWFLAKE_USER=<YOUR_USERNAME>
SNOWFLAKE_ROLE=SYSADMIN
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_TOKEN=<if using PAT>
```

Load in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

### 7. Snowflake Access

**What works:**
- Web login via SSO at Snowsight (`og35375.canada-central.azure.snowflakecomputing.com`)
- MFA authentication
- Account: `OG35375`, Region: `AZURE_CANADACENTRAL`, Role: `SYSADMIN`, Warehouse: `COMPUTE_WH`

**SnowSQL (recommended for CLI access):**
```bash
snowsql -a og35375.canada-central.azure -u <YOUR_USERNAME> --authenticator externalbrowser
```
This opens the browser for SSO/MFA completion.

**Known issues with programmatic access** (see Known Issues section below for details):
- VS Code Snowflake extension has SSO/proofKey errors
- Python connector external browser SSO gives SAML IdP errors
- Python connector PAT gives OAuth/network policy errors

### 8. Power BI Setup

1. Install [[Power BI]] Desktop via Windows Package Manager
2. Install SSMS 22
3. For web access to Power BI Service, use **anonymous/private browser mode** before logging in with service account credentials
4. Service account credentials are in Dashlane (look for "PBI Snowflake Non-Prod" for test, equivalent for prod)

**Power BI environment parameters** (used in `.pbix` model files):

| Environment | CORE_API_URL | SNOWFLAKE_HOST |
|---|---|---|
| Test | `https://aldctestfnapcore1c01.azurewebsites.net` | `og35375.canada-central.azure.snowflakecomputing.com` |
| Prod | `https://aldcprodfnapcore1c01.azurewebsites.net` | `wj66376.canada-central.azure.snowflakecomputing.com` |

### 9. VPN Access (for SellerCloud / SSMS)

VPN access is needed for querying SellerCloud SQL Server databases directly.

1. Obtain VPN configuration from Sean O'Grady (sean.ogrady@5x5inc.ca) or Marshall Johnston
2. Username and password are provided with the config
3. After connecting via VPN, use SSMS to run partitions (usually orderline, marketing activity)
4. Most tables do not need manual partition processing -- GEP is the exception

### 10. Docker / Connector Agent Setup (for deployments)

For building and deploying [[Eclipse]] connector agents. This is typically done on remote servers, not the local dev machine.

**Build server:** `ssh aldc@workstation-agent`

1. Navigate to `docker_build/agent-template-env`
2. Copy the desired config: `cp config-test.json config.json`
   - Configs differ for test, prod Kamloops, prod Coquitlam, and QA
   - Verify: `sleep = 600`, `thread_timeout = 3600`, `max_threads > 1`, `target_host` matches target environment
3. Build: `sudo ./build.sh`
   - Set agent name (e.g., `dcgeneral`) -- for Prod, build separate images for Kamloops and Coquitlam
   - Set branch (e.g., `master` or `1.24.0`)
   - Set version (e.g., `1.24.0`) -- use unique names to avoid overwrites (e.g., `1.24.0-itm-250`)
   - Build pushes to GitHub Container Registry: `https://github.com/orgs/ALDC-io/packages/container/package/agent-dcgeneral`

**Deployment server:** `ssh aldc@<server-url>` (separate servers per environment)

Agent counts by environment:
- Test and Prod Kamloops: 4 agents
- Prod Coquitlam: 3 agents
- QA: 1 agent

For each agent:
1. Shut down the old agent in Portainer (keep as backup, delete the previous backup)
2. On the server: `sudo ./run.sh`
3. Set image name (e.g., `agent-dcgeneral:1.24.0`)
4. Set container name (e.g., `agent1-1.24.0`)
5. For normal agents, accept defaults when asked for options
6. For **GEP SellerCloud** agent: enter `openvpn` as the option name, then input values from Dashlane

**Docker login (if registry push fails):**
```bash
export DOCKER_CLI_TOKEN=<token from github>
echo $DOCKER_CLI_TOKEN | sudo docker login ghcr.io --username <github-username> --password-stdin
```
Use the `aldc-svc-automation` account. Note: `sudo` must already be authenticated or the password prompt will consume the pipe input.

### 11. Bookmarks and Productivity Setup

Create browser bookmarks for frequently accessed URLs:
- [[Eclipse]] templates dashboard
- [[Snowflake]] Snowsight
- Jira
- Confluence
- Miro
- GitHub
- [[Power BI]] Service (`app.powerbi.com`)

Set up SSH known hosts for servers (e.g., Terence workstation).

### 12. Sanity Checklist

Before starting real tickets, confirm:

- [ ] Repos clone successfully
- [ ] `.venv` activates in connector repo
- [ ] Requirements install (using no-pyarrow file)
- [ ] `.env` loads
- [ ] Basic Python imports work (`pandas`, `numpy`)
- [ ] Git status is clean (no venv files showing)
- [ ] [[Snowflake]] web login works via SSO
- [ ] [[Power BI]] Desktop installed and opens
- [ ] [[Power BI]] Service accessible with service account

## Pitfalls / Gotchas

### VS Code Snowflake Extension Unreliable

Observed errors: `Cannot read properties of null (reading 'proofKey')`, `Cannot read properties of null (reading 'ssoUrl')`, hostname certificate mismatch. Caused by enterprise SSO configuration + PrivateLink/network policy. **Do not block development on this extension** -- use Snowsight web UI instead.

### Python Snowflake Connector SSO Fails

External browser SSO gives SAML IdP errors (`390190`). PAT auth gives OAuth/Okta errors. This is a platform-level configuration issue, not a local setup problem. Requires Snowflake admin clarification on: whether `externalbrowser` is allowed, whether PATs work, whether key-pair or OAuth is preferred.

### pyarrow Incompatibility

`pyarrow==5.0.0` pinned in `requirements.txt` is incompatible with Python 3.12. Use the `requirements-no-pyarrow.txt` workaround.

### Docker sudo and Password Pipes

When using `echo $TOKEN | sudo docker login ...`, if `sudo` hasn't been recently authenticated, it prompts for a password and the pipe sends your token to the password prompt instead. Always run a `sudo ls` or similar first to cache sudo credentials.

## See Also

- [[clients-repo]] -- primary repository structure
- [[Eclipse]] -- connector platform
- [[Snowflake]] -- data warehouse
- [[Power BI]] -- reporting layer
- [[gep-snowflake-pbi-deployment]] -- end-to-end deployment runbook
- [[ticket-breakdown-to-ship]] -- ticket lifecycle process
