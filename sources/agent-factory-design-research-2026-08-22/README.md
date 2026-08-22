# Agent Factory design research — raw pass reports, 2026-08-22

**Immutable.** Five research passes run against `ALDC-io/agent-factory` @ `feat/readiness-generator`
on 2026-08-22, and the shared brief they were all given. Synthesised into
[[agent-factory-spec]], [[agent-factory-isolation-ladder]] and [[agent-factory-certification]].

| File | Brief |
|---|---|
| `CONTEXT.md` | the shared brief — measured state, prior conclusions, the mandatory evidence tiering |
| `RA-data-sandbox.md` | Is the T2 ephemeral data sandbox real, cheap and safe? |
| `RB-credential-boundary.md` | How is a capability tier enforced when the agent needs real credentials? |
| `RC-attestation-and-versioning.md` | What must "certified" mean, and what is an agent as a versioned artefact? |
| `RD-session-orchestration.md` | What should run the sessions? Is worktree-on-one-machine a dead end? |
| `RE-data-oracle.md` | What is the oracle for data work, and what makes a corpus adequate? |

They are kept because the spec quotes their conclusions and **not** their evidence trails. When
§18.3 says "re-verify before staking a decision on this", these files hold the source URLs, the
tier each claim was given, and each pass's own account of what it could not settle.

⚠ **Every pass ran behind a domain-allowlisting egress proxy that blocked most vendor
documentation.** Claims tiered `DOCUMENTED*` were reached through a search index and never read in
context; roughly a third of the vendor claims are one tier weaker than they look, and one pair —
whether Snowflake object tagging needs Enterprise Edition — came back **self-contradictory**. Each
report states its own blocked-host list up front.
