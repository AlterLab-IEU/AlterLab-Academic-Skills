"""Every AlterLab skill a SKILL.md names in backticks must exist.

`alterlab-skill-finder` routes by name, so a name that points at no skill sends the model to an
"Unknown skill" error. The v3.0.0 routing map named three such skills (`alterlab-grant-writer`,
`alterlab-sec-edgar`, `alterlab-irb-consent`). This test fails on any backticked `alterlab-*` token
in a SKILL.md that is neither a skill folder nor a plugin, bundle, or marketplace name (the same
allowlist `scripts/confusion_matrix.py` applies to evals). Reference files are not scanned: the
workflow references use `alterlab-<name>/` as output-folder names.
"""

from __future__ import annotations

import re

import confusion_matrix as cm

NAME = re.compile(r"`(alterlab-[a-z0-9-]+)`")


def test_skill_md_names_only_real_skills(skill_files) -> None:
    skills = {p.parent.name for p in skill_files}
    plugins = cm.plugin_names()
    unknown = sorted(
        f"{md.parent.name}: {name}"
        for md in skill_files
        for name in set(NAME.findall(md.read_text(encoding="utf-8")))
        if name not in skills and name not in plugins
    )
    assert not unknown, "SKILL.md names skills that do not exist:\n" + "\n".join(unknown)
