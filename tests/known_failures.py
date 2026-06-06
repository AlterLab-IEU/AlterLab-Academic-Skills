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
# (Empty — treatment-plans and latex-posters were split into references/ in v1.1.0.)
BODY_TOO_LONG: dict[str, str] = {}

# Body cites references/<file>.md paths that don't exist on disk.
# Fix path: either create the file or update the citation to point at an existing one.
# (Empty — all dangling citations fixed in v1.1.0; legitimate cross-skill references
# are now resolved by audit_skills.missing_references rather than whitelisted here.)
REFERENCES_MISSING: dict[str, str] = {}

# skills/**/scripts/*.py files that do not byte-compile (genuine SyntaxError).
# Keys are repo-relative paths; values are the reason. The compile test is
# syntax-only (py_compile, no import) so missing deps never land here.
# Fix path: repair the SyntaxError, then remove the entry.
# (Empty — all 161 script files compile cleanly as of v1.1.0.)
SCRIPTS_COMPILE_FAILURES: dict[str, str] = {}

# Core plugin agent .md files under skills/core/**/agents/ that still lack
# registerable `name`/`description` frontmatter. Keys are repo-relative paths.
# These two are owned by a concurrent workstream (integrity_verification and
# bibliography); their frontmatter backfill lands separately. Remove each entry
# once that work merges — the test will flip XPASS → hard failure if regressed.
PLUGIN_AGENTS_MISSING_FRONTMATTER: dict[str, str] = {}
