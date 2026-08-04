---
tags: [concept, pattern, ai, claude-code, skill, tracking, self-improvement]
aliases: [Skill Mirrors, Council Skills, Tracked Skills]
sources: []
created: 2026-07-30
updated: 2026-08-03
---

# Tracked skill sources — the council-of-five skills

Version-controlled mirrors of the adversarial council and orchestration skills, so their evolution
is diffable and can drive a self-improvement loop. Companion knowledge pages hold the *why*;
these files hold the *what*.

| Mirror | Live canonical path | Knowledge page |
|---|---|---|
| `inquest-SKILL.md` | `~/.claude/skills/inquest/SKILL.md` | [[inquest-bug-resolution]] |
| `conclave-SKILL.md` | `~/.claude/skills/conclave/SKILL.md` | [[conclave-pr-review]] |
| `army-SKILL.md` | `~/.claude/skills/army/SKILL.md` | *none yet* — revision log is inline, `SKILL.md` §Revision log |

⚠ **`assay` is a general-purpose council skill and is NOT mirrored** (`~/.claude/skills/assay/`).
By the reasoning below it qualifies, so this is a gap rather than a decision — it is unbacked until
someone adds it and its row here.

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
for s in inquest conclave army; do
  diff -q --strip-trailing-cr "$HOME/.claude/skills/$s/SKILL.md" \
                              "$HOME/repos/wiki/concepts/patterns/skills/$s-SKILL.md" \
    && echo "  in sync: $s" || echo "  DRIFTED: $s"
done
```

Run this before trusting a mirror, and after any skill edit.

⚠ **`--strip-trailing-cr` is load-bearing, and so is `/.gitattributes`.** `core.autocrlf=true`
converts these files to CRLF on checkout, which breaks byte-identity and makes this check report
`DRIFTED` on every fresh clone — a check that reads authoritative and returns garbage. Measured on
`army-SKILL.md`: a fresh `git checkout-index` produced **11,653 bytes / 180 CRLF** against the live
file's **11,473 / 0**. The repo-root `.gitattributes` pins `*-SKILL.md` to `eol=lf` so the bytes
survive checkout; the `diff` flag is insurance for working copies that predate that rule. Verified
after the fix: all three mirrors 0 CRLF and in sync.

## Known limitation

A copy will drift the moment someone edits the live skill and forgets step 2. The durable fix is to
make `~/.claude/skills/{inquest,conclave,army}` symlinks into this directory so there is one file rather
than two — deferred, because it needs a Windows symlink/junction and a decision about whether the
wiki is an appropriate home for executable config. **Until then, treat a mirror as a snapshot and
run the drift check.**

## Why these are tracked and others are not

These are the **general-purpose adversarial council and orchestration skills** — reusable across
every repo and client, and the ones most worth improving over time because each real incident
teaches them something. `army` differs from the other two in kind: the councils fix their lens set
in advance because their domain is known, whereas `army` chooses the decomposition itself, which is
why its guardrails are stricter and its revision log matters more. Project-scoped skills live with their project (e.g. `aldc-launchpad/.claude/commands/`
for the `launchpad-*` set). Vlad's `/investigate-adversarial` is documented separately at
[[adversarial-investigation-skill]] and is not mirrored here.

## See Also

- [[inquest-bug-resolution]]
- [[conclave-pr-review]]
- [[adversarial-investigation-skill]]
- [[ai-pr-workflow]]
