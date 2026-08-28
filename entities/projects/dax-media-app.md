---
tags: [entity, project, fusion92, dax, flight-check-app, web-app, eclipse]
aliases: [DAX Media App, Flight Check App, Flight Management Application, Flight Check Replacement]
sources: [CF92/1439399945, CF92/1206779949, CF92/1360887813, CF92/1425440769, CF92/1437204481, CF92/1437302786, CF92/1437204494, CF92/1632141315, CF92/1633681409, CF92/1654030337, CF92/1660911619, TECH/1777106945 (Steven Offboarding), TECH/1772126209 (Azure Resources Reference)]
created: 2026-04-18
updated: 2026-08-28
---

# DAX Media App

Flight Management web application built by ALDC for [[fusion92]]. Replaces Fusion92's legacy "Flight Check" Firebase/Google Cloud application. **"DAX"** is Fusion92's product family name for ALDC-built tools.

> **Name disambiguation:** "Flight Check" historically referred to both (a) this web app and (b) ALDC's operational data-pipeline validation process (see [[flight-check]]). In CF92 Confluence, "Flight Check" = the app. In ALDC engineering context, [[flight-check]] = the operational runbook. This page covers the app.

In production since **November 2024**. Hosted at `eclipse.datavize.com` (built on [[Eclipse]] 2.0 framework). Owned by Karen Prete (ALDC).

## Architecture

Source: Confluence TECH/1777106945 (Steven Offboarding).

- **Frontend:** Next.js, running inside [[Eclipse]] 2.0 (not Eclipse 2.1). Flight Check cannot currently run as a standalone application — it depends on Eclipse 2 for authentication (token sharing).
- **Document Storage:** Flight and job data stored as "Application" JSON documents in [[CosmosDB]], accessed via [[core_api]] (the old/v1 version, not v2/Eclipse 2.1).
- **Business Logic Backend:** Split between [[core_api]] and the [[workflows|Dax API]]. General calls (auth, user info, document retrieval) go through Core API; all new features go to the Dax API. Over time, existing features should be routed through the Dax API even if they call Core API internally.
- **Reporting Layer:** Flight Check data synced to [[Snowflake]] by the `FlightCheckSnowflakeSyncWorkflow` ([[workflows]], `dax_api/sync/lib.py:130`), driven by Azure Functions timer triggers.
  > ⚠ **Corrected 2026-08-28 (FU92-430).** This bullet used to read *"every 30 minutes … up to an hour to appear"*. **That is wrong, and it misled both a client and an investigation.** The 30-minute cadence only holds for **14 hours a day**: the incremental syncs run `0 20,50 10-23 * * *` — :20 and :50 past the hour, **hours 10–23 UTC only** (`function_app.py:341,365`) — plus a single full reconcile at **09:10 UTC** (`:391`). So there is a **10h30m nightly blackout, 23:50 → 10:20 UTC**, and an overnight edit can take **~10.5 hours** to appear, not one. The window is Pacific-aligned while Fusion92 is **Central**, so their working evening (after ~18:50 CT) falls inside the gap. Dynamic-table lag sits on top of this. See [[fusion92-platform-ids]] § *Clearing IDs*.

### Azure Resources (Production)

| Resource | Type | Purpose |
|---|---|---|
| `aldcprodfnapf921c01` | Function App | Dax API (Flight Check backend) |
| `aldcprodwbapflightcheck1c01` | App Service | Flight Check frontend |
| `aldcprodwbapnode1c01` | App Service | Eclipse 2 (used for Flight Check auth/hosting) |

Source: Confluence TECH/1772126209 (Azure Resources Reference).

---

## User Roles

| Role | Capabilities |
|------|-------------|
| Super Admin | Full access: all jobs/flights, field management, user management, approve/reject |
| Admin | All jobs/flights, user management, approve/reject; no field-type changes |
| User | Own jobs/flights (create/edit/submit/delete); view + duplicate/export others' |
| Buyer | (Added in PRJ537) Spend input, pacing view |

Statuses: **Draft → Submitted → In Review → Approved / Declined → (resubmit)**

## Phase 1: Flight Management Application

*Status: COMPLETE. In production November 2024. Source: CF92/1206779949*

Replaced the existing Flight Check Firebase app. Integrates job/flight creation, approval workflows, and field management into the [[Eclipse]] 2.0 framework.

### Scope

**In:** Job + flight list/create/edit/details screens, admin screen (channel/platform/creative unit management), user invitation/roles, SmartSheets field integration, same Eclipse 2.0 UI layout.

**Out (Phase 1):** Home screen, flight list screen, in-app notifications (email added later), change orders, white-label, programmatic activation model.

### Key Data Model

- **Job** = Campaign umbrella. Fields: Job # (PRJ + 6 digits, matches [[Snowflake]] Project #), Account Name, Campaign Code, Campaign Name, Advertiser Name, Business Unit, Notes.
- **Flight** = Individual media buy within a job. Fields: Channel, Platform, Creative Unit, Start/End Date, Budget, Publisher Name (for Direct Partner → [[#netsuite-po-sync|NetSuite sync]]), DIOS Audience Name (for [[custom-fusion-92-audience-api|DIOS-to-DAX API]]), and more.
- **Flight status workflow:** Draft → Submitted → In Review → Approved / Declined → (Draft again for re-submission)

### Phase 1 Timeline (all COMPLETE)

| Milestone | Owner | Completed |
|-----------|-------|-----------|
| Job List | Karen Prete | 2024-09-13 |
| Create/Edit Job | Karen Prete | 2024-09-25 |
| Job Details | Karen Prete | 2024-10-04 |
| Create/Edit Flight | Karen Prete | 2024-10-11 |
| Admin | Karen Prete | 2024-10-31 |
| Migration to Production | Karen Prete | 2024-11-21 |

### Phase 1 Feedback Highlights

Key changes made during UAT before/after go-live:

| Area | Change |
|------|--------|
| Platform names | Advantage360 → Soapbox; Adelphic → Viant; added Meta, X, CTV |
| Mandatory fields | Business Unit removed; Flight Name added (now mandatory + searchable) |
| Flight ID | 5-character random alpha-numeric |
| Commission/Tech % | Admin-only (hidden from regular users) |
| Export | Excel export added; multi-select output |
| Change log | Manual email distribution (interim until Notifications built) |

**Deferred to Phase 1.1 / Phase 2:** Frequency field, Platform Optimization Goal (free-form), Creative Unit Details, DCM Ad Serving toggle, HVM-dependent field visibility, horizontal layout export, color coding alerts.

---

## Phase 2: Metrics Data Consolidation

*Status: Gathering requirements (as of 2025-01-09 snapshot). Source: CF92/1360887813*

Removes reliance on SmartSheets for data entry. Adds Platform Spend data entry/viewing and bidirectional data flow with [[Snowflake]].

### Scope

**In:** Platform Spend toggle (shows direct partner data when available / manual entry when not), pacing % alert (exclamation mark when pace off by >10% or conversion data missing), bidirectional data flow app ↔ [[Snowflake]].

**Field additions:**
- Job: Platform Spend (rollup), Pace %, Impressions, Clicks, Conversions
- Flight: MRX Net (monthly input), Platform Net (monthly input), Pace (calculated), Clicks, Conversions, Pace %

### Phase 2 Timeline

| Milestone | Deadline |
|-----------|----------|
| Development Begins | 2025-01-03 |
| Fusion Testing | 2025-01-08 |
| Production | 2025-01-09 |

---

## Additional Fields & Change Log

*Status: IN PRODUCTION. Deployed 2024-11-27. Source: CF92/1437204481*

Added required flight fields and established a manual change log for approved-flight modifications.

### Field Additions (Flight Screen)

- Frequency (free-form)
- Platform Ad Account ID (free-form)
- Platform Campaign ID (free-form)
- Order ID (free-form)

*Note: These map to the [[fusion92-platform-ids|platform ID mapping]] used for Flight Check data matching.*

### Change Log

Manual email distribution at **8am and 1pm Pacific** to Media Ops (Shannon Hotz, Juliann Otto, Olivia Misterovich, Maria Cioletti — Fusion92).

**Included events:** Any status change from Submitted onward, field changes (who changed what field, previous → current value, timestamp, Job ID + Flight ID). Does NOT include initial Draft creation.

Change log is manual until the in-app Notifications system is production-ready.

---

## Notifications System

*Status: IN PROGRESS (December 2024 timeline). Source: CF92/1437302786*

Automated email notifications for flight status transitions. The notification batch jobs — status-change emails (4× daily) and pacing emails — are implemented in the [[workflows|workflows repo]] (`F92_workflow_app`, `dax_api/notifications/`) and triggered by Azure Functions timer functions. See [[workflows]] § Data Flow — Notification email path for the implementation details.

### Notification Matrix

| From | To | Recipients |
|------|----|-----------|
| Draft | Submitted | Media Ops, Shannon Hotz, Juliann Otto |
| Submitted | Approved | Creator, Media Ops, Shannon Hotz, Juliann Otto |
| Submitted | Declined | Creator, Shannon Hotz |
| Submitted → Draft (unsubmit) | — | Media Ops, Shannon Hotz, Juliann Otto |
| Approved → Draft | — | Creator, Media Ops, Shannon Hotz, Juliann Otto |
| Declined → Draft | — | Creator, Media Ops, Shannon Hotz, Juliann Otto |

**Batch:** Multiple flight approvals on a job → single batched notification. Single change → individual notification.

**Delivery cadence:** 4× daily (9am, 11am, 2pm, 5pm EST) — subject to revision post-launch.

---

## PRJ505 — UI Redesign

*Status: COMPLETE. In production 2025-08-13. Source: CF92/1437204494*

UI refresh to match Figma designs provided by Fusion92. Two objectives:

1. Align front-end UX with F92's Figma design (approved by F92 Creative + Leadership).
2. Fix Show Notes — display notes only for the clicked/selected job(s), not all jobs globally.

**Design reference:** [DAX AI Figma](https://www.figma.com/design/rIR8i86pBZYE6tejJUhFt5/DAX-Ai)

Timeline: Design 2025-05-14 → Dev 2025-05-29 → F92 Testing 2025-05-30 → Production final updates 2025-08-08.

---

## PRJ538 — App Feature Addition (Bulk Actions & Workflow Improvements)

*Status: COMPLETE. In production 2025-09-05. Depends on PRJ505. Source: CF92/1632141315*

Enhanced workflows: bulk flight actions, rejection notes in notification emails, new "In Review" status, change workflow, improved flight duplication.

### Key Feature Additions

- **Bulk submission/review/approval** across multiple flights at once
- **"In Review" status** — new stage between Submitted and Approved
- **Change Workflow** — new screens for post-approval change management
- **Rejection Notes column** added to notification emails
- **Flight Duplication improvements** — duplicated flights show who duplicated, default to Draft, no PO number

**Design reference:** [DAX AI Figma (ALDC Version)](https://www.figma.com/design/KrJuwBTAXw8KYVDqDLvE1Z/DAX-AI---ALDC-Version)

*Note: Figma represents the authoritative source; some discrepancies existed in written requirements — Figma takes precedence.*

Timeline: Design 2025-06-25 → Dev 2025-07-10 → F92 Testing 2025-07-18 → Production 2025-08-15.

---

## PRJ537 — Smartsheet Replacement

*Status: Consulting & Design (as of 2025-09-05). Depends on PRJ505 + PRJ538. Source: CF92/1633681409, CF92/1654030337*

Deprecates [[fusion92]]'s SmartSheet system and replaces it with native app functionality + bidirectional [[Snowflake]] data exchange.

### Scope

- Deprecate Smartsheet; move budget/spend data entry into app
- Introduce **Buyer role** (spend input, pacing view)
- Direct Partner flights display Platform Spend data from [[Snowflake]]
- Manual spend input when direct partner API data is unavailable
- Pacing exchange between app and data warehouse

### Smartsheet Requirements — Data Table Spec

**When direct partner data IS available:**
- One row per month (flight start → end); read-only; pacing notifications automated.

**When direct partner data is NOT available:**
- User can add rows via (+) button; select monthly time range (no overlapping); all fields nullable; user can edit/delete rows; no automated pacing notifications.

**When direct partner data becomes available:** API data takes priority and replaces manual entries.

**Filtering:** "Choose Date" button constrains table to date range within flight dates. Filter appears as removable bubble. Flight-to-date sum row at bottom updates dynamically with filter.

**Pacing formula:**
```
((Actual Platform Net to date / Planned Budget) / (Days into flight / Total flight days)) × 100
```

**Required columns:** Actual Impressions, Actual Clicks, Actual Conversions, Actual Platform Net.

### PRJ537 Timeline

| Milestone | Status |
|-----------|--------|
| Consulting & Design (starts 2025-07-16) | IN PROGRESS |
| Development & QA (starts 2025-09-22) | Not started |
| Fusion Testing | Not started |
| Production | TBD |

*Delay: Out-of-office periods for Karen, Shannon, Johanna.*

---

## NetSuite PO Sync {#netsuite-po-sync}

*Source: CF92/1660911619. Last updated: 2025-09-23*

Direct Partner flights in the DAX Media App automatically create and sync Purchase Orders in NetSuite.

### Eligibility

Only flights with **Channel = Direct Partner** are eligible. A "NetSuite Status" indicator and "Sync With NetSuite" button appear once eligible. Job number must match a valid NetSuite project.

### Creating a New PO (First Sync)

1. Click "Sync With NetSuite" (green indicator).
2. Confirm the dialog — this creates a new PO in NetSuite.
3. Progress spinner → success message → redirect to Job Details.

After first sync, these fields lock:
- **Channel** — locked to Direct Partner (only syncing channel)
- **PO Number** — auto-populated with NetSuite PO # (locked to protect sync)

### Field Mapping: Flight → NetSuite PO

| Source | Flight Field | NetSuite PO Field |
|--------|-------------|-------------------|
| Job | Job Number | Project Number |
| Job | Campaign ID + Campaign Name | Memo |
| Flight | Channel | Line Item Type (`Digital Media Costs: Digital Media - Direct`) |
| Flight | Flight ID | Flight ID (line item) |
| Flight | Start/End Date | Date range (line item) |
| Flight | Flight Name + Notes | Description (line item) |
| Flight | Budget | Quantity (Rate = 1) |
| Flight | Publisher Name | Vendor (exact match required) |

**Auto-set (not user-editable):**

| PO Field | Value |
|----------|-------|
| Employee | Project Manager from NetSuite project (fallback: ALDC user ID) |
| Project Manager | Shannon Hotz (Fusion-requested default) |
| Client Lead | Jody Messinger (Fusion-requested default) |
| External ID | Flight document UUID — **critical sync identifier; never visible to users** |

> **Why Quantity = Budget / Rate = 1:** Prevents NetSuite PO close-out issues when partial payments are recorded.

### Subsequent Syncs

After initial sync, the flight auto-syncs to the connected PO on every save (only if relevant PO fields changed). No confirmation required. Status returns to `In Sync` on success.

**Sync statuses:**
- `Not Synced` — new or unsynchronized flight
- `In Sync` — current state matches NetSuite
- `Out Of Sync` — last sync failed; retries on each save (does not block edits or progression)
- `Manual PO#` — sync connection unlocked (admin only; irreversible)
- `All NetSuite Sync Disabled` — global emergency disable

### Publisher Name Management

For Direct Partner flights, Publisher Name is a searchable dropdown sourced from the NetSuite vendor list (exact match required, case-sensitive). Admins can add names manually (displayed with `(Eclipse)` prefix in-app, prefix stripped before sending to NetSuite). When a vendor is added to NetSuite, move the manual entry to inactive.

### Unlocking a PO Connection (Admin Only)

Red **"Unlock NetSuite PO#"** button on synced flights. Irreversible — permanently breaks the sync connection. Channel + PO Number become editable; flight status → `Manual PO#`.

> **Warning:** After unlocking, the NetSuite PO must be manually updated or deleted. The sync connection cannot be restored.

### Key Technical Notes

- **Sync is one-way:** Flight → NetSuite. Manual NetSuite edits are **overwritten** on next sync.
- **External ID is the sync anchor**, not PO number. Pre-existing POs cannot be synced (no External ID). Only POs created by Flight Check sync are valid sync targets.
- **Duplicating a synced flight** clears PO number + External ID; the copy starts as `Not Synced` and can create a new independent PO.

### Troubleshooting

- [ ] Channel set to "Direct Partner"?
- [ ] Flight saved before clicking Sync?
- [ ] Job number matches a valid NetSuite project?
- [ ] Publisher Name in dropdown (exact NetSuite vendor name)?
- [ ] First sync: PO Number field empty?
- [ ] Error: Expand context and copy for support ticket.

---

## Flight Metrics Table

Source: Confluence TECH/1777106945 (Steven Offboarding).

The flight metrics table serves three purposes: show direct API metrics data, show legacy Smartsheet data, and allow manual data entry for platforms without API connections.

### Data Source Priority

1. **Direct API data** — always shown when available; overrides all other sources
2. **Smartsheet data** — shown for flights before 2026 when no API data exists
3. **Manual data** — shown when neither API nor Smartsheet data exists

For a select group of flights created in Flight Check during 2025 (when manual entry wasn't yet available), a mix of Smartsheet + manual data is possible: Smartsheet data shows for 2025 dates, manual entry is available for dates after 2025.

### Filtering Behaviour

Filtering differs by data source:

- **Direct API tables**: filterable to the day. Rows reorganise into monthly buckets but start/end at selected dates regardless of month boundaries.
- **Smartsheet rows**: filterable by row only. Any rows overlapping the selected date range are shown in full.
- **Manual rows**: filterable by row. Rows use arbitrary time frames as entered and are shown in full if a filter date falls within the row's range.

### Spend and Pacing

The spend value in the metrics table drives the `Actual Platform Net Spend` field in the flight, which is the base for all `Actual` spend and pacing calculations. Filtering the metrics table does **not** affect this value.

Manual metrics time periods cannot overlap and cannot be set outside of the flight start and end dates. The table may be locked in certain flight states or for certain user roles.

---

## Pacing

Source: Confluence TECH/1777106945 (Steven Offboarding).

### Flight Pacing Formula

```
(actual spend / total budget) / (days passed in flight / total days in flight)
```

### Job Pacing

Uses the same formula with these differences:
- Only includes flights that are **finished or currently running** (not-yet-started flights are excluded)
- `days passed` = min start date of included flights → current date (or last end date if all flights are done)
- `total days` = min start date → max end date of included flights

> **Known limitation:** When flights within a job have large variations in duration or budget, the job pacing calculation spreads all budget/spend across the full duration, which can produce misleadingly high or low values. Solutions discussed with Fusion92 include showing average flight pacing or weighted calculations, but none implemented yet.

### Pacing Notifications

- **Out of Range**: sent Tuesday and Thursday mornings for flights pacing above 110% or below 90%
- **Flight End**: sent every morning to flight creators the day after a flight ends, with the final pacing number

---

## Admin Features

Source: Confluence TECH/1777106945 (Steven Offboarding).

The Admin page allows:
- **User role management** — adjust roles for existing users
- **Change log export** — export an audit trail of the last several months of tracked changes
- **Dropdown management** — add new options to dropdown fields and move between Active and Inactive lists. E.g., the Account field in a job has a set list of accounts. Dependant dropdowns update accordingly.

### User Settings

Accessed through the username menu (top-right), which goes through the Eclipse app using application metadata. Currently only Notification settings are adjustable — users can toggle notification groups or individual notifications. Settings are stored in Cosmos and updated on save.

> **QA note:** In QA, the settings button appears twice — both lead to the same page. Cause unknown.

---

## Known Issues and Gotchas

Source: Confluence TECH/1777106945 (Steven Offboarding).

| Issue | Detail |
|---|---|
| **Standalone running** | Flight Check requires Eclipse 2 to be running for shared auth tokens. Both apps must be running for local dev and QA. |
| **User invite flow** | Known issues with new user password-setting. After a role change, user settings may behave unexpectedly — ask the user to log out and back in. Role changes auto-disable notification settings not available to the new role but never auto-enable anything. |
| **Cosmos document structure** | Flights and jobs are stored as generic "Application" JSON documents. Schema changes must be carefully managed. The difference between a flight and a job is encoded via an ID linking to a Metadata document for the respective form/table. |
| **Core API vs Dax API split** | The boundary is informal. All new features should go to the Dax API. General calls (auth, user info, document retrieval) go through Core API because they are generic ALDC logic. Custom logic (exports, calculations, metrics) goes through Dax API. Ideally everything would flow through the Dax API which can call Core internally. |

---

## See Also

- [[entities/repos/flight-check|flight-check (repo)]] — the Next.js frontend repo that implements this product. Architecture, developer guide, deployment, and API surface documented there.
- [[workflows]] — the Azure Functions backend ("DAX API") for this product. Implements the DAX API routes, notification batch jobs, NetSuite PO sync, Microsoft Ads token refresh, and Snowflake sync. See [[workflows]] for the full engineering reference.
- [[fusion92]] — client; platform connections, ALDC team
- [[fusion92-platform-ids]] — platform account/campaign/order ID mapping (used by Flight Check data matching)
- [[custom-fusion-92-audience-api]] — DIOS-to-DAX audience API (DIOS Audience Name field in flights)
- [[flight-check]] — ALDC operational data-pipeline validation process (different from this app)
- [[Eclipse]] — framework this app is built on
- [[Snowflake]] — data warehouse for bidirectional pacing data exchange (Phase 2 / PRJ537)
- [[nextcloud]] — Nextcloud folders used for DIOS audience data
