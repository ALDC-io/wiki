---
tags: [concept, architecture, local-network, infra, tailscale, vpn, storage, proxy, truenas, nginx]
aliases: [Local Network, ALDC Local Network, Nginx Proxy Manager, TrueNAS, Covenant, kookiet]
sources: [Confluence INFRA/1630371841, INFRA/1024622602, INFRA/961576965, CORE/1749811201]
created: 2026-04-18
updated: 2026-04-18
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

## See Also

- [[nextcloud]] — ALDC Cloud: asset sync for Agent VMs; user/share table
- [[tailscale-linux]] — Tailscale install + Remmina remote desktop on Ubuntu
- [[agent-builds]] — Agent VM setup mounts Covenant and NextCloud
- [[proxmox]] — hypervisor host guides + guest disk expansion
- [[aldc-naming-convention]] — on-prem VM naming pattern
- [[deployment-groups]] — Proxmox hypervisor inventory + VM ID conventions
- `vault/infra-credentials.md` § Covenant credentials — CIFS/SMB passwords
