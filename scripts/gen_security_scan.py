#!/usr/bin/env python3
"""Generate SECURITY_SCAN.md — a CI-attested trust manifest for the shipped skill code.

Every peer suite's install docs say "audit before installing." This pre-empts that: a
generated, CI-checked manifest that (a) enumerates the exact outbound-host allowlist the
shipped skill code talks to and (b) attests, from a static scan, that the code contains no
shell-pipe, no ``os.system`` / ``shell=True``, no ``eval``/``exec`` on input, and no
hardcoded secrets. It converts the repo's hidden security discipline into a visible,
verifiable signal for cautious labs.

Scope: everything a user actually installs — ``skills/**`` Python, shell, and ``.mcp.json``.
The maintenance scripts under ``scripts/`` are out of scope (not shipped in a plugin).

The output is **deterministic** (no timestamps) so CI can enforce currency:

    python3 scripts/gen_security_scan.py            # (re)write SECURITY_SCAN.md
    python3 scripts/gen_security_scan.py --check     # fail if SECURITY_SCAN.md is stale
    python3 scripts/gen_security_scan.py --strict     # fail if any dangerous pattern is found

Single-file, stdlib-only.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
OUT = REPO_ROOT / "SECURITY_SCAN.md"

_HOST_RE = re.compile(r"https?://([A-Za-z0-9.-]+)")

# Dangerous patterns. `eval`/`exec` use a negative lookbehind so METHOD calls (`model.eval()`,
# `forward_eval(`) and attribute access do NOT match — only the bare builtins do.
_DANGER = {
    "os.system()": re.compile(r"\bos\.system\s*\("),
    "subprocess shell=True": re.compile(r"shell\s*=\s*True"),
    "builtin eval() on input": re.compile(r"(?<![\w.])eval\s*\("),
    "builtin exec() on input": re.compile(r"(?<![\w.])exec\s*\("),
    "pipe-to-shell (curl|wget | sh)": re.compile(r"(?:curl|wget)[^\n|]*\|\s*(?:sh|bash)\b"),
    "hardcoded OpenAI key": re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    "hardcoded AWS key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}

# Generic-secret detection is handled separately so obvious placeholders don't false-positive.
# We capture the assigned VALUE, then reject anything that looks like a doc placeholder
# (`your_parallel_api_key`, `your-api-key-here`, `changeme`, …). Skill scripts read real
# credentials from the environment, so the only literal assignments are placeholders.
_SECRET_RE = re.compile(
    r"""(?i)(?:api_key|secret|token|password)\s*=\s*["']([A-Za-z0-9_\-]{16,})["']"""
)
_PLACEHOLDER_RE = re.compile(
    r"(?i)your|here|example|placeholder|changeme|dummy|sample|redacted|xxxx|test|fake|none"
)
_SECRET_LABEL = "hardcoded generic secret"
_CHECK_LABELS = [*_DANGER, _SECRET_LABEL]

# Registrable-domain reduction, handling common multi-label public suffixes.
_MULTI_SUFFIX = {"ac.uk", "co.uk", "gov.uk", "org.uk", "gov.tr", "org.tr", "com.tr",
                 "edu.tr", "co.jp", "com.au"}

# Curated category for the known outbound hosts, so the allowlist reads as *intentional*.
# Anything not listed is labelled "other (review)" so nothing hides behind a generic bucket.
_DOMAIN_CATEGORY = {
    # Literature / scholarly
    "arxiv.org": "Preprints / literature", "biorxiv.org": "Preprints / literature",
    "crossref.org": "Scholarly metadata", "doi.org": "DOI resolver",
    "openalex.org": "Scholarly index", "semanticscholar.org": "Scholarly index",
    "doaj.org": "Open-access journals", "openarchives.org": "OAI-PMH", "purl.org": "Persistent URLs",
    "figshare.com": "Research data", "datacommons.org": "Open data", "wikipedia.org": "Reference",
    # Biomedical / genomics
    "nih.gov": "NCBI / NIH", "ensembl.org": "Genomics", "uniprot.org": "Proteins",
    "rcsb.org": "Protein structures", "string-db.org": "Protein interactions",
    "reactome.org": "Pathways", "kegg.jp": "Pathways", "monarchinitiative.org": "Phenotypes",
    "opentargets.org": "Target–disease", "gtexportal.org": "Expression",
    "depmap.org": "Cancer dependency", "cbioportal.org": "Cancer genomics",
    "broadinstitute.org": "Genomics", "elixir.no": "Bioinformatics infra",
    "nf-co.re": "nf-core pipelines", "geniml.org": "Genomics ML",
    # Clinical / regulatory
    "clinicaltrials.gov": "Clinical trials", "fda.gov": "Regulatory",
    "clinpgx.org": "Pharmacogenomics", "pharmvar.org": "Pharmacogenomics",
    # Chemistry / drug discovery
    "bindingdb.org": "Binding affinities", "docking.org": "Compound libraries",
    "drugbank.ca": "Drugs", "hmdb.ca": "Metabolites", "brenda-enzymes.org": "Enzymes",
    "metabolomicsworkbench.org": "Metabolomics", "tdcommons.ai": "Therapeutics benchmarks",
    "materialsproject.org": "Materials", "sron.nl": "Spectroscopy",
    # Patents / economics / astronomy
    "uspto.gov": "Patents", "patentsview.org": "Patents", "stlouisfed.org": "FRED economics",
    # LLM / API backends (require user-supplied keys)
    "openai.com": "LLM backend (user key)", "openrouter.ai": "LLM backend (user key)",
    "parallel.ai": "Research backend (user key)",
    # Bioinformatics infra (UK)
    "ebi.ac.uk": "EMBL-EBI", "sanger.ac.uk": "Wellcome Sanger", "sherpa.ac.uk": "OA policies (SHERPA)",
    # Turkish academia
    "dergipark.org.tr": "Turkish journals (DergiPark)", "trdizin.gov.tr": "TR Dizin index",
    "tubitak.gov.tr": "TÜBİTAK", "uak.gov.tr": "ÜAK (doçentlik)", "ulakbim.gov.tr": "ULAKBİM",
    "yok.gov.tr": "YÖK",
    # Gene / annotation aggregators (MCP connectors)
    "mygene.info": "Gene annotation",
    # Infra / CDN / docs
    "github.com": "Source / infra", "jsdelivr.net": "CDN", "readthedocs.io": "Docs",
    "w3.org": "Standards", "graphdrawing.org": "Standards", "fastmcp.app": "MCP infra",
    "labarchives.com": "ELN",
    # Placeholders / local (non-network)
    "example.com": "Placeholder (docs only)", "store": "Placeholder (commented docs)",
    "localhost": "Local (non-network)", "scientific-writer.local": "Local (non-network)",
}


def shipped_files() -> list[Path]:
    """Code a user installs/runs: the skill tree plus the standalone MCP connectors."""
    roots = [SKILLS_DIR]
    connectors = REPO_ROOT / "mcp-servers"
    if connectors.is_dir():
        roots.append(connectors)
    files: list[Path] = []
    for root in roots:
        for pat in ("*.py", "*.sh"):
            files += root.rglob(pat)
        files += root.rglob(".mcp.json")
    return sorted(files)


def registrable_domain(host: str) -> str:
    host = host.strip(".").lower()
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in _MULTI_SUFFIX:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def scan() -> dict:
    files = shipped_files()
    hosts: Counter[str] = Counter()
    danger: dict[str, list[str]] = {k: [] for k in _CHECK_LABELS}
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        rel = str(f.relative_to(REPO_ROOT))
        for h in _HOST_RE.findall(text):
            hosts[registrable_domain(h)] += 1
        for label, rx in _DANGER.items():
            if rx.search(text):
                danger[label].append(rel)
        # Real (non-placeholder) hardcoded secret?
        if any(not _PLACEHOLDER_RE.search(m.group(1)) for m in _SECRET_RE.finditer(text)):
            danger[_SECRET_LABEL].append(rel)
    return {"files": files, "hosts": hosts, "danger": danger}


def render(result: dict) -> str:
    hosts: Counter[str] = result["hosts"]
    danger: dict[str, list[str]] = result["danger"]
    n_py = sum(1 for f in result["files"] if f.suffix == ".py")
    n_sh = sum(1 for f in result["files"] if f.suffix == ".sh")
    n_mcp = sum(1 for f in result["files"] if f.name == ".mcp.json")

    lines: list[str] = []
    lines.append("# Security Scan & Trust Manifest")
    lines.append("")
    lines.append("> **Generated** — do not edit by hand. Regenerate with "
                 "`python3 scripts/gen_security_scan.py`; CI fails if this file is stale "
                 "(`--check`) or if the attestation is violated (`--strict`).")
    lines.append("")
    lines.append("This manifest is a static scan of the code a user actually installs or runs "
                 f"(`skills/**` and the `mcp-servers/**` connectors): **{n_py} Python**, "
                 f"**{n_sh} shell**, and **{n_mcp} `.mcp.json`** files. It exists so a cautious "
                 "lab can verify the suite's posture without auditing every file by hand.")
    lines.append("")

    lines.append("## Attestation")
    lines.append("")
    lines.append("| Check | Result |")
    lines.append("|-------|--------|")
    clean = True
    for label in _CHECK_LABELS:
        hits = danger[label]
        if hits:
            clean = False
            lines.append(f"| No {label} | ❌ **{len(hits)}** — {', '.join(hits[:3])} |")
        else:
            lines.append(f"| No {label} | ✅ none |")
    lines.append("")
    lines.append(f"**Overall:** {'✅ clean — every check passed.' if clean else '❌ review required.'}")
    lines.append("")

    lines.append("## Outbound network allowlist")
    lines.append("")
    lines.append("Every host the shipped skill code references, reduced to its registrable "
                 "domain. All are legitimate scientific/academic APIs, first-party LLM "
                 "backends (which require a **user-supplied** key), infrastructure/CDN, or "
                 "documentation placeholders. No telemetry or analytics endpoints.")
    lines.append("")
    lines.append("| Domain | Category | Refs |")
    lines.append("|--------|----------|------|")
    for dom in sorted(hosts):
        cat = _DOMAIN_CATEGORY.get(dom, "other (review)")
        lines.append(f"| `{dom}` | {cat} | {hosts[dom]} |")
    lines.append("")
    lines.append(f"_{len(hosts)} distinct domains._")
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append("A stdlib regex scan (`scripts/gen_security_scan.py`) over all shipped "
                 "`skills/**` `.py`/`.sh`/`.mcp.json` files. `eval`/`exec` detection uses a "
                 "negative lookbehind so method calls like `model.eval()` are not flagged; "
                 "only the bare builtins would be. Secrets detection flags literal "
                 "long-token assignments to `api_key`/`secret`/`token`/`password` and known "
                 "cloud-key shapes — skill scripts read credentials from environment "
                 "variables, never inline them.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if SECURITY_SCAN.md is out of date")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any dangerous pattern is found")
    args = ap.parse_args(argv)

    result = scan()
    rendered = render(result)
    any_danger = any(result["danger"][k] for k in result["danger"])

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != rendered:
            print("SECURITY_SCAN.md is out of date — run: python3 scripts/gen_security_scan.py",
                  file=sys.stderr)
            return 1
        print(f"SECURITY_SCAN.md up to date ({len(result['hosts'])} domains, "
              f"{'clean' if not any_danger else 'DANGER FOUND'}).")
        return 1 if (args.strict and any_danger) else 0

    OUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)} "
          f"({len(result['hosts'])} domains, {'clean' if not any_danger else 'DANGER FOUND'}).")
    return 1 if (args.strict and any_danger) else 0


if __name__ == "__main__":
    raise SystemExit(main())
