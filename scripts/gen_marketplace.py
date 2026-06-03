#!/usr/bin/env python3
"""Generate .claude-plugin/marketplace.json from the skills/ tree.

Claude Code plugin skill-discovery is NOT recursive: a plugin's `skills` array
must list each leaf directory that contains a SKILL.md directly. This repo nests
skills two levels deep (skills/<category>/<skill>/SKILL.md), so we emit ONE plugin
per category, each listing only that category's skill directories. All plugins
live in a single marketplace, so users add the marketplace once and install only
the domains they need:

    /plugin marketplace add AlterLab-IEU/AlterLab-Academic-Skills
    /plugin install alterlab-bioinformatics@alterlab-academic-skills

Regenerate after adding/removing/moving skills:  python scripts/gen_marketplace.py
Verify it is up to date (CI):                     python scripts/gen_marketplace.py --check
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
OUT = REPO / ".claude-plugin" / "marketplace.json"

# Human-facing one-liners per category (kept here, not derived, so the catalog reads well).
CATEGORY_BLURB = {
    "core": "Core research-to-publication pipeline plus teaching and thesis tools",
    "databases": "Connectors to scientific databases (PubMed, ChEMBL, UniProt, GEO, and more)",
    "bioinformatics": "Genomics, proteomics, and single-cell analysis (Scanpy, BioPython, pysam, ESM)",
    "cheminformatics": "Chemistry and drug discovery (RDKit, docking, ADMET, mass spec)",
    "clinical-research": "Clinical decision support, medical imaging, and regulatory workflows",
    "data-science": "Machine learning and statistics (scikit-learn, PyTorch, transformers, SHAP)",
    "visualization": "Publication-quality plotting and schematics (Matplotlib, Seaborn, Plotly)",
    "writing-tools": "Scientific writing, citations, grants, posters, and academic career",
    "lab-integrations": "Laboratory platforms (Benchling, DNAnexus, Opentrons, Protocols.io)",
    "domain-specific": "Quantum computing, geospatial, materials, astronomy, and digital humanities",
    "document-tools": "Document and Markdown conversion (MarkItDown, Open Notebook)",
    "research-tools": "Search, discovery, Zotero, qualitative methods, ethics, and open science",
    "finance-economics": "Economic and financial data (FRED, Alpha Vantage, SEC EDGAR, market research)",
}


VERSION = "1.2.0"
HOMEPAGE = "https://github.com/AlterLab-IEU/AlterLab-Academic-Skills"
AUTHOR = {"name": "AlterLab @ Izmir University of Economics", "url": "https://github.com/AlterLab-IEU"}

# `category` powers the `/plugin > Discover` filter UI; keywords aid search.
CATEGORY_TAGS = {
    "core": ("research", ["research", "writing", "peer-review", "pipeline", "academic"]),
    "databases": ("data", ["database", "api", "pubmed", "uniprot", "chembl", "bioinformatics"]),
    "bioinformatics": ("science", ["genomics", "proteomics", "single-cell", "scanpy", "biopython"]),
    "cheminformatics": ("science", ["chemistry", "drug-discovery", "rdkit", "docking", "admet"]),
    "clinical-research": ("science", ["clinical", "medical-imaging", "dicom", "regulatory"]),
    "data-science": ("data", ["machine-learning", "statistics", "pytorch", "scikit-learn", "transformers"]),
    "visualization": ("productivity", ["plotting", "matplotlib", "seaborn", "plotly", "figures"]),
    "writing-tools": ("writing", ["scientific-writing", "citations", "grants", "posters", "latex"]),
    "lab-integrations": ("science", ["lab-automation", "benchling", "opentrons", "dnanexus"]),
    "domain-specific": ("science", ["quantum", "geospatial", "materials", "astronomy", "digital-humanities"]),
    "document-tools": ("productivity", ["markdown", "document-conversion", "markitdown"]),
    "research-tools": ("research", ["literature-search", "zotero", "qualitative", "ethics", "open-science"]),
    "finance-economics": ("data", ["finance", "economics", "fred", "sec-edgar", "market-research"]),
}


def build() -> dict:
    plugins = []
    for cat_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        skill_dirs = sorted(
            d for d in cat_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
        )
        if not skill_dirs:
            continue
        cat = cat_dir.name
        category, keywords = CATEGORY_TAGS.get(cat, ("research", [cat]))
        plugins.append(
            {
                "name": f"alterlab-{cat}",
                "source": "./",
                "description": f"{CATEGORY_BLURB.get(cat, cat)} ({len(skill_dirs)} skills)",
                "version": VERSION,
                "author": AUTHOR,
                "homepage": HOMEPAGE,
                "license": "MIT",
                "category": category,
                "keywords": keywords,
                "strict": False,
                "skills": [f"./skills/{cat}/{d.name}" for d in skill_dirs],
            }
        )
    total = sum(len(p["skills"]) for p in plugins)
    return {
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        "name": "alterlab-academic-skills",
        "owner": {
            "name": "AlterLab @ Izmir University of Economics",
            "email": "alterlab.ieu@gmail.com",
        },
        "metadata": {
            "description": f"{total} Claude skills for academic research, organized by domain",
            "version": VERSION,
        },
        "plugins": plugins,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if marketplace.json is stale")
    args = ap.parse_args()

    data = build()
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            print("marketplace.json is out of date — run: python scripts/gen_marketplace.py", file=sys.stderr)
            return 1
        print(f"marketplace.json is up to date ({len(data['plugins'])} plugins).")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    total = sum(len(p["skills"]) for p in data["plugins"])
    print(f"Wrote {OUT.relative_to(REPO)}: {len(data['plugins'])} plugins, {total} skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
