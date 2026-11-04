"""alterlab-pyzotero's zotero_export.py — keyless subset export from an exported library.

`export -o` used to print only a count, so a reply had nothing to report the selection by;
it now lists each written entry (key as written, year, DOI, title) on stdout.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "research-tools" / "alterlab-pyzotero"
spec = importlib.util.spec_from_file_location("zotero_export", SKILL / "scripts" / "zotero_export.py")
ze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ze)

LIBRARY = SKILL / "evals" / "fixtures" / "my_library.json"
EXPECTED_DOIS = {"10.1136/bmj.n71", "10.1016/j.envint.2020.106274", "10.1016/j.ebiom.2022.104147",
                 "10.1056/NEJMoa2307563", "10.1038/s41586-024-07487-w"}


def test_export_to_file_lists_each_written_entry(tmp_path, capsys) -> None:
    out = tmp_path / "recent.bib"
    rc = ze.main(["export", str(LIBRARY), "--type", "article-journal", "--year-from", "2020",
                  "--to", "bibtex", "-o", str(out)])
    assert rc == 0
    bib = out.read_text(encoding="utf-8")
    keys = re.findall(r"^@article\{([^,]+),", bib, flags=re.MULTILINE)
    assert len(keys) == 5 and not any(k.startswith("http") for k in keys)
    assert set(re.findall(r"doi = \{([^}]+)\}", bib)) == EXPECTED_DOIS

    captured = capsys.readouterr()
    assert "exported 5 of 11 items as bibtex" in captured.err
    rows = [line.split("\t") for line in captured.out.splitlines()]
    assert [r[0] for r in rows] == keys            # the keys the file actually uses
    assert {r[2].removeprefix("doi:") for r in rows} == EXPECTED_DOIS
    assert "Language models are few-shot learners" not in captured.out  # conference paper


def test_export_to_stdout_stays_a_clean_file(capsys) -> None:
    rc = ze.main(["export", str(LIBRARY), "--type", "article-journal", "--year-from", "2020",
                  "--to", "bibtex"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("@article{") and "\tdoi:" not in out
    assert out.count("@article{") == 5
