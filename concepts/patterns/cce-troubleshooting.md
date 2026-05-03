---
tags: [concept, pattern, cce, troubleshooting, claude-code]
aliases: [CCE issues, CCE troubleshooting]
sources: [sources/obsidian-import/general/CCE/Issues/]
created: 2026-04-16
updated: 2026-05-02
---

# CCE Troubleshooting

Known issues and fixes for the Claude Code Enhanced (CCE) system. CCE is a wrapper around Claude Code with auto-updating, hooks, and Zeus memory integration.

## Issue #1: settings.local.json Parsing Error

**Symptom**: CCE startup shows hook validation error — `"string": Expected object, but received string`

**Root cause**: The `hooks` field in `.claude/settings.local.json` was a string instead of the required `{"type": "command", "command": "..."}` object format. CCE's `git reset --hard origin/main` on every launch would overwrite any local fix.

**Fix options**:
1. **Merge to main** — only permanent fix since CCE resets to origin/main on every launch
2. **Set `CCE_SKIP_UPDATE=true`** — prevents git reset but also stops auto-updates
3. **Better long-term**: Add `settings.local.json` to `.gitignore` and have CCE generate it per-machine on first launch

**Final resolution**: Removed `settings.local.json` from git tracking, added to `.gitignore`, and CCE generates it with correct format on launch (PHASE 3.25). Existing users' customizations are backed up to `~/.cce/settings.local.json.bak` during the one-time transition.

## Issue #2: Zeus Message API Not Found

**Symptom**: `zeus-memory/api/messaging not found` warning on startup

**Root cause**: CCE looks for locally-cloned `zeus-memory` repo at `~/repos/zeus-memory/api/messaging`. If not cloned, cross-machine messaging (inbox, presence poller) is unavailable.

**Impact**: Harmless warning. Nothing breaks without it.

## Issue #2b: Settings Check Skipped (Windows Path Bug)

**Symptom**: Python error during settings validation on Windows/Git Bash

**Root cause**: MINGW expands `$HOME` to `/c/Users/PaulRussell` but Python on Windows needs `C:\Users\PaulRussell`. The `open(settings_file)` call fails silently.

**Fix**: Use `os.path.expanduser("~")` in the Python snippet instead of the bash-expanded `$HOME` path.

## Issue #3: CCE Startup Environment Variables

**Symptom**: `ZEUS_API_KEY` not available when poller daemon starts

**Root cause**: The daemon script expects `ZEUS_API_KEY` in the environment but doesn't load `.env` itself.

**Quick fix**:
```bash
set -a && source ~/.env && set +a && unset ANTHROPIC_API_KEY && python ~/.claude/hooks/cce-poller-daemon.py &
```

**Long-term fix**: Have PHASE 4 of the CCE startup script source `.env` before launching the poller daemon.

## Issue #4: Zeus API Key Mismatch

Referenced but details in separate issue file.

## Issue #5: CCE Hooks Updater

Referenced but details in separate issue file.

## Issue #6: Status Line Not Appearing

Referenced but details in separate issue file.

## Issue #7: CCX MCP "No active session" / Stale Session Accumulation

**Symptom**: CCX MCP tools fail with `"No active session for session_id='' user_id='anonymous'"` or `"Invalid or missing Mcp-Session-Id"`.

**Root cause**: Stale sessions accumulate in the CCX SessionManager because SessionEnd hooks don't always fire (Claude Code crash, timeout, etc.). The MCP auto-resolution logic requires exactly 1 active session to map `user_id`; with multiple sessions it falls through to `"anonymous"`, and ToolHandler rejects the call. Orphan recovery at server startup also re-creates sessions with fresh `started_at` timestamps, defeating the lazy re-resolution filter.

**Symptom variant**: `cce_memory_store` returns `{"status": "queued"}` but memories don't appear in Zeus. This is the same root cause — session count > 1 prevents user resolution. Memories ARE queued in CCX; they land after recovery. Verify via leaderboard after fixing.

**Diagnosis**:
```bash
curl -s http://localhost:7432/api/health  # check "sessions" count — should be 1
```

**Manual recovery** (run in order — confirmed working 2026-05-02):
```bash
# 1. Mark orphan JSONL files as processed
for f in ~/repos/ccx/data/sessions/cc-*.jsonl; do
  sid=$(basename "$f" .jsonl)
  marker="$HOME/repos/ccx/data/sessions/auto-learn-${sid}"
  [ ! -f "$marker" ] && echo "processed" > "$marker" && echo "Marked: $sid"
done

# 2. Clean stale session cache — keep only most recent session-*.id file
# Find most recent:
ls -t /c/Users/PaulRussell/AppData/Local/ccx/session-*.id | head -1
# Read its session ID:
cat $(ls -t /c/Users/PaulRussell/AppData/Local/ccx/session-*.id | head -1)
# Delete all others (Git Bash):
KEEP=$(ls -t /c/Users/PaulRussell/AppData/Local/ccx/session-*.id | head -1 | xargs basename)
for f in /c/Users/PaulRussell/AppData/Local/ccx/session-*.id; do
  [ "$(basename $f)" != "$KEEP" ] && rm "$f" && echo "Removed: $(basename $f)"
done

# 3. Restart CCX container
docker restart ccx
sleep 3

# 4. Re-fire session-start (use session ID read in step 2)
SESSION_ID="cc-xxxxxxxxxxxxxxx"  # from step 2
curl -X POST http://localhost:7432/events/session-start \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"${SESSION_ID}\", \"user\": \"paul\", \"hostname\": \"$(hostname)\", \"cwd\": \"$(pwd)\"}"

# 5. Verify
curl -s http://localhost:7432/api/health  # sessions should be 1

# 6. Verify memories landed (check leaderboard)
curl -s https://zeus.aldc.io/api/learnings/leaderboard \
  -H "X-API-Key: zm_aldc_mgmt_5fa85da311ce24614a52128d7a2e63eb" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); paul=next(u for u in d['leaderboard'] if u['user']=='paul'); print(paul)"
```

**Code fix** (pending upstream in ccx repo for JK/Mike):
1. `server.py` MCP `initialize`: fall back to `settings.cce_user` when session-count auto-resolution fails (multiple sessions)
2. `server.py` MCP `tools/call`: same `cce_user` fallback in lazy re-resolution
3. `server.py` MCP handler: auto-recover MCP sessions with unknown `Mcp-Session-Id` after container restart instead of rejecting
4. **Enhancement:** Add CCX health check (`sessions == 1`) as first step in `/cce-learn` — auto-run recovery before storing memories to eliminate the failure mode

**First observed**: 2026-04-30 (3 consecutive sessions)
**Confirmed recovery**: 2026-05-02 — 21 stale sessions cleared, all queued memories landed

## General CCE Architecture Notes

- CCE runs `git checkout -- . && git clean -fd && git reset --hard origin/main` on every launch (PHASE 1)
- This means local changes don't survive restarts unless merged to main or `CCE_SKIP_UPDATE=true` is set
- Settings files should be gitignored and generated per-machine

## See Also

- [[cce]] — CCE project overview (in entities/projects/)
