---
tags: [distributed-workflow, active, azure-deploy-automation, ci-cd, playwright]
aliases: [Azure Deploy Automation Tracker, Automated Deploy Pipeline]
sources: [session/2026-04-29]
created: 2026-04-29
updated: 2026-04-29
---

# Azure Deploy Automation — Workstream Tracker

Automate the full Azure staging deployment and production promotion pipeline for [[entities/repos/eclipse|eclipse]] (Next.js frontend) and [[core_api]] (Python FastAPI backend). Today's process is entirely manual: trigger GitHub Actions, wait, verify staging URL by hand, swap slots in Azure Portal. The target is a pipeline where merging to `eclipse-2.1` triggers CI → stage deploy → automated E2E tests → slot swap, with a human approval gate on the swap step as a safety net.

## Goal

End state: merging a PR to `eclipse-2.1` in either repo triggers:

1. **CI quality gates** (already exist — no changes needed)
2. **Automated deploy to the Azure staging slot** (currently manual `workflow_dispatch`)
3. **Playwright E2E tests** against the staging URL (currently zero E2E tests exist)
4. **Slot swap to production** gated by GitHub environment protection rules (currently manual via Azure Portal)

"Done" = both repos have the full pipeline running, Playwright critical-path tests catch regressions, and the swap step requires a human reviewer click before executing.

## Lane

Wiki: **ALDC**

Owned paths (this workstream may write here):

- `processes/distributed-workflow/active/azure-deploy-automation.md` (this tracker)

**Implementation** lives in the GitHub repos, not the wiki:
- `ALDC-io/eclipse` — workflow YAML, Playwright config, E2E tests
- `ALDC-io/core_api` — workflow YAML, swap job

Read-only outside the lane. Do not edit existing wiki deployment runbooks ([[eclipse-azure-deployment]], [[gep-snowflake-pbi-deployment]]) — update them after the pipeline is live and validated.

## Required Context

Read in parallel at boot:

- [[eclipse-azure-deployment]] — current manual deploy runbook. The process this workstream automates. Contains swap order rules (backend first), staging URLs, rollback procedure, and the 2026-04-29 wrong-branch incident post-mortem.
- [[entities/repos/eclipse|eclipse (repo)]] — frontend repo details: CI workflows, tech stack (Next.js 14, Mantine 7, NextAuth 4), deployment infrastructure.
- [[core_api]] — backend repo details: CI workflows, Dockerfile (Python 3.11 + .NET), deployment to GHCR + Azure Web App.
- [[azure-environments]] — subscription model. Prod apps are in Production 2 subscription, resource group `aldcprodrsgp1c`.
- [[deployment-groups]] — resource inventory. App services: `aldcprodwbapeclipse1c01` (frontend), `aldcprodwbapcore1c01` (backend).
- [[GitHub Actions]] — current CI/CD state: manually triggered deploys, 6-gate quality system.

## Plan-Mode Rule

**Plan-mode-first for the first session of each phase.** Each phase introduces a distinct concern (workflow triggers, Playwright setup, swap automation) and the implementation details depend on findings during the previous phase. Skip plan mode for follow-up sessions within the same phase if scope is unchanged.

## Current State (as of 2026-04-29)

### Eclipse repo (`ALDC-io/eclipse`, branch `eclipse-2.1`)
- **CI**: 6-gate quality system — Semgrep SAST, Trufflehog secrets, Architecture (dependency-cruiser), Mutation testing (Stryker), Supply chain (GuardDog + Aikido), Claude AI review
- **PR checks**: npm audit, ESLint, Prettier
- **Deploy**: `deploy_az_webapp.yaml` — manual `workflow_dispatch` → `npm build` → `azure/webapps-deploy@v3` to `stage` slot
- **Tests**: Jest + Vitest installed, **Playwright v1.54.2 installed as dependency**, but NO `playwright.config.ts`, NO E2E tests, only 3-4 unit test files
- **Storybook** v9.1.2 installed
- **Environment**: "Production (Eclipse 2.1)" exists with **no protection rules**

### core_api repo (`ALDC-io/core_api`, branch `eclipse-2.1`)
- **CI**: Same quality gate (mutation testing + supply chain disabled)
- **Deploy**: `deploy_az_webapp_container.yaml` — manual `workflow_dispatch` → Docker build (self-hosted runner, GHCR) → `azure/webapps-deploy@v3` to `stage` slot
- **Tests**: pytest with 3 test files, minimal coverage
- **Environment**: "Production (Eclipse 2.1)" exists with **no protection rules**

### Key constraints
- **Backend swaps before frontend** — new frontend code calls new API endpoints; 404s result if backend isn't on the new version yet
- **Slot swap is bidirectional** — swap again to rollback
- **Staging CosmosDB**: `aldctestcsdb1c01`, database `core`
- **Staging URLs**: `aldcprodwbapeclipse1c01-stage.azurewebsites.net` (frontend), `aldcprodwbapcore1c01-stage.azurewebsites.net` (backend)

### Workflow comparison (eclipse vs core_api)

Both use the **same deploy pattern** — only the build step differs:

| | Eclipse | core_api |
|---|---|---|
| Trigger | Manual `workflow_dispatch` | Manual `workflow_dispatch` |
| Auth | OIDC (client-id, tenant-id, subscription-id) | OIDC (identical) |
| Build | `npm install && npm run build` → `.next/standalone` | Docker image via `aldc-io/devops/actions/build-and-publish-image` → GHCR |
| Deploy | `azure/webapps-deploy@v3` → stage slot | `azure/webapps-deploy@v3` → stage slot |
| Runner | `ubuntu-latest` | Build: `self-hosted`, Deploy: `ubuntu-latest` |
| Versioning | None | `aldc-io/devops/actions/version@main` (semver) |
| Swap | Manual (Azure Portal) | Manual (Azure Portal) |

## Workflows

### To-Do

#### Phase 1: Automated Stage Deploy (~1 day per repo)

Modify existing deploy workflows to trigger automatically when CI passes on `eclipse-2.1`. Keep `workflow_dispatch` for manual triggers.

- [ ] **Eclipse** — modify `.github/workflows/deploy_az_webapp.yaml`
  - Add `workflow_run` trigger: fires when CI workflow completes successfully on `eclipse-2.1`
  - Add condition: `if: github.event_name != 'workflow_run' || github.event.workflow_run.conclusion == 'success'`
  - Hardcode environment to `Production (Eclipse 2.1)` for auto-triggered runs; keep `inputs.environment` for manual
  - `workflow_run` with `branches: [eclipse-2.1]` correctly filters out PR-triggered CI runs (head branch = PR source branch, not target)
- [ ] **core_api** — modify `.github/workflows/deploy_az_webapp_container.yaml`
  - Same `workflow_run` pattern as Eclipse
- [ ] **Verify** both workflows trigger correctly on a test merge to `eclipse-2.1`

#### Phase 2: Playwright E2E Tests (~1-2 weeks, eclipse repo)

Eclipse already has Playwright v1.54.2 installed as a dependency. Needs config and tests.

**Testing options (ranked by complexity):**

| Option | Effort | Catches | Misses |
|---|---|---|---|
| 1. Smoke tests only (HTTP health checks) | ~1 day | Deploy failures, broken configs, server crashes | UI regressions, broken interactions |
| 2. **Playwright critical path (RECOMMENDED)** | ~1-2 weeks | Regressions in core flows, broken navigation, API failures | Edge cases, permission flows, less-used features |
| 3. Playwright comprehensive | ~3-4 weeks | All user flows, CRUD, permissions, all visual types | Nothing major — but high maintenance burden |
| 4. Visual regression (screenshots + Percy) | ~4-6 weeks | Subtle visual changes | Noisy false positives, baseline management |

**Recommended: Option 2 — Playwright critical path** (5-10 tests):

- [ ] Create `playwright.config.ts` — base URL from `E2E_BASE_URL` env var, chromium only, 2 retries in CI, auth state reuse via `storageState`
- [ ] Create `e2e/global-setup.ts` — login with test credentials, save auth state to `e2e/.auth/user.json`
- [ ] Create `e2e/login.spec.ts` — login flow, invalid credentials, redirect to dashboard
- [ ] Create `e2e/dashboard.spec.ts` — dashboard page loads, key elements visible
- [ ] Create `e2e/navigation.spec.ts` — click through sidebar links, verify pages load without errors
- [ ] Create `e2e/data-display.spec.ts` — data table or visual renders with actual data (GEP test account `da8904db`)
- [ ] Create `e2e/metrics-card.spec.ts` — metrics card displays, YoY tooltip with sub-year timeframe
- [ ] Create `e2e/external-app.spec.ts` — iframe-hosted app loads (SKU Profitability / navira-demo)
- [ ] Add E2E job to deploy workflow — runs after `build-and-deploy`, installs Playwright browsers, runs tests, uploads report artifact
- [ ] **Test credentials**: create a dedicated E2E test user in CosmosDB (`aldctestcsdb1c01` / `core` / `user` container). Store as GitHub secrets: `E2E_USERNAME`, `E2E_PASSWORD`
- [ ] Add `e2e/.auth/` to `.gitignore`

#### Phase 3: Automated Slot Swap with Approval Gate (~1 day total)

- [ ] **GitHub environment protection rules** — add required reviewers to "Production (Eclipse 2.1)" on both repos. This gates the swap step behind a human click.
- [ ] **Eclipse** — add `swap-to-production` job to deploy workflow:
  - `needs: e2e-tests`
  - `if: github.event_name == 'workflow_run'` (only auto-swap on CI-triggered deploys, not manual)
  - `environment: Production (Eclipse 2.1)` (triggers the approval gate)
  - `az webapp deployment slot swap --resource-group aldcprodrsgp1c --name ${{ vars.AZURE_APP_SERVICE_NAME }} --slot stage --target-slot production`
- [ ] **core_api** — add equivalent `swap-to-production` job
- [ ] **Backend-first swap coordination**: for initial implementation, each repo swaps independently. The human reviewer enforces backend-first order by approving core_api's swap before eclipse's. Document this in the approval step's description.
- [ ] **Future (Phase 3b)**: eclipse workflow triggers core_api swap first via `gh workflow run` or GitHub API, waits for completion, then swaps frontend. Requires a PAT or GitHub App token with cross-repo permissions.

#### Phase 4 (Future): Expanded Coverage

- [ ] Expand Playwright suite to 20-40 tests (Option 3) as the app grows
- [ ] Add API-level integration tests for core_api (hit staging API endpoints directly)
- [ ] Automate backend-first swap coordination (Phase 3b cross-repo triggering)
- [ ] Consider visual regression testing if UI precision becomes critical

### Safety Considerations

1. **Rollback**: Slot swap is bidirectional — swap again to revert. Workflow should output a "how to rollback" message on completion.
2. **Branch protection**: Ensure `eclipse-2.1` has branch protection (require PR, require CI pass) so untested code can't merge and auto-deploy.
3. **Flaky tests**: Set Playwright retries to 2, use `expect.toBeVisible()` with generous timeouts. Start conservative — a flaky test that blocks production is worse than no test.
4. **Environment protection**: The required-reviewer gate on "Production (Eclipse 2.1)" is the primary safety net. Can be removed once confidence in the E2E suite builds.

## Session Log

### 2026-04-29 — Research and plan (Opus, aldc-shipyard repo)

- **did**: Compared Azure deploy workflows across eclipse and core_api repos on `eclipse-2.1` branch. Read wiki deployment runbook. Explored CI infrastructure, test setup, GitHub environments, and shared devops actions in both repos.
- **decided**: 3-phase implementation plan. Phase 1: auto-trigger stage deploy via `workflow_run`. Phase 2: Playwright critical-path E2E tests (Option 2, ~1-2 weeks). Phase 3: slot swap with GitHub environment approval gate. Backend-first coordination is manual initially (human reviewer controls order).
- **key findings**: Both repos use identical deploy pattern (only build step differs). Playwright v1.54.2 already installed in eclipse. "Production (Eclipse 2.1)" environment exists on both repos with no protection rules. Connector repo has no Azure workflows (irrelevant to this workstream).
- **next**: Phase 1 implementation — modify deploy workflows in both repos.

## Decisions Log

- 2026-04-29 — **`workflow_run` over extending CI workflow**: keeps CI and deploy as separate workflows — easier to debug, re-run independently, and reason about. Alternative (deploy job inside CI workflow) couples concerns.
- 2026-04-29 — **Playwright critical path (Option 2) over smoke tests**: Eclipse already has Playwright installed. 5-10 E2E tests catch the UI regressions that matter without the maintenance burden of comprehensive coverage. Smoke tests (Option 1) miss UI issues entirely.
- 2026-04-29 — **Manual swap coordination over cross-repo automation**: backend-first swap order enforced by human reviewer initially. Cross-repo automation (GitHub API calls) adds PAT/token management complexity. Revisit in Phase 3b once the basic pipeline is validated.
- 2026-04-29 — **Approval gate on swap, not on deploy**: deploying to stage is safe (staging slot is isolated). The risk is in promoting to production. Gate only the swap step.

## Pending Wiki Updates

Once the pipeline is live and validated:
- `processes/deployment/eclipse-azure-deployment.md`: Update TL;DR and detailed steps to reflect automated pipeline. Mark manual workflow trigger as "legacy/fallback". Document the approval gate.
- `entities/tools/github-actions.md` (if it exists): add note about automated deploy pipeline.

## Blockers / Open Questions

- 2026-04-29 — **E2E test user**: need to create a dedicated test account in staging CosmosDB (`aldctestcsdb1c01` / `core` / `user` container). Who should create this? What permissions does it need?
- 2026-04-29 — **Environment protection rules**: who should be listed as required reviewers on "Production (Eclipse 2.1)"? Paul + who else?
- 2026-04-29 — **Branch protection**: is `eclipse-2.1` currently protected (require PR + CI)? If not, this is a prerequisite — otherwise code can be pushed directly and auto-deploy without review.

## Cross-Lane Requests

_None yet._

## Next Session Boot Prompts

### Phase 1 Boot Prompt — Automated Stage Deploy

````
You are resuming the **Azure Deploy Automation** workstream, Phase 1: Automated Stage Deploy.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\azure-deploy-automation.md`
3. Read the required context pages (parallel reads):
   - `C:\Users\PaulRussell\repos\wiki\processes\deployment\eclipse-azure-deployment.md`
   - `C:\Users\PaulRussell\repos\wiki\entities\repos\eclipse.md`
   - `C:\Users\PaulRussell\repos\wiki\entities\repos\core_api.md`
4. Read the current deploy workflows:
   - `git show eclipse-2.1:.github/workflows/deploy_az_webapp.yaml` in the eclipse repo
   - `git show eclipse-2.1:.github/workflows/deploy_az_webapp_container.yaml` in the core_api repo
   - `git show eclipse-2.1:.github/workflows/ci.yml` in both repos (to get the CI workflow name for the `workflow_run` trigger)
5. Pick up at the Phase 1 To-Do checklist.

**Scope:** Modify deploy workflows in both repos to add `workflow_run` triggers that fire when CI passes on `eclipse-2.1`. Keep existing `workflow_dispatch` for manual triggers. Create feature branches, do NOT push directly to `eclipse-2.1`.

**Plan mode rule:** Plan-mode-first for Phase 1. Verify the `workflow_run` trigger semantics (branch filtering, conclusion check) before writing YAML.

When done, update the Session Log in this tracker and check off completed To-Do items.
````

### Phase 2 Boot Prompt — Playwright E2E Tests

````
You are resuming the **Azure Deploy Automation** workstream, Phase 2: Playwright E2E Tests.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\azure-deploy-automation.md`
3. Read required context pages (parallel reads):
   - `C:\Users\PaulRussell\repos\wiki\processes\deployment\eclipse-azure-deployment.md`
   - `C:\Users\PaulRussell\repos\wiki\entities\repos\eclipse.md`
4. In the eclipse repo on `eclipse-2.1`, read:
   - `package.json` (confirm Playwright version and test scripts)
   - `src/app/(auth)/login/page.tsx` (login flow for E2E setup)
   - `src/app/(app_shell)/AppShellLayout.tsx` (app shell structure)
   - `src/app/(app_shell)/dashboards/page.tsx` (dashboard page)
   - `src/components/Navbar/Navbar.tsx` (navigation structure)
5. Pick up at the Phase 2 To-Do checklist.

**Scope:** Create Playwright config, global auth setup, and 5-10 critical-path E2E test files in the eclipse repo. Add E2E job to the deploy workflow. All work on a feature branch.

**Key details:**
- Eclipse uses NextAuth credentials login (email + password)
- Mantine UI components (AppShell, Navbar, etc.)
- Staging URL derived from `vars.AZURE_APP_SERVICE_NAME` + `-stage.azurewebsites.net`
- Test credentials via GitHub secrets `E2E_USERNAME` / `E2E_PASSWORD`
- GEP test account `da8904db` for data-display tests
- Metrics card YoY tooltip only appears with timeframes under 1 year

**Plan mode rule:** Plan-mode-first. The exact test cases depend on the app structure — explore the pages and components before writing tests.

When done, update the Session Log in this tracker and check off completed To-Do items.
````

### Phase 3 Boot Prompt — Swap Automation with Approval Gate

````
You are resuming the **Azure Deploy Automation** workstream, Phase 3: Automated Slot Swap with Approval Gate.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\azure-deploy-automation.md`
3. Read:
   - `C:\Users\PaulRussell\repos\wiki\processes\deployment\eclipse-azure-deployment.md` (swap procedure, backend-first rule)
   - `C:\Users\PaulRussell\repos\wiki\concepts\architecture\azure-environments.md` (resource group: `aldcprodrsgp1c`)
4. Read the deploy workflows as modified by Phase 1 (should now have `workflow_run` triggers).
5. Check the Blockers section for resolved questions (E2E test user, reviewer list, branch protection).
6. Pick up at the Phase 3 To-Do checklist.

**Scope:**
1. Configure GitHub environment protection rules (required reviewers) on "Production (Eclipse 2.1)" for both repos via `gh api`.
2. Add `swap-to-production` job to both deploy workflows — gated by the environment, runs `az webapp deployment slot swap`.
3. Only auto-swap on `workflow_run` triggers (not manual `workflow_dispatch`).
4. Document the backend-first approval order in the workflow step description.

**Key details:**
- App services: `aldcprodwbapeclipse1c01` (frontend), `aldcprodwbapcore1c01` (backend)
- Resource group: `aldcprodrsgp1c`
- OIDC auth — same secrets as the deploy step
- Backend MUST swap before frontend when both change

**Plan mode rule:** Plan-mode-first. Verify environment protection rule API format and swap command syntax before implementing.

When done, update the Session Log in this tracker, check off To-Do items, and apply Pending Wiki Updates to [[eclipse-azure-deployment]].
````

---

## See Also

- [[eclipse-azure-deployment]] — the manual runbook this workstream automates
- [[entities/repos/eclipse|eclipse (repo)]] — frontend repo
- [[core_api]] — backend repo
- [[GitHub Actions]] — CI/CD platform
- [[azure-environments]] — subscription and environment model
- [[ai-pr-workflow]] — the PR workflow this pipeline extends with automated deploy
