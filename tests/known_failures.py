"""Single source of truth for known content-debt failures.

Each entry maps a (test_name, skill_relative_path) → reason. Tests look up
this dict and use `pytest.xfail` so CI stays green, but the debt remains
visible. When you fix one of these, remove its entry — the test will
flip from XPASS to a hard failure if regressed.

When adding new skills, you should NOT add entries here. New work must
pass the full schema.
"""

from __future__ import annotations

# Body exceeds the 1500-line hard limit.
# Fix path: move detail into references/ sub-files; SKILL.md should be a router.
BODY_TOO_LONG = {
    "skills/clinical-research/alterlab-treatment-plans/SKILL.md":
        "1573 lines (>1500). Move treatment-protocol templates into references/.",
    "skills/writing-tools/alterlab-latex-posters/SKILL.md":
        "1598 lines (>1500). Move LaTeX templates into references/ and link them.",
}

# Body cites references/<file>.md paths that don't exist on disk.
# Fix path: either create the file or update the citation to point at an existing one.
REFERENCES_MISSING = {
    "skills/core/alterlab-paper-writer/SKILL.md":
        "cites references/apa7_style_guide.md (actual: apa7_extended_guide.md)",
    "skills/data-science/alterlab-torch-geometric/SKILL.md":
        "cites references/api_patterns.md and references/layer_capabilities.md (no such files)",
    "skills/visualization/alterlab-scientific-schematics/SKILL.md":
        "cites references/diagram_types.md (no such file)",
    "skills/visualization/alterlab-scientific-viz/SKILL.md":
        "cites references/examples.md, objects_interface.md, function_reference.md (no such files)",
    "skills/writing-tools/alterlab-research-grants/SKILL.md":
        "cites 7 generic reference files that do not exist (timeline_planning, "
        "team_building, budget_preparation, review_criteria, resubmission_strategies, "
        "research_methods, funding_mechanisms)",
}
