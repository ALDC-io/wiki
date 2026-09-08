---
tags: [entity, repo, core-api, aldc, eclipse, api, azure-functions]
aliases: [core_api, core-api, core api]
sources: [daily/2026-04-17.md, ~/.claude/CLAUDE.md, CORE/1467940876, CORE/1048248321, CORE/238387201, CORE/7929869, CORE/886603777, CORE/885620774, CORE/909737996, CORE/892796955, TECH/1777106945 (Steven Offboarding)]
created: 2026-04-17
updated: 2026-09-08
---

# core_api

ALDC's core API service. Lives at `C:\Users\PaulRussell\repos\core_api`. The backend API powering [[Eclipse]] — reads connection/template configs from [[CosmosDB]], handles warehouse-rebuild functions, and previously also held connector data-pull queries before they were migrated to the [[connector]] repo for [[Prefect]].

## Runtime

- **Python 3.11** (hard requirement — pinned by the Azure Functions worker)
- **Azure Functions v4** (`FUNCTIONS_EXTENSION_VERSION=~4`, `FUNCTIONS_WORKER_RUNTIME=python`)
- Deployed to [[Azure]] Function Apps (one per env — see table below)
- Reads all runtime config from env vars, loaded locally from `local.settings.json`

## Environments (function app → resources)

| Env | Function App | Resource Group | Storage (core / queue) | [[CosmosDB]] |
|-----|--------------|----------------|------------------------|--------------|
| **prod** | `aldcprodfnapcore1c01` | `aldcprodrsgp1c` | `aldcprodstaccore1c01` / `aldcprodstacqueue1c01` | `aldcprodcsdb1c01` |
| **qa** | `aldcqafnapcore1c01` | `aldcqarsgp1c` | `aldcqastaccore1c01` / `aldcqastacqueue1c01` | `aldcqacsdb1c01` |
| **test** | (confirm — name not captured yet) | `aldctestrsgp1c` | `aldcteststaccore1c01` / `aldcteststacqueue1c01` | `aldctestcsdb1c01` |

All envs share tenant `e2bae64b-6e5f-4f55-b81c-ada320c7f572`. Full per-env secrets in `vault/core-api-local-settings.md`.

## Role in the pipeline

core_api is the **Eclipse-side** control plane. It is **not directly connected to [[Snowflake]]** in the Prefect world — the data path is:

```
connector (Prefect flow) ──► Azure Storage Account ──► Snowflake query pulls into DWH
            │
            │   (connector = transport layer)
            ▼
         core_api (Eclipse API)
```

So data **transport** is owned by the [[connector]] repo; core_api's job is Eclipse-API surface area and warehouse-rebuild functions — not moving data itself.

> **Open question (2026-04-17):** the exact role split between core_api and connector is still fuzzy. Today's KT note: "for prefect connector/template — connection through PBI — not core_api anymore." That phrasing needs unpacking — specifically what "connection through PBI" means in the Prefect flow context.

## Key modules / endpoints

### `route_warehouse.py` — warehouse rebuild

The most frequently-touched module when debugging bad data. Key function:

- **`warehouse_recreate_current`** — rebuilds the data that feeds the `CURRENT_*` and combined views in [[Snowflake]]
  - Invoke via [[Postman]] (Steven's collection has the request pre-wired)
  - On failure: check [[Snowflake]] **Query History** for failed queries. Use the `ACCOUNTADMIN` role to see the **un-redacted** query text — otherwise parameters are masked

### `route_work.py` — work lifecycle (pick / complete / visibility timeout)

Governs how the [[Eclipse]] connector fleet dequeues and executes work items.

**Key functions:**
- **`work_pick`** (~line 706) — dequeues the next eligible partition from the connection's Azure Storage Queue. The queue message **visibility timeout** is set here via `receive_message`; hard-coded as `60*60*4` = 4 hours (introduced commit `5fb7de4`, also present in the GP-277 pick-fix `85557db`).
- **`work_pick_agent`** (~line 966) — connection-scoped pick variant (used when the agent has `connection_authorized` set). Same visibility timeout constant.
- **`work_complete`** — acknowledges the dequeued message (deletes it from the queue), preventing it from resurfaces.

**Visibility timeout — 2026-06-11 change ([[GP-257]]):**
Reduced from `60*60*4` (4h) → `60*60` (1h) on the TEST core_api STAGE slot (`aldctestfnapcore1c01-stage`). Rationale: max real report latency proven at ~25 min across 959 completions (p99 ~17 min), so 1h has no double-pick risk while allowing a crashed executor's message to recover 3h sooner. The 4h value was originally conservative but caused OOM-killed executors' partitions to remain locked for 4h before the zombie sweep could act. The change is deployed to the STAGE slot only; the PROD slot still carries 4h (as of 2026-06-11).

**Rollback:** `git checkout 85557db -- v1/route_work.py && func publish --slot stage` restores the 4h constant on stage.

> **Note:** The connector itself never sets the visibility timeout — it only relays `queue_pop_receipt`/`queue_id` between `/work/pick` and `/work/complete`. All visibility logic lives here in core_api.

### Other surface areas (from Postman collections)

Based on the request organization in Steven's and Lawrence's collections — see [[postman-collections]] for the full catalog:

- **account/** — `list`, `describe`, `encode`, `invoice`, `clientinfo`, etc.
- **dataset/** — `synchronize`, `describe`, `list`, `request`, `query` (DAX + Snowflake-backed)
- **application/** — `clone`, application-container management
- **notification/** — notifications surface
- **warehouse/** — `warehouse_recreate_current` and related

## Running locally

Full runbook: [[core-api-local-setup]]. TL;DR:

1. Python 3.11 venv
2. Azure Functions Core Tools + Azure VS Code extension
3. `local.settings.json` from `vault/core-api-local-settings.md`
4. `func start` (or F5 in VS Code)
5. Point [[Postman]] at `http://localhost:7071`, use `x-function-key: none-for-local`
6. Use a real Fusion or GEP `account_id` — those are the accounts the collection is pre-wired against

## Debugging workflow

When an endpoint misbehaves:

1. Reproduce in [[Postman]] against local core_api
2. Inspect terminal / VS Code Functions output for exceptions
3. Check [[Snowflake]] Query History (as `ACCOUNTADMIN` for un-redacted text) if the call touches warehouse data
4. Check [[CosmosDB]] `schema` container for stale template documents if the failure is around Eclipse template resolution
5. Follow [[debugging-warehouse-loads]] for the full decision tree

> **⚠ Gotcha — the generic 500 masks the real exception (`v1/__init__.py:1035-1056`).** The top-level handler catches *every* unhandled exception and returns the **same** message — `"This route function is not currently implemented, no results found at route or incorrect route specified."` (500). So that text does **not** mean the route is missing — it usually means the handler raised a normal Python exception. Worse, it tries `json.loads(str(e))` and, when `e` isn't a `raise_error()`-formatted JSON string, the `traceback` it returns is the **handler's own `JSONDecodeError`** (`Expecting value: line 1 column 1`), not the real traceback. **The real error is only in the Azure Function logs** (the handler `print(str(e))`s it). To diagnose: tail the function app logs / App Insights, or reproduce locally. Example (2026-06-03, [[GP-277]] Fix C): a `TypeError` from a call-site arg-count mismatch (`warehouse_schema_match_tolerant` called with 7 of 8 positional args, missing `session_id`) surfaced as this generic "route not implemented" 500 on `/warehouse/merge`. Static-read the changed code's call sites before chasing infra.

## Migration from core_api → connector

Historically, queries that pulled data from external APIs lived in core_api. 

For the [[Prefect]] migration:

- **Transport/data-pull queries** have been moved out of core_api and into the [[connector]] repo (`connector/accounts/<ACCOUNT>/deployments/`)
- **Core API surface** (Eclipse backend, warehouse rebuild triggers) **stays** in core_api

This matches the broader split: Eclipse (= core_api + web UI) is the control plane; connector is the data plane.

## Old core vs new core

There are **two lineages** of core_api still visible in the Postman collections:

- **New core** — current production. Target with **Steven's Dax and Core Collection**
- **Old core** — legacy surface. Target with **Analytic Labs Control v1 (LAWRENCE)** collection

Most endpoints have converged, but if a bug is reported against an endpoint only present in Lawrence's collection, confirm with the team whether it's hitting old or new core before chasing it in source.

## Deployment

core_api deploys like other ALDC [[Azure]] web apps / function apps: [[GitHub Actions]] builds the container and pushes it to the staging slot, then a manual **swap** in the Azure Portal points production traffic at the new slot. See [[eclipse-azure-deployment]] for the full flow (same pattern as Eclipse) and [[GitHub Actions]] for the workflow-level detail.

> **✅ Real deploy workflow EXISTS (corrected 2026-07-23; the 2026-04-29 "dummy stubs" note was stale).**
> `deploy_az_webapp_container.yaml` = **"Deploy to Azure (Staging)"** (workflow id `192556804`) is the working
> container deploy: `rollback-check → build → deploy` to the `stage` slot of `aldcprodwbapcore1c01`. Manual dispatch
> `gh workflow run 192556804 --repo ALDC-io/core_api --ref eclipse-2.1 -f force_deploy=true`, then a **slot swap**
> to prod. Full procedure + gotchas (push-trigger fails by design; `force_deploy` needed; mutable-tag rollback;
> slot-specific `jwt_secret`) in [[eclipse-azure-deployment]] § Pitfalls. (`deploy_on_premise.yaml` remains a stub.)

> **Default branch changed to `eclipse-2.1` (2026-04-29).** Previously `main`. Changed after an incident where deploying from `main` caused the dummy workflow to overwrite the Actions UI. See [[eclipse-azure-deployment]] § Incident: 2026-04-29 wrong-branch deploy.

### Hosting — Azure Functions, NOT an on-prem container (clears a recurring confusion)

core_api runs as an **Azure Functions app** (FastAPI-in-a-Functions-container on App Service). Per env:

| Env | Function App | Resource group | Cosmos it talks to |
|---|---|---|---|
| TEST | `aldctestfnapcore1c01` | `aldctestrsgp1c` | `aldctestcsdb1c01` (db `core`) |
| PROD | `aldcprodfnapcore1c01` / `…c03` | `aldcprodrsgp1c` | `aldcprodcsdb1c01` |

**There is NO on-prem core_api container to `docker exec` into.** `192.168.31.20` (`aldcsuptdock1c01` / Nostromo, Portainer) and `wks-agent` (`192.168.31.210`) host **connector agents + observability**, not core_api. To run core_api code against a real env you either (a) call the Function App over HTTPS with the **master token** = `base64(MASTER_CLIENT_ID:MASTER_CLIENT_SECRET)` from that app's settings (route `/v1/{function}/{option}`, anonymous authLevel, raw `Authorization` header — no `Bearer ` prefix), or (b) **run it locally / in-process** pointed at the target env by exporting that app's settings (`az functionapp config appsettings list -g <rg> -n <app> -o json`). Full local runbook: [[core-api-local-setup]].

### Eclipse dataset sync (`dataset_synchronize`) — silent-empty gotcha + fix

Synchronizing an Eclipse **Dataset** (`type:data_model`) over the deployed HTTP path (the Explorer ⋮ → **Synchronize**, or `POST /v1/dataset/accountsynchronize`) can **toast/return success while writing an EMPTY `definition`** (0 tables/columns/measures → the Eclipse field picker shows "Nothing found"). Two independent failure modes, both in `model_get_metadata` (`route_dataset.py`), which probes **every non-hidden column** via a `model_get_cardinality` `executeQueries` round-trip:

1. **Timeout on large models** — hundreds of sequential Power BI `executeQueries` calls exceed the Azure gateway's ~230s limit, so `dataset_update` never runs. (Confirmed GP-293, model `2d8587b5` = 42 tables.)
2. **`model_get_cardinality` returns `None`** for some column → `TypeError: '<=' not supported between 'NoneType' and 'int'` at `route_dataset.py:1280` (`if column_cardinality <= 100`) → crashes before the write. Data-dependent (only if a column's cardinality probe yields no row). (Confirmed GP-291.)

**Fix / workaround (proven):**
- **Preferred** — run core_api's own `dataset_synchronize(account_id, dataset_id)` **in-process locally** (no gateway timeout), env from `az functionapp config appsettings list`. This completes the full scan and writes the correct `definition` via `dataset_update`. Used for GP-293 (`2d8587b5` → 29 tables / 223 cols / 199 measures incl. the 4 MAP tables + 21 MAP measures). Driver: `aldc-launchpad/pbi_ops/_gp293_coreapi_local_sync.py` (import `route_dataset`, feed settings via stdin JSON; needs `pip install azure-functions twilio mailjet_rest croniter` on Python 3.11/3.13).
- **If mode 2 (None-cardinality crash) also fires** — surgical Cosmos edit of the `dataset` doc's `definition` (remove dead entries from `tables`/`columns`/`measures` + `format_strings` + `sort_by_columns`, back up first, `upsert_item`): `aldc-launchpad/pbi_ops/_gp291_cache_surgical_edit.py`.
- **Mode 2 (None crash) — FIXED 2026-07-22, core_api PR [#246](https://github.com/ALDC-io/core_api/pull/246).** Guard added at `route_dataset.py:1280`: `if column_cardinality is not None and column_cardinality <= 100`. Validated in-process against TEST `da8904db` "Sales Model" (e80ffd34) + "Marshall Test" (0025d4b4), PBI `66151728` → 17 tables / 116 cols / 86 measures each, no crash. Deploy: merge main → container build → stage slot → swap to prod (rollback = swap back / revert single commit).
- **Mode 1 (gateway ~230s timeout) — STILL OPEN (logged, not ticketed per Paul 2026-07-22).** The fix above does NOT address it: for large models the per-column cardinality scan on the HTTP sync path can still exceed the Azure gateway ~230s limit. **Mitigations to pursue:** batch the cardinality probes into fewer `executeQueries` calls, raise the function/gateway timeout, or move the per-column scan off the synchronous request path (async). Until then, use the in-process local runner for large-model syncs.

### Eclipse dataView/dashboard data — the `capacity_options.dataset_name` name-resolution trap

**Symptom:** an Eclipse-2.1 dashboard/dataView renders its *structure* (layout, KPI cards, filters, titles) but **every visual shows "Error loading data"** — and there is **no client-side network/console error** (the data fetch is server-side RSC → core backend → PBI, so it never appears in the browser network tab).

**Root cause (GP-293, 2026-07-22):** the Eclipse data path resolves the target PBI model **by NAME**, using the `dataset` doc's `capacity_options.dataset_name` — **not** only `capacity_options.dataset_id`. If the stored name is stale/wrong (model was renamed, or the Eclipse dataset was created with a placeholder name), name resolution returns **HTTP 404 `PowerBIEntityNotFound`** and all `executeQueries` fail. GUID-based paths (the getInfo `dataset_synchronize` scan, and delegated `PBIClient.execute_dax` by GUID) **still succeed and mask the bug** — so the field picker/schema look fine while every dashboard visual is blank.

**Diagnosis that nails it:** connect via XMLA **by name** (`XmlaClient(ws, name, token)`) — a mismatch throws `PowerBIEntityNotFound (404)` at "Getting the PBI shared database name". Cross-check the model's live name with `PBIClient.list_datasets(ws)` vs `capacity_options.dataset_name`. A/B: repoint → error; correct the name → renders.

**Fix:** set `capacity_options.dataset_name` on the Cosmos `dataset` doc to the model's **exact** live workspace name, then re-load. Tooling: `aldc-launchpad/pbi_ops/_gp293_fix_dataset_name.py` (verify/fix/rollback). **Rule: whenever creating or repointing an Eclipse dataset, verify `capacity_options.dataset_name` == the model's live PBI name, not just the GUID.** (GP-293 example: doc said `"Navira Marketing Model (Test)"`; live name was `"Marketing Model"`.)

## Eclipse-2.1 Explorer backend — code location & branch grounding (READ FIRST before touching Explorer)

**The Explorer feature** (Datasets / DataViews / Visuals / Dashboards / Catalog, plus RBAC and per-client data
isolation) for the **eclipse-2.1** product (`eclipse.analyticlabs.io` + its staging slot) is served by **`core_api`
ON THE `eclipse-2.1` BRANCH — and ONLY that branch.** `main` and the various `fix/*` branches (e.g.
`fix/dataset-sync-cardinality-none-guard`) **do not contain the Explorer backend at all** — a grep for
`explorer_*` / `rbac_role_assignment` on them returns nothing, which is misleading.

On `core_api@eclipse-2.1` the relevant code is:
- `v1/route_explorer.py` — Azure-Functions handlers for dashboards/widgets/catalog; reads the Cosmos
  `container_explorer_visual` / `explorer_data_view` / `explorer_dashboard` containers.
- `api/dashboards/`, `api/visuals/`, `api/data_views/` (`router.py` + `db.py` + `schema.py`) — newer
  FastAPI-style modules.
- `api/rbac/role_assignments/` + `api/permission_checker.py` — RBAC / `rbac_role_assignment`.
- `api/power_bi_model_client.py` and `v1/route_dataset.py` (`model_query`) — the PBI `executeQueries` path
  (fixed-pool `impersonatedUserName`, see the dataset-sync section above).
- The **frontend** is the **`eclipse` repo on its own `eclipse-2.1` branch** (Next 15 App Router; proxies to
  this backend). Both repos have an `eclipse-2.1` branch — use it for both.

**⚠ Do NOT analyze `eclipse_exp` for eclipse-2.1 questions.** `eclipse_exp` (FastAPI + **Postgres**, ACA,
`eclipse-exp.aldc.io`) is a *separate next-gen successor for NEW tenants* — different storage, different
deployment. Its route shapes look nearly identical to Explorer's, which makes it an easy wrong turn. The
eclipse-2.1 product (Navira/GEP, GP-261/GP-293) stores Explorer content in **Cosmos** via `core_api@eclipse-2.1`,
**not** in eclipse_exp's Postgres. (The `entities/repos/eclipse.md` page is flagged stale and frames eclipse_exp
as "the successor," which contributed to this confusion.)

**Grounding rule:** before investigating any eclipse-2.1 Explorer behaviour (data isolation, filter enforcement,
RBAC, the query path), `git grep`/read the **`eclipse-2.1` ref of BOTH `eclipse` and `core_api`** — not whatever
branch happens to be checked out. Mis-grounding here (analysing `eclipse_exp` + the wrong `core_api` branch) cost
significant time in the GP-293 session (2026-07-22). Confirm the branch first; the wiki + your own session
evidence (Cosmos containers, `route_dataset.model_query`) point to `core_api@eclipse-2.1` — trust that over
route-shape inference.

### Explorer per-client data isolation — SHIPPED (GP-299, prod 2026-07-23)

> **✅ FIXED + DEPLOYED TO PROD 2026-07-23 (GP-299, PR [#247](https://github.com/ALDC-io/core_api/pull/247)).**
> Option A implemented: `get_dashboard_visual_data` now passes `dashboard.filters`; `request_visual_data`
> sanitizes the request **at entry** (via `visuals.lib.enforce_locked_filters`) so **every** query path (default,
> previous-period, YoY, table-comparison) inherits the enforced scope. Enforcement covers **both `mode:locked`
> AND `mode:hidden`** filters (Eclipse's `hidden` mode also carries a fixed `lockedValue` — `hasLockedValue =
> Locked || Hidden` in the frontend — so it was bypassable the same way). Hardening: **case-insensitive** field
> matching (DAX names are case-insensitive, so `brand` vs `Brand` can't slip the strip); an **inclusive-operator
> whitelist** in `dashboards.lib.locked_filter_conditions` (only `Equals`/`IsOneOf` may be locked — a `NotEquals`
> lock would *widen* scope); and **fail-closed** (raise `CoreApiException(500)`, never skip) on a
> misconfigured/unparseable lock. 26 tests. Deployed via **stage→prod slot swap** on `aldcprodwbapcore1c01`
> (Production 2). `jwt_secret` is slot-specific, so a stage-minted token 401s on prod (expected). GP-300 dep upgrade
> shipped in the same swap. **The finding below is retained for context; it describes the pre-fix state.**
>
> **Not yet done (follow-ups):** quote/whitespace field-drift normalization (casefold handles casing only);
> dashboard write-time validation of locked-filter fields against dataset column locators; live crafted-request
> proof with a real client-scoped user. Direct visual/dataView
> endpoints remain guarded by `Visual_View`/`DataView_View` + grant discipline (no locked-filter enforcement there —
> a dataView isn't bound to one dashboard's lock).
>
> **⚠ 2026-07-27 — this fix was INCOMPLETE. It covered the data path only; see [[GP-304]] below.**
> **Bypass B is now settled from code** (no client tenant required): the RBAC hierarchy is **flat** —
> `build_permission_map` parents *every* non-account resource to the **account**, so there is no
> dashboard→visual inheritance edge. `external-user` carries `[Account_Access]` only, and a dashboard-scoped
> `viewer` grants `Visual_View` on the **dashboard's** resource id, not on visuals. So a client 403s on the
> direct endpoints **by role design**, not by per-dashboard config that could drift.

#### ⚠ GP-304 — locked filters did NOT cover the filter-VALUE endpoint (found 2026-07-27)

**The durable lesson, and the one to carry into any future scoping work: a locked filter is only as strong as
the *narrowest* route that queries the dataset. Enumerate EVERY route, not just the obvious data route.**

GP-299 secured `.../visuals/{id}/data/`. It did not touch:

```
GET /v2/dashboards/{dashboard_id}/dataset/fields/{field_locator}/values/
```

which is authorised by **`Dashboard_View` alone** — the exact grant a released client holds on their own
dashboard — and was passed **no locked filters** (`request_field_values` issued its DISTINCT query with
`filters=[]`). **No tampering required**: this is the endpoint that populates filter dropdowns, so it is
reachable from an ordinary browser session.

- **Measured on prod** against a dashboard locked to one brand: **177 brands**, **86 vendor email addresses**,
  161 manufacturer names, 7 internal account-manager names. 54 of 112 columns enumerable. A second client's
  dashboard returned the identical 177 — the lock was ignored **uniformly**, not misconfigured on one dashboard.
- **Seller identity did not leak — but only by accident.** Every seller column exceeds the endpoint's
  **200-cardinality cap** (`Seller ID` 759/1,556) and returns null. The **cap**, not the lock, was protecting it.
  A fragile guarantee: it would fail silently the day a seller dimension fell below 200 distinct values.
- **The tell that makes this unambiguous:** the comment on the data route 30 lines below says *"locked filters
  are a security boundary and always apply"* — while this route applied none. An oversight against the
  codebase's own stated invariant, and **no GP-299 test touched it**.
- **Fix:** thread `dashboards.lib.locked_filter_conditions` through `get_dataset_field_values` →
  `request_field_values`, landing in `DatasetRequest.filters` — the *same slot* the data path uses via
  `visuals.lib.create_dataset_request`. Reuse the helper rather than reimplement, so the inclusive-operator
  whitelist and fail-closed behaviour come along for free. Zero-regression by construction: no locked filter →
  `filters=[]`, byte-identical to before, so the internal all-brands tier is untouched.
- Branch `feature/GP-293-fieldvalues-locked-filter` off **`eclipse-2.1`**, 11 tests. **Not yet deployed.**

> **⚠ 2026-07-29 — that fix was itself INCOMPLETE. It closes exactly ONE column. See the section
> immediately below before treating GP-304 as solved by `filters` alone.**

##### ⚠ GP-304 part 2 — passing the lock through scopes only SAME-TABLE columns (measured 2026-07-29)

**The durable mechanism, and the reason a second bound was needed: the field-values query is
`CALCULATETABLE(SUMMARIZECOLUMNS(<col>), KEEPFILTERS(<lock>))`, and that shape narrows only columns on the
SAME TABLE as the locked column. A filter on a different table is silently ignored.**

Measured on prod against Brinno's `Brand='Brinno'`-locked dashboard, *with* the part-1 fix applied:

| Column | result |
|---|---|
| `'Brand'[Brand]` | 177 → **1** ✅ |
| `'Product'[Brand]` | 177 → **177** ❌ — the identical roster, one column away |
| `'MAP Violators Daily'[Brand]` | 112 → **112** ❌ |
| `'MAP Violators by Brand'[Brand]` | 81 → **81** ❌ |
| `'Vendor'[Vendor Email]` | 86 → **86** ❌ |

- **Positive control, so this is not a probe artifact:** same-table *does* narrow — a `Product[Brand]` lock
  takes `Product[Manufacturer Name]` from **162 → 1**. Filters are applied; they just don't propagate.
- **Adding a measure** to the query scopes every *brand* column to 1 — the scoping comes from blank-row
  elimination — but leaves `Vendor` at 86, because **`'Vendor'` has no relationship path to `'Brand'` at all**.
  So no filter shape can ever scope it, and the measure cannot be chosen generically on a dataset-agnostic
  route. **Shapes tried and rejected:** `fieldFilters=[lock]` (still 177); adding the locked column to the
  group-by (**empty payload**).
- **Fix (`06aa015`) — bound *which columns* may be enumerated, not just how they are filtered.** New
  `dashboards.lib.assert_field_is_dashboard_filter()`: the dashboard-scoped route may only serve columns the
  dashboard **configures as a filter**; anything else raises `CoreApiException(404)` (matching
  `get_visual_from_dashboard`'s containment check; 404 not 403 so the response doesn't confirm the column
  exists). Exact match — the bypass *is* a same-named column on another table, so suffix matching would
  reopen it. Mode-independent, fails closed on a dashboard with no filters, short-circuits before the model is
  queried.
- **Why that is the right answer rather than a blunt deny:** prod serves **54 enumerable columns** while every
  MAP dashboard — client *and* internal — configures exactly **3** (`'Brand'[Brand]`,
  `'Navira MAP Violators'[Selling FBA (Yes/No)]`, `'Navira MAP Violators'[Avg ASINs Listed]`). The other ~51
  have no UI function on this route; they are reachable only by calling the API directly, which is the attack
  rather than the feature. **The allow-list *is* the dashboard's filter bar**, so it closes everything at once —
  including the columns scoping provably cannot reach — at zero functional cost, and leaves the internal tier's
  values unchanged.
- **Residual, stated rather than buried:** `'Navira MAP Violators'[Avg ASINs Listed]` remains served
  **unscoped** on client dashboards (55 values) because it *is* a configured filter and Brand cannot scope it.
  Non-identifying numerics, but cross-client, and **not closed**. Separately,
  `'Navira MAP Violators'[Selling FBA (Yes/No)]` already **404s** on this route because its column name contains
  `/`, which breaks path routing — a *configured* client filter that can never load its values. Own ticket.
- **Not yet verified:** the allow-list applies to **every** dashboard with a locked filter, including the ~21
  combined client **sales** dashboards. Only 4 dashboards' filter configs were inspected. Sweep all of them
  (read-only) before swapping.

**⭐ The process lesson, which outlives the bug: the deploy gate would have certified the fix while the
vulnerability remained.** The e2e `D1` test asserted on the single locator the original probe happened to
measure, so after deploying part 1 it would have gone **GREEN** while `'Product'[Brand]` still returned all
177 brands. *When you fix an enumeration bug, the test must enumerate every equivalent route to the same
data — not the one instance you found first.* D1 now sweeps 4 brand-bearing columns × 19 dashboards, and a new
`D5` asserts sensitive non-brand dimensions are scoped **or refused**.

**Merge is dead-locked on process, not code.** PR #250 is OPEN/MERGEABLE with **11/11 CI green**, but
`eclipse-2.1` requires an approving review: the author cannot self-approve, Paul's token is `admin: false`, and
the green `review` check is the **Claude bot, which only COMMENTED** (0 approvals). ⚠ **A green bot "review"
check does not satisfy a required-approval rule** — don't read the check list as merge-readiness.
- **Routes confirmed CLOSED (no action):** `/v2/datasets/{id}/fields/.../values/` and
  `/v2/data_views/{id}/dataset/fields/.../values/` check `Dataset_View`/`DataView_View` via
  `check_dependency(require_active_account, …)` — i.e. against the **active account**, which `external-user`
  lacks. Note this is a *different check shape* from `check_path`: account-level `Creator` **does** hold both,
  so any internal Creator can enumerate any dataView's values account-wide.

**Two process lessons worth more than the bug:**
1. **A code read answered what was parked on infrastructure.** GP-299 deferred Bypass B to "the first client
   tenant" for ~4 days; the router dependency plus the role definition settled it in minutes. Check whether a
   question is *actually* blocked on an environment before parking it.
2. **`email-validator` is absent from `requirements.txt`**, so `api/password_reset/schema.py`'s `EmailStr` makes
   **every** unit test in this repo fail to *collect* on a clean install — GP-299's own tests included. These
   tests are therefore not running in any environment built from `requirements.txt` alone. Install it locally to
   run the suite; worth its own ticket.

#### ⭐ A visual can scope ITSELF — `visual.options.filters` is server-enforced and merge-only (GP-293, 2026-07-24)

**The most reusable finding in this section: the answer to "how do I put a client-scoped visual on a dashboard
whose lock can't reach that grain?" — and it needs no code change.**

- **`explorer_visual.options.filters` is applied SERVER-SIDE and MERGED with (never replaced by) the client
  request body.** So a per-client clone of a visual can carry `options.filters = [Brand[Brand]=<client>]` and be
  correctly scoped **independently of the dashboard's locked filter**.
- **Proven by a hardened tamper battery** (throwaway `Product[Default Vendor]`-locked dashboard, then repeated
  live on `a4ec0d1d`): `filters=[]` → the client's own rows; `Brand equals <other client>` → **0 rows** (merge,
  cannot widen); `Brand is_one_of [own, other]` → own rows only (intersection); `Brand not_equals own` →
  **HTTP 400** (GP-299's inclusive-operator whitelist); tampered on **every** query path (`default`,
  `expanded-timeframe`, `previous-period`, `year-over-year`, `table-comparison`) → 0 rows; holds under 7d/90d/205d
  timeframe overrides. A client can only ever **narrow to empty**, never widen.
- **This corrects an earlier conclusion on this page.** We reasoned that because `explorer_data_view` docs have
  **no filter field**, row scoping could come *only* from the dashboard locked filter (GP-299) or RLS. The
  dataView half is true; the conclusion was not — the **visual** layer was never checked. The lead that cracked
  it: `SELECT * FROM explorer_visual` found `506db98c` already carrying `'Account'[Account Name]='BCBSM'`.
- **Also disproved: an injected dashboard lock does NOT necessarily break a foreign-grain visual.** Components
  with `ignore_global_filters` **true and false** rendered identically on a vendor-locked dashboard, because the
  MAP seller table groups on the **terminal hub** — so the `Product[Default Vendor]` predicate is **inert**, not
  fatal. The "single value … cannot be determined" 500s were specific to the **island table** and to grouping the
  **by-brand** table. Don't over-generalise that failure.
- **Cost of the pattern:** one visual clone per client — loses "edit once, all inherit", so a column change
  becomes N scripted edits. The `dax_query_builder` `FILTER(ALL())` change is therefore an **optimisation, not a
  prerequisite**.
- **Comparison columns:** Eclipse auto-appends `Prev %`/`YoY %` per measure. `options.show_previous_period=False`
  + `options.comparison_measures=[]` removes them (mechanism established by GP-298).
- **Ops lesson:** a visual-data payload exposes **`lastRefreshedAt`**. A model refresh mid-session changes
  fingerprints and *looks* like a regression from your edit — A/B by rolling the change out and re-measuring
  under the same refresh generation before concluding anything.
- Tooling: `aldc-launchpad/eclipse_ops/_gp293_optionC_test.py` (experiment; creates only new docs, full
  rollback), `_gp293_pilot_embed_brinno.py` (`create`/`embed`/`verify`/`rollback`). Evidence:
  `aldc-launchpad/docs/evidence/gp293.md` §3d.

#### GP-293 — embeddable MAP component: what scopes vs. what doesn't (2026-07-24)

Investigating a **reusable MAP Violators component droppable into any client dashboard** surfaced a hard
interaction between GP-299's enforcement and Eclipse's DAX builder. Durable findings (read with the
self-scoping finding above, which supersedes the "only three options" framing below):

- **The per-client MAP fan-out ALREADY WORKS and is GP-299-safe.** The 19 dedicated **"MAP Violators —
  <Client>"** dashboards (prod Cosmos `aldcprodcsdb1c01`) each lock on **`Brand[Brand]`** and share ONE visual
  **`63d41094`** ("MAP Violators — Sellers", dataView `44388094`). Verified live: Brinno=6, Rain Bird=64,
  Slobproof=4, Dalen=52 sellers — each shows only its own sellers, **stable under crafted-filter tampering**
  (GP-299 strips the tampered Brand filter, re-injects the client's). This *is* the working reusable component.
- **Why it works — the pattern:** display columns from the **terminal seller-hub** `Navira MAP Violators`
  (no outgoing relationship), numbers from the **daily measures** (`MAP Daily Violations`, etc.) on
  `MAP Violators Daily` (**related to `Brand`**). A `Brand[Brand]` lock cascades Brand→Daily and scopes cleanly.
- **The catch — combined dashboards that lock on `Product[Default Vendor]` (e.g. "Brinno Dashboard"
  `a4ec0d1d`) can't embed a scoped MAP visual as a pure data-model change.** GP-299 injects the dashboard's
  locked filter into **every** visual, and `api/dax_query_builder.py` renders it as
  `SUMMARIZECOLUMNS(<group cols>, KEEPFILTERS(<simple predicate>), <measure>)`. A `Product[Default Vendor]`
  filter cannot reach the Brand-grained MAP data single-direction, and the **bare simple-predicate
  `KEEPFILTERS`** throws PBI 400 **"a single value for column … cannot be determined"** (→ core_api 500 "Data
  source returned no response") on any MAP table that isn't the terminal hub. Proven via core_api's exact
  impersonated `executeQueries` (imperson. user from capacity `87888186`).
- **The lever:** the **table-form** `KEEPFILTERS(FILTER(ALL('T'[Col]),'T'[Col]=v))` **does** work where the bare
  predicate fails. Options considered at the time: **(1)** standardize embedding dashboards to a `Brand[Brand]`
  (or conformed client-dimension) lock → the existing component drops in, no code change (tradeoff: sales scopes
  by brand not vendor, ~1.7% for Brinno — **ruled out for combined dashboards** for that reason);
  **(2)** change `dax_query_builder` to emit the `FILTER(ALL())` form for **locked** filters → keeps sales on
  vendor **and** keeps ONE shared component; **(3)** RLS (applies as table-`FILTER`, dodges the trap entirely —
  heaviest). ⭐ **Option (4), shipped instead — the self-scoped visual above.** It required no code change, left
  sales on vendor, and is what put MAP on Brinno's combined dashboard. (2) remains worthwhile purely to avoid
  per-client clones.
- **Dead ends (do not retry):** bidi `Product↔Brand` (breaks `SUMMARIZECOLUMNS` on the by-brand table; hub+daily
  query under bidi timed out >2min) — though it IS sales/COGS-neutral; a disconnected/connected **island** table
  + 2nd locked filter (the injected `Product` lock errors on it). **DAX simulation is unreliable** — core_api's
  real query is looser than hand-written `SUMMARIZECOLUMNS`; validate on the live path or via impersonated
  `executeQueries`.
- **The exposure was REAL and is CLOSED (2026-07-24).** `a4ec0d1d` carried **5 external `brinno.com` users**, and
  `f16fb03d` was serving them a payload **byte-identical** (fingerprint `b1af53f80c6c`) to the internal all-brands
  dashboard `eaa10f9e` — tampering the vendor filter changed nothing, proving the injected lock was wholly inert
  rather than merely weak. Fix = removed that ONE layout component (visual doc kept; internal `eaa10f9e` still
  uses it). After: the endpoint returns **404** for that dashboard+visual pair — closed server-side, not hidden.
- **Client→brand exclusivity is provable from data, and it passes.** `Product` carries **both** `[Brand]` and
  `[Default Vendor]`, so one single-table DAX query settles whether any Brand spans two clients: **19 SAFE, 0
  BLOCKED, 0 unmatched**. The many-to-many runs in the harmless direction — a client has multiple *vendors* but
  exactly **one** brand. Use this as the gate before any per-client RBAC release.
- ⚠ **Do NOT filter client rosters by email domain.** Legitimate client users sit on **gmail.com** (360Feel, Rain
  Bird), **yahoo.com** (CIBU), a third-party agency **marketspire.ai** (Dalen) and **icloud.com** (NAVIRA).
  Mirror the client's own sales-dashboard roster **per user** instead.
- Full plan + IDs + tooling: `aldc-launchpad/boot-prompts/navira-map-client-scope-SOLUTION-plan.md` and
  `docs/evidence/gp293.md` (GP-293); e2e acceptance suite `aldc-launchpad/tests/e2e/` (26 tests).

**RBAC IS server-enforced; the dashboard locked-filter WAS NOT (pre-GP-299).** Read from `core_api@eclipse-2.1`:
- **RBAC is real.** Every Explorer data endpoint carries a FastAPI dependency: the dashboard-visual-data router is
  `dependencies=[PermissionChecker.check_path("dashboard_id", [Dashboard_View])]` (`api/dashboards/router.py`),
  the direct visual endpoint needs `Visual_View`, the direct dataView data endpoint needs `DataView_View`
  (`api/visuals/router.py`, `api/data_views/router.py`). So **object access is genuinely gated** (contrast the
  earlier eclipse_exp mis-read where checks weren't wired).
- **The locked Brand filter is NOT injected server-side.** `get_dashboard_visual_data` calls
  `request_visual_data(dashboard.dataset_id, account_id, visual.options, body)` — it **never passes
  `dashboard.filters`**. `create_dataset_request` (`api/visuals/lib.py`) sets `filters = visual_data_request.filters
  or []` (+ timeframe date-range only). → the returned rows are scoped **entirely by the client-supplied request
  body**. A client with legitimate `Dashboard_View` on their own brand-locked dashboard can POST to that endpoint
  with `body.filters=[]` (or a different brand) and receive **all brands' data**. The lock is presentation-only
  (the frontend sends it for normal clicking — which is why GP-261's UI leak-test passed — but a crafted request
  bypasses it).

**Consequence:** a per-client `mode:locked` `Brand` dashboard is **NOT a robust data boundary** for external
clients. RBAC isolates *which* dashboards/visuals a user can reach, **not** row-level brand scoping within a
shared multi-brand model. The internal all-brands tier is unaffected (internal users are meant to see all brands).

**Simplest robust fix (recommended over full RLS): enforce the locked filter server-side.** Patch
`get_dashboard_visual_data` to pass `dashboard.filters` into `request_visual_data`, and force `mode:locked`
filters into the query — **stripping/overriding any client `body.filters` on locked fields** so the client cannot
remove or alter them. Pair with a **grant discipline**: client users get `Dashboard_View` on *their* dashboard
**only** — never `Visual_View`/`DataView_View` on the shared visual/dataView (so the direct endpoints 403 for them).
Contained blast radius (one endpoint), no model changes, and it makes GP-261's already-built per-client dashboards
genuinely safe. **Heavier alternative:** true RLS — change `v1/route_dataset.model_query`'s `impersonatedUserName`
(currently `choice(fixed_pool)`) to the end-user's brand principal + add RLS roles to the model; high blast radius
(that line serves every account's queries). Tracked in the isolation ticket + boot prompt
`aldc-launchpad/boot-prompts/navira-map-client-isolation.md`.

## Access

Paul's current state (2026-04-17):

- Eclipse production access granted 2026-04-17 (covers the core_api backend)
- Has Steven's `local.settings.json` (stored in `vault/core-api-local-settings.md`)
- Service principal (from `local.settings.json`) has active access to prod CosmosDB / storage
- Azure owner permissions still pending (Brayden → Sean)

## Datasets API

Source: Confluence CORE/1467940876 (Datasets and API Access, 2025-10-08).

Datasets are a data-access abstraction layer — clients request curated data via REST without knowing the underlying infrastructure.

**Endpoints:**
- Test: `https://api-test.aldc.io/v1/dataset/request`
- Prod: `https://api.aldc.io/v1/dataset/request`

### Request format

```json
{
  "account_id": "<ACCOUNT_ID>",
  "dataset_id": "<DATASET_ID>",
  "preview": false,
  "request": {
    "format": "row",
    "fields": ["'Date (Action)'[Year Name]", "'Account'[Account Name]"],
    "filters": [{"field": "'Date (Action)'[Year Name]", "operator": "equals", "value": 2024}],
    "measures": ["Actual - Spend - Gross"]
  }
}
```

`format` options: `row` (default), `column`, `array`, `parquet` (base64 gzip), `csv` (base64). Set `preview: true` to get row count only.

### Dataset introspection

`POST /v1/dataset/describe?debug=full` — returns `definition.columns` (use `column_locator` in `fields`), `definition.measures` (use `measure_name` in `measures`), and `definition.tables`.

### CosmosDB setup (capacity_provider → capacity → dataset)

Three documents required per account:

1. **capacity_provider** — `type: "tenant"`, `provider: "data_model"`, holds `tenant_id` + `admin_service_client_id` + encrypted `admin_service_client_secret`
2. **capacity** — links `account_id` to `capacity_provider_id`; holds `workspace_id`, `service_client_id`, encrypted `service_client_secret`, and `impersonation` list
3. **dataset** — `type: "data_model"`, links `account_id` to `capacity_id`; holds `dataset_name` + `dataset_id` from Power BI

### App registration requirements

Two Azure app registrations per account:

| App | API Permissions | CosmosDB role |
|---|---|---|
| `Power BI REST API {ACCOUNT_ID}` | `Capacity.READ.ALL`, `Dataset.READ.ALL`, `Semantic Model.READ.ALL`, `Workspace.READ.ALL` | Capacity + capacity provider |
| `Power BI REST API {ACCOUNT_ID} Admin` | None | Admin on capacity provider |

Both apps added to Entra group `Power BI Embed {ACCOUNT_SHORT_CODE}`. That group needs **Service principals can call Fabric public APIs** and **Service principals can access read-only admin APIs** enabled in Power BI Admin portal, and **Contributor** access to the PBI workspace.

See also: [[powerbi-secret-refresh]] for secret rotation runbook.

## Azure Queue Storage Trigger (dispatcher)

Source: Confluence CORE/1048248321 (Azure Queue Storage Trigger, 2022-12-08).

> *Verify deployment approach against current infrastructure — created 2022.*

Task queue messages are consumed by a Python Azure Function (the "dispatcher") using a Queue Storage Trigger. This replaced the legacy task/trigger and runs exclusively for the task daemon.

### Function app naming

`aldc{env}fnapdispatch{dg}{region}{seq}` — e.g., `aldcprodfnapdispatch1c01`.

### function.json binding

```json
{
  "bindings": [{
    "name": "msg",
    "type": "queueTrigger",
    "direction": "in",
    "queueName": "tasks",
    "connection": "{STORAGE_ACCOUNT_NAME}_STORAGE"
  }]
}
```

`connection` must match the custom connection string name in Azure portal settings.

### Required app settings (Azure portal)

| Setting | Value |
|---|---|
| `CLIENT_ID` | Master client ID or service account for the deployment group |
| `CLIENT_SECRET` | Corresponding secret |
| `{STORAGE_ACCOUNT_NAME}_STORAGE` | Queue storage account connection string (same as `AzureWebJobsStorage`) |

### Local setup

Add `{STORAGE_ACCOUNT_NAME}_STORAGE` + `CLIENT_ID` + `CLIENT_SECRET` to `local.settings.json`. Set `LocalHttpPort: 7072` if running alongside core_api (which uses 7071). Update `launch.json` port to `9091`.

## REST API Specification (2021 design)

Source: Confluence CORE/238387201 (2021-02).

> *2021 design spec — endpoint surface has evolved. Use [[postman-collections]] as the current source of truth for live endpoints.*

### URL structure

```
POST https://{targethost}.azurewebsites.net/v1/{function}/{option}
```

**Auth:** `Authorization: Bearer {TOKEN}` where TOKEN = Base64(`sas_id:sas_key`).

**Debug param:** `?debug=full|partial|none`

### Standard response envelope

```json
{
  "response": {
    "code": 200,
    "type": "Success",
    "message": "...",
    "origin": "function/option",
    "payload": {}
  }
}
```

### Endpoint reference (2021)

| Endpoint | Purpose |
|---|---|
| `account/describe` | Account metadata + storage SAS tokens |
| `account/list` | Accounts accessible by SAS ID |
| `session/init` | Create session → returns `session_id` |
| `session/event` | Write event (setup/output/transport/stage/merge) with start/end status |
| `session/complete` | Close session, compute duration |
| `session/describe` | Full session + all events |
| `session/list` | Sessions by account + status filter |
| `session/zombie` | Sessions exceeding timeout threshold |
| `schedule/init` | Initialize schedule entry |
| `schedule/event` | Write schedule event |
| `schedule/complete` | Close schedule, compute duration |
| `schedule/describe` | Full schedule + events |
| `schedule/list` | Schedules by account + status |
| `schedule/zombie` | Schedules exceeding timeout |
| `warehouse/schema` | Most recent schema for a session |
| `warehouse/extract` | Store schema against session_id |
| `warehouse/stage` | Ingest staged Parquet from Azure Storage into Snowflake stage table |
| `warehouse/merge` *(planned)* | Merge session data with master table |
| `fragment/*` *(planned)* | Fragment inventory management (reconciliation, incomplete tracking) |
| `data/table` *(planned)* | Table metadata for a catalog |
| `data/query` *(planned)* | Execute query against catalog |

### Session event flow

`session/init` → events: `setup` → `output` → `transport` → `stage` → `merge` → `session/complete`

Each event phase has `start` + `end` status writes. Zombie detection kills sessions that exceed timeout without a `complete` call.

### Planned migration

OAuth 2.0 token model was planned to replace SAS-credential Bearer tokens. Current state: unknown — check with team.

## Environment Variables

Source: Confluence CORE/886603777 (2022-07).

> *All actual secret values are redacted — see `vault/infra-credentials.md` § External services credentials + § Dev/old-env core_api credentials.*

### Full variable glossary

| Variable | Description | Example / Default |
|---|---|---|
| `COSMOS_DATABASE` | CosmosDB database name | `"core"` |
| `COSMOS_HOSTNAME` | CosmosDB URL | `https://aldc{env}csdb{inst}.documents.azure.com/` |
| `COSMOS_KEY` | CosmosDB auth key | → vault |
| `COSMOS_THROUGHPUT` | Container throughput (RU/s); `-1` = serverless | `-1` |
| `COSMOS_RETENTION` | Analytical Store retention (seconds); `-1` = infinite | `15768000` (6 months) |
| `ENVIRONMENT_LEVEL` | Tier | `dev`, `test`, `prod`, `stage` |
| `ENVIRONMENT_VERSION` | Deployed version | `"2022-03"` |
| `ENVIRONMENT_ADMIN` | Admin controls enabled | `1` / `0` |
| `ENVIRONMENT_LOCATION` | Runtime context | `"VS Code Runtime Local"`, `"Azure"` |
| `ENCRYPTION_KEY` | Two-way secret encryption key (Base64, **32 bytes exactly**) | → vault |
| `MASTER_CLIENT_ID` | Master client with all API privileges | `FFFFFFFF0000` |
| `MASTER_CLIENT_SECRET` | Master client secret | → vault |
| `MASTER_CLIENT_ENABLE` | Master client enabled | `1` / `0` |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription | → vault |
| `AZURE_CLIENT_ID` | Service principal client ID | → vault |
| `AZURE_TENANT_ID` | Azure AD tenant ID | `e2bae64b-6e5f-4f55-b81c-ada320c7f572` |
| `AZURE_CLIENT_SECRET` | Service principal secret | → vault |
| `SYS_STORAGE_NAME` | Storage account name | `aldcdevstac01coresvc` |
| `STORAGE_SAS1` / `STORAGE_SAS2` | SAS tokens (primary / secondary) | → vault |
| `PUSHOVER_TOKEN` | Pushover push token | → vault |
| `TWILIO_SID` / `TWILIO_TOKEN` / `TWILIO_NUMBER` | Twilio SMS credentials | → vault |
| `MAILJET_EMAIL` / `MAILJET_KEY` / `MAILJET_SECRET` | Mailjet email credentials | → vault |

Full `local.settings.json` for each environment: `vault/core-api-local-settings.md`.

### ⚠ Gotcha — ONE absent env var disables every route, and it reports HTTP 200 "success"

Surfaced by [[ALDC-1175]] (2026-09-08, GEP/Navira SALES DETAIL SYNC). Four properties of
`v1/func_common.py`'s env handling that together make config failures both catastrophic and
invisible. Read this before diagnosing *any* `Environment variable setup failed` report.

**1. Every variable in the glossary above is validated as MANDATORY.** `func_common.py` builds one
dict and loops `if variable_value == None: raise`. So `PUSHOVER_TOKEN`, `TWILIO_*`, `GPT_KEY`,
`GPT_ORG` and the `AZURE_*` set are hard prerequisites for **every** request — including routes that
never touch them. The FastAPI rewrite (`api/__init__.py` → `GlobalConfig`) already models these
correctly as `Optional`; the legacy path does not.

**2. ⭐ The error names the FIRST absent variable — so it hands you a free diagnostic.** Python
preserves dict insertion order, so `Environment Variable <X> improperly set` proves **every nullable
key before `<X>` was populated**, and says **nothing** about the keys after it. Read the dict order
in `func_common.py` and split it at `<X>`: prefix = healthy, suffix = UNKNOWN and needing separate
verification. Do not treat such an error as "the environment is empty" — a config missing exactly
one variable looks identical to a total wipe unless you use the ordering.

**3. `== None` tests absence, not blankness.** An empty string `""` **passes**. So the variable must
be genuinely absent from the process environment — which rules out `docker compose`
`KEY: ${VAR}` with `VAR` unset (that yields `""`). Useful for eliminating mechanisms fast.

**4. It is sticky per process, and served as HTTP 200 "success".** `environment_error` is a
module-level global evaluated **once at import**; `v1/__init__.py:302` gates on it as the first
statement of the request `try`, **before route dispatch and before every per-route
`check_auth_*` guard** (⚠ precise wording: `CurrentAuth` *is* constructed earlier at lines 96-99, so
authentication is evaluated first — what's missing is any *early rejection* of an unauthenticated
caller). So a bad-config worker fails everything until it restarts — and it does **not** crash out
and get replaced: the Cosmos client at `func_common.py:112-115` still builds fine, so the worker
stays alive serving errors indefinitely.

⭐ **And EVERY v1 response is HTTP 200 — not just this one.** `status_code` appears **exactly once
in the whole 74KB `v1/__init__.py`**, at line 1281, hardcoded `status_code=200`. The 400 "client
error" and 500 "server error" branches return HTTP 200 too. **A status-code monitor is blind to
100% of v1 errors.** On the env-error path specifically, `:1247` *additionally* overwrites the
body's `code`/`type`/`message` with `200`/`"success"`/`"success"`, so a body-parsing monitor is
blinded as well — two independent cannot-fail layers. Sibling of the generic-500 masking gotcha in
*Debugging workflow* above.

⚠ **If you fix this:** correct **line 1247** first (a config failure is not `"success"` —
unambiguously wrong). Treat **line 1281** as a separate, coordinated change: making it honour
`response_dict["code"]` is a **breaking change for every existing caller**, including client-side
daemons we do not control (see [[ALDC-1175]]).

Also note `api/__init__.py:59-65` (`get_global_config()`) calls **`os.abort()`** on validation
failure — SIGABRT at import, a crash-loop. Loud rather than silent, so better, but it is a **third
distinct behaviour** for the same condition in one codebase.

**5. Corollary for triage — an error surfaced by a client's system is not an error owned by it.**
ALDC-1175 arrived as a client-side Python traceback and was first assessed as "not us"; the string
came from `func_common.py:92`. **Grep the repos for the literal error text before assigning
blame** — the client's daemon had merely interpolated our response body into its own exception.

### ⛔ `AZURE_CLIENT_ID` cannot be both present and absent — the ALDC-1002 / `func_common` deadlock

Surfaced by [[ALDC-1175]]. **`DefaultAzureCredential()` requires `AZURE_CLIENT_ID` to be UNSET to
use a Function App managed identity, while `func_common.py` requires it to be SET or the whole v1
API returns errors.** The two cannot be satisfied at once, and ALDC-1002 (`v1/keyvault_client.py`,
merged to `eclipse-2.1` 2026-09-05 as `9caded0`) shipped code that needs the managed-identity side.

Why, in the installed SDK (`azure/identity/_credentials/default.py`):

- `:149` — `EnvironmentCredential` is appended **first** in the chain, so with
  `AZURE_CLIENT_ID`/`AZURE_TENANT_ID`/`AZURE_CLIENT_SECRET` all present (all three are in
  `func_common`'s mandatory list, so they *must* be) the **service principal wins** and the managed
  identity granted "Key Vault Secrets User" is never used.
- `:121-122` — `managed_identity_client_id` **defaults to `os.environ.get(AZURE_CLIENT_ID)`**, and
  `:162-164` passes it to `ManagedIdentityCredential(client_id=...)`. So the fallback is *also*
  poisoned: it asks IMDS for a **user-assigned** identity whose client ID is a service-principal
  app ID, which does not exist.
- The SDK states it plainly in `azure/identity/_credentials/azure_arc.py:52`:
  *"DefaultAzureCredential ensure the AZURE_CLIENT_ID environment variable is not set."*

⚠ **So the two obvious fixes are each other's cause.** Removing `AZURE_CLIENT_ID` to unblock Key
Vault detonates the env loop and takes the API down; re-adding it to restore the API silently
re-breaks Key Vault — `get_private_key()` swallows failures to `None`
(`keyvault_client.py:73-74, 84-86`), Snowflake falls back to password auth, and **ALDC-1098**
(password-fallback removal) would then hard-fail on deploy. **Neither layer alone is a fix.** The
resolution has to make the env contract and the credential strategy consistent in the same change —
e.g. pass an explicit `ManagedIdentityCredential`, or `exclude_environment_credential=True`, rather
than relying on `DefaultAzureCredential`'s chain order.

**General rule:** `DefaultAzureCredential`'s chain order is configuration, not a detail. Any service
that sets `AZURE_*` service-principal vars **cannot** also use a managed identity through it.

### ⛔ Which resource serves `api.aldc.io` — two apps with near-identical names, different codebases

Established on [[ALDC-1175]] and worth checking before *any* core_api diagnosis:

| Hostname | Resource | Kind / runtime | Codebase |
|---|---|---|---|
| **`api.aldc.io`** | **`aldcprodfnapcore1c01`** (`aldcprodrsgp1c`) | `functionapp,linux`, `sku: Dynamic` (Y1 Consumption), `PYTHON|3.11` | **legacy `v1/`** — the one that can emit the env error |
| `api.eclipse.analyticlabs.io` | `aldcprodwbapcore1c01` | web app, container | **FastAPI `api/`** rewrite — `POST /v1/account/list` → `404 {"detail":"Not Found"}` |

⚠ **No *web* app carries `api.aldc.io`.** Anyone running `az webapp list` / `az webapp config …`
alone targets the wrong resource and gets empty or misleading output — and an empty result there
looks exactly like a missing setting. Use `az functionapp …` for the `api.aldc.io` host. The DNS
A-records point at **Cloudflare**, so DNS never names the origin; the **ARM hostname binding** does.

Consequence for the [[ALDC-1175]]-class defect: the **two prod deployments of the same service
disagree about which variables are mandatory.** `aldcprodwbapcore1c01` holds 23 settings and **no**
`AZURE_CLIENT_ID` (consistent with `GlobalConfig`'s `Optional`); `aldcprodfnapcore1c01` needs all 25
nullable keys. `aldcprodfnapcore1c03` also 404s on `/v1/` and is not a casualty either.

### ⚠ Deploy gotcha — the container tag is mutable (Web App pipeline only)

Measured on [[ALDC-1175]]: prod and `stage` on the **container Web App** pipeline reference the
**same mutable tag** `ghcr.io/aldc-io/core-api:2.0.0-eclipse-2-1.1` — byte-identical across three
build runs (2026-09-02, 09-05, 09-08). Two consequences:

1. **That app picks up new code on any restart or scale-out, with no slot swap.** Combined with the
   import-time-per-process `environment_error` above, that can produce **mixed worker populations**
   — some workers on old code/config and healthy, some on new and broken.
2. **The rollback-safety gate cannot fail.** `deploy_az_webapp_container.yaml:73` gates on
   `[ "$STAGE_IMAGE" != "$PROD_IMAGE" ]`, but since the tag never changes it compares a constant to
   itself — it reported success on `push` runs with `force_deploy=false` and would do so even if
   stage genuinely held a rollback version. Remove what it guards and it stays green.
   ⚠ Pinning to an immutable digest *without* fixing the comparison makes the gate block **every**
   deploy (differing digests become the normal state), which reads as "the gate broke" and invites
   `force_deploy=true` as a habit. Fix both together. Tracked by [[ALDC-994]].

⛔ **Scope correction, and it is the reason this heading names the pipeline:** this does **not**
apply to `aldcprodfnapcore1c01` / `api.aldc.io`, which is a Python 3.11 Consumption **Function App**
with no `DOCKER_CUSTOM_IMAGE_NAME`, deployed by zip/publish (signature in the activity log:
`ListPublishingCredentials` + `Sync Web Apps Function Triggers` + Stop/Start). On [[ALDC-1175]] this
mechanism was initially published as the explanation for the outage timing and had to be withdrawn —
the real trigger was an explicit operator `Stop`/`Start`. **Check `kind`/`sku`/`linuxFxVersion`
before attributing anything to the container pipeline.**

### ⚠ Measurement traps when diagnosing this app (each one produced a false conclusion)

1. **`az monitor activity-log list` silently caps at 50 events.** On [[ALDC-1175]] a filtered run
   returned a timeline that looked complete and **began 51 minutes after the causal event**. Pass
   `--max-events 2000`. A truncated log reads exactly like a quiet one.
2. **Cloudflare 403s `urllib` but passes `curl`.** 70/70 Python-client requests to `api.aldc.io`
   returned `HTTP 403` while identical `curl` requests returned 200. A Python-scripted probe would
   report a total outage that does not exist. Use `curl`, or set a browser UA, and probe the
   `*.azurewebsites.net` origin separately to bypass the edge.
3. **On Y1 Consumption there is no worker identity at any layer.** `az webapp list-instances`
   returns empty, `clientAffinityEnabled` is null so there is no `ARRAffinity` cookie, and
   direct-origin responses carry no `x-azure-ref`/`Request-Context`. So *no number of probes proves
   the fleet healthy* — argue the population structurally instead (last config write + a Stop/Start
   destroying every process + a full enumeration of required keys).
4. **The `"client id"` in the response body is NOT an instance fingerprint** — it is a fresh
   `str(uuid.uuid4().hex)` per request (`v1/route_auth.py:8`). It looks like one. It isn't.
5. **Useful discriminator once you are probing:** `code: 500` + a `JSONDecodeError` in the payload =
   healthy config (that is the generic-500 masking path); `code: 200` + `"payload": "Environment
   variable setup failed…"` = broken config. A monitor should key on the latter, never on the HTTP
   status.

## Architecture & Language Stack

Source: Confluence CORE/7929869 (Architecture Overview, 2020-11).

> *2020 design context. Python version upgraded from 3.8 → 3.11; everything else broadly consistent.*

**Main components:** Source Systems → Work Agent → Core API (Azure Function App) → CosmosDB + Storage Account + Snowflake → Power BI / Eclipse (App Service).

**External services:** Twilio (SMS), Pushover (push notifications), Mailjet (email), Fivetran (data integration).

**Language stack:** Python 3.8 original (now 3.11), PL/SQL (Snowflake), frontend TBD. Source control: GitHub.

> **Note (2020):** Python 3.9 was flagged as incompatible with pyarrow. Python 3.13 has the same issue — see [[core-api-local-setup]] § Common failures.

## Notification Module (route_notification.py)

Source: Confluence CORE/885620774 (2021-11).

> *2021 — verify function signatures and queue integration against current codebase.*

The notification system is asynchronous: messages are queued via Azure Queue Storage, then consumed and routed to the appropriate delivery channel.

**Queue functions:**
- `notification_queue_user()` — queues for a single user
- `notification_queue_group()` — queues for a group
- `func_common.send_message_to_queue()` → writes to `"notifications"` queue

`notification_send()` dequeues messages and routes on `method`:

### Pushover

```python
def pushover_notification(user_list, message, origin, title, priority, device=None):
```

- `priority`: `"high"` → 1, `"medium"` → 0, `"low"` → -1
- `user_list`: single key in list **or** comma-separated string (no spaces) for groups
- Posts to `https://api.pushover.net:443/1/messages.json`
- Returns `1` on success, `0` on failure
- Env var: `PUSHOVER_TOKEN` → `vault/infra-credentials.md` § External services

### SMS (Twilio)

```python
def sms_notification(user, message, origin):
```

- Single recipient per call (unlike Pushover's batch support)
- Phone number requires `+1` prefix for US numbers
- Env vars: `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_NUMBER` → vault

## Task Daemon (route_task.py)

Source: Confluence CORE/909737996 (2022-07).

> *2022 — verify against current codebase. The Azure Queue Storage Trigger (§ above) now handles task execution in newer deployments.*

Four-stage pipeline for scheduled task execution:

1. **`/task/create`** — creates task doc in CosmosDB; sets `datetimestamp_next_utc` if created via API
2. **`schedule_integrator`** — computes next execution timestamp from cron schedule (uses `croniter`; adds sub-minute `seconds` field)
3. **`/task/scan`** — finds tasks where `datetimestamp_next_utc ≤ now`; pushes to queue; sets `next_utc = None` to prevent duplicates
4. **`/task/trigger`** — dequeues + executes API call; updates `datetimestamp_last_utc`; calls `schedule_integrator` for next `next_utc`

Task lifecycle: create → scan picks up → trigger executes → reschedule → repeat.

Cron format: standard 5-field (`* * * * *`) plus optional `seconds` int. `* * * * *` + `seconds: 30` = every 30 seconds. See [[cosmosdb-schema]] § Task Collection for document schema.

## Portal Data Export & Power BI Integration

Source: Confluence CORE/892796955 (2021-12).

> *2021 — verify `route_portal.py` endpoint name and request format against current codebase.*

`route_portal.py` → `portal_data` function queries Snowflake views and returns results. Use `format: "row"` for Power BI compatibility.

### Request format

```json
{
  "account_id": "ef53b697",
  "view": "GA_COUNTRY_SOURCE",
  "options": {
    "columns": ["GA_COUNTRY", "PAGEVIEWS", "GA_SOURCE"],
    "filters": [{"field": "PAGEVIEWS", "operator": "equals", "value": 10}]
  },
  "format": "row"
}
```

### Import into Power BI

1. Postman → send request → Save Response → JSON file
2. Power BI Desktop → **Get Data** → **JSON** → select file
3. Power Query Editor: find `response.payload` column → expand (double arrows) → **Expand to New Rows** → expand again, uncheck "Use original column name as prefix"
4. Ctrl+click desired columns → **Remove Other Columns**

Result: clean table with keys as headers, values as rows.

## Client Data Query Endpoints — Usage Patterns

Source: Confluence TECH/1777106945 (Steven Offboarding). Supplements the technical endpoint spec in § Datasets API above.

Three query patterns exist for clients to access warehouse data:

### `dataset/request` with `dataset_id` (primary — Eclipse 2.1)

The primary endpoint Eclipse 2.1 uses. Queries go to the **Power BI API** and get data from the semantic model, ensuring clients see exactly what they'd see in a pivot table or visualization. Requests use a JSON body to describe desired data (fields, filters, measures), which core_api transforms into a DAX query (the Power BI query language, not Fusion92's "DAX" product name) and sends to the Power BI model API.

**Limitations:**
- Data size limits on returned responses
- Filters only support AND operations between them
- Filter operators limited to simple comparisons (equals, greater than, etc.)

### `dataset/request` with `capacity_id` (direct Snowflake SQL)

Allows clients to send **raw Snowflake SQL** as a payload. More powerful but requires the client to know schema and table names.

- Some safeguards against dangerous operations, but access should be granted sparingly
- GEP uses this for querying raw Amazon Ad `EXTRACT_*` tables not available through the Power BI model
- Data size limits apply; no server-side pagination — clients must design queries to split large datasets
- GEP also uses the older `dataset/query` endpoint for some `EXTRACT_` tables, but this endpoint is preferred

### `dataset/query` (legacy — older filter-based SQL generation)

Uses the same filter structure as `dataset/request` (with `dataset_id`) but accepts schema and table parameters to generate a simple SQL query against Snowflake directly.

- Older API; should not be offered to new clients
- Used internally by the [[workflows|Dax API]] where direct Snowflake access is needed
- Could be expanded with security improvements, but better to expand the `capacity_id` request pattern instead

### Client API documentation

User-facing API documentation exists at the [Postman Documenter](https://documenter.getpostman.com/view/42132163/2sAYXCmKTz#568b210a-7321-4f2d-bdc1-64e41d950ba9). May be somewhat out of date — always verify against the current code.

---

## Emergency contact

- Brayden Marshall — `brayden.w.marshall@gmail.com` (personal — use only in emergencies; should also be on the GitHub contributors list for core_api)

## Development Standards

All code in core_api must follow ALDC standards:

- [[ai-pr-workflow]] — automated PR checks (Semgrep, TruffleHog, Claude Opus review, PyTestArch, quality gate). Live as of 2026-04-10.
- [[adversarial-investigation-skill]] — `/investigate-adversarial` skill for debugging and architecture decisions
- [[ai-development-project-standard]] — mandatory header + ROI tracking for any feature with >50% AI authorship
- [[python-development-standards]] — PEP 8, Google docstrings, VS Code + PyLint conventions (Python 3.11 hard requirement in this repo)
- [[git-branching-strategy]] — ALDC branching model; core_api follows the same `development` → `user-testing` → `main` flow

## Relationship to eclipse_exp

[[eclipse_exp]] is the next-generation successor to core_api + [[Eclipse]]. It runs in parallel via a strangler-fig migration: new clients provision directly on eclipse_exp (FastAPI + PostgreSQL + JWT + RLS), while existing clients served by core_api (Azure Functions + CosmosDB + legacy auth) continue unaffected. During the migration window, core_api remains the production control plane for all legacy tenants. The two systems do not share a database — eclipse_exp uses its own PostgreSQL schema (`eclipse_exp`) while core_api reads from CosmosDB. See [[eclipse_exp]] § Migration from Legacy Eclipse for the cutover mechanics.

## Known API Gaps

The repo actually exposes **two API surfaces side-by-side**: the legacy Azure Functions `v1` (port 7071, `/v1/…`) and a newer FastAPI `v2` (port 8000, `/v2/…`, entrypoint `api/main.py`, started via `python run.py` or `python run_debug.py`). The v2 surface is the active backend for the current `eclipse` repo on disk and is **deployed in production at `https://api.eclipse.analyticlabs.io/v2/`** (CORS allowlist: `https://eclipse.analyticlabs.io` — the paired [[entities/repos/eclipse|eclipse-2.1]] frontend). The rest of this page still primarily documents v1. A full refresh is pending (see [[action-items]]).

### v2 has no PATCH/PUT for `application_metadata` (surfaced 2026-04-21 by [[DV-444]])

`core_api/api/applications/router.py` exposes only `GET /hierarchy/` and `GET /metadata/`. The update handler exists in `core_api/v1/route_application.py` (`update_metadata_item`, ~lines 308–329) and is routed as `application/updatemetadata` by `core_api/api/legacy_router.py`. However `core_api/api/main.py:164` **comments out the legacy router**, so that path is **not reachable** on the running v2 service.

**Workaround used for DV-444**: direct CosmosDB patch via Azure Portal Data Explorer against the `application_metadata` container, partition key `/account_id`. See [[DV-444]] for the exact record and steps.

**Proper fix (open action item)**: add a v2 PATCH endpoint on `/v2/applications/{id}` that validates input, calls an update-metadata equivalent, and handles the camelCase-vs-snake_case translation (v2 schema uses `appName`; the raw CosmosDB document uses `app_name`). Tracked in [[action-items]].

Uncommenting the legacy router to re-enable `application/updatemetadata` was considered and rejected — it would expose every legacy v1 endpoint, not just the one needed.

## See Also

- [[core-api-local-setup]] — step-by-step runbook for running locally
- [[python-development-standards]] — PEP 8 + Google docstring + linter conventions for all ALDC Python
- [[postman-collections]] — collections that drive core_api (Steven's new-core, Lawrence's old-core)
- [[Eclipse]] — the UI / platform core_api backs
- [[connector]] — sibling repo that owns the data-transport layer post-Prefect migration
- [[CosmosDB]] — where core_api reads connection/template configs
- [[Azure]] — hosts core_api as a function app
- [[azure-environments]] — subscription / env map
- [[Postman]] — used to reproduce and debug core_api calls
- [[debugging-warehouse-loads]] — runbook for warehouse-load failures involving core_api
- [[eclipse-azure-deployment]] — deployment process (staging slot + swap)
- [[connector-timeout-outage]] — prior incident touching the core_api / Azure Function boundary
- `vault/core-api-local-settings.md` — actual secrets (gitignored)
