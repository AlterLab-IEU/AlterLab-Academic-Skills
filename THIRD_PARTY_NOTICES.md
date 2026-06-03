# Third-Party Notices

This repository (AlterLab Academic Skills) is licensed under the **MIT License**
(see [`LICENSE`](LICENSE)). The skill *content* — the SKILL.md guidance, reference
docs, and helper scripts authored by AlterLab — is original work under the license
declared in each skill's frontmatter `license:` field.

## Tools, libraries, and databases the skills describe

These skills are **instructional wrappers**: they teach Claude how to use third-party
open-source libraries and public data resources. Installing a skill does **not** bundle
or redistribute those tools — users install/access them separately, and **each remains
governed by its own license and terms of service** (e.g. PyPI package licenses, database
access agreements such as KEGG's academic-use terms, UniProt, COSMIC's Sanger
registration, and API providers' terms). Always review the upstream tool's license and a
data resource's terms before use in research or redistribution.

## Per-skill license distribution

Each skill declares the license appropriate to its own content in its `SKILL.md`
frontmatter. Current distribution across the 180 skills:

| License | Skills |
|---|---:|
| MIT | 146 |
| Apache-2.0 | 17 |
| GPL-3.0 | 4 |
| CC0-1.0 | 4 |
| GPL-2.0 | 2 |
| CC-BY-4.0 | 2 |
| BSD-3-Clause | 2 |
| LGPL-3.0 | 1 |
| CeCILL-2.1 | 1 |
| CC-BY-3.0 | 1 |

Regenerate this table after license changes; the source of truth is each skill's
frontmatter (`python scripts/audit_skills.py` reports the canonical value per skill).

## Note on removed material

Earlier revisions contained Anthropic's proprietary document-skills code (docx/pdf/pptx/
xlsx). That code is `© Anthropic, PBC` under terms that prohibit redistribution and
derivative works, and has been **removed** from this repository (v1.1.0). It is not
included or relicensed here.
