# ALDC Agentic Coding Guidelines

### Draft v0.2 — March 2026

  

*How we use CCE (Claude Code Enhanced) to produce high-quality code and systems.*

  

---

  

## 1. Philosophy

  

We are a small team building production systems with an AI coding agent as a core team member. That gives us leverage far beyond our headcount — but only if we use it with discipline.

  

**Our position on the spectrum:**

- We are not vibe coding. Every line we ship, we can explain.

- We are not writing specs in EARS notation before every change.

- We practice **plan-then-execute with verification** — the sweet spot for a team our size.

  

**Three principles:**

1. **The agent is only as good as the system around it.** CCE's hooks, auto-learn, status line, and team messaging exist because raw Claude Code isn't enough. The infrastructure compounds.

2. **Verification over trust.** If the agent can't prove it works (tests, syntax checks, runtime confirmation), it doesn't ship.

3. **Context is the constraint, not capability.** Managing what the agent knows — through subagents, focused sessions, and persistent state — is the highest-leverage skill.

  

### The Numbers Behind the Discipline

  

These are not opinions — they're measurements from production deployments and research studies:

  

- **~33% first-attempt success rate**: Claude Code succeeds on its first autonomous attempt about one-third of the time (Anthropic's own RL Engineering team). Verification isn't optional.

- **2.74x security vulnerability rate**: In a December 2025 analysis of 470 GitHub PRs, AI-co-authored code had 2.74x more security vulnerabilities than human-written code.

- **50% token savings in healthy code**: Codebases with high code health scores use half the tokens for equivalent tasks. Clean code makes the agent more effective, not just more readable.

- **40% context utilization threshold**: Output quality starts degrading at 40% context window usage — not when the window is full. By the time you feel the context is "getting long," quality has already declined.

- **90% improvement with multi-agent**: Anthropic's orchestrator-worker pattern (large model coordinating smaller model workers) outperformed a single large model by 90.2% on research tasks.

- **80% fewer false starts**: Teams that write a plan/spec before implementation eliminate 80% of "the agent got confused halfway through" incidents.

  

---

  

## 2. The CCE Development Lifecycle

  

Every coding session follows this rhythm:

  

### Phase 1: Orient (first 30 seconds)

- CCE auto-updates hooks and skills from Zeus on session start

- Status line shows: task count, pending items, daily learnings, who's online

- **Check your inbox.** If there are messages from the team, read them first — they may change your priorities

- Review the task board if working on tracked work

  

### Phase 2: Plan (before writing code)

- **Use Plan Mode** (`Ctrl+G` or `/plan`) for anything non-trivial

- Let Claude explore the codebase read-only, then propose an approach

- Review the plan. Push back. Refine. *This is where you prevent 80% of wasted work.*

- For large changes, break the plan into discrete tasks

- **Anchor the problem, not just the tasks.** Write the core problem and your original intent into the first task or a progress note — not just the implementation steps. When a session runs long and context compresses, task lists survive but motivation doesn't. Before declaring any multi-step work complete, re-read the anchor and ask: "did I solve the actual problem, or did I just complete the tasks I could still see?"

  

### Phase 3: Implement

- Switch to Normal Mode and execute the plan

- Let Claude work in focused bursts — one concern at a time

- If it goes off-track after two corrections, **start a new session** with a better prompt. Persist your findings to a file or commit first — then begin fresh. Don't accumulate confusion in context.

  

### Model Tier Routing

  

Not every task needs the same model. Using the right model for the right job saves time and improves quality:

  

| Task Type | Recommended Tier | Why |

|---|---|---|

| File search, grepping, code reading | Haiku (fast/cheap) | Speed matters more than depth |

| Standard implementation, refactoring | Sonnet (balanced) | Good reasoning at reasonable cost |

| Architecture decisions, security review, complex debugging | Opus (deep) | These need maximum reasoning |

| Parallel sub-investigations | Sonnet or Haiku workers | Fresh context per worker, results synthesized by main session |

  

**The orchestrator pattern:** For complex tasks, use a high-capability model as the "brain" that plans and synthesizes, with smaller models as "arms" that search, read, and gather data in parallel. Each worker gets a focused task and a fresh context window — no context rot from the main session leaking in.

  

When launching sub-agents for investigation:

- Give each agent one precise question, specific starting files, and an expected output format

- Run independent investigations in parallel, not sequentially

- The orchestrator synthesizes findings — don't relay agent results verbatim

  

### Phase 4: Verify

- **Every change must be verified before commit.** Options:

  - Run tests (`pytest`, `npm test`, etc.)

  - Syntax check (`python3 -c "import ast; ast.parse(open('file').read())"` when pytest isn't available locally)

  - Start a local server and confirm behavior

  - Use a second Claude session as reviewer (Writer/Reviewer pattern)

- The tool_usage_logger tracks what happened — auto-learn captures it at session end

  

### Phase 5: Commit & Communicate

- Write clear commit messages (imperative mood, explain *why*)

- If the change affects others, send a message via CCE (`/msg`)

- Push when ready — CI/CD handles the rest

  

---

  

## 3. Context Management

  

**This is the single most important skill for working with CCE.**

  

### The Rules

  

| Rule | Why |

|------|-----|

| **One concern per session** | Context pollution causes compounding errors. A focused session is cheap. |

| **Use subagents for exploration** | They run in isolated context and report back summaries. Your main context stays clean. |

| **Keep CLAUDE.md lean** | If Claude can figure it out by reading the code, don't put it in CLAUDE.md. Every line has a cost. |

| **After two failed corrections, start a new session** | You're fighting accumulated context, not the problem. Commit or persist findings, then start fresh with a better prompt. |

| **Don't mix research and implementation** | Use subagents for research, or a separate session. Keep implementation context clean from exploration noise. |

  

### Why Context Hygiene Matters: Context Rot

  

Context rot is not a metaphor — it's a measurable phenomenon. As tokens accumulate, the model's attention spreads thinner across all token relationships. The practical effects:

  

- Instructions from early in the session (including CLAUDE.md rules) lose influence

- The model starts "forgetting" project conventions while still generating syntactically correct code

- Failed approaches accumulate as noise, biasing the model toward repeating similar failures

- Even with a 1M-token window, quality degrades well before the limit

  

**The threshold is lower than you think.** Don't wait until the context feels full. Quality starts degrading around 40% utilization. If Claude is generating code that ignores conventions it followed earlier in the session — that's context rot, not a bug. Wrap up, commit, and start a new session.

  

### The Compaction Trap

  

When the context window fills, Claude compresses earlier parts of the conversation to make room. **CLAUDE.md rules are loaded at session start — they're the first thing compressed away.**

  

After compaction, Claude continues working but stops following project conventions. The code still runs, but it violates patterns, ignores gotchas, and introduces inconsistencies. You won't notice until review.

  

**Defenses:**

- Keep sessions short enough to avoid compaction (the best defense)

- If you notice convention drift, wrap up and start a new session — compaction has already degraded quality

- Critical rules that must survive compaction belong in **hooks**, not just CLAUDE.md — hooks fire deterministically regardless of context state

- CCE's PostToolUse hooks and auto-learn help, but they don't replace the conventions lost from CLAUDE.md during compaction

  

### What Goes in CLAUDE.md

  

**Include:**

- Commands Claude can't guess (custom build scripts, test runners, deploy commands)

- Style rules that differ from defaults (e.g., "no semicolons in JS", "snake_case for API routes")

- Known gotchas that cause repeated mistakes (e.g., "asyncpg needs datetime objects, not strings")

- Testing instructions specific to the project

- Auth/env patterns ("use `X-API-Key` header, not Bearer")

  

**Exclude:**

- Anything derivable from reading the code

- Standard language conventions

- Long architectural explanations (link to docs instead)

- Comments like "IMPORTANT" everywhere — use emphasis sparingly or it loses effect

  

### What Goes in Memory (not CLAUDE.md)

  

CCE's memory system (`~/.claude/projects/.../memory/`) stores cross-session knowledge:

- Team member details and preferences

- Workflow patterns ("share long research as Slack canvas")

- Confirmed gotchas from debugging sessions

- External system references (Linear projects, Grafana dashboards)

- User-specific context (role, expertise level, communication preferences)

  

**Memory is for humans. CLAUDE.md is for the agent.**

  

---

  

## 4. Verification Standards

  

### The Iron Law

  

**No completion claim is valid without fresh verification evidence.**

  

This means: the agent (or you) must run a verification command, read its output, and confirm the output matches the claimed result. "It should work" is not verification. "The tests passed" without showing test output is not verification. A green checkmark from a previous run is not verification.

  

Every verification must be:

- **Fresh** — run after the final change, not before it

- **Read** — output actually examined, not just "it ran without errors"

- **Matched** — output confirms the specific claim being made

  

This applies to all three tiers below. The tiers determine *how* to verify. The Iron Law determines *that* you must verify.

  

### Tier 1: Must-Verify (production code)

- Run the test suite. If tests don't exist for the changed code, write them first.

- For backend changes: confirm the API endpoint works through the full proxy chain (not just direct API — see Eclipse gotcha about Next.js proxy)

- For frontend changes: visual confirmation via local server or screenshot

- For database changes: verify migrations run cleanly, confirm RLS policies apply

  

### Tier 2: Syntax-Verify (when full tests aren't available)

- Python: `python3 -c "import ast; ast.parse(open('file.py').read())"`

- JavaScript/TypeScript: `node -c file.js` or `npx tsc --noEmit`

- Bash: `bash -n script.sh`

- SQL: dry-run against a test database

  

### Tier 3: Peer-Verify (complex or risky changes)

- **Writer/Reviewer pattern:** Implement in one CCE session, then open a fresh session to review

- The reviewer has no confirmation bias from the implementation context

- Especially important for: auth changes, data model changes, deployment config, anything touching money

  

### Instructions vs. Enforcement

  

CLAUDE.md is **advisory**. Hooks are **law**.

  

| Mechanism | Behavior | Survives Compaction | Reliability |

|---|---|---|---|

| CLAUDE.md | Guides agent behavior through instructions | No — first thing lost | High early in session, degrades |

| Memory | Provides cross-session context | N/A — loaded per session | Moderate — depends on relevance matching |

| Hooks | Fires deterministically on lifecycle events | Yes — independent of context | 100% — code execution, not model compliance |

  

**Rule of thumb:** If a rule must apply with zero exceptions (security review on auth files, syntax validation before commit, backup before destructive operations), put it in a hook. If a rule guides style and approach (prefer small functions, use snake_case), CLAUDE.md is fine.

  

Don't duplicate between CLAUDE.md and hooks. If it's in a hook, remove it from CLAUDE.md — every CLAUDE.md line competes for attention, and redundant lines waste that budget.

  

### What "Verified" Means for CCE Hooks

All hooks auto-updated from Zeus go through:

1. HMAC-SHA256 signature verification

2. SHA256 file integrity check

3. Syntax validation (`bash -n`, `py -m py_compile`)

4. Backup of previous version to `_previous/`

  

This is the standard. If we verify our infrastructure code, we verify our application code.

  

---

  

## 5. Session Hygiene

  

### Starting a Session

1. Check the status line — inbox, pending tasks, who's online

2. If picking up previous work, read relevant memory/CLAUDE.md — don't assume context carries over

3. State your goal clearly in the first prompt. Be specific about scope.

  

### Multi-Session Continuity

  

For work spanning more than one session:

  

1. **At session end**: Write a brief progress note — what was completed, what's next, what's blocked. Store it where the next session will find it (Zeus task, CLAUDE.md comment, or a `progress.md` in the working directory).

2. **At next session start**: Read the progress note before doing anything. State the goal with context: "Continuing feature X. Completed: A, B. Next: C, D. Blocked on: E."

3. **Use git history as ground truth**: `git log --oneline -20` tells the next session exactly what was done. Commit frequently with clear messages — they're the agent's breadcrumbs.

  

Auto-learn captures session metadata to Zeus. Progress notes capture **intent and state** — what the agent was thinking, not just what it did. Both are needed.

  

### During a Session

- **One concern per session.** Fixing a bug, adding a feature, or doing research — not all three.

- Watch the context window. Quality degrades at 40% utilization — don't wait until it feels full.

- Use subagents (`Agent` tool) for side investigations — they don't pollute your context

- Let the tool_usage_logger and auto-learn do their job — they capture what you did for future sessions

  

### Ending a Session

- CCE auto-learns on session end (captures tools used, files modified, duration)

- The poller shuts down cleanly

- Stale cache files are cleaned up

- **Don't kill sessions abruptly** — let SessionEnd hooks run

  

### The 50-Tool Checkpoint

The tool_usage_logger triggers a learning checkpoint every 50 tool calls. When you see it:

- Consider if this is a natural break point

- If the session is getting long, commit your work and start a new session

- Long sessions degrade quality — the research is clear on this

  

---

  

## 6. Team Collaboration via CCE

  

### Presence

- CCE broadcasts a heartbeat every 30 seconds — your team knows you're online

- The status line shows who's active: `| JK Lori Mike`

- This enables async coordination without Slack noise

  

### Messaging

- Use `/msg` to send messages to team members through CCE

- Messages are surfaced during work (PostToolUse hook, 5s cooldown)

- Urgent messages bypass the cooldown

- The Stop hook blocks if you have unread messages — read them before moving on

  

### Learnings

- Every session's work is auto-captured to Zeus Memory

- The status line shows daily learning records (DR/TDR) — personal and team

- These learnings feed into future session context

- **The virtuous cycle:** Work → Learn → Remember → Better work

  

### Task Coordination

- Zeus tasks appear in the status line (assigned to you | delegated to others)

- Use task deep links to jump into specific work: `/internal/tasks?taskId=<uuid>`

- Update task status as you work — the team sees progress in real time

  

---

  

## 7. Code Quality Standards

  

### Code Health as Agent Prerequisite

  

AI agents amplify what's already there. In clean code, they produce clean code. In messy code, they produce worse mess.

  

Before delegating complex work to CCE:

- Is the target module well-structured? If not, clean it up first (CCE can help, under close review)

- Are there existing tests? If not, write them first — they serve as both verification and specification

- Is the code well-commented where logic is non-obvious? If not, add context — the agent reads comments

  

This isn't perfectionism. Messy code makes the agent generate lower-quality output AND use more tokens doing it. A 30-minute cleanup before delegation saves hours of fixing agent-generated problems after.

  

### What CCE Must Always Do

1. **Run existing tests** before considering a change complete

2. **Not introduce security vulnerabilities** — OWASP Top 10 awareness is baseline

3. **Not over-engineer** — solve the problem asked, not the problem imagined

4. **Preserve existing patterns** — match the codebase's style, don't introduce new abstractions unnecessarily

5. **Handle the proxy chain** — for Eclipse, test through NextAuth login flow, not just direct API

6. **Check git history before changing existing code.** Run `git blame` or `git log` on the lines being modified. Code that looks wrong is more likely a deliberate fix you don't understand yet. The burden of proof is on the proposed change, not on the existing code. Never accept a "fix" from CCE that reverts a previous fix — if git history shows the current code was introduced to solve a specific problem, that problem still exists.

7. **Scan for bug patterns after finding one.** When a bug is found, check for the same pattern in the rest of the file, the module, and related modules. Bugs cluster — the same mistake that caused one failure is likely repeated nearby. Fix the pattern, not just the instance.

  

### What We Expect From Each Other

- **Review AI-generated code like you wrote it.** You're responsible for what ships.

- **If you can't explain what it does, don't commit it.** Simon Willison's golden rule.

- **Flag when something feels wrong.** CCE produces plausible code that misses edge cases. Trust your instincts.

- **Share learnings.** If you discover a gotcha, add it to CLAUDE.md or memory. Future sessions benefit.

  

### Cognitive Debt

  

Technical debt is code you know is bad. **Cognitive debt is code you don't understand.**

  

AI agents produce functional code faster than any human. The danger: your codebase accumulates logic that nobody on the team can explain, debug, or safely modify. This is worse than technical debt because you can't see it — you only discover it when something breaks at 2am and the fix requires understanding code that was never understood in the first place.

  

**How to avoid it:**

- When CCE generates a non-trivial implementation, read it before committing. Not skim — read.

- If a function would take longer to understand than to rewrite, rewrite it yourself.

- When reviewing AI-generated code, ask: "could I debug this at 2am without the AI?"

- If the answer is no, simplify it until the answer is yes.

  

The speed advantage of AI coding is real. But speed without comprehension is a loan with compounding interest.

  

### Common CCE Failure Modes (and how we guard against them)

  

| Failure Mode | Guard |

|---|---|

| Plausible but wrong edge case handling | Verification Tier 1-3 above |

| Context degradation in long sessions | 50-tool checkpoint, focused sessions, subagents for exploration, 40% threshold awareness |

| Repeating known mistakes | CLAUDE.md gotchas section, auto-learn |

| Security vulnerabilities (unauthenticated endpoints, injection) | Code review, Writer/Reviewer pattern |

| Over-engineering / scope creep | Plan Mode first, explicit scope in prompts |

| Hallucinated APIs or library methods | Always verify against actual docs or runtime |

| Reverting a previous fix as "cleanup" | `git blame` before accepting changes to existing code |

| Fix-break-fix loop (same file edited 5+ times) | If a file is edited 5+ times in one session, stop. Persist findings, start a new session, rethink the approach. The agent is thrashing, not converging. |

| Declaring "done" without verification | Iron Law — no claim without fresh evidence from a verification command |

| Post-compaction convention drift | Keep sessions short, use hooks for critical rules, watch for style inconsistencies |

  

---

  

## 8. Project-Specific Patterns

  

### Eclipse Exp (FastAPI + Next.js)

- **Python 3.12 required** — WSL has 3.10, so use syntax checks locally, full tests via CI

- **Test the proxy, not just the API** — the Next.js proxy layer has its own failure modes

- **asyncpg needs datetime objects** — SQL casts don't help, parse strings to datetime first

- **`_record_to_dict` strips NULLs** — Pydantic defaults apply, plan accordingly

- **Remote is always ahead** — `git pull --rebase origin main` before push

  

### Zeus Memory (FastAPI + asyncpg)

- **Text search: ALWAYS `search_vector @@ to_tsquery()`** — never ILIKE on 3.5M rows

- **Auth: `X-API-Key` header** — not Bearer

- **Dockerfile COPY list is explicit** — new `.py` files MUST be added or routes 404 silently

- **22 route modules** — add new routes as new files in `api/routes/`, register in `main.py`

  

### Eclipse Landing (Static HTML)

- **Branch: main** (Vercel auto-deploys)

- **No framework** — vanilla HTML/CSS/JS, inline styles

- **Update llms.txt + llms-full.txt** when changing any site content

- **GitHub token lacks org API access** — merge locally, push directly

  

---

  

## 9. When NOT to Use CCE Autonomously

  

CCE is powerful, but some actions require human judgment:

  

- **Destructive git operations** — force push, reset hard, branch deletion

- **Database migrations on production** — always review the SQL manually

- **Auth/security changes** — Writer/Reviewer pattern mandatory

- **External communications** — Slack messages, PR comments, emails to clients

- **Infrastructure changes** — CI/CD pipelines, container configs, DNS

- **Spending money** — API keys with billing, cloud resource provisioning

  

For these, CCE can *draft* but a human must *execute*.

  

---

  

## 10. Continuous Improvement

  

### How We Get Better

1. **Auto-learn captures every session** — tool usage, files modified, duration

2. **The learnings cache tracks daily records** — personal and team motivation

3. **CLAUDE.md evolves** — when you hit a gotcha twice, add it

4. **Memory persists patterns** — workflow insights, team preferences, debugging solutions

5. **Hooks auto-update from Zeus** — improvements deploy to the whole team automatically

  

### What to Add to These Guidelines

This is a living document. When you discover:

- A new verification technique that catches bugs → add to Section 4

- A context management trick that saves time → add to Section 3

- A project-specific gotcha → add to Section 8

- A failure mode we haven't documented → add to Section 7

  

### Measuring Success

- **Learnings per day (DR)** — visible on the status line, tracks session productivity

- **Time to first working version** — plan mode should reduce false starts

- **Bugs caught before production** — verification tiers should catch them earlier

- **Team communication flow** — inbox + presence should reduce Slack context switching

  

---

  

## Appendix A: Quick Reference

  

```

Start session    → Check status line, read inbox, state goal clearly

Plan             → Ctrl+G (Plan Mode) for anything non-trivial

Anchor           → Write the core problem into your first task — it survives compaction

Implement        → One concern at a time, focused bursts

Verify           → Iron Law: fresh evidence from a verification command, or it's not done

Context at 40%?  → Quality is already degrading. Commit and start a new session.

Two corrections failed? → Persist findings, start a new session with a better prompt

Research task?   → Use subagents, keep main context clean

Multi-session?   → Progress note at end, read it at start, git log as ground truth

Team message?    → /msg <user> <message>

Session ending?  → Let SessionEnd hooks run (don't kill -9)

Found a gotcha?  → Add to CLAUDE.md or memory

Bug found?       → Fix it, then scan for the same pattern elsewhere

```

  

## Appendix B: CCE Architecture At a Glance

  

```

SessionStart ──→ hooks-updater (Zeus) + poller launch

     │

UserPromptSubmit ──→ inbox-check (authoritative API call)

     │

PostToolUse ──→ posttool-check (surface messages) + tool_usage_logger

     │

Stop ──→ stop-check (block if unsurfaced messages)

     │

SessionEnd ──→ kill poller + auto-learn → Zeus Memory + cleanup

  

Status Line (continuous):

  CCE v## | # Task | # Pending | #/# DR | #/# TDR | Online Users

```

  

---

  

*These guidelines are maintained by the ALDC development team. Last updated: March 24, 2026.*