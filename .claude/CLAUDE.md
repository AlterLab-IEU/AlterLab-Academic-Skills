# AlterLab Academic Skills — Project-Level Claude Configuration

## Skill Routing Rules

### Core Pipeline Skills (`skills/core/` holds 10 skills)

`skills/core/` contains 10 skills: the 4 orchestration skills below, plus `alterlab-teaching-design`, `alterlab-thesis-supervisor`, `alterlab-citation-verifier`, `alterlab-link-health`, `alterlab-workflow-orchestration`, and `alterlab-skill-finder` (the front-door router / `alterflow` multi-agent launcher).

| Skill | Trigger When | Modes |
|-------|-------------|-------|
| `alterlab-deep-research` | User wants to investigate a topic, find literature, fact-check claims | full, quick, socratic, review, lit-review, fact-check |
| `alterlab-paper-writer` | User wants to write, draft, or revise an academic paper | full, plan, outline-only, revision, abstract-only, lit-review, format-convert, citation-check |
| `alterlab-paper-reviewer` | User wants a manuscript reviewed or critiqued | full, re-review, quick, methodology-focus, guided |
| `alterlab-research-pipeline` | User wants the full end-to-end research-to-publication workflow | Orchestrates all above |

### Routing Logic

1. **Single task -> direct skill**: If the user only needs research, writing, or review, activate that skill directly. Do not invoke the pipeline for single tasks.
2. **Multi-step workflow -> pipeline**: If the user describes a full research-to-publication goal, activate `alterlab-research-pipeline`.
3. **Unclear scope -> ask**: If ambiguous whether the user wants one skill or the full pipeline, ask before proceeding.
4. **Socratic modes**: When the user's question is vague or exploratory, prefer Socratic modes (socratic for research, plan for writing, guided for review) to help them clarify intent.

---

## Handoff Protocol

Skills pass structured materials between pipeline stages:

### Stage 1: Research -> Writing
**alterlab-deep-research** produces and hands off:
- RQ Brief (research question formalization)
- Methodology Blueprint
- Annotated Bibliography
- Synthesis Report
- INSIGHT Collection

### Stage 2: Writing -> Review
**alterlab-paper-writer** produces and hands off:
- Complete paper text (structured sections)
- Field analyst agent auto-detects domain and configures appropriate reviewers

### Stage 3: Review -> Revision
**alterlab-paper-reviewer** produces and hands off:
- Editorial Decision Letter
- Revision Roadmap
- Per-reviewer detailed comments with severity ratings

### Revision Loop
- Maximum 2 revision loops (review -> revise -> re-review -> final revise)
- After 2 loops, proceed to format-convert and final output

---

## MCP Tool Preferences

When MCP servers are available, skills MUST prefer live data over training knowledge:

### Priority 1 — Always use when available
| MCP Server | Skills That Benefit |
|------------|-------------------|
| **PubMed** (`search_articles`, `get_full_text_article`, `get_article_metadata`) | alterlab-pubmed, alterlab-deep-research, alterlab-literature-review, alterlab-paper-writer |
| **Scholar Gateway** (`semanticSearch`) | alterlab-deep-research, alterlab-research-lookup, alterlab-scientific-brainstorm |
| **Clinical Trials** (`search_trials`, `get_trial_details`, `analyze_endpoints`) | alterlab-clinicaltrials, alterlab-clinical-decision, alterlab-treatment-plans |

### Priority 2 — Use when relevant
| MCP Server | Skills That Benefit |
|------------|-------------------|
| **Hugging Face** (`hub_repo_search`, `hf_doc_search`) | alterlab-transformers, alterlab-pytorch-lightning, alterlab-esm |
| **Context7** (`resolve-library-id`, `query-docs`) | All tool-specific skills (RDKit, Scanpy, Matplotlib, etc.) for up-to-date API docs |

### Priority 3 — Use for workflow support
| MCP Server | Use Case |
|------------|----------|
| **Filesystem** | Read/write research outputs, manage skill files |
| **Memory** | Persist research context across sessions |
| **Sequential Thinking** | Complex multi-step research planning |

### MCP Rules
- Always cite the data source and retrieval date when using MCP-fetched data
- If an MCP tool fails, fall back to training knowledge but disclose the limitation
- Never fabricate MCP results — if the tool returns no results, say so

---

## Quality Standards for New Skills

All new skills added to this project must meet these requirements:

### Structure
- Frontmatter table with `name` and `description` fields
- Name follows `alterlab-{name}` convention (lowercase, hyphenated)
- Include: Identity, Core Mission, Frameworks/Methods, Output Templates, Quality Standards sections
- End with suite label: `Part of the AlterLab Academic Skills suite.`

### Content
- Role description must be specific and expert-level (not generic)
- Include at least 3 concrete frameworks or methodologies
- Provide structured output templates (not just prose instructions)
- Define quality rubrics with measurable criteria
- Include error handling / edge case guidance

### Academic Rigor
- All factual claims must reference established methodologies
- Evidence hierarchy must be respected where applicable
- AI disclosure requirements must be included
- Ethical considerations must be addressed for the domain

### Testing
- Each skill should be tested with at least 3 representative prompts
- Verify that the skill activates correctly based on its trigger description
- Confirm output matches the defined templates and quality standards

---

## Commit Convention

All commits to this project follow conventional commits with AlterLab prefixes:

```
feat: add alterlab-{skill-name}          # New skill
feat({category}): add alterlab-{name}    # New skill with scope
improve: alterlab-{name} — {detail}      # Enhancement
fix: alterlab-{name} — {detail}          # Bug fix
docs: {description}                       # Documentation
chore: {description}                      # Maintenance
```
