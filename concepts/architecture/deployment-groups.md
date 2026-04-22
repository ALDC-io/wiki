---
tags: [concept, architecture, azure, deployment-group, infra, canada]
aliases: [Deployment Groups, Azure Deployment Groups, Canada Deployment Groups, DG1, DG2]
sources: [Confluence INFRA/944373761, INFRA/973012993, INFRA/922615840, INFRA/937885723, INFRA/945782785, INFRA/947486721, INFRA/947486737, INFRA/948142081, CORE/800489527]
created: 2026-04-18
updated: 2026-04-18
---

# ALDC Azure Deployment Groups (Canada)

Azure deployment groups are ALDC's per-purpose (and per-developer) isolated environments. Each group consists of a resource group plus a standard set of Azure resources: Function Apps (Core API), Web App (Portal), Cosmos DB, queue storage, Synapse Workspace, Postgres DB, and an on-prem Proxmox Agent VM. All resource names follow [[aldc-naming-convention]].

Documented here: the Canada (`c`) deployment groups as of mid-2022. Resource names are current; version/deployment-state snapshots are stale.

## Environment matrix (Canada)

| Environment | DG | Resource Group | Azure Subscription | Billing |
|---|---|---|---|---|
| Production 2 | 1 | `aldcprodrsgp1c` | Production 2 | Production |
| Quality 1 (QA) | 1 | `aldcqarsgp1c` | Quality 1 | Non-prod |
| Test 1 | 1 | `aldctestrsgp1c` | Test 1 | Non-prod |
| Demo 1 | 1 | `aldcdemorsgp1c` | _(not specified)_ | Non-prod |
| Development 2 — DG1 (Sean O'Grady) | 1 | `aldcdevrsgp1c` _(see note)_ | Development 2 | Non-prod |
| Development 2 — DG2 (Lawrence Young) | 2 | `aldcdevrsgp2c` | Development 2 | Non-prod |
| Development 2 — DG3 (Emile Bilodeau) | 3 | `aldcdevrsgp3c` _(see note)_ | Development 2 | Non-prod |
| Development 2 — DG4 (Mitchell Pask) | 4 | `aldcdevrsgp4c` _(see note)_ | Development 2 | Non-prod |

> **Resource-group note for Dev DG1/DG3/DG4**: The Confluence source pages list `aldcprodrsgp1c` as the resource group — this appears to be a copy-paste artifact. DG2 (Lawrence) is correctly listed as `aldcdevrsgp2c`, so by naming convention the others should be `aldcdevrsgp1c`, `aldcdevrsgp3c`, `aldcdevrsgp4c`.

> **Dev DG1–3 share an App Registration**: See `vault/infra-credentials.md` § Development App Registrations. This is unusual — three developer environments share one Azure identity. DG4 (Mitchell) has its own.

## Per-environment Azure resource inventory

### Production 2 — DG1

| Component | Resource |
|---|---|
| Resource Group | `aldcprodrsgp1c` |
| Core API — Function App (General) | `aldcprodfnapcore1c01` |
| Core API — Storage | `aldcprodstaccore1c01` |
| Core API — App Service Plan | `aldcprodapspcore1c01` |
| Queue Storage | `aldcprodstacqueue1c01` |
| Cosmos DB | `aldcprodcsdb1c01` |
| Synapse Workspace | `aldcprodswsp1c01` |
| Synapse Storage | `aldcprodstacswsp1c01` |
| Portal — Web App (legacy Eclipse / Next 14 Pages Router) | `aldcprodwbapportal1c01` — served at `https://eclipse.aldc.io` |
| Eclipse-2.1 Web App (current prod UI / Next 15 App Router) | `aldcprodwbapeclipse1c01` — served at `https://eclipse.analyticlabs.io/`; Azure default URL `https://aldcprodwbapeclipse1c01.azurewebsites.net/` is reachable but CORS-blocked for auth |
| Eclipse-2.1 Core API (prod FastAPI backend) | Served at `https://api.eclipse.analyticlabs.io/v2/`; paired with the Eclipse-2.1 Web App above. Origin allowlist on prod core_api is `https://eclipse.analyticlabs.io`. |
| Portal — App Service Plan | `aldcprodapspportal1c01` |
| Portal — Storage | `aldcprodstacportal1c01` |
| Portal — Postgres DB | `aldcprodpgdbportal1c01` |
| Core API App Registration | `aldcprodaprgcore1c01` |
| Agent VM (Proxmox) | `aldcprodagnt1c01` |
| DNS — General API | `general.api.canada.prod.aldc.io` |

Prod 2 provisions only the General API Function App instance; Portal and Data API instances not deployed. Credentials: `vault/infra-credentials.md` § Production 2.

> **Eclipse vs Eclipse-2.1**: Two parallel prod deployments on **different brand domains** — not a pending DNS cutover of the same hostname. `aldcprodwbapportal1c01` is the legacy Next 14 Pages Router deploy at `https://eclipse.aldc.io` (the `aldc.io` brand). `aldcprodwbapeclipse1c01` is the Next 15 App Router rewrite at `https://eclipse.analyticlabs.io/` (the `analyticlabs.io` brand) — this is the current production product, running out of the `eclipse-2.1` branch, paired with prod core_api at `https://api.eclipse.analyticlabs.io/v2/`. Verify eclipse-2.1 changes via `https://eclipse.analyticlabs.io/` — the Azure default URL is reachable but CORS-blocked for auth because only `.analyticlabs.io` is in the origin allowlist. See [[entities/repos/eclipse|eclipse (repo)]] disambiguation for the full context.

### Quality 1 (QA) — DG1

| Component | Resource |
|---|---|
| Resource Group | `aldcqarsgp1c` |
| Core API — Function App | `aldcqafnapcore1c01` |
| Core API — Storage | `aldcqastaccore1c01` |
| Core API — App Service Plan | `aldcqaapspcore1c01` |
| Queue Storage | `aldcqastacqueue1c01` |
| Cosmos DB | `aldcqacsdb1c01` |
| Synapse Workspace | `aldcqaswsp1c01` (status uncertain in source) |
| Synapse Storage | `aldcdevstacswsp2c01` (noted as uncertain in source) |
| Portal — Web App | `aldcqawbapportal1c01` |
| Portal — App Service Plan | `aldcqaapspportal1c01` |
| Portal — Storage | `aldcqastacportal1c01` |
| Portal — Postgres DB | `aldcqapgdbportal1c01` |
| Core API App Registration | `aldcqaaprgcore1c01` |
| Django config | `core.settings_qa1c01` |

Credentials: `vault/infra-credentials.md` § QA1.

### Test 1 — DG1

Test is the most fully provisioned non-prod environment — all three Function App instances (General, Portal, Data) are deployed and DNS-registered.

| Component | Resource |
|---|---|
| Resource Group | `aldctestrsgp1c` |
| Core API — Function App (General) | `aldctestfnapcore1c01` |
| Core API — Function App (Portal) | `aldctestfnapcore1c02` |
| Core API — Function App (Data) | `aldctestfnapcore1c03` |
| Core API — Storage (General/Portal/Data) | `aldcteststaccore1c01/02/03` |
| Core API — App Service Plans | `aldctestapspcore1c01/02/03` |
| Queue Storage | `aldcteststacqueue1c01` |
| Cosmos DB | `aldctestcsdb1c01` |
| Synapse Workspace | `aldctestswsp1c01` |
| Synapse Storage | `aldcteststacswsp1c01` |
| Portal — Web App | `aldctestwbapportal1c01` |
| Portal — App Service Plan | `aldctestapspportal1c01` |
| Portal — Storage | `aldcteststacportal1c01` |
| Portal — Postgres DB | `aldctestpgdbportal1c01` |
| Core API App Registration | `aldctestaprgcore1c01` |
| Agent VM (Proxmox) | `aldctestagnt1c01` |
| DNS — General API | `api-test.api.canada.aldc.io` |
| DNS — Portal API | `portal-test.api.canada.aldc.io` |
| DNS — Data API | `data-test.api.canada.aldc.io` |

Credentials: `vault/infra-credentials.md` § Test1.

### Demo 1 — DG1

Demo is the only environment without a Synapse Workspace deployment.

| Component | Resource |
|---|---|
| Resource Group | `aldcdemorsgp1c` |
| Core API — Function App (General) | `aldcdemofnapcore1c01` |
| Core API — Storage | `aldcdemostaccore1c01` |
| Core API — App Service Plan | `aldcdemoapspcore1c01` |
| Queue Storage | `aldcdemostacqueue1c01` |
| Cosmos DB | `aldcdemocsdb1c01` |
| Synapse Workspace | _(not deployed in Demo)_ |
| Portal — Web App | `aldcdemowbapportal1c01` |
| Portal — App Service Plan | `aldcdemoapspportal1c01` |
| Portal — Storage | `aldcdemostacportal1c01` |
| Portal — Postgres DB | `aldcdemopgdbportal1c01` |
| Core API App Registration | `aldcdemoaprgcore1c01` |
| Agent VM (Proxmox) | `aldcdemoagnt1c01` |
| Django config | `core.settings_demo1c01` |

Credentials: `vault/infra-credentials.md` § Demo1.

### Development 2 — DG2 (Lawrence Young)

DG2 is the most fully documented dev environment.

| Component | Resource |
|---|---|
| Resource Group | `aldcdevrsgp2c` |
| Core API — Function App | `aldcdevfnapcore2c01` |
| Core API — Storage | `aldcdevstaccore2c01` |
| Core API — App Service Plan | `aldcdevapspcore2c01` |
| Queue Storage | `aldcdevstacqueue2c01` |
| Cosmos DB | `aldcdevcsdb2c01` |
| Synapse Workspace | `aldcdevswsp2c01` |
| Synapse Storage | `aldcdevstacswsp2c01` |
| Portal — Web App | `aldcdevwbapportal2c01` |
| Portal — App Service Plan | `aldcdevapspportal2c01` |
| Portal — Storage | `aldcdevstacportal2c01` |
| Portal — Postgres DB | `aldcdevpgdbportal2c01` |
| Core API App Registration | `aldcdevaprgcore2c01` |

Credentials: `vault/infra-credentials.md` § Development App Registrations / DG2.

### Development 2 — DG1 (Sean O'Grady), DG3 (Emile Bilodeau), DG4 (Mitchell Pask)

DG1, DG3, and DG4 follow the same pattern as DG2 with their respective group numbers. DG1/DG3 share an App Registration with DG2; DG4 (Mitchell) has a distinct one. See `vault/infra-credentials.md` § Development App Registrations for all client IDs and secrets.

## Deployment playbook

Standard procedure for provisioning a new Azure deployment group. Steps marked `→` link to the full [[azure-environment-bootstrap]] runbook.

1. Copy existing PowerShell template folder; edit parameters for target resources →
2. Execute PowerShell templates: Resource Group → Core API → Portal →
3. Create Core API App Registration manually (contributor access to subscription) →
   - Record: Subscription ID, Client ID, Client Secret
4. Run Core API Configuration PowerShell (`<function-app>/configuration.ps1`) →
   - Generate a fresh 32-byte base64 `ENCRYPTION_KEY` per environment (do not reuse across envs)
5. Deploy Function App (Core API) to all instances
6. Copy existing client tenant database to correct format for the deployment group
7. Load core Cosmos DB documents: `account.json`, `account_secret.json`, `work_template.json`
8. Test Function App: `account/describe` for a known account
9. Run Portal Configuration PowerShell (`<web-app>/configuration.ps1`) →
10. Upload Portal background images to portal storage account
11. Configure Postgres DB: create database + create service username
12. Create Portal API Client (enable; assign `portal` and `essentials` groups)
13. Ensure Web App settings file is correct
14. Deploy Web App (Portal): code → migration → superuser creation (`super@aldc.io`)
15. Create agent VM clone in Proxmox
16. Configure agent VM: Python, PowerShell, drivers, NetSuite, virtual env, config file, client service groups

## Virtual Hosts & On-Prem Infrastructure

Source: Confluence CORE/800489527 (Data Centre, last updated 2026-02-11).

### Network Connectivity

| Site | Provider | Account | Throughput |
|---|---|---|---|
| Kamloops (KA1 — Site 3) | Telus Business | 606340644 | 940/940 Mbps (dual WAN: SFP + Ethernet) |
| Coquitlam (Site 2) | Telus Business | — | 3000/3000 Mbps |

Telus Business Customer Care: 604 549-3292, 08:00–17:00 PT.

### Workload Resource Summary

| Function | CPU | Memory | Storage (net) | GPU |
|---|---|---|---|---|
| Backup | Small | 48 GB | 40 TB Magnetic | — |
| Employee VMs (9×) | Medium | 216 GB | 2.25 TB | 22.5 GB Basic |
| Fusion92 VMs (5×) | Small | 40 GB | 1.25 TB | 12.5 GB Basic |
| LLM GPU Services | Large | 128 GB | 3 TB | 32 GB CUDA/Tensor |
| Docker Support | Small | 128 GB | 500 GB | — |
| Sandboxes (2×) | Small | 64 GB | 1 TB | — |
| Agents QA/Test | Medium | 128 GB | 1.1 TB | — |
| **Total** | — | **816 GB** | **9.6 TB NVMe + 40 TB Magnetic** | **67 GB** |

### Subnet Architecture

| Subnet | Purpose | DHCP Range | DNS Suffix |
|---|---|---|---|
| 192.168.x0.1/24 | Proxmox Hypervisor Mgmt | None | `hv` |
| 192.168.x1.1/24 | Proxmox Guests (support) | 50–250 | `support` |
| 192.168.x2.1/24 | Proxmox Guests (prod) | 50–250 | `prod` |
| 192.168.x3.1/24 | Proxmox Guests (non-prod) | 50–250 | `nonprod` |
| 192.168.x7.1/24 | Guest VLAN | 50–250 | `guest` |
| 192.168.x8.1/24 | Home Network | 50–250 | `home` |
| 192.168.x9.1/24 | Office Network | 50–250 | `office` |
| 192.168.9.1/24 | Backup (isolated) | None | — |

Site prefixes: Coquitlam (Site 2) = `192.168.20–29.x`, Kamloops (Site 3) = `192.168.30–39.x`, Bonaparte (Site 5) = `192.168.50–59.x`.

### Proxmox Hypervisors

Named after fictional spaceships. Proxmox admin portal: port 8006.

| Site | Machine | Environments | Primary Uses | Proxmox URL | iDRAC |
|---|---|---|---|---|---|
| KA1 | Nostromo (R730) | SUPPORT, NONPROD | Workstations, Docker Dev/QA | 192.168.30.80:8006 | 192.168.30.81 |
| KA1 | Sulaco (R730) | PROD | Docker Production 1 | 192.168.30.82:8006 | 192.168.30.83 |
| KA1 | Patna (R430) | SANDBOX | Docker Sandbox | 192.168.30.84:8006 | 192.168.30.85 |
| KA1 | Auriga (R730xd) | SUPPORT | TrueNAS, Docker Support | 192.168.30.86:8006 | 192.168.30.87 |
| VR1 | Infinity (R730) | PROD | Docker Production 2 | 192.168.30.80:8006 | 192.168.22.157 |

**Nostromo specs:** 2× E5-2697A V4 (16-core 2.6 GHz), 512 GB RAM, 8 TB ZFS boot storage.

Backups stored on Covenant CIFS shares (`Proxmox-<machine-name>`). For CIFS reconnect issues: `umount -f -a -t cifs -l` then remount. Quick restore: SCP `.zst` backup to `/var/lib/vz/dump` and restore from Proxmox UI.

### Docker Container Runtimes

VM naming prefix: `17XXX`.

| Hypervisor | VM ID | Machine | Env | IP | Cores | Memory | Role |
|---|---|---|---|---|---|---|---|
| Sulaco | 17001 | `aldcproddock1c01` | Prod DG1 | 192.168.35.70 | 52 | 224 GB | Docker Node 01 |
| Marathon | 17003 | `aldcproddock1c03` | Prod DG1 | 192.168.22.70 | 32 | 128 GB | Docker Node 01 |
| Auriga | 17005 | `aldctestdock1c01` | Test DG1 | 192.168.36.70 | 16 | 96 GB | Docker Node 01 |
| Auriga | 17008 | `aldcqadock1c01` | QA DG1 | 192.168.36.71 | 16 | 64 GB | Docker Node 01 |
| Nostromo | 17007 | `aldcsuptdock1c01` | Support DG1 | 192.168.31.20 | 16 | 128 GB | Docker Node 01 |
| Infinity | 17009 | `aldcproddock1c05` | Prod DG1 | — | 52 | 224 GB | Docker Node 05 |

### Support VMs (VM 13XXX series)

| Hypervisor | VM ID | Name | OS | IP | Purpose |
|---|---|---|---|---|---|
| Nostromo | 13002 | Galactica | Windows 10 | — | SQL Server (RDP only). Credentials: `vault/infra-credentials.md` § Data Centre VM credentials |
| Nostromo | 13003 | Tycho | Ubuntu | — | [[local-network\|Tailscale]] Gateway |
| Auriga | 13004 | Covenant | TrueNAS (FreeBSD) | — | iSCSI Server + Fileserver |
| Nostromo | 13005 | Ganymede | Ubuntu 22.04 | — | Docker Server |
| Gateway | 13006 | Scarif | Ubuntu 22.04 | — | [[nextcloud\|Nextcloud]] Server |
| Nostromo | 13008 | Nextcloud2 | Ubuntu 22.04 | — | Backup Nextcloud Server |

### VM Templates (VM 16XXX series)

| Hypervisor | VM ID | Name | OS |
|---|---|---|---|
| Gateway | 16001 | `template-ubuntu22` | Ubuntu 22.04 |
| Sulaco | 16002 | `template-winsvr22` | Windows Server 2022 |
| Nostromo | 16003 | `template-ubuntusvr22` | Ubuntu Server 22.04 |
| — | 16004 | `template-docker` | Ubuntu Server 22.04 |
| — | 16005 | `template-workstation` | Windows 10 |

VirtIO/QEMU drivers required on Windows and Linux VMs at provisioning.

### VM Numbering Convention

| Range | Purpose |
|---|---|
| `11XXX` | Agents (non-prod; deprecated as of v1.9.0) |
| `12XXX` | Agents (prod; deprecated) |
| `13XXX` | Support services |
| `14XXX` | Support/test/non-prod |
| `15XXX` | Workstations |
| `16XXX` | Templates |
| `17XXX` | Docker/Kubernetes |

### UDM Pro DDNS

Dynamic DNS via Cloudflare using the `willswire/unifi-cloudflare-ddns` container.

## See Also

- [[aldc-naming-convention]] — the naming pattern all resources above follow; includes DNS format and tagging requirements
- [[azure-environment-bootstrap]] — full PowerShell runbook (steps 2–4 above)
- [[azure-environments]] — subscription-to-environment mapping (which subscription each env lives in)
- [[connector]] — Agent VM runs the connector; Docker-based, Proxmox-cloned
- `vault/infra-credentials.md` — all credentials redacted from this page: Synapse admin, portal superuser, Postgres per-env, Core API app registrations, portal/agent API clients, Data Centre VM credentials
