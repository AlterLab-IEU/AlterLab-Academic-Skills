#!/usr/bin/env python3
"""Generate .claude-plugin/marketplace.json (and sync package.json version) from the skills/ tree.

## Scoping (v2.0 — per the docs/design/scoping-spike.md verdict)

The scoping spike (RESOLVED — GO) found the v1.x shape was broken: every plugin
used ``source: "./"`` plus an explicit ``skills`` array, which loads ALL 180
skills for every plugin. Two documented facts cause this: (1) a relative string
``source`` resolves the plugin ROOT relative to the marketplace/repo root, so
``"./"`` makes every plugin's root the repo root; (2) the ``skills`` field is
ADDITIVE ("in addition to default ``skills/``"), so the curated array cannot
subtract the repo-wide ``skills/`` tree that auto-discovery walks.

Fix (Option A — no mass file moves): point each plugin's ``source`` at its own
domain folder (``./skills/<domain>``) and make the ``skills`` array entries
plugin-root-relative (``./alterlab-pubmed`` not ``./skills/databases/...``).
Domains have NO nested ``skills/`` subdir, so default ``skills/`` auto-discovery
finds nothing under the new root and the explicit array is the only thing loaded
— scoping each install to one domain.

## Surface beyond skills (commands / agents / hooks / mcpServers)

Some domains ship more than skills. This generator auto-discovers, relative to
each domain's plugin root:

* ``.mcp.json``            -> emits ``"mcpServers": "./.mcp.json"`` (also auto-discovered)
* ``hooks/hooks.json``     -> emits ``"hooks": "./hooks/hooks.json"`` (also auto-discovered)
* ``<skill>/commands/``    -> emits ``"commands": [...]`` (REPLACES default; must be explicit)
* ``<skill>/agents/``      -> emits ``"agents": [...]`` (REPLACES default; must be explicit)

``commands`` and ``agents`` REPLACE the default ``commands/`` / ``agents/`` plugin-root
folders (which do not exist here — the files are nested inside individual skill dirs),
so they MUST be enumerated explicitly or they will not load.

## Versioning

The single source of truth for the version is ``[project].version`` in
``pyproject.toml``. This script reads it from there and writes it into BOTH
``.claude-plugin/marketplace.json`` and ``package.json``. Do not hand-edit the
version in those generated files.

Regenerate after adding/removing/moving skills:  uv run python scripts/gen_marketplace.py
Verify it is up to date (CI):                     uv run python scripts/gen_marketplace.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
OUT = REPO / ".claude-plugin" / "marketplace.json"
PYPROJECT = REPO / "pyproject.toml"
PACKAGE_JSON = REPO / "package.json"
SPIKE_DOC = REPO / "docs" / "design" / "scoping-spike.md"

HOMEPAGE = "https://github.com/AlterLab-IEU/AlterLab-Academic-Skills"
AUTHOR = {"name": "AlterLab @ Izmir University of Economics", "url": "https://github.com/AlterLab-IEU"}

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
    "turkish-academia": "Turkish academic system workflows (YÖK, ÜAK, DergiPark, YÖK-Tez, TÜBİTAK, doçentlik)",
    "faculty-life": "Faculty research-lifecycle and academic administration (syllabus AI-policy, IRB/consent, post-award grant admin, recommendation letters, accreditation AoL)",
    "methodology": "Research methodology and rigor scaffolds (Iron Laws, rationalization tables, decision flowcharts, systematic-reasoning checklists)",
    "social-science-workflow": "Stage-gated social-science methods spine — orchestrator + 5 validity gates (design/identifying-assumption, measurement, sampling/power, reflexivity, inference) and 11 analysis modules (causal inference, complex-survey analysis, SEM/psychometrics, multilevel models, QCA, SNA, ABM, text-as-data, qualitative analysis, meta-analysis, missing data)",
}

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
    "turkish-academia": ("research", ["turkish-academia", "yok", "uak", "dergipark", "yok-tez", "tubitak"]),
    "faculty-life": ("productivity", ["faculty", "teaching", "irb", "grant-admin", "accreditation", "recommendation-letters"]),
    "methodology": ("research", ["methodology", "research-rigor", "systematic-reasoning", "checklists", "decision-flowcharts"]),
    "social-science-workflow": ("research", ["social-science", "research-design", "causal-inference", "psychometrics", "sampling", "power-analysis"]),
}


def read_version() -> str:
    """Single source of truth: [project].version in pyproject.toml.

    Hand-rolled parse (no tomllib import gymnastics needed) — match the first
    ``version = "..."`` that appears after the ``[project]`` table header.
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            continue
        if in_project:
            m = re.match(r'version\s*=\s*"([^"]+)"', stripped)
            if m:
                return m.group(1)
    raise SystemExit("error: could not find [project].version in pyproject.toml")


def scoping_verdict() -> str:
    """Read the GO/NO-GO verdict out of the scoping-spike design doc.

    Returns 'go' or 'no-go'. Defaults to 'go' if the doc cannot be parsed, since
    that is the resolved verdict; the marketplace shape is gated on this so a
    future flip of the doc to NO-GO falls back to the legacy (documented-broken)
    shape rather than silently shipping the wrong layout.
    """
    if not SPIKE_DOC.is_file():
        return "go"
    head = SPIKE_DOC.read_text(encoding="utf-8")[:4000].lower()
    # Look for an explicit NO-GO before GO; the doc states the verdict up top.
    m = re.search(r"\bstatus[:*\s]+resolved[^\n]*\b(no-go|go)\b", head)
    if m:
        return "no-go" if m.group(1) == "no-go" else "go"
    if "no-go" in head and "— go" not in head and "go (" not in head:
        return "no-go"
    return "go"


def _rel_dirs(skill_dir: Path, sub: str) -> list[str]:
    """If skill_dir/<sub> exists and is non-empty, return its plugin-root-relative path."""
    d = skill_dir / sub
    if d.is_dir() and any(d.iterdir()):
        return [f"./{skill_dir.name}/{sub}"]
    return []


def build_plugin_scoped(cat_dir: Path, version: str) -> dict | None:
    """Build one per-domain plugin entry in the v2.0 scoped shape (verdict == 'go')."""
    skill_dirs = sorted(
        d for d in cat_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    )
    if not skill_dirs:
        return None
    cat = cat_dir.name
    category, keywords = CATEGORY_TAGS.get(cat, ("research", [cat]))

    entry: dict = {
        "name": f"alterlab-{cat}",
        # source = the domain folder => plugin root is <repo>/skills/<cat>/.
        # No nested skills/ exists under it, so the explicit skills[] below is
        # the only thing loaded => the install is scoped to this one domain.
        "source": f"./skills/{cat}",
        "description": f"{CATEGORY_BLURB.get(cat, cat)} ({len(skill_dirs)} skills)",
        "version": version,
        "author": AUTHOR,
        "homepage": HOMEPAGE,
        "license": "MIT",
        "category": category,
        "keywords": keywords,
        "strict": False,
        # Plugin-root-relative (NOT ./skills/<cat>/<skill>).
        "skills": [f"./{d.name}" for d in skill_dirs],
    }

    # --- extra surface, discovered relative to this domain's plugin root ---

    # commands/ and agents/ are nested inside individual skill dirs. These fields
    # REPLACE the (nonexistent) default plugin-root commands/ and agents/ folders,
    # so they MUST be enumerated explicitly or they will not load.
    commands: list[str] = []
    agents: list[str] = []
    for sd in skill_dirs:
        commands += _rel_dirs(sd, "commands")
        agents += _rel_dirs(sd, "agents")
    if commands:
        entry["commands"] = commands
    if agents:
        entry["agents"] = agents

    # hooks/hooks.json and .mcp.json sit at the domain (plugin) root. They are
    # auto-discovered there, but declaring them is explicit and survives the
    # additive/replace subtleties.
    if (cat_dir / "hooks" / "hooks.json").is_file():
        entry["hooks"] = "./hooks/hooks.json"
    if (cat_dir / ".mcp.json").is_file():
        entry["mcpServers"] = "./.mcp.json"

    return entry


# Domains that ALSO ship a standalone `.claude-plugin/plugin.json`, so the folder can be
# installed as its own plugin (clone + `claude --plugin-dir skills/<domain>`), independent of
# the umbrella marketplace. plugin.json supports an explicit `skills` array (Claude Code plugins
# reference), so no restructuring is needed. Add a domain name here to give it the same treatment.
STANDALONE_PLUGIN_DOMAINS = {"social-science-workflow"}


def build_domain_plugin_json(cat_dir: Path, version: str) -> dict | None:
    """Standalone `.claude-plugin/plugin.json` for a single domain (plugin root == the domain dir).

    Reuses the scoped marketplace entry but drops the marketplace-only `source` / `strict` /
    `category` fields. The `skills` array is already plugin-root-relative (`./<skill>`), which is
    exactly right when the plugin root is the domain folder itself."""
    entry = build_plugin_scoped(cat_dir, version)
    if entry is None:
        return None
    drop = {"source", "strict", "category"}
    manifest = {
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        **{k: v for k, v in entry.items() if k not in drop},
    }
    return manifest


def domain_plugin_paths(version: str) -> list[tuple[Path, str]]:
    """(path, rendered-json) for every standalone domain plugin.json to emit / drift-check."""
    out = []
    for cat in sorted(STANDALONE_PLUGIN_DOMAINS):
        cat_dir = SKILLS / cat
        manifest = build_domain_plugin_json(cat_dir, version)
        if manifest is None:
            continue
        path = cat_dir / ".claude-plugin" / "plugin.json"
        out.append((path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"))
    return out


def build_plugin_legacy(cat_dir: Path, version: str) -> dict | None:
    """Legacy (v1.x) shape, kept ONLY for the verdict == 'no-go' fallback.

    NOTE: this shape is documented-broken (see docs/design/scoping-spike.md):
    source "./" makes the plugin root the repo root and the additive skills[]
    array cannot subtract the repo-wide skills/ tree, so EVERY plugin loads ALL
    skills. Emitted only if the spike verdict is flipped to NO-GO.
    """
    skill_dirs = sorted(
        d for d in cat_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    )
    if not skill_dirs:
        return None
    cat = cat_dir.name
    category, keywords = CATEGORY_TAGS.get(cat, ("research", [cat]))
    return {
        "name": f"alterlab-{cat}",
        "source": "./",
        "description": f"{CATEGORY_BLURB.get(cat, cat)} ({len(skill_dirs)} skills)",
        "version": version,
        "author": AUTHOR,
        "homepage": HOMEPAGE,
        "license": "MIT",
        "category": category,
        "keywords": keywords,
        "strict": False,
        "skills": [f"./skills/{cat}/{d.name}" for d in skill_dirs],
    }


def build(version: str, verdict: str) -> dict:
    builder = build_plugin_scoped if verdict == "go" else build_plugin_legacy
    plugins = []
    for cat_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        entry = builder(cat_dir, version)
        if entry is not None:
            plugins.append(entry)
    total = sum(len(p["skills"]) for p in plugins)
    description = f"{total} Claude skills for academic research, organized by domain"
    return {
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        "name": "alterlab-academic-skills",
        # Top-level description/version are the first-class marketplace fields per the
        # Claude Code plugin-marketplace spec; the metadata block below mirrors them for
        # backward compatibility (and `metadata.version` is read by tests/test_versioning.py).
        "description": description,
        "version": version,
        "owner": {
            "name": "AlterLab @ Izmir University of Economics",
            "email": "alterlab.ieu@gmail.com",
        },
        "metadata": {
            "description": description,
            "version": version,
            # metadata.author advertises the marketplace maintainer (agentskills.io spec).
            "author": AUTHOR,
        },
        "plugins": plugins,
    }


def render_package_json(version: str) -> str:
    """Return package.json with its top-level "version" set to `version`.

    Preserves all other fields and formatting (2-space indent + trailing newline)
    so the only diff is the version bump.
    """
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    data["version"] = version
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if marketplace.json or package.json version is stale")
    args = ap.parse_args()

    version = read_version()
    verdict = scoping_verdict()
    data = build(version, verdict)
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    pkg_rendered = render_package_json(version)

    domain_plugins = domain_plugin_paths(version)

    if args.check:
        stale = []
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            stale.append(".claude-plugin/marketplace.json")
        pkg_current = PACKAGE_JSON.read_text(encoding="utf-8") if PACKAGE_JSON.exists() else ""
        if pkg_current != pkg_rendered:
            stale.append("package.json (version out of sync with pyproject.toml)")
        for path, text in domain_plugins:
            cur = path.read_text(encoding="utf-8") if path.exists() else ""
            if cur != text:
                stale.append(str(path.relative_to(REPO)))
        if stale:
            print(
                "out of date — run: uv run python scripts/gen_marketplace.py\n  - "
                + "\n  - ".join(stale),
                file=sys.stderr,
            )
            return 1
        print(
            f"marketplace.json + package.json up to date "
            f"({len(data['plugins'])} plugins, v{version}, verdict={verdict})."
        )
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    PACKAGE_JSON.write_text(pkg_rendered, encoding="utf-8")
    for path, text in domain_plugins:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    total = sum(len(p["skills"]) for p in data["plugins"])
    extra = f" + {len(domain_plugins)} standalone plugin.json" if domain_plugins else ""
    print(
        f"Wrote {OUT.relative_to(REPO)} + package.json{extra}: "
        f"{len(data['plugins'])} plugins, {total} skills, v{version} (verdict={verdict})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
