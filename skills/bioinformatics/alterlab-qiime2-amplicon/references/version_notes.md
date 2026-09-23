# Version notes — QIIME 2 2026.1 -> 2026.7

The current release is **QIIME 2 2026.7** (announced 2026-07-22,
https://qiime2.org/news/qiime-2-2026-7-is-now-available-34255/). The amplicon pipeline
commands this skill teaches are unchanged across 2026.1 -> 2026.7; what moved is the
distribution name, the env files, and some plugin boundaries on the shotgun side. Facts
about the `summarize` change below come from the official 2026.1 release announcement
(https://qiime2.org/news/qiime-2-2026-1-is-now-available-33935/, announced 2026-01-28).

## Breaking change: `feature-table summarize`

In `q2-feature-table`, **2026.1 swapped two action names**:

- the old `summarize` **visualizer** was renamed **`_summarize`** (now private), and
- the former **`summarize_plus` pipeline** was renamed to **`summarize`**.

Net effect: today, calling `qiime feature-table summarize` runs what used to be
`summarize_plus` — the **enhanced** summary that also produces feature-frequency and
sample-frequency artifacts in addition to the `.qzv`. Consequences for workflows:

- **Older tutorials that call `summarize_plus`** must switch to `summarize`.
- Do **not** call `_summarize` (private/legacy).
- Practically, keep using `qiime feature-table summarize` and read `table.qzv`; that *is*
  the plus behavior now.

## Distribution rename, shipped in 2026.4

The 2026.1 notes announced: *"in our next release (2026.4) we will be renaming the amplicon
distribution to qiime2, since this is the historical collection of packages that our user
base is familiar with in the context of the qiime2 namespace."* This shipped as planned and
holds in 2026.7.

Implications:

- The conda **env file name and channel path change** (`rachis-qiime2-<platform>-conda.yml`
  under `<release>/qiime2/released/`; see `installation.md`).
- The **plugin commands do not change** — `qiime tools import`,
  `qiime cutadapt trim-paired`, `qiime dada2 denoise-paired`,
  `qiime feature-classifier classify-sklearn`,
  `qiime diversity core-metrics-phylogenetic` are all stable across the rename.

## Framework renamed to `rachis`

Also in 2026.1: the underlying QIIME 2 **framework was renamed from `qiime2` to
`rachis`** and is now published on PyPI. This is the framework package, not the user-facing
`qiime` CLI; pipeline command names are unaffected. (This is why the 2026.4 env files are
named `rachis-qiime2-*`.)

## Other plugin updates noted in 2026.1

- `q2-alignment`: added protein-sequence support.
- `q2-boots`: improved memory efficiency in medoid calculations.
- `q2-types`: added formats for genomic data and taxonomy-to-contig mappings.

## Plugin moves in 2026.7

These affect the shotgun-metagenomics side, not the amplicon pipeline, but they break older
command lines:

- Binning / MAG actions moved out of `q2-annotate` into a new **`q2-mag`** plugin.
- Pangenome filtering actions moved into **`q2-quality-control`**.
- `da-barplot` was replaced by **`ancombc2-visualizer`**, which took over the old name.
- `q2view` now shows annotations in the provenance DAG.

## How to stay current

When running a different release, **verify command names and install files from the
official sources** rather than trusting this file:

- Latest announcement: https://qiime2.org/news/qiime-2-2026-7-is-now-available-34255/
- 2026.1 announcement: https://qiime2.org/news/qiime-2-2026-1-is-now-available-33935/
- Amplicon docs: https://amplicon-docs.qiime2.org/
- Library quickstart (install): https://library.qiime2.org/quickstart/amplicon
- In the active env: `qiime info` and `qiime <plugin> <action> --help`.
