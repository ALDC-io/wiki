---
tags: [concept, architecture, azure, cost, infrastructure, test1, quality1]
aliases: [Azure non-prod cost reduction, Test 1 Quality 1 cost, Azure cost cleanup 2026-08]
sources: [session 2026-08-13, Azure Cost Management API, Azure CLI]
created: 2026-08-13
updated: 2026-08-13
---

# Azure Non-Prod Cost Reduction (Test 1 + Quality 1)

Cost-reduction pass across the two non-production [[Azure]] subscriptions on **2026-08-13**,
triggered by an Azure "payment past due" email that reached John Moran, who could not see
inside the subscription and asked what Test 1 was for. Combined run-rate reduced from
**~$620/mo to ~$280/mo (~$341/mo, ~$4,100/yr)** with no environment decommissioned and no
capability lost. Sibling of [[snowflake-cost-analysis]] and [[prefect-cost-analysis]].

Subscription inventory and naming live in [[azure-environments]].

## Baseline and result

| Subscription | Before | After | Saved |
|---|---|---|---|
| Test 1 (`6969113c-…`) | ~$372/mo | ~$180/mo | ~$190 |
| Quality 1 (`efe036d8-…`) | ~$247/mo | ~$120/mo | ~$130 |
| **Combined** | **~$620/mo** | **~$280/mo** | **~$341** |

"Before" = month-to-date run-rate 1–12 Aug (already net of the Superset/Cube containers being
stopped on 28 July, which had been $155/mo).

## What changed

| # | Change | Basis |
|---|---|---|
| 1 | `aldctestapspportal1c01` P1v2 **×2 → ×1 instance** | ~$117/mo. MEASURED ($234.53 App Service ÷ 2 instances) |
| 2 | Log level → `Warning` on `aldctestfnapcore1c01` + `aldcqafnapcore1c01` | ~$130/mo. **DERIVED / PENDING** — see below |
| 3 | Deleted Front Door `aldc-portal-afd` | ~$50/mo. MEASURED |
| 4 | Deleted `pg-aldc-superset-qa` | ~$24/mo. MEASURED |
| 5 | Deleted Launchpad/Superset footprint (see below) | ~$20/mo. MEASURED (SWA Standard ~$12 + ACR Basic $7.33) |
| — | Deleted empty shells `aldcqafnapqueuetrigger`, `ASP-aldctestrsgp1e-a775` | $0 — housekeeping |

> **⚠ PENDING VERIFICATION:** item 2 (~$130/mo) is the **only projected figure** — derived from
> measured ingestion rates after the trace volume collapsed, not from a bill. **Verify on the
> next billing cycle (September 2026).** This number was quoted to John Moran by email on
> 2026-08-13, so it needs to hold up. Everything else is measured from actual charges.

### Launchpad/Superset removal (Quality 1)

Deleted: `aci-aldc-superset-qa`, `aci-aldc-cube-qa`, `func-aldc-portal-qa` (+`plan-`),
`swa-aldc-portal-qa`, `staldcportalqa`, `aldc-launchpad-speech`, `aldcqaazcr1c01`.

**Deliberately preserved:** `aldc-vault-qa`, `aldc-cred-vault-qa`, and `func-aldc-cred-qa`
(+ plan + `staldccredqa`) — reasons below.

## Gotchas — read before repeating this

### 1. Scale instance COUNT, not TIER

Downgrading `aldctestapspportal1c01` **P1v2 → S1** broke `eclipse-test.aldc.io` (immediate
HTTP 503, not a slow start). S1 has **1.75 GB** RAM against P1v2's **3.5 GB**; the Python portal
app does not fit. Rolled back; app recovered.

The reasoning error worth remembering: the downgrade was justified by a **price comparison
between environments** ("Quality runs the same two apps on S1 for $102 vs Test's $234") without
ever checking the app's memory requirement. *A price comparison is not evidence that a workload
fits.*

Reducing instance **count** is safe by contrast — on App Service every instance runs *all* apps
on the plan, so removing one changes nothing about per-instance memory. Measured before/after:
65% → 65–66%. Zero downtime.

### 2. `rg-aldc-launchpad` exists in BOTH subscriptions — they are not the same thing

| Subscription | Contents |
|---|---|
| **Test 1** | **only `aldc-vault-test`** — the actively-used non-prod Key Vault |
| Quality 1 | the 13-resource Launchpad/Superset footprint |

Deleting "the launchpad resource group" by name would have destroyed `aldc-vault-test`.
**Always enumerate a resource group per-subscription before acting on it.**

### 3. A vault named for a project can hold other systems' credentials

`aldc-vault-qa` and `aldc-cred-vault-qa` sit inside `rg-aldc-launchpad` and look like Launchpad
artifacts. They are not. They held `snowflake-prod-admin`, `snowflake-admin-nonprod`,
`lectric--amazon-spapi--*` (4 secrets), `prefect-api-auth-string`, `eclipse-postgres-test`, and
`gep-prefect--amazon-ads/*--oauth`. Only `superset-*`, `cube-api-secret` and `portal-hmac-secret`
were actually Launchpad's. **Open a vault and read the secret names before deleting it.**
See [[credential-storage-tiers]] context in [[infra-credentials]].

### 4. An empty App Insights result is not a zero

Querying `AppTraces` for `aldctestfnapf921c01` returned nothing, which read as "the job never
runs". The **platform metric `FunctionExecutionCount`** (Azure Monitor, independent of App
Insights) showed **1 execution/day for 30 consecutive days**. The App Insights blank was
NOT-RECORDED, not ZERO. Cross-instrument before concluding absence — same lesson as
[[snowflake-cost-analysis]] lesson 7.

### 5. Log Analytics cost is trace chatter, not diagnostics

Retention was already at the 30-day minimum, so the lever is **volume**, not retention.
Measured split across both subs:

| Table | Combined 30d | Share |
|---|---|---|
| **AppTraces** | **38.2 GB** | **94%** |
| AppMetrics | 1.19 GB | |
| AppPerformanceCounters | 0.58 GB | |
| AppRequests | 0.52 GB | |

At ~$3.45/GB CAD (reconciles exactly: Test's $80.58 ÷ 24.06 GB). Traces were **100%
SeverityLevel 1 (Information)** from a **single app per subscription** —
`aldctestfnapcore1c01` (2,475,217 records/3d) and `aldcqafnapcore1c01` (1,722,683/3d).
Warnings across the same window: 97 and 29 records, ~0 MB.

**The fix (no code deploy, app-setting only):**

```
AzureFunctionsJobHost__logging__logLevel__default      = Warning
AzureFunctionsJobHost__logging__logLevel__Host.Results = Information
```

`Host.Results` is kept at Information deliberately so per-execution request telemetry survives.
Rollback = delete the two settings. Result: trace rate per 5 min went `740, 370, 740, 403 → 1`
(Test) and `210, 1260, 1260, 1349 → 1` (Quality), with AppRequests and warnings still flowing.

Note: `logLevel__default` does **not** suppress `Host.Function.Console` (Python `print()`/stdout)
— that needs its own key if it ever dominates.

### 6. Front Door has no "pause"

`aldc-portal-afd` was fronting a container stopped since 28 July (endpoint returned HTTP 504,
no custom domains bound). Front Door bills whether or not the origin is alive — you delete it or
you keep paying. `az afd profile delete` **rejects `--yes`**; use the REST `DELETE` on
`Microsoft.Cdn/profiles/{name}` instead. Deletion is async (~minutes in `Deleting` state).

### 7. A stopped Postgres flexible server restarts itself after 7 days

`az postgres flexible-server stop` halts compute billing but Azure **force-starts it after 7
days**. It is a pause, not a saving. Permanent removal requires deletion.

## Open items

- **Sean O'Grady's access** — account is **disabled** (`accountEnabled: false`) but still holds
  **Owner on all four subscriptions** (including Production 2) *and* **Global Administrator** in
  Entra. Not an active breach (a disabled account can't sign in) but stale standing privilege
  that reads badly in an audit. Azure Owner assignments removable by Paul/Vlad; the Global Admin
  role needs John or Lori.
- **Azure billing ownership** — the "payment past due" is unresolved. Billing lives on the
  **billing account**, a plane separate from subscription RBAC: John holds Entra
  *Billing Administrator* + *Global Administrator* and still sees "insufficient privilege",
  because Entra Billing Admin covers M365 billing, not a Pay-As-You-Go Azure account (tied to a
  single Account Administrator identity, likely Sean's). Route: Lori has identical roles and
  should try; otherwise a Microsoft support ticket to transfer billing ownership. **Risk: if the
  subscription is disabled it takes eclipse-test AND the live Fusion92 integration down.**
- **Do we need both Test 1 and Quality 1?** Worth ~$120/mo. Unresolved — see below.

## Test 1 vs Quality 1 — what is actually known

Both are live and structurally near-identical (portal web app + node web app, core_api
functions, task daemon, dispatcher, F92 function app, Cosmos, Postgres, Synapse, storage).

**Discriminating facts found:**

- **Test 1** carries the real hostnames people log into (`eclipse-test.aldc.io`,
  `eclipse2-test.aldc.io`) and a **live Fusion92 integration** —
  `aldctestfnapf921c01`: NetSuite PO sync, publishers feed, notifications, and a
  **Microsoft Ads token refresh on a daily 07:00 timer** (proven firing, 30/30 days). This is a
  production workload living in a test subscription.
- **Quality 1** has **no custom domains at all** — only raw `azurewebsites.net`. Its Launchpad
  half was dormant (`func-aldc-portal-qa`: 0 executions in 30 days while Running — a true zero).

**What is NOT established:** whether Quality is *intended* as a pre-production gate. Deployment
history didn't discriminate (Test last deployed 2025-07-25, Quality 2025-01-17, function apps
have no deployment records). High execution counts don't prove human use — a task-daemon +
dispatcher pattern generates executions by polling itself. **This is a process question for Vlad
Ryzhkov and Mike Stuart, not an Azure one.**

## Method note

Two catches on this pass came from a discipline worth keeping: **baseline before changing,
verify at the rendered surface after, and open things before deleting them.** The one change
that broke something (gotcha 1) was the one made from inference rather than measurement, and the
outage was only diagnosable *because* there was no baseline — which cost several steps.
See [[evidence-gated-changes]] framing in the global rules.

## See Also

- [[azure-environments]] — subscription → environment mapping and naming convention
- [[Azure]] — tool page
- [[snowflake-cost-analysis]] — the Snowflake-side equivalent (epic ALDC-651)
- [[prefect-cost-analysis]] — Prefect infra cost model
- [[eclipse-azure-deployment]] — how code reaches these subscriptions
- [[infra-credentials]] — vault pointers (gitignored)
