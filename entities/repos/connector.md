---
tags: [entity, repo, connector, aldc, prefect, data-plane]
aliases: [connector, connector-repo, Eclipse connector runtime]
sources: [daily/2026-04-17.md, entities/tools/prefect.md, entities/tools/eclipse.md, ~/.claude/CLAUDE.md, Confluence TECH/1769177102 (Old Connectors v3, Brayden Offboarding), TECH/1772421124 (On-Prem Servers)]
created: 2026-04-17
updated: 2026-04-27
---

# connector

ALDC's data-transport / data-plane repository. Lives at `C:\Users\PaulRussell\repos\connector`. Houses the runtime code that pulls data from source APIs/DBs, drops it into [[Azure]] storage, and triggers [[Snowflake]] ingestion queries. Being actively migrated from legacy `BaseConnector`-based connectors to [[Prefect]] flows (PRE-000).

## Role in the pipeline

connector owns the **data plane** — the actual movement of bytes from source → intermediate storage → Snowflake:

```
Source APIs / DBs
        │
        ▼
connector (legacy BaseConnector or Prefect flow)
        │  writes pulled data
        ▼
Azure Storage Account  ◄──── transport layer
        │
        │  Snowflake query (COPY INTO / MERGE)
        ▼
Snowflake DWH (CURRENT_* tables in source schemas)
```

Contrast with [[core_api]], which is the **control plane** (Eclipse backend, CosmosDB reads, warehouse-rebuild functions). The two repos used to share responsibility; the Prefect migration has been pulling transport code out of core_api into connector.

## Architecture layers

From the Prefect migration notes (see [[Prefect]] for full detail):

| Layer | Location | Pattern |
|-------|----------|---------|
| Legacy connectors | `connector/connectors/*.py` | `BaseConnector`-based, dict-style options/connection. Not registered with Prefect |
| Prefect bootstrap | `main.py → DeploymentRunner.serve_local()` | Registers block schemas, serves deployments from `connector/accounts/<account>/deployments/` |
| Reference implementation | `connector/accounts/ALDC_QA/deployments/exchange_rates.py` | Senior dev example of target Prefect pattern |
| Output handling | `BaseConnector.add_response()` | Parquet write, Azure blob upload, Snowflake staging / merge |
| Test framework | `tests/conftest.py` + `tests/test_*.py` | Session-scoped `prefect_test_harness`, mocked Block/Azure/Snowflake fixtures. `pytest tests/` required on every PR |
| CI quality gate | `.github/workflows/quality-gate.yml` | Semgrep · TruffleHog · pytest · PyTestArch · Claude Opus review. All checks must be green before merge to `operation-fiasco` |

## Docker deployment

connector runs as a Docker container on VMs (workstation-agent build → push to GHCR → deploy via Portainer across test/prod/QA hosts). Full procedure at [[connector-docker-deployment]].

## Relationship to core_api (Prefect era)

> **Paul's open question (2026-04-17):** the exact boundary is still fuzzy. Today's KT note: "for prefect connector/template — connection through PBI — not core_api anymore." That phrasing needs unpacking — specifically what "connection through PBI" means in the Prefect flow context.

Current best understanding:

- **Pre-Prefect**: core_api held both Eclipse API surface + many data-pull queries
- **Post-Prefect**: data-pull queries moved into connector; core_api retains Eclipse API + warehouse rebuild functions
- The Prefect flows themselves live under `connector/accounts/<ACCOUNT>/deployments/`

## Incidents of note

- [[connector-timeout-outage]] — post-mortem on the `/work/pick` Azure Function timeout caused by an O(N_accounts × N_connections) global queue sweep

## Deployment environments

Follows the [[azure-environments]] model. QA subscription currently hosts the Prefect sandbox where new flows are proven out before rolling to prod.

## Legacy (pre-Prefect) architecture

Sourced from Confluence TECH/1769177102 (Brayden Offboarding / Old Connectors), ingested 2026-04-17.

The pre-Prefect connector stack — still running until the Prefect migration completes — has four moving parts:

- **Connector Agents** — on-prem Docker containers on the Kamloops and Coquitlam servers. Poll [[core_api]]'s `/work/pick` endpoint for queued work items. Deploy runbook: [[connector-docker-deployment]].
- **Core API (connector instance)** — the `aldcprodfnapcore1c03` function app (not `aldcprodfnapcore1c01`, which serves Legacy Eclipse / Eclipse 1). See [[Azure]] for the full function-app inventory.
- **Task Trigger** — `aldcprodfnaptrigger1c01`. Periodically calls core's `/task/scan`. A "task" is a document in the CosmosDB `task` container describing an API request + schedule. `/task/scan` finds due tasks and queues each as a message on Azure Queue Storage (`aldcprodstacqueue1c01`).
- **Queue Trigger** — `aldcprodfnapqueuetrigger1c01`. Drains the Azure Queue and executes each queued task. The key task type is `/work/scan`, which finds due templates and queues them onto per-connection work queues.

### Queue storage layout

Work items sit across **multiple** Azure Storage accounts named `aldcprodstac1c<account-id>` — distinct from `aldcprodstacqueue1c01` (which holds *tasks*, not *work items*). Within each of those storage accounts there is one queue per connection ID. Connector Agents poll these via `/work/pick`.

### End-to-end template run

1. Task Trigger fires on schedule → calls `/task/scan`
2. `/task/scan` queues a `/work/scan` task onto Azure Queue Storage (`aldcprodstacqueue1c01`)
3. Queue Trigger drains that queue → calls `/work/scan`
4. `/work/scan` finds due templates → queues work items onto per-connection queues in `aldcprodstac1c<N>` storage accounts
5. Connector Agents poll `/work/pick` via the `aldcprodfnapcore1c03` [[core_api]] instance → pick work items → execute

This is the architecture the [[Prefect]] migration is replacing. See [[connector-timeout-outage]] for the `/work/pick` incident that exposed the global-queue-sweep scaling limit.

### Deploying Connector Agents (legacy)

Source: Confluence TECH/1769177102 (Old Connectors v3, updated 2026-04-22).

1. SSH into the workstation-agent VM (`wks-agent`, IP `192.168.31.210`). See [[local-network]] § Virtual Machine Reference.
2. Navigate to `docker_build/agent-template-env`
3. `ls` to find the config file for the target environment → `cp config-prod-kamloops.json config.json`
4. Run `sudo ./build.sh` — follow prompts, push to GHCR when asked
5. SSH into the target Docker host (Kamloops or Coquitlam)
6. Navigate to the directory with the build scripts (location varies by host)
7. Run `sudo ./run.sh` — follow prompts
8. Verify the new agent is running, then stop the old agent

See [[connector-docker-deployment]] for the full Docker runbook.

### Sellercloud VPN Agent

Source: Confluence TECH/1769177102 (Old Connectors v3, updated 2026-04-22).

A special connector agent runs on the **Kamloops host only** for GEP's Sellercloud SQL connection. It is a separate agent because it must connect to Sellercloud's VPN to reach their SQL database.

**Building the VPN agent image:**
- When running `build.sh`, enter agent ID `gep-sellercloudvpn` (instead of the default). This creates a separate image with a different agent ID so it only picks up Sellercloud SQL templates.

**Deploying the VPN agent:**
1. Run `./run.sh` as normal
2. When prompted for **Script Option**, enter `openvpn`
3. When prompted for environment variables, enter the VPN credentials from Dashlane → Secrets → "GEP Sellercloud SQL VPN" one at a time (e.g., `OVPN_USERNAME` → `GEP_Chris.Verde`)
4. After all variables, type `exit` to start the container
5. Check container logs — look for a VPN connection success message near the top

## Development Standards

All code in the connector repo must follow ALDC standards:

- [[ai-pr-workflow]] — automated PR checks (Semgrep, TruffleHog, Claude Opus review, PyTestArch, quality gate). Live as of 2026-04-10.
- [[adversarial-investigation-skill]] — `/investigate-adversarial` skill for debugging and architecture decisions
- [[ai-development-project-standard]] — mandatory header + ROI tracking for any feature with >50% AI authorship
- [[python-development-standards]] — PEP 8, Google docstrings, VS Code + PyLint conventions
- [[git-branching-strategy]] — ALDC branching model; connector follows the same `development` → `user-testing` → `main` flow

## Connector Specs

The 6 ad platform connector specs in `entities/tools/connectors/` document the legacy connection/options schemas and auth patterns that Prefect flows must replicate. Full development pattern in [[connector-development-standards]].

- [[google-analytics]] — GA4 + Universal Analytics connector
- [[facebook-ads]] — Meta Marketing API connector
- [[bing-ads]] — Microsoft Advertising connector
- [[google-ads]] — Google Ads connector
- [[amazon-ads]] — Amazon Ads + DSP connector
- [[trade-desk]] — The Trade Desk My Reports connector
- [[google-oauth-python]] — shared Google OAuth pattern (used by GA4 + Google Ads)
- [[connector-token-refresh]] — operational token refresh runbook (Bing 90-day, Facebook 60-day)

## See Also

- [[Prefect]] — the orchestration framework this repo is migrating to
- [[connector-development-standards]] — canonical Prefect connector pattern (attribute hierarchy, migration steps, PartitionScheme/MergeScheme selection)
- [[python-development-standards]] — PEP 8 + Google docstring + linter conventions for all ALDC Python
- [[Eclipse]] — the platform connector serves (legacy pattern)
- [[core_api]] — sibling control-plane repo
- [[Azure]] — hosts the storage accounts connector writes to
- [[Snowflake]] — final destination of connector output
- [[connector-docker-deployment]] — Docker deploy runbook
- [[connector-timeout-outage]] — prior incident post-mortem
- [[azure-environments]] — where the QA/prod Prefect deployments live
