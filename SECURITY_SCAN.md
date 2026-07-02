# Security Scan & Trust Manifest

> **Generated** — do not edit by hand. Regenerate with `python3 scripts/gen_security_scan.py`; CI fails if this file is stale (`--check`) or if the attestation is violated (`--strict`).

This manifest is a static scan of the code a user actually installs (`skills/**`): **236 Python**, **3 shell**, and **2 `.mcp.json`** files. It exists so a cautious lab can verify the suite's posture without auditing every file by hand.

## Attestation

| Check | Result |
|-------|--------|
| No os.system() | ✅ none |
| No subprocess shell=True | ✅ none |
| No builtin eval() on input | ✅ none |
| No builtin exec() on input | ✅ none |
| No pipe-to-shell (curl|wget | sh) | ✅ none |
| No hardcoded OpenAI key | ✅ none |
| No hardcoded AWS key | ✅ none |
| No hardcoded generic secret | ✅ none |

**Overall:** ✅ clean — every check passed.

## Outbound network allowlist

Every host the shipped skill code references, reduced to its registrable domain. All are legitimate scientific/academic APIs, first-party LLM backends (which require a **user-supplied** key), infrastructure/CDN, or documentation placeholders. No telemetry or analytics endpoints.

| Domain | Category | Refs |
|--------|----------|------|
| `arxiv.org` | Preprints / literature | 11 |
| `bindingdb.org` | Binding affinities | 2 |
| `biorxiv.org` | Preprints / literature | 5 |
| `brenda-enzymes.org` | Enzymes | 2 |
| `broadinstitute.org` | Genomics | 2 |
| `cbioportal.org` | Cancer genomics | 2 |
| `clinicaltrials.gov` | Clinical trials | 2 |
| `clinpgx.org` | Pharmacogenomics | 3 |
| `crossref.org` | Scholarly metadata | 6 |
| `datacommons.org` | Open data | 4 |
| `depmap.org` | Cancer dependency | 1 |
| `dergipark.org.tr` | Turkish journals (DergiPark) | 6 |
| `doaj.org` | Open-access journals | 2 |
| `docking.org` | Compound libraries | 4 |
| `doi.org` | DOI resolver | 26 |
| `drugbank.ca` | Drugs | 1 |
| `ebi.ac.uk` | EMBL-EBI | 9 |
| `elixir.no` | Bioinformatics infra | 3 |
| `ensembl.org` | Genomics | 3 |
| `example.com` | Placeholder (docs only) | 1 |
| `fastmcp.app` | MCP infra | 1 |
| `fda.gov` | Regulatory | 1 |
| `figshare.com` | Research data | 1 |
| `github.com` | Source / infra | 23 |
| `graphdrawing.org` | Standards | 1 |
| `gtexportal.org` | Expression | 2 |
| `hmdb.ca` | Metabolites | 4 |
| `jsdelivr.net` | CDN | 1 |
| `kegg.jp` | Pathways | 3 |
| `labarchives.com` | ELN | 3 |
| `localhost` | Local (non-network) | 6 |
| `materialsproject.org` | Materials | 1 |
| `metabolomicsworkbench.org` | Metabolomics | 3 |
| `monarchinitiative.org` | Phenotypes | 3 |
| `nf-co.re` | nf-core pipelines | 1 |
| `nih.gov` | NCBI / NIH | 15 |
| `openai.com` | LLM backend (user key) | 1 |
| `openalex.org` | Scholarly index | 16 |
| `openarchives.org` | OAI-PMH | 2 |
| `openrouter.ai` | LLM backend (user key) | 19 |
| `opentargets.org` | Target–disease | 1 |
| `parallel.ai` | Research backend (user key) | 5 |
| `patentsview.org` | Patents | 1 |
| `pharmvar.org` | Pharmacogenomics | 3 |
| `purl.org` | Persistent URLs | 1 |
| `rcsb.org` | Protein structures | 6 |
| `reactome.org` | Pathways | 3 |
| `readthedocs.io` | Docs | 2 |
| `sanger.ac.uk` | Wellcome Sanger | 1 |
| `scientific-writer.local` | Local (non-network) | 1 |
| `semanticscholar.org` | Scholarly index | 3 |
| `sherpa.ac.uk` | OA policies (SHERPA) | 4 |
| `sron.nl` | Spectroscopy | 1 |
| `stlouisfed.org` | FRED economics | 3 |
| `store` | Placeholder (commented docs) | 1 |
| `string-db.org` | Protein interactions | 4 |
| `tdcommons.ai` | Therapeutics benchmarks | 1 |
| `trdizin.gov.tr` | TR Dizin index | 4 |
| `tubitak.gov.tr` | TÜBİTAK | 2 |
| `uak.gov.tr` | ÜAK (doçentlik) | 2 |
| `ulakbim.gov.tr` | ULAKBİM | 2 |
| `uniprot.org` | Proteins | 1 |
| `uspto.gov` | Patents | 5 |
| `w3.org` | Standards | 2 |
| `wikipedia.org` | Reference | 1 |
| `yok.gov.tr` | YÖK | 3 |

_66 distinct domains._

## Method

A stdlib regex scan (`scripts/gen_security_scan.py`) over all shipped `skills/**` `.py`/`.sh`/`.mcp.json` files. `eval`/`exec` detection uses a negative lookbehind so method calls like `model.eval()` are not flagged; only the bare builtins would be. Secrets detection flags literal long-token assignments to `api_key`/`secret`/`token`/`password` and known cloud-key shapes — skill scripts read credentials from environment variables, never inline them.

