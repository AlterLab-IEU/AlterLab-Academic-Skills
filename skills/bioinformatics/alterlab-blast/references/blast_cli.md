# BLAST+ 2.17.0 — Command-Line Reference

Deep reference for the AlterLab BLAST+ skill. Pins to NCBI BLAST+ **2.17.0**.
Primary source: NCBI BLAST Command Line Applications User Manual
(https://www.ncbi.nlm.nih.gov/books/NBK569856/) and its options appendix
(https://www.ncbi.nlm.nih.gov/books/NBK279684/).

## Programs

| Program | Query | Subject DB (`-dbtype`) | Typical use |
|---------|-------|------------------------|-------------|
| `blastn` | nucleotide | `nucl` | nucleotide vs nucleotide |
| `blastp` | protein | `prot` | protein vs protein |
| `blastx` | nucleotide (6-frame translated) | `prot` | annotate an unknown ORF/transcript |
| `tblastn` | protein | `nucl` (translated) | find a protein in a genome/transcriptome |

All take `-query`, `-db`, `-out`, `-evalue`, `-outfmt`, `-num_threads`.

## Building a database: `makeblastdb`

```bash
makeblastdb -in seqs.fasta -dbtype {nucl|prot} -parse_seqids \
  -out mydb -title "human description"
```

- **`-parse_seqids`** parses the FASTA deflines into the DB's index so you can
  later retrieve specific records with `blastdbcmd -entry <id>` and so the IDs
  stay clean for DIAMOND reuse. It cannot be added retroactively — rebuild if you
  forgot it.
- `-dbtype nucl` for nucleotide subjects, `prot` for protein.
- BLAST+ 2.17.0 can read **gzip- and zstd-compressed FASTA** input directly and
  writes JSON DB metadata alongside the index.
- Multi-FASTA on stdin: `... -in - ...`.

### Retrieving sequences back out

```bash
blastdbcmd -db mydb -entry sp|P01308|INS_HUMAN          # one record
blastdbcmd -db mydb -entry all -outfmt "%f"             # dump all as FASTA
blastdbcmd -db mydb -info                               # DB stats
```

`blastdbcmd -entry` only works if the DB was built with `-parse_seqids`.

## Output formats (`-outfmt`)

| `-outfmt` | Meaning |
|-----------|---------|
| `0` | pairwise (human-readable; default) |
| `6` | **tabular** — the canonical machine-parseable format |
| `7` | tabular with comment lines (`# ` headers + `# N hits found`) |
| `5` | BLAST XML |
| `15` | BLAST JSON (single file) |

Format `6`/`7` default columns (the `std` keyword) are exactly:

```
qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
```

Customize by appending a **quoted** space-separated keyword list (BLAST+ syntax):

```bash
blastp -query q.faa -db nr -outfmt '6 qseqid sseqid pident length evalue bitscore staxids sscinames' -out hits.tsv
```

Useful extra keywords: `staxids`, `sscinames`, `qcovs` (query coverage per
subject), `qlen`, `slen`, `stitle`. (DIAMOND uses the *unquoted* form — see
`diamond.md`.)

## `-task` (blastn)

`blastn` ships several task presets; the default is `megablast`:

| `-task` | When |
|---------|------|
| `megablast` (default) | highly similar sequences (same species, sequencing-error scale) |
| `dc-megablast` | discontiguous megablast — inter-species comparison |
| `blastn` | traditional, more sensitive to divergent hits |
| `blastn-short` | short queries (< ~30 nt): primers, sgRNA, oligos |

`blastp` likewise has `blastp` (default), `blastp-fast`, `blastp-short`.
Picking the wrong task is a common cause of "BLAST missed an obvious hit".

## `-max_target_seqs` — the heuristic trap

From the options appendix, `-max_target_seqs` is the **"Number of aligned
sequences to keep"** (default **500**), applied with report formats above
`-outfmt 4`. Critically:

- It is a **heuristic limit applied during the search**, not a post-hoc "return
  the N best" filter. The set of sequences kept is **not guaranteed** to be the N
  highest-scoring ones.
- **Ties are broken by order of sequences in the database**, not by score.
- Therefore `-max_target_seqs 1` does **not** reliably return the single best
  hit. To get a true best-hit, leave `-max_target_seqs` generous and select the
  top row *after* sorting by `bitscore` (see `scripts/parse_blast_tab.py`).

## Taxonomy scoping {#taxonomy}

```bash
blastn -query q.fna -db nt -taxids 9606            # restrict to Homo sapiens
blastp -query q.faa -db nr -taxids 2,4751          # bacteria + fungi
blastp -query q.faa -db nr -negative_taxids 2      # exclude bacteria
```

- `-taxids` / `-negative_taxids` take comma-separated NCBI taxids; subtree
  expansion is automatic (a clade taxid covers its descendants).
- `-taxidlist` / `-negative_taxidlist` read taxids from a file.
- Requires a **taxonomy-aware DB**: NCBI's pre-formatted `nt` / `nr` ship with
  the needed taxid mapping; for a custom DB supply taxids at build time
  (`-taxid` / `-taxid_map`) so scoping works.

## Threading: `-num_threads` and `-mt_mode`

- `-num_threads N` — number of CPU threads.
- `-mt_mode` (integer) controls *how* work is split across threads:
  - `0` (default) — split by database volume; best for **few large** queries.
  - `1` — split by query; set this when searching **many small** queries so all
    threads stay saturated. The appendix describes mode 1 as the setting for
    "a large number of queries … with multiple threads".
- BLAST+ 2.15+ can auto-select the mode; set it explicitly for predictable
  behavior on batch jobs.

## Common e-value / filter flags

- `-evalue 1e-5` — expectation-value threshold (lower = stricter).
- `-qcov_hsp_perc 80` — minimum % query coverage per HSP.
- `-perc_identity 90` — (blastn) minimum percent identity.
- `-word_size`, `-gapopen`, `-gapextend`, `-reward`, `-penalty` — alignment
  scoring knobs; defaults differ per `-task`.

## Worked example: annotate unknown transcripts against nr

```bash
# Translated nucleotide query vs protein nr, taxonomy + coverage columns
blastx -query transcripts.fna -db nr \
  -task blastx \
  -evalue 1e-10 -max_target_seqs 50 -num_threads 8 -mt_mode 1 \
  -outfmt '6 qseqid sseqid pident length evalue bitscore staxids sscinames qcovs' \
  -out transcripts_vs_nr.tsv

uv run python scripts/parse_blast_tab.py transcripts_vs_nr.tsv \
  --columns 'qseqid sseqid pident length evalue bitscore staxids sscinames qcovs' \
  --best-hit --min-identity 30 --min-qcov 50
```
