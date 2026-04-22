---
tags: [entity, tool, cloudflare, dns, domain, hosting]
aliases: [Cloudflare, CF]
sources: [daily/2026-04-17.md]
created: 2026-04-17
updated: 2026-04-17
---

# Cloudflare

ALDC's DNS and domain registration control plane. All hosted sites (client dashboards, internal apps, prospect sites) have their public DNS records managed in Cloudflare.

## What lives in Cloudflare

- **Complete catalog of hosted sites** — the Cloudflare dashboard is the authoritative list of every public-facing site ALDC hosts
- **CNAME records pointing to backends** — most sites CNAME to an [[Azure]] web app (example: Eclipse web UI CNAMEs to the Azure web app URL). Set the CNAME target field to the Azure web app hostname
- **DNS for on-prem services** — records for services running on on-prem servers (e.g., `aldc-ca-w1`, which hosts the DIOS API — currently the only prod artifact on that server)

## Hosting backends behind Cloudflare

| Backend | Typical use |
|---------|-------------|
| [[Azure]] web apps | Most engineering-owned services (Eclipse web, core_api, etc.) |
| Vercel | Prospect sites only — not commonly used by engineers |
| On-prem (e.g. `aldc-ca-w1`) | Legacy / niche services. DIOS API is the only prod artifact still on `aldc-ca-w1` |

## Access

Access granted by Brayden on 2026-04-17. Owner/admin permissions beyond that level may need a follow-up with Brayden / Sean.

## See Also

- [[Azure]] — primary hosting target for CNAMEs
- [[Eclipse]] — one of the services fronted by a Cloudflare CNAME
- [[eclipse-azure-deployment]] — deployment flow that ultimately updates what the Cloudflare CNAME is pointing at (via slot swap)
