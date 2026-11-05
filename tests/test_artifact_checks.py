"""Artifact checks (scripts/artifact_checks.py) and their wiring into the behavioral runner.

Every check kind runs on real small files written here (PNG built with zlib/struct, a PDF with
a real xref table, a PPTX zip package, CSV/JSON/BibTeX/Markdown text). The runner wiring is
driven through ``run_evals._run_arm`` / ``_grade_case`` with a fake ``_claude_call`` that writes
(or fails to write) files into the arm's workspace, and a fake judge — no model, no network.
"""

from __future__ import annotations

import csv
import io
import json
import struct
import zipfile
import zlib
from pathlib import Path

import pytest

import artifact_checks as ac
import run_evals

REPO = Path(__file__).resolve().parent.parent


# --- real small files ------------------------------------------------------------------------
def png_bytes(width=4, height=3, dpi: float | None = 300, corrupt_crc=False) -> bytes:
    def chunk(kind: bytes, body: bytes) -> bytes:
        crc = zlib.crc32(kind + body) & 0xFFFFFFFF
        return struct.pack(">I", len(body)) + kind + body + struct.pack(
            ">I", crc ^ (1 if corrupt_crc and kind == b"IHDR" else 0))
    raw = b"".join(b"\x00" + bytes([200, 30, 30]) * width for _ in range(height))
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2,
                                                            0, 0, 0))
    if dpi:
        ppm = round(dpi / 0.0254)
        out += chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1))
    return out + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def pdf_bytes(pages=1) -> bytes:
    kids = " ".join(f"{3 + i} 0 R" for i in range(pages))
    objs = ["<< /Type /Catalog /Pages 2 0 R >>",
            f"<< /Type /Pages /Kids [{kids}] /Count {pages} >>"]
    objs += ["<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>"] * pages
    body, offsets = b"%PDF-1.4\n", []
    for n, o in enumerate(objs, 1):
        offsets.append(len(body))
        body += f"{n} 0 obj\n{o}\nendobj\n".encode()
    xref = len(body)
    body += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    body += "".join(f"{off:010d} 00000 n \n" for off in offsets).encode()
    body += (f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
             .encode())
    return body


def pptx_bytes(slides=("Results", "Methods")) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("ppt/presentation.xml", "<p:presentation/>")
        for i, text in enumerate(slides, 1):
            z.writestr(f"ppt/slides/slide{i}.xml", f"<p:sld><a:t>{text}</a:t></p:sld>")
    return buf.getvalue()


def write(ws: Path, rel: str, data: bytes | str) -> Path:
    p = ws / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return p


def run(ws: Path, path: str, typ: str, *checks: dict, **kw) -> dict:
    decl = {"path": path, "type": typ, "checks": list(checks)}
    assert ac.declaration_errors([decl]) == [], ac.declaration_errors([decl])
    return ac.check_artifact(ws, decl, **kw)


def verdicts(rec: dict) -> list[str]:
    return [c["verdict"] for c in rec["checks"]]


# --- every check kind, on real files ---------------------------------------------------------
def test_json_checks(tmp_path):
    write(tmp_path, "out/r.json", json.dumps({"summary": {"total": 24, "ok": True},
                                              "entries": [{"verdict": "verified"}] * 3}))
    rec = run(tmp_path, "out/r.json", "json",
              {"kind": "json_keys", "keys": ["summary", "entries"]},
              {"kind": "json_keys", "path": "summary", "keys": ["total"]},
              {"kind": "json_path_equals", "path": "summary.total", "value": 24},
              {"kind": "json_path_equals", "path": "entries.0.verdict", "value": "verified"},
              {"kind": "min_rows", "path": "entries", "min": 3, "max": 3},
              {"kind": "number_within", "path": "summary.total", "expected": 25,
               "tolerance": 1},
              {"kind": "contains_text", "text": ["nope", "verified"]})
    assert rec["exists"] and rec["parseable"] and verdicts(rec) == ["PASS"] * 9
    bad = run(tmp_path, "out/r.json", "json",
              {"kind": "json_keys", "keys": ["missing"]},
              {"kind": "json_path_equals", "path": "summary.total", "value": 23},
              {"kind": "json_path_equals", "path": "summary.ok", "value": 1},  # True is not 1
              {"kind": "json_path_equals", "path": "no.such.path", "value": 1},
              {"kind": "number_within", "path": "summary.total", "expected": 20,
               "tolerance": 3.9},
              {"kind": "min_rows", "path": "entries", "min": 4},
              {"kind": "contains_text", "text": "absent"})
    assert verdicts(bad)[2:] == ["FAIL"] * 7


def test_csv_checks(tmp_path):
    write(tmp_path, "s.csv", "column,dtype,missing_count\nod600,float64,12\nph,float64,5\n")
    rec = run(tmp_path, "s.csv", "csv",
              {"kind": "csv_columns", "columns": ["Column", "missing_count"]},
              {"kind": "min_rows", "min": 2, "max": 2},
              {"kind": "number_within", "column": "missing_count", "match": {"column": "ph"},
               "expected": 5, "tolerance": 0},
              {"kind": "number_within", "column": "missing_count", "row": 0, "expected": 12,
               "tolerance": 0},
              {"kind": "contains_text", "text": "od600"})
    assert verdicts(rec) == ["PASS"] * 7
    bad = run(tmp_path, "s.csv", "csv",
              {"kind": "csv_columns", "columns": ["n_missing"]},
              {"kind": "min_rows", "min": 3},
              {"kind": "number_within", "column": "missing_count", "match": {"column": "ph"},
               "expected": 4, "tolerance": 0.5},
              {"kind": "number_within", "column": "missing_count",
               "match": {"column": "notes"}, "expected": 0, "tolerance": 0},
              {"kind": "number_within", "column": "dtype", "row": 0, "expected": 0,
               "tolerance": 0})
    assert verdicts(bad)[2:] == ["FAIL"] * 5
    write(tmp_path, "ragged.csv", "a,b\n1,2\n3\n")
    assert run(tmp_path, "ragged.csv", "csv")["parseable"] is False


def test_png_checks_decode_the_pixel_stream(tmp_path):
    write(tmp_path, "f.png", png_bytes(1200, 900, dpi=300))
    rec = run(tmp_path, "f.png", "png", {"kind": "png_dpi", "expected": 300, "tolerance": 1},
              {"kind": "png_min_size", "min_width": 900, "min_height": 600})
    assert verdicts(rec) == ["PASS"] * 4 and "1200x900" in rec["checks"][3]["detail"]
    write(tmp_path, "low.png", png_bytes(300, 200, dpi=72))
    low = run(tmp_path, "low.png", "png", {"kind": "png_dpi", "expected": 300, "tolerance": 1},
              {"kind": "png_min_size", "min_width": 900, "min_height": 600})
    assert verdicts(low) == ["PASS", "PASS", "FAIL", "FAIL"]
    write(tmp_path, "nodpi.png", png_bytes(dpi=None))
    assert verdicts(run(tmp_path, "nodpi.png", "png",
                        {"kind": "png_dpi", "expected": 300, "tolerance": 1}))[2] == "FAIL"
    write(tmp_path, "crc.png", png_bytes(corrupt_crc=True))
    write(tmp_path, "trunc.png", png_bytes()[:-20])
    write(tmp_path, "fake.png", b"\x89PNG\r\n\x1a\n" + b"x" * 40)
    for name in ("crc.png", "trunc.png", "fake.png"):
        assert run(tmp_path, name, "png")["parseable"] is False, name


def test_pdf_checks(tmp_path):
    write(tmp_path, "a.pdf", pdf_bytes(pages=2))
    rec = run(tmp_path, "a.pdf", "pdf", {"kind": "pdf_min_pages", "min": 2})
    assert verdicts(rec) == ["PASS"] * 3
    assert verdicts(run(tmp_path, "a.pdf", "pdf", {"kind": "pdf_min_pages", "min": 3}))[2] == "FAIL"
    write(tmp_path, "cut.pdf", pdf_bytes()[:-40])  # truncated: no %%EOF
    write(tmp_path, "notpdf.pdf", "just text that claims to be a PDF")
    assert run(tmp_path, "cut.pdf", "pdf")["parseable"] is False
    assert run(tmp_path, "notpdf.pdf", "pdf")["parseable"] is False


def test_pptx_checks(tmp_path):
    write(tmp_path, "d.pptx", pptx_bytes())
    rec = run(tmp_path, "d.pptx", "pptx", {"kind": "pptx_min_slides", "min": 2},
              {"kind": "contains_text", "text": "methods"})
    assert verdicts(rec) == ["PASS"] * 4
    assert verdicts(run(tmp_path, "d.pptx", "pptx",
                        {"kind": "pptx_min_slides", "min": 3}))[2] == "FAIL"
    write(tmp_path, "zip.pptx", b"PK\x03\x04 not really a zip")
    assert run(tmp_path, "zip.pptx", "pptx")["parseable"] is False


def test_text_and_bib_checks(tmp_path):
    write(tmp_path, "r.md", "# Report\n\nod600 missing in 12 rows\n")
    md = run(tmp_path, "r.md", "md", {"kind": "min_rows", "min": 2},
             {"kind": "contains_text", "text": "OD600"})
    assert verdicts(md) == ["PASS"] * 4
    write(tmp_path, "empty.txt", "   \n")
    assert run(tmp_path, "empty.txt", "txt")["parseable"] is False
    write(tmp_path, "a.bib", "@article{a, title={X}, pages={1--2}}\n@string{j = {J}}\n"
                             "@book{b, title={Y}}\n")
    bib = run(tmp_path, "a.bib", "bib", {"kind": "min_rows", "min": 2, "max": 2},
              {"kind": "contains_text", "text": "1--2"})
    assert verdicts(bib) == ["PASS"] * 4, "@string is not an entry"
    write(tmp_path, "unbalanced.bib", "@article{a, title={X}\n")
    assert run(tmp_path, "unbalanced.bib", "bib")["parseable"] is False


# --- missing / unsafe / stored ---------------------------------------------------------------
def test_missing_file_fails_every_declared_check(tmp_path):
    rec = run(tmp_path, "out/x.json", "json", {"kind": "json_keys", "keys": ["a"]})
    assert rec["exists"] is False and rec["sha256"] is None and rec["stored_as"] is None
    assert verdicts(rec) == ["FAIL", "FAIL", "FAIL"]
    assert all(c["detail"] == "file missing" for c in rec["checks"])


def test_symlinks_and_directories_are_not_followed(tmp_path):
    secret = tmp_path / "outside.json"
    secret.write_text('{"a": 1}')
    ws = tmp_path / "ws"
    (ws / "out").mkdir(parents=True)
    (ws / "out" / "x.json").symlink_to(secret)
    (ws / "out" / "d.json").mkdir()
    for path in ("out/x.json", "out/d.json"):
        rec = run(ws, path, "json", {"kind": "json_keys", "keys": ["a"]})
        assert rec["exists"] and verdicts(rec) == ["PASS", "FAIL", "FAIL"], path


def test_artifacts_are_hashed_and_copied_into_the_results_dir(tmp_path):
    ws, results = tmp_path / "ws", tmp_path / "results"
    data = png_bytes()
    write(ws, "out/f.png", data)
    store = results / "artifacts" / "STAMP" / "case" / "skilled" / "run-1"
    rec = run(ws, "out/f.png", "png", store_dir=store, results_dir=results)
    assert rec["bytes"] == len(data)
    assert rec["sha256"] == __import__("hashlib").sha256(data).hexdigest()
    assert rec["stored_as"] == "artifacts/STAMP/case/skilled/run-1/out/f.png"
    assert (results / rec["stored_as"]).read_bytes() == data


def test_ungraded_runs_record_but_do_not_score(tmp_path):
    write(tmp_path, "f.png", png_bytes())
    rec = run(tmp_path, "f.png", "png", graded=False)
    assert rec["exists"] and set(verdicts(rec)) == {"NA"}


def test_clear_artifacts_removes_only_declared_outputs(tmp_path):
    write(tmp_path, "out/f.png", png_bytes())
    write(tmp_path, "out/keep.txt", "x")
    ac.clear_artifacts(tmp_path, [{"path": "out/f.png", "type": "png"},
                                  {"path": "../escape", "type": "txt"}])
    assert not (tmp_path / "out" / "f.png").exists() and (tmp_path / "out" / "keep.txt").exists()


# --- declarations and schema -------------------------------------------------------------------
@pytest.mark.parametrize("decl, needle", [
    ({"path": "/abs.json", "type": "json"}, "relative path"),
    ({"path": "../up.json", "type": "json"}, "relative path"),
    ({"path": "a.json", "type": "xlsx"}, "type"),
    ({"path": "a.png", "type": "png", "checks": [{"kind": "json_keys", "keys": ["a"]}]},
     "does not apply"),
    ({"path": "a.csv", "type": "csv", "checks": [{"kind": "number_within", "column": "c",
                                                  "expected": 1, "tolerance": 0}]}, "row"),
    ({"path": "a.json", "type": "json", "checks": [{"kind": "number_within", "path": "x",
                                                    "expected": 1, "tolerance": -1}]},
     "tolerance"),
    ({"path": "a.json", "type": "json", "checks": [{"kind": "png_dpi"}]}, "needs"),
    ({"path": "a.md", "type": "md", "checks": [{"kind": "min_rows", "min": 1, "bogus": 2}]},
     "does not take"),
])
def test_bad_declarations_are_rejected(decl, needle):
    errs = ac.declaration_errors([decl])
    assert errs and any(needle in e for e in errs), errs
    data = {"skill": "x", "evals": [{"id": "a", "prompt": "p", "expected_output": "e",
                                     "artifact_checks": [decl]}]}
    assert run_evals._structural_errors(data), "the built-in validator must reject it too"


def test_shipped_artifact_checks_validate_with_both_validators():
    names = ["alterlab-matplotlib", "alterlab-citation-mgmt", "alterlab-eda"]
    dirs = [d for d in run_evals.skill_dirs() if d.name in names]
    assert len(dirs) == 3
    for d in dirs:
        data = json.loads(run_evals.eval_path(d).read_text(encoding="utf-8"))
        assert any(e.get("artifact_checks") for e in data["evals"]), d.name
        assert run_evals._structural_errors(data) == [], d.name
        assert run_evals.validate_skill(d).ok, run_evals.validate_skill(d).errors
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((REPO / "docs" / "evals.schema.json").read_text(encoding="utf-8"))
    for d in dirs:
        jsonschema.Draft202012Validator(schema).validate(
            json.loads(run_evals.eval_path(d).read_text(encoding="utf-8")))


def _shipped(skill: str, eval_id: str) -> tuple[dict, Path]:
    d = next(x for x in run_evals.skill_dirs() if x.name == skill)
    data = json.loads(run_evals.eval_path(d).read_text(encoding="utf-8"))
    return next(e for e in data["evals"] if e["id"] == eval_id), d / "evals"


def test_eda_expected_values_match_the_fixture(tmp_path):
    """The eval author's expected missing counts are right for the shipped fixture: a correct
    column summary computed from it passes, an off-by-one count fails."""
    e, evals_dir = _shipped("alterlab-eda", "csv-tabular-eda")
    with open(evals_dir / "fixtures" / "experiment_results.csv", newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    lines = ["column,dtype,missing_count"] + [
        f"{c},object,{sum(1 for r in data if not r[i].strip())}" for i, c in enumerate(header)]
    write(tmp_path, "out/column_summary.csv", "\n".join(lines) + "\n")
    recs = ac.check_artifacts(tmp_path, e["artifact_checks"])
    assert set(ac.verdicts(recs)) == {"PASS"}
    write(tmp_path, "out/column_summary.csv", "\n".join(lines).replace("od600,object,12",
                                                                       "od600,object,11"))
    assert "FAIL" in ac.verdicts(ac.check_artifacts(tmp_path, e["artifact_checks"]))


def test_bib_checks_separate_a_cleaned_file_from_the_messy_input(tmp_path):
    e, evals_dir = _shipped("alterlab-citation-mgmt", "format-deduplicate-bibtex")
    messy = (evals_dir / "fixtures" / "messy.bib").read_text(encoding="utf-8")
    write(tmp_path, "out/cleaned.bib", messy)  # handing back the input unchanged
    assert "FAIL" in ac.verdicts(ac.check_artifacts(tmp_path, e["artifact_checks"]))
    cleaned = """@book{braun2022thematic,
  author = {Braun, Virginia and Clarke, Victoria},
  title = {{Thematic Analysis: A Practical Guide}},
  publisher = {SAGE}, year = {2022}}
@article{Wisniewski_2020,
  author = {Wisniewski, Benedikt and Zierer, Klaus and Hattie, John},
  title = {{The Power of Feedback Revisited}}, journal = {Frontiers in Psychology},
  volume = {10}, pages = {3087}, year = {2020}, doi = {10.3389/fpsyg.2019.03087}}
@article{hattie2007,
  author = {Hattie, John and Timperley, Helen}, title = {{The Power of Feedback}},
  journal = {Review of Educational Research}, year = {2007}, pages = {81--112}}
@article{kluger1996,
  author = {Kluger, Avraham N. and DeNisi, Angelo}, title = {{The Effects of Feedback}},
  journal = {Psychological Bulletin}, year = {1996}, pages = {254--284}}
"""
    write(tmp_path, "out/cleaned.bib", cleaned)
    assert set(ac.verdicts(ac.check_artifacts(tmp_path, e["artifact_checks"]))) == {"PASS"}


def test_checks_never_reach_the_arms(tmp_path):
    """Expected values live in evals/evals.json, which prepare_workspace never copies; the
    prompt note names paths, types and descriptions only."""
    e, evals_dir = _shipped("alterlab-eda", "csv-tabular-eda")
    skill_dir = evals_dir.parent
    fixtures = run_evals.prepare_workspace(tmp_path / "skilled", e, evals_dir, skill_dir)
    files = [p.relative_to(tmp_path / "skilled").as_posix()
             for p in (tmp_path / "skilled").rglob("*") if p.is_file()]
    assert files and not any(f.startswith("skill/evals") for f in files)
    prompt = run_evals.build_prompt(e, fixtures)
    assert "out/column_summary.csv" in prompt and "missing_count" in prompt
    assert "number_within" not in prompt and "expected" not in prompt and "tolerance" not in prompt


# --- runner wiring -------------------------------------------------------------------------------
CASE = {"id": "plot", "prompt": "Make the figure and save it.",
        "expected_output": "Makes the GOOD figure.",
        "assertions": [{"type": "should_trigger", "value": True}],
        "artifact_checks": [{"path": "out/fig.png", "type": "png",
                             "checks": [{"kind": "png_dpi", "expected": 300, "tolerance": 1}]}]}


def _fake_judge(prompt, model, timeout, system=None):
    if "ENGAGED:" in prompt:
        return "ENGAGED: YES"
    return "VERDICT: PASS" if "GOOD" in prompt.split("RESPONSE:")[-1] else "VERDICT: FAIL"


def _fake_call(writes):
    """A _claude_call stand-in: on call N, write writes[N] (bytes or None) to out/fig.png."""
    seen = {"n": 0, "saw_stale": []}

    def call(prompt, model, timeout, system=None, cwd=None, extra_args=None):
        target = Path(cwd) / "out" / "fig.png"
        seen["saw_stale"].append(target.exists())
        data = writes[seen["n"]]
        seen["n"] += 1
        if data is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return run_evals.CallResult("GOOD figure saved to out/fig.png", "answer")
    return call, seen


def _arm(tmp_path, monkeypatch, writes, runs=1, skilled=True):
    call, seen = _fake_call(writes)
    monkeypatch.setattr(run_evals, "_claude_call", call)
    monkeypatch.setattr(run_evals, "_claude", _fake_judge)
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    res = run_evals._run_arm("p", "m", 30, runs, ws, CASE, "alterlab-x", CASE["expected_output"],
                             "SKILL" if skilled else None, skilled,
                             artifact_dir=tmp_path / "results" / "artifacts" / "S" / "c" / "arm",
                             results_dir=tmp_path / "results")
    return res, seen


def test_run_arm_passes_when_the_declared_file_is_written(tmp_path, monkeypatch):
    res, _ = _arm(tmp_path, monkeypatch, [png_bytes(dpi=300)])
    assert res["outcome"] == "PASS"
    assert res["dimensions"] == {"substantive": "PASS", "routing": "PASS",
                                 "skill_vocabulary": None, "artifacts": "PASS"}
    art = res["runs"][0]["artifacts"][0]
    assert art["stored_as"] == "artifacts/S/c/arm/run-1/out/fig.png"
    assert (tmp_path / "results" / art["stored_as"]).exists()


def test_run_arm_fails_when_the_answer_only_claims_the_file(tmp_path, monkeypatch):
    """The answer text says the file was saved and the rubric judge PASSes it, but no file
    exists: that is never completed artifact work."""
    res, _ = _arm(tmp_path, monkeypatch, [None])
    assert res["dimensions"]["substantive"] == "PASS"
    assert res["dimensions"]["artifacts"] == "FAIL" and res["outcome"] == "FAIL"
    assert res["runs"][0]["artifacts"][0]["exists"] is False


def test_run_arm_fails_a_wrong_dpi(tmp_path, monkeypatch):
    res, _ = _arm(tmp_path, monkeypatch, [png_bytes(dpi=72)], skilled=False)
    assert res["dimensions"]["artifacts"] == "FAIL" and res["dimensions"]["routing"] is None


def test_a_later_run_is_never_credited_with_an_earlier_runs_file(tmp_path, monkeypatch):
    res, seen = _arm(tmp_path, monkeypatch, [png_bytes(), None, None], runs=3)
    assert seen["saw_stale"] == [False, False, False], "outputs are cleared before each run"
    per_run = [r["artifacts"][0]["exists"] for r in res["runs"]]
    assert per_run == [True, False, False] and res["dimensions"]["artifacts"] == "FAIL"


def test_grade_case_stores_both_arms_under_the_run_stamp(tmp_path, monkeypatch):
    skill = tmp_path / "skills" / "alterlab-x"
    (skill / "evals").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: alterlab-x\n---\nbody\n")
    (skill / "evals" / "evals.json").write_text(json.dumps({"skill": "alterlab-x",
                                                             "evals": [CASE]}))
    call, _ = _fake_call([png_bytes(), png_bytes(dpi=96)])
    monkeypatch.setattr(run_evals, "_claude_call", call)
    monkeypatch.setattr(run_evals, "_claude", _fake_judge)
    cases, _ = run_evals._behavioral_cases(None, None, skill)
    rec = run_evals._grade_case(cases[0], "m", 30, 1, results_dir=tmp_path / "res",
                                run_stamp="STAMP")
    base = tmp_path / "res" / "artifacts" / "STAMP" / "alterlab-x__plot"
    assert (base / "skilled" / "run-1" / "out" / "fig.png").exists()
    assert (base / "bare" / "run-1" / "out" / "fig.png").exists()
    assert rec["skilled"]["dimensions"]["artifacts"] == "PASS"
    assert rec["bare"]["dimensions"]["artifacts"] == "FAIL"
    assert len(rec["hashes"]["rubric_sha256"]) == 64
