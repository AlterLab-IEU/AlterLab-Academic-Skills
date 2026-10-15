"""alterlab-citation-mgmt's format_bibtex.py parses real-world BibTeX layouts.

The original parser was one regex that needed each entry's closing brace on its own line, so a
file exported with single-line entries came back "No entries found".
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "writing-tools" / "alterlab-citation-mgmt"
spec = importlib.util.spec_from_file_location("format_bibtex", SKILL / "scripts" / "format_bibtex.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)


def _parse(text: str):
    return fb.BibTeXFormatter().parse_bibtex(text)


def test_messy_fixture_parses_and_deduplicates() -> None:
    f = fb.BibTeXFormatter()
    entries = f.parse_bibtex_file(str(SKILL / "evals" / "fixtures" / "messy.bib"))
    assert len(entries) == 5
    unique = f.deduplicate_entries(entries)
    assert sorted(e["key"] for e in unique) == ["Wisniewski_2020", "braun2022thematic",
                                                 "hattie2007", "kluger1996"]
    assert next(e for e in unique if e["key"] == "kluger1996")["fields"]["year"] == "1996"


def test_layouts_nested_braces_quotes_and_skipped_blocks() -> None:
    text = ('@string{jrn = "Journal"}\n@comment{ignore me}\n'
            '@Article{a1, title={The {DNA} of Feedback}, author="Doe, J. and Roe, R.", '
            'year=2020, note = "a, b"}\n'
            '@book(b2,\n  title = {Book},\n  year = {2019})\n')
    entries = _parse(text)
    assert [e["key"] for e in entries] == ["a1", "b2"]
    a1 = entries[0]["fields"]
    assert a1["title"] == "The {DNA} of Feedback" and a1["year"] == "2020"
    assert a1["author"] == "Doe, J. and Roe, R." and a1["note"] == "a, b"
    assert entries[1]["type"] == "book" and entries[1]["fields"]["year"] == "2019"


def test_well_formed_file_still_parses() -> None:
    text = "@article{k,\n  author = {A},\n  title = {T},\n  year = {2001}\n}\n"
    assert _parse(text) == [{"type": "article", "key": "k",
                             "fields": {"author": "A", "title": "T", "year": "2001"}}]


def test_duplicates_by_doi_url_form_and_by_title_keep_the_fuller_entry() -> None:
    f = fb.BibTeXFormatter()
    entries = _parse("@article{x, title={Same Paper}, year={2010}}\n"
                     "@article{y, title={Same paper.}, year={2010}, journal={J}, volume={1}}\n"
                     "@article{z, doi={10.1/ABC}}\n@article{w, doi={https://doi.org/10.1/abc}}\n")
    kept = f.deduplicate_entries(entries)
    assert [e["key"] for e in kept] == ["y", "z"]
