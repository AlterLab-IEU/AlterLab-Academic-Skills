"""The alterlab-skill-finder skill index stays in sync with the catalog.

`references/skill_index.md` is generated from `skills.json` by `scripts/gen_skill_index.py`.
This gates drift in CI: if a skill is added/renamed and the index is not regenerated, this fails.
"""

from __future__ import annotations

import json

import gen_skill_index


def test_skill_index_matches_catalog() -> None:
    catalog = json.loads(gen_skill_index.CATALOG.read_text(encoding="utf-8"))
    expected = gen_skill_index.build_index(catalog)
    current = gen_skill_index.OUT.read_text(encoding="utf-8") if gen_skill_index.OUT.exists() else ""
    assert current == expected, (
        "skills/core/alterlab-skill-finder/references/skill_index.md is stale — "
        "run `python3 scripts/gen_skill_index.py`"
    )


def test_every_skill_appears_in_index() -> None:
    catalog = json.loads(gen_skill_index.CATALOG.read_text(encoding="utf-8"))
    skills = catalog["skills"] if isinstance(catalog, dict) else catalog
    index = gen_skill_index.OUT.read_text(encoding="utf-8")
    missing = [s["name"] for s in skills if f"`{s['name']}`" not in index]
    assert not missing, f"skills absent from the router index: {missing}"
