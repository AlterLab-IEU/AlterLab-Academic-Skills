---
name: alterlab-blast
description: "Runs NCBI BLAST+ 2.17.0 sequence searches from the command line: makeblastdb (with -parse_seqids), blastn/blastp/blastx/tblastn with tabular -outfmt 6/7 for parsing, correct -task choice (megablast vs blastn vs blastn-short), -taxids/-negative_taxids taxonomic scoping, and -mt_mode multithreading; plus a DIAMOND blastp --ultra-sensitive path for large protein searches. Warns that -max_target_seqs is a heuristic keep-count, not a top-N best-hits filter. Use when the user wants command-line BLAST, makeblastdb, a local BLAST database, blastn/blastp/blastx/tblastn searches, or DIAMOND protein search. For the Bio.Blast web NCBIWWW API prefer alterlab-biopython; for quick one-liner database lookups prefer alterlab-gget. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash(makeblastdb:*) Bash(blastn:*) Bash(blastp:*) Bash(blastx:*) Bash(tblastn:*) Bash(blastdbcmd:*) Bash(diamond:*)
compatibility: "Requires NCBI BLAST+ 2.17.0 binaries on PATH (conda: `bioconda::blast`; or Homebrew `blast`); no API key or account needed for local searches. DIAMOND (`bioconda::diamond`) is optional and only used for the large-protein fast path. Parsing/QC helper runs under `uv run python` with the standard library only."
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# BLAST+ — Command-Line Sequence Search

Run local NCBI **BLAST+ 2.17.0** searches end-to-end: build a database with
`makeblastdb`, search it with `blastn` / `blastp` / `blastx` / `tblastn`, emit
machine-parseable tabular output, and scope by taxonomy. For very large protein
searches, hand off to **DIAMOND** `blastp --ultra-sensitive` (100x–10,000x the
speed of BLAST, per the DIAMOND project). This is the **CLI / local-database**
skill; it is deliberately distinct from the Biopython web API and the gget
one-liner (see routing table below).

> Bulk DB builds and large searches are CPU/IO-heavy and fully offline — good
> candidates to run on local compute rather than burning API calls.

## When to Use This Skill

Use this skill when the request involves any of:

- "BLAST these sequences", "run blastn/blastp/blastx/tblastn", "command-line BLAST"
- "build a local BLAST database", "makeblastdb", "index this FASTA for BLAST"
- "search my reads against a local nt/nr database", "get tabular BLAST hits I can parse"
- "scope the BLAST search to a taxon" (`-taxids` / `-negative_taxids`)
- "BLAST is too slow on millions of proteins" → DIAMOND `blastp`
- retrieving sequences out of a BLAST DB (`blastdbcmd`, requires `-parse_seqids`)

### Does NOT Trigger

Route adjacent requests to the right sibling skill instead of forcing BLAST+:

| The request is really about… | Route to |
|------------------------------|----------|
| The **web** BLAST API (`Bio.Blast.NCBIWWW.qblast`), or scripting BLAST inside a Python pipeline with `Bio.Blast` parsing | `alterlab-biopython` |
| A **quick one-liner** BLAST/database lookup (`gget blast`, gene/structure/enrichment lookups) | `alterlab-gget` |
| Unified programmatic access to many bio web services (UniProt, KEGG, Ensembl REST, NCBI eUtils) | `alterlab-bioservices` |
| Building/searching a **phylogenetic tree** from sequences, not a similarity search | `alterlab-phylogenetics` |
| Read alignment to a reference genome (BWA/minimap2 → BAM) and SAM/BAM handling | `alterlab-pysam` |
| FASTQ→VCF variant calling pipeline | `alterlab-nf-core-sarek` |
| Transcript-level RNA-seq quantification (salmon/kallisto) | `alterlab-rnaseq-quant` |
| 16S/ITS amplicon classification (QIIME 2) | `alterlab-qiime2-amplicon` |
| Protein **structure** prediction / embeddings (ESM, AlphaFold) | `alterlab-esm` |

If the user explicitly says "web BLAST", "NCBIWWW", or "without installing
anything", they want `alterlab-biopython`, not this skill.

## Quick Start

```bash
# 1. Build a protein DB (‑parse_seqids enables blastdbcmd retrieval + DIAMOND reuse)
makeblastdb -in proteins.fasta -dbtype prot -parse_seqids -out mydb -title "my proteins"

# 2. Search, tabular output you can parse, std 12 columns
blastp -query query.faa -db mydb -outfmt 6 -evalue 1e-5 -out hits.tsv

# 3. QC / summarize the tabular output (stdlib only)
uv run python scripts/parse_blast_tab.py hits.tsv --best-hit
```

`-outfmt 6` is the canonical machine-readable format; its default columns are
the `std` set: `qseqid sseqid pident length mismatch gapopen qstart qend sstart
send evalue bitscore`. Use `-outfmt 7` for the same columns plus comment lines.

## Choosing the Right Program

| Query | Subject DB | Program |
|-------|-----------|---------|
| nucleotide | nucleotide | `blastn` |
| protein | protein | `blastp` |
| nucleotide (translated) | protein | `blastx` |
| protein | nucleotide (translated) | `tblastn` |

`-dbtype` for `makeblastdb` is `nucl` for nucleotide subjects, `prot` for protein.

## The Five Things People Get Wrong

1. **`-max_target_seqs` is NOT a "top N best hits" filter.** It is the number of
   aligned sequences to *keep*, applied during the search as a heuristic cutoff;
   ties are broken "by order of sequences in the database", not by score. Setting
   `-max_target_seqs 1` does **not** reliably return the single best hit. To get
   the best hit, keep a generous value and pick the top row *after* sorting by
   bitscore (see `scripts/parse_blast_tab.py --best-hit`). Default is 500.
2. **Wrong `-task` for `blastn`.** `megablast` (default) is for highly similar
   sequences; use `blastn` for cross-species / more divergent hits and
   `blastn-short` for queries < ~30 nt (primers, sgRNAs). `dc-megablast` is the
   discontiguous option for inter-species comparison.
3. **Forgetting `-parse_seqids` at DB-build time.** Without it you cannot pull
   sequences back out with `blastdbcmd -entry`, and DIAMOND cannot reuse the
   sequence IDs cleanly. You cannot add it later without rebuilding.
4. **Quoting the `-outfmt` custom column list for DIAMOND.** BLAST+ wants the
   spec quoted (`-outfmt '6 qseqid sseqid pident evalue'`); **DIAMOND wants it
   unquoted** (`--outfmt 6 qseqid sseqid pident evalue`). Mixing these up is a
   common silent error.
5. **Multithreading.** Use `-num_threads N`. For *many small queries*, set
   `-mt_mode 1` (split by query) so all threads stay busy; `-mt_mode 0` (default,
   split by database volume) suits few large queries. BLAST+ 2.15+ can choose
   automatically, but set it explicitly when in doubt.

Full option reference, taxonomy scoping, and DB-prep details:
[`references/blast_cli.md`](references/blast_cli.md).

## Taxonomic Scoping

Restrict a search to (or away from) clades by NCBI taxid:

```bash
blastn -query q.fna -db nt -taxids 9606 -outfmt 6 -out human_only.tsv
blastp -query q.faa -db nr -negative_taxids 2 -outfmt 6 -out no_bacteria.tsv
```

Scoping by taxid requires a taxonomy-aware database (one built/downloaded with
its `*.taxid` mapping, e.g. NCBI's pre-formatted `nt` / `nr`). See
[`references/blast_cli.md`](references/blast_cli.md#taxonomy).

## DIAMOND — Fast Path for Large Protein Searches

When `blastp` / `blastx` against millions of proteins is too slow, DIAMOND is a
drop-in for protein-space search:

```bash
diamond makedb --in nr.faa -d nr_diamond
diamond blastp -d nr_diamond -q query.faa -o hits.tsv \
  --ultra-sensitive --outfmt 6 qseqid sseqid pident length evalue bitscore
```

Sensitivity ladder (fast → most sensitive): `--fast`, `--mid-sensitive`,
`--sensitive`, `--more-sensitive`, `--very-sensitive`, `--ultra-sensitive`.
Use `--ultra-sensitive` when you need BLAST-comparable recall; default fast mode
trades sensitivity for speed. DIAMOND's `--outfmt 6` is compatible with the
BLAST+ tabular parser below. Details and tradeoffs:
[`references/diamond.md`](references/diamond.md).

## Recommended Workflow

1. **Pick the program** from the query/subject table above.
2. **Build the DB** with `makeblastdb -parse_seqids` (or download a pre-formatted
   NCBI DB). For >~1M proteins, build a DIAMOND DB instead.
3. **Search** with `-outfmt 6`, an explicit `-evalue` threshold, the right
   `-task` (blastn), and `-num_threads`. Add `-taxids` if scoping.
4. **Parse & QC** with `scripts/parse_blast_tab.py` — it sorts by bitscore,
   extracts best-hit-per-query, applies identity/coverage/e-value filters, and
   flags the `-max_target_seqs` pitfall if the column count looks truncated.
5. **Retrieve** any hit sequence with
   `blastdbcmd -db mydb -entry <id>` (needs `-parse_seqids`).

## Verify Before Reporting

- Confirm `blastn -version` / `diamond version` actually ran — never report hits
  you did not produce.
- State the program, `-task`, `-evalue`, and DB used; results are meaningless
  without them.
- If you used `-max_target_seqs`, confirm best-hit selection was done by
  *post-hoc bitscore sort*, not by trusting the keep-count as a top-N.
- For DIAMOND results, note the sensitivity level used.

## References

- [`references/blast_cli.md`](references/blast_cli.md) — full BLAST+ 2.17.0 option
  reference: programs, `makeblastdb`, `-outfmt` columns, `-task`, taxonomy
  scoping, `-mt_mode`, `blastdbcmd` retrieval, and the `-max_target_seqs` caveat.
- [`references/diamond.md`](references/diamond.md) — DIAMOND DB build, sensitivity
  modes, output formats, and when to choose it over BLAST+.
- NCBI BLAST+ manual: https://www.ncbi.nlm.nih.gov/books/NBK569856/
- DIAMOND: https://github.com/bbuchfink/diamond

Part of the AlterLab Academic Skills suite.
