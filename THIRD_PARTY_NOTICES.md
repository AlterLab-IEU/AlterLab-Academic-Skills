# Third-Party Notices

This repository (AlterLab Academic Skills) is licensed under the **MIT License**
(see [`LICENSE`](LICENSE)). The skill *content* — the SKILL.md guidance, reference
docs, and helper scripts authored by AlterLab — is original work under the license
declared in each skill's frontmatter `license:` field.

## Provenance / Upstream

AlterLab Academic Skills began as a **content fork** of
[**K-Dense-AI/scientific-agent-skills**](https://github.com/K-Dense-AI/scientific-agent-skills)
(formerly published as `claude-scientific-skills`), the scientific Agent Skills library by
**K-Dense Inc.** We gratefully acknowledge K-Dense's work as the seed of this collection.

**License compatibility.** The upstream repository is released under the **MIT License,
Copyright (c) 2025 K-Dense Inc.** (verified against the upstream
[`LICENSE.md`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/LICENSE.md)
and the GitHub-reported license metadata). MIT's permission grant explicitly allows use,
copying, modification, and **sublicensing** of the Software, provided the original copyright
notice and permission notice are retained. Distributing our derivative work under our own MIT
license (Copyright (c) 2026 AlterLab Creative Technologies Laboratory) is therefore permitted;
this is a **relicensing of a derivative within the MIT family**, not a license change of the
upstream work. The upstream MIT copyright notice for K-Dense Inc. is preserved below.

```
MIT License

Copyright (c) 2025 K-Dense Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Scope of the derivative.** At fork time, **42 skill bodies were byte-identical** to their
K-Dense counterparts; the remainder were already diverging and the collection has since been
substantially restructured, audited, corrected, and extended into the 180-skill AlterLab suite
(13 research domains). The systematic deltas — added executable evals, license/citation audits,
script-correctness fixes, progressive-disclosure refactors, the academic-faculty framing, and
the bilingual (EN/TR) documentation — are narrated in [`PROVENANCE.md`](PROVENANCE.md). This is
a derivative of an MIT-licensed work, not a verbatim redistribution.

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
