"""scripts/activation_eval.py — the hand-labelled skill-activation set.

No model calls: the CLI call (``ask_model``), the CLI probe and the run metadata are replaced.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import activation_eval as ae  # noqa: E402
import run_evals as rv  # noqa: E402

CATALOG = rv.skill_catalog()


@pytest.fixture(scope="module")
def case_data():
    return ae.load_and_validate(ae.CASES_PATH, ae.REPO, CATALOG)


def _case(cid, data):
    return next(c for c in data["cases"] if c["id"] == cid)


def _mk(**kw):
    base = {"id": "x", "prompt": "p", "language": "en", "kind": "clear",
            "installed_profile": "core-only", "expected": "alterlab-deep-research",
            "acceptable": [], "distractors": [], "note": "n"}
    base.update(kw)
    return base


# --- Profiles from the real manifests ----------------------------------------------------
def test_real_profiles_follow_bundle_dependencies(case_data):
    _, profiles = case_data
    full = set(profiles["full"]["skills"])
    assert full == set(CATALOG), "alterlab-complete must install every skill in the catalog"
    core_dirs = {p.parent.name for p in (REPO / "skills" / "core").glob("*/SKILL.md")}
    assert set(profiles["core-only"]["skills"]) == core_dirs
    ess = set(profiles["essentials"]["skills"])
    assert {"alterlab-citation-verifier", "alterlab-pubmed", "alterlab-research-workflows",
            "alterlab-test-selection-guard", "alterlab-citation-mgmt"} <= ess
    assert not ess & {"alterlab-dergipark", "alterlab-matplotlib", "alterlab-rdkit"}
    assert "alterlab-essentials" in profiles["essentials"]["plugins"]
    tr = profiles["turkish-academia+core"]["skills"]
    assert len(tr) == 23 and "alterlab-docentlik-eligibility" in tr
    assert "alterlab-paper-reviewer" not in profiles["visualization-only"]["skills"]


def test_workflows_plugin_pulls_in_core_dependency():
    prof = ae.compute_profiles({"wf": {"plugins": ["alterlab-workflows"]}}, ae.load_plugins())
    assert prof["wf"]["plugins"] == ["alterlab-core", "alterlab-workflows"]
    assert "alterlab-deep-research" in prof["wf"]["skills"]


def _fake_repo(tmp_path: Path, *, bundle_deps=("plug-b",), b_skill_dir="beta") -> Path:
    def skill(d: Path, name: str):
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: \"d\"\n---\n# x\n")
    skill(tmp_path / "skills" / "a" / "alpha", "alterlab-alpha")
    skill(tmp_path / "skills" / "b" / "beta", "alterlab-beta")
    (tmp_path / "skills" / "b" / ".claude-plugin").mkdir(parents=True)
    (tmp_path / "skills" / "b" / ".claude-plugin" / "plugin.json").write_text(json.dumps(
        {"name": "plug-b", "skills": [f"./{b_skill_dir}"], "dependencies": ["plug-a"]}))
    (tmp_path / "bundle" / ".claude-plugin").mkdir(parents=True)
    (tmp_path / "bundle" / ".claude-plugin" / "plugin.json").write_text(json.dumps(
        {"name": "bundle", "dependencies": list(bundle_deps)}))
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text(json.dumps({"plugins": [
        {"name": "plug-a", "source": "./skills/a", "strict": False, "skills": ["./alpha"]},
        {"name": "plug-b", "source": "./skills/b", "strict": True},
        {"name": "bundle", "source": "./bundle", "strict": True}]}))
    return tmp_path


def test_profiles_from_fake_manifests_resolve_transitively(tmp_path):
    plugins = ae.load_plugins(_fake_repo(tmp_path))
    assert plugins["plug-a"]["skills"] == ["alterlab-alpha"]
    assert plugins["bundle"]["skills"] == []
    prof = ae.compute_profiles({"b": {"plugins": ["bundle"]}, "a": {"plugins": ["plug-a"]}},
                               plugins)
    assert prof["b"]["skills"] == ["alterlab-alpha", "alterlab-beta"]
    assert prof["b"]["owner"] == {"alterlab-alpha": "plug-a", "alterlab-beta": "plug-b"}
    assert prof["a"]["skills"] == ["alterlab-alpha"]


def test_unknown_plugin_and_missing_skill_dir_fail_loudly(tmp_path):
    plugins = ae.load_plugins(_fake_repo(tmp_path / "one", bundle_deps=("plug-zzz",)))
    with pytest.raises(ae.CaseFileError, match="unknown plugin 'plug-zzz'"):
        ae.compute_profiles({"x": {"plugins": ["bundle"]}}, plugins)
    with pytest.raises(ae.CaseFileError, match="has no SKILL.md"):
        ae.load_plugins(_fake_repo(tmp_path / "two", b_skill_dir="gone"))


# --- Case-file validation ----------------------------------------------------------------
def test_shipped_case_file_is_valid_and_covers_the_matrix(case_data):
    data, _ = case_data
    cases = data["cases"]
    assert 30 <= len(cases) <= 45
    assert {c["kind"] for c in cases} == set(ae.KINDS)
    assert {c["language"] for c in cases} == {"en", "tr"}
    assert sum(c["language"] == "tr" for c in cases) >= 8
    assert any(c["expected"] == "none" for c in cases)
    assert any(c["kind"] == "unavailable" and c["acceptable"] for c in cases)


def test_every_label_names_a_real_skill(case_data):
    data, _ = case_data
    for c in data["cases"]:
        for n in [c["expected"], *c["acceptable"], *c["distractors"]]:
            assert n == "none" or n in CATALOG, (c["id"], n)


def test_unavailable_cases_really_exclude_the_expected_skill(case_data):
    data, profiles = case_data
    unavailable = [c for c in data["cases"] if c["kind"] == "unavailable"]
    assert len(unavailable) >= 4
    for c in unavailable:
        prof = profiles[c["installed_profile"]]
        assert c["expected"] not in prof["skills"], c["id"]
        shown = {x["name"] for x in ae.build_candidates(c, prof, 1)}
        assert c["expected"] not in shown, c["id"]
        assert set(c["acceptable"]) <= shown, c["id"]


@pytest.mark.parametrize("mutate, message", [
    (lambda c: c.update(expected="alterlab-does-not-exist"), "unknown skill 'alterlab-does-not"),
    (lambda c: c.update(acceptable=["alterlab-nope"]), "acceptable names unknown skill"),
    (lambda c: c.update(distractors=["alterlab-nope"]), "distractors names unknown skill"),
    (lambda c: c.update(kind="unavailable", expected="alterlab-deep-research"),
     "IS installed"),
    (lambda c: c.update(expected="alterlab-dergipark"), "not installed in profile"),
    (lambda c: c.update(kind="ambiguous", acceptable=[]), "needs at least one acceptable"),
    (lambda c: c.update(kind="distractor", distractors=[]), "needs at least one explicit"),
    (lambda c: c.update(distractors=["alterlab-matplotlib"]), "not installed in the profile"),
    (lambda c: c.update(acceptable=["alterlab-rdkit"]), "can never be picked"),
    (lambda c: c.update(installed_profile="nope"), "unknown installed_profile"),
    (lambda c: c.update(language="de"), "language must be"),
    (lambda c: c.pop("note"), "missing ['note']"),
])
def test_invalid_cases_are_rejected(case_data, mutate, message):
    _, profiles = case_data
    case = _mk()
    mutate(case)
    errs = ae.validate_cases({"cases": [case]}, CATALOG, profiles)
    assert any(message in e for e in errs), errs


def test_duplicate_ids_rejected(case_data):
    _, profiles = case_data
    errs = ae.validate_cases({"cases": [_mk(), _mk()]}, CATALOG, profiles)
    assert any("duplicate id" in e for e in errs)


def test_main_exits_64_on_invalid_case_file(tmp_path, capsys):
    data = json.loads(ae.CASES_PATH.read_text(encoding="utf-8"))
    bad = copy.deepcopy(data)
    bad["cases"][0]["expected"] = "alterlab-typo-skill"
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    assert ae.main(["--cases", str(path), "--estimate"]) == 64
    assert "alterlab-typo-skill" in capsys.readouterr().err


# --- Candidates ---------------------------------------------------------------------------
def test_candidates_are_deterministic_and_seeded(case_data):
    data, profiles = case_data
    c = _case("distractor-meta-analysis", data)
    prof = profiles[c["installed_profile"]]
    a = ae.build_candidates(c, prof, 7)
    assert a == ae.build_candidates(c, prof, 7)
    names = [x["name"] for x in a]
    assert names == sorted(names)
    assert ae.shuffled(names, 7, c["id"], 1) == ae.shuffled(names, 7, c["id"], 1)
    assert ae.shuffled(names, 7, c["id"], 1) != ae.shuffled(names, 8, c["id"], 1)
    assert ae.shuffled(names, 7, c["id"], 1) != ae.shuffled(names, 7, c["id"], 2)
    assert sorted(ae.shuffled(names, 7, c["id"], 2)) == names


def test_large_profile_subset_policy(case_data):
    data, profiles = case_data
    c = _case("distractor-meta-analysis", data)
    prof = profiles["full"]
    cands = {x["name"]: x["why"] for x in ae.build_candidates(c, prof, 3)}
    assert len(prof["skills"]) > ae.FULL_LIST_MAX and len(cands) < len(prof["skills"])
    assert "expected-plugin" in cands["alterlab-meta-analysis"]
    assert "explicit-distractor" in cands["alterlab-literature-review"]
    assert "explicit-distractor" in cands["alterlab-statistical-analysis"]
    ssci = [s for s in prof["skills"] if prof["owner"][s] == "alterlab-social-science-workflow"]
    assert set(ssci) <= set(cands)
    core = [s for s in prof["skills"] if prof["owner"][s] == "alterlab-core"]
    assert set(core) <= set(cands)
    assert sum("background-sample" in w for w in cands.values()) == ae.BACKGROUND_SAMPLE


def test_small_profile_shows_every_installed_skill(case_data):
    data, profiles = case_data
    c = _case("tr-docentlik-prescreen", data)
    cands = ae.build_candidates(c, profiles["turkish-academia+core"], 1)
    assert [x["name"] for x in cands] == profiles["turkish-academia+core"]["skills"]


# --- Outcomes -----------------------------------------------------------------------------
@pytest.mark.parametrize("case, choice, outcome", [
    (_mk(expected="alterlab-seaborn"), "alterlab-seaborn", "correct"),
    (_mk(kind="ambiguous", expected="alterlab-scientific-viz",
         acceptable=["alterlab-matplotlib"]), "alterlab-matplotlib", "acceptable_alternate"),
    (_mk(expected="alterlab-matplotlib", distractors=["alterlab-seaborn"]),
     "alterlab-seaborn", "wrong_skill"),
    (_mk(expected="alterlab-matplotlib"), "none", "missed"),
    (_mk(expected="none"), "alterlab-tr-academic-style", "false_activation"),
    (_mk(expected="none"), "none", "correct"),
    (_mk(kind="unavailable", expected="alterlab-pubmed"), "none",
     "correct_unavailable_handling"),
    (_mk(kind="unavailable", expected="alterlab-pubmed", acceptable=["alterlab-deep-research"]),
     "alterlab-deep-research", "acceptable_alternate"),
    (_mk(kind="unavailable", expected="alterlab-pubmed"), "alterlab-trdizin",
     "false_activation"),
    (_mk(kind="unavailable", expected="alterlab-pubmed"), "alterlab-pubmed",
     "false_activation"),  # an off-list pick of the uninstalled skill is not credit
    (_mk(), None, "no_answer"),
])
def test_classify_every_outcome(case, choice, outcome):
    assert ae.classify(case, choice) == outcome


def test_majority_ties_take_the_worse_outcome():
    case = _mk(expected="alterlab-matplotlib")
    assert ae.majority(case, ["alterlab-matplotlib", "alterlab-seaborn"])[:2] == \
        ("alterlab-seaborn", True)
    assert ae.majority(case, ["alterlab-matplotlib", "none", "alterlab-matplotlib"])[:2] == \
        ("alterlab-matplotlib", False)
    assert ae.majority(case, [None, "none", None]) == ("none", False, {"none": 1})
    assert ae.majority(case, [None, None]) == (None, False, {})


def test_parse_choice_handles_markup_off_list_and_no_answer():
    shown = ["alterlab-seaborn", "alterlab-plotly"]
    assert ae.parse_choice("CHOICE: **alterlab-plotly**\nok", shown)["choice"] == "alterlab-plotly"
    v = ae.parse_choice("CHOICE: alterlab-pubmed\nbecause", shown)
    assert v["choice"] == "alterlab-pubmed" and v["off_list"]
    assert ae.parse_choice("CHOICE: None — nothing fits", shown)["choice"] == "none"
    assert ae.parse_choice("I would use seaborn", shown)["status"] == "unparseable"
    assert ae.parse_choice("<no-answer> TIMEOUT after 5s", shown)["status"] == "no_answer"


def test_summary_denominators_are_explicit():
    rows = [
        {"kind": "clear", "language": "en", "installed_profile": "full", "expected": "x",
         "outcome": "correct"},
        {"kind": "clear", "language": "en", "installed_profile": "full", "expected": "x",
         "outcome": "acceptable_alternate"},
        {"kind": "clear", "language": "tr", "installed_profile": "full", "expected": "x",
         "outcome": "no_answer"},
        {"kind": "unavailable", "language": "tr", "installed_profile": "core-only",
         "expected": "x", "outcome": "correct_unavailable_handling"},
        {"kind": "distractor", "language": "en", "installed_profile": "core-only",
         "expected": "none", "outcome": "false_activation"},
    ]
    s = ae.summarize(rows)
    o = s["overall"]
    assert o["cases"] == 5 and o["answered"] == 4
    assert o["success"] == {"n": 3, "of": 4, "rate": 0.75}
    assert o["strict"] == {"n": 2, "of": 4, "rate": 0.5}
    assert s["by_kind"]["clear"]["answered"] == 2
    assert s["by_language"]["tr"]["success"] == {"n": 1, "of": 1, "rate": 1.0}
    assert s["by_profile"]["core-only"]["counts"]["false_activation"] == 1
    assert s["by_expectation"]["none"]["success"]["n"] == 0
    assert set(s["by_expectation"]) == {"installed-skill", "unavailable", "none"}
    empty = ae.summarize([rows[2]])["overall"]
    assert empty["answered"] == 0 and empty["success"]["rate"] is None


# --- CLI: dry run, estimate, live (faked) --------------------------------------------------
def _no_calls(*_a, **_k):
    raise AssertionError("no model call expected")


def test_estimate_counts_cases_times_runs(monkeypatch, capsys, case_data):
    monkeypatch.setattr(ae, "ask_model", _no_calls)
    data, _ = case_data
    n = len(data["cases"])
    assert ae.main(["--estimate"]) == 0
    assert f"{n} case(s) x 3 run(s) = {3 * n} claude CLI call(s)" in capsys.readouterr().out
    n_unavail = sum(c["kind"] == "unavailable" for c in data["cases"])
    assert ae.main(["--estimate", "--kind", "unavailable", "--runs", "5"]) == 0
    assert f"= {5 * n_unavail} claude" in capsys.readouterr().out
    assert ae.main(["--estimate", "--language", "tr", "--limit", "2", "--runs", "1"]) == 0
    assert "2 case(s) x 1 run(s) = 2" in capsys.readouterr().out
    assert ae.main(["--estimate", "--case", "nonexistent-case"]) == 2


def test_dry_run_prints_prompts_and_candidates_without_calls(monkeypatch, capsys):
    monkeypatch.setattr(ae, "ask_model", _no_calls)
    monkeypatch.setattr(ae, "_cli_available", lambda: False)
    assert ae.main(["--dry-run", "--case", "unavailable-tr-dergipark-core"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "profile=core-only" in out
    assert "DergiPark'taki" in out
    assert "- alterlab-deep-research:" in out
    assert "- alterlab-dergipark:" not in out


def test_live_run_blocked_without_cli(monkeypatch, tmp_path):
    monkeypatch.setattr(ae, "ask_model", _no_calls)
    monkeypatch.setattr(ae, "_cli_available", lambda: False)
    assert ae.main(["--case", "clear-seaborn-violin", "--results-dir", str(tmp_path)]) == 2
    assert not list(tmp_path.iterdir())


@pytest.fixture
def fake_live(monkeypatch):
    monkeypatch.setattr(ae, "_cli_available", lambda: True)
    monkeypatch.setattr(rv, "configure_confinement", lambda request="auto": "none")
    monkeypatch.setattr(rv, "_run_metadata", lambda kind, model, runs, timeout: {
        "schema_version": 1, "kind": kind, "model": model, "runs_per_arm": runs,
        "isolation": {"cli_flags": ["--safe-mode"], "confinement": {"mode": "none"}}})
    prompts: list[str] = []

    def install(answer):
        def fake(prompt, model, timeout):
            prompts.append(prompt)
            return answer(prompt)
        monkeypatch.setattr(ae, "ask_model", fake)
        return prompts
    return install


def _listed(prompt: str) -> list[str]:
    return re.findall(r"^- (alterlab-[a-z0-9-]+):", prompt, re.MULTILINE)


def test_live_run_records_candidates_votes_and_outcomes(fake_live, tmp_path, case_data):
    data, _ = case_data
    by_req = {c["prompt"]: c for c in data["cases"]}

    def answer(prompt):  # always pick the labelled skill, even when it is not installed
        req = prompt.split("USER REQUEST:\n", 1)[1].split("\n\nINSTALLED SKILLS", 1)[0]
        return f"CHOICE: {by_req[req]['expected']}\nreason"
    prompts = fake_live(answer)
    code = ae.main(["--language", "tr", "--runs", "3", "--seed", "11",
                    "--results-dir", str(tmp_path)])
    assert code == 0
    (path,) = tmp_path.glob("activation-set-*.json")
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert rec["schema_version"] == 1 and rec["kind"] == "activation-set"
    assert rec["status"] == "measured" and rec["runs"] == 3 and rec["seed"] == 11
    assert rec["case_set"]["selected"] == len(rec["cases"]) == len(prompts) // 3
    for c in rec["cases"]:
        names = [x["name"] for x in c["candidates"]]
        assert len(c["votes"]) == 3
        for v in c["votes"]:
            assert sorted(v["order"]) == names
        if c["kind"] == "unavailable":  # picked an uninstalled (never shown) skill
            assert c["outcome"] == "false_activation" and c["off_list"]
        elif c["expected"] == "none":
            assert c["outcome"] == "correct"
        else:
            assert c["outcome"] == "correct" and c["choice"] == c["expected"]
    shown = [_listed(p) for p in prompts]
    recorded = [v["order"] for c in rec["cases"] for v in c["votes"]]
    assert shown == recorded
    o = rec["summary"]["overall"]
    assert o["answered"] == o["cases"] == len(rec["cases"])


def test_live_run_partial_and_blocked_exit_codes(fake_live, tmp_path):
    def answer(prompt):
        if "TR Dizin" in prompt.split("INSTALLED SKILLS", 1)[0]:
            return "<no-answer> TIMEOUT after 300s"
        return "CHOICE: none\nnothing fits"
    fake_live(answer)
    args = ["--case", "tr-trdizin-journal-status", "--case", "none-offtopic-travel",
            "--runs", "1", "--results-dir", str(tmp_path / "p")]
    assert ae.main(args) == 3
    rec = json.loads(next((tmp_path / "p").glob("*.json")).read_text(encoding="utf-8"))
    assert rec["status"] == "partial"
    outcomes = {c["id"]: c["outcome"] for c in rec["cases"]}
    assert outcomes == {"tr-trdizin-journal-status": "no_answer",
                        "none-offtopic-travel": "correct"}
    assert rec["summary"]["overall"]["answered"] == 1

    fake_live(lambda p: "<no-answer> claude CLI exited 1: auth")
    assert ae.main(["--kind", "clear", "--runs", "1", "--results-dir",
                    str(tmp_path / "b")]) == 2
    rec = json.loads(next((tmp_path / "b").glob("*.json")).read_text(encoding="utf-8"))
    assert rec["status"] == "blocked"
