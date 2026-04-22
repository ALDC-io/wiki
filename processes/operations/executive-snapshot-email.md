---
tags: [process, operations, email, automation, cron]
aliases: [Executive Snapshot Email, Screenshot App]
sources: [Confluence CORE/1559461890]
created: 2026-04-18
updated: 2026-04-18
---

# Executive Snapshot Email Script & Schedule

Automated email script that sends executive snapshot reports on a cron schedule. Runs on an Auriga Proxmox VM in Pacific timezone.

## Location

| Field | Value |
|---|---|
| Proxmox host | Auriga (192.168.30.86) |
| VM ID | 11099 |
| VM name | `aldctestagnt1c01` |
| VM IP | 192.168.36.123 |
| Script directory | `~/screenshot_app` (aldc user) |

## Cron schedule

| Run | Time |
|---|---|
| Test run | 7:30 AM Pacific |
| Production email | 8:00 AM Pacific |

View current schedule: `crontab -l` (as `aldc` user).

## Timezone configuration

VM timezone is set to `Canada/Pacific` so cron jobs run in Pacific time rather than UTC.

```bash
# Change timezone
sudo timedatectl set-timezone <timezone>

# Verify
timedatectl
```

## Maintenance

- Edit files in `~/screenshot_app` to change recipients, schedule, or script logic
- The 7:30 AM test run provides a verification window before the 8:00 AM production send
- Monitor for errors: `journalctl -u cron` or `/var/log/syslog`

## See Also

- [[deployment-groups]] — Auriga hypervisor (VM 11099 host) + VM naming
- [[agent-builds]] — Proxmox VM management
- [[powerbi-secret-refresh]] — Power BI secrets used by reports
