"""figure_tools.py — the keyless renderer shared by four visual skills.

The file is copied verbatim into each skill (skills are installed separately), so the copies
must stay identical; its fallback thresholds must match the optional AI scripts it mirrors; and
the lint and review bookkeeping are checked without any renderer installed.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
COPIES = [
    REPO / "skills/visualization/alterlab-scientific-schematics/scripts/figure_tools.py",
    REPO / "skills/visualization/alterlab-infographics/scripts/figure_tools.py",
    REPO / "skills/visualization/alterlab-generate-image/scripts/figure_tools.py",
    REPO / "skills/writing-tools/alterlab-scientific-slides/scripts/figure_tools.py",
]


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"figure_tools_{path.parts[-3]}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ft():
    return _load(COPIES[0])


def test_copies_are_identical():
    texts = {p: p.read_bytes() for p in COPIES}
    first = texts[COPIES[0]]
    assert all(t == first for t in texts.values()), \
        "figure_tools.py copies differ; edit one and copy it to the other three skills"


@pytest.mark.parametrize("copy", COPIES[:2] + COPIES[3:], ids=lambda p: p.parts[-3])
def test_fallback_thresholds_match_the_ai_scripts(copy):
    mod = _load(copy)
    for kind, (script, cls, const) in mod.AI_SOURCES.items():
        ai = copy.with_name(script)
        if not ai.exists():
            continue
        live = mod.read_constants(ai, [const], cls)[const]
        live = live if isinstance(live, dict) else {"default": live}
        assert {k: float(v) for k, v in live.items()} == mod.THRESHOLDS[kind], kind


def test_lint_flags_overflow_small_text_and_no_viewbox(ft, tmp_path):
    svg = tmp_path / "f.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100" font-size="8">'
        '<rect x="10" y="10" width="100" height="40"/>'
        '<text x="15" y="35">This label is far too long for its box</text></svg>')
    rep = ft.lint_svg(svg, width_in=3.5)
    joined = " ".join(rep["warnings"])
    assert "no viewBox" in joined
    assert "overflows its box" in joined
    assert "pt at 3.5 in" in joined  # 8 user units over 400 at 3.5 in ~ 5 pt


def test_lint_reports_parse_errors(ft, tmp_path):
    bad = tmp_path / "bad.svg"
    bad.write_text("<svg><text>unclosed</svg>")
    assert "error" in ft.lint_svg(bad)


def test_score_loop_applies_threshold_and_cap(ft, tmp_path):
    log = tmp_path / "log.json"
    first = ft.score(log, "schematic", "journal", "v1.png", 7.0, "overflow", "f.svg", None, "CONSORT")
    assert first["decision"].startswith("REVISE") and first["threshold"] == 8.5
    second = ft.score(log, "schematic", "journal", "v2.png", 9.0, "clean", "f.svg", None, None)
    assert second["decision"] == "DONE"
    data = json.loads(log.read_text())
    assert data["final_image"] == "v2.png" and data["meets_threshold"] is True
    with pytest.raises(ValueError):
        ft.score(log, "schematic", "journal", "v3.png", 9.5, "x", None, None, None)


def test_score_stops_below_threshold_at_the_cap(ft, tmp_path):
    log = tmp_path / "log.json"
    ft.score(log, "slide", "default", "a.png", 5.0, "x", None, 1, None)
    data = json.loads(log.read_text())
    assert data["success"] is True and data["meets_threshold"] is False
    assert "maximum" in data["early_stop_reason"]


def test_render_rejects_unknown_types(ft, tmp_path):
    src = tmp_path / "x.bmp"
    src.write_text("")
    with pytest.raises(ValueError):
        ft.render(src, tmp_path / "out.png")
    svg = tmp_path / "x.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>')
    with pytest.raises(ValueError):
        ft.render(svg, tmp_path / "out.gif")


def test_openrouter_key_lookup_is_optional(ft, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    assert ft.find_openrouter_key(None) is None
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY='abc'\n")
    assert ft.find_openrouter_key(None) == "abc"
    assert ft.find_openrouter_key("explicit") == "explicit"
