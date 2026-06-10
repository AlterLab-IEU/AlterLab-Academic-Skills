# Third-Party Notices

This repository (AlterLab Academic Skills) is licensed under the **MIT License**
(see [`LICENSE`](LICENSE)). The skill *content* — the SKILL.md guidance, reference
docs, and helper scripts authored by AlterLab — is original work under the license
declared in each skill's frontmatter `license:` field, **except where it derives from
an upstream collection** (see Provenance below). A condensed attribution record for both
upstreams is also kept in the [`NOTICE`](NOTICE) file.

## Provenance / Upstream

AlterLab Academic Skills derives from **two** upstream Agent Skills collections, each
acknowledged below with its own copyright and license. We do not overwrite or replace either
upstream's authorship; the original notices are preserved verbatim.

| # | Upstream | Author / © | License | Derived AlterLab skills |
|---|---|---|---|---|
| 1 | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | K-Dense Inc. (© 2025) | MIT | The bioinformatics, cheminformatics, data-science, databases, visualization, lab-integrations and domain-specific tool-wrapper skills (the bulk of the suite) |
| 2 | [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | Cheng-I Wu / 吳政宜 (© 2026) | **CC-BY-NC 4.0** | `core/alterlab-deep-research`, `core/alterlab-paper-writer`, `core/alterlab-paper-reviewer`, `core/alterlab-research-pipeline` |

See [`PROVENANCE.md`](PROVENANCE.md) for the narrative lineage. Per-upstream license terms and the
required attribution strings follow.

### Upstream 1 — K-Dense-AI/scientific-agent-skills (MIT)

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

### Upstream 2 — Imbad0202/academic-research-skills (CC-BY-NC 4.0)

The four `core/` research-lifecycle skills below adapt the agent-team architecture of
[**Imbad0202/academic-research-skills**](https://github.com/Imbad0202/academic-research-skills) by
**Cheng-I Wu (吳政宜)** (with contributors aspi6246, mchesbro1, cloudenochcsis, eltociear). That
upstream is released under the **Creative Commons Attribution-NonCommercial 4.0 International
license (CC-BY-NC 4.0), Copyright (c) 2026 Cheng-I Wu** (verified against the upstream
[`LICENSE`](https://github.com/Imbad0202/academic-research-skills/blob/main/LICENSE), which opens
`Copyright (c) 2026 Cheng-I Wu / This work is licensed under the Creative Commons`).

**Required attribution.** CC-BY-NC 4.0 requires retaining the creator's identification, a copyright
notice, a reference to the license, and the disclaimer of warranties. The upstream requests the
following attribution string, reproduced here verbatim:

```
Based on Academic Research Skills by Cheng-I Wu
https://github.com/Imbad0202/academic-research-skills
```

**Per-skill derivation map.** Each AlterLab skill below adapts the correspondingly named upstream
skill (upstream versions current at verification):

| AlterLab skill | Upstream skill (version) | Distinctive shared structure |
|---|---|---|
| `core/alterlab-deep-research` | Deep Research (v2.9.4) | 13-agent research team; Socratic mentor, devil's advocate, risk-of-bias, source-verification agents; multi-mode (incl. PRISMA systematic review) |
| `core/alterlab-paper-writer` | Academic Paper (v3.2.0) | 12-agent writing pipeline; intake → structure → draft → revision-coach → citation-compliance agents |
| `core/alterlab-paper-reviewer` | Academic Paper Reviewer (v1.10.0) | Multi-reviewer peer-review system with an editor-in-chief (EiC) synthesizer and devil's-advocate reviewer |
| `core/alterlab-research-pipeline` | Academic Pipeline (v3.12.0) | End-to-end orchestrator chaining research → write → integrity-check → review → revise with a state tracker |

**License-compatibility notice — IMPORTANT.** CC-BY-NC 4.0 is a **NonCommercial** license and is
**not** a permissive MIT-family license. Unlike the K-Dense MIT material, CC-BY-NC works **cannot be
sublicensed or relicensed under MIT**, and the NonCommercial restriction follows the derivative.
The four skills above currently declare `license: MIT` in their own SKILL.md frontmatter; that
frontmatter value does **not** override the upstream's terms and is, for these four skills,
inaccurate with respect to their lineage. This notice records the accurate upstream license so the
attribution and use restrictions are not lost. Anyone redistributing or using these four skills
must:

1. retain the attribution string above and a link to the upstream;
2. honor the **NonCommercial** restriction (no commercial use of these four skills or their
   derivatives without separate permission from Cheng-I Wu); and
3. treat CC-BY-NC 4.0 — not MIT — as the governing license for these four skills until their
   per-skill frontmatter is corrected or the material is independently re-implemented.

The CC-BY-NC 4.0 legal text is available at
<https://creativecommons.org/licenses/by-nc/4.0/legalcode>. This per-skill frontmatter correction
is tracked as follow-up work and is intentionally **not** made here (this change touches only the
notices, per the editing scope); see the NOTICE file for the condensed attribution record.

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
frontmatter. Current distribution across the 209 skills:

| License | Skills |
|---|---:|
| MIT | 175 |
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

**Caveat.** This table reflects the `license:` value *as declared in frontmatter*. For the four
`core/` skills derived from the CC-BY-NC 4.0 upstream (see "Upstream 2" above), the frontmatter
declares `MIT` but the **governing** license is CC-BY-NC 4.0; the table over-counts MIT by four
until that frontmatter is corrected. Treat the Provenance section and [`NOTICE`](NOTICE) as
authoritative over this count where they conflict.

## Note on removed material

Earlier revisions contained Anthropic's proprietary document-skills code (docx/pdf/pptx/
xlsx). That code is `© Anthropic, PBC` under terms that prohibit redistribution and
derivative works, and has been **removed** from this repository (v1.1.0). It is not
included or relicensed here.
