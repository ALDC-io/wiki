---
tags: [concept, architecture, local-network, infra, tailscale, vpn, storage, proxy, truenas, nginx]
aliases: [Local Network, ALDC Local Network, Nginx Proxy Manager, TrueNAS, Covenant, kookiet]
sources: [Confluence INFRA/1630371841, INFRA/1024622602, INFRA/961576965, CORE/1749811201, TECH/1772421124 (On-Prem Servers, Brayden Offboarding)]
created: 2026-04-18
updated: 2026-05-27
---

# ALDC Local Network Infrastructure

ALDC's on-prem network provides shared storage, VPN access, and a reverse proxy for external-facing services. These complement Azure cloud resources — Agent VMs on Proxmox depend on [[nextcloud]] and Covenant storage, and the reverse proxy exposes internal services externally.

## Reverse proxy

ALDC uses **Nginx Proxy Manager** (NPM) to route external traffic to internal services. DNS entries for reverse-proxied hosts are managed via a **Cloudflare DDNS Docker container** per host, running on the Support Docker server.

- NPM is accessible via Heimdall → "Support" (credentials in Dashlane)
- **Adding a new host requires two steps:**
  1. Add a proxy host in Nginx Proxy Manager
  2. Add a matching Cloudflare DDNS Docker container in the `cloudflare_ddns_main` stack — copy-paste an existing container config and update to match the new host

> **Diagram note:** The reverse proxy flow diagram exists on Confluence INFRA/1630371841 (2025-06-23) but is image-only and not retrievable via the MCP API. View on Confluence directly.

## Network storage — TrueNAS / Covenant

ALDC uses **TrueNAS** for local network storage on a server named **Covenant**.

| Field | Value |
|---|---|
| Hostname | `covenant.prod.site3.aldc` |
| Location | Surrey |
| Remote address | `66.183.0.251` |
| Remote SFTP port | `32322` |
| Pool | `Storage` — RAIDZ2 × 6, 30 TiB |

### SFTP remote access

Use **FileZilla** (or any SFTP client):
- Host: `sftp://66.183.0.251`, port `32322`
- Credentials: your SMB/CIFS Covenant credentials (same as local network access)
- Proxmox backup CIFS credentials: `proxmox / {{COVENANT_PROXMOX_PASSWORD}}` — see `vault/infra-credentials.md` § Covenant credentials

### Share access from Agent VMs

Agent VMs access the `Client_Tenants` share via the NextCloud sync daemon. The preferred pattern is one NextCloud container per cluster acting as a Samba relay — agents mount the Samba share, not NextCloud directly. See [[nextcloud]] § Agent VM integration.

## VPN — Tailscale

ALDC uses **Tailscale** for VPN access to on-prem resources.

| Machine | Tailscale IP | Account | Router | Routes exposed |
|---|---|---|---|---|
| kookiet | `100.70.65.48` | john.moran@aldc.io | Yes | NextCloud `192.168.22.150`, TrueNAS `192.168.22.200`, Roon `192.168.22.170` |
| Donnager | `100.113.52.87` | john.moran@aldc.io | No | — |
| inazami | `100.64.241.28` | john.moran@aldc.io | No | — |

`kookiet` is the critical subnet router. If it is offline, remote Tailscale access to NextCloud, Covenant, and Roon is lost.

For step-by-step setup on Ubuntu, see [[tailscale-linux]].

## Service Access Portals

Quick-reference URLs for connecting to on-prem and non-prod services. Source: Confluence CORE/1749811201 (2026-02-13).

### Production

| Service | URL |
|---|---|
| Snowflake | https://wj66376.canada-central.azure.snowflakecomputing.com/ |
| Portainer (Docker) | https://192.168.31.20:9446/ |
| Proxmox (Infinity, Coquitlam) | https://192.168.22.71:8006/ |

### Non-Production

| Service | URL |
|---|---|
| Snowflake | https://og35375.canada-central.azure.snowflakecomputing.com/ |
| Portainer (Docker) | https://192.168.31.20:9445/ |

### Support Infrastructure

| Service | URL |
|---|---|
| Proxmox (Nostromo, Kamloops) | https://192.168.30.80:8006/ |
| Nginx Proxy Manager | http://192.168.31.20:81/ |
| Portainer (Support) | https://192.168.31.20:9444/ |

## Mounting Covenant Storage on Linux

Source: Confluence CORE/1023770631 (2022-10).

To mount the Covenant NAS share via CIFS on a Linux VM or agent:

```bash
sudo apt install cifs-utils
sudo mkdir /mnt/covenant
sudo mount -t cifs -o username=agent //192.168.35.10/Storage/ /mnt/covenant
# Enter password when prompted
```

Credentials: `agent` / `{{COVENANT_AGENT_PASSWORD}}` — see `vault/infra-credentials.md` § Covenant credentials.

## Virtual Machine Reference

Source: Confluence TECH/1772421124 (On-Prem Servers, Brayden Offboarding). Updated 2026-04-24.

SSH credentials for all machines: `aldc/aldc1234` — see `vault/infra-credentials.md` § On-Prem VM SSH credentials. Proxmox host login credentials are in Dashlane.

| Common Name | VM Name | IP | Proxmox Host | Portainer | Purpose |
|---|---|---|---|---|---|
| Production Docker Host (Kamloops) | `aldcproddock1c01` | 192.168.35.70 | Nostromo (192.168.30.80:8006) | Production (192.168.31.20:9446) | Production [[connector]] agents. Also runs the Sellercloud VPN agent. |
| Production Docker Host (Coquitlam) | `aldcproddock1c03` | 192.168.22.70 | Infinity (192.168.22.71:8006) | Production (192.168.31.20:9446) | Secondary production [[connector]] agents (no Sellercloud VPN). `/etc/hosts` has `galactica.prod.site3.aldc → 192.168.35.138` (added 2026-05-27, required for cross-site DNS). |
| Support Docker Host | `aldcsuptdock1c01` | 192.168.31.20 | Nostromo (192.168.30.80:8006) | Support (192.168.31.20:9444) | Testing/QA resources + [[custom-fusion-92-audience-api|DIOS API]]. All publicly accessible on-prem services run here. |
| Workstation agent | `wks-agent` | 192.168.31.210 | Nostromo (192.168.30.80:8006) | N/A | Building and pushing [[connector]] Docker images. See [[connector-docker-deployment]]. |
| Galactica SQL Server | `server-galactica` | 192.168.35.138 | Nostromo (192.168.30.80:8006) | N/A | SQL Server for miscellaneous connector data. Local domain: `galactica.prod.site3.aldc`. |
| Brayden's Workstation VM | `wks-brayden-marshall` | 192.168.31.218 | Nostromo (192.168.30.80:8006) | N/A | Legacy dev workstation. ~~Useful for accessing the Support Docker host (not reachable via VPN)~~ — **superseded, see note below**. Password in `vault/infra-credentials.md`. |

> **Correction 2026-07-26:** the Support Docker host **is** reachable directly over VPN —
> ports 22 (SSH) and 81 (Nginx Proxy Manager) both answer from a VPN-connected workstation.
> The previous note claiming otherwise sent people through the legacy `wks-brayden-marshall`
> VM unnecessarily. Go direct.

### Accessing `aldcsuptdock1c01` (verified 2026-07-26)

Use key auth, not the shared password. Pubkey is installed for `aldc`; an SSH alias lives in
`~/.ssh/config` on Paul's workstation:

```
Host suptdock
    HostName 192.168.31.20
    User aldc
    IdentityFile ~/.ssh/id_ed25519
    BatchMode yes
```

Two gotchas, both learned the hard way:

- **ControlMaster multiplexing fails on this host** — `read from master failed: Connection
  reset by peer`. Same flakiness as [[connector-docker-deployment|wks-agent]]. Keep
  `ControlMaster no`. Connection economy comes from **batching remote work into a single
  `ssh` invocation**, which also avoids the fail2ban trip (~5 connects in <1 min → ~10 min
  lockout).
- **`aldc` is in `sudo` and `adm` but not `docker`**, and `sudo` requires a password. So
  `docker ps` fails for a non-interactive session. Fix once with
  `sudo usermod -aG docker aldc` (applies on next login). Note `docker` group membership is
  effectively root-equivalent — acceptable here only because `aldc` already has full
  password-based `sudo`.

## Publicly Accessible Services

Source: Confluence TECH/1772421124 (On-Prem Servers, Brayden Offboarding).

Only the **Support Docker host** (`aldcsuptdock1c01`) is configured for public internet access. Currently the [[custom-fusion-92-audience-api|DIOS API]] is the only production service exposed this way.

### How it works

Three parts:
1. **Run the service** on the Support Docker host, mapped to a specific unused port
2. **Configure a Proxy Host** in Nginx Proxy Manager with the target domain and the internal IP:port (e.g., `audience-fusion92-app.aldc-ca-w1.com` → `192.168.31.20:7000`)
3. **Configure a CNAME** in [[Cloudflare]] pointing the domain to the public IP of the on-prem server (`173.180.33.21`)

### Adding a new public-facing service (Nginx Proxy Manager)

1. Go to Nginx Proxy Manager at `http://192.168.31.20:81/` and log in (credentials in Dashlane)
2. Go to **Proxy Hosts**
3. Click **Add Proxy Host** (top-right)
4. Fill in the form: domain name (subdomain of `aldc-ca-w1.com`), IP address, and port of the service on the Support host

> **Note:** Images in the Confluence source show the NPM UI forms but are not extractable via the MCP API.

## See Also

- [[nextcloud]] — ALDC Cloud: asset sync for Agent VMs; user/share table
- [[tailscale-linux]] — Tailscale install + Remmina remote desktop on Ubuntu
- [[agent-builds]] — Agent VM setup mounts Covenant and NextCloud
- [[proxmox]] — hypervisor host guides + guest disk expansion
- [[aldc-naming-convention]] — on-prem VM naming pattern
- [[deployment-groups]] — Proxmox hypervisor inventory + VM ID conventions
- `vault/infra-credentials.md` § Covenant credentials — CIFS/SMB passwords
