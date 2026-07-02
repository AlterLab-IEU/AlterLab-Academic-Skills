#!/usr/bin/env python3
"""Cross-skill confusion matrix — turn the eval assets into a collision benchmark.

With 210 skills (39 database connectors, 30 bioinformatics skills) the failure mode a
large suite actually hits is *cross-firing*: a user's request activates the wrong sibling.
This tool measures that risk statically (no LLM, CI-safe) from two signals already in the
repo:

1. **Trigger-noun overlap between siblings.** Each skill's ``description`` carries the
   activation surface. We tokenize each description into distinctive trigger nouns and,
   within every domain, rank sibling pairs by keyword overlap (Jaccard). High-overlap
   pairs are the cross-firing hot spots.

2. **Near-miss deferral coverage.** The eval convention pairs each skill with
   ``should_not_trigger`` near-misses that name the sibling to defer to. We check, for
   every high-overlap pair, whether such a mutual near-miss exists — a high-overlap pair
   with NO near-miss between them is an actionable routing gap.

It also enforces one hard invariant used by CI/tests: every ``alterlab-*`` skill named in
any eval's ``expected_output`` / assertion values must resolve to a real skill (no dangling
or typo'd cross-references).

    python3 scripts/confusion_matrix.py              # full report
    python3 scripts/confusion_matrix.py --top 25     # top-N overlap pairs
    python3 scripts/confusion_matrix.py --strict     # exit non-zero on dangling eval refs
    python3 scripts/confusion_matrix.py --json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

_SKILL_TOKEN = re.compile(r"\balterlab-[a-z0-9]+(?:-[a-z0-9]+)*")
_WORD = re.compile(r"[a-z][a-z0-9+/-]{2,}")

# Generic tokens that carry no discriminating signal — drop them before overlap scoring.
_STOPWORDS = frozenset({
    "use", "when", "this", "that", "for", "the", "and", "with", "from", "via", "into",
    "over", "across", "part", "academic", "skills", "suite", "alterlab", "user", "users",
    "using", "data", "analysis", "analyze", "python", "api", "apis", "rest", "direct",
    "access", "not", "trigger", "triggers", "prefer", "instead", "want", "wants", "need",
    "needs", "run", "running", "build", "building", "based", "between", "multiple", "other",
    "skill", "tool", "tools", "library", "libraries", "workflow", "workflows", "research",
    "results", "queries", "query", "search", "searching", "provide", "provides", "get",
    "generate", "generating", "support", "you", "are", "its", "per", "each", "any", "all",
    "one", "two", "raw", "http", "https", "does", "doing", "your",
})


def skill_dirs() -> list[Path]:
    return sorted(p.parent for p in SKILLS_DIR.rglob("SKILL.md"))


def _frontmatter(skill_md: Path) -> dict[str, str]:
    lines = skill_md.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    fm: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line and line[0] not in " \t#":
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
    return fm


def _use_when_clause(desc: str) -> str:
    """The trigger-bearing part of a description: everything from the first 'Use ...' on,
    minus the suite label. Falls back to the whole description if no 'Use' clause."""
    m = re.search(r"\bUse (?:when|this|for|whenever|to)\b", desc, re.IGNORECASE)
    clause = desc[m.start():] if m else desc
    return clause.replace("Part of the AlterLab Academic Skills suite.", "")


def trigger_tokens(desc: str) -> set[str]:
    words = _WORD.findall(_use_when_clause(desc).lower())
    return {w for w in words if w not in _STOPWORDS}


def load_skills() -> dict[str, dict]:
    """name -> {category, tokens, dir}."""
    out: dict[str, dict] = {}
    for d in skill_dirs():
        fm = _frontmatter(d / "SKILL.md")
        name = fm.get("name") or d.name
        out[name] = {
            "category": d.parent.name,
            "tokens": trigger_tokens(fm.get("description", "")),
            "dir": d,
        }
    return out


def eval_skill_refs() -> dict[str, set[str]]:
    """skill -> set of sibling alterlab-* names it names in its evals (expected_output +
    assertion values)."""
    refs: dict[str, set[str]] = {}
    for ev in sorted(SKILLS_DIR.rglob("evals/evals.json")):
        try:
            data = json.loads(ev.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        this = data.get("skill", ev.parent.parent.name)
        found: set[str] = set()
        for e in data.get("evals", []) or []:
            text = e.get("expected_output", "") + " " + " ".join(
                str(a.get("value", "")) for a in e.get("assertions", []) or []
            )
            found |= set(_SKILL_TOKEN.findall(text))
        refs[this] = found
    return refs


def dangling_refs(known: set[str]) -> list[tuple[str, str]]:
    """(eval_file, token) for every alterlab-* token in an eval that names no real skill."""
    out: list[tuple[str, str]] = []
    for ev in sorted(SKILLS_DIR.rglob("evals/evals.json")):
        try:
            data = json.loads(ev.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rel = str(ev.relative_to(REPO_ROOT))
        for e in data.get("evals", []) or []:
            text = e.get("expected_output", "") + " " + " ".join(
                str(a.get("value", "")) for a in e.get("assertions", []) or []
            )
            for tok in set(_SKILL_TOKEN.findall(text)):
                if tok not in known:
                    out.append((rel, tok))
    return sorted(set(out))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def confusion_pairs(skills: dict[str, dict], refs: dict[str, set[str]],
                    min_overlap: float = 0.12) -> list[dict]:
    """Ranked within-domain sibling pairs by trigger-noun overlap, annotated with whether a
    mutual near-miss deferral exists between them."""
    by_cat: dict[str, list[str]] = {}
    for name, meta in skills.items():
        by_cat.setdefault(meta["category"], []).append(name)

    pairs: list[dict] = []
    for cat, names in by_cat.items():
        names = sorted(names)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                score = _jaccard(skills[a]["tokens"], skills[b]["tokens"])
                if score < min_overlap:
                    continue
                mutual = (b in refs.get(a, set())) or (a in refs.get(b, set()))
                pairs.append({
                    "category": cat,
                    "a": a,
                    "b": b,
                    "overlap": round(score, 3),
                    "shared": sorted(skills[a]["tokens"] & skills[b]["tokens"]),
                    "mutual_near_miss": mutual,
                })
    pairs.sort(key=lambda p: p["overlap"], reverse=True)
    return pairs


def deferral_coverage(skills: dict[str, dict], refs: dict[str, set[str]]) -> list[str]:
    """Skills whose evals name NO resolvable sibling in any negative (weaker near-miss)."""
    known = set(skills)
    weak = []
    for name in skills:
        sib = {r for r in refs.get(name, set()) if r in known and r != name}
        if not sib:
            weak.append(name)
    return sorted(weak)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--top", type=int, default=30, help="how many overlap pairs to print")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any eval names a non-existent skill")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    skills = load_skills()
    refs = eval_skill_refs()
    known = set(skills)
    dangles = dangling_refs(known)
    pairs = confusion_pairs(skills, refs)
    uncovered = [p for p in pairs if not p["mutual_near_miss"]]
    weak = deferral_coverage(skills, refs)

    if args.json:
        print(json.dumps({
            "total_skills": len(skills),
            "dangling_eval_refs": dangles,
            "overlap_pairs": pairs,
            "high_overlap_without_near_miss": uncovered,
            "skills_without_named_sibling_negative": weak,
        }, indent=2))
    else:
        print("=== Cross-skill confusion matrix ===")
        print(f"skills: {len(skills)}  |  within-domain overlap pairs (Jaccard≥0.12): {len(pairs)}")
        print(f"dangling eval skill-refs: {len(dangles)}")
        for f, tok in dangles:
            print(f"  DANGLING {tok} in {f}")
        print(f"\nTop {min(args.top, len(pairs))} cross-firing risk pairs "
              "(★ = no mutual near-miss between them → routing gap):")
        for p in pairs[:args.top]:
            flag = "  " if p["mutual_near_miss"] else "★ "
            print(f"  {flag}{p['overlap']:.3f} [{p['category']}] {p['a']} ~ {p['b']}  "
                  f"shared={p['shared'][:6]}")
        print(f"\nHigh-overlap pairs with NO mutual near-miss (routing gaps): {len(uncovered)}")
        print(f"Skills with no named-sibling negative (weaker boundary evals): {len(weak)}")
        if weak:
            print("  " + ", ".join(weak))

    return 1 if (args.strict and dangles) else 0


if __name__ == "__main__":
    raise SystemExit(main())
