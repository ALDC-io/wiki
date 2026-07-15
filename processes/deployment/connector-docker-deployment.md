---
tags: [process, deployment, docker, connector, agents]
aliases: [connector deployment, Docker agent deployment, agent deployment]
sources: [sources/obsidian-import/general/Docker -Core Connectors - VMs.md, CORE/1074823173]
created: 2026-04-16
updated: 2026-07-15
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

### CRITICAL: Containers MUST run with `--privileged` mode

Agent containers mount a CIFS share from the co-located `agent-nextcloud` container at startup via `run.sh`:

```bash
mount -t cifs -o username=agent,password=$NEXTCLOUD_PASSWORD,domain=WORKGROUP \
  //agent-nextcloud/nextcloud /media/nextcloud
```

This requires `SYS_ADMIN` capability. **If the container is not privileged, the mount fails silently** — the agent starts and appears healthy, but `/media/nextcloud/` is empty. All templates reading CSV supplement files will fail with `[Errno 2] No such file or directory`.

**When deploying via Portainer:** Duplicate/Edit → Capabilities tab → enable **Privileged mode**.

**When deploying via CLI:**
```bash
docker run -d --name <name> --restart unless-stopped \
  --network agent-bridge \
  --privileged \
  --cap-add SYS_ADMIN --cap-add DAC_READ_SEARCH \
  --env-file env_vars \
  ghcr.io/aldc-io/agent-<name>:master
```

**To verify a running container has the correct privileges:**
```bash
docker inspect <container> --format 'Privileged={{.HostConfig.Privileged}} CapAdd={{.HostConfig.CapAdd}}'
# Expected: Privileged=true
```

**Note:** Portainer web exec console does NOT inherit SYS_ADMIN even in a privileged container. Mount commands from exec will fail with "Unable to apply new capability set." — use a container restart instead.

### Samba password must match NEXTCLOUD_PASSWORD env var

The `agent-nextcloud` container runs `smbd` and serves the NextCloud data as a Samba share. The Samba password for the `agent` user must match the `NEXTCLOUD_PASSWORD` env var in the agent container (currently `ALDCAgent007_`).

If auth fails (`NT_STATUS_LOGON_FAILURE` from smbclient), reset the Samba password from inside the `agent-nextcloud` container:

```bash
(echo "ALDCAgent007_"; echo "ALDCAgent007_") | smbpasswd -s agent
```

Verify Samba is running: `pgrep -la smbd` (should show 2 `smbd -D` processes).

### CSV supplement files must be UTF-8 (or the whole file is silently dropped)

The legacy `BaseConnectorFlat` CSV reader (`connector/base/base_connector_flat.py`) historically opened files as UTF-8 only. **Client-exported CSVs are frequently Windows-1252** (Excel / Google Sheets on Windows) — a single accented character (`é`, `ñ`, smart quotes) raised `UnicodeDecodeError` and aborted the entire file before any row parsed → no stage, no merge, and the exception was swallowed (schedule marked complete, no alert). The downstream `SUPPLEMENT.*_CSV` table simply stays stale while sibling CSV templates keep refreshing.

Symptom to recognize: one CSV supplement table frozen (`last_altered` behind its siblings) with the agent logs showing `OPENING FILE …` but **no** `FIELDS`/`SCHEMA`/`SESSION INIT` for its category.

Fixed in [[GP-286]] — the reader now falls back `utf-8-sig → cp1252 → latin-1` and raises on a zero-row parse. If you see this on an agent running an image built before 2026-07-07, rebuild + recreate the container (this page), or re-encode the offending file to UTF-8 as an immediate unblock.

### Docker Login Issues
If the build fails to push to the container registry:
```bash
export DOCKER_CLI_TOKEN=<token from github>
echo $DOCKER_CLI_TOKEN | sudo docker login ghcr.io --username <github-username> --password-stdin
```

**Important**: Use `sudo` before the docker login or the pipe may send the token to the sudo password prompt. Use `aldc-svc-automation` account, or a personal token if problems persist.

**GHCR push token expires on `wks-agent` (recurring).** `build.sh` runs `docker build` (fine) then `docker push`, and the push can `403: unauthorized: unauthenticated` because the cached GHCR credential on the box has gone stale — even though the image built cleanly (it's sitting locally, just not uploaded). Fix = re-auth and re-push (no rebuild needed):
```bash
echo '<token>' | docker login ghcr.io -u aldc-svc-automation --password-stdin   # token: vault § Docker / GHCR service account (no-expiry, regen 2026-05-04)
docker push ghcr.io/aldc-io/agent-<name>:<tag>
```
`docker` runs **without sudo** on `wks-agent` (aldc is in the docker group) — so run `build.sh` unprivileged to avoid the sudo-password-vs-stdin problem entirely (observed 2026-07-15, GP-287).

### `wks-agent` SSH is fail2ban-prone — space your connections
Several SSH connections in quick succession (~5 in <1 min) trip fail2ban (connection **reset**, then **timeout** for ~10 min). Space connections out, **batch commands into a single `ssh`**, and don't rapid-retry. For build completion, **poll the GHCR REST API off-box** instead of SSH-tailing the build log:
```bash
gh api "orgs/ALDC-io/packages/container/agent-<name>/versions" --jq '.[] | select(.metadata.container.tags[]? == "<tag>") | .updated_at'
```
(watch the tag's `updated_at` advance). `build.sh` prompt tip: answer **dev-image = N** and give a **version** string → clean tag `agent-<name>:<version>`; a branch name containing `/` breaks the docker tag. (GP-287, 2026-07-15.)

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
