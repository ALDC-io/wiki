---
tags: [ops-platform, launchpad, credentials, prefect, blocks, active]
created: 2026-05-13
updated: 2026-05-13
---

# Phase 1C: Prefect Block Provisioning

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase1c.md` → `/launchpad-phase1c`
**Status:** Planned (starts after 1B)
**Effort:** 3–4 days
**Depends on:** Phase 1B (submission backend)

## Goal

One-click "Provision to Prefect" from the credential dashboard. Azure Function reads credential from Key Vault → creates/updates Prefect Blocks across QA/UAT/Prod environments. Includes validation step before provisioning.

## Deliverables

1. `provision-prefect-block` Azure Function: Key Vault → Prefect REST API
2. Block type mapping registry (credential type → Prefect Block class)
3. Three-environment replication (QA/UAT/Prod)
4. Validation function: test credential against provider API before provisioning
5. Dashboard "Validate" + "Provision to Prefect" buttons with environment checkmarks

## Block Type Mapping

| Credential Type | Block Class | Slug Pattern |
|---|---|---|
| API key | `Secret` | `{provider}-{client_code}` |
| OAuth token | `Secret` / `ConnectorConnectionBase` | `{provider}-oauth-{client_code}` |
| Snowflake | `SnowflakeCredentials` | `snowflake-{env}-{client_code}` |
| Windsor API key | `Secret` | `windsor-api-key-{client_code}` |

## The Complete Bridge

```
Client submits credential (Phase 1B)
  → Azure Function writes to Key Vault
    → Engineer clicks "Validate" (tests against provider API)
      → Engineer clicks "Provision to Prefect"
        → Azure Function reads Key Vault → calls Prefect REST API
          → Prefect Block created across QA/UAT/Prod
            → Connector reads Block at runtime (no connector changes needed)
```

## Key Constraints

- Prefect Python client handles CSRF automatically (proven in GP-243)
- Prefect auth: HTTP Basic via PREFECT_API_AUTH_STRING
- Block registration is idempotent (overwrite=True)
- Existing connector code reads blocks unchanged — this is invisible to connectors

## Next Session Boot Prompt

````
You are working on **ALDC Launchpad Phase 1C** (Prefect Block Provisioning).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\aldc-launchpad\active\phase-1c-prefect-provisioning.md`
3. Read the approved plan: `C:\Users\PaulRussell\.claude\plans\floating-giggling-neumann.md` — Phase 1C section
4. Read `C:\Users\PaulRussell\repos\prefect-connectors\scripts\register_gep_blocks.py` — existing block registration pattern
5. Read `C:\Users\PaulRussell\repos\prefect-connectors\connector\account_registry.py` — PLACEHOLDER block creation pattern
6. Read `C:\Users\PaulRussell\repos\wiki\entities\tools\prefect.md` — Prefect server auth + block conventions

Goal: Build provision-prefect-block Azure Function, block type registry, validation step, 3-env replication.
````

## See Also

- [[phase-1b-credential-submission]] — Backend (prerequisite)
- [[phase-1d-automation]] — Monitoring and reminder automation (next)
