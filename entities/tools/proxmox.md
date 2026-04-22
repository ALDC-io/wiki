---
tags: [entity, tool, proxmox, infra, vm, hypervisor, gpu]
aliases: [Proxmox, Proxmox VE, Proxmox Hypervisor]
sources: [Confluence CORE/1043726358, CORE/1087340545, CORE/1160904705, CORE/1086881800]
created: 2026-04-18
updated: 2026-04-18
---

# Proxmox VE

ALDC's hypervisor platform for on-prem VM management. Runs on five physical servers (Nostromo, Sulaco, Patna, Auriga, Infinity) across Kamloops and Coquitlam sites. Admin portal on port 8006. Full host inventory and network topology: [[deployment-groups]] § Virtual Hosts & On-Prem Infrastructure.

---

## Host Administration

Source: Confluence CORE/1043726358 (2024-04).

### Network: Jumbo frames (MTU 9000)

Useful on isolated 10 Gb networks (e.g., VMBR09 backup bridge). Edit `/etc/network/interfaces`:

```
auto vmbr09
iface vmbr09 inet static
    address 192.168.39.80/24
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    pre-up ip link set eno1 mtu 9000
```

Or set MTU directly on the interface: `iface eno1 inet manual` + `mtu 9000`. Restart networking after changes.

### Package repos (no subscription)

Enterprise apt source will fail without a subscription. Switch to no-subscription repo — edit `/etc/apt/sources.list.d/pve-enterprise.list`:

```
# Comment out enterprise line, add:
deb http://download.proxmox.com/debian/pve bullseye pve-no-subscription
```

If `apt-get update` fails: `apt-get update --allow-releaseinfo-change`

### VM management

**Kill locked guest** (error "Can't lock file"):
```bash
rm /var/lock/qemu-server/lock-<VMID>.conf
```

**Useful shell commands:**
- `qm list` — view all VMs + stats
- `qm unlock <vmid>` — unlock stuck VM (e.g., after failed backup)
- `smartctl -a /dev/<device>` — S.M.A.R.T. disk info
- `apt install nvme-cli && nvme error-log /dev/<device>` — NVMe error log

### Storage

**ZFS stripe pool** (CLI — then add via UI: Datacenter → Storage):
```bash
zpool create <name> /dev/nvme0n1 /dev/nvme1n1 /dev/<other>
```

**Remove stale filesystem from disk** (e.g., moved from another host):
```bash
wipefs -af /dev/<device>
lvs          # list volume groups
vgremove <vg>  # remove stale VG (especially any with -OLD- suffix)
```

**Disk performance test** (all NVMe should exceed 1000 MB/s):
```bash
fio --ioengine=libaio --direct=1 --sync=1 --rw=read --bs=1M \
    --numjobs=1 --iodepth=1 --runtime=60 --time_based \
    --name seq_read --filename=/dev/nvme0n1
```

### IP address changes

1. SSH to host (or use iDRAC console if changing subnet/VLAN)
2. Edit `/etc/network/interfaces` — update `vmbr0` address + gateway
3. Edit `/etc/hosts` — update IP for hostname
4. **Do NOT rename the hypervisor**

### Fiber Channel

Nostromo and Covenant are connected via experimental QLogic 16 Gb/8 Gb FC SAN. To rescan for new FC targets/extents: see [unixarena.com FC rescan guide](https://www.unixarena.com/2013/06/how-to-scan-new-fc-luns-and-scsi-disks.html/).

---

## Guest Provisioning

Source: Confluence CORE/1087340545 (2024-02).

### Windows 10 VM

1. Create VM: machine type **q35**, storage **VirtIO SCSI** (NOT SATA/IDE), CPU type **host**
2. Mount: Windows 10 ISO + VirtIO-GPU driver ISO
3. **Disable balloon driver** (causes Windows performance issues)
4. Network: VirtIO device, VM bridge with VLAN support enabled
5. Hostname: `aldc<env>agnt<dg><region><seq>` (e.g., `aldctestagnt4c03`)
   - If Settings UI unresponsive: `Rename-Computer` via PowerShell
6. Install remaining VirtIO/QEMU drivers: [Proxmox Windows VirtIO Drivers](https://pve.proxmox.com/wiki/Windows_VirtIO_Drivers)

### Linux VM

1. Clone existing Ubuntu image from backup
2. Find/replace old hostname with new name throughout clone
3. Update hostname: `hostnamectl set-hostname <new-hostname>`

### Parsec console access

Cannot view Proxmox console while Parsec is active. If Parsec drops and you need console:

1. Remove PCI Device from VM hardware
2. Change Display from `none` → `Default`
3. Access console normally

**Revert to Parsec:** change Display back to `none`, re-add PCI Device.

**For new VMs** — set UUID in `/etc/pve/qemu-server/<vmid>.conf` to avoid Parsec licensing conflicts:
```
args: -uuid 00000000-0000-0000-0000-00000001<VMID padded to 4 digits>
```

### Expanding a guest disk

Source: Confluence CORE/1086881800 (2023-03).

> **WARNING:** Online ext4 resizing is not 100% safe — take a full backup or snapshot first. Expand the Proxmox disk first, then run steps below inside the guest.

1. **Resize partition** in parted:
   ```bash
   sudo parted /dev/sda
   (parted) unit s
   (parted) print free        # note last sector number
   (parted) resizepart 2      # accept in-use warning
   # enter last available sector from print (e.g., 2097151s)
   (parted) print free        # confirm
   (parted) quit
   ```

2. **Refresh kernel** partition table:
   ```bash
   lsblk /dev/sda
   # If still shows old size:
   sudo partprobe -s
   ```

3. **Grow filesystem:**
   ```bash
   sudo resize2fs /dev/sda2
   # If error: sudo e2fsck -f /dev/sda2 first, then retry
   ```

4. **Verify:** `df -h /dev/sda2`

> Prefer growing `/dev/sda` over adding a new `/dev/sdb` disk — if Proxmox added `/dev/sdb`, remove it and add capacity to `/dev/sda` instead.

---

## vGPU Configuration

Source: Confluence CORE/1160904705 (2024-12).

**Hardware:** Nostromo — 2× NVIDIA M40 24 GB GPUs. MDEV profile `nvidia-15` (6× 3.5 GB instances per GPU = 12 concurrent vGPU workstations total).

### Proxmox host setup

Follow [wvthoog/proxmox-vgpu-installer](https://github.com/wvthoog/proxmox-vgpu-installer).

### Windows vGPU license setup

1. Add UUID arg to VM config (`/etc/pve/qemu-server/<vmid>.conf`), replacing `15022` with actual VM ID:
   ```
   args: -uuid 00000000-0000-0000-0000-000000015022
   ```

2. Check MDEV usage per GPU — select least-loaded GPU:
   ```bash
   nvidia-smi   # run in Proxmox shell
   ```
   Set MDEV instance via PCIe passthrough in VM hardware settings.

3. Synchronize Windows system time to `server-ceres` (fastapi-dls licensing server at `192.168.30.103`), timezone: `America/Vancouver`.

4. Install Windows GRID driver from: `Storage\Software\Drivers\nVidia vGPU Drivers\Windows Client Drivers`

5. Acquire license token (PowerShell inside guest):
   ```powershell
   curl.exe --insecure -L -X GET https://192.168.30.103/-/client-token `
     -o "C:\Program Files\NVIDIA Corporation\vGPU Licensing\ClientConfigToken\client_configuration_token_$($(Get-Date).tostring('dd-MM-yy-hh-mm-ss')).tok"
   Restart-Service NVDisplay.ContainerLocalSystem
   & 'nvidia-smi' -q | Select-String "License"
   ```

**References:** [fastapi-dls](https://github.com/GreenDamTan/fastapi-dls) · [vGPU profiles](https://wvthoog.nl/proxmox-7-vgpu-v2/#Create_vGPU_profiles)

---

## See Also

- [[deployment-groups]] — host inventory (Nostromo/Sulaco/Patna/Auriga/Infinity), VM numbering (11XXX–17XXX)
- [[agent-builds]] — agent VM provisioning + backup/restore on Proxmox
- [[local-network]] — CIFS/Covenant storage, Tailscale VPN
- [[nextcloud]] — asset sync to agent VMs
