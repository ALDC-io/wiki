---
tags: [ops-platform, launchpad, credentials, prefect, blocks, complete]
created: 2026-05-13
updated: 2026-05-14
---

# Phase 1C: Prefect Block Provisioning

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase1c.md` → `/launchpad-phase1c`
**Status:** Complete (2026-05-14)
**Effort:** 1 session (~3 hours)
**Depends on:** Phase 1B (submission backend)
**Commit:** `eb523aa` — `feat: Phase 1C — Prefect block provisioning (Key Vault → Prefect Blocks)`

## Goal

One-click "Provision to Prefect" from the credential dashboard. Azure Function reads credential from Key Vault → creates/updates Prefect Blocks across QA/UAT/Prod environments. Includes validation step before provisioning.

## Deliverables — All Complete

1. **`provision-prefect-block` Azure Function** — `POST /credentials/{id}/provision`. Reads from Key Vault, creates/updates Prefect blocks via REST API. Supports environment filtering. Returns per-block results with block names and IDs.

2. **Block type mapping registry** (`services/block_registry.py`) — Maps credential type → Prefect block type + slug pattern. Non-Snowflake → one `secret` block (all envs). Snowflake → three `snowflake-credentials` blocks (per-env).

3. **Three-environment replication** — Block specs generated per-env for Snowflake credentials. Non-Snowflake credentials create a single block available to all work pools. Optional `environments` filter in the provision request.

4. **Full validation suite** (`services/validation.py`) — Provider-specific validation before provisioning:
   - Amazon Ads: refresh token → access token → GET /v2/profiles (returns profile count + IDs)
   - Amazon SP-API: refresh token exchange verification
   - Sellercloud: auth endpoint call
   - TikTok: advertiser info fetch
   - Windsor: pass-through (Windsor manages tokens)
   - Generic: non-empty check fallback
   - Local dev: mock results

5. **Dashboard UX** — "Validate" and "Provision to Prefect" buttons wired to real API. Spinner + loading states during operations. Environment checkmarks (QA/UAT/Prod) after provisioning. Validation result panel with provider details. Notes auto-update on provision. No timeline pollution from transient states.

## Block Type Mapping (Implemented)

| Credential Type | Block Class | Slug Pattern | Per-Env |
|---|---|---|---|
| API key | `secret` | `{provider}-{client_suffix}` | No |
| Direct OAuth | `secret` | `{provider}-{client_suffix}` | No |
| LWA OAuth | `secret` | `{provider}-{client_suffix}` | No |
| Windsor OAuth | `secret` | `{provider}-{client_suffix}` | No |
| Snowflake | `snowflake-credentials` | `{provider}-{env}-{client_suffix}` | Yes (QA/UAT/Prod) |

## Architecture

### Prefect REST API Approach

Chose REST API over Python SDK to keep the Azure Function App lightweight (no `prefect` dependency). The `PrefectService` (`services/prefect.py`) handles:
- Block type lookup by slug (`GET /block_types/slug/{slug}`)
- Block document search (`POST /block_documents/filter`)
- Create (`POST /block_documents/`) or update (`PATCH /block_documents/{id}`)
- HTTP Basic auth matching existing Prefect server config
- Local dev mock store for testing without a Prefect server

### The Complete Bridge (Verified)

```
Client submits credential (Phase 1B)
  → Azure Function writes to Key Vault
    → Engineer clicks "Validate" (tests against provider API)
      → Engineer clicks "Provision to Prefect"
        → Azure Function reads Key Vault → calls Prefect REST API
          → Prefect Block created (all envs or per-env)
            → Connector reads Block at runtime (no connector changes needed)
```

### Files Created/Modified

| File | Action | Purpose |
|---|---|---|
| `api/credential-exchange/services/prefect.py` | Created | Prefect REST API client + local mock |
| `api/credential-exchange/services/block_registry.py` | Created | Credential type → block type mapping |
| `api/credential-exchange/services/validation.py` | Created | Provider-specific credential validation |
| `api/credential-exchange/function_app.py` | Modified | Added validate + provision endpoints |
| `api/credential-exchange/local.settings.json` | Modified | Added PREFECT_API_URL, PREFECT_API_AUTH_STRING |
| `platform/master/data/credentials.json` | Modified | Added `provisioning` status definition |
| `platform/master/pages/credentials/index.html` | Modified | Wired buttons, env checkmarks, validation display |

## Key Decisions

- **REST over SDK**: Prefect Python SDK would add heavy cold-start to the Function App. REST calls are lightweight and the block CRUD operations are simple enough.
- **Single block for non-Snowflake**: API keys and OAuth tokens are environment-agnostic — one block serves all work pools. Only Snowflake needs per-env blocks (different accounts per env).
- **No timeline pollution**: Transient states (validating, provisioning) are UI-only — only final results (validated, provisioned, failed) get timeline entries.
- **Status restore on failure**: Network errors restore the previous status instead of regressing (e.g., a validated credential stays validated if the API is unreachable).
- **Notes auto-update**: After provisioning, the notes field is overwritten with the live block name and Key Vault ref.

## Key Constraints

- Prefect auth: HTTP Basic via PREFECT_API_AUTH_STRING
- Block creation is idempotent (find-existing → PATCH, else POST)
- Existing connector code reads blocks unchanged — this is invisible to connectors
- `local.settings.json` is gitignored (contains auth string placeholder)

## Testing

Tested locally with `func start`. Full pipeline verified: Enter credential → Key Vault mock → Validate (provider mock) → Provision (Prefect mock) → status update + environment checkmarks + notes update.

Production integration test pending: set `PREFECT_API_AUTH_STRING` → provision a real credential → verify block appears on https://prefect.analyticlabs.io.

## See Also

- [[phase-1b-credential-submission]] — Backend (prerequisite)
- [[phase-1d-automation]] — Monitoring and reminder automation (deferred)
- [[prefect]] — Prefect server auth, block conventions, work pool architecture
