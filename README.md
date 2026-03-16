# AlterLab Academic Skills

> **Project**: AlterLab Academic Skills — 180+ Claude AI skills for faculty members and academic researchers
> **Owner**: AlterLab Creative Technologies Laboratory
> **Audience**: Faculty members, academicians, and researchers

---

## Overview

AlterLab Academic Skills is a comprehensive suite of AI-powered research tools organized into a domain-based hierarchy. It combines a 4-skill academic research pipeline (39 specialized agents) with 170+ scientific tools covering databases, bioinformatics, cheminformatics, clinical research, data science, visualization, and more.

### How It Differs from AlterLab FC

| | AlterLab FC | AlterLab Academic |
|--|-------------|-------------------|
| **Audience** | Communication faculty students | Faculty members & academicians |
| **Focus** | Creative production & coursework | Research, publication & scientific computing |
| **Skills** | 36 skills (PRA, CDM, NMC) | 180+ skills (12 domains) |

---

## Skill Categories

### Core Pipeline (4 skills)
The heart of the system — a multi-agent research-to-publication pipeline.

| Skill | Agents | Description |
|-------|--------|-------------|
| `alterlab-deep-research` | 13 | Multi-mode research with systematic review, Socratic dialogue, fact-checking |
| `alterlab-paper-writer` | 12 | Academic paper authoring with LaTeX, bilingual support, 9 writing modes |
| `alterlab-paper-reviewer` | 7 | Multi-perspective peer review with Devil's Advocate, 0-100 quality rubrics |
| `alterlab-research-pipeline` | 7 | 10-stage orchestrator with integrity verification and material passports |

### Databases (39 skills)
Connectors to 250+ scientific databases — PubMed, ChEMBL, UniProt, ClinicalTrials.gov, COSMIC, and more.

### Bioinformatics (25 skills)
Genomics, proteomics, and molecular biology tools — Scanpy, BioPython, ESM, single-cell analysis, phylogenetics.

### Cheminformatics (12 skills)
Chemistry and drug discovery — RDKit, molecular dynamics, docking, ADMET analysis.

### Clinical Research (10 skills)
Clinical decision support, treatment planning, medical imaging, regulatory compliance.

### Data Science (22 skills)
ML/statistics — scikit-learn, PyTorch Lightning, statsmodels, SHAP, transformers.

### Visualization (8 skills)
Scientific plotting and graphics — Matplotlib, Seaborn, Plotly, schematics, infographics.

### Writing Tools (12 skills)
Scientific writing, literature review, citation management, grant writing, poster design.

### Lab Integrations (9 skills)
Laboratory platform connectors — Benchling, DNAnexus, Opentrons, Protocols.io.

### Domain-Specific (15 skills)
Quantum computing, geospatial, materials science, astrophysics, and more.

### Document Tools (6 skills)
File format handling — DOCX, PDF, PPTX, XLSX, Markdown.

### Research Tools (7 skills)
Search and discovery — Perplexity, parallel web search, Zotero, scientific brainstorming.

### Finance & Economics (7 skills)
Financial data and analysis — FRED, Alpha Vantage, SEC EDGAR, market research.

---

## Directory Structure

```
AlterLab_Academic/
├── skills/
│   ├── core/                    # 4 pipeline skills + shared schemas
│   ├── databases/               # 39 database connectors
│   ├── bioinformatics/          # 25 bio/genomics tools
│   ├── cheminformatics/         # 12 chemistry/drug discovery
│   ├── clinical-research/       # 10 clinical/medical tools
│   ├── data-science/            # 22 ML/statistics tools
│   ├── visualization/           # 8 plotting/charting tools
│   ├── writing-tools/           # 12 scientific writing tools
│   ├── lab-integrations/        # 9 lab platform connectors
│   ├── domain-specific/         # 15 specialized field tools
│   ├── document-tools/          # 6 file format tools
│   ├── research-tools/          # 7 search/discovery tools
│   └── finance-economics/       # 7 financial/economic tools
├── README.md                    # This file
└── CLAUDE.md                    # Project instructions
```

---

## Installation

### Claude Code (Recommended)
```bash
# Clone or copy the skills directory to your Claude project
cp -r AlterLab_Academic/skills/ .claude/skills/
```

### Manual Installation
Copy individual SKILL.md files to your Claude Code skills directory or upload to Claude Projects.

---

## Usage

Skills activate automatically based on user intent. Examples:

- "Help me research the latest findings on CRISPR gene editing" → `alterlab-deep-research`
- "Write an academic paper on machine learning in education" → `alterlab-paper-writer`
- "Review my manuscript for methodology issues" → `alterlab-paper-reviewer`
- "Search PubMed for recent studies on Alzheimer's biomarkers" → `alterlab-pubmed`
- "Analyze my RNA-seq data" → `alterlab-scanpy` + `alterlab-pydeseq2`
- "Create a scientific poster for my conference" → `alterlab-latex-posters`

---

## Credits

Built by AlterLab Creative Technologies Laboratory.

Core pipeline skills adapted from [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) by Cheng-I Wu (CC-BY-NC 4.0).
Scientific skills adapted from [claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) by K-Dense AI.

---

## License

This project combines works under different licenses:
- Core pipeline skills: CC-BY-NC 4.0
- Scientific skills: See individual skill files for licensing
- AlterLab additions: MIT
