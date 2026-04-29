---
tags: [distributed-workflow, active, navira, credentials, testing, tooling]
aliases: [Credential Validation Toolkit, Navira API Tester]
sources: []
created: 2026-04-28
updated: 2026-04-28
---

# Credential Validation Toolkit

## Goal

A lightweight Python CLI in `aldc-shipyard/scripts/credential_tester/` that can validate API credentials for every Navira platform — both existing (Amazon Ads, SP-API, Sellercloud) and incoming (Google Ads, Meta, TikTok, etc.). When done: `python run_all.py` produces a credential status report showing which platforms are accessible, which tokens are expired, and which are still pending. Runs alongside all Navira phases as an ongoing operational tool.

## Lane

Wiki: ALDC

Owned paths (this workstream may write here):

- `C:\Users\PaulRussell\repos\aldc-shipyard\scripts\credential_tester\`
- `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\credential-validation-toolkit.md`

Read-only outside the lane. Cross-lane edits go through *Cross-Lane Request*.

## Required Context

Every session must read these at boot:

- [[navira-credentials-access]] — credential audit, what we have vs what we need, investigation items I-1 through I-6
- `C:\Users\PaulRussell\repos\aldc-shipyard\scripts\setup.py` — existing repo patterns (config loading, interactive prompts, colored output)
- `C:\Users\PaulRussell\repos\aldc-shipyard\config\gep.yaml` — local repo paths (includes path to clients repo where Eclipse connection JSONs live)

## Plan-Mode Rule

First session per execution phase enters plan mode. Subsequent sessions within the same phase skip plan mode if scope is unchanged. If a new platform is added mid-phase, re-enter plan mode for that platform only.

## Execution Phases

### Phase 0 — Foundation

**Scope:** Project structure, shared utilities, config loading, result reporting.

**Deliverables:**
- `scripts/credential_tester/__init__.py`
- `scripts/credential_tester/config.py` — loads credentials from three sources (priority order):
  1. Eclipse connection JSONs via clients repo path in `config/gep.yaml`
  2. Local `credential_tester_config.json` (for new creds not yet in Eclipse)
  3. Environment variables (for CI / automation)
- `scripts/credential_tester/report.py` — structured test result collector + formatters:
  - Terminal output (colored, like setup.py)
  - Markdown (paste into wiki / Jira)
  - JSON (machine-readable)
- `scripts/credential_tester/base.py` — `CredentialTest` base class defining the interface:
  - `name` — platform display name
  - `phase` — which Navira phase this belongs to
  - `load_credentials()` — resolve creds from config sources
  - `test_connection()` → `TestResult(status, message, details)`
  - Statuses: `PASS`, `FAIL`, `EXPIRED`, `STUB` (no creds yet), `SKIP` (dependency missing)
- `scripts/credential_tester/run_all.py` — discovers all test modules, runs them, generates report
- `requirements-credential-tester.txt` — pinned deps (kept separate from main repo deps)

**Dependencies:** None — can start immediately.

**Resolves:** Foundation for all subsequent phases.

---

### Phase 1 — Already Have Credentials (Tier 1)

**Scope:** Build and run testers for platforms with active production credentials. These validate what we already have and resolve investigation items I-2 and I-4.

**Deliverables:**

#### `test_amazon_ads.py`
- Load: LWA refresh token from `clients/GEP/eclipse/connections/amazon_ads.json`
- Test: Exchange refresh token for access token → call `GET /v2/profiles` to enumerate all profiles
- Bonus: Report which marketplace regions have profiles (resolves **I-4** — if UK/CA profiles show up, we don't need to ask Navira)
- Pass criteria: HTTP 200 + at least one profile returned

#### `test_amazon_sp_api.py`
- Load: LWA credentials from `clients/GEP/eclipse/connections/amazon_seller_central.json`
- Test: Exchange refresh token for access token → call `GET /orders/v0/orders` with a 1-day lookback (minimal query)
- Pass criteria: HTTP 200 (even if zero orders returned)

#### `test_sellercloud_rest.py`
- Load: Username/password from `clients/GEP/eclipse/connections/sellercloud_rest.json`
- Test 1 (sales — existing): Authenticate → call a known sales endpoint
- Test 2 (inventory — **resolves I-2**): Authenticate → call inventory endpoint (e.g., `GET /api/inventory/items` or equivalent). Report whether creds have inventory permissions or return 403.
- Pass criteria: HTTP 200 on sales; inventory result determines whether we need to ask Navira for a permission upgrade

**Dependencies:** Phase 0 complete. `config/gep.yaml` must have valid `repos.clients` path.

**Resolves:** I-2 (Sellercloud inventory permissions), I-4 (Amazon Ads UK/CA profile discovery).

---

### Phase 2 — Phase 1A Platform Stubs (Tier 2)

**Scope:** Build testers for Phase 1A platforms where ALDC has infrastructure but Navira hasn't provided account details yet. These run in `STUB` mode until creds arrive, then flip to real tests. Also resolves I-5 and I-6.

**Deliverables:**

#### `test_google_ads.py`
- Load: Developer token from vault (env var `GOOGLE_ADS_DEVELOPER_TOKEN`); OAuth refresh token from config (not yet available)
- Test (pre-creds / **resolves I-5**): Validate developer token exists and check access level by calling `GET /customers:listAccessibleCustomers` with just the dev token + a test refresh token. If no refresh token, report `STUB` but confirm dev token is present.
- Test (post-creds): Use Navira's MCC ID + refresh token → run a minimal GAQL query (`SELECT campaign.id FROM campaign LIMIT 1`)
- Pass criteria: GAQL returns results without permission error

#### `test_meta_ads.py`
- Load: ALDC App ID + app_secret (from env vars or config); Navira access token (from config, not yet available)
- Test (pre-creds / **resolves I-6**): Verify ALDC App ID is valid by calling `GET /app?access_token=<app_id>|<app_secret>` (app-level token). Report whether the app requires re-verification.
- Test (post-creds): Use Navira's access token → call `GET /me/adaccounts` to verify BM access
- Pass criteria: App verification passes; post-creds returns ad account list

#### `test_amazon_ads_uk_ca.py`
- Depends on `test_amazon_ads.py` profile enumeration results
- If Phase 1 found UK/CA profiles: run the same SP/SB/SD report test scoped to those profiles
- If no UK/CA profiles found: report `SKIP` with message "No UK/CA profiles — confirm with Navira"

**Dependencies:** Phase 0 complete. Stubs work immediately; full tests after Navira provides creds.

**Resolves:** I-5 (Google Ads dev token level), I-6 (Facebook App token status).

---

### Phase 3 — Phase 1B+ Platform Stubs (Tier 3)

**Scope:** Minimal stubs for all remaining platforms. These exist so `run_all.py` gives a complete picture even for platforms not yet started. Each stub reports `STUB` status with a message describing what creds are needed.

**Deliverables:**
- `test_tiktok.py` — stub: needs Business Center ID + OAuth app registration
- `test_email_marketing.py` — stub: needs platform identification (Klaviyo/Mailchimp/HubSpot)
- `test_target_plus.py` — stub: needs confirmation of seller status + access method
- `test_smartscout.py` — stub: needs subscription tier + API key
- `test_purchasing_system.py` — stub: needs system identification
- `test_email_productivity.py` — stub: needs M365/Google Workspace tenant details

**Dependencies:** Phase 0 complete.

**Resolves:** Nothing directly — these are placeholders.

---

### Phase 4 — Report Generator & Investigation Sweep

**Scope:** Wire everything together. `run_all.py` produces a comprehensive credential status report. Run the full suite to resolve all pending investigations.

**Deliverables:**
- `run_all.py` enhancements:
  - Group results by phase (1A, 1B, 1C, 2, 3, 4)
  - Color-coded terminal output (PASS=green, FAIL=red, EXPIRED=yellow, STUB=gray, SKIP=blue)
  - Markdown report suitable for pasting into [[navira-credentials-access]] or Jira
  - JSON report for programmatic consumption
  - `--phase 1a` flag to run only a specific phase's tests
  - `--investigate` flag to run only the I-1 through I-6 investigation tests
- Run the full suite and update [[navira-credentials-access]] with results:
  - Move confirmed items from "ALDC to Investigate First" to "Already Have" or "Ask Navira"
  - Update Token Expiry Status with verified dates

**Dependencies:** Phases 1–3 complete.

**Resolves:** Final pass on all investigation items. Produces the definitive credential status report.

---

## Estimated Effort

| Phase | Sessions | Depends On | Resolves |
|---|---|---|---|
| Phase 0 — Foundation | 1 | Nothing | Project structure |
| Phase 1 — Tier 1 (Have Creds) | 1–2 | Phase 0 | I-2, I-4 |
| Phase 2 — Tier 2 (1A Stubs) | 1 | Phase 0 | I-5, I-6 |
| Phase 3 — Tier 3 (1B+ Stubs) | 1 | Phase 0 | — |
| Phase 4 — Report & Sweep | 1 | Phases 1–3 | All remaining |

Phases 1–3 can run in parallel after Phase 0 is done. Total: ~4–6 sessions.

## Session Log

Append-only. Newest at the bottom.

### 2026-04-28 — Workstream created

- did: Designed execution plan (4 phases), wrote boot prompts, created workstream tracker
- decided: CLI in `aldc-shipyard/scripts/credential_tester/` (not an Eclipse app); read existing Eclipse connection JSONs for Tier 1 creds; stubs for platforms awaiting creds
- next: Phase 0 — foundation (project structure, config loader, report generator, base class)

## Decisions Log

- 2026-04-28 — CLI tool in `aldc-shipyard`, not an Eclipse app. Reason: internal operational tool used a handful of times per platform; no UI/deployment overhead needed. Revisit only if Navira self-service testing becomes a requirement.
- 2026-04-28 — Three-tier credential source (Eclipse JSONs → local config → env vars). Reason: Tier 1 platforms already have creds in Eclipse connection files; new creds arrive ad-hoc and shouldn't require committing to the clients repo first.
- 2026-04-28 — Separate `requirements-credential-tester.txt`. Reason: tester needs API client libraries (google-ads, amazon-advertising-api, facebook-business-sdk) that the main aldc-shipyard scripts don't need. Keep dependency footprints isolated.

## Blockers / Open Questions

- 2026-04-28 — I-1 (SP-API private→public) should be resolvable via Amazon docs; if not, may need to contact Amazon developer support. Not a blocker for Phases 0–2 but blocks Phase 1C testing.

## Cross-Lane Requests

_(none yet)_

## Boot Prompts

### Phase 0 — Foundation

````
You are starting the Navira Credential Validation Toolkit workstream, Phase 0 (Foundation).

Working directory: C:\Users\PaulRussell\repos\aldc-shipyard

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\credential-validation-toolkit.md`
3. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\navira-credentials-access.md` (credential audit + investigation items)
4. Read `C:\Users\PaulRussell\repos\aldc-shipyard\scripts\setup.py` (existing repo patterns)
5. Read `C:\Users\PaulRussell\repos\aldc-shipyard\config\gep.yaml` (local repo paths)

Your task: Implement Phase 0 — Foundation. Create the project structure at `scripts/credential_tester/` with:
- `__init__.py`
- `config.py` — credential loader (Eclipse JSONs → local config → env vars)
- `report.py` — test result collector + terminal/markdown/JSON formatters
- `base.py` — CredentialTest base class (name, phase, load_credentials, test_connection → TestResult)
- `run_all.py` — test discovery + execution + report generation
- `requirements-credential-tester.txt` — minimal deps for foundation only

Follow the coding patterns in setup.py (colored terminal output, Path-based file handling).
Do NOT install dependencies or run the code — just create the files.

Plan mode rule: enter plan mode first since this is the first session of this phase. Get Paul's approval before writing code.

When done, update the Session Log in this tracker with what was done and what's next.
````

### Phase 1 — Tier 1 (Already Have Creds)

````
You are resuming the Navira Credential Validation Toolkit workstream, Phase 1 (Tier 1 — Already Have Creds).

Working directory: C:\Users\PaulRussell\repos\aldc-shipyard

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\credential-validation-toolkit.md`
3. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\navira-credentials-access.md` — focus on "Already Have" platforms and investigations I-2, I-4
4. Read the Phase 0 files: `scripts/credential_tester/base.py`, `config.py`, `report.py`
5. Read the Eclipse connection JSONs to understand their schema:
   - Find clients repo path from `config/gep.yaml` → `repos.clients`
   - Read `{clients}/GEP/eclipse/connections/amazon_ads.json`
   - Read `{clients}/GEP/eclipse/connections/amazon_seller_central.json`
   - Read `{clients}/GEP/eclipse/connections/sellercloud_rest.json`

Your task: Implement Phase 1 — three credential testers for platforms we already have production creds for:
1. `test_amazon_ads.py` — LWA token exchange + profile enumeration (resolves I-4: report UK/CA profiles)
2. `test_amazon_sp_api.py` — LWA token exchange + minimal orders query
3. `test_sellercloud_rest.py` — REST auth + sales endpoint + inventory endpoint probe (resolves I-2)

Each tester must subclass CredentialTest from base.py and work with run_all.py.
Update requirements-credential-tester.txt with needed API client libraries.
Do NOT run the tests against live APIs without Paul's approval.

Plan mode rule: enter plan mode first since this is the first session of this phase.

When done, update the Session Log in this tracker. Note which investigations (I-2, I-4) are ready to resolve once Paul approves running against live APIs.
````

### Phase 2 — Tier 2 (Phase 1A Stubs)

````
You are resuming the Navira Credential Validation Toolkit workstream, Phase 2 (Tier 2 — Phase 1A Platform Stubs).

Working directory: C:\Users\PaulRussell\repos\aldc-shipyard

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\credential-validation-toolkit.md`
3. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\navira-credentials-access.md` — focus on Phase 1A platforms, investigations I-5, I-6
4. Read the existing testers from Phase 1 for patterns
5. Read wiki connector specs: `C:\Users\PaulRussell\repos\wiki\entities\tools\connectors\google-ads.md` and `facebook-ads.md`

Your task: Implement Phase 2 — three testers for Phase 1A platforms (ALDC has infrastructure, awaiting Navira creds):
1. `test_google_ads.py` — pre-creds: validate ALDC dev token exists + check level (I-5); post-creds: GAQL test query
2. `test_meta_ads.py` — pre-creds: verify ALDC Facebook App status (I-6); post-creds: ad account enumeration
3. `test_amazon_ads_uk_ca.py` — depends on Phase 1's profile enumeration; test UK/CA-specific ad reports if profiles found

Each tester supports two modes: STUB (no Navira creds yet) and FULL (after creds arrive). The STUB mode should still validate ALDC-side readiness.

Plan mode rule: skip plan mode if Phase 1 patterns are clear and reusable.

When done, update the Session Log. Note I-5 and I-6 readiness.
````

### Phase 3 — Tier 3 (1B+ Stubs)

````
You are resuming the Navira Credential Validation Toolkit workstream, Phase 3 (Tier 3 — Phase 1B+ Stubs).

Working directory: C:\Users\PaulRussell\repos\aldc-shipyard

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\credential-validation-toolkit.md`
3. Read `scripts/credential_tester/base.py` for the CredentialTest interface

Your task: Create minimal stubs for all remaining platforms:
- `test_tiktok.py`, `test_email_marketing.py`, `test_target_plus.py`
- `test_smartscout.py`, `test_purchasing_system.py`, `test_email_productivity.py`

Each stub returns TestResult(status=STUB, message="<what creds are needed>"). Keep them short — just enough for run_all.py to show a complete platform inventory.

Plan mode rule: skip plan mode — this is mechanical work following established patterns.

When done, update the Session Log.
````

### Phase 4 — Report Generator & Investigation Sweep

````
You are resuming the Navira Credential Validation Toolkit workstream, Phase 4 (Report Generator & Investigation Sweep).

Working directory: C:\Users\PaulRussell\repos\aldc-shipyard

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\credential-validation-toolkit.md`
3. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\navira-credentials-access.md` — focus on "ALDC to Investigate First" table
4. Read `scripts/credential_tester/run_all.py` and `report.py`
5. Read all test_*.py files to understand current state

Your task: Enhance run_all.py with:
1. Group results by Navira phase (1A, 1B, 1C, 2, 3, 4)
2. `--phase 1a` flag to run only specific phase tests
3. `--investigate` flag to run only I-1 through I-6 investigation tests
4. Markdown report formatter (suitable for pasting into wiki/Jira)
5. JSON report formatter

Then: run the full suite with Paul's approval, capture results, and update navira-credentials-access.md:
- Move resolved investigations from "ALDC to Investigate First" to appropriate sections
- Update Token Expiry Status with verified data
- Update the pre-filled questionnaire JSON if investigation results change what we need from Navira

Plan mode rule: enter plan mode for the run_all.py enhancements. Skip plan mode for the wiki updates (mechanical, based on test results).

When done, update the Session Log with the definitive credential status.
````

## See Also

- [[navira/README|Navira Roadmap]] — master workflow hub
- [[navira-credentials-access]] — credential audit, investigation items, client access request
- [[aldc-shipyard]] — host repo for the toolkit
- [[connector-development-standards]] — ALDC Prefect connector patterns (testers validate what connectors will consume)
