---
name: alterlab-brenda
description: Access the BRENDA enzyme database — keyless through its public enzyme pages and DSMZ SPARQL endpoint, or through its SOAP API with an optional login — to retrieve kinetic parameters (Km, kcat, kcat/Km, Ki, IC50), pH and temperature optima, inhibitors and activators, reaction equations, organism data, and substrate-specific enzyme information indexed by EC number. Use when looking up enzyme kinetics, turnover numbers, or substrate specificity for biochemical research and metabolic pathway analysis. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read WebFetch Bash(curl:*) Bash(python:*)
compatibility: No API key or login required. Keyless default — BRENDA's public enzyme pages (www.brenda-enzymes.org/enzyme.php, every table per EC number, CC BY 4.0) parsed by scripts/brenda_web.py (standard library) plus the DSMZ BRENDA SPARQL endpoint (sparql.dsmz.de/api/brenda) for searches across EC numbers. An optional free BRENDA login (BRENDA_EMAIL/BRENDA_PASSWORD) switches the helpers to the SOAP API via zeep.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-10-22"
    credentials: "optional: BRENDA_EMAIL, BRENDA_PASSWORD (a free BRENDA login for the SOAP API; the keyless web backend reads the same tables from BRENDA's public pages)"
---

# BRENDA Database

## Overview

BRENDA (BRaunschweig ENzyme DAtabase) is the world's most comprehensive enzyme information
system, containing detailed enzyme data from scientific literature. Query kinetic parameters
(Km, kcat, Ki), reaction equations, substrate specificities, organism information, and optimal
conditions — **with no login**: every BRENDA table for an EC number is on its public enzyme
page, and DSMZ (BRENDA's operator) runs a keyless SPARQL endpoint over the same data. The
SOAP API is an optional backend for users with a BRENDA account.

## When to Use This Skill

This skill should be used when:
- Searching for enzyme kinetic parameters (Km, kcat, Vmax)
- Retrieving reaction equations and stoichiometry
- Finding enzymes for specific substrates or reactions
- Comparing enzyme properties across different organisms
- Investigating optimal pH, temperature, and conditions
- Accessing enzyme inhibition and activation data
- Supporting metabolic pathway reconstruction and retrosynthesis
- Performing enzyme engineering and optimization studies
- Analyzing substrate specificity and cofactor requirements

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Metabolic pathway maps, KEGG Orthology, or compound-to-pathway mapping | `alterlab-kegg` |
| Genome-scale flux simulation (FBA/FVA, knockouts) | `alterlab-cobrapy` |
| Drug/compound bioactivity (IC50, Ki) against drug targets | `alterlab-chembl` |
| Protein sequence, domains, or GO annotation of an enzyme | `alterlab-uniprot` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-kegg`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Core Capabilities

BRENDA access is organized into nine capability areas. Copy-ready snippets for each live in
`references/capabilities.md`.

1. **Kinetic parameter retrieval** — Km, kcat, Vmax by EC number / organism / substrate.
2. **Reaction information** — reaction equations and stoichiometry.
3. **Enzyme discovery** — find enzymes by substrate, product, or reaction pattern.
4. **Organism-specific data** — compare enzyme properties across organisms.
5. **Environmental parameters** — optimal/stability pH and temperature, cofactors.
6. **Substrate specificity** — Km/Vmax/kcat per substrate, affinity ranking.
7. **Inhibition and activation** — Ki, IC50, activators and mechanisms.
8. **Enzyme engineering support** — thermophilic homologs, pH-stable variants.
9. **Kinetic modeling** — modeling parameters and Michaelis-Menten plots.

## Keyless Quick Start (default)

`scripts/brenda_web.py` (standard library, no install). Verified live 2026-10-22:

```bash
W=scripts/brenda_web.py
python $W list 1.1.1.1                                    # 44 tables; KM VALUE 1064 rows
python $W table 1.1.1.1 km --substrate ethanol --csv      # 149 Km rows, 56 organisms
python $W table 1.1.1.1 km --substrate ethanol --organism "Saccharomyces cerevisiae"
python $W table 1.1.1.27 ki --csv                          # LDH Ki VALUE, 82 rows
python $W table 1.1.1.1 temperature_optimum                # Pyrococcus furiosus 100 °C ...
python $W enzymes-for 2-phenylethanol                      # SPARQL: 2.3.1.84, 1.1.1.2, 1.1.1.1, ...
python $W reactions 2-phenylethanol --ec 1.1.1.1           # 2-phenylethanol + NAD(+) = phenylacetaldehyde + NADH
python $W enzymes-for "oxamic acid" --role Inhibitor       # names are BRENDA ligand names, exact
```

Table aliases: `km`, `kcat` (TURNOVER NUMBER), `kcat_km`, `ki`, `ic50`, `inhibitor`,
`activator`, `specific_activity`, `ph_optimum`, `ph_range`, `ph_stability`,
`temperature_optimum`, `temperature_range`, `temperature_stability`, `organism`,
`substrate` (substrate/product pairs with reversibility), `natural_substrate`, `reaction`,
`cofactor`, `metals`. Every row carries ORGANISM, UNIPROT, COMMENTARY (pH, °C, mutant,
isoenzyme) and the BRENDA LITERATURE id with a `literature.php` link — report them, since
BRENDA values are per-publication, not consensus values.

Etiquette: one page per EC number holds all tables (cached for 7 days in
`./brenda_web_cache`); the script waits 2 s between requests (robots.txt Crawl-delay: 2).
Data are CC BY 4.0 — cite BRENDA. The SPARQL graph has reactions, substrates/products,
inhibitors, activators and organisms but **no numeric kinetics**; numbers come from the pages.

**Coverage, and where to look when BRENDA is thin** (all keyless, verified 2026-10-22):

| Source | Covers | Thinner on |
|--------|--------|-----------|
| BRENDA enzyme pages (`brenda_web.py table`) | Km, kcat, kcat/Km, Ki, IC50, specific activity, pH/temperature optimum/range/stability, inhibitors, activators, cofactors, organisms, substrates/products, literature | organisms nobody measured — e.g. EC 6.3.1.2 has 13 *E. coli* Km rows but none for *S. cerevisiae* or *T. thermophilus*; say so rather than infer |
| BRENDA SPARQL (`enzymes-for`, `reactions`) | which EC numbers use a compound as substrate/product/inhibitor/activator; reaction equations | numeric values; exact BRENDA ligand names only |
| UniProt REST (`rest.uniprot.org/uniprotkb/search?query=ec:1.1.1.1&fields=accession,organism_name,kinetics,ph_dependence,temp_dependence&format=tsv`) | curated KM/Vmax/kcat comments, pH and temperature dependence per protein entry | far fewer values than BRENDA; many entries have none |
| Rhea (`www.rhea-db.org/rhea?query=2-phenylethanol&columns=rhea-id,equation,ec&format=tsv`) | balanced reaction equations with ChEBI ids and EC links | kinetics; some reactions lack an EC |
| ExPASy ENZYME (`enzyme.expasy.org/EC/1.1.1.1.txt`) | official name, alternative names, catalytic activity, cofactors, comments | kinetics, organisms |

SABIO-RK moved to a new web application in 2026; its old `sabioRestWebServices` paths now
return the web page, not data, so it is not scripted here — use its web search by hand if
needed.

## Core Workflow

The typical entry point retrieves kinetic data by EC number, then parses the delimited
response. `brenda_client` picks the backend: keyless web pages by default, SOAP when a
BRENDA login is set (`BRENDA_BACKEND=web|soap|auto` forces one; `soap` without a login
fails with an error naming the variables instead of answering from the web pages):

```python
from scripts.brenda_client import get_km_values
from scripts.brenda_queries import parse_km_entry

km_data = get_km_values("1.1.1.1", organism="Saccharomyces cerevisiae")
for entry in km_data:
    parsed = parse_km_entry(entry)
    # parse_km_entry keys mirror the raw BRENDA fields: 'kmValue' (string)
    # plus a derived 'km_value_numeric' (float). There is no 'km_value' key.
    print(parsed.get("organism"), parsed.get("substrate"), parsed.get("km_value_numeric"))
```

EC numbers must be fully qualified (e.g. `1.1.1.1`, not `1.1.1`). On the web backend an EC
number is needed for kinetics (find candidates first with `search_enzymes_by_substrate`,
which uses SPARQL); `get_reactions("*", reaction="*2-phenylethanol*")` searches across EC
numbers. `get_inhibitors`, `get_activators`, `get_environmental_parameters(ec, organism=...)`
and `find_thermophilic_homologs(ec, min_temp, substrate=...)` read BRENDA's dedicated tables
on the web backend. See `references/data_formats.md` for the response format.

**SOAP calling convention (optional backend).** The `brenda_zeep.wsdl` operations take *separate* arguments in
WSDL order — `client.service.getKmValue(email, sha256_pw, "ecNumber*1.1.1.1",
"organism*Homo sapiens", "kmValue*", "kmValueMaximum*", "substrate*", "commentary*",
"ligandStructureId*", "literature*")` — and return lists of typed objects. A single
comma-joined string fails in zeep ("Missing element password"). `scripts/brenda_client.py`
handles the argument order and converts results to `field*value#…` strings for the parsers.

**Usage policy.** BRENDA asks clients to send at most one request per second (the client
enforces this; the web backend waits 2 s), and its data are licensed CC BY 4.0 — cite BRENDA
in derived work.

## Installation Requirements

Nothing for the keyless path. Optional extras:

```bash
uv pip install pandas matplotlib seaborn   # exports and plots
uv pip install zeep                        # only for the optional SOAP backend
```

## Optional: SOAP Login

The SOAP backend needs a free BRENDA account; everything above works without it.

1. **Create .env file**:
```
BRENDA_EMAIL=your.email@example.com
BRENDA_PASSWORD=your_brenda_password
```

2. **Or set environment variables**:
```bash
export BRENDA_EMAIL="your.email@example.com"
export BRENDA_PASSWORD="your_brenda_password"
```

3. **Register for BRENDA access**:
   - Visit https://www.brenda-enzymes.org/
   - Create an account
   - Check your email for credentials
   - Note: There's also `BRENDA_EMIAL` (note the typo) for legacy support

## Helper Scripts

This skill ships these Python helper scripts under `scripts/`:

- `scripts/brenda_web.py` — keyless BRENDA access (public enzyme pages + SPARQL); CLI and
  importable `get_table`, `enzymes_for`, `reactions_for`, `sparql`.
- `scripts/brenda_client.py` — backend switch (web by default, SOAP with a login) behind
  `get_km_values` / `get_reactions`.

- `scripts/brenda_queries.py` — high-level enzyme data analysis (parsing, search, cross-organism
  comparison, environmental parameters, specificity, inhibitors/activators, engineering targets).
- `scripts/brenda_visualization.py` — kinetic/pH/temperature/substrate plots and Michaelis-Menten curves.
- `scripts/enzyme_pathway_builder.py` — enzymatic pathway and retrosynthetic route construction.

Full function inventories and usage are in `references/helper_scripts.md`.

## Reference Index

- **`references/api_reference.md`** — Complete SOAP API method docs, parameter lists/formats,
  EC number structure/validation, response specs, error codes, literature citation formats.
- **`references/capabilities.md`** — Copy-ready code for all nine capability areas.
- **`references/workflows.md`** — Six end-to-end workflows (discovery, cross-organism comparison,
  engineering targets, pathway construction, kinetic analysis, industrial selection).
- **`references/helper_scripts.md`** — Function inventory and usage for the three helper scripts.
- **`references/data_formats.md`** — BRENDA response formats, parsing patterns, rate limits,
  error handling, troubleshooting, and additional resources.
