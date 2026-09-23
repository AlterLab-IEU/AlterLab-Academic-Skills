"""The release workflow's notes come from the CHANGELOG section of the version being released.

`scripts/release_notes.py` extracts that section, re-flows hard-wrapped lines (release bodies
render every newline as a line break), and makes relative links absolute. These tests pin the
three transformations and check that the current pyproject version has a CHANGELOG section, so a
release can never go out with empty notes.
"""

from __future__ import annotations

import re

import release_notes

SAMPLE = """# Changelog

## [Unreleased]

## [9.9.9] — 2099-01-01

Intro paragraph that is
hard-wrapped over two lines.

- **Item one** continues
  on an indented line.
  - nested item stays separate
- Item two links [`ROADMAP.md`](ROADMAP.md), [site](https://example.org) and [top](#top).

```
code line one
code line two
```

## [9.9.8] — 2098-01-01

- older entry
"""


def test_section_stops_at_the_next_version() -> None:
    body = release_notes.section(SAMPLE, "9.9.9")
    assert body.startswith("Intro paragraph")
    assert "older entry" not in body and "## [" not in body


def test_missing_version_yields_nothing() -> None:
    assert release_notes.section(SAMPLE, "1.0.0") == ""


def test_reflow_joins_wrapped_lines_but_keeps_blocks() -> None:
    out = release_notes.reflow(release_notes.section(SAMPLE, "9.9.9")).splitlines()
    assert "Intro paragraph that is hard-wrapped over two lines." in out
    assert "- **Item one** continues on an indented line." in out
    assert "  - nested item stays separate" in out
    assert out[out.index("```") + 1 : out.index("```") + 3] == ["code line one", "code line two"]


def test_absolutize_rewrites_only_relative_links() -> None:
    out = release_notes.absolutize(
        "[a](ROADMAP.md) [b](https://example.org) [c](#top)", "o/r", "v9.9.9"
    )
    assert "[a](https://github.com/o/r/blob/v9.9.9/ROADMAP.md)" in out
    assert "[b](https://example.org)" in out and "[c](#top)" in out


def test_current_version_has_release_notes(repo_root) -> None:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject).group(1)
    changelog = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    assert release_notes.section(changelog, version), f"CHANGELOG has no [{version}] section"


def test_main_fails_without_a_section(tmp_path, capsys) -> None:
    log = tmp_path / "CHANGELOG.md"
    log.write_text(SAMPLE, encoding="utf-8")
    assert release_notes.main(["1.0.0", "--changelog", str(log)]) == 1
    assert release_notes.main(["9.9.9", "--changelog", str(log), "--repo", "o/r"]) == 0
    assert "https://github.com/o/r/blob/v9.9.9/ROADMAP.md" in capsys.readouterr().out
