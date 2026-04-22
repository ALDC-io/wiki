---
tags: [concept, pattern, git, branching, release, workflow, commits, semver]
aliases: [Git Branching Strategy, Git branching cheatsheet, ALDC branching model, Commit message format, Semantic Versioning, Semver]
sources: [Confluence TECH/1362296835 (Git Branching Strategy), Confluence TECH/1362133015 (Git branching cheatsheet), Confluence TECH/1242300433 (GitHub commit conventions), Confluence TECH/1010335752 (Semantic Versioning)]
created: 2026-04-17
updated: 2026-04-17
---

# Git Branching Strategy

ALDC's branching model for the [[clients-repo]]. Each client has its own pair of long-lived branches that all eventually merge into `main`.

## Branch layout

Each client has two long-lived branches plus the shared `main`:

| Branch | Role | Contains |
|---|---|---|
| `<CLIENT>/development` | Internal dev | Reviewed and internally-tested changes, **not yet** client-tested |
| `<CLIENT>/user-testing` | Client review | Changes under client testing, awaiting approval |
| `main` | Production | What is currently deployed in production |

Example: Kit & Ace → `KIT_ACE/development`, `KIT_ACE/user-testing`. Fusion 92 → `FUSION_92/development`, `FUSION_92/user-testing`.

**Rule**: developers open PRs into the client's `development` branch — never directly into `user-testing` or `main`.

## Happy-path walkthrough

1. **Developer** makes a change in the data-warehouse model or [[Eclipse]] connection/template
2. **Developer** tests as much as they can locally, opens a PR into the client's `development` branch, adds another developer as reviewer
3. **Reviewer** comments on the PR and approves once their comments are resolved
4. **Karen** (or whoever is applicable) tests on our side, posts issues either on the PR or on the Jira ticket
5. Once all code review and test issues are resolved, the PR is merged and the feature branch deleted
6. When the changes are ready for **user testing**, merge `development` → `user-testing`:
   - Create a new branch from `development`, then PR *that* branch into `user-testing`. Prevents future `development` commits from accidentally getting pulled into `user-testing`.
7. Hand Eclipse Test over to the client for user testing
   - If the client finds issues: create a **hotfix branch** off the client's `user-testing`, fix, merge back into `user-testing`
8. Once the client verifies the changes: merge `user-testing` → `main`; also merge any hotfix changes from `user-testing` back into `development` so dev doesn't lose them
9. **Deploy to Production directly from `main`** — see [[client-release-checklist]]

## Cheatsheet — "what are you trying to do?"

### Make a routine change for a client

1. Create a new branch off `<CLIENT>/development` — name it starting with the Service Item code (e.g. `ITM-123` or `ITM-123-make-some-changes`)
2. Push to GitHub, open a PR into `<CLIENT>/development`, add a reviewer
3. Get the PR reviewed; hand off to whoever tests internally (usually Karen — test the model/report in Test)
4. Merge the PR into `<CLIENT>/development`
5. Merge `<CLIENT>/development` → `<CLIENT>/user-testing`, deploy where necessary
6. Merge `<CLIENT>/user-testing` → `main`, deploy directly from `main`

> **Caveat**: if `user-testing` contains multiple changes but only one is production-ready, you need to handle that on a case-by-case basis — the branching model doesn't cleanly support cherry-picking one of several in-flight changes. Known minor flaw.

### Fix something the client found during user testing

1. Create a new branch off `<CLIENT>/user-testing`
2. Make your fix, open a PR back into `<CLIENT>/user-testing`
3. Normal review + test flow, then hand back to the client for re-testing

> **Important**: after merging the hotfix, **also merge `<CLIENT>/user-testing` → `<CLIENT>/development`** so `development` catches up.

### Hotfix directly to production

1. Create a new branch off `main`
2. Make your fix, open a PR back into `main`, get it reviewed + tested
3. Merge the PR

> **Important**: after merging to `main`, **also merge `main` → `<CLIENT>/user-testing`** and **`main` → `<CLIENT>/development`** for the affected client so both branches catch up with the hotfix.

## Known flaws

- **Mixed in-flight changes in `user-testing`**: if multiple independent changes are sitting in `user-testing` and only some are client-approved, promoting just the approved subset is awkward. Handle ad-hoc.

## Commit message format

Sourced from Confluence TECH/1242300433 (GitHub page), ingested 2026-04-17.

Commits should be labelled `<Jira-ID>-<WorkTitle>`. Examples:

- `CRTL-1210-AmazonAdsConnector`
- `CRTL-827-LoginScreen`
- `ITM-123-fix-inventory-filter`

If the work cannot be summarized by a single short title, the Jira ID alone is acceptable.

## Versioning (semver)

Sourced from Confluence TECH/1010335752 (Semantic Versioning), ingested 2026-04-17. Content dates from 2022; the "what counts as a MAJOR bump" decision was explicitly still open at source time — treat those thresholds as proposed-not-ratified.

ALDC releases follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH` (e.g. `1.3.14`).

| Position | Increment when | ALDC interpretation |
|---|---|---|
| `MAJOR` | Incompatible API changes (large system impact) | Expected to be rare. Should only bump after a major rework / code thrown-away event. Proposed threshold: "3+ sprints of dedicated work on a portion of the system." |
| `MINOR` | Backwards-compatible feature additions | Typical QA release |
| `PATCH` | Backwards-compatible bug fixes | Rush fixes that ship outside the usual QA pipeline |

**Additional notation** (from the semver spec):

- **Prerelease**: hyphen suffix — `1.0.0-alpha`, `1.0.0-alpha.1`, `1.0.0-0.3.7`
- **Build metadata**: plus-sign suffix — `1.0.0+001`, `1.0.0-beta+exp.sha.5114f85`, `1.0.0+21AF26D3`

**Usage rules:**

- No negative integers
- Values start at `0`
- `MAJOR` version `0` = predevelopment; `1` = first public API release
- When `MAJOR` or `MINOR` iterate, positions to the right reset to `0` (e.g. `1.4.7` → `2.0.0`)

**Open question flagged in source**: "we will need to decide what is counted as a MAJOR version update, otherwise we will end up at version 50+ on our API very quickly." Treat the `MAJOR` threshold as needing team alignment before a real bump.

## See Also

- [[clients-repo]] — the repo this strategy applies to
- [[client-release-checklist]] — deploy checklist that runs after `main` is updated
- [[gep-snowflake-pbi-deployment]] — GEP-specific deployment walkthrough
- [[ticket-breakdown-to-ship]] — ticket-lifecycle workflow this slots into
