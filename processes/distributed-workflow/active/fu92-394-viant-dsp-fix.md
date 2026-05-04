---
tags: [distributed-workflow, active, fusion92, viant, bug]
aliases: [FU92-394 Viant DSP Fix]
sources: []
created: 2026-05-04
updated: 2026-05-04
---

# FU92-394 — Viant DSP Connector Fix

## Goal

Re-enable Viant DSP actuals reporting in DAX by fixing the connector timeout bug, re-enabling Eclipse schedules, backfilling missing data (April 2 → present), and closing out with client communication. Done = actuals flowing, connector stable for 48hrs, client notified.

## Lane

Wiki: ALDC

Owned paths:
- `tickets/fusion92/FU92-394.md`
- `processes/distributed-workflow/active/fu92-394-viant-dsp-fix.md`

## Required Context

Every session must read these at boot:

- [[FU92-394]] — ticket page with root cause and fix plan
- [[FU92-342]] — prior Viant connector issue (PK dedup) for context
- [[connector]] — legacy connector repo overview
- `C:\Users\PaulRussell\repos\connector\connector\viant_dsp_reporting.py` — the connector code to fix

## Plan-Mode Rule

First session (code fix) starts in plan mode to confirm the timeout approach. Subsequent sessions (re-enable, validate, close) skip plan mode.

## Phases & Boot Prompts

### Phase 1: Code Hardening

Apply timeout and error handling fixes to `viant_dsp_reporting.py` before re-enabling schedules.

````
You are working on FU92-394 — Viant DSP connector timeout fix. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\fu92-394-viant-dsp-fix.md`
3. Read the ticket: `C:\Users\PaulRussell\repos\wiki\tickets\fusion92\FU92-394.md`
4. Read the connector code: `C:\Users\PaulRussell\repos\connector\connector\viant_dsp_reporting.py`

Task: Fix the polling timeout bug in `get_completed_reports()` (line 149-180):
- Add MAX_POLL_ATTEMPTS constant (60 iterations = ~1hr max)
- After max attempts, raise a clear exception with report statuses
- Handle non-"completed" terminal statuses (e.g., "Failed", "Error") — break the loop, raise descriptive error
- Add HTTP 429 rate-limit handling with exponential backoff in `_get_response_json()`
- Add timeout/retry to `pandas.read_csv(url)` in `process_downloads()`

This is the legacy connector repo (not prefect-connectors). Paul handles git commits.

When done, update the tracker session log and ticket status.
````

### Phase 1b: Safe Deployment (via new CI pipeline)

Deploy the fix through the new Docker CI pipeline with rollback capability.

````
You are working on FU92-394 Phase 1b — safe deployment of the Viant timeout fix. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\fu92-394-viant-dsp-fix.md`
3. Read the ticket: `C:\Users\PaulRussell\repos\wiki\tickets\fusion92\FU92-394.md`

Deployment path: development → master via CI (Option 1).
development has the Docker CI workflow (.github/workflows/docker-publish.yml) + GP-199 Amazon Ads feature.
master last updated March 9, 2026.

Steps:
1. BEFORE ANYTHING: record the current Docker image tag/SHA running on Kamloops via Portainer — this is our rollback target
2. PR the viant fix branch into development → CI builds test image (:development + :<sha>)
3. Validate on test agents: confirm timeout fires on a stuck report, confirm normal runs complete
4. Merge development → master → CI builds prod image (:master + :<sha>)
5. Deploy to Kamloops via Portainer (pull new :master image)
6. Monitor first connector run — if queue blocks or errors, immediately rollback: Portainer → redeploy old image SHA from step 1

Rollback is instant via Portainer image swap. No data loss risk — connector is append-only with PK dedup to Snowflake.

Note: this also brings GP-199 (Amazon Ads SB endpoint) and the Docker CI workflow itself into production.

Paul handles git commits and merges.
````

### Phase 2: Re-enable and Backfill

After code fix is merged and deployed, re-enable schedules in Eclipse 1.

````
You are working on FU92-394 Phase 2 — re-enable Viant DSP connectors. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\fu92-394-viant-dsp-fix.md`
3. Read the ticket: `C:\Users\PaulRussell\repos\wiki\tickets\fusion92\FU92-394.md`

Task: Guide Paul through re-enabling the three Viant DSP templates in Eclipse 1:
- Viant DSP - Campaign Performance Report
- Viant DSP - Campaign ROAS Report
- Viant DSP - Conversion Report

Steps:
1. Confirm the code fix from Phase 1 has been deployed to the Kamloops server
2. Re-enable each template schedule in Eclipse 1 legacy frontend
3. Trigger a manual backfill run covering April 2 → present
4. Monitor initial run for timeout/error behavior

When done, update the tracker session log.
````

### Phase 3: Testing / Validation

Verify data is flowing and connector is stable.

````
You are working on FU92-394 Phase 3 — validation. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\fu92-394-viant-dsp-fix.md`
3. Read the ticket: `C:\Users\PaulRussell\repos\wiki\tickets\fusion92\FU92-394.md`

Task: Validate Viant actuals are flowing:
1. Query Snowflake for MAX(date) on Viant source tables — confirm data beyond April 2
2. Check DAX flights that were reported as missing actuals — confirm actuals now visible
3. Review connector run logs on Kamloops for any errors or timeout triggers
4. Monitor for 24-48hrs stability (no queue blocking, no hung processes)
5. Check the Reach & Frequency template (snowflake_v1, 550/73/0) — separate issue or related?

When done, update the tracker session log with validation results.
````

### Phase 4: Jira Update + Client Email

Close out the ticket and draft client communication.

````
You are working on FU92-394 Phase 4 — close out. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\fu92-394-viant-dsp-fix.md`
3. Read the ticket: `C:\Users\PaulRussell\repos\wiki\tickets\fusion92\FU92-394.md`

Task:
1. Update FU92-394 in Jira with resolution steps (what was fixed, what was validated)
2. Draft a client-facing email for Lori (EI Lead) to send to the client (Juliann). Tone: professional, reassuring. DO NOT mention that connectors were intentionally disabled. Frame as: we identified a connector stability issue, applied fixes including timeout safeguards, backfilled the missing data, and added monitoring to prevent recurrence. Include what improvements were made.
3. Transition the Jira ticket to Done

When done, update the tracker session log and archive this workstream.
````

## Session Log

### 2026-05-04 — Triage and planning

- did: Investigated Viant connector code, identified root cause (no polling timeout → queue block → schedules disabled), confirmed 3/4 templates inactive in Eclipse 1, created FU92-394 in Jira, created wiki ticket page and workstream tracker
- decided: Must apply code fix before re-enabling schedules to prevent recurrence
- next: Phase 1 — implement timeout fix in viant_dsp_reporting.py

## Decisions Log

- 2026-05-04 — Fix code before re-enabling schedules (not just re-enable and hope). Re-enabling without the timeout fix risks the same queue-blocking incident.
- 2026-05-04 — Client communication will not mention intentional disabling. Frame as connector stability issue identified and fixed with safeguards added.

## Pending Wiki Updates

- `index.md`: Add `- [[FU92-394]] — Viant DSP actuals missing after 4/2. Connector timeout bug → schedules disabled → never re-enabled. Fix + backfill.` under Tickets > Fusion92
- `log.md`: `| 2026-05-04 | triage | FU92-394: Viant DSP actuals missing — root cause identified (connector timeout, schedules disabled), Jira ticket created, workstream tracker created |`

## Blockers / Open Questions

- 2026-05-04 — Need to confirm: has the connector Docker image been rebuilt/deployed since Jan 2026? If not, code fix requires a rebuild + redeploy to Kamloops.
- 2026-05-04 — Reach & Frequency template (snowflake_v1, 550/73/0) — is this a separate issue or related to the same incident?

## Cross-Lane Requests

None yet.

## Next Session Boot Prompt

Use Phase 1 boot prompt above.
