---
tags: [concept, pattern, ai, claude-code, skill, tracking, self-improvement]
aliases: [Skill Mirrors, Council Skills, Tracked Skills]
sources: []
created: 2026-07-30
updated: 2026-07-30
---

# Tracked skill sources — the council-of-five skills

Version-controlled mirrors of the two adversarial council skills, so their evolution is diffable
and can drive a self-improvement loop. Companion knowledge pages hold the *why*;
these files hold the *what*.

| Mirror | Live canonical path | Knowledge page |
|---|---|---|
| `inquest-SKILL.md` | `~/.claude/skills/inquest/SKILL.md` | [[inquest-bug-resolution]] |
| `conclave-SKILL.md` | `~/.claude/skills/conclave/SKILL.md` | [[conclave-pr-review]] |

## ⚠ The mirror contract — read before editing either file

**`~/.claude/skills/<name>/SKILL.md` is canonical. These files are mirrors.** Claude Code loads
skills from `~/.claude/skills/`, which is **not** a git repository — that is the whole reason these
mirrors exist.

**Mirrors are kept byte-identical on purpose.** No added frontmatter, no header, no edits. That is
what makes drift detectable by a plain `diff`. Do not "improve" a mirror in place.

### Sync direction

1. Edit the **live** skill at `~/.claude/skills/<name>/SKILL.md` (that is what actually runs).
2. Copy it here verbatim.
3. Add a dated entry to the **Revision log** on the knowledge page, naming the incident that drove
   the change.

### Drift check

```bash
for s in inquest conclave; do
  diff -q "$HOME/.claude/skills/$s/SKILL.md" \
          "$HOME/repos/wiki/concepts/patterns/skills/$s-SKILL.md" \
    && echo "  in sync: $s" || echo "  DRIFTED: $s"
done
```

Run this before trusting a mirror, and after any skill edit.

## Known limitation

A copy will drift the moment someone edits the live skill and forgets step 2. The durable fix is to
make `~/.claude/skills/{inquest,conclave}` symlinks into this directory so there is one file rather
than two — deferred, because it needs a Windows symlink/junction and a decision about whether the
wiki is an appropriate home for executable config. **Until then, treat a mirror as a snapshot and
run the drift check.**

## Why these two are tracked and others are not

These are the **general-purpose adversarial council skills** — reusable across every repo and
client, and the ones most worth improving over time because each real incident teaches them
something. Project-scoped skills live with their project (e.g. `aldc-launchpad/.claude/commands/`
for the `launchpad-*` set). Vlad's `/investigate-adversarial` is documented separately at
[[adversarial-investigation-skill]] and is not mirrored here.

## See Also

- [[inquest-bug-resolution]]
- [[conclave-pr-review]]
- [[adversarial-investigation-skill]]
- [[ai-pr-workflow]]
