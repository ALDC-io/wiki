---
tags: [ticket, gep, fusion92, infrastructure, connector, operations, resolved, incident]
aliases: [GP-269, GP-PENDING-infra-connector-failures, Infra Connector Failures, NFS Mount Missing, SQL Server Unreachable, Eclipse Core API DNS]
sources: []
created: 2026-05-22
updated: 2026-05-27
first_alerted: ~2026-05-09
---

# GP-PENDING — Infrastructure & Connector Failures (Multi-Issue)

Four long-running infrastructure failures discovered 2026-05-22 during investigation of a GEP/Navira missing sales data incident. All issues pre-date the sales incident (which was a suspended Snowflake task chain — a separate matter). These failures have been silently degrading data quality for 13–27+ days.

## Status

`resolved` — GP-269 closed 2026-05-25. All GEP issues resolved and stable for 3+ days. Backup containers removed from Kamloops + Coquitlam. Issue 4B (Viant DSP IP whitelist) split to [[FU92-418]].

### Resolution Log (2026-05-22)

**Issue 1 — NextCloud/NFS Mount: RESOLVED**
- **Root cause:** Agent containers on both Coquitlam (`0c2ff15f18f2`) and Kamloops (`agent-dcgeneral-master`) were deployed via Portainer **without `--privileged` mode**. The `run.sh` startup script calls `mount -t cifs` which requires `SYS_ADMIN` capability — without it, the mount fails silently and the agent runs against an empty `/media/nextcloud/`.
- **Secondary issue:** Samba password in the `agent-nextcloud` containers' passdb did not match the `NEXTCLOUD_PASSWORD` env var (`ALDCAgent007_`). Reset via `smbpasswd -s agent` on both hosts.
- **Fix:** Recreated agent containers on both Coquitlam and Kamloops with `--privileged` mode enabled via Portainer. CIFS mounts confirmed working on both hosts. All 10 templates will resume on next scheduled run.

**Issue 2 — SQL Server DNS: RESOLVED 2026-05-27**
- **Root cause:** Docker's internal DNS resolver (`127.0.0.11` in the container's `/etc/resolv.conf`) cannot resolve ALDC's local domain `*.prod.site3.aldc`. The Eclipse connection uses the FQDN `galactica.prod.site3.aldc` (not the IP `192.168.35.138`), so ODBC login times out at the DNS stage. The 2026-05-22 TCP test was a **false negative** — it tested via IP directly, not the FQDN, so it passed while templates continued to fail.
- **Why Kamloops works:** The Kamloops agent (`192.168.35.70`) is on the same subnet as Galactica (`192.168.35.138`) and has local DNS that resolves `.prod.site3.aldc`. Coquitlam (`192.168.22.70`) is cross-site and lacks this DNS.
- **Fix:** Recreated `agent-dcgeneral-coquitlam-master` container with `--add-host galactica.prod.site3.aldc:192.168.35.138`. This injects the mapping into the container's `/etc/hosts` and survives container restarts. Verified: DNS resolves, TCP connects, ODBC authenticates and queries successfully. NFS mount also healthy.
- **Backup:** Old container preserved as `agent-dcgeneral-coquitlam-master-backup-pre-dnsfix`.
- **SSH keys:** Installed ed25519 key-based auth on both Coquitlam (`192.168.22.70`) and Kamloops (`192.168.35.70`) for passwordless access from Paul's workstation.
- **Recurrence note:** This is the 10th occurrence of this root cause per observability alerts. The `--add-host` flag makes it durable across container restarts, but any future container recreation (e.g. env var update via Portainer) must preserve the `--add-host` or the issue will return. Consider adding `galactica.prod.site3.aldc` to the Docker host's DNS or adding an `extra_hosts` entry to the Portainer stack/template.

**Issue 3 — Eclipse Core API DNS: SELF-RESOLVED**
- Both `api.eclipse.analyticlabs.io` and `aldcprodfnapcore1c01.azurewebsites.net` resolve correctly. Transient DNS blip; no action needed.

**Issue 4 — Fusion92 Credentials: BLOCKED (investigated 2026-05-22)**

**4A — Microsoft Ads Azure AD Client Secret: RESOLVED 2026-05-22**
- **Root cause:** Both client secrets on Azure AD app registration `98fe3659-b606-4550-9b16-c5e51a792618` expired (March 21 + March 28, 2026). Automated daily refresh stopped → 100% connector failure.
- **Fix:** New secret "Eclipse Secret 2026-05-22" created (24-month expiry → 2028-05-22). Paul granted app ownership by Global Admin, secret created via Graph API.
- **Token refresh:** Existing refresh token (55 days old) was still valid. Two-cycle refresh completed, CosmosDB connection document updated with fresh token.
- **Agent containers:** Both recreated via Portainer API with new `MICROSOFT_ADS_CLIENT_SECRET`:
  - Kamloops (KA1): `agent-dcgeneral-master` — running, Privileged=True preserved
  - Coquitlam (VA1): `agent-dcgeneral-coquitlam-master` — running, Privileged=True preserved
  - Old containers kept as `*-backup-pre-envupdate` for rollback
- **Secret stored:** Wiki `vault/infra-credentials.md` — § Microsoft Ads
- **Tooling built:**
  - `scripts/_renew_msads_secret.py` — verify + refresh + CosmosDB update
  - `scripts/_check_credential_expiry.py` — tenant-wide expiry audit (found 38 expired + 1 expiring in 2 days)
  - `scripts/_update_agent_env.py` — safe container env var update with config preservation + rollback
- **Production verified:** 60 partitions queued manually via Eclipse, 3,233+ completed successfully. Zero expired-secret errors post-fix. Transient failures (tmp file collisions, timeouts) are normal and auto-retry.
- **Remaining:** Remove backup containers (`*-backup-pre-envupdate`) on both hosts once stable for 24h

**4B — Viant DSP Snowflake IP Whitelist: BLOCKED on Fusion92 (investigated 2026-05-22)**
- **Account ownership confirmed:** `zj81514` (`central-us.azure`) is **Fusion92/Viant-managed**, not ALDC. ALDC has a reader account (`ALDC_Reader`) provisioned for the Reach and Frequency connector.
- **IP block confirmed:** Tested from ALDC office IP (`173.180.33.21`) — same block. Strict network policy rejects all non-whitelisted IPs. Error: "Incoming request with IP/Token is not allowed to access Snowflake."
- **Credentials valid:** Not an auth failure — purely IP policy. Username/password not revoked.
- **Prior state:** Connector was working (data from Nov 2024+). Something changed on Fusion92/Viant's side ~27 days ago.
- **Connection:** `zj81514.central-us.azure.snowflakecomputing.com`, database `VIANT`, schema `DATA`, warehouse `COMPUTE_WH`, user `ALDC_Reader`, connection ID `2ee1d143-419f-4169-8185-546ca3aadbbc`.
- **Action:** Contact Fusion92 → whitelist agent IP `50.98.149.51` + optionally ALDC office `173.180.33.21`. Ask what changed.

## Summary of Issues

| # | Issue | Clients Affected | Duration | Severity |
|---|---|---|---|---|
| 1 | Nextcloud/NFS mount missing on dcgeneral-coquitlam | GEP (8 templates), Fusion92 (2 templates) | 13+ days (~2026-05-09) | High |
| 2 | On-prem SQL Server unreachable | GEP (2 templates), Fusion92 (5 templates) | 13–14+ days (~2026-05-08) | High |
| 3 | Eclipse Core API DNS failure | All clients | ~hours (reported 2026-05-22 08:52 PT) | Critical |
| 4 | Fusion92 credential failures | Fusion92 (Microsoft Ads + Viant DSP) | 27+ days | High |

---

## Issue 1 — Nextcloud/NFS Mount Missing on dcgeneral-coquitlam

### Description

Agent `dcgeneral-coquitlam` (container `0c2ff15f18f2`) has a missing Nextcloud/NFS mount at `/media/nextcloud/`. All connectors that read CSV supplement files from this path are failing at 100% error rate.

**Error:**
```
[Errno 2] No such file or directory: '/media/nextcloud/Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV SUPPLEMENT/...'
```

### Affected Templates

**GEP CSV Supplement templates (5 — 100% failure rate):**
- Forecast with Type
- Marketplace Name
- Company Name
- State Names
- Marketplace Config

**GEP Supplement templates (3 — 100% failure rate):**
- Account Managers
- Sellercloud Channel Map
- SKU Kits

**Fusion92 templates (2 — 100% failure rate):**
- Flight Check - Flights
- Flight Check - Jobs

### Data Impact

All GEP CSV-driven dimensions are stale since ~2026-05-09. This includes marketplace metadata (`Marketplace Name`, `Marketplace Config`), state name lookups, company names, and SKU kit mappings. Any report relying on these supplement tables will have gaps or stale values.

Fusion92 Flight Check data (Flights + Jobs) is also stale for 13+ days.

### Suggested Remediation

1. SSH to `dcgeneral-coquitlam` and verify whether the Nextcloud sync daemon is running: `systemctl status nextcloud-client` (or equivalent)
2. Check if the mount point `/media/nextcloud/` exists and is populated: `ls /media/nextcloud/`
3. If the daemon crashed, restart it and verify mount re-populates
4. If the mount is empty, check Nextcloud server connectivity from the agent VM
5. Once mount is restored, manually re-run or reschedule all 10 affected templates to backfill data
6. Check [[agent-builds]] for the Nextcloud cluster daemon pattern on Agent VMs
7. Consider adding a mount-health check to [[observability-platform]] — a missing `/media/nextcloud/` should alert before connectors start failing

### See Also

- [[nextcloud]] — ALDC Cloud file sharing; Nextcloud cluster daemon pattern
- [[agent-builds]] — Proxmox Agent VM provisioning and Nextcloud cluster daemon setup
- [[observability-platform]] — Monitoring platform; candidate location for mount-health alert

---

## Issue 2 — On-Prem SQL Server Unreachable

### Description

Multiple Eclipse connectors targeting an on-prem SQL Server are failing with ODBC login timeout errors. The SQL Server has been unreachable for 13–14+ days.

**Error:**
```
('HYT00', '[HYT00] [Microsoft][ODBC Driver 18 for SQL Server]Login timeout expired (0) (SQLDriverConnect)')
```

### Affected Templates

**GEP templates (2):**
- Calendar
- Financial Currency

**Fusion92 templates (5):**
- Financial Currency
- Geography Country
- KPI Periodicity
- Time Calendar
- Time Time

### Data Impact

GEP financial currency data is stale; calendar/time dimension data is stale. Fusion92 time and periodicity dimensions are stale — these feed into financial and performance reporting. Any aggregation relying on time-grain lookups will silently return stale or incorrect results.

### Actual Resolution (2026-05-27)

**Connection config:** `clients/GEP/eclipse/connections/sql_server.json` — server `galactica.prod.site3.aldc`, database `ALDC_LIBRARY`, user `eclipse`, connector `sqlserver_v1`, connection ID `5b6336a4-5c49-483d-b281-eee8ad315e22`.

**Diagnostic steps that identified the root cause:**
1. `docker exec` into agent container → `python3 socket.getaddrinfo("galactica.prod.site3.aldc", 1433)` → `Name or service not known` (DNS failure)
2. `cat /etc/resolv.conf` → only `nameserver 127.0.0.11` (Docker internal DNS, no ALDC domain knowledge)
3. TCP test via IP `192.168.35.138:1433` → OK (SQL Server is healthy)
4. Confirmed Kamloops agent resolves the FQDN natively (same-subnet DNS)

**Fix applied:**
```bash
docker stop agent-dcgeneral-coquitlam-master
docker rename agent-dcgeneral-coquitlam-master agent-dcgeneral-coquitlam-master-backup-pre-dnsfix
docker run -d --name agent-dcgeneral-coquitlam-master --network agent-bridge \
  --restart unless-stopped --privileged --workdir /app/agent \
  --add-host galactica.prod.site3.aldc:192.168.35.138 \
  [env vars preserved from original] \
  ghcr.io/aldc-io/agent-dcgeneral-coquitlam:master /bin/sh -c "/app/scripts/run.sh"
```

**Post-fix verification:** DNS resolves, ODBC connects and queries, NFS mount healthy, `ExtraHosts: ["galactica.prod.site3.aldc:192.168.35.138"]` confirmed in container config.

**Host-level fix (2026-05-27):** Added `192.168.35.138 galactica.prod.site3.aldc` to `/etc/hosts` on the Docker host `aldcproddock1c03` (`192.168.22.70`) itself. This means all future containers on this host inherit the mapping automatically — even if someone recreates the agent container without `--add-host`, DNS will still resolve via the host's `/etc/hosts`. This is the belt-and-suspenders fix that prevents the 10th+ recurrence.

**SSH key auth (2026-05-27):** Installed ed25519 key-based SSH auth on both Docker hosts (`aldc@192.168.22.70` and `aldc@192.168.35.70`) from Paul's workstation. Future on-prem investigations will not require repeated password entry.

### Remediation Runbook (for future recurrence)

1. Check if the container has `ExtraHosts` set: `docker inspect <container> --format "{{json .HostConfig.ExtraHosts}}"`
2. If empty, the container was recreated without `--add-host` — recreate with it
3. Always test DNS resolution using the FQDN, not the IP — the IP test gives false negatives for this class of issue
4. Any container recreation on Coquitlam must include `--add-host galactica.prod.site3.aldc:192.168.35.138`
5. ~~Long-term: add `galactica.prod.site3.aldc` to Docker host-level DNS (`/etc/hosts` on `aldcproddock1c03`) or configure a proper DNS server for `.prod.site3.aldc` domain~~ **DONE 2026-05-27** — entry added to `/etc/hosts` on `aldcproddock1c03`. All containers now inherit this mapping. The per-container `--add-host` is still good practice as defense-in-depth.

### See Also

- [[local-network]] — On-prem network; Galactica at `192.168.35.138` on Nostromo (Kamloops)
- [[agent-builds]] — Agent VM setup; ODBC Driver 18 noted for Ubuntu workaround
- [[observability-platform]] — Monitoring; SQL Server connectivity should be a named probe
- `clients/GEP/eclipse/connections/sql_server.json` — Eclipse connection config for Galactica

---

## Issue 3 — Eclipse Core API DNS Failure

### Description

Two Eclipse Core API endpoints are returning DNS resolution failures. Reported 2026-05-22 at 08:52 PT. This is an acute failure — duration unknown but likely short (hours).

**Errors:**
```
[eclipse-2-core-api] Down: getaddrinfo ENOTFOUND api.eclipse.analyticlabs.io
[core-api] Down: getaddrinfo ENOTFOUND aldcprodfnapcore1c01.azurewebsites.net
```

### Affected Systems

- `api.eclipse.analyticlabs.io` — Eclipse 2 Core API public endpoint (Cloudflare DNS → Azure)
- `aldcprodfnapcore1c01.azurewebsites.net` — core_api Azure App Service direct hostname

### Data Impact

If Core API is unreachable, Eclipse cannot execute connector tasks (templates call core_api for work pickup via `/work/pick`). All active connector runs would fail until resolved. This may be intermittent or transient — confirm current status before escalating.

### Suggested Remediation

1. Check Azure Portal → App Services → `aldcprodfnapcore1c01` — confirm the app is running and not stopped/crashed
2. Check [[GitHub Actions]] → recent deployments — confirm no failed deployment left the app in a broken state
3. Test DNS resolution from outside: `nslookup api.eclipse.analyticlabs.io` — confirm Cloudflare DNS record is intact (see [[Cloudflare]])
4. If the Azure app is healthy but DNS is failing, check Cloudflare CNAME record for `api.eclipse.analyticlabs.io` points to `aldcprodfnapcore1c01.azurewebsites.net`
5. Check [[observability-platform]] — this alert was already triggered; confirm it is still active or self-resolved
6. If the app itself crashed, check Azure App Service logs and restart

### See Also

- [[core_api]] — ALDC core API service; production hostname `aldcprodfnapcore1c01`
- [[Cloudflare]] — DNS; `api.eclipse.analyticlabs.io` CNAME lives here
- [[eclipse-azure-deployment]] — Deploy/rollback procedure for Eclipse + core_api
- [[observability-platform]] — Uptime Kuma alert source for this incident
- [[aldc-naming-convention]] — Hostname decode: `aldcprodfnapcore1c01` = ALDC Prod Function App Core 1 Canada 01

---

## Issue 4 — Fusion92 Credential Failures (27+ Days)

### Description

Two Fusion92 connector credentials have been expired or blocked for 27+ days, causing 100% failure rates on those connectors.

### 4A — Microsoft Ads: Azure AD Client Secret Expired

**Client app:** `98fe3659-b606-4550-9b16-c5e51a792618`
**Failure rate:** 178/178 (100%)
**Duration:** 27+ days

The Azure AD app registration's client secret used to authenticate the Microsoft Ads (Bing Ads) connector has expired. All 178 attempted runs have failed.

**Remediation:**
1. Go to Azure Portal → Azure Active Directory → App registrations → find `98fe3659-b606-4550-9b16-c5e51a792618`
2. Under Certificates & secrets, generate a new client secret (note expiry date — recommend 24 months)
3. Update the secret in the Eclipse connection config for the Fusion92 Microsoft Ads connection
4. Update `vault/credentials.md` with the new secret and new expiry date
5. Check [[powerbi-secret-refresh]] for the analogous PBI secret refresh procedure — follow the same pattern for expiry-date tracking
6. Verify the new secret works by manually triggering a connector run
7. Add an expiry alert to [[observability-platform]] for Azure AD client secrets

**See Also:** [[bing-ads]] — Microsoft Advertising connector; 90-day refresh token lifecycle; [[connector-token-refresh]] — OAuth token refresh runbook

### 4B — Viant DSP: Snowflake Network Policy Blocking Connector IP

**Connector IP:** `50.98.149.51`
**Snowflake account:** `zj81514`
**Failure rate:** 271/271 (100%)
**Duration:** 27+ days

A Snowflake network policy on the Viant DSP account `zj81514` is blocking the connector's egress IP `50.98.149.51`. All 271 runs have failed.

**Remediation:**
1. Identify who owns the `zj81514` Snowflake account — this may be a Fusion92-managed or Viant-managed Snowflake instance
2. If ALDC-managed: go to Snowflake → `zj81514` → Admin → Security → Network Policies and add `50.98.149.51` to the allowed IP list
3. If client-managed: contact Fusion92 / Viant to request the connector IP be whitelisted
4. Verify IP `50.98.149.51` is stable — if this is an on-prem agent IP that rotates, investigate using a static NAT/egress IP
5. Once whitelisted, trigger a manual connector run to confirm access

**Note:** This may be related to [[FU92-394]] / [[FU92-416]] (Viant connector history). Check those pages for prior Viant connectivity work before engaging Fusion92.

**See Also:** [[fusion92]] — Fusion92 client entity; [[FU92-394]] — prior Viant connector outage; [[FU92-416]] — Viant auth token lifespan investigation

---

## Priority Ordering

| Priority | Issue | Rationale |
|---|---|---|
| P1 | Issue 3 — Eclipse Core API DNS | Acute, blocks ALL connectors if active. Confirm/resolve immediately. |
| P2 | Issue 1 — NFS Mount Missing | 10 templates down, 13+ days of stale data; quick fix (restart daemon) if mount is the only problem |
| P3 | Issue 2 — SQL Server Unreachable | 7 templates down, 13+ days; fix depends on network/server ownership |
| P4 | Issue 4 — Fusion92 Credentials | 27+ days stale; Azure AD secret is a fast fix; Viant IP whitelist may require client coordination |

## Impact Assessment

| Client | Data Stale Since | Stale Datasets |
|---|---|---|
| GEP | ~2026-05-09 | Marketplace Name, Marketplace Config, Forecast with Type, Company Name, State Names, Account Managers, Sellercloud Channel Map, SKU Kits, Calendar, Financial Currency |
| Fusion92 | ~2026-05-09 (NFS); ~2026-05-08 (SQL); ~2026-04-25 (creds) | Flight Check Flights/Jobs, Financial Currency, Geography Country, KPI Periodicity, Time Calendar, Time Time, Microsoft Ads actuals, Viant DSP actuals |

## Next Steps

- [x] ~~Confirm Issue 3 (Core API DNS) is still active or self-resolved~~ — self-resolved (transient)
- [x] ~~SSH to `dcgeneral-coquitlam` and restore Nextcloud mount (Issue 1)~~ — resolved 2026-05-22
- [x] ~~Identify and restore on-prem SQL Server connectivity (Issue 2)~~ — likely self-healed; monitoring
- [x] ~~File as Jira ticket~~ — GP-269 created and updated. Transitioned Development → QA (2026-05-22) with structured status comment.
- [x] ~~Get Global Admin to create new Azure AD client secret~~ — Paul granted app ownership, secret created via Graph API (2026-05-22)
- [x] ~~Run `python scripts/_renew_msads_secret.py refresh <secret>`~~ — completed 2026-05-22, CosmosDB updated
- [x] ~~Update Portainer env vars on Coquitlam + Kamloops agent containers~~ — completed 2026-05-22 via `_update_agent_env.py`
- [x] ~~Determine ownership of Snowflake account `zj81514`~~ — Fusion92/Viant-owned, confirmed 2026-05-22
- [x] ~~Verify Microsoft Ads connector success~~ — 3,233+ partitions completed successfully 2026-05-22
- [x] ~~Update Dashlane entries~~ — secret + refresh token updated 2026-05-22
- [ ] Remove backup containers (`*-backup-pre-envupdate`) on Kamloops + Coquitlam after 24h stability
- [ ] **BLOCKED:** Whitelist request sent to Fusion92 via Lori + Support (CC Mike Stuart) 2026-05-22. Awaiting response. Agent IP `50.98.149.51` on Snowflake account `zj81514` (Issue 4B)
- [x] ~~Renew ALDC Email MCP Server secret before 2026-05-25~~ — new secret `ALDC Email MCP_26_05_24` created by JK 2026-05-23 (expires 2028-05-22). Recorded in `vault/infra-credentials.md`. ALDC-175 created for automated expiry monitoring.
- [ ] Review 38 expired tenant secrets for cleanup or renewal

## See Also

- [[observability-platform]] — Source of alerts; all four issues were surfaced here
- [[observability-architecture]] — Alert system design; staleness detection
- [[nextcloud]] — Nextcloud file sharing; NFS/cluster daemon pattern
- [[agent-builds]] — Agent VM provisioning; Nextcloud daemon setup
- [[local-network]] — On-prem topology; SQL Server connectivity paths
- [[GEP]] — GEP/Navira client entity
- [[fusion92]] — Fusion92 client entity
- [[FU92-394]] — Prior Viant DSP outage (connector timeout; now potentially blocked by IP policy)
- [[FU92-416]] — Viant auth token lifespan investigation
- [[connector-token-refresh]] — OAuth token refresh runbook; Microsoft Ads 90-day cycle
- [[bing-ads]] — Microsoft Advertising connector details
- [[GP-PENDING-data-share-stability]] — Related infrastructure-health ticket (share gap detection)
