---
tags: [concept, architecture, governance, cell-os, agent-factory, evidence, gates]
aliases: [CELL OS gates, CELL//OS governance gates, next-gates handoff, DEC-20260906-001, Gate 0.5, Gate 1, Gate 2]
sources: [CELL_OS_Next_Gates_Handoff_v1/, CELL_OS_Next_Gates_Handoff_v1/reference/CELL_OS_Baseline_Approval_Record_v1.md, CELL_OS_Next_Gates_Handoff_v1/reference/CELL_OS_Baseline_Correction_Addendum_v1.md]
created: 2026-09-06
updated: 2026-09-06
---

# CELL // OS governance gates

The bounded, founder-authorized gate sequence that advances [[agent-factory]] / CELL // OS without
letting any one session decide its own scope. Each gate runs in a **fresh session**, against
**hash-verified control inputs**, inside an explicitly stated authority boundary, and returns a
checksum-verifiable result ZIP that goes back to ChatGPT unchanged for second-pass review.

The pattern is the point: the prompt is written by one party, executed by another, and the
executor's authority is enumerated — including what it may **not** do — so that "I could see an
obvious fix" never becomes "I applied an obvious fix".

## Governing records

| Record | ID | SHA-256 | Role |
|---|---|---|---|
| Baseline Approval Record | `DEC-20260906-001` | `a00a80d4…8241d518` | The founder's approval, kept separate from what it approves |
| Audit–Intent–Verification Reconciliation | — | `42586d71…35083849` | The governing measured baseline |
| Controlled Verification Result ZIP | `2026-09-06T075930Z` | `35ab3993…5c92ac4fe5e` | The 1,000-test baseline the gates measure against |
| Baseline Correction Addendum | `COR-20260906-001` | `dc2d045d…9fa1653cb8` | Corrects **only** the two ignored-state dependency statements |

⭐ **The approval record is deliberately a separate artefact from the reconciliation it approves.**
Approving a baseline does not silently promote every proposal nested inside it — terminology
(`Project Context Graph`, `Delivery Mesh`), the PM-integration contract, the release-one acceptance
mission and the final object schemas all remain *candidates requiring explicit review*.

## The sequence

| Gate | Scope | Status |
|---|---|---|
| `GATE_0_5_BOOTSTRAP_GOVERNANCE_REPOSITORY` | Create a clean bootstrap governance/spec repo; writes only there | **PASS** 2026-09-06 — 23 files at `repos/cell-os-project-intelligence-governance`, on `main`, no remote, 0 commits. Result `…Gate_0_5_Bootstrap_Result_2026-09-06T104140Z.zip` (`852d2e6d…`) |
| `GATE_1_CONTROLLED_ENVIRONMENT_PARITY_DIAGNOSTIC` | Measure the 21 baseline failures read-only; may run in parallel with 0.5 | **COMPLETE / PARTIAL_CONFIRMATION** 2026-09-06 — 18 of 19 environment hypotheses closed. Result `…Gate_1_…_2026-09-06T130324Z.zip` (`aa41d212…74be89d8`) |
| `GATE_2_PROJECT_INTELLIGENCE_CONTRACT_SPECIFICATION` | Candidate release-one contracts, inside the bootstrap repo | **Reconciliation in progress** 2026-09-08 — `CELL-G2-RECON-WO-v2`, RUN_ID `20260908T060128Z`. Checkpoints 00A–00F; A1–A9 approved as directions. See below |

Method for gate-1-shaped work: [[controlled-readonly-diagnostic]].

## What the gates measured

The 21 failures at audited commit `3c876fd` partition as **17 sibling-repository-coupled + 2
gitignored-state-coupled + 2 committed-repository (F101)**. Gate 1 confirmed the environmental
19 as far as authority allowed:

- 17 connector-coupled failures → **all pass** with only a sibling `prefect-connectors` checkout
  at `0195e59c…` present.
- 1 task-store-dependent failure → **passes** with only the screened `.data/tasks.jsonl` present.
- 1 mission-manifest-dependent failure → **`BLOCKED_NOT_MEASURED`**.

⭐ **So only 2 of 21 are real code findings.** The rest were a missing sibling checkout and a
missing gitignored file — which is exactly why the environment had to be reproduced rather than
reasoned about.

## Authority is the load-bearing part

Each prompt enumerates prohibitions as explicitly as permissions. Gate 1's boundary forbade
fixing F101, running either full suite, executing anything from a source tree, installing
dependencies, network access, choosing a runtime topology, and touching any `.data` file other
than the single named one. *"If a useful change appears obvious, record it only as a future
candidate. Do not make it."*

⭐ **The correction addendum shows why a narrow boundary is not pedantry.** `COR-20260906-001`
established that the two gitignored-state failures depend on **two different** files — the earlier
reconciliation had described both as `tasks.jsonl` — and then explicitly declined to grant access
to the second. The correct response was to test one, leave the other `NOT_MEASURED`, and report
the exact file and permission needed (`SCREENED_MISSION_MANIFEST_FIXTURE` over
`.data/missions/marketing-model-reconstruction-v1.json`). Widening the boundary inside the session
would have produced a better-looking number and a worthless gate.

## Gotchas for the next gate

- ⛔ **The documented pack path is wrong.** `START_HERE.md` and `REQUIRED_INPUTS.md` both name
  `repos\_cellos_handoffs\CELL_OS_Next_Gates_Handoff_v1\`, **which does not exist**. The pack is
  double-nested at `repos\CELL_OS_Next_Gates_Handoff_v1\CELL_OS_Next_Gates_Handoff_v1\`. Resolve
  the root from the prompt's *actual* location and record the deviation.
- ⚠ **Gate 0.5 was bitten by this machine's system-level `core.autocrlf` and LFS filters** — any
  gate that commits must override locally in the target repo, never globally.
- Each gate's ZIP, `.zip.sha256` sidecar and full receipt go back to **ChatGPT unchanged**, and no
  follow-on work starts in the same session.
- `ASSIGNMENT_STATUS` and the result verdict are **two separate fields**. `COMPLETE` means the
  authorized procedure finished; it does not mean everything passed.

## Gate 2 reconciliation run `20260908T060128Z`

Work order `CELL-G2-RECON-WO-v2`. External run root `repos/_cellos_reconciliation_runs/20260908T060128Z/`;
candidate output confined to `specifications/release-one/reconciliation/20260908T060128Z/`. **Not a Jira
ticket — this workstream has no ticket key; the work-order ID is the identifier.**

⭐ **Three of my own published conclusions were wrong, and each was caught by a *different* control.**
That is the reusable lesson, not the specific errors:

| Wrong claim | Caught by | Truth |
|---|---|---|
| Provider stdout byte-exactly preserved (`32023d67…`) | Re-measuring the file | 1762 bytes on disk, 1761 hashed — text-mode read normalized CRLF→LF, `write_text` re-expanded. The digest matched **neither** the provider bytes nor the file |
| Seven fixture→schema bindings "undeclared" | Reading `fixture-bundle` | All 15 declared by `$ref`, `additionalProperties: false`. I never opened the schema whose job is to declare them, then offered the gap as a founder decision |
| "Five schemas accept arbitrary JSON" | Enumerating root keywords | Filter tested only `required`+`additionalProperties`, missing root `oneOf` and root `type`. Only 2 are definition libraries — by design |

⛔ **A parse test whose control also passes is not a test.** Checking `--max-turns` support via
`claude --max-turns 1 --version` returned exit 0 — and so did `--definitely-not-a-flag --version`,
because `--version` short-circuits before argument validation. The discriminating instrument was a
string search of the compiled binary. The flag is real, just hidden from `--help`.

⛔ **RFC 8785 orders object members by UTF-16 code unit, not Unicode code point.** Python's `sorted()`
on `str` keys is code-point order. With keys `U+E000` and `U+10000` the orders invert (the
supplementary-plane key encodes as a surrogate pair starting `0xD800`, numerically below `0xE000`) and
the digests differ. Any "canonical JSON" implementation written in Python is non-conformant until this
is fixed — and reproducing a corpus's own hashes proves consistency with *that corpus's algorithm*,
never interoperability.

⚠ **An over-broad check fails valid positives, and that is a defect, not a finding.** A freshness check
that fired on every `UNKNOWN_FRESHNESS` record failed three positive fixtures. The contract said
"blocks wherever current applicability is **mandatory**" — the qualifier was load-bearing, and the
requirement has to be *declared*, never inferred.

**The gating blocker for acceptance:** the Prompt-and-Run-Traceability Mission needs a
`prompt_object_id` + `prompt_content_hash` pair, and **no Prompt Registry exists**. All supplied
historical evidence contains exactly one run record (`paused: true`) with none of the mandatory
linkage fields — `NOT_RECORDED`, corroborated by three independent instruments. No run, however well
instrumented, can populate that link until the registry exists.

Method note: `agent-factory`'s `HeadlessProvider` hardcodes `--dangerously-skip-permissions`, so it is
unavailable for unattended use. A run-local provider adapter injected at `RunController(provider=…)`
proved the task→invocation→ledger chain end-to-end without modifying the repo — but avoiding the
unsafe path is not remediating it.

## See Also

- [[agent-factory]] — the subject under measurement, and the per-gate session records
- [[controlled-readonly-diagnostic]] — the reusable battery Gate 1 established
- [[vacuous-verification]] — why "the check ran" and "the check measured something" are different
