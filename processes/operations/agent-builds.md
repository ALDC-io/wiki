---
tags: [process, operations, agent, proxmox, windows, linux, vm, backup]
aliases: [Agent Builds, Agent VM Setup, Agent Backup, Agent Redeployment, Proxmox Agent]
sources: [Confluence INFRA/957382661, INFRA/1062567937, CORE/922550273]
created: 2026-04-18
updated: 2026-04-18
---

# Agent VM Builds, Backup & Redeployment

Runbooks for provisioning ALDC Agent VMs on Proxmox (Windows and Linux) and for backing up and restoring them. The agent process runs on these VMs and executes Eclipse data-pull jobs.

## VM naming convention

Agent VMs follow [[aldc-naming-convention]]:

```
aldc<env>agnt<deployment-group><region><instance>
```

Example: `aldctestagnt4c03` — test env, agent, DG4, Canada, instance 03.

## Proxmox VM ID numbering scheme

| Range | Purpose |
|---|---|
| 11XXX | Agents (non-prod) |
| 12XXX | Agents (prod) |
| 13XXX | Support |
| 14XXX | Support / Other (test / non-prod) |
| 15XXX | Workstations |
| 16XXX | Templates |

---

## Windows agent build

### Proxmox VM configuration

- OS: **Windows Server 2019 Trial** ISO
- Two disks, **100 GB each**
- Machine type: **q35**; storage controller: **VirtIO SCSI**; BIOS: **SeaBIOS**
- Mount: Windows ISO + VirtIO-GPU driver image; enable QEMU guest agent checkbox
- CPU type: **host**
- Network: **VirtIO** NIC, VM bridge with VLAN enablement

### Post-OS-install setup

1. Set hostname to naming convention (use `Rename-Computer` in PowerShell if the Settings UI is uncooperative)
2. Set pagefile to **40 GB** on both `C:` and `D:`
3. Install **Python 3.8**
4. PowerShell: `Set-ExecutionPolicy Unrestricted`
5. Create virtual environment directory at `D:\agent\`
6. Copy agent code from GitHub into `D:\agent\`
7. Activate venv; run `pip install -r requirements.txt`
8. Configure `agent\config\config.json`: set `loop`, `number_of_threads`, `agent_id`, `client_id`, `client_secret`
9. Add SMB shortcut on desktop: `\\covenant.prod.site3.aldc\Storage` — credentials: `agent / {{COVENANT_AGENT_PASSWORD}}` (see `vault/infra-credentials.md` § Covenant credentials)
10. Install **NextCloud desktop client**:
    - Login: `agent@aldc.io` — password in `vault/infra-credentials.md` § NextCloud
    - Root directory: `D:\assets`
    - Sync scope: client tenants folder → `D:\assets`

---

## Linux agent build

1. Clone an existing Ubuntu Linux image from backup
2. Rename the VM — find/replace `template-agent-linux` with new VM name, then:
   ```bash
   hostnamectl set-hostname new-hostname
   ```
3. If necessary, install Python 3.8:
   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt-get update
   sudo apt-get install python3.8 python3.8-distutils
   sudo apt install python3-virtualenv
   ```
4. Update Ubuntu: `sudo apt-get upgrade`
5. Copy agent to `~/agent/`
6. Run the agent:
   ```bash
   cd ~/agent
   virtualenv venv -p python3.8
   source ./venv/bin/activate
   pip install -r requirements.txt
   # edit config/config.json
   python3.8 executor_master.py
   ```

### Linux systemd service commands

```bash
sudo systemctl start agent      # start
sudo systemctl stop agent       # stop
sudo journalctl -f -u agent     # tail logs
```

### SQL Server ODBC 18 on Ubuntu — known pitfall

Ubuntu has deprecated `apt-key`. Workaround for installing Microsoft ODBC 18 (run each line individually):

```bash
curl https://packages.microsoft.com/keys/microsoft.asc \
  | gpg --dearmor > /tmp/microsoft.gpg
sudo mv /tmp/microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg

curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list \
  | sudo tee /etc/apt/sources.list.d/mssql-release.list

sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

> Some servers require `;Encrypt=no` appended to the connection string.

---

## NextCloud client daemon — cluster pattern

Preferred: run **one NextCloud sync container per cluster/location** serving `Client_Tenants` as a Samba share on the local network. Agents mount the Samba share. This avoids per-agent client maintenance. See [[nextcloud]] § Agent VM integration.

Running the NextCloud client on every agent creates a "needy service" dependency that must be managed individually across the cluster.

---

## Agent backup

1. Log in to the appropriate Proxmox instance
2. Power off the agent VM
3. Select backup for the target machine
   - If no backups appear: check the CIFS share connection (see § CIFS reconnect below)
4. Use default backup configuration

### Move backup file

1. Connect to the Proxmox host via **FileZilla** SFTP (SSH/SCP port 22)
2. Navigate to `/var/lib/vz/dump`
3. Sort by last-modified; identify the correct `.zst` backup image
4. Download, then upload to the destination Proxmox host at `/var/lib/vz/dump`

### Redeploy from backup

1. On destination Proxmox: select the `.zst` backup → Restore
2. Assign a VM ID per the numbering scheme above
3. If bridge error: select **Network Device** in Hardware tab and choose available bridge
4. For Linux agents: follow the Linux build steps above after restore

### Backups stored on Covenant (CIFS)

Each Proxmox hypervisor mounts a CIFS share `Proxmox-<machine-name>` from Covenant (TrueNAS).

- CIFS credentials: `proxmox / {{COVENANT_PROXMOX_PASSWORD}}` — see `vault/infra-credentials.md` § Covenant credentials

### CIFS reconnect (if share goes offline)

The CIFS connection does **not** restore automatically after a drop. Re-establish via Proxmox Shell:

```bash
umount -f -a -t cifs -l
mount -t cifs
```

---

## Legacy agent process (Windows VMs)

Source: Confluence CORE/922550273 (Agent Virtual Machine (VM), 2023-08-22).

> *Created 2022-04-12, updated 2023-08-22. Agent process model predates Docker-based agents. Verify current state — Docker via Portainer is now the primary method.*

The legacy agent runs on Windows VMs. All files in versioned directories:

```
c:\aldc\agent_<yyyy-mm>\
├── executor_master.py   # Main agent process
├── config.json          # Configuration
└── venv\                # Python virtual environment
```

Use the newest `agent_<yyyy-mm>` directory.

### Start / stop

```cmd
cd c:\aldc\agent_<yyyy-mm>
.\venv\Scripts\activate     # (venv) appears in green when active
python executor_master.py
```

**Graceful stop:** Set `"loop": false` in `config.json` — agent finishes current task then exits.
**Force stop:** `Ctrl+C` (use only if stuck).

### Configuration keys (env vars override config.json)

| Key | Purpose |
|---|---|
| `agent_id` | Agent identity |
| `target_host` | core_api host |
| `loop` | `false` = stop after current task |
| `max_threads` | Concurrency limit |
| `client_id` / `client_secret` | API auth |
| `sleep` | Queue polling interval (ms) |
| `verbose` | Detailed logging |
| `parquet_max_days` | Parquet retention |

**Connectivity:** Access via [[connector-docker-deployment#deployment-via-portainer|Portainer]] (current); legacy AnyDesk/RDC is deprecated.

## See Also

- [[nextcloud]] — NextCloud asset sync; agent@aldc.io credentials
- [[local-network]] — Covenant (TrueNAS) storage; Tailscale VPN for remote access
- [[tailscale-linux]] — connecting to agent VMs remotely from Ubuntu
- [[aldc-naming-convention]] — VM naming pattern
- [[deployment-groups]] — each deployment group provisions an `agnt` Agent VM; VM 13XXX + 17XXX numbering
- [[connector-docker-deployment]] — Docker-based agent build + Portainer deployment (current primary method)
- `vault/infra-credentials.md` § Covenant credentials + § NextCloud — all agent VM credentials
