---
tags: [ops-platform, launchpad, credentials, oauth, azure-functions, active]
created: 2026-05-13
updated: 2026-05-14
---

# Phase 1B: Secure Credential Submission

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase1b.md` → `/launchpad-phase1b`
**Status:** In Progress — scaffold + backend + dashboard wiring complete, 11/11 local tests passing. Remaining: Azure provisioning + production deploy.
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

## Deliverable Status

| # | Deliverable | Status | Notes |
|---|---|---|---|
| 1 | Azure Key Vault `aldc-credential-vault` | Bicep ready | `infra/credential-vault.bicep` — Standard tier, Canada Central, RBAC auth, purge protection |
| 2 | Azure Function App (6 functions) | Built + tested | `api/credential-exchange/function_app.py` — all 6 routes, 11/11 E2E tests passing locally |
| 3 | Client submission page | Built | `platform/portal/connect/submit.html` — multi-state (API key form, OAuth auth, user/pass), dark theme, security headers |
| 4 | Dashboard integration | Wired | "Request from Client" → `generate-link`/`generate-oauth-url`, "Enter Credential" → `enter-credential`, "Validate" → `get-status`, toast notifications, copy-link + email UI |

### Function Inventory

| Function | Route | Auth | Status |
|---|---|---|---|
| `generate-link` | `POST /api/credentials/generate-link` | Function key | Working — HMAC-signed 7-day TTL tokens |
| `submit-credential` | `POST /api/credentials/submit/{token}` | Anonymous (token) | Working — validates HMAC, writes Key Vault |
| `enter-credential` | `POST /api/credentials/enter` | Function key | Working — engineer direct entry |
| `oauth-callback` | `GET /api/oauth/callback/{provider}` | Anonymous (state) | Working — mock in dev, real HTTP in prod |
| `generate-oauth-url` | `POST /api/credentials/generate-oauth-url` | Function key | Working — Amazon LWA + TikTok adapters |
| `get-status` | `GET /api/credentials/{id}/status` | Function key | Working — metadata only |

### Files Created

```
api/credential-exchange/
├── function_app.py          # 6 HTTP-triggered Azure Functions (Python v2)
├── host.json, requirements.txt, local.settings.json, .funcignore
├── services/keyvault.py     # Key Vault client (local dev store for testing)
├── services/hmac_tokens.py  # HMAC token gen/validation (7-day TTL)
├── services/audit.py        # Structured audit logging (auto-redacts secrets)
├── providers/base.py        # ProviderAdapter ABC
├── providers/amazon_lwa.py  # Amazon LWA OAuth (Ads + SP-API)
└── providers/tiktok.py      # TikTok for Business OAuth

platform/portal/connect/
├── submit.html              # Client submission page (6 states, provider-specific instructions)
└── staticwebapp.config.json # Azure SWA routing + security headers

infra/
└── credential-vault.bicep   # Key Vault + Function App + Storage + RBAC
```

## Session Log

### 2026-05-14 — Credential data corrected, provider search, committed

- did: Corrected credential data — removed 6 F92 placeholders (not real), corrected Amazon US/Sellercloud/SP-API from fake "provisioned" to "validated" (tokens exist in Eclipse but not in Key Vault/Prefect Blocks). Cleared fabricated `prefectBlock`/`keyVaultRef` values. Added Zeus-seeded provider knowledge base (`providers.json`, 24 providers) and replaced static provider dropdown with searchable input (alias matching, auto-fill, info card). Fixed dropdown option styling for dark theme. All work committed in 5 git commits.
- decided: Credential data must reflect reality — "provisioned" means actually in a Prefect Block, not just "token exists somewhere." F92 credentials deferred until properly inventoried.
- status: Phase 1B fully committed. Credential status: 9 GEP (0 provisioned, 5 validated, 2 pending, 2 draft).

### 2026-05-14 — Phase 1B scaffold + backend + dashboard wiring

- did: Built complete Azure Function App scaffold with all 6 functions implemented and locally tested (11/11 E2E tests pass). Created 3 service modules: KeyVaultService (with in-memory LocalStore for dev), HMAC token generation/validation (7-day TTL, base64+HMAC-SHA256), audit logging (auto-redacts secret fields). Created 2 provider adapters: Amazon LWA (Ads API + SP-API) and TikTok for Business (with mock mode for local dev). Built client submission page (`platform/portal/connect/submit.html`) with 6 states (loading, error, API key form, user/pass form, OAuth authorization, success), provider-specific instructions for SmartScout/Sellercloud/Amazon/TikTok. Created Bicep infrastructure template (`infra/credential-vault.bicep`) with Key Vault (Standard, RBAC, soft delete+purge protection), Function App (Python 3.11, Linux, consumption plan), managed identity RBAC assignment. Wired Phase 1A dashboard buttons to Phase 1B API: "Request from Client" calls `generate-link` or `generate-oauth-url` based on auth type, "Enter Credential" calls `enter-credential`, "Validate" calls `get-status`. Added toast notifications, copy-link + email buttons, link result display in expanded credential rows. Fixed func host stability by disabling AzureWebJobsStorage (HTTP-only functions don't need it).
- decided: Windsor OAuth credentials handled as status-only (no API call — Windsor manages tokens). Local dev uses in-memory store + mock token exchange, same code paths as production. Secret naming uses Key Vault-safe format: `{client}--{provider}--{type}` (lowercase, hyphens only).
- status: All code written and locally tested. Not yet deployed to Azure. Phase 1B is functionally complete pending Azure provisioning.
- next: Provision Azure resources (Key Vault + Function App) or proceed to Phase 1C (Prefect Block provisioning) which depends on the Key Vault being live.

## See Also

- [[phase-1a-credential-dashboard]] — Frontend (prerequisite, dashboard buttons now wired to Phase 1B API)
- [[phase-1c-prefect-provisioning]] — Block provisioning (next)
- [[../backlog/phase-5-credentials]] — Original Phase 5 (superseded by 1A-1D)
