"""Fault-injection tests for the plugin dynamic workflows (``skills/workflows/workflows/*.js``).

Each test runs a workflow through ``scripts/workflow_dryrun.mjs`` with a *scenario*: fixtures that
pin what chosen agents return, plus injected faults (an agent that throws, returns null, omits items,
repeats or invents ids, fails to write the report, or reports the file missing). The assertions
check the workflow's returned payload: incomplete, failed, or weakly supported work must never be
counted or labelled as completed, verified, or validated, and a report path is returned only when
the file was read back from disk.

Skipped when Node.js is not installed.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DRYRUN = REPO_ROOT / "scripts" / "workflow_dryrun.mjs"
WORKFLOWS = REPO_ROOT / "skills" / "workflows" / "workflows"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="Node.js not installed")


def run(name: str, args: object, rules: list[dict], capture: str | None = None, mode: str = "a", script: Path | None = None) -> dict:
    """Dry-run a workflow under a scenario; return the harness output (with ``result``).

    ``script`` overrides the plugin path, for the maintainer workflow under ``.claude/workflows/``.
    """
    scenario: dict = {"rules": rules}
    if capture:
        scenario["capture"] = capture
    proc = subprocess.run(
        [NODE, str(DRYRUN), str(script or WORKFLOWS / f"{name}.js"), json.dumps(args), mode, json.dumps(scenario)],
        capture_output=True, text=True, timeout=60, cwd=REPO_ROOT,
    )
    line = (proc.stdout.strip().splitlines() or ["{}"])[-1]
    out = json.loads(line)
    assert out.get("ok"), f"{name}: dry run failed: {out.get('error')}"
    assert isinstance(out.get("result"), dict), f"{name}: the harness did not print the returned value"
    return out


def ret(match: str, value: object) -> dict:
    return {"match": match, "return": value}


def act(match: str, action: str, **kw: object) -> dict:
    return {"match": match, "action": action, **kw}


def confirm(status: str = "COMPLETE", **extra: object) -> dict:
    return ret("^confirm report on disk", {"exists": True, "bytes": 2048, "first_heading": "# Report", "states_status": status, **extra})


def prompt_of(out: dict, label_re: str) -> str:
    hits = [c["prompt"] for c in out.get("captured", []) if re.search(label_re, c["label"])]
    assert hits, f"no captured prompt for {label_re}"
    return hits[0]


def section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def assert_payload_shape(result: dict) -> None:
    assert result["status"] in {"complete", "partial", "blocked"}
    assert isinstance(result["status_reasons"], list)
    assert "coverage" in result and "report" in result
    if result["status"] == "complete":
        assert result["status_reasons"] == []
        assert result["report"] is not None
    else:
        assert result["status_reasons"], "a partial or blocked run must say why"
    if result["status"] == "blocked":
        assert result["report"] is None


# ============================================================== citation-audit
CA = "citation-audit"
CA_ARGS = {"path": "paper.md"}
CA_OUT = "alterlab-citation-audit.md"


def ca_doc(claims_total: int = 6) -> dict:
    return {
        "references": [{"id": f"R{i}", "text": f"Author{i} et al. ({2010 + i}). Title {i}. Journal."} for i in range(1, 6)],
        "claims": [
            {"id": "C1", "claim": "Mindfulness lowers burnout by 30%.", "refs": ["R1"]},
            {"id": "C2", "claim": "The effect persists for a year.", "refs": ["R2"]},
            {"id": "C3", "claim": "Effects are larger in ICU nurses.", "refs": ["R1", "R2"]},
            {"id": "C4", "claim": "Dropout is under 5%.", "refs": ["R3"]},
            {"id": "C5", "claim": "Costs fall by half.", "refs": ["R4"]},
            {"id": "C6", "claim": "Managers support it.", "refs": ["R99"]},
        ],
        "claims_total": claims_total,
        "placeholders": [],
    }


CA_REF_VERDICTS = {"results": [
    {"id": "R1", "verdict": "VERIFIED", "evidence": "Crossref DOI match 0.98"},
    {"id": "R2", "verdict": "VERIFIED", "evidence": "OpenAlex match 0.95"},
    {"id": "R3", "verdict": "NOT_FOUND", "evidence": "title, author+year, and DOI searches empty"},
    {"id": "R4", "verdict": "PAC", "evidence": "year is 2013, not 2014", "corrected": "Author4 et al. (2013)."},
    {"id": "R5", "verdict": "VERIFIED", "evidence": "Crossref match 0.99"},
]}
CA_CLAIM_VERDICTS = {"results": [
    {"id": "C1", "verdict": "SUPPORTED", "evidence": "\"burnout fell 31%\""},
    {"id": "C2", "verdict": "UNSUPPORTED", "evidence": "follow-up was 12 weeks", "fix": "persists for 12 weeks"},
    {"id": "C3", "verdict": "SUPPORTED", "evidence": "\"larger in ICU\""},
    {"id": "C5", "verdict": "CONTRADICTED", "evidence": "\"costs rose\"", "fix": "costs did not fall"},
]}


def ca_rules(*extra: dict, claims_total: int = 6, status: str = "COMPLETE") -> list[dict]:
    """Fixtures first (the first applicable "return" rule wins), faults after."""
    fixtures = [
        ret("^extract references", ca_doc(claims_total)),
        ret("^references ", CA_REF_VERDICTS),
        ret("^claims batch", CA_CLAIM_VERDICTS),
        ret("^recheck ", {"overturned": False, "evidence": "searched Crossref, OpenAlex, ORCID: nothing"}),
        confirm(status),
    ]
    returns = [r for r in extra if "return" in r]
    return returns + fixtures + [r for r in extra if "return" not in r]


def test_citation_audit_baseline_is_complete() -> None:
    res = run(CA, CA_ARGS, ca_rules())["result"]
    assert_payload_shape(res)
    assert res["status"] == "complete"
    assert res["report"] == CA_OUT
    c = res["counts"]
    assert (c["claims_checked"], c["TF"], c["PAC"], c["IH"], c["SH"]) == (4, 1, 1, 0, 2)
    assert c["claims_total"] == 6 and c["claims_extracted"] == 6 and c["claims_checkable"] == 4
    cov = res["coverage"]
    assert cov["rechecks"]["requested"] == 8 and cov["rechecks"]["completed"] == 8
    assert {x["id"] for x in res["unchecked"]["claims_not_checkable"]} == {"C4", "C6"}


def test_citation_audit_claims_checked_counts_verdicts_not_dispatches() -> None:
    out = run(CA, CA_ARGS, ca_rules(act("^claims batch", "null")))
    res = out["result"]
    assert_payload_shape(res)
    assert res["counts"]["claims_checked"] == 0, "claims whose batch failed must not count as checked"
    assert res["counts"]["SH"] == 0
    cl = res["coverage"]["claims"]
    assert (cl["requested"], cl["dispatched"], cl["completed"], cl["failed"], cl["unresolved"]) == (4, 4, 0, 4, 4)
    assert cl["retried"] == 1 and "claims batch 1 (retry)" in out["calls"]
    assert res["unchecked"]["claims_without_verdict"] == ["C1", "C2", "C3", "C5"]
    assert res["status"] == "partial"


def test_citation_audit_thrown_batch_is_retried_once() -> None:
    out = run(CA, CA_ARGS, ca_rules(act("^claims batch", "throw", times=1)))
    res = out["result"]
    assert res["counts"]["claims_checked"] == 4
    assert res["coverage"]["claims"]["retried"] == 1
    assert out["calls"].count("claims batch 1 (retry)") == 1
    assert res["status"] == "complete"


def test_citation_audit_omitted_item_is_retried_then_left_unchecked() -> None:
    res = run(CA, CA_ARGS, ca_rules(act("^claims batch", "drop", ids=["C5"])))["result"]
    assert res["counts"]["claims_checked"] == 3
    assert res["counts"]["SH"] == 1, "only C2 can stand; C5 never got a verdict"
    assert res["unchecked"]["claims_without_verdict"] == ["C5"]
    assert res["coverage"]["claims"]["retried"] == 1
    assert res["status"] == "partial"


def test_citation_audit_retry_answers_for_items_not_sent_do_not_inflate_counts() -> None:
    # First call omits C5; the retry (sent only C5) answers all four claims again.
    res = run(CA, CA_ARGS, ca_rules(act("^claims batch", "drop", ids=["C5"], times=1)))["result"]
    assert res["counts"]["claims_checked"] == 4
    assert res["coverage"]["id_issues"]["unknown"] == 3
    assert res["status"] == "complete"


def test_citation_audit_duplicate_ids() -> None:
    same = run(CA, CA_ARGS, ca_rules(act("^claims batch", "duplicate")))["result"]
    assert same["counts"]["claims_checked"] == 4 and same["coverage"]["id_issues"]["duplicate"] == 1
    # A duplicate that disagrees is discarded and the claim retried once ...
    once = run(CA, CA_ARGS, ca_rules(act("^claims batch", "duplicate", values={"verdict": "CONTRADICTED"}, times=1)))["result"]
    assert once["counts"]["claims_checked"] == 4 and once["coverage"]["id_issues"]["conflicting"] == 1
    assert once["coverage"]["claims"]["retried"] == 1
    # ... and stays unchecked if the retry disagrees with itself too.
    always = run(CA, CA_ARGS, ca_rules(act("^claims batch", "duplicate", values={"verdict": "CONTRADICTED"})))["result"]
    assert always["counts"]["claims_checked"] == 3 and "C1" in always["unchecked"]["claims_without_verdict"]


def test_citation_audit_unknown_and_missing_ids() -> None:
    unknown = run(CA, CA_ARGS, ca_rules(act("^claims batch", "unknown_id"), act("^references ", "unknown_id")))["result"]
    assert unknown["counts"]["claims_checked"] == 4 and unknown["counts"]["references_with_verdict"] == 5
    assert unknown["coverage"]["id_issues"]["unknown"] == 2
    assert unknown["coverage"]["rechecks"]["flags"] == 4, "an invented id must not create a flag"
    missing = run(CA, CA_ARGS, ca_rules(act("^claims batch", "missing_id")))["result"]
    assert missing["counts"]["claims_checked"] == 3
    assert missing["unchecked"]["claims_without_verdict"] == ["C1"]
    assert missing["coverage"]["id_issues"]["missing"] == 2  # first call and its retry


def test_citation_audit_flag_without_completed_rechecks_is_provisional() -> None:
    out = run(CA, CA_ARGS, ca_rules(act("^recheck reference R3 ", "null")), capture="^write integrity report$")
    res = out["result"]
    assert res["counts"]["TF"] == 0, "a NOT_FOUND flag with no completed re-check must not count as TF"
    assert res["counts"]["flags_recheck_incomplete"] == 1
    [flag] = res["unchecked"]["flags_recheck_incomplete"]
    assert (flag["id"], flag["category"], flag["rechecks_completed"]) == ("R3", "TF", 0)
    rc = res["coverage"]["rechecks"]
    assert (rc["requested"], rc["dispatched"], rc["completed"], rc["failed"], rc["retried"]) == (8, 8, 6, 2, 2)
    assert res["status"] == "partial"
    prompt = prompt_of(out, "^write integrity report$")
    stood = section(prompt, "Flags that stood after two completed re-checks:", "Provisional flags (re-check incomplete):")
    provisional = section(prompt, "Provisional flags (re-check incomplete):", "Placeholders:")
    assert '"R3"' not in stood and '"R3"' in provisional
    assert "Status: PARTIAL" in prompt and "independent re-check" not in prompt
    assert "not independent verification" in prompt


def test_citation_audit_one_of_two_rechecks_is_not_enough() -> None:
    res = run(CA, CA_ARGS, ca_rules(act(r"^recheck claim C2 \(1/2\)", "throw")))["result"]
    assert res["counts"]["SH"] == 1, "C2 has one completed re-check, so only C5 counts"
    [flag] = res["unchecked"]["flags_recheck_incomplete"]
    assert (flag["id"], flag["rechecks_completed"]) == ("C2", 1)
    # A failed re-check retried successfully completes the flag.
    ok = run(CA, CA_ARGS, ca_rules(act(r"^recheck claim C2 \(1/2\)", "null", times=1)))["result"]
    assert ok["counts"]["SH"] == 2 and ok["coverage"]["rechecks"]["retried"] == 1 and ok["status"] == "complete"


def test_citation_audit_overturned_flag_is_not_counted() -> None:
    res = run(CA, CA_ARGS, ca_rules(act(r"^recheck reference R4 \(2/2\)", "set", values={"overturned": True})))["result"]
    assert res["counts"]["PAC"] == 0 and res["counts"]["flags_overturned_on_recheck"] == 1
    assert res["status"] == "complete"


def test_citation_audit_cap_is_reported() -> None:
    out = run(CA, CA_ARGS, ca_rules(claims_total=212, status="PARTIAL"), capture="^write integrity report$")
    res = out["result"]
    assert res["counts"]["claims_total"] == 212 and res["counts"]["claims_extracted"] == 6
    assert res["coverage"]["extraction"]["claims_not_extracted"] == 206
    assert res["unchecked"]["claims_not_extracted"] == 206
    assert res["status"] == "partial" and any("capped" in r for r in res["status_reasons"])
    assert res["report"] == CA_OUT
    assert '"claims_total":212' in prompt_of(out, "^write integrity report$")


def test_citation_audit_reference_batch_failure() -> None:
    res = run(CA, CA_ARGS, ca_rules(act("^references ", "null")))["result"]
    refs = res["coverage"]["references"]
    assert (refs["requested"], refs["completed"], refs["unresolved"], refs["retried"]) == (5, 0, 5, 1)
    assert res["unchecked"]["references_without_verdict"] == ["R1", "R2", "R3", "R4", "R5"]
    assert res["counts"]["TF"] == 0 and res["counts"]["PAC"] == 0
    assert res["status"] == "partial"


def test_citation_audit_failed_report_writing_blocks() -> None:
    out = run(CA, CA_ARGS, ca_rules(act("^write integrity report", "throw")))
    res = out["result"]
    assert_payload_shape(res)
    assert res["report"] is None and res["status"] == "blocked"
    assert any("report-writing agent failed" in r for r in res["status_reasons"])
    assert "write integrity report (retry)" in out["calls"]
    assert res["counts"]["claims_checked"] == 4, "the audit numbers are still returned"
    once = run(CA, CA_ARGS, ca_rules(act("^write integrity report", "null", times=1)))["result"]
    assert once["report"] == CA_OUT and once["status"] == "complete" and once["coverage"]["report"]["attempts"] == 2


def test_citation_audit_report_must_be_read_back() -> None:
    missing = run(CA, CA_ARGS, ca_rules(act("^confirm report on disk", "set", values={"exists": False, "bytes": 0})))
    res = missing["result"]
    assert res["report"] is None and res["status"] == "blocked"
    assert any("not found on disk" in r for r in res["status_reasons"])
    assert "write integrity report (retry)" in missing["calls"], "a write that cannot be found is retried once"
    unconfirmed = run(CA, CA_ARGS, ca_rules(act("^confirm report on disk", "null")))["result"]
    assert unconfirmed["report"] is None and unconfirmed["status"] == "blocked"
    mismatch = run(CA, CA_ARGS, ca_rules(status="PARTIAL"))["result"]
    assert mismatch["report"] == CA_OUT and mismatch["status"] == "partial"


def test_citation_audit_lookups_that_did_not_happen_keep_the_audit_partial() -> None:
    unverified = run(CA, CA_ARGS, ca_rules(act("^references ", "set_items", ids=["R5"], values={"verdict": "UNVERIFIED"}), status="PARTIAL"))["result"]
    assert unverified["counts"]["unverified"] == 1 and unverified["counts"]["TF"] == 1
    assert unverified["status"] == "partial" and any("UNVERIFIED" in r for r in unverified["status_reasons"])
    uncheckable = run(CA, CA_ARGS, ca_rules(act("^claims batch", "set_items", ids=["C3"], values={"verdict": "UNCHECKABLE"}), status="PARTIAL"))["result"]
    assert uncheckable["counts"]["claims_checked"] == 4 and uncheckable["counts"]["claims_uncheckable"] == 1
    assert uncheckable["status"] == "partial"


def test_citation_audit_failed_extraction_is_not_reported_as_empty() -> None:
    res = run(CA, CA_ARGS, [act("^extract references", "null")])["result"]
    assert_payload_shape(res)
    assert res["status"] == "blocked" and res["report"] is None
    assert any("extraction agent failed" in r for r in res["status_reasons"])
    assert "No reference list" not in res.get("message", "")


# ============================================================== review-panel
RP = "review-panel"
RP_ARGS = {"path": "paper.pdf", "venue": "PLOS ONE"}
RP_OUT = "alterlab-review-panel.md"
RP_LENSES = ["Methodology reviewer", "Statistics reviewer", "Devil's advocate"]


def rp_review(n: int, major_issue: str) -> dict:
    return {
        "recommendation": "major_revision",
        "summary": f"Reviewer {n} summary.",
        "strengths": ["clear question"],
        "concerns": [
            {"id": "M1", "severity": "major", "issue": major_issue, "location": "Methods 2.3", "suggested_fix": "report it"},
            {"id": "m1", "severity": "minor", "issue": f"typo {n}", "location": "p. 4", "suggested_fix": "fix"},
        ],
    }


RP_ISSUES = ["No power analysis", "Model ignores clustering by ward", "Effect may be regression to the mean"]


def rp_rules(*extra: dict, status: str = "COMPLETE") -> list[dict]:
    profile = {
        "field": "nursing", "paper_type": "empirical", "design": "cluster RCT", "reporting_guideline": "CONSORT",
        "lenses": [{"key": f"l{i}", "title": t, "focus": f"focus {i}"} for i, t in enumerate(RP_LENSES)],
    }
    fixtures = [ret("^field analyst", profile)]
    fixtures += [ret(f"^{re.escape(t)}( \\(retry\\))?$", rp_review(i, RP_ISSUES[i])) for i, t in enumerate(RP_LENSES)]
    fixtures += [ret("^check: ", {"valid": True, "reason": "the methods do not address it"}), confirm(status)]
    returns = [r for r in extra if "return" in r]
    return returns + fixtures + [r for r in extra if "return" not in r]


def test_review_panel_baseline_is_complete() -> None:
    res = run(RP, RP_ARGS, rp_rules())["result"]
    assert_payload_shape(res)
    assert res["status"] == "complete" and res["report"] == RP_OUT
    assert res["major_concerns"] == {"raised": 3, "validated": 3, "unverified": 0, "withdrawn": 0}
    assert res["reviewers"]["requested"] == 3 and res["reviewers"]["completed"] == 3


@pytest.mark.parametrize("fault", ["null", "throw"])
def test_review_panel_missing_validation_is_unverified_not_validated(fault: str) -> None:
    out = run(RP, RP_ARGS, rp_rules(act("^check: Statistics reviewer", fault)), capture="^editor-in-chief$")
    res = out["result"]
    assert res["major_concerns"] == {"raised": 3, "validated": 2, "unverified": 1, "withdrawn": 0}
    [u] = res["concerns"]["unverified"]
    assert u["reviewer"] == "Statistics reviewer" and u["issue"] == RP_ISSUES[1]
    assert all(c["reviewer"] != "Statistics reviewer" for c in res["concerns"]["validated"])
    cc = res["coverage"]["concern_checks"]
    assert (cc["requested"], cc["completed"], cc["failed"], cc["retried"]) == (3, 2, 1, 1)
    assert res["status"] == "partial"
    prompt = prompt_of(out, "^editor-in-chief$")
    validated = section(prompt, "Validated major concerns:", "UNVERIFIED major concerns")
    unverified = section(prompt, "UNVERIFIED major concerns", "Withdrawn concerns:")
    assert RP_ISSUES[1] not in validated and RP_ISSUES[1] in unverified
    assert "not independent confirmation" in prompt


def test_review_panel_validation_retry_and_withdrawal() -> None:
    retried = run(RP, RP_ARGS, rp_rules(act("^check: Statistics reviewer", "throw", times=1)))["result"]
    assert retried["major_concerns"]["validated"] == 3 and retried["status"] == "complete"
    assert retried["coverage"]["concern_checks"]["retried"] == 1
    withdrawn = run(RP, RP_ARGS, rp_rules(act("^check: Devil", "set", values={"valid": False})))["result"]
    assert withdrawn["major_concerns"] == {"raised": 3, "validated": 2, "unverified": 0, "withdrawn": 1}
    assert withdrawn["status"] == "complete"


def test_review_panel_failed_reviewer_is_counted() -> None:
    res = run(RP, RP_ARGS, rp_rules(act("^Statistics reviewer", "null")))["result"]
    assert res["reviewers"] == {"requested": 3, "used": 3, "completed": 2, "missing": ["Statistics reviewer"]}
    rv = res["coverage"]["reviewers"]
    assert (rv["requested"], rv["dispatched"], rv["completed"], rv["failed"], rv["retried"]) == (3, 3, 2, 1, 1)
    assert res["major_concerns"]["raised"] == 2 and res["status"] == "partial"
    once = run(RP, RP_ARGS, rp_rules(act("^Statistics reviewer", "throw", times=1)))["result"]
    assert once["reviewers"]["completed"] == 3 and once["status"] == "complete"


def test_review_panel_duplicate_concerns() -> None:
    same = run(RP, RP_ARGS, rp_rules(act("^Methodology reviewer$", "duplicate", field="concerns")))["result"]
    assert same["major_concerns"]["raised"] == 3, "the same concern listed twice is checked once"
    assert same["coverage"]["id_issues"]["duplicate"] == 1
    distinct = run(RP, RP_ARGS, rp_rules(act("^Methodology reviewer$", "duplicate", field="concerns", values={"issue": "Attrition is unexplained"})))["result"]
    assert distinct["major_concerns"]["raised"] == 4, "two different concerns sharing an id are both kept"
    assert len({c["id"] for c in distinct["concerns"]["validated"] if c["reviewer"] == "Methodology reviewer"}) == 2


def test_review_panel_lens_cap_is_reported() -> None:
    args = {"path": "paper.pdf", "lenses": [f"Lens {i}" for i in range(1, 9)]}
    res = run(RP, args, rp_rules(ret("^Lens ", rp_review(9, "Generic concern")), status="PARTIAL"))["result"]
    assert res["reviewers"]["requested"] == 8 and res["reviewers"]["used"] == 6 and res["reviewers"]["completed"] == 6
    assert res["status"] == "partial" and any("capped" in r for r in res["status_reasons"])


def test_review_panel_report_failures_block() -> None:
    res = run(RP, RP_ARGS, rp_rules(act("^editor-in-chief", "throw")))["result"]
    assert_payload_shape(res)
    assert res["status"] == "blocked" and res["report"] is None
    assert res["major_concerns"]["validated"] == 3
    gone = run(RP, RP_ARGS, rp_rules(act("^confirm report on disk", "set", values={"exists": False, "bytes": 0})))["result"]
    assert gone["status"] == "blocked" and gone["report"] is None


def test_review_panel_failed_profile_blocks() -> None:
    out = run(RP, RP_ARGS, [act("^field analyst", "null")])
    assert out["result"]["status"] == "blocked" and out["result"]["report"] is None
    assert out["calls"] == ["field analyst", "field analyst (retry)"]


# ============================================================== systematic-review-screening
SR = "systematic-review-screening"
SR_ARGS = {"question": "Does mindfulness training reduce burnout in nurses?", "records": "export.ris", "batch": 5}
SR_DIR = "alterlab-screening"
SR_A = {s: "include" for s in range(1, 11)} | {3: "exclude", 8: "exclude"}
SR_B = SR_A | {2: "exclude", 7: "exclude"}  # disagrees with A on sid 2 and sid 7
SR_ADJ = SR_A | {2: "include", 7: "exclude"}


def decisions(sids: range | list[int], table: dict[int, str]) -> dict:
    return {"decisions": [
        {"sid": s, "decision": table[s], "code": "E1" if table[s] == "exclude" else "I", "reason": "title/abstract"} for s in sids
    ]}


def sr_confirm(included: int, unresolved: int, status: str = "COMPLETE") -> dict:
    return confirm(status, others=[
        {"path": f"{SR_DIR}/included.jsonl", "exists": True, "lines": included},
        {"path": f"{SR_DIR}/unresolved.jsonl", "exists": True, "lines": unresolved},
    ])


def sr_rules(*extra: dict, included: int = 7, unresolved: int = 0, status: str = "COMPLETE") -> list[dict]:
    protocol = {
        "pico": "nurses; mindfulness; usual care; burnout; any design",
        "criteria": [{"code": "I1", "kind": "include", "rule": "nurses"}, {"code": "E1", "kind": "exclude", "rule": "not nurses"}],
        "queries": [{"database": "pubmed", "query": "mindfulness AND burnout"}, {"database": "openalex", "query": "mindfulness burnout"}],
    }
    fixtures = [
        ret("^protocol", protocol),
        ret("^merge \\+ de-duplicate", {"identified": [{"source": "export.ris", "n": 12}], "duplicates_removed": 2, "total": 10, "file": f"{SR_DIR}/records.jsonl"}),
        ret("^batch 1 · screener A", decisions(range(1, 6), SR_A)),
        ret("^batch 2 · screener A", decisions(range(6, 11), SR_A)),
        ret("^batch 1 · screener B", decisions(range(1, 6), SR_B)),
        ret("^batch 2 · screener B", decisions(range(6, 11), SR_B)),
        ret("^adjudication", decisions(range(1, 11), SR_ADJ)),
        sr_confirm(included, unresolved, status),
    ]
    returns = [r for r in extra if "return" in r]
    return returns + fixtures + [r for r in extra if "return" not in r]


def flow_adds_up(flow: dict) -> None:
    assert flow["screened"] + flow["unresolved"] == flow["submitted_for_screening"]
    assert flow["screened"] == flow["excluded_title_abstract"] + flow["sought_for_retrieval"]


def test_screening_baseline_is_complete() -> None:
    res = run(SR, SR_ARGS, sr_rules())["result"]
    assert_payload_shape(res)
    assert res["status"] == "complete" and res["report"] == f"{SR_DIR}/prisma-screening.md"
    f = res["flow"]
    flow_adds_up(f)
    assert (f["screened"], f["unresolved"], f["sought_for_retrieval"], f["excluded_title_abstract"]) == (10, 0, 7, 3)
    assert res["included_sids"] == [1, 2, 4, 5, 6, 9, 10]
    assert res["kappa_records"] == 10
    assert res["coverage"]["records"]["resolved_by"] == {"agreement": 8, "adjudication": 2, "second_review": 0}
    assert res["files"] == {"included": f"{SR_DIR}/included.jsonl", "unresolved": f"{SR_DIR}/unresolved.jsonl"}


def test_screening_failed_adjudication_leaves_records_unresolved_and_retained() -> None:
    out = run(SR, SR_ARGS, sr_rules(act("^adjudication", "null"), included=6, unresolved=2, status="PARTIAL"), capture="^PRISMA report$")
    res = out["result"]
    f = res["flow"]
    flow_adds_up(f)
    assert (f["screened"], f["unresolved"], f["sought_for_retrieval"], f["excluded_title_abstract"]) == (8, 2, 6, 2)
    assert [u["sid"] for u in res["unresolved"]] == [2, 7]
    assert 2 not in res["included_sids"], "an unresolved record is not counted as included"
    assert res["coverage"]["adjudication"]["retried"] == 1
    assert res["status"] == "partial"
    prompt = prompt_of(out, "^PRISMA report$")
    assert '"unresolved":2' in prompt and '{"sid":2,' in section(prompt, "UNRESOLVED records:", "Reply with")
    assert "Status: PARTIAL" in prompt and "not agreement between independent human screeners" in prompt


def test_screening_adjudication_retry_recovers() -> None:
    res = run(SR, SR_ARGS, sr_rules(act("^adjudication", "throw", times=1)))["result"]
    assert res["flow"]["unresolved"] == 0 and res["coverage"]["adjudication"]["retried"] == 1
    assert res["status"] == "complete"


def test_screening_failed_screener_uses_second_review_and_keeps_disagreement_unresolved() -> None:
    res = run(SR, SR_ARGS, sr_rules(act("^batch 2 · screener B", "null"), included=7, unresolved=1, status="PARTIAL"))["result"]
    f = res["flow"]
    flow_adds_up(f)
    # sids 6-10 had only screener A; the adjudicator agrees on 6, 8, 9, 10 and disagrees on 7.
    assert (f["screened"], f["unresolved"]) == (9, 1)
    assert res["unresolved"] == [{"sid": 7, "reason": "one screener failed, and that screener and the second reviewer disagree"}]
    sc = res["coverage"]["screening"]
    assert sc["records_with_both_screeners"] == 5 and sc["records_with_one_screener"] == 5
    sd = sc["screener_decisions"]
    assert (sd["requested"], sd["completed"], sd["unresolved"]) == (20, 15, 5)
    assert res["kappa_records"] == 5
    assert res["coverage"]["records"]["resolved_by"]["second_review"] == 4
    assert res["status"] == "partial"


def test_screening_records_without_any_screener_are_not_adjudicated_alone() -> None:
    out = run(SR, SR_ARGS, sr_rules(act("^batch 2 · screener", "null"), included=4, unresolved=5, status="PARTIAL"), capture="^adjudication")
    res = out["result"]
    assert [u["sid"] for u in res["unresolved"]] == [6, 7, 8, 9, 10]
    assert all(u["reason"].startswith("neither screener") for u in res["unresolved"])
    assert res["flow"]["screened"] == 5 and res["flow"]["unresolved"] == 5
    adj_prompt = prompt_of(out, "^adjudication 1$")
    assert '"sid": 2' in adj_prompt and '"sid": 6' not in adj_prompt


def test_screening_failed_screener_and_adjudicator() -> None:
    res = run(SR, SR_ARGS, sr_rules(act("^batch 2 · screener B", "null"), act("^adjudication", "null"), included=3, unresolved=6, status="PARTIAL"))["result"]
    f = res["flow"]
    flow_adds_up(f)
    assert (f["screened"], f["unresolved"], f["sought_for_retrieval"]) == (4, 6, 3)
    assert res["included_sids"] == [1, 4, 5]
    assert sorted(u["sid"] for u in res["unresolved"]) == [2, 6, 7, 8, 9, 10]


def test_screening_partial_screener_output() -> None:
    res = run(SR, SR_ARGS, sr_rules(act("^batch 1 · screener A", "drop", ids=[4, 5]), status="PARTIAL"))["result"]
    assert res["coverage"]["screening"]["records_with_one_screener"] == 2
    assert res["coverage"]["screening"]["screener_decisions"]["retried"] >= 1
    assert res["flow"]["screened"] == 10 and res["coverage"]["records"]["resolved_by"]["second_review"] == 2
    assert res["status"] == "partial", "records not dual-screened make the run partial"


def test_screening_duplicate_unknown_and_missing_sids() -> None:
    dup = run(SR, SR_ARGS, sr_rules(act("^batch 1 · screener A", "duplicate", count=2)))["result"]
    assert dup["flow"]["screened"] == 10 and dup["coverage"]["id_issues"]["duplicate"] == 2
    assert dup["coverage"]["screening"]["screener_decisions"]["completed"] == 20
    assert dup["status"] == "complete"
    conflicting = run(SR, SR_ARGS, sr_rules(act("^batch 1 · screener A$", "duplicate", values={"decision": "exclude"})))["result"]
    assert conflicting["coverage"]["id_issues"]["conflicting"] == 1
    assert conflicting["flow"]["screened"] == 10 and conflicting["status"] == "complete"  # retried and recovered
    # The adjudication fixture answers all 10 sids although it is sent only the 2 conflicts, so the
    # baseline already ignores 8 answers for records it was not asked about.
    baseline = run(SR, SR_ARGS, sr_rules())["result"]
    assert baseline["coverage"]["id_issues"]["unknown"] == 8
    unknown = run(SR, SR_ARGS, sr_rules(act("^batch 1 · screener A", "unknown_id"), act("^adjudication", "unknown_id")))["result"]
    assert unknown["flow"] == baseline["flow"] and unknown["included_sids"] == baseline["included_sids"]
    assert unknown["coverage"]["id_issues"]["unknown"] == 8 + 2
    missing = run(SR, SR_ARGS, sr_rules(act("^batch 1 · screener A", "missing_id"), status="PARTIAL"))["result"]
    assert missing["coverage"]["id_issues"]["missing"] == 2
    assert missing["coverage"]["screening"]["records_with_one_screener"] == 1
    assert missing["flow"]["screened"] == 10


def test_screening_report_failures_block() -> None:
    res = run(SR, SR_ARGS, sr_rules(act("^PRISMA report", "null")))["result"]
    assert_payload_shape(res)
    assert res["status"] == "blocked" and res["report"] is None
    assert res["files"] == {"included": None, "unresolved": None}
    gone = run(SR, SR_ARGS, sr_rules(act("^confirm report on disk", "set", values={"exists": False, "bytes": 0})))["result"]
    assert gone["status"] == "blocked" and gone["report"] is None
    short = run(SR, SR_ARGS, sr_rules(included=5))["result"]
    assert short["report"] is not None and short["status"] == "partial"
    assert short["files"]["included"] is None, "included.jsonl with the wrong number of lines is not returned"


def test_screening_failed_search_is_reported() -> None:
    args = {"question": "Does mindfulness training reduce burnout in nurses?", "databases": ["pubmed", "openalex"], "batch": 5}
    search = {"database": "pubmed", "query_run": "mindfulness AND burnout", "count": 6, "total_hits": 6, "capped": False, "file": f"{SR_DIR}/records-pubmed.jsonl"}
    res = run(SR, args, sr_rules(ret("^search ", search), act("^search openalex", "null"), status="PARTIAL"))["result"]
    s = res["coverage"]["searches"]
    assert (s["requested"], s["completed"], s["failed"], s["retried"]) == (2, 1, 1, 1)
    assert s["failed_databases"] == ["openalex"]
    assert res["status"] == "partial"
    capped = run(SR, args, sr_rules(ret("^search ", search | {"capped": True, "total_hits": 900}), status="PARTIAL"))["result"]
    assert any("capped" in r for r in capped["status_reasons"])


def test_screening_respects_the_agent_cap() -> None:
    """2,000 records whose screeners never answer: retries run until the cap guard stops them, and
    every record is counted as UNRESOLVED instead of the run exceeding 1,000 agents."""
    big = {"identified": [{"source": "export.ris", "n": 2000}], "duplicates_removed": 0, "total": 2000, "file": f"{SR_DIR}/records.jsonl"}
    out = run(SR, SR_ARGS, sr_rules(ret("^merge \\+ de-duplicate", big), ret("^batch ", {"decisions": []}), status="PARTIAL"))
    res = out["result"]
    assert out["agents"] <= 1000 and res["coverage"]["agents"] == out["agents"]
    assert any("agent runtime cap was reached" in r for r in res["status_reasons"])
    assert (res["flow"]["screened"], res["flow"]["unresolved"]) == (0, 2000)
    assert res["report"] is not None, "agents are held back so the report can still be written and read back"
    assert res["status"] == "partial"


def test_screening_failed_early_stages_block() -> None:
    for stage in ("^protocol", "^merge \\+ de-duplicate"):
        res = run(SR, SR_ARGS, sr_rules(act(stage, "null")))["result"]
        assert_payload_shape(res)
        assert res["status"] == "blocked" and res["report"] is None


# ============================================================== claim-stress-test (smoke)
CS = "claim-stress-test"
CS_ARGS = {"claims": ["Mindfulness causes lower burnout.", "The effect generalizes to all hospital staff."]}
NO_OBJECTION = {"refuted": False, "severity": "none", "argument": "holds under this lens"}
FATAL = {"refuted": True, "severity": "fatal", "argument": "does not hold"}


def cs_rules(*extra: dict, status: str = "COMPLETE") -> list[dict]:
    returns = [r for r in extra if "return" in r]
    return returns + [ret(" · ", NO_OBJECTION), confirm(status)] + [r for r in extra if "return" not in r]


def test_claim_stress_test_baseline_is_complete() -> None:
    res = run(CS, CS_ARGS, cs_rules())["result"]
    assert_payload_shape(res)
    assert res["status"] == "complete" and res["ratings"] == {"survives": 2}
    assert res["coverage"]["lenses"]["requested"] == 6 and res["coverage"]["lenses"]["completed"] == 6


@pytest.mark.parametrize("fault", ["null", "throw"])
def test_claim_stress_test_claim_without_lenses_is_unrated_not_survives(fault: str) -> None:
    res = run(CS, CS_ARGS, cs_rules(act("^C1 · ", fault)))["result"]
    c1, c2 = res["claims"]
    assert (c1["rating"], c1["lenses_completed"]) == ("unrated", 0), "a claim no lens examined must not 'survive'"
    assert c2["rating"] == "survives"
    lz = res["coverage"]["lenses"]
    assert (lz["requested"], lz["completed"], lz["failed"], lz["retried"]) == (6, 3, 3, 3)
    assert res["status"] == "partial"


def test_claim_stress_test_rating_only_when_missing_lens_cannot_change_it() -> None:
    settled = run(CS, CS_ARGS, cs_rules(ret("^C1 · (counter-evidence|citation-support)", FATAL), act("^C1 · inference", "null")))["result"]
    assert settled["claims"][0]["rating"] == "refuted" and settled["claims"][0]["lenses_completed"] == 2
    unsettled = run(CS, CS_ARGS, cs_rules(act("^C1 · inference", "null")))["result"]
    assert unsettled["claims"][0]["rating"] == "unrated", "two 'no objection' lenses cannot rule out a fatal third"


def test_claim_stress_test_failures_block() -> None:
    res = run(CS, CS_ARGS, cs_rules(act("^write report", "throw")))["result"]
    assert_payload_shape(res)
    assert res["status"] == "blocked" and res["report"] is None
    extract = run(CS, {"path": "paper.md"}, [act("^extract headline claims", "null")])["result"]
    assert extract["status"] == "blocked" and "extraction agent failed" in extract["status_reasons"][0]


# ============================================================== rebuttal (smoke)
RB = "rebuttal"
RB_ARGS = {"manuscript": "paper.docx", "reviews": ["r1.pdf", "r2.pdf"], "out_dir": "rb"}
RB_COMMENTS = {"comments": [
    {"id": "R1.1", "reviewer": "R1", "text": "Report the power analysis.", "kind": "major", "asks_for": "new_analysis"},
    {"id": "R1.2", "reviewer": "R1", "text": "A clear, well-written paper.", "kind": "praise", "asks_for": "none"},
    {"id": "R2.1", "reviewer": "R2", "text": "Define burnout in the abstract.", "kind": "minor", "asks_for": "rewrite"},
]}


def rb_draft(cid: str) -> dict:
    return {"id": cid, "stance": "agree_changed", "response": "We thank the reviewer.",
            "change": {"location": "Methods 2.1", "description": "added"}, "author_action": "none"}


def rb_rules(*extra: dict, status: str = "COMPLETE") -> list[dict]:
    fixtures = [
        ret("^split reviews", RB_COMMENTS), ret("^R1\\.1", rb_draft("R1.1")), ret("^R2\\.1", rb_draft("R2.1")),
        ret("^consistency pass", {"issues": []}),
        confirm(status, others=[{"path": "rb/change-log.md", "exists": True, "lines": 4}, {"path": "rb/author-actions.md", "exists": True, "lines": 2}]),
    ]
    returns = [r for r in extra if "return" in r]
    return returns + fixtures + [r for r in extra if "return" not in r]


def test_rebuttal_baseline_is_complete() -> None:
    res = run(RB, RB_ARGS, rb_rules())["result"]
    assert_payload_shape(res)
    assert res["status"] == "complete" and res["report"] == "rb/response-letter.md"
    assert (res["actionable"], res["responded"], res["consistency_checked"], res["consistency_issues"]) == (2, 2, True, 0)


def test_rebuttal_consistency_pass_that_did_not_run_is_not_zero_issues() -> None:
    out = run(RB, RB_ARGS, rb_rules(act("^consistency pass", "null")), capture="^assemble letter$")
    res = out["result"]
    assert res["consistency_checked"] is False and res["consistency_issues"] is None
    assert res["coverage"]["consistency"] == {"requested": 1, "completed": 0, "retried": 1}
    assert res["status"] == "partial"
    assert "did NOT run" in prompt_of(out, "^assemble letter$")


def test_rebuttal_failed_draft_and_failed_letter() -> None:
    res = run(RB, RB_ARGS, rb_rules(act("^R2\\.1", "throw")))["result"]
    assert res["responded"] == 1 and res["unanswered"] == ["R2.1"] and res["status"] == "partial"
    assert res["coverage"]["responses"]["retried"] == 1
    dup = run(RB, RB_ARGS, rb_rules(act("^split reviews", "duplicate", values={"text": "Also report effect sizes."})))["result"]
    assert dup["comments"] == 4 and dup["actionable"] == 3, "two different comments sharing an id are both answered"
    blocked = run(RB, RB_ARGS, rb_rules(act("^assemble letter", "null")))["result"]
    assert_payload_shape(blocked)
    assert blocked["status"] == "blocked" and blocked["report"] is None


# ============================================================== grant-mock-panel (smoke)
GP = "grant-mock-panel"
GP_ARGS = {"path": "proposal.pdf", "funder": "NIH", "mechanism": "R01"}
GP_ROLES = ["primary", "secondary", "tertiary", "skeptic"]


def gp_review(role: str) -> dict:
    return {"scores": [{"key": "significance", "score": 3, "rationale": "r"}, {"key": "approach", "score": 4, "rationale": "r"}],
            "overall": 3, "strengths": ["team"],
            "weaknesses": [{"id": "W1", "severity": "major", "issue": f"{role}: aims are interdependent", "where": "Aims"}]}


def gp_rules(*extra: dict, status: str = "COMPLETE") -> list[dict]:
    rubric = {"scale_min": 1, "scale_max": 9, "lower_is_better": True, "source": "NIH simplified review framework (2025)",
              "criteria": [{"key": "significance", "title": "Significance", "guidance": "g"}, {"key": "approach", "title": "Approach", "guidance": "g"}]}
    fixtures = [ret("^funder criteria", rubric)] + [ret(f"^{r} reviewer", gp_review(r)) for r in GP_ROLES]
    fixtures += [ret("^check ", {"stands": True, "reason": "not addressed", "fix": "decouple Aim 2"}), confirm(status)]
    returns = [r for r in extra if "return" in r]
    return returns + fixtures + [r for r in extra if "return" not in r]


def test_grant_panel_baseline_is_complete() -> None:
    res = run(GP, GP_ARGS, gp_rules())["result"]
    assert_payload_shape(res)
    assert res["status"] == "complete" and res["overall_mean"] == 3
    assert res["weaknesses"] == {"raised": 4, "standing": 4, "unverified": 0, "withdrawn": 0}


@pytest.mark.parametrize("fault", ["null", "throw"])
def test_grant_panel_unchecked_weakness_is_unverified_not_standing(fault: str) -> None:
    out = run(GP, GP_ARGS, gp_rules(act("^check skeptic", fault)), capture="^summary statement$")
    res = out["result"]
    assert res["weaknesses"] == {"raised": 4, "standing": 3, "unverified": 1, "withdrawn": 0}
    assert res["standing_weaknesses"] == 3 and res["unverified_weaknesses"][0]["reviewer"] == "skeptic"
    assert res["status"] == "partial"
    prompt = prompt_of(out, "^summary statement$")
    standing = section(prompt, "Standing weaknesses:", "UNVERIFIED weaknesses")
    assert "skeptic: aims" not in standing


def test_grant_panel_scores_and_reviewers_are_accounted() -> None:
    off = run(GP, GP_ARGS, gp_rules(act("^primary reviewer", "set_items", field="scores", values={"score": 12})))["result"]
    assert off["coverage"]["scores"]["off_scale"] == 2 and off["coverage"]["scores"]["missing"] == 2
    assert [c["n"] for c in off["criteria"]] == [3, 3] and off["status"] == "partial"
    gone = run(GP, GP_ARGS, gp_rules(act("^tertiary reviewer", "null")))["result"]
    assert gone["reviewers"] == {"requested": 4, "completed": 3, "missing": ["tertiary"]} and gone["status"] == "partial"
    blocked = run(GP, GP_ARGS, gp_rules(act("^summary statement", "throw")))["result"]
    assert_payload_shape(blocked)
    assert blocked["status"] == "blocked" and blocked["report"] is None


# ============================================================== literature-map (smoke)
LM = "literature-map"
LM_ARGS = {"topic": "LLM-assisted qualitative coding", "out_dir": "lm"}


def lm_rules(*extra: dict, status: str = "COMPLETE") -> list[dict]:
    plan = {"angles": [{"key": "core", "rationale": "terms", "query": "q1"}, {"key": "methods", "rationale": "methods", "query": "q2"}]}
    sweep = {"key": "x", "count": 40, "top": [{"title": "Paper A", "year": 2023, "doi": "10.1/a"}, {"title": "Paper B", "year": 2024, "doi": "10.1/b"}]}
    themes = {"themes": [
        {"name": "Reliability", "summary": "s", "key_works": ["10.1/a"], "open_questions": ["Does LLM coding match human kappa?"]},
        {"name": "Ethics", "summary": "s", "key_works": ["10.1/b"], "open_questions": ["Who owns the codebook?"]},
    ]}
    fixtures = [ret("^search plan", plan), ret("^sweep: ", sweep), ret("^cluster themes", themes),
                ret("^gap: ", {"open": True, "evidence": "OpenAlex and PubMed searches found nothing", "sharpened": "narrowed"}), confirm(status)]
    returns = [r for r in extra if "return" in r]
    return returns + fixtures + [r for r in extra if "return" not in r]


def test_literature_map_baseline_is_complete() -> None:
    res = run(LM, LM_ARGS, lm_rules())["result"]
    assert_payload_shape(res)
    assert res["status"] == "complete" and res["report"] == "lm/literature-map.md"
    assert len(res["open_gaps"]) == 2 and res["unchecked_gaps"] == [] and res["works"] == 2


@pytest.mark.parametrize("fault", ["null", "throw"])
def test_literature_map_unchecked_gap_is_not_open(fault: str) -> None:
    res = run(LM, LM_ARGS, lm_rules(act("^gap: Ethics", fault)))["result"]
    assert len(res["open_gaps"]) == 1
    [u] = res["unchecked_gaps"]
    assert u["theme"] == "Ethics" and "did not complete" in u["why"]
    assert res["coverage"]["gaps"]["retried"] == 1 and res["status"] == "partial"


def test_literature_map_failures() -> None:
    no_themes = run(LM, LM_ARGS, lm_rules(act("^cluster themes", "null")))
    res = no_themes["result"]
    assert res["themes"] == [] and res["open_gaps"] == [] and res["status"] == "partial"
    assert not any(c.startswith("gap:") for c in no_themes["calls"])
    sweep = run(LM, LM_ARGS, lm_rules(act("^sweep: methods", "null")))["result"]
    assert sweep["coverage"]["sweeps"]["failed_angles"] == ["methods"] and sweep["status"] == "partial"
    dup = run(LM, LM_ARGS, lm_rules(ret("^search plan", {"angles": [{"key": "core", "rationale": "r", "query": "q"}] * 2})))["result"]
    assert len(set(dup["angles"])) == 2, "angle keys name output files, so they are made unique"
    blocked = run(LM, LM_ARGS, lm_rules(act("^write map", "null")))["result"]
    assert_payload_shape(blocked)
    assert blocked["status"] == "blocked" and blocked["report"] is None


# ============================================================== skill-freshness-audit (maintainer workflow)
SFA = "skill-freshness-audit"
SFA_SCRIPT = REPO_ROOT / ".claude" / "workflows" / "skill-freshness-audit.js"
SFA_ARGS = {"domains": ["databases"]}
SFA_SKILLS = ["alterlab-pubmed", "alterlab-openalex", "alterlab-arxiv"]


def sfa_finding(skill: str, kind: str) -> dict:
    return {"skill": skill, "file": f"skills/databases/{skill}/SKILL.md", "kind": kind, "stale": f"{skill} v1.0",
            "current": f"{skill} v2.0", "source": "https://pypi.org/pypi/example/json", "severity": "misleads"}


SFA_AUDIT = {"checked": SFA_SKILLS, "findings": [sfa_finding("alterlab-pubmed", "version"), sfa_finding("alterlab-openalex", "endpoint")]}


def sfa_rules(*extra: dict, status: str = "COMPLETE") -> list[dict]:
    fixtures = [
        ret("^inventory", {"domains": [{"domain": "databases", "skills": SFA_SKILLS}]}),
        ret("^databases batch 1", SFA_AUDIT),
        ret("^verify ", {"confirmed": True, "note": "PyPI lists 2.0 as the current release", "suggested_edit": "v1.0 -> v2.0"}),
        confirm(status),
    ]
    returns = [r for r in extra if "return" in r]
    return returns + fixtures + [r for r in extra if "return" not in r]


def sfa(rules: list[dict], capture: str | None = None, mode: str = "a", args: object = SFA_ARGS) -> dict:
    return run(SFA, args, rules, capture=capture, mode=mode, script=SFA_SCRIPT)


def test_freshness_audit_baseline_is_complete() -> None:
    res = sfa(sfa_rules())["result"]
    assert_payload_shape(res)
    assert res["status"] == "complete" and res["report"] == "freshness-report.md"
    assert (res["confirmed"], res["rejected"], res["unverified"], res["unchecked"]) == (2, 0, 0, [])
    sk, vf = res["coverage"]["skills"], res["coverage"]["verification"]
    assert (sk["requested"], sk["completed"], sk["unresolved"]) == (3, 3, 0)
    assert (vf["requested"], vf["completed"], vf["unresolved"]) == (2, 2, 0)


@pytest.mark.parametrize("mode", ["a", "b", "mixed"])
def test_freshness_audit_reaches_every_stage(mode: str) -> None:
    """Only the inventory and audit are pinned; the verifier, writer, and read-back use fake data per mode."""
    fixtures = [ret("^inventory", {"domains": [{"domain": "databases", "skills": SFA_SKILLS}]}), ret("^databases batch 1", SFA_AUDIT)]
    out = sfa(fixtures, mode=mode)
    assert out["phases"] == ["Inventory", "Audit", "Verify", "Report"]
    assert_payload_shape(out["result"])


@pytest.mark.parametrize("fault", ["null", "throw"])
def test_freshness_audit_failed_verifier_is_unverified_not_rejected(fault: str) -> None:
    out = sfa(sfa_rules(act("^verify alterlab-pubmed", fault)), capture="^(write report|verify alterlab-openalex)")
    res = out["result"]
    assert (res["confirmed"], res["rejected"], res["unverified"]) == (1, 0, 1), "a verifier that did not complete must not count as a rejection"
    assert res["unverified_findings"][0]["skill"] == "alterlab-pubmed"
    vf = res["coverage"]["verification"]
    assert (vf["requested"], vf["dispatched"], vf["completed"], vf["failed"], vf["retried"]) == (2, 2, 1, 1, 1)
    assert out["calls"].count("verify alterlab-pubmed: version (retry)") == 1, "retries are bounded at one"
    assert res["status"] == "partial"
    report = prompt_of(out, "^write report$")
    assert "alterlab-pubmed" not in section(report, "Rejected:", "UNVERIFIED (verifier did not complete):")
    assert "alterlab-pubmed" in section(report, "UNVERIFIED (verifier did not complete):", "Unchecked skills:")
    assert "not independent verification" in report
    assert prompt_of(out, "^verify alterlab-openalex").startswith("Separately verify")


def test_freshness_audit_verifier_retry_and_rejection() -> None:
    once = sfa(sfa_rules(act("^verify alterlab-pubmed", "throw", times=1)))["result"]
    assert (once["confirmed"], once["unverified"], once["status"]) == (2, 0, "complete")
    assert once["coverage"]["verification"]["retried"] == 1
    rejected = sfa(sfa_rules(act("^verify alterlab-openalex", "set", values={"confirmed": False})))["result"]
    assert (rejected["confirmed"], rejected["rejected"], rejected["unverified"], rejected["status"]) == (1, 1, 0, "complete")


def test_freshness_audit_failed_or_partial_batch_is_unchecked() -> None:
    failed = sfa(sfa_rules(act("^databases batch 1", "null")))["result"]
    assert failed["unchecked"] == [f"databases/{s}" for s in SFA_SKILLS], "a failed audit batch is not 'audited with no findings'"
    sk = failed["coverage"]["skills"]
    assert (sk["dispatched"], sk["completed"], sk["failed"], sk["retried"]) == (3, 0, 3, 1)
    assert failed["confirmed"] == 0 and failed["status"] == "partial"
    partial = sfa(sfa_rules(act("^databases batch 1", "set", values={"checked": ["alterlab-pubmed"]})))["result"]
    assert partial["unchecked"] == ["databases/alterlab-openalex", "databases/alterlab-arxiv"] and partial["status"] == "partial"
    # The retry re-sends only the omitted skills; it repeats both findings and names pubmed again.
    recovered = sfa(sfa_rules(act("^databases batch 1", "set", values={"checked": ["alterlab-pubmed"]}, times=1)))["result"]
    assert recovered["unchecked"] == [] and recovered["status"] == "complete"
    assert recovered["confirmed"] == 2, "a finding reported again on the retry counts once"
    assert recovered["coverage"]["id_issues"]["duplicate"] == 2 and recovered["coverage"]["id_issues"]["unknown"] == 1


def test_freshness_audit_ignores_findings_for_skills_not_sent() -> None:
    res = sfa(sfa_rules(act("^databases batch 1", "unknown_id", field="findings", id_field="skill")))["result"]
    assert res["confirmed"] == 2 and res["coverage"]["verification"]["requested"] == 2
    assert res["coverage"]["id_issues"]["unknown"] == 1


def test_freshness_audit_report_must_exist() -> None:
    out = sfa(sfa_rules(act("^write report", "throw")))
    res = out["result"]
    assert_payload_shape(res)
    assert res["status"] == "blocked" and res["report"] is None and res["confirmed"] == 2
    assert "write report (retry)" in out["calls"]
    missing = sfa(sfa_rules(act("^confirm report on disk", "set", values={"exists": False, "bytes": 0})))
    assert missing["result"]["status"] == "blocked" and missing["result"]["report"] is None
    assert any("not found on disk" in r for r in missing["result"]["status_reasons"])
    assert "write report (retry)" in missing["calls"]


def test_freshness_audit_inventory_failures() -> None:
    out = sfa([act("^inventory", "null")])
    assert_payload_shape(out["result"])
    assert out["result"]["status"] == "blocked" and out["calls"] == ["inventory", "inventory (retry)"]
    args = {"domains": ["databases", "chemistry"]}
    res = sfa(sfa_rules(status="PARTIAL"), args=args)["result"]
    assert res["coverage"]["inventory"]["domains_missing"] == ["chemistry"] and res["status"] == "partial"


# ============================================================== the harness itself
def _raw(name: str, args: object, scenario: object) -> dict:
    proc = subprocess.run(
        [NODE, str(DRYRUN), str(WORKFLOWS / f"{name}.js"), json.dumps(args), "a", json.dumps(scenario)],
        capture_output=True, text=True, timeout=60, cwd=REPO_ROOT,
    )
    return json.loads((proc.stdout.strip().splitlines() or ["{}"])[-1])


def test_harness_rejects_malformed_scenarios() -> None:
    bad_action = _raw(CA, CA_ARGS, {"rules": [{"match": "x", "action": "explode"}]})
    assert not bad_action["ok"] and "unknown action" in bad_action["error"]
    both = _raw(CA, CA_ARGS, {"rules": [{"match": "x", "action": "null", "return": {}}]})
    assert not both["ok"]
    # A fixture must look like a real structured output.
    off_schema = _raw(CA, CA_ARGS, {"rules": [ret("^extract references", {"references": "not a list"})]})
    assert not off_schema["ok"] and "fixture" in off_schema["error"]
    bad_enum = _raw(CA, CA_ARGS, {"rules": [ret("^extract references", ca_doc()), ret("^references ", {"results": [{"id": "R1", "verdict": "FINE", "evidence": "e"}]})]})
    assert not bad_enum["ok"] and "not one of" in bad_enum["error"]


def test_harness_skip_and_times_count_matching_calls() -> None:
    # skip the first matching call, fail the next one only: the first write succeeds, so no retry happens.
    out = run(CA, CA_ARGS, ca_rules(act("^write integrity report", "throw", skip=1, times=1)))
    assert out["calls"].count("write integrity report") == 1 and "write integrity report (retry)" not in out["calls"]
    assert out["faults"] == 0
    out = run(CA, CA_ARGS, ca_rules(act("^write integrity report", "throw", times=1)))
    assert out["faults"] == 1 and "write integrity report (retry)" in out["calls"]


# ============================================================== all workflows
# The seven plugin workflows plus the maintainer workflow.
ALL_SCRIPTS = [*sorted(WORKFLOWS.glob("*.js")), SFA_SCRIPT]


@pytest.mark.parametrize("script", ALL_SCRIPTS, ids=lambda p: p.stem)
def test_no_independence_claims_for_same_model_agents(script: Path) -> None:
    """Separate contexts of one model are not independent verification; the scripts must not say so."""
    text = script.read_text(encoding="utf-8").lower()
    for phrase in ("independent re-check", "independent reviewer", "independent screener", "two independent",
                   "independent multi-reviewer", "genuinely independent", "independently"):
        assert phrase not in text, f"{script.name} still says '{phrase}'"
    assert "same model" in text, f"{script.name} should tell the report writer that same-model agreement is not independent"


PLAYBOOK = REPO_ROOT / "skills" / "workflows" / "alterlab-research-workflows"


@pytest.mark.parametrize("doc", [PLAYBOOK / "SKILL.md", *sorted((PLAYBOOK / "references").glob("*.md"))], ids=lambda p: p.name)
def test_playbooks_do_not_claim_independence(doc: Path) -> None:
    text = doc.read_text(encoding="utf-8")
    if doc.name == "SKILL.md":
        # Body only: the frontmatter description is mirrored into generated catalogs outside this tree.
        text = text.split("\n---\n", 1)[1]
    for phrase in ("independent re-check", "independent reviewer", "independent screener", "two independent",
                   "genuinely independent", "independently", "**independence.**"):
        assert phrase not in text.lower(), f"{doc.name} still says '{phrase}'"


@pytest.mark.parametrize("script", sorted(WORKFLOWS.glob("*.js")), ids=lambda p: p.stem)
def test_each_playbook_documents_status_and_payload(script: Path) -> None:
    text = (PLAYBOOK / "references" / f"{script.stem}.md").read_text(encoding="utf-8")
    assert "## Returned payload" in text and "`partial`" in text, f"{script.stem}.md should document status and the payload"


@pytest.mark.parametrize("script", ALL_SCRIPTS, ids=lambda p: p.stem)
def test_failed_report_always_blocks(script: Path) -> None:
    """Every workflow: when no report-writing agent succeeds, there is no report path and the run is blocked."""
    from tests.test_workflows import SAMPLE_ARGS

    writers = r"^(write integrity report|editor-in-chief|PRISMA report|write report|assemble letter|summary statement|write map)"
    res = run(script.stem, SAMPLE_ARGS[script.stem], [act(writers, "throw")], script=script)["result"]
    assert_payload_shape(res)
    assert res["report"] is None and res["status"] == "blocked"
