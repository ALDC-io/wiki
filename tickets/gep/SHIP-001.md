---
tags: [ticket, internal, shipyard, rename]
aliases: [SHIP-001, shipyard-rename]
sources: []
created: 2026-05-04
updated: 2026-05-04
---

# SHIP-001 — Rename aldc-shipyard to shipyard

Rename the repo from `aldc-shipyard` to `shipyard`. Drops the `aldc-` prefix for a cleaner, memorable name that doesn't collide with CCE/CCX/Zeus. Future home for wiki + Zeus Memory integration.

## Status

Planned — Research & Tooling lane (sprint-agnostic).

## Scope

Based on prior rename (aldc-automation → aldc-shipyard, 2026-04-29 session 3):

1. **GitHub**: `gh repo rename shipyard` on `ALDC-io/aldc-shipyard`
2. **Local folder**: `C:\Users\PaulRussell\repos\aldc-shipyard` → `C:\Users\PaulRussell\repos\shipyard`
3. **Claude Code memory**: migrate `~/.claude/projects/C--Users-PaulRussell-repos-aldc-shipyard\` to new path-keyed directory
4. **Wiki references**: update `[[aldc-shipyard]]` entity page, index.md, repo-integration-map, any workstream trackers referencing the repo path
5. **PROGRESS.md**: update header
6. **Boot prompts**: any that reference `C:\Users\PaulRussell\repos\aldc-shipyard`

Estimated: ~15-20 min dedicated session.

## Boot Prompt

````
You are renaming the aldc-shipyard repo to shipyard. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this ticket: `C:\Users\PaulRussell\repos\wiki\tickets\gep\SHIP-001.md`
3. Read the prior rename session for reference: `C:\Users\PaulRussell\repos\aldc-shipyard\PROGRESS.md` — search for "2026-04-29 (session 3) — repo rename cleanup"

Steps:
1. gh repo rename shipyard (on ALDC-io/aldc-shipyard)
2. Rename local folder: aldc-shipyard → shipyard
3. Update PROGRESS.md header
4. Grep wiki for "aldc-shipyard" — update all references to "shipyard"
5. Update the [[aldc-shipyard]] wiki entity page (rename to shipyard.md)
6. Migrate Claude Code memory files from old path-keyed directory to new one
7. Update index.md with new page name
8. Commit both repos

Paul handles git commits. This is a Sonnet-appropriate mechanical task.
````

## See Also

- [[aldc-shipyard]] — current entity page (to be renamed)
- Prior rename: PROGRESS.md session 2026-04-29 (session 3)
