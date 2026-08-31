#!/usr/bin/env python3
"""wiki_lint — the check `CLAUDE.md` §4 has always defined and never run.

⭐ **Ship the instrument, not the repair.** Every uncontrolled count of this corpus produced during
the 2026-08-30 review was wrong, and wrong by a plausible amount rather than by an error:

    broken links     1,146  ->  532  ->  437  ->  244  ->  216  ->  38 genuinely repairable
    unreachable      181 (37%)  ->  12 (3.5%)

Nobody was careless. Each figure came from an instrument that ran fine and could not see something.
So this file's job is not to fix the wiki — it is to make a number about the wiki reproducible, and
to **refuse to report at all when its own controls fail**.

⛔ **The four exclusions, each bought with a specific near-miss.** A checker without them does damage:

1. **Code spans and fenced blocks are masked.** 44% of apparent broken links are not links. The 19
   ``[[wikilinks]]`` occurrences are `CLAUDE.md` *documenting the convention*, and template
   placeholders like ``[[YYYY-MM-DD]]`` live in `daily/_template.md`. A repair script without this
   mask rewrites the schema documentation.
2. **`sources/` is immutable** (`CLAUDE.md`: *"RAW SOURCES — immutable, never modify"*). Its 152
   pages are a deliberate archive of Paul's pre-wiki Obsidian vault. They are excluded from the page
   population and **kept as valid link targets** — a page legitimately cites a source document.
   Counting them as orphans inflated the orphan rate by ~5x and is what made the corpus look broken.
3. **Zeus Memory keys are external pointers, not broken links.** `project_*` / `feedback_*` targets
   are deliberately given wikilink syntax with display aliases. "Repairing" them deletes the only
   pointers from the wiki into Zeus Memory.
4. **`log.md` is append-only** (`CLAUDE.md`). It is reported on and never proposed for rewrite.
   Rewriting an append-only operation log for cosmetic link hygiene is the F82 defect.

⭐ **The controls are mandatory and the exit code depends on them.** A link checker that silently
resolves nothing reports a beautifully clean wiki. So `--check-instrument` runs first, always: it
asserts the resolver finds pages that are known to exist and does *not* find one known absent. **If a
control fails the run aborts with exit 2 and reports nothing**, because a number from a blind
instrument is worse than no number.

Read-only. It opens files and prints. It never writes to the corpus.

    python scripts/wiki_lint.py              # full report
    python scripts/wiki_lint.py --counts     # just the regenerable counts, for index.md
    python scripts/wiki_lint.py --strict     # exit 1 if repairable defects exist (CI)
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import subprocess
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    print("wiki_lint needs pyyaml: pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Excluded from the PAGE POPULATION, retained as LINK TARGETS. See docstring exclusion 2.
IMMUTABLE = ("sources/",)
#: Excluded from both — gitignored, not part of the corpus.
#: Excluded from both — gitignored `# Local-only session scratch (never committed)`.
#: ⚠ 335 was 4 too many: it retained 3 `scratch/` files and `PROGRESS.md`. The authored
#: corpus is 331 (330 git-tracked, +1 real-but-uncommitted page).
NOT_CORPUS = ("vault/", "scratch/", "PROGRESS.md")
#: Append-only; reported on, never proposed for rewrite. Exclusion 4.
APPEND_ONLY = ("log.md",)
#: ⛔ NEVER aggregate freshness by directory max(). Earned 2026-08-31: `processes/` last-commit
#: read 2026-08-29 and looked tended, while 87 of its 101 pages had no substantive change in 90+
#: days. The recency came entirely from THREE NEW FILES. A directory whose freshness comes from
#: creation is accreting, not maintaining — report per-page, and split created from modified.
#: Corollary: filter mechanical edits by PER-FILE LINE COUNT, never by files-touched-per-commit —
#: the two largest commits here (174 and 130 files) authored most of the corpus.
FRESHNESS_RULE = "per-page, created split from modified; never directory max()"

#: Cross-system pointers into Zeus Memory. Exclusion 3.
EXTERNAL_PREFIXES = ("project_", "feedback_", "session_", "task_")

WIKILINK = re.compile(r"\[\[([^\]|#\n]+)")
#: Resolution tiers — LOWER WINS. The policy is DECLARED, never emergent.
TIER_PATH, TIER_ALIAS, TIER_STEM, TIER_TITLE = 0, 1, 2, 3
POLICY = "explicit path > exact alias > filename stem > title/H1; sources/ deprioritised"

#: Fenced blocks first, then inline code. Order matters — an inline-code regex run first would
#: chew the fence markers and leave the block body exposed.
FENCE = re.compile(r"```.*?```|~~~.*?~~~", re.S)
INLINE = re.compile(r"`[^`\n]*`")


def rel(p: pathlib.Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def mask_code(text: str) -> str:
    """Blank code regions, preserving offsets so line numbers stay honest."""
    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))
    return INLINE.sub(blank, FENCE.sub(blank, text))


class Wiki:
    def __init__(self, root: pathlib.Path):
        self.root = root
        self.all: list[pathlib.Path] = []
        self.corpus: list[pathlib.Path] = []      # authored, lintable
        self.index: dict[str, list] = {}          # key -> [(tier, page), ...]
        self.text: dict[pathlib.Path, str] = {}
        self.fm: dict[pathlib.Path, dict] = {}
        self._load()

    def _load(self) -> None:
        for p in sorted(self.root.rglob("*.md")):
            if ".git" in p.parts:
                continue
            r = rel(p)
            if r.startswith(NOT_CORPUS):
                continue
            self.all.append(p)
            if not r.startswith(IMMUTABLE):
                self.corpus.append(p)
            try:
                t = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                t = ""
            self.text[p] = t
            fm: dict = {}
            if t.startswith("---"):
                parts = t.split("---", 2)
                if len(parts) >= 3:
                    try:
                        loaded = yaml.safe_load(parts[1])
                        fm = loaded if isinstance(loaded, dict) else {}
                    except yaml.YAMLError:
                        fm = {}
            self.fm[p] = fm
            self._register(p, fm, t)

    def _register(self, p: pathlib.Path, fm: dict, text: str) -> None:
        """Index every name this page answers to, WITH ITS TIER.

        ⛔ Not `setdefault`. A flat first-wins index is an *undocumented tie-break*, and an
        undocumented tie-break is how `entities/tools/eclipse.md` — 391 lines, the flagship
        connector-platform doc — sits at in-degree 0 while `[[Eclipse]]` is written 117 times and
        every one of them means that page. The link looks green and lands somewhere else.
        """
        demote = 10 if rel(p).startswith(IMMUTABLE) else 0

        def add(key: str, tier: int) -> None:
            if key:
                self.index.setdefault(key, []).append((tier + demote, p))

        add(rel(p)[:-3].lower(), TIER_PATH)
        for a in (fm.get("aliases") or []):
            if isinstance(a, str):
                add(a.strip().lower(), TIER_ALIAS)
        add(p.stem.lower(), TIER_STEM)
        if p.parent.name:
            add(f"{p.parent.name}/{p.stem}".lower(), TIER_STEM)
        if isinstance(fm.get("title"), str):
            add(fm["title"].strip().lower(), TIER_TITLE)
        m = re.search(r"^#\s+(.+)$", text, re.M)
        if m:
            add(m.group(1).strip().lower(), TIER_TITLE)

    def candidates(self, target: str) -> list:
        """Every (tier, page) for a key, best tier first."""
        return sorted(self.index.get(target.strip().lower(), []), key=lambda tp: tp[0])

    def _partial_path(self, target: str):
        """Obsidian's partial-path form — `[[navira/README]]`, `[[entities/repos/eclipse]]`.

        223 instances over 59 targets, the single largest NON-defect bucket in this corpus —
        larger than code examples. A flat resolver reports every one as broken. Matched on a path
        SUFFIX and accepted only when exactly one page matches, so it can never invent a winner.
        """
        t = target.strip().lower().removesuffix(".md")
        while t.startswith(("../", "./")):        # relative form -> plain suffix
            t = t.split("/", 1)[1]
        if "/" not in t:
            return None
        hits = list(dict.fromkeys(
            pg for key, cands in self.index.items() for _tier, pg in cands
            if key == t or key.endswith("/" + t)))
        return hits[0] if len(hits) == 1 else None

    def resolve(self, target: str):
        """The winner under the DECLARED policy: path > exact alias > stem > title, sources/ last.

        ⭐ The policy is stated in `POLICY` and printed by the report, because a reachability number
        quoted without its tie-break is not a measurement — 16 live pages flip reachability purely
        on the choice of rule.
        """
        c = self.candidates(target)
        if c:
            return c[0][1]
        return self._partial_path(target)

    def is_ambiguous(self, target: str) -> bool:
        """True when two DIFFERENT pages tie at the winning tier.

        This is the check `CLAUDE.md` 4 has no equivalent of, and the one that must exist *before*
        any repair — a repair validated under one tie-break silently regresses under another.
        """
        c = self.candidates(target)
        if len(c) < 2:
            return False
        best = c[0][0]
        return len({p for tier, p in c if tier == best}) > 1

    def links(self, p: pathlib.Path):
        """(target, line) for every real wikilink on a page — code regions masked."""
        for m in WIKILINK.finditer(mask_code(self.text[p])):
            yield m.group(1).strip(), self.text[p].count("\n", 0, m.start()) + 1


# --------------------------------------------------------------------------- the mandatory control

def check_instrument(w: Wiki) -> list[str]:
    """⛔ Runs before anything is reported. A failure here aborts the run.

    Two halves, and the second is the one people skip: proving the resolver finds what exists is not
    enough — an index that returned a page for *every* string would pass that and report zero broken
    links forever.
    """
    fails: list[str] = []

    must_resolve = ["star-schema-convention", "vacuous-verification", "GEP", "snowflake"]
    for key in must_resolve:
        if w.resolve(key) is None:
            fails.append(f"POSITIVE CONTROL FAILED: {key!r} should resolve and did not")

    must_not = ["this-page-does-not-exist-xyzzy", "confirm-consumer-source"]
    for key in must_not:
        got = w.resolve(key)
        if got is not None:
            fails.append(f"NEGATIVE CONTROL FAILED: {key!r} resolved to {rel(got)}")

    probe = "[[star-schema-convention]] `[[in-code-should-be-masked]]`"
    if "in-code-should-be-masked" in mask_code(probe):
        fails.append("MASK CONTROL FAILED: inline code was not masked")
    if "star-schema-convention" not in mask_code(probe):
        fails.append("MASK CONTROL FAILED: the mask ate a real link")

    if len(w.index) < len(w.all):
        fails.append(f"INDEX TOO SMALL: {len(w.index)} keys for {len(w.all)} pages")
    return fails


# ------------------------------------------------------------------------------------- the checks

def classify(target: str, w: Wiki) -> str:
    r"""⛔ SYNTAX IS CHECKED BEFORE RESOLUTION, and the order is the whole point.

    17 links carry a trailing backslash (`[[entities/repos/eclipse\]]` x7). A resolver with any
    permissive normalisation strips it and reports them **green while the raw file is malformed** —
    a check that cannot fail on the class it exists to catch. Resolving first would hide them, so
    resolution comes second.

    Note `../foo` and `a/b` are NOT malformed — they are Obsidian's relative and partial-path forms,
    223 instances over 59 targets and the largest non-defect bucket in this corpus.
    """
    t = target.strip()
    if t.endswith(("\\", "/")) or t != t.strip("\\"):
        return "malformed"
    if w.resolve(target) is not None:
        return "ok"
    if target.startswith(EXTERNAL_PREFIXES):
        return "external"          # Zeus Memory pointer — NOT broken
    if re.fullmatch(r"(GP|FU92|DV|ALDC|SHIP)-[0-9A-Z-]+", target, re.I):
        return "ticket-no-page"    # needs a page written, not a link edited
    return "missing"


def report(w: Wiki, counts_only: bool, strict: bool) -> int:
    buckets: dict[str, list[tuple[str, str, int]]] = collections.defaultdict(list)
    inbound: dict[pathlib.Path, set] = collections.defaultdict(set)

    for p in w.corpus:
        if rel(p) in APPEND_ONLY:
            continue
        for target, line in w.links(p):
            kind = classify(target, w)
            if kind == "ok":
                inbound[w.resolve(target)].add(p)
            else:
                buckets[kind].append((rel(p), target, line))

    unreferenced = [p for p in w.corpus if not inbound[p] and rel(p) not in APPEND_ONLY]
    no_fm = [p for p in w.corpus if not w.fm[p]]
    no_sources = [p for p in w.corpus if w.fm[p] and not w.fm[p].get("sources")]

    print(f"pages (all, incl. immutable sources/)  {len(w.all)}")
    print(f"pages (authored corpus, lintable)      {len(w.corpus)}")
    print(f"alias index keys                       {len(w.index)}")
    if counts_only:
        return 0

    print()
    print("LINKS — code spans masked, sources/ kept as targets, log.md excluded as a source")
    print(f"  repairable (missing page)            {len(buckets['missing'])}")
    print(f"  malformed (escaping / rel path)      {len(buckets['malformed'])}")
    print(f"  ticket id, no page written           {len(buckets['ticket-no-page'])}   <- write a page, do not edit the link")
    print(f"  external pointer (Zeus Memory)       {len(buckets['external'])}   <- NOT broken; repairing these deletes them")

    for kind in ("missing", "malformed"):
        if buckets[kind]:
            print(f"\n  {kind}:")
            for src, tgt, line in sorted(buckets[kind])[:40]:
                print(f"    {src}:{line}  ->  [[{tgt}]]")
            if len(buckets[kind]) > 40:
                print(f"    … {len(buckets[kind]) - 40} more")

    print(f"\nREACHABILITY\n  nothing links to them                {len(unreferenced)} / {len(w.corpus)}")
    by_dir = collections.Counter(rel(p).split("/")[0] for p in unreferenced)
    for d, n in by_dir.most_common(8):
        print(f"    {n:4d}  {d}")

    print("")
    print("AMBIGUITY — the check CLAUDE.md 4 has no equivalent of")
    print("  policy: " + POLICY)
    shadowed: dict = {}
    amb = 0
    for pg in w.corpus:
        if rel(pg) in APPEND_ONLY:
            continue
        for target, _ln in w.links(pg):
            if w.is_ambiguous(target):
                amb += 1
                win = w.resolve(target)
                for _t, cand in w.candidates(target):
                    if cand is not win:
                        shadowed.setdefault(cand, set()).add(target)
    print("  links resolving through an ambiguous key   " + str(amb))
    print("  live pages SHADOWED by a collision         " + str(len(shadowed)))
    for pg, keys in sorted(shadowed.items(), key=lambda kv: -len(kv[1]))[:8]:
        print("    " + rel(pg) + "  <- " + ", ".join(sorted(keys)[:3]))
    print("  A shadowed page is cited and unreachable — the link looks green and lands elsewhere.")

    print(f"\nSCHEMA (CLAUDE.md 4)\n  no frontmatter                       {len(no_fm)}")
    print(f"  frontmatter but no sources:          {len(no_sources)}")

    print("\nWRITE-SIDE LIVENESS — the mechanism, not the corpus")
    for d in ("daily", "standup", "workplan"):
        dated = sorted(x.stem for x in (w.root / d).glob("*.md") if re.match(r"\d{4}-\d{2}-\d{2}", x.stem))
        print(f"  {d + '/':12s} newest dated entry  {dated[-1] if dated else 'NONE'}")
    try:
        pt = (w.root / "potential-tickets.md").read_text(encoding="utf-8", errors="replace")
        filed = len(re.findall(r"^\s*[-*]\s", pt.split("## Filed")[1].split("##")[0], re.M)) if "## Filed" in pt else 0
        print(f"  potential-tickets  entries promoted to Filed  {filed}")
    except (OSError, IndexError):
        print("  potential-tickets  NOT-VISIBLE")

    repairable = len(buckets["missing"]) + len(buckets["malformed"])
    print(f"\nGENUINELY REPAIRABLE LINK DEFECTS: {repairable}")
    print("Everything else above is a page to write, an external pointer, or a deliberate archive.")

    if strict and repairable:
        return 1
    return 0


#: Every class the 2026-08-30 council identified, with an example that must land in it. A
#: classifier is only worth its exclusions, and an exclusion nobody has watched fire is a guess.
SELF_TEST = [
    ("entities/repos/eclipse" + chr(92), "malformed",       "trailing backslash, x17 in corpus"),
    ("star-schema-convention",           "ok",              "plain stem"),
    ("../ops-platform/README",           "ok",              "relative form — NOT a defect"),
    ("navira/README",                    "ok",              "partial path — largest non-defect bucket"),
    ("project_lectric_cm_data_gap",      "external",        "Zeus key — repairing it deletes it"),
    ("GP-293",                           "ticket-no-page",  "write a page, do not edit the link"),
    ("no-such-page-xyzzy",               "missing",         "genuinely repairable"),
]


def self_test(w: Wiki) -> int:
    bad = 0
    for target, expect, why in SELF_TEST:
        got = classify(target, w)
        if got != expect:
            bad += 1
            print(f"  FAIL  {target!r} -> {got}, expected {expect}  ({why})")
        else:
            print(f"  pass  {expect:16s} {why}")
    print("")
    print(str(len(SELF_TEST) - bad) + "/" + str(len(SELF_TEST)) + " classification controls pass")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint the wiki. Read-only.")
    ap.add_argument("--counts", action="store_true", help="just the regenerable counts")
    ap.add_argument("--strict", action="store_true", help="exit 1 if repairable defects exist")
    ap.add_argument("--self-test", action="store_true",
                    help="prove each classification branch can fire")
    a = ap.parse_args()

    w = Wiki(ROOT)
    fails = check_instrument(w)
    if fails:
        print("INSTRUMENT CONTROL FAILED — reporting nothing.", file=sys.stderr)
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        print("\nA number from a blind instrument is worse than no number.", file=sys.stderr)
        return 2
    if a.self_test:
        return self_test(w)
    return report(w, a.counts, a.strict)


if __name__ == "__main__":
    raise SystemExit(main())
