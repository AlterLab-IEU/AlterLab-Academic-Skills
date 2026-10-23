"""Regression tests: BibTeX parsing and input accounting in verify_citations.py.

Covers the reported defects (single-line entries and indented closing braces parsed as
zero entries; mixed bibliographies silently losing entries), the BibTeX syntax the
tokenizer must handle, actionable diagnostics for malformed input, the rule that a
partial audit can never pass, and conservative network behaviour.

No test touches the network: an autouse fixture replaces the HTTP layer with a guard
that fails the test on any outbound call, and the network tests inject failures.
"""

from __future__ import annotations

import email.message
import importlib.util
import json
import random
import socket
import sys
import types
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "core" / "alterlab-citation-verifier"
SCRIPT = SKILL_DIR / "scripts" / "verify_citations.py"
FIXTURES = SKILL_DIR / "evals" / "fixtures"
EDGE_BIB = FIXTURES / "bibtex_edge_cases.bib"
MIXED_BIB = FIXTURES / "bibtex_mixed_malformed.bib"
MODULE_NAME = "alterlab_verify_citations_under_test"


def _load_module():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module  # before exec_module: @dataclass looks the module up
    spec.loader.exec_module(module)
    return module


vc = _load_module()
REAL_HTTP_GET = vc._http_get


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Fail loudly on any real HTTP call; make retries/backoff instant."""

    def guard(*args, **kwargs):
        pytest.fail(f"test attempted network access: {args[:1]}")

    monkeypatch.setattr(vc, "_http_get", guard)
    monkeypatch.setattr(vc.urllib.request, "urlopen", guard)
    monkeypatch.setattr(vc, "_HAS_REQUESTS", False)
    monkeypatch.setattr(vc, "_requests", None)
    monkeypatch.setattr(vc.time, "sleep", lambda _s: None)


def parse(text: str, fmt: str = "auto"):
    res = vc.parse_input(text, fmt)
    assert_accounted(res)
    return res


def assert_accounted(res) -> None:
    """Every detected entry is in exactly one bucket, and every diagnostic is actionable."""
    assert res.detected == len(res.entries) + len(res.rejected) + len(res.unsupported)
    for d in res.rejected + res.unsupported:
        assert isinstance(d["line"], int) and d["line"] >= 1, d
        assert d["end_line"] >= d["line"] and d["error_line"] >= 1, d
        assert d["reason"], d
    for e in res.entries:
        assert e.fmt in ("bibtex", "freeform", "doi"), e
        assert e.line >= 1, e


def verified_stub(entry, mailto, threshold, offline):
    """Stand-in for verify_entry when every lookup succeeds (no network)."""
    return vc._verdict(entry, vc._ref_id(entry), "verified", detail="stub", matches=[])


def run_main(capsys, *argv):
    rc = vc.main([str(a) for a in argv])
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


# --------------------------------------------------------------------------- #
# Reported defects                                                            #
# --------------------------------------------------------------------------- #


def test_single_line_entry_parses():  # defect 1
    text = "@article{key, title={X}, author={Y}, year={2020}}"
    res = parse(text)
    assert [e.key for e in res.entries] == ["key"]
    e = res.entries[0]
    assert (e.title, e.authors, e.year) == ("X", ["Y"], "2020")
    assert (e.fmt, e.line, e.entry_type) == ("bibtex", 1, "article")
    assert res.complete and res.format_detected == "bibtex"
    # The legacy list-returning API sees the same entry.
    assert [x.key for x in vc.parse_bibliography(text, "auto")] == ["key"]
    assert [x.key for x in vc.parse_bibtex(text)] == ["key"]


@pytest.mark.parametrize("closing", ["  }", "\t}", "        }", "}", "    }   ", "  )"])
def test_indented_or_outdented_closing_delimiter(closing):  # defect 2
    opener = "(" if ")" in closing else "{"
    text = (f"@article{opener}key2,\n  title = {{Deep learning}},\n  author = {{LeCun, Yann}},\n"
            f"  year = {{2015}}\n{closing}\n")
    res = parse(text)
    assert [(e.key, e.title, e.authors, e.year) for e in res.entries] == [
        ("key2", "Deep learning", ["LeCun, Yann"], "2015")]
    assert res.complete


def test_closing_brace_on_the_last_field_line():
    res = parse("@book{k,\n  title = {T},\n  year = {2001}}")
    assert [(e.key, e.title, e.year) for e in res.entries] == [("k", "T", "2001")]


def test_mixed_bibliography_from_the_report_loses_nothing():  # defect 3
    text = (
        "@article{good1,\n  title={A good one},\n  author={Smith, J.},\n  year={2019}\n}\n"
        "@article{inline, title={Inline entry}, author={Doe, J.}, year={2020}}\n"
        "@misc{broken,\n  title={Missing a brace,\n  year={2021}\n}\n"
        "@article{good2,\n  title={Second good},\n  author={Roe, R.},\n  year={2018}\n}\n"
        "Vaswani, A., & Shazeer, N. (2017). Attention is all you need. NeurIPS.\n"
        "doi:10.1038/s41598-023-41032-5\n"
    )
    res = parse(text)
    assert res.detected == 6  # the pre-fix parser returned 3 of these, one with a garbled title
    assert [e.key for e in res.entries if e.fmt == "bibtex"] == ["good1", "inline", "good2"]
    assert [e.title for e in res.entries][:3] == ["A good one", "Inline entry", "Second good"]
    assert {e.fmt for e in res.entries} == {"bibtex", "freeform", "doi"}
    assert [(d["key"], d["line"]) for d in res.rejected] == [("broken", 7)]
    assert "unbalanced braces" in res.rejected[0]["reason"]
    assert not res.complete and res.format_detected == "mixed"


def test_mixed_fixture_accounts_for_every_entry():
    res = parse(MIXED_BIB.read_text(encoding="utf-8"))
    assert (res.detected, len(res.entries), len(res.rejected), len(res.unsupported)) == (9, 5, 3, 1)
    assert [(e.fmt, e.key, e.line) for e in res.entries] == [
        ("bibtex", "walters2023", 6), ("bibtex", "kaplan2020", 18), ("freeform", "", 26),
        ("doi", "", 28), ("bibtex", "vaswani2017", 29)]
    assert res.entries[2].title.startswith("The pen is mightier than the keyboard")
    assert res.entries[3].doi == "10.1177/0956797614524581"
    rejected = {d["key"]: d for d in res.rejected}
    assert set(rejected) == {"unbalanced2020", None, "missingcomma2019"}
    assert rejected["unbalanced2020"]["line"] == 13
    assert "unbalanced braces" in rejected["unbalanced2020"]["reason"]
    assert "line 18" in rejected["unbalanced2020"]["reason"]
    assert "missing citation key" in rejected[None]["reason"] and rejected[None]["line"] == 19
    assert "missing comma after citation key 'missingcomma2019'" in rejected["missingcomma2019"]["reason"]
    assert rejected["missingcomma2019"]["error_line"] == 21
    (unsupported,) = res.unsupported
    assert unsupported["key"] == "custom2022" and "@patentapplication" in unsupported["reason"]


# --------------------------------------------------------------------------- #
# BibTeX syntax the tokenizer must handle                                     #
# --------------------------------------------------------------------------- #


def test_edge_case_fixture_parses_completely():
    res = parse(EDGE_BIB.read_text(encoding="utf-8"))
    assert res.complete and res.format_detected == "bibtex"
    assert [e.key for e in res.entries] == [
        "walters2023", "mueller2014", "vaswani2017", "kaplan2020", "schrodinger1935"]
    assert sorted(b["entry_type"] for b in res.skipped) == ["comment", "preamble", "string"]
    by_key = {e.key: e for e in res.entries}
    m = by_key["mueller2014"]  # quoted values, @string + '#', bare numbers, trailing comma
    assert m.title == "The pen is mightier than the keyboard: Advantages of longhand over laptop note taking"
    assert m.authors == ["Mueller, Pam A.", "Oppenheimer, Daniel M."]
    assert (m.venue, m.year, m.doi) == ("Psychological Science", "2014", "10.1177/0956797614524581")
    v = by_key["vaswani2017"]  # @INPROCEEDINGS( ... ) with a trailing comma
    assert (v.entry_type, v.arxiv_id, len(v.authors)) == ("inproceedings", "1706.03762", 8)
    assert v.authors[6] == "Kaiser, \\Lukasz"
    assert by_key["kaplan2020"].authors == ["Kaplan, Jared"]  # "and others" is dropped
    assert by_key["kaplan2020"].line == by_key["schrodinger1935"].line == 29  # one line


def test_nested_braces_in_values():
    res = parse("@article{n1, title={The {DNA} of {X {Y {Z}}}}, author={Doe, J.}, year=2001}")
    assert res.entries[0].title == "The DNA of X Y Z"


def test_quoted_values_with_braces_and_escaped_quotes():
    res = parse('@article{q1, title = "Deep {L}earning with {"}quotes{"} and {\\"o}", '
                'author = "Doe, Jane and Roe, Richard", year = "1999"}')
    e = res.entries[0]
    assert e.title == 'Deep Learning with "quotes" and \\"o'
    assert e.authors == ["Doe, Jane", "Roe, Richard"]
    assert e.year == "1999"


def test_parentheses_delimited_entry():
    res = parse("@article(p1, title={X (Y) Z}, author={A, B}, year=2020)")
    assert [(e.key, e.title, e.year) for e in res.entries] == [("p1", "X (Y) Z", "2020")]


def test_multiple_entries_on_one_line():
    res = parse('@article{a, title={A}} @book{b, title={B}}  @misc(c, title="C")')
    assert [(e.key, e.entry_type, e.title, e.line) for e in res.entries] == [
        ("a", "article", "A", 1), ("b", "book", "B", 1), ("c", "misc", "C", 1)]


def test_trailing_and_doubled_commas():
    res = parse("@article{t1,\n  title={T},\n  year={2020},\n}\n@article{t2, title={T2},, year={2021},}")
    assert [(e.key, e.year) for e in res.entries] == [("t1", "2020"), ("t2", "2021")]
    assert res.complete
    assert any("extra ','" in w for w in res.entries[1].warnings)


def test_entry_types_and_field_names_are_case_insensitive():
    res = parse("@ARTICLE{C1, TITLE={Upper}, Author={Smith, J.}, YEAR={2010}}\n"
                "@InProceedings{C2, Title={Mixed}, aUtHoR={Doe, J.}}")
    assert [(e.key, e.entry_type, e.title, e.authors) for e in res.entries] == [
        ("C1", "article", "Upper", ["Smith, J."]), ("C2", "inproceedings", "Mixed", ["Doe, J."])]


def test_string_macros_concatenation_and_month_names():
    res = parse('@string{jcl = "Journal of " # "Comp. Ling."}\n@STRING(pre = {The })\n'
                '@article{m1, title = pre # {DNA} # " story", journal = jcl, month = jan, year = 2001}')
    (e,) = res.entries
    assert (e.title, e.venue, e.year) == ("The DNA story", "Journal of Comp. Ling.", "2001")
    assert [b["entry_type"] for b in res.skipped] == ["string", "string"]
    assert res.complete


def test_string_defined_after_use_still_expands():
    res = parse("@article{late, title={T}, journal = jx}\n@string{jx = {Late Journal}}")
    assert res.entries[0].venue == "Late Journal"


def test_undefined_macro_in_a_checked_field_is_rejected_not_guessed():
    res = parse("@article{u1, title = nosuch, year = 2001}")
    assert not res.entries
    (d,) = res.rejected
    assert d["key"] == "u1" and "undefined @string macro 'nosuch'" in d["reason"]


def test_undefined_macro_in_other_fields_is_a_warning():
    res = parse("@article{u2, title = {Fine}, journal = nosuch, year = 2001}")
    (e,) = res.entries
    assert e.venue == "nosuch" and any("nosuch" in w for w in e.warnings)
    assert res.complete and res.warnings and res.warnings[0]["key"] == "u2"


def test_comment_preamble_and_string_blocks_are_skipped_but_listed():
    res = parse('@comment{ @article{old, title={Old}} }\n@preamble{ "\\newcommand{\\x}{y}" }\n'
                "@Comment{jabref-meta: databaseType:bibtex;}\n@article{k, title={Kept}}")
    assert [e.key for e in res.entries] == ["k"]  # the entry inside @comment is not parsed
    assert [(b["line"], b["entry_type"]) for b in res.skipped] == [
        (1, "comment"), (2, "preamble"), (3, "comment")]
    assert res.detected == 1 and res.complete


def test_set_xdata_and_commented_out_entries_are_listed_not_verified():
    res = parse("@set{s1, entryset={a,b}}\n@xdata{x1, publisher={P}}\n"
                "% @article{old,\n%   title = {Old},\n% }\n@article{a, title={A}}")
    assert [e.key for e in res.entries] == ["a"]
    assert [(b["entry_type"], b["key"]) for b in res.skipped] == [
        ("set", "s1"), ("xdata", "x1"), ("commented-out", "old")]
    assert res.complete


def test_percent_comment_line_inside_an_entry_is_skipped_with_a_warning():
    res = parse("@article{k,\n  % title = {old},\n  title = {new},\n}")
    (e,) = res.entries
    assert e.title == "new" and any("'%' comment line" in w for w in e.warnings)


def test_latex_accents_pass_through_and_compare_folded():
    res = parse(r"@article{acc, title={Schr{\"o}dinger's {Cat}}, "
                r"author={M{\"u}ller, J{\"o}rg and {\'E}mile Zola and Kaiser, {\L}ukasz}}")
    (e,) = res.entries
    assert e.title == "Schr\\\"odinger's Cat"  # passed through, not mangled
    assert e.authors == ['M\\"uller, J\\"org', "\\'Emile Zola", "Kaiser, \\Lukasz"]
    assert vc._surname(e.authors[0]) == "müller"
    assert vc.author_overlap(e.authors, ["Müller", "Zola", "Kaiser"]) == 1.0
    assert vc.title_ratio(e.title, "Schrödinger's cat") == pytest.approx(1.0)


def test_braced_corporate_authors_are_not_split_on_and():
    res = parse("@techreport{who, title={Report}, author={{World Health Organization} and "
                "{Food and Agriculture Organization}}}")
    assert res.entries[0].authors == ["World Health Organization", "Food and Agriculture Organization"]


def test_crlf_line_endings_bom_and_email_at_signs():
    res = parse("﻿@article{w1,\r\n  title = {Windows},\r\n  note = {mail foo@bar.com},\r\n"
                "  year = {2019}\r\n}\r\n@article{w2, title={Two}}\r\n")
    assert [(e.key, e.title, e.year, e.line) for e in res.entries] == [
        ("w1", "Windows", "2019", 1), ("w2", "Two", "", 6)]


def test_unknown_entry_type_is_unsupported_with_reason():
    res = parse("@foo{f1, title={X}}")
    assert not res.entries and not res.complete
    (d,) = res.unsupported
    assert d["key"] == "f1" and d["entry_type"] == "foo" and "@foo" in d["reason"]


def test_duplicate_keys_and_fields_are_warned_and_first_value_kept():
    res = parse("@article{d, title={One}, title={Ignored}}\n@article{D, title={Two}}")
    assert [(e.key, e.title) for e in res.entries] == [("d", "One"), ("D", "Two")]
    assert any("duplicate field 'title'" in w for w in res.entries[0].warnings)
    assert any("duplicate citation key" in w for w in res.entries[1].warnings)


# --------------------------------------------------------------------------- #
# Malformed input: actionable diagnostics, no collateral loss, no crash       #
# --------------------------------------------------------------------------- #

MALFORMED = [
    # id, text, reason fragment, key, error line
    ("unbalanced-braces", "@article{ub, title={Open,\n  year={2001}\n}\n@article{ok, title={Fine}}",
     "unbalanced braces", "ub", 1),
    ("unbalanced-at-eof", "@article{ok, title={Fine}}\n@article{ub, title={Never closed, year={2001}",
     "unbalanced braces", "ub", 2),
    ("missing-key", "@article{, title={X}}", "missing citation key", None, 1),
    ("field-instead-of-key", "@article{title={X}, year={2020}}", "missing citation key", None, 1),
    ("missing-comma-after-key", "@article{smith2020\n  title={X}}",
     "missing comma after citation key 'smith2020'", "smith2020", 2),
    ("space-in-key", "@article{Smith 2020, title={X}}", "keys cannot contain spaces", "Smith", 1),
    ("missing-comma-between-fields", "@article{mc,\n  title={X}\n  author={Y}}",
     "missing comma after field 'title'", "mc", 3),
    ("unterminated-quote", '@article{uq,\n  title = "No closing quote,\n  year = {2001}}',
     "unterminated quote", "uq", 2),
    ("missing-equals", "@article{me, title {X}}", "missing '=' after field name 'title'", "me", 1),
    ("missing-open-brace", "@article nb,\n  title={X},\n}", "missing '{' or '(' after '@article'", "nb", 1),
    ("unbraced-nonnumeric", "@article{pg, title={X}, pages = 1--10}",
     "missing comma after field 'pages'", "pg", 1),
    ("closed-early", "@article{ec,\n  title={X}},\n  year={2001}\n}", "closed early", None, 2),
    ("malformed-string", "@string{x = }\n@article{k, title={T}}", "malformed @string", None, 1),
]


@pytest.mark.parametrize("text, fragment, key, error_line", [m[1:] for m in MALFORMED],
                         ids=[m[0] for m in MALFORMED])
def test_malformed_entry_diagnostics(text, fragment, key, error_line):
    res = parse(text)
    hits = [d for d in res.rejected if fragment in d["reason"]]
    assert hits, [d["reason"] for d in res.rejected]
    d = hits[0]
    assert d["key"] == key
    assert d["error_line"] == error_line
    assert d["format"] == "bibtex" and d["excerpt"]
    assert not res.complete


def test_a_malformed_entry_does_not_swallow_the_entries_after_it():
    text = ("@article{a, title={A}}\n@article{bad, title={Unclosed, year={2001}\n"
            "@article{b, title={B}}\n@article{c, title = \"Unterminated}\n@article{d, title={D}}\n"
            "@article{e, title={E} @article{f, title={F}}")
    res = parse(text)
    assert [e.key for e in res.entries] == ["a", "b", "d", "f"]
    assert [d["key"] for d in res.rejected] == ["bad", "c", "e"]
    assert "missing closing '}' before the next entry" in res.rejected[2]["reason"]


GARBAGE = [
    "@", "@article", "@article{", "@article{k,", "@article{k, title={", '@article{k, title="',
    "}}}}", "{{{{", "@string{x = }", "@comment{", "@preamble{", '@string{a = "x" # }',
    "@article(k, title={x}", "@article{k, title=}", "@article{k, = {x}}", "@@@@",
    "@article{k, title={x}}}}}", "@article{k, title = {x} # }", "\x00@article{k}",
    "@article{k, title = {x} # nosuch # \"y\"}", "%\n%%\n@", "@article{k, title=\"a{b\"}",
    "@article(k, title={a)b})", "@ARTICLE {k ,title={x},}", "@misc{k}", "@misc{k,}",
]


@pytest.mark.parametrize("fmt", ["auto", "bibtex", "doi", "freeform"])
@pytest.mark.parametrize("text", GARBAGE)
def test_parser_never_crashes_and_always_accounts(text, fmt):
    parse(text, fmt)


def test_parser_survives_random_brace_soup():
    rng = random.Random(20261014)
    alphabet = '@{}()",=# \n%abcT12\\'
    for _ in range(400):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 80)))
        for fmt in ("auto", "bibtex"):
            parse(text, fmt)


# --------------------------------------------------------------------------- #
# Other input formats are preserved                                           #
# --------------------------------------------------------------------------- #


def test_freeform_fixture_parses_as_before():
    res = parse((FIXTURES / "bibliography_24_entries.md").read_text(encoding="utf-8"))
    assert res.format_detected == "freeform" and res.complete
    # 24 numbered references plus the heading and intro paragraph, exactly as v1.1.0 split it.
    assert len(res.entries) == 26
    numbered = [e for e in res.entries if e.raw[:3].rstrip(". ").isdigit()]
    assert len(numbered) == 24
    assert numbered[0].title == "Attention is all you need" and numbered[0].year == "2017"
    assert [e.line for e in res.entries] == sorted(e.line for e in res.entries)


def test_doi_list_is_unchanged():
    text = ("10.1038/s41598-023-41032-5\nhttps://doi.org/10.1177/0956797614524581\n"
            "arXiv:1706.03762\n# a comment\n2001.08361v2\n")
    res = parse(text)
    assert res.format_detected == "doi" and res.complete
    assert [(e.doi, e.arxiv_id, e.line) for e in res.entries] == [
        ("10.1038/s41598-023-41032-5", "", 1), ("10.1177/0956797614524581", "", 2),
        ("", "1706.03762", 3), ("", "2001.08361", 5)]


def test_mostly_identifier_list_keeps_its_full_references():
    text = ("10.1038/s41598-023-41032-5\n10.1177/0956797614524581\n2001.08361\n"
            "Smith, J. (2020). A free-form one. Journal.\nDOIs:")
    res = parse(text)
    assert [e.fmt for e in res.entries] == ["doi", "doi", "doi", "freeform"]
    assert res.entries[3].title == "A free-form one"
    assert [d["line"] for d in res.ignored_text] == [5] and res.complete


def test_explicit_doi_format_flags_lines_without_identifiers():
    res = parse("10.1038/s41598-023-41032-5\nSmith, J. (2020). A free-form one. Journal.\nReferences:",
                "doi")
    assert [e.doi for e in res.entries] == ["10.1038/s41598-023-41032-5"]
    (d,) = res.unsupported
    assert d["line"] == 2 and "--format doi reads identifiers only" in d["reason"]


def test_explicit_bibtex_format_flags_non_bibtex_references():
    res = parse("@article{z, title={Z}}\nSmith, J. (2020). A free-form one. Journal.\n", "bibtex")
    assert [e.key for e in res.entries] == ["z"]
    (d,) = res.unsupported
    assert d["line"] == 2 and "--format auto" in d["reason"]


def test_lone_stray_brace_is_a_warning_but_stray_fields_are_rejected():
    res = parse("@article{a, title={A}}\n}\n@article{b, title={B}}")
    assert [e.key for e in res.entries] == ["a", "b"] and res.complete
    assert [(w["line"], w["reason"]) for w in res.warnings] == [(2, "stray brace(s) outside any entry ignored")]
    res = parse("@article{a, title={A}}\n  year = {2001}\n}\n")
    assert not res.complete and "entry 'a' was probably closed early" in res.rejected[0]["reason"]


def test_bibtex_header_prose_is_listed_not_counted():
    res = parse("Automatically generated by Mendeley Desktop.\n\n@article{z, title={Z}}\n")
    assert [e.key for e in res.entries] == ["z"] and res.complete
    assert [d["line"] for d in res.ignored_text] == [1]


def test_unknown_format_raises_value_error():
    with pytest.raises(ValueError):
        vc.parse_input("x", "ris")


# --------------------------------------------------------------------------- #
# Partial input can never produce a passing verdict                           #
# --------------------------------------------------------------------------- #


def _report(text: str, verify=verified_stub, accounting: bool = True):
    res = vc.parse_input(text)
    results = [verify(e, "x", 0.7, False) for e in res.entries]
    acc = vc.input_accounting(res, processed=len(results)) if accounting else None
    return vc.build_report(results, "x", 0.7, False, accounting=acc)


def test_partial_parse_is_partial_even_when_every_parsed_entry_verifies():
    report = _report(MIXED_BIB.read_text(encoding="utf-8"))
    assert report["status"] == "partial"
    assert report["summary"]["verdict"] == "PARTIAL"
    assert report["summary"]["verdict_counts"]["verified"] == 5  # every parsed entry "passed"
    assert report["warning"].startswith("PARTIAL AUDIT: 4 of 9 detected entries were not verified")
    assert report["summary"]["notes"][0] == report["warning"]
    assert report["summary"]["input"] == {"detected": 9, "parsed": 5, "rejected": 3,
                                          "unsupported": 1, "processed": 5, "unprocessed": 0}
    acc = report["input_accounting"]
    assert acc["complete"] is False and acc["format_detected"] == "mixed"
    assert acc["parsed_by_format"] == {"bibtex": 3, "doi": 1, "freeform": 1}
    assert len(acc["rejected_entries"]) == 3 and len(acc["unsupported_entries"]) == 1
    keys = list(report)
    assert keys.index("status") < keys.index("summary") and keys.index("warning") < keys.index("summary")


def test_complete_parse_with_verified_entries_still_passes():
    report = _report(EDGE_BIB.read_text(encoding="utf-8"))
    assert (report["status"], report["warning"], report["summary"]["verdict"]) == ("complete", None, "PASS")
    assert report["input_accounting"]["non_reference_blocks"] == {"comment": 1, "preamble": 1, "string": 1}


def test_unsupported_only_input_is_not_a_pass():
    report = _report("@article{a, title={A}}\n@foo{f, title={F}}")
    assert report["summary"]["verdict"] == "PARTIAL" and report["status"] == "partial"


def test_serious_findings_still_fail_on_partial_input():
    def placeholder(entry, *_):
        return vc._verdict(entry, vc._ref_id(entry), "PH", detail="stub", matches=[])

    report = _report(MIXED_BIB.read_text(encoding="utf-8"), verify=placeholder)
    assert report["summary"]["verdict"] == "FAIL" and report["status"] == "partial"


def test_build_report_does_not_trust_inconsistent_accounting():
    res = vc.parse_input(EDGE_BIB.read_text(encoding="utf-8"))
    results = [verified_stub(e, "x", 0.7, False) for e in res.entries[:2]]
    acc = vc.input_accounting(res, processed=5)  # claims more than was verified
    acc["complete"] = True
    report = vc.build_report(results, "x", 0.7, False, accounting=acc)
    assert report["status"] == "partial" and report["summary"]["verdict"] == "PARTIAL"


def test_build_report_with_no_results_is_never_a_pass():
    report = vc.build_report([], "x", 0.7, False)
    assert report["summary"]["verdict"] not in ("PASS", "PASS_WITH_CONDITIONS")


def test_legacy_build_report_call_still_works():
    report = _report(EDGE_BIB.read_text(encoding="utf-8"), accounting=False)
    assert report["status"] == "complete" and report["summary"]["verdict"] == "PASS"


# --------------------------------------------------------------------------- #
# CLI: exit codes, banner, report                                             #
# --------------------------------------------------------------------------- #


def test_cli_partial_run_exits_3_with_banner_and_report(capsys, tmp_path):
    out = tmp_path / "report.json"
    rc, stdout, stderr = run_main(capsys, MIXED_BIB, "--offline", "--out", out)
    assert rc == 3
    assert stderr.index("WARNING: PARTIAL AUDIT") < stderr.index("wrote 5 verdicts")
    assert "line 13 [unbalanced2020] rejected: unbalanced braces" in stderr
    assert "line 24 [custom2022] unsupported: unknown entry type '@patentapplication'" in stderr
    assert "status=partial" in stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "partial" and report["summary"]["verdict"] == "PARTIAL"
    assert report["input_accounting"]["detected"] == 9
    assert [e["input"]["line"] for e in report["entries"]] == [6, 18, 26, 28, 29]


def test_cli_complete_run_exits_0_without_banner(capsys):
    rc, stdout, stderr = run_main(capsys, EDGE_BIB, "--offline")
    assert rc == 0 and "WARNING" not in stderr
    report = json.loads(stdout)
    assert report["status"] == "complete"
    assert report["summary"]["verdict"] == "UNVERIFIED"  # offline is never a pass
    assert {e["verdict"] for e in report["entries"]} == {"unverified"}


def test_cli_inline_single_line_entry_is_verified_not_rejected(capsys):
    rc, stdout, _ = run_main(capsys, "@article{key, title={X}, author={Y}, year={2020}}", "--offline")
    assert rc == 0  # before the fix: "no bibliography entries parsed", exit 2
    assert json.loads(stdout)["summary"]["total"] == 1


def test_cli_exits_2_when_no_entry_can_be_parsed(capsys):
    rc, stdout, stderr = run_main(capsys, "@article{, title={X}}", "--offline")
    assert rc == 2
    assert "missing citation key" in stderr and "none of the 1 detected entries" in stderr
    report = json.loads(stdout)  # diagnostics are still delivered
    assert report["summary"]["verdict"] == "PARTIAL"
    assert report["input_accounting"]["rejected_entries"][0]["reason"].startswith("missing citation key")


def test_cli_exits_2_when_nothing_is_detected(capsys):
    rc, stdout, stderr = run_main(capsys, "@comment{nothing to see}", "--offline")
    assert rc == 2 and stdout == "" and "no bibliography entries" in stderr


def test_cli_help_and_docstring_document_exit_codes(capsys):
    with pytest.raises(SystemExit) as exc:
        vc.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for text in (help_text, vc.__doc__):
        assert "xit codes" in text
        assert "0  complete audit" in text and "3  partial audit" in text and "2  bad input" in text


def test_interrupted_run_reports_unprocessed_entries(monkeypatch, capsys):
    done = []

    def interrupt_after_first(entry, *args):
        if done:
            raise KeyboardInterrupt
        done.append(entry.key)
        return verified_stub(entry, *args)

    monkeypatch.setattr(vc, "verify_entry", interrupt_after_first)
    rc, stdout, stderr = run_main(capsys, EDGE_BIB)
    assert rc == 3 and "interrupted" in stderr
    report = json.loads(stdout)
    assert report["status"] == "partial" and report["summary"]["verdict"] == "PARTIAL"
    acc = report["input_accounting"]
    assert (acc["processed"], acc["unprocessed"]) == (1, 4)
    assert [u["ref_id"] for u in acc["unprocessed_entries"]] == [
        "mueller2014", "vaswani2017", "kaplan2020", "schrodinger1935"]


def test_internal_error_on_one_entry_is_unverified_not_dropped(monkeypatch, capsys):
    def boom_on_kaplan(entry, *args):
        if entry.key == "kaplan2020":
            raise RuntimeError("boom")
        return verified_stub(entry, *args)

    monkeypatch.setattr(vc, "verify_entry", boom_on_kaplan)
    rc, stdout, _ = run_main(capsys, EDGE_BIB)
    report = json.loads(stdout)
    assert rc == 0 and report["summary"]["verdict"] == "UNVERIFIED"
    (bad,) = [e for e in report["entries"] if e["ref_id"] == "kaplan2020"]
    assert bad["verdict"] == "unverified" and bad["internal_error"] is True and "boom" in bad["detail"]


# --------------------------------------------------------------------------- #
# Network failures are `unverified` — never passing, never fabricated         #
# --------------------------------------------------------------------------- #

ATTENTION = ("@article{vaswani2017, title={Attention is All you Need}, author={Vaswani, Ashish}, "
             "year={2017}, doi={10.48550/arXiv.1706.03762}}")


def _entry(text: str = ATTENTION):
    return vc.parse_input(text).entries[0]


@pytest.mark.parametrize("exc", [vc.NetworkUnavailable("no route to host"),
                                 vc.SourceError("HTTP 429 — rate limited; retry later"),
                                 vc.SourceError("no answer after retries (timed out)")],
                         ids=["offline", "rate-limited", "timeout"])
def test_lookup_failures_give_unverified(monkeypatch, exc):
    def failing(*args, **kwargs):
        raise exc

    monkeypatch.setattr(vc, "_http_get", failing)
    for text in (ATTENTION, "@article{k, title={A study with no identifier}, author={Doe, J.}, year={2020}}"):
        r = vc.verify_entry(_entry(text), "x", 0.7, False)
        assert r["verdict"] == "unverified" and r["severity"] == "MEDIUM"
        assert "NOT confirmed" in r["detail"] and r["manual_instructions"]
        assert not r["matches"]


def _http_error(code: int, retry_after: str = ""):
    headers = email.message.Message()
    if retry_after:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError("https://example.invalid", code, "error", headers, None)


@pytest.mark.parametrize("make_exc", [
    lambda: urllib.error.URLError(ConnectionRefusedError("refused")),
    lambda: urllib.error.URLError(socket.timeout("timed out")),
    lambda: TimeoutError("timed out"),
    lambda: _http_error(429, "86400"),
    lambda: _http_error(503),
], ids=["connection-refused", "urlerror-timeout", "timeout", "http-429", "http-503"])
def test_http_layer_failures_degrade_to_unverified(monkeypatch, make_exc):
    calls = []

    def fake_urlopen(request, timeout=None):
        calls.append(request.full_url)
        raise make_exc()

    monkeypatch.setattr(vc, "_http_get", REAL_HTTP_GET)
    monkeypatch.setattr(vc.urllib.request, "urlopen", fake_urlopen)
    r = vc.verify_entry(_entry(), "x", 0.7, False)
    assert calls, "the real HTTP layer was not exercised"
    assert r["verdict"] == "unverified"
    assert all(st in ("offline", "error") or st.startswith("error") for st in r["source_status"].values())


class _FakeResponse:
    def __init__(self, status: int, headers: dict | None = None) -> None:
        self.status_code = status
        self.headers = headers or {}
        self.text = ""

    def json(self) -> dict:
        return {}


@pytest.mark.parametrize("behaviour", ["http-429", "http-503", "connection-error", "read-timeout"])
def test_requests_backend_failures_degrade_to_unverified(monkeypatch, behaviour):
    class ConnectionError(Exception):  # named like requests' exceptions, which _http_get keys on
        pass

    class ReadTimeout(Exception):
        pass

    calls = []

    def fake_get(url, headers=None, timeout=None):
        calls.append(url)
        if behaviour == "http-429":
            return _FakeResponse(429, {"Retry-After": "86400"})
        if behaviour == "http-503":
            return _FakeResponse(503)
        if behaviour == "connection-error":
            raise ConnectionError("refused")
        raise ReadTimeout("slow")

    monkeypatch.setattr(vc, "_http_get", REAL_HTTP_GET)
    monkeypatch.setattr(vc, "_HAS_REQUESTS", True)
    monkeypatch.setattr(vc, "_requests", types.SimpleNamespace(get=fake_get))
    r = vc.verify_entry(_entry(), "x", 0.7, False)
    assert calls, "the requests code path was not exercised"
    assert r["verdict"] == "unverified", r["detail"]


def test_rate_limited_run_is_unverified_with_notes(monkeypatch, capsys):
    monkeypatch.setattr(vc, "_http_get", REAL_HTTP_GET)
    monkeypatch.setattr(vc.urllib.request, "urlopen",
                        lambda request, timeout=None: (_ for _ in ()).throw(_http_error(429, "86400")))
    rc, stdout, _ = run_main(capsys, EDGE_BIB)
    report = json.loads(stdout)
    assert rc == 0 and report["status"] == "complete"
    assert report["summary"]["verdict"] == "UNVERIFIED"
    assert report["summary"]["verdict_counts"]["verified"] == 0
    assert report["summary"]["verdict_counts"]["TF"] == 0  # failures are never fabrication
    assert report["summary"]["source_errors"] and report["summary"]["notes"]
