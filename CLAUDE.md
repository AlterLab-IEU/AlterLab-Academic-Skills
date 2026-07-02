# AlterLab Academic Skills — by AlterLab Creative Technologies Laboratory

> **Project**: AlterLab Academic Skills — 238 Claude AI skills for faculty and researchers
> **Owner**: AlterLab Creative Technologies Laboratory

---

## Project Overview

This project provides **238 professional Claude AI skills** organized into 17 domain categories for faculty members, academicians, and researchers. Each skill transforms Claude into a domain-specific expert assistant tailored to academic research, scientific computing, and scholarly publishing workflows.

The repo is installable as a Claude Code plugin marketplace named `alterlab-academic-skills`, with 17 domain plugins (`alterlab-core`, `alterlab-databases`, `alterlab-bioinformatics`, `alterlab-cheminformatics`, `alterlab-clinical-research`, `alterlab-data-science`, `alterlab-visualization`, `alterlab-writing-tools`, `alterlab-lab-integrations`, `alterlab-domain-specific`, `alterlab-document-tools`, `alterlab-research-tools`, `alterlab-finance-economics`, `alterlab-turkish-academia`, `alterlab-faculty-life`, `alterlab-methodology`, `alterlab-social-science-workflow`).

### Audience
- Faculty members and academic researchers
- NOT students (see AlterLab FC for student skills)

### Naming Convention
- **Folder**: `alterlab-{name}` (lowercase, hyphenated)
- **Frontmatter name**: `"alterlab-{name}"`
- **Suite label**: `Part of the AlterLab Academic Skills suite.`

---

## Skill Categories

| Category | Path | Count | Description |
|----------|------|-------|-------------|
| Core Pipeline | `skills/core/` | 9 | Research -> Write -> Review -> Publish pipeline + citation-verifier + link-health + workflow-orchestration |
| Databases | `skills/databases/` | 39 | Scientific database connectors |
| Bioinformatics | `skills/bioinformatics/` | 38 | Genomics, proteomics, molecular biology |
| Cheminformatics | `skills/cheminformatics/` | 12 | Chemistry, drug discovery |
| Clinical Research | `skills/clinical-research/` | 7 | Clinical decision support, medical tools |
| Data Science | `skills/data-science/` | 22 | ML, statistics, data analysis |
| Visualization | `skills/visualization/` | 9 | Scientific plotting and graphics |
| Writing Tools | `skills/writing-tools/` | 13 | Scientific writing, citations, posters |
| Lab Integrations | `skills/lab-integrations/` | 9 | Laboratory platform connectors |
| Domain-Specific | `skills/domain-specific/` | 18 | Quantum, geospatial, materials science |
| Document Tools | `skills/document-tools/` | 3 | Markdown conversion, notebook handling |
| Research Tools | `skills/research-tools/` | 14 | Search, discovery, reference management |
| Finance & Economics | `skills/finance-economics/` | 7 | Financial data and analysis |
| Turkish Academia | `skills/turkish-academia/` | 12 | Turkish academic system workflows (YÖK, ÜAK, DergiPark, TÜBİTAK) |
| Faculty Life | `skills/faculty-life/` | 6 | Faculty research-lifecycle and academic administration |
| Methodology | `skills/methodology/` | 3 | Research methodology and rigor scaffolds |
| Social-Science Workflow | `skills/social-science-workflow/` | 17 | Stage-gated methods spine: orchestrator + 5 validity gates (design, measurement, sampling, reflexivity, inference) + 11 analysis modules (causal-inference, SEM/psychometrics, QCA, SNA, ABM, text-as-data, survey-analysis, qualitative-analysis, multilevel-models, meta-analysis, missing-data) |

**Total: 238 skills across 17 categories**

---

## Core Pipeline Routing Rules

The core category holds 9 skills: 6 pipeline skills (`alterlab-research-pipeline`, `alterlab-deep-research`, `alterlab-paper-writer`, `alterlab-paper-reviewer`, `alterlab-teaching-design`, `alterlab-thesis-supervisor`) plus `alterlab-citation-verifier`, `alterlab-link-health`, and `alterlab-workflow-orchestration` (composes skills into multi-agent workflows). The pipeline skills coordinate as a multi-agent research-to-publication system:

### Skill Routing

1. **alterlab-research-pipeline vs individual skills**: The pipeline is the full orchestrator (research -> write -> review -> revise -> finalize). If the user only needs a single function (just research, just write, just review), trigger the corresponding skill directly without the pipeline.

2. **alterlab-deep-research vs alterlab-paper-writer**: Complementary. Deep Research = upstream research engine (investigation + fact-checking). Paper Writer = downstream publication engine (paper writing + bilingual abstracts). Recommended flow: deep-research -> paper-writer.

3. **alterlab-deep-research socratic vs full**: socratic = guided Socratic dialogue to help users clarify their research question. full = direct production of research report. When the user's research question is unclear, suggest socratic mode.

4. **alterlab-paper-writer plan vs full**: plan = chapter-by-chapter guided planning via Socratic dialogue. full = direct paper production. When the user wants to think through their paper structure, suggest plan mode.

5. **alterlab-paper-reviewer guided vs full**: guided = Socratic review that engages the author in dialogue about issues. full = standard multi-perspective review report. When the user wants to learn from the review, suggest guided mode.

### Full Pipeline Flow

```
alterlab-deep-research (socratic/full)
  -> alterlab-paper-writer (plan/full)
    -> alterlab-paper-reviewer (full/guided)
      -> alterlab-paper-writer (revision)
        -> alterlab-paper-reviewer (re-review, max 2 loops)
          -> alterlab-paper-writer (format-convert -> final output)
```

### Handoff Protocol

**deep-research -> paper-writer**
Materials: RQ Brief, Methodology Blueprint, Annotated Bibliography, Synthesis Report, INSIGHT Collection

**paper-writer -> paper-reviewer**
Materials: Complete paper text. Field analyst agent auto-detects domain and configures reviewers.

**paper-reviewer -> paper-writer (revision)**
Materials: Editorial Decision Letter, Revision Roadmap, Per-reviewer detailed comments

---

## MCP Integration

When MCP tools are available, skills should prefer them over simulated responses:

| MCP Server | Use For | Priority Skills |
|------------|---------|-----------------|
| **PubMed** | Literature search, article metadata, full-text retrieval | alterlab-pubmed, alterlab-deep-research, alterlab-literature-review |
| **Scholar Gateway** | Semantic academic search across disciplines | alterlab-deep-research, alterlab-research-lookup |
| **Clinical Trials** | Trial search, eligibility, endpoint analysis | alterlab-clinicaltrials, alterlab-clinical-decision |
| **Hugging Face** | Model discovery, documentation lookup | alterlab-transformers, alterlab-pytorch-lightning |
| **Context7** | Library documentation queries | All tool-specific skills (RDKit, Scanpy, etc.) |

**Rule**: If an MCP tool can answer the query with live data, use it instead of relying on training data alone. Always cite the data source and retrieval date.

---

## Key Quality Rules

- All claims must have citations
- Evidence hierarchy respected (meta-analyses > RCTs > cohort > case reports > expert opinion)
- Contradictions disclosed with evidence quality comparison
- AI disclosure in all reports
- Default output language matches user input

---

## Build & Validation

| Command | Purpose |
|---------|---------|
| `python scripts/audit_skills.py` | Audit skills (frontmatter, naming, counts) |
| `pytest tests/` | Run the validation test suite |
| `python scripts/gen_marketplace.py` | Regenerate the `alterlab-academic-skills` marketplace + 17 domain plugins |

---

## Commit Convention

- `feat: add alterlab-{skill-name}` — new skill
- `feat({category}): add alterlab-{skill-name}` — new skill with category scope
- `improve: alterlab-{skill-name} — {what changed}` — skill enhancement
- `fix: alterlab-{skill-name} — {what was wrong}` — bug fix
- `docs: update README` — documentation
- `chore: {description}` — project maintenance

All skill names use the `alterlab-` prefix. Conventional commits format required.
