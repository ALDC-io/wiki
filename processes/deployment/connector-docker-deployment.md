---
tags: [process, deployment, docker, connector, agents]
aliases: [connector deployment, Docker agent deployment, agent deployment]
sources: [sources/obsidian-import/general/Docker -Core Connectors - VMs.md, CORE/1074823173]
created: 2026-04-16
updated: 2026-04-18
---

# Connector Docker Deployment

End-to-end process for building and deploying [[Eclipse]] connector agents as Docker containers. Agents run on VMs managed via Portainer.

## Environments

| Environment | Servers | Agents per Server | Notes |
|-------------|---------|-------------------|-------|
| Test | 1 | 4 | |
| Prod Kamloops | 1 | 4 | Separate image from Coquitlam |
| Prod Coquitlam | 1 | 3 | Separate image from Kamloops |
| QA | 1 | 1 | |

## Prerequisites

- SSH access to `aldc@workstation-agent` (build server)
- SSH access to target deployment server
- Docker CLI logged into `ghcr.io` (ALDC GitHub Container Registry)
- Portainer access for the target environment

## Step 1: Build the Docker Image

```bash
ssh aldc@workstation-agent
cd docker_build/agent-template-env
cp <desired-config>.json config.json
```

Config files vary by environment (`config-test.json`, etc.). Before building, verify:
- `sleep = 600`
- `thread_timeout = 3600`
- `max_threads > 1`
- `target_host` matches the correct environment URL

```bash
sudo ./build.sh
```

You'll be prompted for:
1. **Agent name**: e.g., `dcgeneral`
2. **Branch**: `master` or a version tag like `1.24.0`
3. **Version**: e.g., `1.24.0`
   - Same name overwrites the existing image
   - For intermediate builds, use `1.24.1` or `1.24.0-itm-250` to keep both versions

The build script also pushes to the container registry. Verify at:
`https://github.com/orgs/ALDC-io/packages/container/package/agent-dcgeneral`

**If deploying to Prod**: build separate images for Kamloops and Coquitlam (different configs).

## Step 2: Deploy to Target Server

```bash
ssh aldc@<target-server-URL>
cd docker_assets/images/agent_template
```

For each agent (repeat 1-4 times depending on environment):

1. **Stop the old agent** in Portainer. Keep it as backup; delete the previous backup if stable.
2. **Run the deploy script**:
   ```bash
   sudo ./run.sh
   ```
3. Set the **image name**: e.g., `agent-dcgeneral:1.24.0`
4. Set the **container name**: follows pattern `agent<n>-<version>`, e.g., `agent1-1.24.0`
5. **For normal agents**: just hit Enter when asked for options
6. **For GEP SellerCloud VPN agent**:
   - Enter option name: `openvpn`
   - Enter values from Dashlane secret for `gep-sellercloudvpn`
   - Type `exit` when done

## Step 3: Verify

- Check agent logs in Portainer for healthy startup
- Confirm agents are picking up work items

## Pitfalls / Gotchas

### Docker Login Issues
If the build fails to push to the container registry:
```bash
export DOCKER_CLI_TOKEN=<token from github>
echo $DOCKER_CLI_TOKEN | sudo docker login ghcr.io --username <github-username> --password-stdin
```

**Important**: Use `sudo` before the docker login or the pipe may send the token to the sudo password prompt. Use `aldc-svc-automation` account, or a personal token if problems persist.

### Server Path Differences
The `docker_assets/images/agent_template` path may vary by server. Each server is set up slightly differently.

### VPN Agents
The GEP SellerCloud SQL agent requires OpenVPN configuration. Credentials are in Dashlane under the `gep-sellercloudvpn` entry.

## Docker Reference

Source: Confluence CORE/1074823173 (Docker Guides, 2025-04-15).

### Core concepts

Docker shares the host OS kernel — it is not a VM. Linux containers require a Linux host; Windows containers require Windows. **Images** are blueprints; **containers** are running instances (ephemeral); **volumes** provide persistent storage outside container lifecycle.

### Build & run

```bash
sudo docker build -t <tag> -f <dockerfile> .
sudo docker run --memory=16G --cpus=8 -d --name <name> --network bonded <image>
sudo docker exec -it <name> bash
sudo docker logs -f --tail 10 <name>
```

### MACVLAN networking

Bonds containers directly to the physical network with their own MAC + IP on the local subnet:

```bash
sudo docker network create -d macvlan \
  --subnet=192.168.46.0/24 --gateway=192.168.46.1 \
  --ip-range 192.168.46.160/26 \
  -o parent=enp6s19 bonded
```

`--ip-range` is the CIDR pool Docker manages (must not conflict with DHCP). `--parent` is the physical adapter.

### Volume (bind mount)

```bash
sudo docker volume create --driver local \
  --opt type=none --opt device=/home/aldc/agent/volume --opt o=bind agent_volume
```

### Samba access to volume from Windows

```bash
sudo apt install samba -y && sudo smbpasswd -a aldc
# Add to /etc/samba/smb.conf:
# [agent_volume]
# path = /home/aldc/agent/volume
# valid users = aldc
# writable = yes
sudo ufw allow 445 && sudo ufw allow 135:137/tcp && service smbd restart
# Access: \\<host.fqdn>\agent_volume
```

### GHCR (GitHub Container Registry)

Images stored at org level (`ghcr.io/aldc-io/<package>:<version>`).

```bash
sudo docker login ghcr.io --username <GITHUB_USER>
sudo docker tag <IMAGE_ID> ghcr.io/aldc-io/<package>:<version>
sudo docker push ghcr.io/aldc-io/<package>:<version>
```

Service account: `aldc-svc-automation` — token and password in `vault/infra-credentials.md` § Docker / GHCR service account. Token expires 90 days from creation; check Dashlane if expired.

### Postgres local dev restore

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:latest
    environment:
      POSTGRES_DB: portal
      POSTGRES_USER: aldcportal
      POSTGRES_PASSWORD: "{{POSTGRES_DOCKER_PASSWORD}}"  # vault/infra-credentials.md § Docker
    ports: ["14301:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
```

```bash
# Dump from QA Azure Postgres
pg_dump -h aldcqapgdbportal1c01.postgres.database.azure.com -U aldcportal -d portal -F c -f backup.dump
# Restore to local Docker instance
pg_restore -h 192.168.36.71 -p 14301 -U aldcportal -d portal --no-owner --if-exists --no-acl -c backup.dump
```

## See Also

- [[Eclipse]] — the connector platform these agents run
- [[data-pipeline-flow]] — agents' role in the pipeline
- [[connector-timeout-outage]] — outage caused by agent `/work/pick` scaling issue
- [[agent-builds]] — Proxmox VM provisioning for Docker agent hosts
- [[deployment-groups]] — Docker node inventory per environment
