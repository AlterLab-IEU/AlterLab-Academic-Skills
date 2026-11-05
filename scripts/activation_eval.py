#!/usr/bin/env python3
"""Hand-labelled skill-activation set: does the model pick the right *installed* skill?

``run_evals.py --activation`` asks the same question over every skill's own eval prompts, but
its candidate list is the target plus its first N same-category siblings in alphabetical
order, every skill is assumed installed, only English prompts are used, and a missing skill
is never tested. This harness measures the same description-only selection step on a small,
hand-written case set (``benchmarks/activation/cases.json``):

* every case names an **installed profile** — a realistic install computed from the repo's
  own plugin manifests (``.claude-plugin/marketplace.json``, each plugin's
  ``.claude-plugin/plugin.json`` and the ``plugins/`` bundles, dependencies followed);
* candidates are the installed skills chosen by an explicit policy (below), including the
  case's **hand-picked plausible distractors**, shuffled per run with a recorded seed, and the
  exact list shown is saved with every vote;
* cases are **clear**, **ambiguous** (several acceptable answers), **distractor** (built
  around named confusers) or **unavailable** (the right skill is NOT installed, so the right
  answer is ``none`` or a named installed fallback), in English and Turkish.

Candidate policy (``candidate_policy`` in the results):
  1. a profile with at most FULL_LIST_MAX installed skills: show every installed skill;
  2. a larger profile: show every installed skill of each plugin that owns the expected skill,
     an acceptable alternate or an explicit distractor; every installed alterlab-core skill (the
     general-purpose pipeline that competes with everything); every explicit distractor; plus a
     seeded sample of BACKGROUND_SAMPLE other installed skills so the list is not shaped only by
     the label. An uninstalled skill is never shown.

Outcome per case (majority over ``--runs`` votes; ties resolve to the WORSE outcome):
correct, acceptable_alternate, wrong_skill, missed (``none`` while an installed skill was
expected), false_activation (a skill while ``none`` was expected, or a non-fallback skill on an
unavailable case), correct_unavailable_handling (``none`` when the right skill is not
installed), no_answer (no usable vote: CLI error, refusal, timeout or unparseable reply).

This is a description-only selection proxy, NOT Claude Code's real skill loader; see
docs/activation.md for what it does and does not show.

    uv run python scripts/activation_eval.py --dry-run --limit 3     # prompts, no calls
    uv run python scripts/activation_eval.py --estimate              # number of CLI calls
    uv run python scripts/activation_eval.py --runs 3 --language tr  # live (claude CLI)

Exit codes: 0 = measured (every selected case got a usable majority choice); 3 = partial (some
cases no_answer); 2 = blocked (nothing usable, no ``claude`` CLI, or no case selected);
64 = the case file or a profile is invalid. Activation rates never fail a run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_evals as rv  # noqa: E402  (CLI call, model convention, catalog, results writer)

REPO = Path(__file__).resolve().parent.parent
CASES_PATH = REPO / "benchmarks" / "activation" / "cases.json"
RESULTS_KIND = "activation-set"
SCHEMA_VERSION = 1

FULL_LIST_MAX = 40        # profiles up to this size are shown whole
BACKGROUND_SAMPLE = 8     # seeded extra installed skills for larger profiles
CORE_PLUGIN = "alterlab-core"
DEFAULT_SEED = 20261105

LANGUAGES = ("en", "tr")
KINDS = ("clear", "ambiguous", "distractor", "unavailable")
NONE = "none"

CORRECT = "correct"
ACCEPTABLE = "acceptable_alternate"
WRONG = "wrong_skill"
MISSED = "missed"
FALSE_ACTIVATION = "false_activation"
CORRECT_UNAVAILABLE = "correct_unavailable_handling"
NO_ANSWER = "no_answer"
OUTCOMES = (CORRECT, ACCEPTABLE, CORRECT_UNAVAILABLE, WRONG, MISSED, FALSE_ACTIVATION, NO_ANSWER)
SUCCESS = (CORRECT, ACCEPTABLE, CORRECT_UNAVAILABLE)
STRICT = (CORRECT, CORRECT_UNAVAILABLE)
# Best -> worst; a tied majority takes the worst tied outcome so ties never inflate a rate.
_SEVERITY = (CORRECT, CORRECT_UNAVAILABLE, ACCEPTABLE, MISSED, WRONG, FALSE_ACTIVATION)

_KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_CHOICE = re.compile(r"CHOICE:\s*[`*\"'\[]*([A-Za-z0-9][A-Za-z0-9-]*)", re.IGNORECASE)

SELECT_PROMPT = """You are an AI assistant with a set of installed skills. Before you answer \
a user's request you may load ONE installed skill whose description fits the request. If no \
installed skill fits, you answer without loading one.

USER REQUEST:
{prompt}

INSTALLED SKILLS (name: description):
{listing}

Decide which single skill to load, judging only from the descriptions above. Answer none if \
no listed skill is a good fit for this request; do not pick a skill merely because it is \
loosely related.

Reply with exactly one line:
CHOICE: <one skill name from the list, verbatim, or none>
then one sentence of justification."""


class CaseFileError(Exception):
    """The case file or a profile definition is invalid (exit 64)."""


# --- Plugin manifests -> installed profiles ----------------------------------------------
def _frontmatter_name(skill_md: Path) -> str | None:
    lines = skill_md.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.partition(":")[2].strip().strip('"').strip("'") or None
    return None


def load_plugins(root: Path = REPO) -> dict[str, dict]:
    """Every marketplace plugin: name -> {"skills": [skill names], "dependencies": [...]}.

    Skills come from the marketplace entry's ``skills`` list, else the plugin's own
    ``.claude-plugin/plugin.json`` ``skills`` list, else the Claude Code default
    ``<source>/skills/*/``. Dependencies are the union of both manifests'. A listed skill
    directory without a SKILL.md is an error."""
    mp_path = root / ".claude-plugin" / "marketplace.json"
    try:
        market = json.loads(mp_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseFileError(f"cannot read {mp_path}: {exc}") from exc
    plugins: dict[str, dict] = {}
    for entry in market.get("plugins", []):
        name = entry["name"]
        src = (root / entry["source"]).resolve()
        manifest: dict = {}
        mf = src / ".claude-plugin" / "plugin.json"
        if mf.is_file():
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        listed = entry.get("skills") or manifest.get("skills")
        if listed:
            dirs = [(src / s).resolve() for s in listed]
        else:
            dirs = sorted(p.parent for p in (src / "skills").glob("*/SKILL.md"))
        skills = []
        for d in dirs:
            md = d / "SKILL.md"
            if not md.is_file():
                raise CaseFileError(f"plugin {name}: listed skill dir {d} has no SKILL.md")
            skills.append(_frontmatter_name(md) or d.name)
        deps = list(dict.fromkeys([*entry.get("dependencies", []),
                                   *manifest.get("dependencies", [])]))
        plugins[name] = {"skills": sorted(skills), "dependencies": deps}
    return plugins


def resolve_plugins(names: list[str], plugins: dict[str, dict]) -> list[str]:
    """The named plugins plus their transitive dependencies (sorted). Unknown name -> error."""
    seen: set[str] = set()
    stack = list(names)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        if n not in plugins:
            raise CaseFileError(f"unknown plugin '{n}' (not in the marketplace)")
        seen.add(n)
        stack.extend(plugins[n]["dependencies"])
    return sorted(seen)


def compute_profiles(defs: dict[str, dict], plugins: dict[str, dict]) -> dict[str, dict]:
    """profile -> {"requested", "plugins" (resolved), "skills" (sorted), "owner" skill->plugin}."""
    out: dict[str, dict] = {}
    for pname, spec in defs.items():
        requested = list(spec.get("plugins") or [])
        if not requested:
            raise CaseFileError(f"profile '{pname}' names no plugins")
        resolved = resolve_plugins(requested, plugins)
        owner: dict[str, str] = {}
        for p in resolved:
            for s in plugins[p]["skills"]:
                owner.setdefault(s, p)
        out[pname] = {"requested": requested, "plugins": resolved,
                      "skills": sorted(owner), "owner": owner}
    return out


# --- Case file ---------------------------------------------------------------------------
def load_case_file(path: Path = CASES_PATH) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseFileError(f"cannot read {path}: {exc}") from exc


def validate_cases(data: dict, catalog: dict, profiles: dict[str, dict]) -> list[str]:
    """Every problem in the case file (empty list = valid). Labels must name real skills, and
    each label must make sense for the case's installed profile."""
    errs: list[str] = []
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["case file has no 'cases' list"]
    seen: set[str] = set()
    for i, c in enumerate(cases):
        cid = c.get("id", f"#{i}")
        where = f"case {cid}"
        missing = [k for k in ("id", "prompt", "language", "kind", "installed_profile",
                               "expected", "acceptable", "distractors", "note") if k not in c]
        if missing:
            errs.append(f"{where}: missing {missing}")
            continue
        if not _KEBAB.match(str(cid)):
            errs.append(f"{where}: id must be kebab-case")
        if cid in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(cid)
        if not str(c["prompt"]).strip() or not str(c["note"]).strip():
            errs.append(f"{where}: prompt and note must be non-empty")
        if c["language"] not in LANGUAGES:
            errs.append(f"{where}: language must be one of {LANGUAGES}")
        if c["kind"] not in KINDS:
            errs.append(f"{where}: kind must be one of {KINDS}")
        if not isinstance(c["acceptable"], list) or not isinstance(c["distractors"], list):
            errs.append(f"{where}: acceptable and distractors must be lists")
            continue
        exp = c["expected"]
        for label, names in (("expected", [exp]), ("acceptable", c["acceptable"]),
                             ("distractors", c["distractors"])):
            for n in names:
                if n == NONE and label != "distractors":
                    continue
                if n not in catalog:
                    errs.append(f"{where}: {label} names unknown skill '{n}'")
        if exp in c["acceptable"] or exp in c["distractors"]:
            errs.append(f"{where}: expected '{exp}' repeated in acceptable/distractors")
        if set(c["acceptable"]) & set(c["distractors"]):
            errs.append(f"{where}: a skill is both acceptable and a distractor")
        prof = profiles.get(c["installed_profile"])
        if prof is None:
            errs.append(f"{where}: unknown installed_profile '{c['installed_profile']}'")
            continue
        installed = set(prof["skills"])
        if c["kind"] == "unavailable":
            if exp == NONE:
                errs.append(f"{where}: an unavailable case must name the missing skill")
            elif exp in installed:
                errs.append(f"{where}: unavailable case, but '{exp}' IS installed in "
                            f"profile '{c['installed_profile']}'")
        elif exp != NONE and exp not in installed:
            errs.append(f"{where}: expected '{exp}' is not installed in profile "
                        f"'{c['installed_profile']}' (use kind 'unavailable')")
        for n in c["acceptable"]:
            if n != NONE and n in catalog and n not in installed:
                errs.append(f"{where}: acceptable '{n}' is not installed, so it can never "
                            "be picked")
        for n in c["distractors"]:
            if n in catalog and n not in installed:
                errs.append(f"{where}: distractor '{n}' is not installed in the profile")
        if c["kind"] == "ambiguous" and not c["acceptable"]:
            errs.append(f"{where}: an ambiguous case needs at least one acceptable alternate")
        if c["kind"] == "distractor" and not c["distractors"]:
            errs.append(f"{where}: a distractor case needs at least one explicit distractor")
    return errs


def load_and_validate(path: Path = CASES_PATH, root: Path = REPO,
                      catalog: dict | None = None) -> tuple[dict, dict[str, dict]]:
    """(case data, computed profiles); raises CaseFileError listing every problem."""
    data = load_case_file(path)
    catalog = rv.skill_catalog() if catalog is None else catalog
    profiles = compute_profiles(data.get("profiles") or {}, load_plugins(root))
    for pname, prof in profiles.items():
        unknown = [s for s in prof["skills"] if s not in catalog]
        if unknown:
            raise CaseFileError(f"profile '{pname}': plugin skills not in catalog: {unknown}")
    errs = validate_cases(data, catalog, profiles)
    if errs:
        raise CaseFileError("\n".join(errs))
    return data, profiles


# --- Candidates --------------------------------------------------------------------------
def build_candidates(case: dict, profile: dict, seed: int) -> list[dict]:
    """The candidates shown for ``case`` (sorted by name), each with why it is shown."""
    installed = profile["skills"]
    owner = profile["owner"]
    why: dict[str, list[str]] = {}

    def add(name: str, reason: str) -> None:
        if name in owner:  # never show an uninstalled skill
            why.setdefault(name, [])
            if reason not in why[name]:
                why[name].append(reason)

    if len(installed) <= FULL_LIST_MAX:
        for s in installed:
            add(s, "installed-profile")
        for d in case["distractors"]:
            add(d, "explicit-distractor")
    else:
        focus = [(case["expected"], "expected-plugin")]
        focus += [(a, "acceptable-plugin") for a in case["acceptable"]]
        focus += [(d, "distractor-plugin") for d in case["distractors"]]
        for name, reason in focus:
            if name in owner:
                plugin = owner[name]
                for s in installed:
                    if owner[s] == plugin:
                        add(s, reason)
        for s in installed:
            if owner[s] == CORE_PLUGIN:
                add(s, "core-generalist")
        for d in case["distractors"]:
            add(d, "explicit-distractor")
        pool = sorted(s for s in installed if s not in why)
        rng = random.Random(f"{seed}|{case['id']}|background")
        for s in rng.sample(pool, min(BACKGROUND_SAMPLE, len(pool))):
            add(s, "background-sample")
    return [{"name": n, "why": why[n]} for n in sorted(why)]


def shuffled(names: list[str], seed: int, case_id: str, run: int) -> list[str]:
    """Deterministic per-run presentation order (reduces position bias across runs)."""
    order = sorted(names)
    random.Random(f"{seed}|{case_id}|run{run}").shuffle(order)
    return order


def build_prompt(case: dict, order: list[str], catalog: dict) -> str:
    listing = "\n".join(f"- {n}: {catalog[n][1]}" for n in order)
    return SELECT_PROMPT.format(prompt=case["prompt"], listing=listing)


# --- Model call and parsing ---------------------------------------------------------------
def ask_model(prompt: str, model: str, timeout: int) -> str:
    """One isolated claude CLI call (tests replace this function)."""
    return rv._claude(prompt, model, timeout)


def parse_choice(response: str, shown: list[str]) -> dict:
    """A vote from one response: {"choice", "status", "off_list", "detail"}."""
    if not rv._is_answer(response):
        return {"choice": None, "status": "no_answer", "off_list": False,
                "detail": response[:200]}
    m = _CHOICE.search(response)
    if not m:
        return {"choice": None, "status": "unparseable", "off_list": False,
                "detail": response[:200]}
    choice = m.group(1).lower()
    return {"choice": choice, "status": "answer",
            "off_list": choice != NONE and choice not in shown,
            "detail": response[:300]}


# --- Scoring ------------------------------------------------------------------------------
def classify(case: dict, choice: str | None) -> str:
    """Outcome of one (majority) choice for ``case``."""
    if choice is None:
        return NO_ANSWER
    exp, acc = case["expected"], case["acceptable"]
    if case["kind"] == "unavailable":
        if choice == NONE:
            return CORRECT_UNAVAILABLE
        return ACCEPTABLE if choice in acc else FALSE_ACTIVATION
    if exp == NONE:
        if choice == NONE:
            return CORRECT
        return ACCEPTABLE if choice in acc else FALSE_ACTIVATION
    if choice == exp:
        return CORRECT
    if choice in acc:
        return ACCEPTABLE
    return MISSED if choice == NONE else WRONG


def majority(case: dict, votes: list[str | None]) -> tuple[str | None, bool, dict]:
    """(majority choice, tie?, vote counts). Ties resolve to the worst-outcome choice."""
    counts = Counter(v for v in votes if v is not None)
    if not counts:
        return None, False, {}
    top = max(counts.values())
    tied = sorted(c for c, n in counts.items() if n == top)
    choice = max(tied, key=lambda c: _SEVERITY.index(classify(case, c)))
    return choice, len(tied) > 1, dict(sorted(counts.items()))


def _rate(n: int, of: int) -> dict:
    return {"n": n, "of": of, "rate": round(n / of, 4) if of else None}


def summarize(results: list[dict]) -> dict:
    """Outcome counts with explicit denominators: overall and split by kind, language,
    profile and expectation. ``answered`` (the denominator) excludes no_answer cases."""
    def group(rows: list[dict]) -> dict:
        counts = {o: sum(r["outcome"] == o for r in rows) for o in OUTCOMES}
        answered = len(rows) - counts[NO_ANSWER]
        return {"cases": len(rows), "answered": answered, "counts": counts,
                "success": _rate(sum(counts[o] for o in SUCCESS), answered),
                "strict": _rate(sum(counts[o] for o in STRICT), answered)}

    def split(key) -> dict:
        keys = sorted({key(r) for r in results})
        return {k: group([r for r in results if key(r) == k]) for k in keys}

    def expectation(r: dict) -> str:
        if r["kind"] == "unavailable":
            return "unavailable"
        return "none" if r["expected"] == NONE else "installed-skill"

    return {"overall": group(results),
            "by_kind": split(lambda r: r["kind"]),
            "by_language": split(lambda r: r["language"]),
            "by_profile": split(lambda r: r["installed_profile"]),
            "by_expectation": split(expectation),
            "definitions": {"success": list(SUCCESS), "strict": list(STRICT),
                            "denominator": "answered = cases - no_answer"}}


def run_case(case: dict, profile: dict, catalog: dict, model: str, timeout: int,
             runs: int, seed: int) -> dict:
    cands = build_candidates(case, profile, seed)
    shown = [c["name"] for c in cands]
    votes = []
    for r in range(1, runs + 1):
        order = shuffled(shown, seed, case["id"], r)
        vote = parse_choice(ask_model(build_prompt(case, order, catalog), model, timeout), shown)
        votes.append({"run": r, "order": order, **vote})
    choice, tie, counts = majority(case, [v["choice"] for v in votes])
    outcome = classify(case, choice)
    return {**{k: case[k] for k in ("id", "prompt", "language", "kind", "installed_profile",
                                    "expected", "acceptable", "distractors", "note")},
            "installed_count": len(profile["skills"]), "shown_count": len(shown),
            "candidates": cands, "votes": votes, "vote_counts": counts, "choice": choice,
            "tie": tie, "off_list": bool(choice) and choice != NONE and choice not in shown,
            "outcome": outcome}


def select_cases(cases: list[dict], *, ids: list[str] | None = None, kind: str | None = None,
                 language: str | None = None, profile: str | None = None,
                 limit: int | None = None) -> list[dict]:
    out = [c for c in cases
           if (not ids or c["id"] in ids) and (not kind or c["kind"] == kind)
           and (not language or c["language"] == language)
           and (not profile or c["installed_profile"] == profile)]
    return out[:limit] if limit is not None else out


def status_of(results: list[dict]) -> tuple[str, int]:
    usable = sum(r["outcome"] != NO_ANSWER for r in results)
    if usable == 0:
        return "blocked", 2
    if usable < len(results):
        return "partial", 3
    return "measured", 0


def _cli_available() -> bool:
    return shutil.which("claude") is not None


def _print_summary(summary: dict) -> None:
    def line(label: str, g: dict) -> str:
        c = g["counts"]
        s = g["success"]
        return (f"  {label:24} success {s['n']}/{s['of']}  strict {g['strict']['n']}/"
                f"{g['strict']['of']}  | correct {c[CORRECT]} alt {c[ACCEPTABLE]} "
                f"unavail-ok {c[CORRECT_UNAVAILABLE]} wrong {c[WRONG]} missed {c[MISSED]} "
                f"false-act {c[FALSE_ACTIVATION]} no-answer {c[NO_ANSWER]}")
    print(line("overall", summary["overall"]))
    for split in ("by_kind", "by_language", "by_profile", "by_expectation"):
        print(f"{split}:")
        for k, g in summary[split].items():
            print(line(k, g))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", default=str(CASES_PATH), help="case file (default: %(default)s)")
    ap.add_argument("--runs", type=int, default=3,
                    help="votes per case; majority wins, ties go to the worse outcome "
                         "(default 3; use an odd number)")
    ap.add_argument("--seed", type=int, default=None,
                    help=f"shuffle/sample seed (default: the case file's, else {DEFAULT_SEED})")
    ap.add_argument("--timeout", type=int, default=300, help="per-call timeout in seconds")
    ap.add_argument("--case", action="append", metavar="ID", help="only this case (repeatable)")
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--language", choices=LANGUAGES)
    ap.add_argument("--profile", metavar="NAME")
    ap.add_argument("--limit", type=int, metavar="N", help="first N selected cases")
    ap.add_argument("--dry-run", action="store_true",
                    help="print prompts and candidate lists; make no model calls")
    ap.add_argument("--estimate", action="store_true",
                    help="print how many claude CLI calls a run would make; no calls")
    ap.add_argument("--isolation", choices=["auto", "namespace", "none"], default="auto",
                    help="(live) confinement for CLI calls, as in run_evals.py")
    ap.add_argument("--results-dir", default=str(REPO / "eval-results"),
                    help="where to write the JSON results ('' to skip)")
    args = ap.parse_args(argv)
    if args.runs < 1:
        ap.error("--runs must be >= 1")
    if args.limit is not None and args.limit < 1:
        ap.error("--limit must be >= 1")

    cases_path = Path(args.cases)
    catalog = rv.skill_catalog()
    try:
        data, profiles = load_and_validate(cases_path, REPO, catalog)
    except CaseFileError as exc:
        print(f"Invalid activation case set:\n{exc}", file=sys.stderr)
        return 64
    if args.profile and args.profile not in profiles:
        ap.error(f"unknown profile '{args.profile}'; known: {sorted(profiles)}")
    seed = args.seed if args.seed is not None else int(data.get("default_seed", DEFAULT_SEED))
    selected = select_cases(data["cases"], ids=args.case, kind=args.kind,
                            language=args.language, profile=args.profile, limit=args.limit)
    if not selected:
        print("No activation case selected.", file=sys.stderr)
        return 2

    if args.estimate:
        print(f"{len(selected)} case(s) x {args.runs} run(s) = "
              f"{len(selected) * args.runs} claude CLI call(s) (no judge calls).")
        return 0
    if args.dry_run:
        for c in selected:
            prof = profiles[c["installed_profile"]]
            cands = build_candidates(c, prof, seed)
            order = shuffled([x["name"] for x in cands], seed, c["id"], 1)
            print(f"===== {c['id']} [{c['kind']}/{c['language']}] profile="
                  f"{c['installed_profile']} ({len(prof['skills'])} installed, "
                  f"{len(cands)} shown) expected={c['expected']} "
                  f"acceptable={c['acceptable']} =====")
            for x in cands:
                print(f"  {x['name']:36} {','.join(x['why'])}")
            print(build_prompt(c, order, catalog))
            print()
        print(f"DRY RUN: {len(selected)} case(s); no model calls were made and no results "
              "were produced.")
        return 0

    if not _cli_available():
        print("BLOCKED: the `claude` CLI is not on PATH; this harness needs it.",
              file=sys.stderr)
        return 2
    rv.configure_confinement(args.isolation)
    model = rv.alterlab_model()
    rv._reset_usage()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print("=== ACTIVATION SET (description-only selection proxy; live claude CLI calls) ===")
    print(f"model {model} | {len(selected)} case(s) x {args.runs} run(s) | seed {seed}")
    results = []
    for c in selected:
        res = run_case(c, profiles[c["installed_profile"]], catalog, model, args.timeout,
                       args.runs, seed)
        results.append(res)
        print(f"{c['id']:40} {res['outcome']:30} choice={res['choice']}"
              + (" (tie)" if res["tie"] else "") + (" (off-list)" if res["off_list"] else ""))
    status, code = status_of(results)
    summary = summarize(results)
    raw = cases_path.read_bytes()
    meta = rv._run_metadata(RESULTS_KIND, model, args.runs, args.timeout)
    iso = meta.get("isolation", {})
    meta["isolation"] = {"cli_flags": iso.get("cli_flags"),
                         "confinement": iso.get("confinement"),
                         "working_directory": "fresh temporary directory per call"}
    payload = {**meta, "schema_version": SCHEMA_VERSION, "kind": RESULTS_KIND,
               "started_at": started,
               "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "status": status, "runs": args.runs, "seed": seed,
               "case_set": {"path": str(cases_path.relative_to(REPO))
                            if cases_path.resolve().is_relative_to(REPO) else str(cases_path),
                            "version": data.get("version"),
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "selected": len(selected), "total": len(data["cases"])},
               "filters": {"case": args.case, "kind": args.kind, "language": args.language,
                           "profile": args.profile, "limit": args.limit},
               "profiles": {k: {"requested": v["requested"], "plugins": v["plugins"],
                                "skills": len(v["skills"])} for k, v in profiles.items()},
               "candidate_policy": {"full_list_max": FULL_LIST_MAX,
                                    "background_sample": BACKGROUND_SAMPLE,
                                    "core_plugin": CORE_PLUGIN,
                                    "order": "sorted then shuffled per run with "
                                             "Random(f'{seed}|{case_id}|run{n}')",
                                    "tie_break": "worst tied outcome"},
               "call_shape": "one text-only claude CLI call per vote via run_evals._claude "
                             "(fresh temp dir, isolation flags, no skill files, no tools)",
               "scope_note": "Description-only selection proxy on a small hand-written set; "
                             "not Claude Code's skill loader. Labels need maintainer review.",
               "summary": summary, "usage": dict(rv._USAGE), "cases": results}
    path = rv._write_results(Path(args.results_dir) if args.results_dir else None,
                             RESULTS_KIND, payload)
    print()
    _print_summary(summary)
    if path:
        print(f"results: {path.relative_to(REPO) if path.is_relative_to(REPO) else path}")
    if status != "measured":
        n_bad = sum(r["outcome"] == NO_ANSWER for r in results)
        print(f"{status.upper()}: {n_bad} of {len(results)} case(s) got no usable choice "
              "and are excluded from every rate.", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
