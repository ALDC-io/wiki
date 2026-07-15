---
tags: [ticket, eclipse, aldc, bug, resolved]
aliases: [ALDC-622]
sources: [https://analyticlabsdc.atlassian.net/browse/ALDC-622]
created: 2026-07-15
updated: 2026-07-15
---

# ALDC-622 — Eclipse "Something Went Wrong" when deleting a user (Navira/GEP)

**Type:** Bug | **Status:** ✅ Done (fix live in prod 2026-07-15) | **Project:** ALDC Scrum

## Problem

Navira/GEP admin **Muhammad Masud** (mmasud@globalecompartners.com) reported that deleting a user in the Eclipse v2 web app failed with a generic **"Something went wrong"** error — he could not remove a departed team member. Two deliverables: (1) remove the departed user's records safely, (2) fix the underlying crash so admins can self-serve.

- **Reported by:** Muhammad Masud (Navira/GEP)
- **Environment:** prod — `eclipse.analyticlabs.io` (Eclipse v2 SPA, `eclipse-2.1`)
- **Reproducible:** always, for any account holding an orphaned/legacy role assignment
- **Blocking:** all member edits/removals on the affected account (not just delete)

## Root cause (evidence-proven, not inferred)

The Members page (`accounts/[accountId]/settings/members/page.tsx`) renders `RoleAssignmentsTable`, which resolves each assignment's role via `roleMap[roleId]`. Legacy **account-level** role assignments that lost their Account scope in the Oct-2025 RBAC rework (commit `8aba2c7`) resolve to `undefined` → `undefined.name` **throws during render** → React error boundary ("Something went wrong").

Because the whole table crashed on render, it blocked **all** member edits/removals. The client experienced it as "delete fails," but the delete action was merely *unreachable* — the crash happened before any delete. `RoleAssignmentsTable` also backs the dashboard-access and visual-access settings pages, so the same fix protects those.

## Consumer store (confirmed at the layer, not inferred)

Prod Eclipse (`eclipse.analyticlabs.io`) reads users from **Cosmos** `aldcprodcsdb1c01` / `core` (`user` container + `rbac_role_assignment`), **NOT** the look-alike Postgres `app_user` store (that backs the legacy `eclipse-test.aldc.io` portal). See [[eclipse]] § "Users / login (two stores — do not confuse)".

## Fix

**Data remediation (2026-07-13).** Departed user removed from prod Cosmos: dropped the orphaned `rbac_role_assignment` docs (pk `/account_id`) and soft-deleted the `user` doc (`status = 'SYS_DEL'`, pk `/id`), original docs captured for rollback.

**Code fix — PR #91** (branch `fix/aldc-622-members-crash`, merged to `eclipse-2.1`, commit `db435bc6`).
- `RoleAssignmentsTable` now resolves roles through `resolveAssignedRoles()` (silently drops any unresolved/out-of-scope role) + `formatRoleNames()`, so a stale assignment can never crash render again.
- New `roleAssignmentsTableUtils.ts` + unit tests + a `RoleAssignmentsTable.test.tsx` render-regression test that reproduces the exact crash condition. Gate: **4/4 jest**, all CI green.
- PR #91 was fresh off current `eclipse-2.1` and **superseded #89** (util extraction) and **#90** (render test, `aldc-john-moran`). Approved by `mikestuart26`, merged by Paul.

**Key code locations**

| What | Where |
|------|-------|
| Fix component | `eclipse/src/components/RoleAssignmentsTable/RoleAssignmentsTable.tsx` |
| Role resolver + tests | `eclipse/src/components/RoleAssignmentsTable/roleAssignmentsTableUtils.ts` (+ `.test.ts`) |
| Render-regression test | `eclipse/src/components/RoleAssignmentsTable/RoleAssignmentsTable.test.tsx` |
| Renders on | members / dashboard-access / visual-access settings pages |

## Deploy + verification

Deploy followed the corrected container runbook ([[eclipse-azure-deployment]]) — **not** the no-op `deploy_az_webapp.yaml` code-deploy:
1. Merge → `deploy_az_webapp_container.yaml` built + pushed the image to the **`stage` slot** (green `rollback-check → build → deploy`; `rollback-check` passing confirmed stage == prod before deploy, so the swap promoted only the ALDC-622 delta).
2. Functionally verified on the **staging slot** (`aldcprodwbapeclipse1c01-stage.azurewebsites.net`): Members table renders, edit works.
3. **Swap `stage → production`** (frontend only — no backend/core_api change): `az webapp deployment slot swap -g aldcprodrsgp1c -n aldcprodwbapeclipse1c01 --slot stage --target-slot production`.
4. Verified live on `eclipse.analyticlabs.io`: Members renders, edit/remove works.

**Rollback path:** swap the slots back — no redeploy needed.

## See Also

- [[eclipse]] — Eclipse tool page (two-store trap; container deploy)
- [[eclipse-azure-deployment]] — container deploy runbook (stage-slot + swap; the code-deploy is a no-op)
- Session memory `reference_eclipse_prod_user_store.md` (prod Cosmos user-store delete runbook)
