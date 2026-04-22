---
tags: [entity, repo, cce, claude-code-enhanced, zeus-memory, skills, hooks, agentic-coding]
aliases: [CCE repo, claude_code_enhanced, claude-code-enhanced, Claude Code Enhanced repo]
sources:
  - repos/claude_code_enhanced/README.md
  - repos/claude_code_enhanced/CLAUDE.md
  - repos/claude_code_enhanced/SKILLS_INDEX.md
  - repos/claude_code_enhanced/EXTERNAL_SKILLS.md
  - repos/claude_code_enhanced/cce
  - repos/claude_code_enhanced/scripts/install.sh
  - repos/claude_code_enhanced/tools/cce_cli.py
  - repos/claude_code_enhanced/tools/cce_setup.sh
  - repos/claude_code_enhanced/tools/zeus_integration.py
  - repos/claude_code_enhanced/hooks/*.sh
  - repos/claude_code_enhanced/hooks/*.py
  - repos/claude_code_enhanced/docs/architecture/CCE_ARCHITECTURE.mermaid
  - repos/claude_code_enhanced/docs/decision-agent-accountability.md
  - repos/claude_code_enhanced/.github/workflows/claude.yml
  - repos/claude_code_enhanced/.env.example
  - repos/claude_code_enhanced/.mcp.json
created: 2026-04-20
updated: 2026-04-20
---

# claude_code_enhanced (repo)

> **Disambiguation.** Four overlapping names refer to different things:
> - **`claude_code_enhanced`** — the GitHub repo (this page). What's in the codebase, how to install it, how to extend it.
> - **CCE / "Claude Code Enhanced"** — the product / project. Vision, goals, principles, current-state assessment. See [[cce]] (project page).
> - **`cce`** — the global CLI command, symlinked to `/usr/local/bin/cce` by `install.sh`. This is what you type.
> - **[[zeus-memory]]** — the backend API and Postgres store that CCE depends on for persistence. A separate repo.
>
> This page is the **engineering companion** to [[cce]]. It covers the codebase: launcher phases, hook wiring, data flows, CLI commands, dev setup. For product vision and open questions, read [[cce]].

CCE is ALDC's opinionated wrapper around Claude Code. This repo ships the `cce` launcher, an auto-syncing hook system that enforces team conventions at session boundaries, a 195-skill library under `.claude/skills/`, a set of Python orchestration tools (multi-agent, workflow executor, context compactor, recovery manager), and an AI-first project-template CLI. It is installed per-developer via `git clone` + `install.sh`; there is no server-side deploy. The backend — Zeus Memory — lives in a separate repo ([[zeus-memory]]).

---

## Tech Stack

| Layer | Detail |
|---|---|
| Primary languages | **Bash** (launcher, hooks, setup, install, deploy scripts) + **Python 3** (hooks, tools, tests) |
| Package manifest | **None.** No `pyproject.toml`, no `package.json`, no `requirements.txt` at repo root. Python tools rely on stdlib + installed packages (`requests`, `httpx`, `pytest`). New-developer setup is manual (see § Developer Guide). |
| Distribution | `cce` (Bash launcher, ~600 lines), `scripts/install.sh` (one-command install), `tools/cce_setup.sh` (per-machine credential + config setup) |
| Integration protocols | HTTPS to Zeus Memory API (`https://zeus.aldc.io`), MCP (`https://zeus.aldc.io/mcp` — declared in `.mcp.json`), Unix domain socket for messaging broker (`/run/user/$UID/cce/broker.sock`), local file cache (`~/.cache/cce/`) |
| Platform support | macOS, Linux, Windows (Git Bash). Windows compatibility is a first-class concern — several hooks probe `python3`/`python`/`py` in order because `command -v` returns alias text in non-interactive Git Bash contexts. |

---

## Repo Layout

| Path | Purpose |
|---|---|
| `cce` | Main Bash launcher. 8-phase startup sequence; routes all `cce <subcommand>` calls. |
| `scripts/install.sh` | One-command installer (curl-pipeable). Clones repo, symlinks `cce` to `/usr/local/bin`, runs readiness check. |
| `tools/` | Python tooling (~33 files). See detailed table below. |
| `hooks/` | 20 hook scripts (see § Hook System). Runtime enforcement layer — mix of `.sh` and `.py`. |
| `.claude/skills/` | 195 skill `.md` files across 49 categories (see `SKILLS_INDEX.md`). |
| `.claude/commands/` | Claude Code slash-command definitions. ~25 commands including `msg/`, `session-exit/`, `cce-optimize/`, `repo-learn/`, `zeus-health/`, `discover-skills/`, `weekly-brief.md`, `util.md`. |
| `.claude/settings.local.json` | Per-machine permissions (gitignored; generated on first launch). |
| `commands/msg/` | **Separate from `.claude/commands/`** — top-level `commands/` folder with one entry (`msg/`). Legacy path; relationship to `.claude/commands/msg/` is unclear (see § Tech Debt). |
| `projects/` | AI-first project instances created by `cce init`. Template at `projects/CLAUDE_CODE_PROJECT_TEMPLATE.md`; sub-directories are dated project folders; `completed/` holds archived work. |
| `tests/` | Python pytest suites: `test_phase1.py`, `test_phase2_{compactor,parallel,recovery,workflow}.py`, `test_phase2_5_skills.py`, `test_hallucination_reduction.py`. Locally runnable only — **no CI test job**. |
| `docs/` | Repo-local architecture docs. `architecture/CCE_ARCHITECTURE.mermaid` is the canonical system diagram; also `decision-agent-accountability.md`, `ENVIRONMENT_BEST_PRACTICES.md`, `QA_ENV_CONFIGURATION_2026-01-26.md`. |
| `integrations/` | Integration notes (`tsheets-data.md`). |
| `_archive/` | Historical reports/research. |
| `contract-*.md`, `connector-scaffold.md`, `generate-connector.md` | Top-level command definitions (contract-diff, contract-generate, contract-validate, generate-connector). |
| `SKILLS_INDEX.md` | Auto-generated human-readable table of all 195 skills. |
| `SKILL_TEMPLATE.md` | Template for creating new skills. |
| `skills_index.json` | Machine-readable skill catalog (~42 KB). |
| `EXTERNAL_SKILLS.md` | List of third-party skill repos (Anthropic official, VoltAgent awesome-agent-skills, travisvn awesome-claude-skills, alirezarezvani claude-skills, wshobson commands). |
| `CLAUDE.md` | "First Principles" + context-recovery instructions loaded into every session. |
| `.mcp.json` | Zeus Memory MCP server config (HTTP transport, bearer token from `$ZEUS_API_KEY`). |
| `.env.example` | Env-var template covering GitHub, Anthropic, Gemini, Voyage, Zeus API + DB, Azure, Slack, Nextcloud, Miro. All placeholder values — no hard-coded credentials. |
| `.github/workflows/claude.yml` | Only CI workflow. Triggers `anthropics/claude-code-action@v1` when `@claude` is mentioned in an issue, issue comment, or PR review comment. **Not a build or test pipeline.** |

### `tools/` — Key Python files

| File | Purpose |
|---|---|
| `cce_cli.py` (~33 KB) | Project-template CLI: `init`, `update`, `status`, `list`, `validate`, `archive`, `search`, `decompose`, `troubleshoot` subcommands |
| `cce_setup.sh` | 7-step interactive machine setup wizard (see § Developer Guide) |
| `zeus_integration.py` | HTTP API client for Zeus Memory (stdlib-ish, sanitised-error logging, JSON validation) |
| `multi_agent_orchestrator.py` (~47 KB) | Multi-agent task coordination |
| `workflow_executor.py` | Step-by-step workflow runner with checkpointing |
| `context_compactor.py` | Summarise + compress session context |
| `recovery_manager.py` | Session recovery after errors/interruptions |
| `parallel_executor.py` | Concurrent task runner |
| `model_router.py` | Route tasks to appropriate model (Opus/Sonnet/Haiku) |
| `skill_discovery.py` | Surface candidate skills from session patterns |
| `skill_generator.py` | Auto-generate skill files from templates |
| `context7_handler.py` (~30 KB) | Token-aware cache + ranker for Context7 MCP (hallucination reduction) |
| `troubleshooter.py` | Full diagnostic suite (`cce troubleshoot`) |
| `production_builder.py` | Production build toolchain |
| `git_integration.py` | `GitWorkflowManager`: git commit/branch wrappers (soft dep — gracefully disabled if import fails) |
| `git-askpass.sh` | Feeds `GH_TOKEN` to git for non-interactive HTTPS auth |

---

## Architecture

### Launcher (`cce`) — 8-phase startup

Every `cce` invocation (no args) runs these phases in sequence before `exec claude`:

| Phase | What happens | Skip flag |
|---|---|---|
| 1. Repo resync | `git fetch origin main && git reset --hard origin/main` (only if working tree clean). Also syncs `zeus-memory` repo. | `CCE_SKIP_UPDATE=true` |
| 2. Skill check | `session_start_skill_check.py` — reports pending skill candidates from previous sessions | `CCE_SKIP_SKILL_CHECK=true` |
| 3. MCP config | Inject Zeus MCP server into `~/.claude/mcp.json` via `ensure_zeus_mcp_configured.py` | `CCE_SKIP_MCP_CONFIG=true` |
| 4. Messaging init | Bootstrap messaging broker + listener + task watcher via `zeus-memory/api/messaging/cce-messaging-init.sh` | `CCE_SKIP_MESSAGING=true` |
| 5. Local settings | Generate project-level `.claude/settings.local.json` if missing | (none) |
| 6. Hook sync | Copy every `hooks/*.sh`/`*.py` from repo to `~/.claude/hooks/`; patch `~/.claude/settings.json` with hook + statusLine + env config | `CCE_SKIP_HOOKS=true` |
| 7. Readiness check | `startup_readiness_check.py` — 11-check verification (credentials, GitHub, Zeus API, skills) | `CCE_SKIP_READINESS=true` |
| 8. Launch | `exec claude` — hands off to Claude Code with enhanced context | (none) |

**Key invariant:** the repo working tree is effectively read-only on dev machines. `cce` resets it to `origin/main` on every launch. Never hand-edit files inside `~/repos/claude_code_enhanced/` expecting them to survive. All customisation goes in `~/.claude/` (skills, hooks, settings) or per-project `CLAUDE.md`.

### Hook system — runtime enforcement

Hooks live in `~/.claude/hooks/` (synced from repo) and are wired into Claude Code events via `~/.claude/settings.json`. Four event bindings:

| Event | Hook(s) |
|---|---|
| `SessionStart` | `cce-session-start.sh`, `cce-hooks-updater.py`, `cce-commands-sync.sh`, `session_start_skill_check.py`, `session_start_messaging.sh`, `ensure_zeus_mcp_configured.py`, `ecosystem_review_check.py` |
| `PostToolUse` | `cce-posttool-check.sh`, `tool_usage_logger.sh` |
| `Stop` | `cce-stop-check.sh` (messages), `cce-auto-learn.sh` (spawned in background) |
| `UserPromptSubmit` | `cce-inbox-check.sh`, `message_check.sh` |
| `PreCompact` | `precompact_context_saver.sh` |
| `SessionEnd` | `session_stop_messaging.sh` |
| `statusLine` | `cce-statusline.sh` |

The status line renders: `CCE v<ver> | <n> Inbox | <n> Assigned | <daily>/<daily_target> DR | <daily>/<daily_target> TDR | <online-users>` — reading from `~/.cache/cce/{inbox-messages.json, tasks-stats, learnings-stats, presence-online.json}`.

### Background poller (`cce-poller-daemon.py`)

A separate long-lived Python process started by `cce-session-start.sh`. It:

- Polls `GET /api/presence/messages?peek=true` every **3 seconds** → writes `inbox-messages.json` + `inbox-status` to `~/.cache/cce/`
- Sends `POST /api/presence/heartbeat` every **30 seconds** → updates `presence-online.json`
- Self-terminates if its PID file disappears, if replaced by a newer poller, or after **12 h** max lifetime
- PID file: `~/.cache/cce/poller.pid`

### Auto-update trio — the "virtuous cycle"

Three mechanisms keep CCE current without manual intervention:

1. **Repo resync** — `git fetch origin main && git reset --hard origin/main` on every `cce` launch. Latest-always; no version pinning.

2. **`cce-hooks-updater.py`** — separate HMAC-verified hook distribution channel. Fetches a signed hook manifest from Zeus (`GET /api/hooks/manifest`), HMAC-SHA256 verifies against `$CCE_HOOKS_HMAC_KEY`, SHA-256 checksums each file, atomically replaces `~/.claude/hooks/*` via staging → swap, preserves previous copies in `~/.claude/hooks/_previous/`, writes 100-line log to `~/.cache/cce/hooks-update/updater.log`. Uses `$ZEUS_ALDC_API_KEY` (ALDC team key) in preference to `$ZEUS_API_KEY`. This path allows ALDC to push hook fixes without waiting for each dev to run `cce`.

3. **`cce-auto-learn.sh`** — the outbound half. On `Stop` hook, reads the per-session tool-usage JSONL, computes stats, POSTs a session summary to Zeus (`source=cce-session-auto-learn`, `tenant_id=11111111-1111-1111-1111-111111111111`). Idempotent via per-session marker file `~/.cache/cce/auto-learn-<session_id>`.

This trio embodies **First Principle #2: Virtuous Cycle** — the system self-improves on each session without requiring manual action.

### Skills library (`.claude/skills/`)

195 skills across 49 categories (authoritative figure from `SKILLS_INDEX.md` generated 2026-02-11; `README.md` says "190+", `CLAUDE.md` says "178 + 14 command skills" — both are stale). Top categories by count:

| Category | Skills |
|---|---|
| `zeus-memory/` | 33 |
| `azure/` | 14 |
| `core/` | 13 |
| `deployment/` | 12 |
| `eclipse-app/` | 10 |
| `memory-governance/` | 7 |
| `backend/` | 6 |
| `cce/` | 5 |
| `frontend/` | 5 |

Each skill is a self-contained markdown file with input params, output format, and ALDC-specific patterns. Each is addressable via `Skill(<name>)` from Claude Code. Machine-readable catalog: `skills_index.json`.

### Slash-command library (`.claude/commands/`)

Distinct from skills. Each command has a `SKILL.md` or top-level `.md` with YAML frontmatter (`name`, `description`, `model`, `allowed-tools`). Commands include:

`msg/` · `session-exit/` · `cce-optimize/` · `discover-skills/` · `repo-learn/` · `zeus-health/` · `deploy-watch/` · `cce-learn/` · `log-failed-approach/` · `register-zeus-project/` · `athena-regen/` · `journal/` · `tasks/` · `weekly-brief.md` · `util.md` · `affine.md` · `zeus-patterns/` · `zeus-master-health/` · `publish-hooks/`

### Python orchestration toolkit ("Phase 2")

The `tools/*.py` files form a secondary capability layer beyond the core runtime loop:

- **`multi_agent_orchestrator.py`** (~47 KB) — coordinates parallel Claude Code agent tasks
- **`workflow_executor.py`** — step-by-step workflow runner with checkpointing
- **`context_compactor.py`** — summarises + compresses session context before `/compact`
- **`recovery_manager.py`** — restores context after errors or interruptions
- **`parallel_executor.py`** — concurrent task execution
- **`model_router.py`** — routes tasks to appropriate model tier (Opus/Sonnet/Haiku)
- **`performance_optimizer.py`** — profiling + optimization suggestions
- **`production_builder.py`** — production build toolchain

These are invoked by skills and commands; not typically called directly.

### MCP integration

`.mcp.json` at repo root declares the `zeus-memory` MCP server:

```json
{
  "zeus-memory": {
    "type": "http",
    "url": "https://zeus.aldc.io/mcp",
    "headers": {
      "Authorization": "Bearer ${ZEUS_API_KEY}",
      "Content-Type": "application/json"
    }
  }
}
```

`ensure_zeus_mcp_configured.py` reconciles this into the user's `~/.mcp.json` at session start. HTTP transport. This is how Claude Code's `Remember` tool reaches Zeus.

### First Principles as design invariants

The 8 principles in `CLAUDE.md` are the repo's design rubric. Three have the most direct code implications — the rest belong to the [[cce]] project page:

- **#2 Virtuous Cycle** — the auto-update + auto-learn loop (repo resync + hooks-updater + auto-learn). Every session improves the system.
- **#3 Federation** — Zeus Memory as the central shared knowledge store. No state siloed on individual machines; all learning flows to `https://zeus.aldc.io`.
- **#6 Bidirectional Communication** — team messaging via `/msg` (CCE-native delivery when online, Slack fallback when not). Presence heartbeat (30 s) so team members see each other.

For the canonical system diagram, see `docs/architecture/CCE_ARCHITECTURE.mermaid` (in-repo). Do not maintain a copy here — the in-repo file is authoritative.

---

## Data Flow

CCE is fundamentally a data-plumbing layer between a developer's machine and Zeus Memory. Four distinct flows:

### 1. Tool-use → auto-learn (outbound, per-session)

```
Claude Code tool invocation
  → PostToolUse hook → tool_usage_logger.sh
  → appends JSONL to ~/.cache/cce/session-logs/<session_id>.jsonl

Stop hook fires
  → cce-auto-learn.sh (background, never blocks exit)
  → parses JSONL: tool counts, files modified, session duration
  → POST /api/store
      source=cce-session-auto-learn
      tenant_id=11111111-1111-1111-1111-111111111111  (ALDC Management)
  → stored in Zeus Postgres
  → idempotent via marker file ~/.cache/cce/auto-learn-<session_id>
```

This is the "learn" half of the virtuous cycle. Every session auto-contributes to team-wide knowledge without any manual action.

### 2. Inbox / presence (bidirectional, continuous)

```
Inbound (messages to developer):
  cce-poller-daemon.py
  → GET /api/presence/messages?peek=true  (every 3 s)
  → writes ~/.cache/cce/inbox-messages.json
  → writes ~/.cache/cce/inbox-status ("N messages | preview text")

  cce-inbox-check.sh (UserPromptSubmit)
  → authoritative read: marks messages as read via Zeus API
  → rate-limited: at most once per 10 s
  → clears inbox-messages.json + surfaced-ids after read

  cce-posttool-check.sh (PostToolUse)
  → reads cache only — no API calls
  → surfaces urgent messages mid-session (5 s cooldown)

  cce-stop-check.sh (Stop)
  → surfaces any unsurfaced messages at session end
  → blocks stop once per batch if unread messages exist

Outbound (heartbeat):
  cce-poller-daemon.py
  → POST /api/presence/heartbeat  (every 30 s)
  → identifies by $USER, normalized via USER_MAP to
    canonical names: {jk, lori, marshall, mike, brayden, paul}
  → updates presence-online.json (for statusline rendering)
```

### 3. Messaging (outbound, on-demand)

```
User types: /msg <recipient> <message>
  → command definition: .claude/commands/msg/
  → zeus-memory/api/messaging/delivery.send_message()
  → if recipient online (CCE-native): delivered via Zeus
  → if recipient offline: Slack Bot Token API fallback

Recipients: lori, mike, marshall (alias: mush/mushparker),
            brayden, jk, steven
Fan-out aliases: team / all  (all members except sender)
```

### 4. Hook-update (inbound, per-session-start)

```
cce-hooks-updater.py (SessionStart)
  → GET /api/hooks/manifest from Zeus
  → HMAC-SHA256 verify with $CCE_HOOKS_HMAC_KEY
  → per-file SHA-256 verify
  → atomic replace: staging dir → swap → ~/.claude/hooks/*
  → previous copies preserved in ~/.claude/hooks/_previous/
  → log: ~/.cache/cce/hooks-update/updater.log (100 lines)

Plus repo-level resync (phase 1 of launcher):
  git fetch origin main && git reset --hard origin/main
  (skipped if working tree dirty)
```

### Credential discovery chain

Launcher and hooks each search in order:

- **Launcher**: `$HOME/.env` → `$CCE_ROOT/.env` → `$HOME/projects/.env`
- **Hooks**: `$HOME/.env` → `$HOME/zeus-memory/.env` → `$HOME/repos/zeus-memory/.env`

Per-machine values live in `~/.env` (chmod 0600). The repo's `.env.example` is the schema — all placeholder values, no production secrets.

---

## Hook System

Full reference table of all 20 hooks in `hooks/`. Build this from `ls hooks/` + docstrings — every hook is verified against the actual file.

| Hook file | Trigger | Purpose |
|---|---|---|
| `cce-session-start.sh` | SessionStart | Launch poller daemon, ensure `~/.cache/cce/` exists, kill stale pollers (SIGTERM → SIGKILL), auto-install `team-msg`/`cce-msg-doctor` symlinks in `~/.local/bin/` |
| `cce-hooks-updater.py` | SessionStart | HMAC-SHA256-verified pull of new hook versions from Zeus; atomic replace of `~/.claude/hooks/*`; preserves `_previous/`; stdlib-only |
| `cce-commands-sync.sh` | SessionStart | Sync `.claude/commands/` from CCE repo (source of truth) to `~/.claude/commands/`; always exits 0 |
| `session_start_skill_check.py` | SessionStart | Check for pending skill candidates from previous sessions; analyse recent transcripts for new patterns; report high-confidence candidates |
| `session_start_messaging.sh` | SessionStart | Register session and show presence + pending messages; sends heartbeat via Zeus API |
| `ensure_zeus_mcp_configured.py` | SessionStart | Reconcile `.mcp.json` (repo) into `~/.mcp.json` (user); prevents `Remember` tool auth errors |
| `ecosystem_review_check.py` | SessionStart | Auto-run ecosystem review if: >7 d ago (background, non-blocking) / >30 d ago (immediate) / never run. Skip with `CCE_SKIP_ECOSYSTEM_CHECK=true` |
| `startup_readiness_check.py` | launch-time (phase 7) | 11-check verification: credential discovery, GitHub sync capability, Zeus API accessibility, skills library availability |
| `cce-poller-daemon.py` | daemon (started by session-start) | Long-lived process: polls messages every 3 s, sends heartbeat every 30 s, writes all output to `~/.cache/cce/`; self-terminates after 12 h or if PID file removed |
| `cce-posttool-check.sh` | PostToolUse | Surface inbox messages mid-session; reads cache only (no API calls); 5 s cooldown between checks; urgent messages bypass cooldown; exits 0 always |
| `tool_usage_logger.sh` | PostToolUse | Append every tool invocation to `~/.cache/cce/session-logs/<session_id>.jsonl` (Bash commands, file ops, etc.); also triggers hourly learning-capture reminders at 50-tool intervals |
| `cce-inbox-check.sh` | UserPromptSubmit | **Authoritative** inbox consumer — the only hook that calls the real API to mark messages as read; clears `inbox-messages.json` + `surfaced-ids` + `stop-batch-id` after read; rate-limited to once per 10 s |
| `message_check.sh` | UserPromptSubmit | Fast count-check via Zeus API (< 50 ms, count_only); if messages exist, fetches full list and outputs them inline |
| `cce-stop-check.sh` | Stop | Surface unsurfaced messages at end of turn; blocks stop once per batch with a JSON decision so Claude acknowledges them; reads cache only |
| `cce-auto-learn.sh` | Stop (via stop-check, async) | Parse session JSONL → compute tool counts / files modified / duration → POST to Zeus `/api/store`; idempotent via per-session marker file |
| `session_stop_messaging.sh` | SessionEnd | Deregister from presence API; kill heartbeat daemon |
| `cce-statusline.sh` | statusLine | Render status bar from cache files (`inbox-messages.json`, `tasks-stats`, `learnings-stats`, `presence-online.json`); format: `CCE v<ver> | N Inbox | N Assigned | DR | TDR | online-users` |
| `cce-learnings-cache.py` | background (called by statusline) | Write `~/.cache/cce/learnings-stats` (pipe-delimited: `USER_TODAY|USER_DR|TEAM_TODAY|TEAM_DR`); exits early if cache is fresh (<120 s); supports `--force` / `--bootstrap` |
| `cce-tasks-cache.py` | background (called by statusline) | Write `~/.cache/cce/tasks-stats` (format: `pending_in|pending_out`); persistent task list at `inbox-tasks.json`; exits early if cache fresh (<30 s) |
| `precompact_context_saver.sh` | PreCompact | Preserve critical session state before auto-compaction; outputs preserved context to stdout so Claude sees it after compaction |

### Caching model

All ephemeral state lives under `${XDG_CACHE_HOME:-$HOME/.cache}/cce/`:

| File / Dir | Content |
|---|---|
| `poller.pid` | PID of running poller daemon |
| `inbox-messages.json` | Full message list (written by poller, read by hooks) |
| `inbox-status` | `"N\|SUMMARY"` one-liner for statusline fallback |
| `presence-online.json` | Team presence state (from heartbeat) |
| `tasks-stats` | `"pending_in\|pending_out"` for statusline |
| `learnings-stats` | `"USER_TODAY\|USER_DR\|TEAM_TODAY\|TEAM_DR"` for statusline |
| `session-logs/<session_id>.jsonl` | Per-session tool-usage log |
| `hooks-update/` | `updater.log`, `_previous/` (hook backups), staging dir |
| `auto-learn-<session_id>` | Idempotency marker for auto-learn |
| `current-session-id` | Session ID persisted by SessionStart |

Everything in this directory is regenerable — safe to wipe if debugging.

### Windows / Git Bash compatibility

Several hooks contain an explicit Python-binary probe loop instead of `command -v`:

```bash
PYTHON=""
for _py in python3 python py; do
    if "$_py" -c "import sys" 2>/dev/null; then
        PYTHON="$_py"
        break
    fi
done
[[ -z "$PYTHON" ]] && exit 0
```

This is a deliberate design choice: `command -v` returns alias text in non-interactive Git Bash contexts (where aliases are not loaded), causing the hook to receive an aliased string as the command rather than the real binary path. The probe loop tries each candidate by actually executing it, which is reliable across platforms. Every new hook author on Windows must use this pattern.

---

## Skills & Commands

### Skills vs commands

The repo ships both, and they are distinct:

- **Skills** (`.claude/skills/<category>/<skill>.md`) — reusable prompt templates invoked mid-session. Referenced as `Skill(<name>)` in Claude Code. Token-compressed domain knowledge.
- **Commands** (`.claude/commands/<name>/` or top-level `.md`) — slash-command invocations (`/msg`, `/session-exit`, `/repo-learn`, `/discover-skills`, `/zeus-health`, `/cce-optimize`, etc.). YAML frontmatter specifies `name`, `description`, `model`, `allowed-tools`.

### Scale

- **195 skills** across **49 categories** (per `SKILLS_INDEX.md` auto-generated 2026-02-11 — this is the authoritative figure)
- `README.md` says "190+" — stale
- `CLAUDE.md` says "178 skills + 14 command skills" — stale; different counting convention

### Catalog pointers

| Resource | Purpose |
|---|---|
| `SKILLS_INDEX.md` | Human-readable table of all 195 skills by category |
| `skills_index.json` | Machine-readable catalog (~42 KB) |
| `SKILL_TEMPLATE.md` | Template for creating a new skill |
| `EXTERNAL_SKILLS.md` | Third-party skill repos: Anthropic official, VoltAgent awesome-agent-skills, travisvn awesome-claude-skills, alirezarezvani claude-skills, wshobson commands |

### When to create a skill

From `README.md`:

Create a skill when:
- You have explained the same thing to Claude **3+ times**
- A pattern should be **standardised across projects**
- **Security/quality requirements** must be enforced
- Domain knowledge is **tedious to re-explain**
- Token-heavy explanations could be **condensed**

Do NOT create a skill for: one-offs, operations Claude knows well, rapidly-changing patterns, personal preferences.

### 5-step skill creation workflow (from `README.md`)

1. **Identify the Pattern** — notice repetition during project work; document in `PROGRESS.md`
2. **Use the Template** — copy `SKILL_TEMPLATE.md` (or `~/.claude/skills/SKILL_TEMPLATE.md`) and fill in all sections
3. **Test the Skill** — use it in a real project context and verify results
4. **Save to Correct Category** — `~/.claude/skills/{category}/{skill-name}.md` (lowercase-with-hyphens filename)
5. **Commit and Share** — `git add .claude/skills/ && git commit -m "Add skill: {skill-name}"`

---

## CLI Reference

All `cce` subcommands — some handled inline in the launcher (Bash), others delegated to `tools/cce_cli.py` (Python).

| Command | Handler | Purpose |
|---|---|---|
| `cce` | Launcher | Full 8-phase startup + `exec claude` |
| `cce exit` | Launcher (inline) | Session-exit workflow: learn + Zeus store + cleanup |
| `cce learn` | Launcher (inline) | Print skill-extraction guidance for the current session |
| `cce setup [--pull <IP>] [--user <user>]` | `tools/cce_setup.sh` | One-shot machine setup (interactive or pull-from-reference-machine) |
| `cce troubleshoot` | `tools/troubleshooter.py` | Full diagnostics |
| `cce init <name> [--type=T] [--priority=P] [--duration=D] [--objective="..."]` | `cce_cli.py` | Create new project from `CLAUDE_CODE_PROJECT_TEMPLATE.md` |
| `cce status <name>` | `cce_cli.py` | Read `status.json` from project dir |
| `cce update <name> --phase=<phase> --content="<update>"` | `cce_cli.py` | Append checkpoint to project `PROGRESS.md` |
| `cce list [--status=active\|completed\|archived]` | `cce_cli.py` | Projects inventory |
| `cce validate <name>` | `cce_cli.py` | Structure check |
| `cce archive <name>` | `cce_cli.py` | Move to `projects/completed/`; follow with Nextcloud push |
| `cce search "<query>"` | `cce_cli.py` | Zeus Memory search proxy |
| `cce decompose "<description>"` | `cce_cli.py` | Break a workflow description into atomic tasks |
| `cce git commit --message="..."` | `cce_cli.py` → `git_integration.GitWorkflowManager` | Git commit wrapper (soft dep — disabled if import fails) |
| `cce git branch <name> --type=feature` | `cce_cli.py` → `git_integration.GitWorkflowManager` | Git branch wrapper |
| `cce help` | Launcher | Print help text |

### `CCE_SKIP_*` bypass vars

Use these when debugging the launcher without triggering all phases:

| Var | Phase skipped |
|---|---|
| `CCE_SKIP_UPDATE=true` | Repo resync (phase 1) |
| `CCE_SKIP_SKILL_CHECK=true` | Skill discovery check (phase 2) |
| `CCE_SKIP_MCP_CONFIG=true` | MCP config injection (phase 3) |
| `CCE_SKIP_MESSAGING=true` | Messaging init (phase 4) |
| `CCE_SKIP_HOOKS=true` | Hook sync (phase 6) |
| `CCE_SKIP_READINESS=true` | Readiness check (phase 7) |

Example — start Claude without touching repo, hooks, or `~/.claude/`:

```bash
CCE_SKIP_UPDATE=true CCE_SKIP_HOOKS=true CCE_SKIP_SKILL_CHECK=true cce
```

---

## Developer Guide

### Prerequisites

| Requirement | Notes |
|---|---|
| `git` | Required |
| `python3` (3.10+) | Required |
| `claude` CLI | Required — must be installed before `cce` is useful |
| `bash` | Required. Windows: use Git Bash |
| `curl`, `jq` | Optional — used by some hooks and skills |
| Docker | Optional — used by some skill categories |
| `gh` CLI | Optional — used by some skills |

### Install

**Option 1 — clone and install:**

```bash
git clone https://github.com/ALDC-io/claude_code_enhanced.git ~/repos/claude_code_enhanced
bash ~/repos/claude_code_enhanced/scripts/install.sh
```

**Option 2 — curl-pipe (README convention):**

```bash
curl -sSL https://raw.githubusercontent.com/ALDC-io/claude_code_enhanced/main/install.sh | bash
```

Note: the actual installer lives at `scripts/install.sh` — the curl path uses `install.sh` at root as a convention (the README's stated path); the real file is at `scripts/`. The installer clones the repo, symlinks `cce` to `/usr/local/bin/cce`, runs the readiness check, and shows next steps.

### Per-machine setup

Run after install:

```bash
cce setup
# or pull creds from an existing configured machine:
cce setup --pull <reference-machine-IP> --user <ssh-user>
```

`tools/cce_setup.sh` runs 7 steps:

1. Gather credentials (manual entry or `--pull <IP>` via `sshpass` over SSH)
2. Write `~/.env` (chmod 0600)
3. Configure global git (`user.name`, `user.email`, `credential.helper=store`, `~/.git-credentials`)
4. Write `~/.claude/mcp.json` + `~/.claude/settings.local.json` (Zeus MCP + permission allowlist)
5. Create `~/.cce/{cron,logs,sessions,skills}/`
6. Append CCE section to `~/.bashrc`
7. Clone `zeus-memory` into `~/repos/zeus-memory-api`

### Required env vars

From `.env.example` — must be populated in `~/.env`:

| Var | Required | Purpose |
|---|---|---|
| `ZEUS_API_KEY` | Yes | Personal Zeus Memory API key |
| `ZEUS_TENANT_ID` | Yes | Personal tenant UUID |
| `ANTHROPIC_API_KEY` | Yes | Claude API access |
| `GH_TOKEN` / `GITHUB_TOKEN` | Yes | GitHub repo auth for `cce` update |
| `ZEUS_ALDC_API_KEY` | Recommended | ALDC team tenant key — used for shared learnings (`cce learn`, auto-learn) |
| `CCE_HOOKS_HMAC_KEY` | Recommended | Hook updater HMAC key — required to receive hook pushes from Zeus |
| `DB_*` / `ZEUS_DB_*` | Optional | Zeus Postgres direct access |
| `SLACK_BOT_TOKEN` | Optional | Messaging Slack fallback |
| `AZURE_*` | Optional | Azure resource skills |
| `NEXTCLOUD_*` | Optional | Nextcloud sync (project archive) |
| `MIRO_*` | Optional | Miro integration |

### Tenant IDs (safe to document — not credentials)

- `b513bc6e-ad51-4a11-bea3-e3b1a84d7b55` — JK Confidential (private)
- `11111111-1111-1111-1111-111111111111` — ALDC Management Team (shared roll-up; use for all `cce learn` writes and auto-learn)

The actual API keys live in `~/.env`; these UUIDs are identifier-only and safe to reference in docs and wiki.

### Running CCE

After install and setup, just type `cce` from any directory. The launcher self-locates via:

```
$CCE_ROOT  →  script-resolved path  →  $HOME/repos/claude_code_enhanced/
          →  $HOME/cce/repos/claude_code_enhanced/  →  $HOME/claude_code_enhanced/
```

### Running tests

```bash
cd ~/repos/claude_code_enhanced && python -m pytest tests/
```

Seven test files: `test_phase1.py`, `test_phase2_{compactor,parallel,recovery,workflow}.py`, `test_phase2_5_skills.py`, `test_hallucination_reduction.py`. Tests are **NOT run in CI** — no `.github/workflows/test.yml` exists. Pass locally before merging.

### Context recovery after `/clear`

From `CLAUDE.md`:

```bash
# 1. Verify Zeus Memory
curl https://zeus.aldc.io/health

# 2. Test DB
PGPASSWORD="$DB_PASSWORD" psql \
  "host=psql-zeus-memory-dev.postgres.database.azure.com \
   port=5432 dbname=zeus_core user=zeus_admin sslmode=require" \
  -c "SELECT COUNT(*) FROM zeus_core.memories WHERE tenant_id='b513bc6e-ad51-4a11-bea3-e3b1a84d7b55';"

# 3. Find previous context
git log --oneline -20 && ls -la projects/
```

### Common pitfalls

**Repo working tree is ephemeral.** `cce` resets to `origin/main` on every launch. Never hand-edit files in `~/repos/claude_code_enhanced/` expecting them to survive. All customisation goes in `~/.claude/` or per-project `CLAUDE.md`.

**`.claude/settings.local.json` regeneration.** Gitignored; recreated on launch if missing. The launcher only creates it when absent — it will not overwrite customisations. But `git reset` won't touch it (gitignored), so customisations survive the repo resync.

**`command -v python3` fails in non-interactive Git Bash.** Use the probe-loop pattern from `cce-session-start.sh` when writing new hooks on Windows (see § Hook System → Windows / Git Bash compatibility).

**`ZEUS_API_KEY` vs `ZEUS_ALDC_API_KEY`.** Team learnings use the ALDC key; personal memory uses the personal key. `cce-auto-learn.sh` prefers `ZEUS_ALDC_API_KEY` when set. Use the ALDC key for all `cce learn` writes so they roll up to the shared tenant.

**Stale poller daemon.** PID file at `~/.cache/cce/poller.pid`. `cce-session-start.sh` kills stale pollers (SIGTERM → SIGKILL) on startup. If messaging seems dead: `cat ~/.cache/cce/poller.pid && kill -0 <pid>`.

**Broker socket path.** `/run/user/$UID/cce/broker.sock`. On Windows/Git Bash this path may not exist; the broker falls back silently.

**`projects/` folder is committed.** Project work is in git, not gitignored. Don't let it grow with in-progress private work. Archive to Nextcloud via `cce archive <name>` after completion.

See also [[cce-troubleshooting]] for settings.local.json parsing bugs, Zeus API key issues, and more.

---

## Distribution & Deployment

**There is no server-side deploy.** CCE is a client-side CLI. "Deployment" means distribution to developer machines.

### Install channel

GitHub: `github.com/ALDC-io/claude_code_enhanced`. Install via `scripts/install.sh` or curl-pipe from README.

### Update channel

`cce` launcher resyncs `origin/main` on every invocation (if working tree clean). Latest-always — no version pinning. Skip with `CCE_SKIP_UPDATE=true`.

### Hook distribution

Two independent paths:

1. **Launcher sync** — `cce` copies `hooks/*.sh|*.py` from the repo working tree to `~/.claude/hooks/` during phase 6. Requires the developer to run `cce`.

2. **Zeus hook-updater** — `cce-hooks-updater.py` pulls HMAC-verified hook updates from Zeus independently of the repo. This is the **remote-enforcement path**: ALDC can push a critical hook fix to all online team machines without waiting for each dev to run `cce` again.

### Rollback

Since distribution is `git reset --hard origin/main`, rollback = revert the offending commit on `main`. The next `cce` on each machine pulls the revert automatically.

For hook-only issues pushed via the updater: `~/.claude/hooks/_previous/` holds the prior copy. Swap back manually by copying from `_previous/` to `~/.claude/hooks/`.

### CI/CD

The only GitHub workflow is `.github/workflows/claude.yml`:
- Triggers when a human `@claude`-mentions in an issue, issue comment, or PR review comment
- Runs `anthropics/claude-code-action@v1` with `--max-turns 10`
- Permissions: `contents:write`, `pull-requests:write`, `issues:write`
- Secret: `ANTHROPIC_API_KEY`
- **Not a build, test, or publish pipeline.**

### Azure scripts clarification

`scripts/deploy-with-health-checks.sh`, `scripts/deploy-phase1.sh`, `scripts/azure-diagnostics.sh`, `scripts/container-logs-stream.sh`, `scripts/secret-audit.sh` exist in this repo but they deploy [[zeus-memory]] (the backend API + container apps), **not CCE itself**. Do not confuse them with a "CCE deployment." See [[zeus-memory]] for the container-apps deploy runbook.

### No staging / test environments

Single production track. The "test" for a hook or skill change is: run `cce` on a developer machine. Risky changes should be guarded by `CCE_SKIP_*` env flags. No automated pipeline validates changes.

---

## Project Template System

CCE enforces a mandatory project-template workflow for all CCE work sessions (per `CLAUDE.md`: "no exceptions").

### Template file

`projects/CLAUDE_CODE_PROJECT_TEMPLATE.md` — placeholders include:

- Project type: `Bug Fix | Feature Development | System Integration | Performance Optimization | Other`
- Priority
- Duration
- Objective
- Target Zeus Memory ID

### Lifecycle commands

| Command | Effect |
|---|---|
| `cce init <YYYY-MM-DD-project-name>` | Create `projects/<name>/` with `project_plan.md` + `status.json` |
| `cce update <name> --phase=<phase> --content="<update>"` | Append checkpoint to `PROGRESS.md` (one per Claude session) |
| `cce status <name>` | Read `status.json` |
| `cce list [--status=active\|completed\|archived]` | Inventory `projects/` |
| `cce validate <name>` | Structure check |
| `cce archive <name>` | Move to `projects/completed/`; follow with Nextcloud push |

### State structure per project

```
projects/<YYYY-MM-DD-name>/
├── project_plan.md     # Template instantiation + objective
├── status.json         # Machine-readable status
└── PROGRESS.md         # Session-by-session checkpoints
```

---

## Integrations

| Integration | How | Key env vars |
|---|---|---|
| [[zeus-memory]] | HTTP API at `https://zeus.aldc.io`; also MCP at `https://zeus.aldc.io/mcp`. Code: `tools/zeus_integration.py`. Hook traffic uses stdlib `urllib.request` + bearer token. | `ZEUS_API_KEY`, `ZEUS_ALDC_API_KEY`, `ZEUS_TENANT_ID` |
| MCP | `.mcp.json` (repo) → `~/.mcp.json` (user), reconciled by `ensure_zeus_mcp_configured.py`. HTTP transport. Powers Claude Code's `Remember` tool. | `ZEUS_API_KEY` |
| Slack | Messaging fallback when recipient not online in CCE. Uses `SLACK_BOT_TOKEN` (webhooks go stale — do not use `SLACK_WEBHOOK_URL`). Recipient user IDs in `msg` command skill. | `SLACK_BOT_TOKEN` |
| Context7 MCP | `tools/context7_handler.py` (~30 KB). Token-aware cache + ranker. Reduces hallucinations (see `tests/test_hallucination_reduction.py`). | (none — MCP-based) |
| Anthropic / Claude API | `ANTHROPIC_API_KEY` — consumed by `claude` CLI and some tools/skills | `ANTHROPIC_API_KEY` |
| OpenAI / Gemini | Optional; keys in `.env.example`; consumers scattered across tools and skills | `OPENAI_API_KEY`, `GEMINI_API_KEY` |
| Voyage AI | Embedding model used by Zeus for semantic search | `VOYAGE_API_KEY` |
| Miro | Specific skill category (`miro/`) | `MIRO_ACCESS_TOKEN`, `MIRO_CLIENT_ID`, etc. |
| Nextcloud | Project archive destination for `cce archive`; pattern established in `CLAUDE.md` | `NEXTCLOUD_ZEUS_*` |
| GitHub | `GH_TOKEN` for repo auth; `tools/git-askpass.sh` for non-interactive HTTPS auth; `.git-credentials` written by `cce setup` | `GH_TOKEN`, `GITHUB_TOKEN` |

---

## Tech Debt / Known Issues

**No package manifest.** Python dependencies (`requests`, `httpx`, `pytest`, etc.) are implicit — discovered only by reading `import` statements. A new developer has no one-shot `pip install -r ...`. Fix candidates: add `pyproject.toml` or `requirements.txt`.

**No CI tests.** Seven `pytest` files exist, zero CI runs. Regressions are caught only when a developer runs tests locally before merging. No `.github/workflows/test.yml`.

**Hook distribution by HMAC is team-trust-based.** `CCE_HOOKS_HMAC_KEY` is shared across machines. Compromise of that key plus a valid Zeus API key enables arbitrary code execution on every team member's machine via hook push. This is an explicit architectural trust boundary — document and treat accordingly.

**`git reset --hard` on every launch is fragile.** The repo-resync phase is gated by `git diff --quiet HEAD` — if a dev has uncommitted work in the repo working tree, the reset is skipped. The design assumes the repo is always clean (read-only). An uncommitted change in the repo would silently suppress all future updates until it is removed.

**Windows path handling is by convention, not enforcement.** Every new hook author must remember the `for _py in python3 python py; do ... done` probe-loop pattern. A shared `hooks/_lib.sh` helper would enforce this. Currently it is documented-but-informal.

**Stale skill counts.** `README.md` says "190+", `SKILLS_INDEX.md` says "195 across 49 categories" (authoritative, auto-generated), `CLAUDE.md` says "178 skills + 14 command skills" (different counting convention). All three coexist in the repo. The wiki quotes `SKILLS_INDEX.md` and treats the others as stale.

**`commands/msg/` duplicates `.claude/commands/msg/`** — the legacy top-level `commands/` folder has one entry (`msg/`). Unclear whether this is load-bearing or historical cruft. Flagged for cleanup — do not act without investigation.

**`projects/` is committed to git.** Project work is not gitignored. Risk of accidentally committing client data. Consider gitignoring `projects/` and treating Nextcloud as the canonical store.

**No `.env.example` credential leak** (verified). `.env.example` contains only placeholder values (e.g. `ghp_your_github_token_here`). No production secrets in-repo.

---

## See Also

- [[cce]] — **The product / project page.** Vision, principles, current state, open questions. This repo page covers the engineering layer; [[cce]] covers the "why."
- [[zeus-memory]] — The backend: API, Postgres, DAA, MCP. All CCE persistence lives here.
- [[cce-troubleshooting]] — Known issues and fixes: settings.local.json parsing bugs, Windows path problems, Zeus API key configuration, poller daemon startup. Do not duplicate — link to it.
- [[ai-pr-workflow]] — ALDC's full PR workflow (Semgrep + TruffleHog + Claude Opus review + PyTestArch). CCE is the dev-side layer operating under this umbrella.
- [[ai-driven-dev-workflow]] — ALDC's AI-first development methodology; CCE is the tooling that implements it.
- [[monorepo-research]] — Analysis of consolidating ALDC repos to maximise CCE skill reuse. Research complete, pending decision.
- [[factoria]] — Sibling agentic project (autonomous data engineering platform).
- [[openclaw]] — Sibling agentic project (open-source agent runtime/gateway used by Factoria).
- [[postman-collections]] — Unrelated repo but referenced in CCE skills for API debugging patterns.
