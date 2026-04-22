---
tags: [process, operations, tailscale, vpn, linux, ubuntu, remmina]
aliases: [Tailscale Linux, Tailscale Ubuntu, Connect VM Tailscale Linux]
sources: [Confluence INFRA/1050673157]
created: 2026-04-18
updated: 2026-04-18
---

# Connecting to a VM via Tailscale (Ubuntu)

How to install Tailscale on Ubuntu and remote-desktop into a Windows VM over the ALDC Tailscale network.

## Steps

### 1. Install Tailscale on your Linux machine

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

### 2. Authenticate

```bash
sudo tailscale up
```

Authenticate with your ALDC email when prompted.

### 3. Install Tailscale on the target VM

Install the Windows Tailscale client on the target VM and authenticate with your ALDC email.

### 4. Get the target VM's IPv4 address

On the target VM (PowerShell):

```powershell
ipconfig
```

Note the IPv4 address.

### 5. Verify connectivity from Linux

```bash
tailscale status            # confirm target appears in the peer list
tailscale ping <IPv4>       # confirm reachability
```

### 6. Connect via Remmina

- Open **Remmina** (Ubuntu default remote desktop client)
- Click **New connection profile** (top-left)
- Enter a name; paste the IPv4 address into the **Server** field
- Save and connect
- Enter the Windows VM username and password when prompted

## See Also

- [[local-network]] — Tailscale network overview; `kookiet` is the subnet router for NextCloud/TrueNAS
- [[agent-builds]] — Agent VMs run Windows Server 2019; this method is used for headless setup access
