---
tags: [pattern, sessions, git, worktrees, repo-hygiene, agent-factory, prefect-connectors, aldc-launchpad]
aliases: [artefact homes, session contention, where does this file live, two sessions one checkout]
sources: [agent-factory commits 66b6511 c242913 f837e00, prefect-connectors 8b7c68d, aldc-launchpad 2b44282, measured 2026-08-23]
created: 2026-08-23
updated: 2026-08-23
---

# Session contention and artefact homes

Two problems that turned out to be the same problem: **several Claude sessions editing one checkout**,
and **nobody able to say which repo a given file belongs in**. Both were measured on 2026-08-23 after
one produced a broken `HEAD`.

## The incident, in one paragraph

Four sessions were live. One had `factory/repo.py` created but unstaged; another ran `git add` across
the directory and committed a `claims.py` that imports it. The commit shipped a tree that **did not
import**. It was never pushed, so it was contained — by luck, not by a control. **Neither session
acted wrongly**, which is what makes this a design problem rather than a discipline problem.

## Part 1 — where does an artefact live?

⭐ **The discriminator is one testable question, not a category judgement:**

> **"If I move this, does something break?"**

Measured across three repos:

| Repo | doc files | read by code |
|---|---|---|
| `agent-factory` | 41 | **most of them** |
| `prefect-connectors` | 59 | **one** |
| `aldc-launchpad` | ~1,150 | only script↔output pairs |

That asymmetry is the whole argument, and it is why the two repos get **opposite** answers.

### Three homes

| Home | What | Test |
|---|---|---|
| **with the code** | anything the package reads at import/run time | moving it breaks an import, a test, or a gate |
| **with the repo** | docs on operating *one* codebase, not read by it | moving it makes it undiscoverable to whoever is reading that code |
| **`aldc-launchpad`** | session memory, cross-repo narrative | it spans repos, so it has no single code home |

### ⛔ The rule that was wrong

`aldc-launchpad/CLAUDE.md` said *"agent-factory holds code and contracts only. Its boot prompts and
evidence land here."* **Following that literally breaks the build.** `factory/dispatch.py` validates
its dependency map against `docs/research/*.md` **at import time**; `calibration.py` reads `evals/`;
`readiness.py` reads `docs/specs/`, `docs/findings.d/` and `docs/artifacts/`. Research a package
validates against is **not** session memory, however much it looks like a document.

Corrected 2026-08-23. See [[agent-factory]].

### What actually moved

Only session ephemera, and mostly *out of the repo that was supposed to be clean*
([[prefect-connectors]]): a drafted Jira comment, three session drafts, and a `docs/artifacts/`
directory whose own README already stated the rule that moved it. `PROGRESS.md` was tracked in git
against a standing preference that it stay local; untracked and gitignored.

**Handbooks stayed** — `MIGRATION_HANDBOOK`, `KNOWN_ISSUES`, `CONNECTOR_LANES`, `onboarding/`.
Moving those to the memory layer would make them undiscoverable to the next person reading connector
code, which is the failure the rule exists to prevent.

⚠ **Check references before moving anything.** One file appeared to have 12 references; all 12 were
copies of the same file inside `.wt/` worktrees and `.sessions-pr/` sandboxes. `cmp` every copy
against its original before deleting the original.

## Part 2 — detecting contention

### The instrument that existed keyed on the wrong thing

`sessions.collisions()` reported working directories holding more than one running session. On the
day of the incident it reported **four sessions in `aldc-launchpad`** — while the clobber happened in
**`agent-factory`**, which no session had as its `cwd` at all. It flagged the right sessions **for the
wrong reason**, and would have been silent had their cwds differed.

⭐ **A session's `cwd` says where it started, not what it writes to.**

### What replaced it

`sessions.contended_repos()` reports repos holding **uncommitted work while more than one session is
alive to have written it**. Candidate set = every live session's cwd **plus the primary worktree** —
that last term is what makes the edited-from-elsewhere repo visible.

⛔ **Attribution is `NOT-MEASURABLE` and the instrument says so on every row.** Nothing records which
session touched which file. It reports a **condition**, never a culprit. A row that guessed would be
believed.

### And the guard that catches the consequence

A pre-commit hook exports `git checkout-index` to a temp directory and imports from **there**.

**Checking the working tree would have passed over the real defect** — the untracked file was sitting
on disk. The only meaningful check is against the tree git is about to create. Install it into the
git **common** dir so one install covers every lane worktree.

⚠ Export the **whole index**, not just `.py`. Narrowing it produced false positives from modules that
read data files at import.

## Reusable rules

1. **Ask "does something break if I move this?"** — not "what kind of document is this?".
2. **State a rule only if the repo can survive it.** A rule that breaks the build on contact is worse
   than no rule, because somebody will obey it.
3. **Detect contention on the repo being edited, not the directory a session started in.**
4. **Never guess attribution.** Report the hazard; say the attribution is not measurable.
5. **Check the index, not the working tree**, whenever the question is "what will other people get?".
6. **Stage explicit paths. Never `git add -A` in a shared checkout.**
7. **Killing a PID is not closing a session** — a background session is daemon-supervised and
   respawns with a new PID. See [[resuming-claude-sessions-windows]].
8. ⭐ **An artefact's URL may appear in exactly one repo.** Added 2026-08-29. The generated registry
   (`aldc-launchpad/docs/artifacts/REGISTRY.md`) locates each artifact's source by `git grep`-ing
   every repo for its URL, so a second repo mentioning that URL makes the source **ambiguous, and the
   registry then picks by path ranking rather than by truth**. Proven the same day: a readout filed in
   `aldc-launchpad/docs/readouts/` was mis-attributed to `agent-factory/docs/artifacts/` purely
   because the latter's README carried a courteous "it lives over there" pointer *with the link in
   it*. Keep the prose pointer; drop the URL; let the registry hold the link.

## The artefact registry (added 2026-08-29)

The placement rules above are now **measured rather than remembered**. `REGISTRY.md` is generated —
*"Generated. Do not hand-edit."* — by:

```
Artifact action:"list" scope:"all" limit:50   →  docs/artifacts/registry/live.txt   (verbatim)
python docs/artifacts/registry/build.py
```

It reports, per run: how many artifacts are in the gallery, how many have a **located** source (a repo
references the URL), how many are **probable**, how many have **no source anywhere**, how many are
**orphaned** (recorded in a repo but absent from the gallery), and any **name collisions**.

Measured 2026-08-29: **26 in the gallery · 16 located · 2 probable · 8 with no source anywhere ·
13 orphaned · 1 name collision.**

Two standing consequences:

- **An artifact with no source cannot be rebuilt.** Eight are in that state. If one drifts or needs
  editing, the next session starts from scratch — which is the same failure the three-homes rule
  exists to prevent, one layer up.
- **A name collision is a session hazard, not an aesthetic one.** Two artifacts both reading as
  "agent factory" (`0fdcb1cd…` and `50d3ca62…`) cannot be told apart by a session that was handed
  only the name.

**Register an artifact by writing its URL into its own source directory's README** — that is the hop
`build.py` measures. Publishing without doing so produces a sourceless artifact.

## See Also

- [[agent-factory]] — where this was found, and the readiness harness it protects
- [[agent-session-completion-signals]] — the other half of the two-sessions problem: knowing when the other one has actually STOPPED
- [[prefect-connectors]] — the repo the ephemera left
- [[resuming-claude-sessions-windows]] — session lifecycle on Windows
