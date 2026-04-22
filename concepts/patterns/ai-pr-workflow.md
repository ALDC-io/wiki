---
tags: [concept, pattern, ai, workflow, pr, code-review, engineering-standard, ccx, semgrep, trufflehog]
aliases: [AI PR Workflow, AI Development Workflow, AI-Augmented PR Process, ALDC Development Workflow]
sources: [Confluence ENG/1761050625 (AI Development Workflow Plan, 2026-04-02), Confluence AIRA/1765244929 (ALDC Development Workflow, 2026-04-10)]
created: 2026-04-18
updated: 2026-04-18
---

# AI-Augmented PR Workflow

ALDC's definitive standard for how code goes from idea to production. Applies to all repos. Agreed by the full dev team (Steven, Paul, Vlad, Brayden) 2026-04-02; implemented and expanded by Vlad by 2026-04-10.

> **Strategic context:** This workflow is part of ALDC's broader pivot toward AI-driven and automated software delivery. The goal is to design all AI gates and AI agents with full company context — the Confluence → wiki migration exists specifically to make that context searchable and available to those systems.

## The Chain

**Jira Ticket → Create Branch from main → Code with CCX → Open PR → Automated Checks → Code Owner Review → Merge → Auto-deploy**

Every step is structural. Nothing depends on the contributor remembering to do it.

## Step-by-Step

### 1. Before you code

- **Get a ticket.** No ticket, no work. The ticket defines scope and acceptance criteria.
- **Create a branch from main.** Branch protection rejects direct pushes — including from admins.
- **Read the ADRs** in `docs/decisions/` if touching architecture. Several patterns look wrong but are deliberately correct — ADRs explain why.
- **New to a repo?** Use the CCX `repo-learn` skill — it analyses the repo's patterns and stack.

### 2. While you code

Run **CCX** alongside Claude Code. CCX provides skills, session tracking, team messaging, and auto-learning. See the ALDC Agentic Coding Guidelines in Zeus KB for setup and details.

### 3. Open a PR

Open a PR against main. Four automated checks fire immediately plus a quality-gate aggregator. They run on every PR in every repo — no configuration needed.

#### Automated checks

**1. Security Scan — Semgrep**

Finds security vulnerabilities: SQL injection, XSS, hardcoded credentials, unsafe error handling. Runs thousands of rules including custom ALDC rules (`.semgrep.yml`). Only reports issues *introduced in your PR*, not pre-existing problems.

**2. Secret Scan — TruffleHog**

Scans for leaked credentials — API keys, database passwords, tokens, private keys. Doesn't just pattern-match — **verifies each finding by calling the actual service to confirm the credential is live.** If TruffleHog flags something, it's real.

> If a real credential is found, removing it from code is not enough — it's in git history. Rotate the credential immediately and update everywhere it's used.

**3. AI Code Review — Claude Opus**

Claude reads the full repository, `REVIEW.md` (repo-specific review standards), and all ADRs in `docs/decisions/`, then reviews the PR. Checks:

- Does this change break anything in other files?
- Does it respect the ADR architectural decisions?
- Was error handling or safety code removed?
- Does the code do what the PR title says?
- Are there patterns suggesting the code wasn't reviewed before submission?

Claude posts findings as PR comments. Blocking issues hold the merge button gray. Address or reply to every comment — unresolved conversations block merge.

**4. Architecture Check — PyTestArch**

Verifies code respects structural boundaries (e.g. route modules must not import the database directly; services must not depend on routes). Violations block merge when configured.

**5. Quality-Gate Aggregator**

Collects results from all checks. If any check failed, the aggregator fails and merge is blocked. No exceptions.

### 4. Merge conditions

A PR can merge **only when ALL of the following are true:**

1. All automated checks passed (quality-gate is green)
2. Code owner has approved (defined in `CODEOWNERS`)
3. The approver is **not** the person who pushed the last commit
4. All review conversations are resolved
5. Branch is up to date with main

The bypass list is **empty** — not admins, not repo owners can override. Fix the issue or don't merge.

### 5. After merge

- Auto-deploy triggers for repos with deployment workflows
- Semgrep runs a full scan on the updated main branch
- TruffleHog scans the push-to-main for secrets
- CCX captures session learnings automatically

## Per-repo configuration

Each repo has its own:

| File | Purpose |
|---|---|
| `REVIEW.md` | What the AI reviewer checks for, specific to that repo |
| `CODEOWNERS` | Who must approve PRs |
| `docs/decisions/` | ADRs — architectural decisions explaining non-obvious patterns |
| `.claude/settings.json` | Guards customised for that repo |
| `.semgrep.yml` | Security rules including custom ALDC detection |

## Non-negotiables

1. **No direct push to main.** Branch protection enforces this.
2. **No self-approving your own PR.** Last person who pushed cannot approve.
3. **No bypassing checks.** The bypass list is empty. Fix the issue or don't merge.
4. **No hardcoded credentials.** Use environment variables.
5. **Review your own code before submitting.** Checks catch what you miss — but the first reviewer should be you.

## Addressing check failures from Claude Code

```bash
gh pr view <number> --comments   # see all comments
gh pr checks <number>            # see check statuses
# fix code, commit, push — all checks re-run automatically
```

## Rollout status (as of 2026-04-10)

| Component | Status |
|---|---|
| Feature branch + PR requirement | ✅ Live (GitHub branch protection) |
| Security scan (Semgrep) | ✅ Live |
| Secret scan (TruffleHog) | ✅ Live |
| AI code review (Claude Opus) | ✅ Live |
| Architecture check (PyTestArch) | ✅ Live (where configured) |
| Quality-gate aggregator | ✅ Live |
| CCX skills + session tracking | ✅ Live |
| Auto-deploy on merge | ✅ Live (repos with deployment workflows) |

## See Also

- [[adversarial-investigation-skill]] — `/investigate-adversarial` Claude Code skill for deep investigations
- [[git-branching-strategy]] — branch naming, merge paths, commit format, semver
- [[ai-development-project-standard]] — tracking/metrics standard for AI-built projects (tokens, cost, ROI)
- [[cce]] / [[factoria]] / [[opentribe]] — internal AI projects subject to this workflow
