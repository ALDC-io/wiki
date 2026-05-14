---
tags: [ops-platform, launchpad, credentials, oauth, azure-functions, active]
created: 2026-05-13
updated: 2026-05-13
---

# Phase 1B: Secure Credential Submission

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase1b.md` → `/launchpad-phase1b`
**Status:** Planned (starts after 1A)
**Effort:** 5–7 days
**Depends on:** Phase 1A (dashboard), Phase 0R (monorepo)

## Goal

Build the Azure Functions backend + Azure Key Vault storage + client-facing submission page at `connect.analyticlabs.io`. Solve the 5-minute OAuth code expiry problem with a server-side callback. Support both client submission (via link) and engineer direct entry.

## Deliverables

1. Azure Key Vault `aldc-credential-vault` provisioned (Standard, Canada Central)
2. Azure Function App (`api/credential-exchange/`) with 6 functions:
   - `generate-link` — one-time submission URL (7-day TTL, HMAC-signed)
   - `submit-credential` — client submits API key/token via form → Key Vault
   - `enter-credential` — engineer direct entry (Azure AD auth)
   - `oauth-callback` — **solves 5-min problem**: receives OAuth redirect → exchanges code immediately → Key Vault
   - `generate-oauth-url` — builds provider-specific authorization URL with redirect_uri
   - `get-status` — returns metadata (no secrets) for dashboard polling
3. Client submission page at `connect.analyticlabs.io` (Azure Static Web Apps)
4. Dashboard integration: "Request from Client" + "Add Credential" buttons

## The 5-Minute OAuth Problem — Solved

**Problem:** Amazon LWA auth codes expire in ~5 minutes. Email relay always fails (GP-221 took 8 days).

**Solution:** `oauth-callback` Azure Function. Client clicks auth link → authorizes on provider → provider redirects to our callback → function exchanges code for refresh token in milliseconds → stores in Key Vault. No human touches the auth code.

Auth paths:
- Windsor OAuth (Google, Meta, LinkedIn): Windsor handles entirely; track status only
- Amazon LWA, SP-API, TikTok: `oauth-callback` endpoint (direct OAuth)
- API keys (SmartScout, Sellercloud): `submit-credential` form
- User/pass (SQL Server): `submit-credential` form

## Key Constraints

- Azure Key Vault as source of truth (not CosmosDB, not Prefect Blocks directly)
- Secret naming: `{client_code}--{provider}--{credential_type}`
- No raw secrets in credentials.json, app logs, or API responses
- Every submission writes `zeusContext` event for client Zeus Memory seeding

## Next Session Boot Prompt

````
You are working on **ALDC Launchpad Phase 1B** (Secure Credential Submission).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\aldc-launchpad\active\phase-1b-credential-submission.md`
3. Read the approved plan: `C:\Users\PaulRussell\.claude\plans\floating-giggling-neumann.md` — Phase 1B section
4. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\aldc-launchpad\active\phase-1a-credential-dashboard.md` — understand the dashboard integration points
5. Read the credential exchange design doc: `C:\Users\PaulRussell\repos\aldc-launchpad\api\credential-exchange\credential_exchange_hub_design_doc.md`

Goal: Build Azure Functions (Python), provision Key Vault, create client submission page, implement oauth-callback for 5-min code expiry fix.
Backend: Azure Functions consumption plan, Python, DefaultAzureCredential.
Security: Key Vault stores secrets, credentials.json stores metadata only.
````

## See Also

- [[phase-1a-credential-dashboard]] — Frontend (prerequisite)
- [[phase-1c-prefect-provisioning]] — Block provisioning (next)
- [[../backlog/phase-5-credentials]] — Original Phase 5 (superseded by 1A-1D)
