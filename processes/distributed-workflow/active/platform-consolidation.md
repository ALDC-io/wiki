---
tags: [distributed-workflow, active, agent-factory, platform, consolidation, sessions, credentials]
aliases: [Platform Consolidation, Wave Zero Landing, Branch Reconciliation]
sources: [agent-factory branches measured 2026-08-29, aldc-launchpad .gitignore:39, Wave Zero Board artifact d75fbea0]
created: 2026-08-29
updated: 2026-08-29
---

# Platform Consolidation

## Goal

Several Claude sessions run in parallel across a 54-repo estate and cannot see each other. The
result, measured 2026-08-29: **finished reviewed work sits on branches nothing has merged**, the
readiness figure everyone quotes is **measured on a checkout missing that work**, and a tidy-up
recommendation repeated all day **would have committed a production credential**.

Done looks like: one branch carrying the finished work, one readiness number with its branch
stated beside it, an evidence-backed disposition list for the estate, and the credential hazard
recorded where anyone acting on the tidy-up will see it. **No repo is mutated by this
workstream** — it measures and lists; Paul merges.

## Lane

Wiki: ALDC

Owned paths (this workstream may write here):

- `processes/distributed-workflow/active/platform-consolidation.md` (this tracker)
- `concepts/patterns/` — **new pages only**, listed under *Concepts to nail down*

Read-only outside the lane. Shared-file edits go to *Pending Wiki Updates*, never applied
directly — a rule this session's Neurospect counterpart broke and is recorded as having broken.

## Required Context

Every session must read these at boot. **Three of them already answer questions this workstream
was about to re-derive** — read them before proposing any new concept.

- [[../../../concepts/patterns/session-contention-and-artefact-homes]] — ⭐ already answers "where
  do agent artefacts live" with three homes and the testable discriminator *"If I move this, does
  something break?"*. Also records that `agent-factory`'s docs are **load-bearing code**
  (`factory/dispatch.py` validates `docs/research/*.md` at import), so a name-based retirement
  call gets it backwards.
- [[../../../concepts/patterns/vacuous-verification]] — the measurement-gap family: a result that
  is structurally perfect and empty. Five recorded cases; this workstream adds a sixth.
- [[../orchestration-pattern]] — lanes, single-writer trackers, the shared-file protocol.
- [[../session-lifecycle]] — boot, checkpoint, handoff, end-of-day merge.

Cross-wiki / cross-repo references use absolute paths:

- `C:\Users\PaulRussell\repos\agent-factory\factory\readiness.py` — the 30 gates
- `C:\Users\PaulRussell\repos\agent-factory\scripts\local_tracker.py` — the live UI, `--serve` re-measures per refresh
- `C:\Users\PaulRussell\repos\aldc-launchpad\boot-prompts\engineering-workflow-review-2026-08-29.md` — 31 findings, U1–U6 urgent

## Plan-Mode Rule

**Every session is plan-mode-first.** This workstream touches branches, credentials and repo
retirement — three classes where an unreviewed action is expensive and, in one case,
irreversible. No merge, no deletion and no repo mutation without Paul approving a written plan.

---

## ⛔ Credential hazard — read before acting on any "get untracked work into git" item

The published guidance *"get deploy and rollback into version control — ~1 day"* spans **two
different things with confusingly similar names**. Only one is safe.

| Thing | Status | Action |
|---|---|---|
| `cli/deploy.py`, `cli/deploy_pbi.py`, `cli/rollback.py`, `cli/rollback_pbi.py` | untracked, **not** ignored — genuine drift | ✅ safe to track |
| `rollback/` — **the directory** | **deliberately gitignored**, `.gitignore:39`, commented *"Local rollback snapshots (client data — never commit)"* | ⛔ **never commit** |

`rollback/` holds **11 files; 9 contain the name `CORE_API_CLIENT_TOKEN`** — a token that is
unrotated and authenticates against **prod** `core_api`. The `.gitignore` comment also names
**client data**, so the case stands on more than the token alone.

Verification, printing no values:
`grep -rl 'CORE_API_CLIENT_TOKEN' rollback/ | wc -l` → 9 (of `ls rollback/ | wc -l` → 11)

⛔ **Do not let the two audiences merge.** The open credential exposures and one
written-but-undeployed security fix are enumerated in the private **Council Room** artifact
(`05c2d618`). The leadership-facing **Launchpad** brief (`0eec3279`) was written deliberately
*without* that detail.

---

## Measured state — 2026-08-29

**Branch divergence in `agent-factory`.** Nothing has ever been merged to `main`; every branch is
ahead of it and none behind.

```
cmd: git rev-list --left-right --count main...<branch>
     git merge-base --is-ancestor <sha> <branch>   for 040fe79 4e321d2 3e6416b 38ff8f0

branch                        ahead of main   gate-fix commits
feat/readiness-generator            144            0 / 4
trial/wave0-rescue                  143            0 / 4
lane/control-plane-renamed           87            4 / 4
lane/control-plane                   86            4 / 4
lane/artifact                        61            0 / 4
lane/certify                         60            0 / 4
```

**Readiness per branch**, measured in throwaway detached worktrees, working trees untouched.

```
cmd: git worktree add --detach <tmp> <branch> && python -m factory.readiness

branch                        score    loop  bounded  judgement  certified  handover
lane/control-plane             8/30     0/3    0/4       0/8        3/8        5/7
lane/control-plane-renamed     8/30     0/3    0/4       0/8        3/8        5/7
feat/readiness-generator       9/30     0/3    0/4       0/8        4/8        5/7
trial/wave0-rescue             9/30     0/3    0/4       0/8        4/8        5/7
main                            n/a  — predates factory.readiness entirely
```

### ⛔ The Wave Zero claim does NOT reproduce

The **Wave Zero Board** artifact (`d75fbea0`, 2026-08-29) states that two gates flip on
`lane/control-plane` alone — *"cap FAIL → PASS, the restarting path is capped"*. Measured today:

- `lane/control-plane` carries **4 of 4** cap / from-history / reaper / concurrency commits.
- It scores **8/30 — one LOWER** than the branch carrying none of them.
- **`bounded` is 0/4 and `judgement` is 0/8 on every branch measured.**

The work is real; **it does not move the gates it is named for.** One of those commits itself
says the gates *"could not see the defects they are named for"* and that the wiring checks *"were
greps, and the probe invented a status"* — so part of `0/4` and `0/8` is a **broken instrument,
not a broken system**. That distinction is the repository's entire thesis, applied to its own
score.

⚠️ **A score is a property of a checkout, not of a repo.** `feat/readiness-generator` measured
**10/30** in its working tree and **9/30** in a detached worktree the same day.

⛔ **The stated cause was wrong, and is now disproven — do not repeat it.** This tracker originally
said the difference was *"most likely the pushed-to-origin gate, since commit `50d1154` is
unpushed"*. `factory/readiness.py:600` `g_repo_is_durable()` runs **only `git remote`** and returns
`_pass(f"pushed to {remotes}")` whenever that list is non-empty. It never reads push state, so it
returns the identical verdict in both checkouts and **cannot** account for a one-point difference.
Re-measured 2026-08-29 after every commit was pushed: the gate's behaviour is unchanged, as
predicted. **The cause of the 1-point difference is still unknown.** Measure it; do not re-derive
the hypothesis.

⭐ **The gate is a live instance of the defect this repo is named for.** It is green by coincidence,
not by measurement — it would print *"pushed to origin"* with every commit unpushed. As of
2026-08-29 it is sharper still: `agent-factory`'s `origin` carries the push URL
`no-push://aldc-io-disabled` (a deliberate guard, see *Gotchas*), so the durable gate now reports
**"pushed to origin, personal"** while naming a remote it is structurally unable to push to. See
[[../../../concepts/patterns/vacuous-verification]].

**State the branch beside any figure** — and note that "and ideally the push state" was advice this
gate cannot act on.

---

## Estate corrections — 2026-08-29, all verified independently

Three baseline figures this workstream started from were wrong. Each was caught by re-running a
**stated** command, which is the argument for stating them.

**1. ⛔ `concepts/architecture/repo-integration-map.md` is stale and actively misleading — do NOT
start from it.** It says Prefect work lives at `connector/accounts/<ACCOUNT>/deployments/` on
branch `operation-fiasco`. **`connector/accounts` does not exist** (`ls connector/accounts` →
absent). The page is `updated: 2026-04-20` and mentions **none** of `prefect-connectors`,
`aldc-launchpad`, `agent-factory`, `triage-agent`, `observability`,
`navira-marketing-dashboard`, `ccx`, `zeus-chat-exp`, `conductor` — four of which are top-5 by
recent activity. It is excellent for the 12 repos it does cover. Treat as a base, never an answer.

**2. Seven "repos" are git worktrees, not repos.** Verified with `git worktree list`:

| Directory | Worktree of | Branch |
|---|---|---|
| `eclipse-gp309-fe`, `eclipse-yoy-fix` | `eclipse` | `fix/gp309-surface-error-detail`, `feature/metrics-card-yoy` |
| `core_api-gp309`, `core_api-perf-telemetry` | `core_api` | `fix/gp309-payload-cap`, `perf/dataset-query-telemetry` |
| `clients-attribution`, `clients-navira-consol` | `clients` | `feature/amazon-attribution`, `…navira-canonical-consolidation` |
| `aldc-launchpad-docs` | `aldc-launchpad` | `docs/pantheon-handoff` |

They share one object store. Retiring one is `git worktree remove`, **not a repo decision** —
and it is cheap: all seven have 0 commits unreachable from a remote except
`clients-navira-consol` (2), `core_api-perf-telemetry` (1), `aldc-launchpad-docs` (1).
**This deletes half the "duplication clusters" this tracker originally listed.**

Corrected estate shape: `C:\Users\PaulRussell\repos\` holds **67 directories = 53 git repos +
7 worktrees + 6 non-git** (one, `lessonhub`, is empty). CI: 29 directories contain
`.github/workflows`, but 6 are worktrees inheriting the same files → **23 distinct repos**.

**3. ⭐ Connector deployment counts were double the truth — and the error was mine.**

```
cmd: ls connector/accounts/<A>/deployments/*.py | grep -v __init__ | wc -l

account      published   actual
GEP              7          5
FUSION_92        3          1
KA               3          1
ALDC_QA          3          1
TOTAL           16          8
```

The published command was `ls .../deployments | wc -l`, which counted `__init__.py` and a
`__pycache__/` directory as deployments. The scale figure in the *Certification Loop* artifact
(`d3f0154e`) therefore reads **16 of 196 pairs = 8.2% covered** when the truth is
**8 of 196 = 4.1%**.

⭐ **The refinement this forces on the counts rule:** *printing the command does not make a count
correct — it makes it **auditable**.* This number was published **with** its command and was
still wrong; it was caught precisely because a second reader could re-run it. The rule earns its
place through the audit it enables, not through the discipline it signals.

**One genuine fork remains:** `connector` vs `prefect-connectors` share root commit `57a179e6`
(2021-03-04) with different remotes. **Canonical is `prefect-connectors`** (160 commits in 60
days vs 5; its README states it "replaces the legacy on-prem `connector` agent architecture").
`connector` is in run-out, not dead — last commit 2026-07-15, GP-287.

---

## Concepts to nail down

Three are new. Everything else is already written; do not re-derive it.

1. **A measurement is a property of a checkout.** New. A readiness score, a test count or a gate
   tally is meaningless without the branch it ran against. Today the same branch produced 9 and
   10 within hours. Proposed page: `concepts/patterns/measurement-belongs-to-a-checkout.md`.

2. **Self-truncating measurement.** New case for [[../../../concepts/patterns/vacuous-verification]],
   and a better worked example than the one currently in `~/.claude/CLAUDE.md`. A session
   reported *"5 of 11 files contain the token"*; the answer is 9. Its own account:

   > *"My original command ended in `| head -5`. I capped my own output at five, then reported
   > five as the count. The command was structurally incapable of returning a sixth, so no amount
   > of re-reading the output would have caught it — only re-running it differently."*

   ⭐ This beats the `INDEX.md` illustration in the counts rule, because that number rotted
   through **hand-maintenance** — the case everyone already distrusts. This one came from a
   **live command**, which is the case people assume is safe.

3. **Two things, one name.** New. `cli/rollback.py` (safe to track) and `rollback/` (never
   commit) differ by a slash. Guidance written at the wrong granularity is not merely vague — it
   is actively dangerous when someone applies it mechanically. Belongs beside the credential
   hazard above.

**Already nailed — reference, do not rewrite:** artefact homes and the *"if I move this, does
something break"* test · vacuous verification · lanes and the shared-file protocol · the four
verdicts (canonical in `agent-factory/factory/contract.py`).

---

## Landscape scan — 2026-08-29

Two research passes: shipped products, and open-source repos. Claims tiered
`OBSERVED > REPORTED > MARKETED`; a MARKETED claim is never a design premise.

### ⛔ Our verdict model is COARSER than the state of the art, not finer

We believed the four non-collapsible verdicts were unusual. **Half true, and the wrong half.**

`inspect_ai` (UK AI Safety Institute · MIT · 2.7k★ · pushed 2026-08-29) separates **four things
this estate collapses into one** — incorrect · refused · crashed · **hit-a-cap**:

- `Score` values `CORRECT / INCORRECT / PARTIAL / NOANSWER`, plus `Score.unscored()` — a NaN
  *"preserved but excluded from metrics and reducers"*, i.e. a NOT_RUN that survives into the log
  without contaminating the aggregate.
- `EvalSample` carries `error: EvalError|None` **and** `limit: EvalSampleLimit|None`, the latter
  typed `context | time | working | message | token | turn | cost | operator | custom`.

`SWE-bench` (MIT, `harness/reporting.py` schema v2) does the same at population level — nine ID
lists including **`ambiguous_failure`**, the honest form of `UNMEASURABLE`.

⭐ **What DOES appear unique: the negative-control eval.** No project found pre-registers that an
assertion *can fail* before trusting it. The closest (EvilGenie, SpecBench) detect reward hacking
after the fact. Detection, not pre-registration. **That, not the verdict count, is the
differentiator.**

### ⛔ DEFECT introduced today by commit `50d1154` — cap-kill is recorded as failure

`RepoDeployer.run_agent` records `note_outcome(key, f"exit {rc}")` for **any** non-zero exit. A
run terminated by `--max-turns` or `--max-budget-usd` therefore lands in the ledger as a
*failure*, and `AttemptLedger.context()` tells the next attempt *"do something different"* —
which is **actively wrong advice** after a cap-kill. A capped run may need a larger budget and
the *same* approach; a failed run needs a different one.

**Fix:** add a `cap` outcome distinct from `ok` and `exit N`, modelled on `inspect_ai`'s
`limit` field. Small, and it should land before anyone relies on retry context.

### Gaps worth closing, ranked by value ÷ effort

| # | Gap | Who has it | Tier |
|---|---|---|---|
| 1 | **Fix → permanent eval case, automatically** — solves our corpus-of-1 directly; the corpus should grow from real failures | LangSmith Engine, Arize Signal | REPORTED |
| 2 | **Graduated trust / tiered autonomy** — ⭐ this *is* the qualification ladder, and it ships today | Sentry Seer (per-project actionability score gates PR creation); Resolve.ai (auto-executes only well-defined patterns) | OBSERVED / REPORTED |
| 3 | **Triage and repair separated by policy** — a cleaner authority boundary than ours | Charlie Labs daemons: YAML deny-rules, the triage daemon *cannot* open PRs, change code, or override a human-set priority | OBSERVED |
| 4 | **Blast-radius preview before approval** — concrete counts of files/records/users touched, shown pre-approval | emerging pattern; no shipped product verified | REPORTED |
| 5 | **The cap category** (above) | `inspect_ai` | OBSERVED |

### ⭐ The open field

**No vendor closes the loop by proving the error rate dropped after merge.** Classification,
root-cause and PR drafting are automated everywhere; accepting the root cause, merging, and
deciding the fix *worked in production* are universally human. That is precisely the shape an
evidence-gated four-verdict system is built for.

**Architectural signal:** Sentry Seer is a pipeline, not a product — it **hands code generation
off to Claude Code / Cursor** rather than doing it itself. Our position is the verification
layer, not another generator.

⚠️ **Refused as premises:** Seer's *"94.5% root-cause accuracy"* and *"38,000 issues fixed"* are
MARKETED and self-graded, with "accuracy" undefined. Best time-saved evidence anywhere is 38%
MTTR reduction at DigitalOcean (REPORTED).

### Adoptable, permissively licensed

`inspect_ai` MIT — the limit/error split · `dagger/container-use` Apache-2.0 — per-agent
container + worktree isolation · `anthropic-experimental/sandbox-runtime` Apache-2.0 — cheap
OS-level blast radius · `swt-bench` MIT — judges whether a generated test **reproduces** a bug,
the hard step in triage · `harbor` Apache-2.0 — input lockfile pattern.

⛔ **Do not adopt:** `Roo-Code` **archived** · `Agentless` dead since 2024-12 · `aider` 3 months
stale with **1,834 open issues** · `moatless-tools`, `AutoCodeRover`, `Devon`, `micro-agent`
12–21 months stale. **Licence traps: `autogen` is CC-BY-4.0 — not a code licence — and Phoenix is
Elastic 2.0, not OSI.**

---

## Session Log

Append-only. Newest at the bottom.

### 2026-08-29 — branch reconciliation measured; Wave Zero claim refuted

- did: measured divergence and readiness for six `agent-factory` branches in detached worktrees;
  verified the `rollback/` credential hazard independently (9 of 11, not 5); confirmed no run or
  task record carries a ticket key (`grep -nE "ticket|jira|GP-" factory/runs.py factory/tasks.py`
  → empty).
- decided: measurement only — Paul performs all merges. Disposition lists carry evidence and an
  UNCLEAR verdict rather than a guess.
- next: **land the finished work.** Trial-merge `lane/control-plane` into `feat/readiness-generator`
  in a scratch worktree, resolve the `sessions` naming collision with
  `lane/control-plane-renamed` first, and re-measure. Then W1 disposition list, then W2 diagrams.

## Decisions Log

- 2026-08-29 — **Measurement only; Paul merges.** Seven peer sessions were live and one working
  tree drifted 88→90 files mid-session. No branch operation is worth colliding with live work.
- 2026-08-29 — **Disposition list, no action.** A wrong "remove" is expensive and irreversible;
  rows carry evidence and may say UNCLEAR.
- 2026-08-29 — **Verify, never inherit, a peer session's measurement.** Wave Zero's gate claim did
  not reproduce. Peer findings enter this tracker as hypotheses with their source named.
- 2026-08-29 — **Retirement is decided behaviourally, not nominally.** The test is *"does
  anything break if I move this"*, per [[../../../concepts/patterns/session-contention-and-artefact-homes]].

## Pending Wiki Updates

Applied during the end-of-day merge session. **Not applied directly by this workstream.**

- `index.md`: add under distributed-workflow actives — `[[processes/distributed-workflow/active/platform-consolidation]] — **Platform Consolidation** (created 2026-08-29). Lands finished-but-unmerged work across six agent-factory branches, produces an evidence-backed estate disposition list, and records a credential hazard in aldc-launchpad's untracked-work tidy-up. ⛔ Wave Zero Board's "two gates flip on lane/control-plane" does NOT reproduce — that branch carries 4/4 gate-fix commits and scores 8/30, one lower than the branch carrying none; bounded 0/4 and judgement 0/8 hold on every branch. Nothing has ever been merged to main.`
- `log.md`: append — `| 2026-08-29 | measure | **Six agent-factory branches measured; nothing ever merged to main.** feat/readiness-generator 144 ahead / 0-of-4 gate fixes · lane/control-plane 86 ahead / 4-of-4 · scores 9/30 and 8/30 respectively, so the branch with the fixes scores LOWER. bounded 0/4 and judgement 0/8 on every branch — **Wave Zero Board's "cap FAIL → PASS" claim does not reproduce.** Same branch measured 10/30 in-tree and 9/30 detached; ⛔ the pushed-to-origin hypothesis is DISPROVEN (`readiness.py:600` runs only `git remote` and never reads push state) and the cause is still unknown. ⛔ Credential hazard found in aldc-launchpad: `rollback/` is gitignored deliberately (.gitignore:39, "client data — never commit") and 9 of its 11 files carry `CORE_API_CLIENT_TOKEN` against **prod**; the four `cli/*.py` deploy/rollback scripts are the safe half. A published brief's "get deploy and rollback into version control" would have committed the unsafe half. |`
- `action-items.md`: add to Open — `2026-08-29 — Rotate CORE_API_CLIENT_TOKEN (prod core_api). Unrotated, present in 9 of 11 gitignored rollback/ files and already in tracked files and pushed commits per the Council Room audit.`

## Blockers / Open Questions

- 2026-08-29 — Merge order for the six branches. `lane/control-plane` and
  `lane/control-plane-renamed` differ by one commit and a naming collision (*"two lanes both
  built a sessions"*); which name wins is Paul's call.
- ~~2026-08-29 — Is the 10/30 vs 9/30 difference the push-state gate?~~ **CLOSED, refuted
  2026-08-29.** The proposed test could not have discriminated: `g_repo_is_durable()` reads only
  `git remote`. Everything is now pushed and the gate is unchanged. **Still open: what actually
  causes the 1-point difference between a working tree and a detached worktree at the same commit.**
- 2026-08-29 — Council Room enumerates an undeployed security fix. Deploying it is out of this
  workstream's lane and needs an owner.

## Cross-Lane Requests

- 2026-08-29 — wanted to edit `index.md` and `log.md` directly. Did not; they are in *Pending
  Wiki Updates* above. Recorded because the Neurospect counterpart of this session **did** edit
  its shared files directly, against [[../orchestration-pattern]], and that should not become
  precedent.

## Next Session Boot Prompt

````
You are resuming the Platform Consolidation workstream. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\platform-consolidation.md`.
3. Read every page in *Required Context* (parallel reads). Two of them already answer
   questions about artefact homes and measurement gaps — do not re-derive them.
4. Pick up at the *next:* line of the most recent *Session Log* entry.

Plan mode rule: EVERY session is plan-mode-first. This workstream touches branches, credentials
and repo retirement. No merge, deletion or repo mutation without Paul approving a written plan.

Before trusting any number in this tracker, re-measure it — the commands are stated beside each
one, and a score is a property of a checkout, not of a repo.

When done, follow § *Checkpoint* in
`C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md`.
````

## See Also

- [[../orchestration-pattern]]
- [[../session-lifecycle]]
- [[../../../concepts/patterns/session-contention-and-artefact-homes]]
- [[../../../concepts/patterns/vacuous-verification]]
