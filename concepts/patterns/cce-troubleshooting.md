---
tags: [concept, pattern, cce, troubleshooting, claude-code]
aliases: [CCE issues, CCE troubleshooting]
sources: [sources/obsidian-import/general/CCE/Issues/]
created: 2026-04-16
updated: 2026-04-16
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

## General CCE Architecture Notes

- CCE runs `git checkout -- . && git clean -fd && git reset --hard origin/main` on every launch (PHASE 1)
- This means local changes don't survive restarts unless merged to main or `CCE_SKIP_UPDATE=true` is set
- Settings files should be gitignored and generated per-machine

## See Also

- [[cce]] — CCE project overview (in entities/projects/)
