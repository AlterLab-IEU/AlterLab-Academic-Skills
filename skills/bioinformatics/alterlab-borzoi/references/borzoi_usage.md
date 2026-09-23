# Borzoi — Usage Reference

Deeper detail for `alterlab-borzoi`, verified against the upstream `calico/borzoi` README and
the `borzoi-pytorch` package (0.5.1, current as of 2026-09).

## Two runtimes

| | Reference (TensorFlow) | PyTorch port |
|---|---|---|
| Package | `calico/borzoi` + `calico/baskerville`, installed from git (`pip install -e .`) | `pip install borzoi-pytorch` |
| Framework pin | TensorFlow **2.15.x** | current PyTorch |
| Weights | 4 replicate `.h5` files per species from `storage.googleapis.com/seqnn-share/borzoi/f{0..3}/`, or `./download_models.sh` | Hugging Face `johahi/borzoi-replicate-[0-3]`, `…-mouse` |
| Extras | training (`calico/westminster`), data processing, published tutorials | Flashzoi and Borzoi Prime variants |

The PyTorch port reproduces the reference implementation's predictions (the repo ships a
comparison notebook); pick TensorFlow when you need the published training/scoring scripts,
PyTorch when you want to embed Borzoi in a torch pipeline.

```python
from borzoi_pytorch import Borzoi

model = Borzoi.from_pretrained("johahi/borzoi-replicate-0").eval().cuda()

# Flashzoi: ~3x faster at comparable or slightly better accuracy, needs FlashAttention-2
fast = Borzoi.from_pretrained("johahi/flashzoi-replicate-0").eval().cuda()

# Borzoi Prime (human head) uses its own class
from borzoi_pytorch import Prime
prime = Prime.from_pretrained("johahi/borzoi-prime-replicate-0").eval().cuda()
```

Averaging the four replicates is the standard way to stabilise variant scores.

## Lineage

Borzoi extends the **Enformer** sequence-to-function paradigm to a longer context window and
RNA-seq coverage prediction (Linder et al., *Nature Genetics* 2025,
doi:10.1038/s41588-024-02053-6). Existing Enformer tooling concepts — input window, one-hot
encoding, multi-track output, SAD/SED-style variant scoring — carry over.

## Predicting tracks

1. Extract the reference sequence window centred on the locus (coordinates + a genome
   reference FASTA, or a supplied FASTA).
2. One-hot encode it to the model's expected input length.
3. Run the model to get predicted coverage across its output tracks (RNA-seq, CAGE, ATAC,
   ChIP; human and mouse heads have different track sets — read the `targets.txt` that ships
   with the weights to map track indices to assays/tissues).

## Variant effect scoring

1. Build **reference** and **alternate** sequences for the variant, centred in the window.
2. Predict tracks for both.
3. Summarise the difference (SAD/SED-style aggregates over the relevant gene or region).

The upstream repo's `tutorials/latest/score_variants` (and a `legacy` variant using the
manuscript's transformations) is the reference implementation — follow it rather than
re-deriving the aggregation. The curated e-/s-/pa-/ipaQTL benchmark sets used in the paper
are published under `gs://borzoi-paper/qtl/`, which is the honest way to calibrate what a
given score magnitude means.

Prioritise candidate non-coding variants by predicted change, and remember this is a
*prediction*: corroborate with measured data and known annotations (`alterlab-gnomad` for
frequency, `alterlab-clinvar` for clinical significance).

## In-silico mutagenesis

Mutate each base across a regulatory element and read predicted-track deltas to localise the
functionally important positions. The repo's `tutorials/latest/interpret_sequence` covers
gradient-based attribution as a cheaper alternative to exhaustive ISM.

## Mini Borzoi models

Calico also publishes smaller models trained on subsets of modalities (e.g. K562 RNA-seq
only, or DNase+ATAC+RNA) under `gs://seqnn-share/borzoi/mini/`, each with its own
`targets.txt` and `params.json`. These are a good fit when you only care about one assay and
want a faster model.

## GPU dispatch

Genome-wide or many-variant scans are heavy — dispatch via `alterlab-remote-compute`
(submit → poll → harvest), and consider Flashzoi plus replicate-averaging to keep runtime
manageable.
