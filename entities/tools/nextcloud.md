---
tags: [entity, tool, nextcloud, aldc-cloud, storage, infra]
aliases: [NextCloud, ALDC Cloud, NextCloud Configuration, cloud.aldc.io]
sources: [Confluence INFRA/965640193]
created: 2026-04-18
updated: 2026-04-18
---

# NextCloud (ALDC Cloud)

ALDC's internal file-sharing platform. Primary use: syncing the `Client_Tenants` asset folder to Agent VMs across all deployment environments. Accessible on-prem at `192.168.22.150` (via [[local-network]] Tailscale router `kookiet`).

## User accounts

All passwords are in `vault/infra-credentials.md` § NextCloud users. Two instances documented (`cloud` and `cloud2` — both share the same passwords per group).

| User | Email | Group |
|---|---|---|
| Calvin | calvin@shopduer.com | DISH_DUER |
| Kanise | kanise@shopduer.com | DISH_DUER |
| Quinton | quinton@shopduer.com | DISH_DUER |
| Phoebe Richman-Taylor | phoebe@shopduer.com | DISH_DUER |
| Kelly Byrne | kelly@shopduer.com | DISH_DUER |
| Kat | Kateryna.Petrova@kitandace.com | KIT_ACE |
| Mel | melissa.kinnoch@kitandace.com | KIT_ACE |
| Karen | karen.prete@aldc.io | Team, Team Viz |
| Sean | sean.ogrady@aldc.io | Partners |
| Mitch | mitchell.pask@aldc.io | Team |
| Lawrence | lawrence.young@aldc.io | Team |
| Emile | emile.bilodeau@aldc.io | Team |
| Tina | tina@jamescemeroninc.com | Finance |
| **Agent** | **agent@aldc.io** | **Agents** |
| Mustafa | mustafa.paigeer@aldc.io | Team |
| Jeff | jeff.prete@terrayn.com | TERRAYN |

## Share structure

| Share | Groups with access |
|---|---|
| ALDC | Partners, Backups |
| **Client_Tenants** | **Team** |
| Customers | Team |
| Finance | Finance |
| Marketing | Marketing |
| Partners | — |
| Sales | — |
| Team | Team |
| Team Data Science | Team Data Science |
| Team Viz | Team Viz |
| Vendors | — |

`Client_Tenants` is the critical share for agent operations — it holds per-client asset files synced to `D:\assets` on each Agent VM.

## Agent VM integration

Agent VMs sync `Client_Tenants` to `D:\assets` using the NextCloud desktop client:

- Login: `agent@aldc.io` / `{{NEXTCLOUD_AGENT_PASSWORD}}` — see `vault/infra-credentials.md` § NextCloud
- Root directory on agent: `D:\assets`
- Sync scope: client tenants folder → `D:\assets`

**Preferred pattern (cluster-level):** Run one NextCloud sync container per cluster rather than on every agent instance. The container serves files via Samba to the local network; agents mount the Samba share. This avoids per-agent maintenance overhead. See [[agent-builds]] for setup.

## ZFS Setup & Installation

Source: Confluence CORE/1086881902 (cloud.aldc.io NextCloud build, 2023-03).

> *2023 build procedure for the cloud.aldc.io server. OS on SSD + data on RAID-Z1 (4× 8 TB).*

```bash
sudo apt install zfsutils-linux
sudo fdisk -l                           # identify data disks (/dev/sdb–/dev/sde)
sudo zpool create ncdata raidz1 /dev/sdb /dev/sdc /dev/sdd /dev/sde
sudo zfs set mountpoint=/mnt/ncdata ncdata
zfs list                                # verify MOUNTPOINT = /mnt/ncdata
```

Install NextCloud via automated script (Hanssonit):

```bash
cd /home/ncadmin/Downloads
wget https://raw.githubusercontent.com/nextcloud/vm/master/nextcloud_install_production.sh
sudo bash nextcloud_install_production.sh
# Admin: ncadmin / (see vault/infra-credentials.md § NextCloud users)
```

## Backup Strategy & Disaster Recovery

Source: Confluence CORE/895778817 (cloud.aldc.io Backup Overview, 2023-02).

**Primary:** `https://cloud.aldc.io` (bare-metal Dell, Coquitlam, 192.168.22.229 as of 2023-02-27).

**3-2-1 strategy:**

| Copy | System | Location |
|---|---|---|
| Primary | NextCloud (bare-metal) | Coquitlam |
| Point-in-time | Veeam on Donnager VM | Kamloops (`\\covenant.prod.site3.aldc\storage\ALDC Backup`) |
| Point-in-time | Veeam on Thunderbird VM | Coquitlam (`\\192.168.25.200\ALDC - Covenant\ALDC Backup`) |
| Offsite | Azure blob | `aldcdevstac01portal` |

Coquitlam TrueNAS syncs both Donnager and Thunderbird backup folders on schedule.

**Data folders synced to Covenant (SFTP `66.183.0.251`):** `Client_Tenants`, `ALDC Customers`, `ALDC Finance`, `Infra`, `Marketing`, `Partners`, `Sales`, `Team`.

`Client_Tenants` and `ALDC Finance` also push to Azure offsite. Covenant SFTP credentials: see `vault/infra-credentials.md` § Covenant credentials.

## Client Tenant Access

Source: Confluence CLIEN/948240388.

Clients may require access to `cloud.aldc.io` — typically to upload CSVs consumed by models. An Admin grants access and sets the initial password. Client files land in `\\aldc 01\\Client_Tenants\\<CLIENT_CODE>`. The access registry table in Confluence is **not actively maintained** — authoritative user list is under NextCloud Admin → Accounts.

## See Also

- [[local-network]] — Tailscale routes to NextCloud (`192.168.22.150`); Covenant (TrueNAS) for block storage
- [[agent-builds]] — full Windows/Linux agent build including NextCloud client install
- [[proxmox]] — Proxmox hosts running NextCloud VMs (Scarif VM 13006, Nextcloud2 VM 13008)
- `vault/infra-credentials.md` § NextCloud users — all user passwords
