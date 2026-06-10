# DIAMOND — Fast Protein-Space Search

Reference for the DIAMOND fast path of the AlterLab BLAST+ skill.
Primary source: https://github.com/bbuchfink/diamond and its command-line wiki
(https://github.com/bbuchfink/diamond/wiki/3.-Command-line-options).

## What it is

DIAMOND does pairwise alignment of proteins and translated DNA "at 100x-10,000x
speed of BLAST" (project's own claim). It is a drop-in replacement for `blastp`
and `blastx` (protein subject databases only) when BLAST+ is too slow on large
inputs — think millions of query proteins or nr-scale subject DBs. It does
**not** do nucleotide-vs-nucleotide search; for that stay with `blastn`.

## Build a database

```bash
diamond makedb --in reference.faa -d reference_diamond
# --in / -d ; output gets a .dmnd extension
```

Add `--taxonmap`, `--taxonnodes`, `--taxonnames` (NCBI taxonomy dumps) at build
time to enable taxonomic columns/filters in the output.

## Search

```bash
diamond blastp -d reference_diamond -q query.faa -o hits.tsv \
  --ultra-sensitive \
  --outfmt 6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
```

- `--db/-d`, `--query/-q`, `--out/-o` mirror BLAST+.
- `blastx` is also available (`diamond blastx`) for translated-nucleotide queries
  against a protein DB.

### Sensitivity ladder

Fast → most sensitive (mutually exclusive):

`--fast` · `--mid-sensitive` · `--sensitive` · `--more-sensitive` ·
`--very-sensitive` · `--ultra-sensitive`

- Default (no flag) is the fastest mode — fine for high-identity hits, but it
  misses divergent matches.
- `--ultra-sensitive` is the closest to BLAST recall; use it when you would
  otherwise reach for `blastp` and just need it to finish.
- `--sensitive` / `--more-sensitive` are common middle grounds for homology
  searches.

## Output format — the quoting gotcha

DIAMOND's tabular format is `--outfmt 6` (alias `-f 6`) with the same default
columns as BLAST+. **Custom column keywords must be UNQUOTED and
space-separated**, directly after the `6`:

```bash
# CORRECT (DIAMOND):
diamond blastp ... --outfmt 6 qseqid sseqid pident evalue bitscore

# WRONG for DIAMOND (this is the BLAST+ syntax):
diamond blastp ... --outfmt '6 qseqid sseqid pident evalue bitscore'
```

This is the inverse of BLAST+, which wants the spec quoted. Mixing them up is a
frequent silent failure. The resulting `.tsv` is compatible with
`scripts/parse_blast_tab.py`.

## When to choose DIAMOND vs BLAST+

| Situation | Tool |
|-----------|------|
| Nucleotide-vs-nucleotide | BLAST+ `blastn` (DIAMOND can't) |
| Small protein query set, need exact BLAST behavior | BLAST+ `blastp` |
| Millions of proteins / metagenomic ORFs vs nr | DIAMOND `blastp --ultra-sensitive` |
| Translated DNA vs protein at scale | DIAMOND `blastx` |
| Need taxonomy columns | either, but build the DB with the taxonomy maps |

## Version

Pin to a current DIAMOND release (the project's latest at time of writing is
the v2.2.x line). Run `diamond version` and record it alongside results.
