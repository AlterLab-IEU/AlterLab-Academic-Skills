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

## Surface beyond skills (commands / agents / workflows / hooks / mcpServers / userConfig)

Some domains ship more than skills. This generator auto-discovers, relative to
each domain's plugin root:

* ``.mcp.json``            -> emits ``"mcpServers": "./.mcp.json"``, plus a ``userConfig``
                              option for every ``${user_config.KEY}`` it references
                              (specs live in ``USER_CONFIG_SPEC``; an unknown key is an error)
* ``hooks/hooks.json``     -> not declared: auto-discovered at the plugin root (a marketplace
                              entry rejects the file-path form of ``hooks``)
* ``workflows/*.js``       -> emits ``"workflows": "./workflows/"`` (Claude Code dynamic
                              workflows, run as ``/<plugin>:<meta.name>``)
* ``<skill>/commands/``    -> emits ``"commands": [...]`` (REPLACES default; must be explicit)
* ``<skill>/agents/*.md``  -> emits ``"agents": [...]`` as individual FILES (REPLACES default;
                              the field rejects directory entries)

``commands`` and ``agents`` REPLACE the default ``commands/`` / ``agents/`` plugin-root
folders (which do not exist here — the files are nested inside individual skill dirs),
so they MUST be enumerated explicitly or they will not load.

## Standalone domains (``STANDALONE_PLUGIN_DOMAINS``)

Most entries are ``strict: false`` — the marketplace entry is the whole plugin definition.
A standalone domain instead ships its own ``.claude-plugin/plugin.json`` (so the folder also
works via ``claude --plugin-dir``); its marketplace entry is ``strict: true`` and carries only
metadata, because a ``strict: false`` entry that declares components conflicts with a
component-declaring ``plugin.json`` and the plugin fails to load.

Validate the result with the real loader: ``claude plugin validate .``

## Versioning

The single source of truth for the version is ``[project].version`` in
``pyproject.toml``. This script reads it from there and writes it into BOTH
``.claude-plugin/marketplace.json`` and ``package.json``. Do not hand-edit the
version in those generated files. ``scripts/gen_catalog.py`` embeds the same
version in ``skills.json`` (``summary.version``), so run BOTH after a bump —
``gen_catalog.py --check`` fails on a bump that did not regenerate the catalog.

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
# SchemaStore IDs (editor autocomplete only — Claude Code ignores `$schema` at load time).
MARKETPLACE_SCHEMA = "https://www.schemastore.org/claude-code-marketplace.json"
PLUGIN_SCHEMA = "https://www.schemastore.org/claude-code-plugin-manifest.json"
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
    "workflows": "Runnable multi-agent research workflows for Claude Code (systematic-review screening, citation audit, independent review panel, claim stress-test, rebuttal, grant mock panel, literature map) plus the portable playbook skill",
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
    "workflows": ("research", ["workflows", "multi-agent", "systematic-review", "peer-review", "citation-audit", "orchestration"]),
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


def _agent_files(skill_dir: Path) -> list[str]:
    """Plugin-root-relative paths of every agent definition under skill_dir/agents/.

    The `agents` component field takes agent FILES, not directories — a directory entry
    fails `claude plugin validate` ("agents.0: Invalid input") and makes the whole plugin
    uninstallable. So each `agents/*.md` is listed individually."""
    d = skill_dir / "agents"
    if not d.is_dir():
        return []
    return [f"./{skill_dir.name}/agents/{f.name}" for f in sorted(d.glob("*.md"))]


# `${user_config.KEY}` placeholders used by a domain's `.mcp.json` must be declared as plugin
# `userConfig` options, or Claude Code has nothing to prompt for and the MCP servers start with
# unresolved credentials. Every key a `.mcp.json` references must have a spec here (checked in
# `_user_config`). Strings default to "" so leaving an optional value blank substitutes cleanly.
USER_CONFIG_SPEC: dict[str, dict] = {
    "openalex_api_key": {
        "type": "string",
        "title": "OpenAlex API key (recommended)",
        "description": (
            "Free key from https://openalex.org/settings/api. OpenAlex meters usage per day "
            "(since February 2026); keyless requests share a small per-IP budget and fail with "
            "HTTP 429 once it is spent."
        ),
        "sensitive": True,
        "default": "",
    },
    "zotero_library_id": {
        "type": "string",
        "title": "Zotero library ID (optional)",
        "description": "Numeric user or group library ID, shown at https://www.zotero.org/settings/keys",
        "default": "",
    },
    "zotero_library_type": {
        "type": "string",
        "title": "Zotero library type",
        "description": "Either 'user' (personal library) or 'group'.",
        "default": "user",
    },
    "zotero_api_key": {
        "type": "string",
        "title": "Zotero API key (optional)",
        "description": "Read access key from https://www.zotero.org/settings/keys",
        "sensitive": True,
        "default": "",
    },
}

_USER_CONFIG_RE = re.compile(r"\$\{user_config\.([A-Za-z_][A-Za-z0-9_]*)\}")


def _user_config(cat_dir: Path) -> dict:
    """`userConfig` options for every `${user_config.KEY}` in the domain's `.mcp.json`."""
    mcp = cat_dir / ".mcp.json"
    if not mcp.is_file():
        return {}
    keys = sorted(set(_USER_CONFIG_RE.findall(mcp.read_text(encoding="utf-8"))))
    missing = [k for k in keys if k not in USER_CONFIG_SPEC]
    if missing:
        raise SystemExit(
            f"error: {mcp.relative_to(REPO)} references undeclared user_config key(s) {missing}; "
            "add them to USER_CONFIG_SPEC in scripts/gen_marketplace.py"
        )
    return {k: USER_CONFIG_SPEC[k] for k in keys}


def _skill_dirs(cat_dir: Path) -> list[Path]:
    return sorted(d for d in cat_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())


def count_skills() -> int:
    """Total skills across every domain (standalone entries carry no `skills` array)."""
    return sum(len(_skill_dirs(d)) for d in SKILLS.iterdir() if d.is_dir())


def _components(cat_dir: Path, skill_dirs: list[Path]) -> dict:
    """Component fields (skills, commands, agents, workflows, hooks, MCP, userConfig) for a domain.

    Paths are plugin-root-relative (the plugin root is the domain folder)."""
    comp: dict = {"skills": [f"./{d.name}" for d in skill_dirs]}

    # commands/ and agents/ are nested inside individual skill dirs. These fields REPLACE the
    # (nonexistent) default plugin-root commands/ and agents/ folders, so they MUST be
    # enumerated explicitly or they will not load.
    commands: list[str] = []
    agents: list[str] = []
    for sd in skill_dirs:
        commands += _rel_dirs(sd, "commands")
        agents += _agent_files(sd)
    if commands:
        comp["commands"] = commands
    if agents:
        comp["agents"] = agents

    # Claude Code dynamic-workflow scripts ship in a `workflows/` dir at the plugin root and run
    # as `/<plugin>:<meta.name>`. Declared explicitly because a strict:false entry is the whole
    # definition.
    wf = cat_dir / "workflows"
    if wf.is_dir() and any(wf.glob("*.js")):
        comp["workflows"] = "./workflows/"

    # hooks/hooks.json at the plugin root is auto-discovered in every mode, so it is NOT
    # declared: a marketplace entry rejects the file-path form of `hooks` ("not yet supported in
    # a marketplace entry"), and hooks merge across sources, so re-declaring the default file in
    # a plugin.json would register them twice. .mcp.json is declared (path form is accepted and
    # servers de-duplicate by name).
    if (cat_dir / ".mcp.json").is_file():
        comp["mcpServers"] = "./.mcp.json"
    user_config = _user_config(cat_dir)
    if user_config:
        comp["userConfig"] = user_config
    return comp


# Domains that ship their own `.claude-plugin/plugin.json`, so the folder is a complete plugin
# on its own (clone + `claude --plugin-dir skills/<domain>`), independent of the umbrella
# marketplace. For these the plugin.json is the authority (`strict: true`) and the marketplace
# entry carries only metadata: a strict:false entry that ALSO declares components conflicts with
# a component-declaring plugin.json and the plugin fails to load.
STANDALONE_PLUGIN_DOMAINS = {"social-science-workflow", "workflows"}

# Other marketplace plugins a standalone domain needs at runtime (resolved by name within this
# marketplace and installed alongside it). The workflows call alterlab-core's verifier/reviewer
# skills, so installing alterlab-workflows pulls in alterlab-core. Bare names only: version
# ranges would need per-plugin `{name}--v{version}` git tags, which this repo does not publish.
PLUGIN_DEPENDENCIES = {"workflows": ["alterlab-core"]}

# Dependency-only bundle plugins: installing one installs every plugin it lists, so users get a
# curated set in one step instead of 18 separate installs. Emitted to plugins/<name>/.
BUNDLES = {
    "alterlab-essentials": {
        "description": (
            "Faculty starter kit — installs the core research-to-publication pipeline, the multi-agent "
            "research workflows, research tools, writing tools, methodology gates, and scientific-database "
            "connectors in one step"
        ),
        "domains": ["core", "workflows", "research-tools", "writing-tools", "methodology", "databases"],
        "keywords": ["bundle", "starter-kit", "faculty", "research", "writing"],
    },
    "alterlab-complete": {
        "description": "The complete AlterLab Academic Skills suite — installs every domain plugin in one step",
        "domains": "*",
        "keywords": ["bundle", "complete", "all-domains"],
    },
}
PLUGINS_DIR = REPO / "plugins"


_LICENSE_RE = re.compile(r'(?m)^license:\s*"?([^"\n]+?)"?\s*$')


def _plugin_license(skill_dirs: list[Path]) -> str:
    """SPDX expression covering every skill a plugin bundles, from each SKILL.md `license`.

    Most domains are all-MIT. A domain that bundles differently licensed skills (the core
    pipeline's CC-BY-NC-4.0 skills, the Apache-2.0 Mermaid skill) must not advertise plain MIT.
    """
    found: set[str] = set()
    for d in skill_dirs:
        head = (d / "SKILL.md").read_text(encoding="utf-8").split("\n---", 1)[0]
        m = _LICENSE_RE.search(head)
        found.add(m.group(1).strip() if m else "MIT")
    return " AND ".join(sorted(found, key=lambda s: (s != "MIT", s))) or "MIT"


def build_plugin_scoped(cat_dir: Path, version: str) -> dict | None:
    """Build one per-domain plugin entry in the v2.0 scoped shape (verdict == 'go')."""
    skill_dirs = _skill_dirs(cat_dir)
    if not skill_dirs:
        return None
    cat = cat_dir.name
    category, keywords = CATEGORY_TAGS.get(cat, ("research", [cat]))

    entry: dict = {
        "name": f"alterlab-{cat}",
        # source = the domain folder => plugin root is <repo>/skills/<cat>/.
        # No nested skills/ exists under it, so the explicit skills[] is the only thing
        # loaded => the install is scoped to this one domain.
        "source": f"./skills/{cat}",
        "description": f"{CATEGORY_BLURB.get(cat, cat)} ({len(skill_dirs)} skill{'s' if len(skill_dirs) != 1 else ''})",
        "version": version,
        "author": AUTHOR,
        "homepage": HOMEPAGE,
        "license": _plugin_license(skill_dirs),
        "category": category,
        "keywords": keywords,
    }
    if cat in STANDALONE_PLUGIN_DOMAINS:
        # The domain's own plugin.json declares the components.
        entry["strict"] = True
        return entry
    entry["strict"] = False
    entry.update(_components(cat_dir, skill_dirs))
    return entry


def build_domain_plugin_json(cat_dir: Path, version: str) -> dict | None:
    """Standalone `.claude-plugin/plugin.json` for a single domain (plugin root == the domain dir).

    Carries the same metadata as the marketplace entry (minus the marketplace-only `source` /
    `strict` / `category` fields) plus the full component set. The `skills` array is
    plugin-root-relative (`./<skill>`), which is exactly right when the plugin root is the domain
    folder itself."""
    skill_dirs = _skill_dirs(cat_dir)
    entry = build_plugin_scoped(cat_dir, version)
    if entry is None:
        return None
    drop = {"source", "strict", "category"}
    manifest = {
        "$schema": PLUGIN_SCHEMA,
        **{k: v for k, v in entry.items() if k not in drop},
        **_components(cat_dir, skill_dirs),
    }
    if cat_dir.name in PLUGIN_DEPENDENCIES:
        manifest["dependencies"] = PLUGIN_DEPENDENCIES[cat_dir.name]
    return manifest


def _domain_names() -> list[str]:
    return sorted(d.name for d in SKILLS.iterdir() if d.is_dir() and _skill_dirs(d))


def build_bundle_manifest(name: str, version: str) -> dict:
    """plugin.json for a dependency-only bundle plugin."""
    spec = BUNDLES[name]
    domains = _domain_names() if spec["domains"] == "*" else spec["domains"]
    missing = [d for d in domains if not (SKILLS / d).is_dir()]
    if missing:
        raise SystemExit(f"error: bundle {name} lists unknown domain(s) {missing}")
    return {
        "$schema": PLUGIN_SCHEMA,
        "name": name,
        "description": spec["description"],
        "version": version,
        "author": AUTHOR,
        "homepage": HOMEPAGE,
        "license": "MIT",
        "keywords": spec["keywords"],
        "dependencies": [f"alterlab-{d}" for d in domains],
    }


def build_bundle_entry(name: str, version: str) -> dict:
    """Marketplace entry for a bundle: metadata only; its plugin.json carries the dependencies."""
    manifest = build_bundle_manifest(name, version)
    return {
        "name": name,
        "source": f"./plugins/{name}",
        "description": manifest["description"],
        "version": version,
        "author": AUTHOR,
        "homepage": HOMEPAGE,
        "license": "MIT",
        "category": "research",
        "keywords": manifest["keywords"],
        "strict": True,
    }


def domain_plugin_paths(version: str) -> list[tuple[Path, str]]:
    """(path, rendered-json) for every standalone domain plugin.json to emit / drift-check."""
    out = []
    for cat in sorted(STANDALONE_PLUGIN_DOMAINS):
        cat_dir = SKILLS / cat
        if not cat_dir.is_dir():
            continue
        manifest = build_domain_plugin_json(cat_dir, version)
        if manifest is None:
            continue
        path = cat_dir / ".claude-plugin" / "plugin.json"
        out.append((path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"))
    for name in sorted(BUNDLES):
        path = PLUGINS_DIR / name / ".claude-plugin" / "plugin.json"
        manifest = build_bundle_manifest(name, version)
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
        "license": _plugin_license(skill_dirs),
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
    if verdict == "go":
        plugins += [build_bundle_entry(name, version) for name in sorted(BUNDLES)]
    total = count_skills()
    description = f"{total} Claude skills for academic research, organized by domain"
    return {
        "$schema": MARKETPLACE_SCHEMA,
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
        # `metadata` mirrors description/version for backward compatibility; the marketplace
        # schema has no `metadata.author` (the maintainer lives in `owner`).
        "metadata": {
            "description": description,
            "version": version,
        },
        "plugins": plugins,
    }


def render_package_json(version: str, total: int) -> str:
    """Return package.json with its "version" and skill-count description kept current.

    Preserves all other fields and formatting (2-space indent + trailing newline)
    so the only diff is the version bump / count.
    """
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    data["version"] = version
    data["description"] = (
        f"{total} Claude AI skills for faculty members and academic researchers "
        "— organized by research domain"
    )
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
    pkg_rendered = render_package_json(version, count_skills())

    domain_plugins = domain_plugin_paths(version)

    if args.check:
        stale = []
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            stale.append(".claude-plugin/marketplace.json")
        pkg_current = PACKAGE_JSON.read_text(encoding="utf-8") if PACKAGE_JSON.exists() else ""
        if pkg_current != pkg_rendered:
            stale.append("package.json (version/skill count out of sync)")
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
    total = count_skills()
    extra = f" + {len(domain_plugins)} standalone plugin.json" if domain_plugins else ""
    print(
        f"Wrote {OUT.relative_to(REPO)} + package.json{extra}: "
        f"{len(data['plugins'])} plugins, {total} skills, v{version} (verdict={verdict})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
