# Similarity Search

Aeon provides tools for finding similar patterns within and across time series:
subsequence search (a query window against every position of a collection) and
whole-series search (a query series against every series in a collection), plus an
approximate index for large collections.

API verified against aeon 1.6.0. The 0.x/early-1.x classes `MassSNN`, `DummySNN`,
`StompMotif`, and `RandomProjectionIndexANN` (and the `aeon.similarity_search.series` /
`.collection` modules) no longer exist — use the estimators below.

## Common Contract

All searchers are **fitted on a collection** shaped `(n_cases, n_channels, n_timepoints)`
and queried with `predict(X, k=...)`, where `X` is one series shaped
`(n_channels, n_timepoints)`. `predict` returns `(indexes, distances)`:

- **Subsequence search**: `indexes` has shape `(n_matches, 2)` — `(case, timestamp)` pairs.
- **Whole-series search**: `indexes` has shape `(n_matches,)` — case indices.

Extra search options (`dist_threshold`, `inverse_distance`, `allow_trivial_matches`,
`exclusion_factor`, `X_index`) are passed as keyword arguments to `predict`; which ones
apply differs per estimator, so check its docstring.

## Subsequence Search (`aeon.similarity_search.subsequence`)

- `MASS(length, normalize=False)` - Mueen's Algorithm for Similarity Search
  - FFT-based distance profile, O(n log n) per series
  - **Use when**: Exact Euclidean nearest-neighbour windows in long series
- `NaiveSubsequenceSearch(length, normalize=False, distance="squared", distance_params=None)`
  - Brute-force distance profile with any aeon distance
  - **Use when**: Small data, exact baseline, or a non-Euclidean distance

```python
import numpy as np
from aeon.similarity_search.subsequence import MASS

# A series with the same sine pattern embedded twice
rng = np.random.default_rng(0)
pattern = np.sin(np.linspace(0, 2 * np.pi, 50))
y = np.concatenate([
    pattern + rng.normal(0, 0.1, 50),
    rng.normal(0, 1, 100),
    pattern + rng.normal(0, 0.1, 50),
    rng.normal(0, 1, 100),
])

X = y.reshape(1, 1, -1)          # collection of one univariate series
query = pattern.reshape(1, -1)   # (n_channels, length); length must equal `length`

searcher = MASS(length=50, normalize=True).fit(X)
indexes, distances = searcher.predict(query, k=3)
# indexes -> [[0, 0], [0, 150], ...]: both embedded occurrences are found first
```

## Whole-Series Search (`aeon.similarity_search.whole_series`)

- `NaiveSeriesSearch(normalize=False, distance="squared", distance_params=None)`
  - Exact k-NN over whole series with any aeon distance (e.g. `"dtw"`)
- `SimHashIndexANN(n_tables=20, n_bits_per_table=8, random_state=None, normalize=True)`
  - Locality-sensitive hashing index; approximate, fast on large collections

```python
from aeon.datasets import load_classification
from aeon.similarity_search.whole_series import NaiveSeriesSearch, SimHashIndexANN

X_train, _ = load_classification("GunPoint", split="train")

exact = NaiveSeriesSearch(distance="dtw").fit(X_train)
idx, dist = exact.predict(X_train[0], k=3)        # idx[0] == 0 (the query itself)

ann = SimHashIndexANN(random_state=0).fit(X_train)
idx_ann, dist_ann = ann.predict(X_train[0], k=5)  # approximate neighbours
```

## Matrix Profile, Motifs, and Discords

aeon 1.6 has no dedicated motif-discovery estimator. Compute the matrix profile with
`MatrixProfileTransformer` (a thin wrapper over `stumpy.stump`; install `stumpy`):

```python
import numpy as np
from aeon.transformations.series import MatrixProfileTransformer

mp = MatrixProfileTransformer(window_length=50).fit_transform(y)

motif_start = int(np.argmin(mp))     # window with the closest non-trivial match
discord_start = int(np.argmax(mp))   # most isolated window (anomaly candidate)
```

- **Distance profile**: distances from one query to all subsequences
- **Matrix profile**: each subsequence's distance to its nearest non-trivial neighbour
- **Motif**: pair of subsequences with minimum matrix-profile distance
- **Discord**: subsequence with maximum matrix-profile distance (anomaly)

For discord-based anomaly scoring as an estimator, use `STOMP` from
`aeon.anomaly_detection.series.distance_based` (see `anomaly_detection.md`). For
full motif sets (top-k motifs with all their occurrences), `stumpy.motifs` is the
reference implementation.

## Algorithm Selection

- **Exact subsequence search**: `MASS`
- **Subsequence search with DTW or other elastic distance**: `NaiveSubsequenceSearch`
- **Exact whole-series k-NN**: `NaiveSeriesSearch`
- **Fast approximate whole-series search**: `SimHashIndexANN`
- **Motifs / discords**: `MatrixProfileTransformer` (+ `stumpy`), or `STOMP` for discords

## Use Cases

### Pattern Matching
Find where a template occurs in a long recording:

```python
searcher = MASS(length=len(heartbeat_template), normalize=True)
searcher.fit(ecg.reshape(1, 1, -1))
indexes, distances = searcher.predict(heartbeat_template.reshape(1, -1), k=20)
onsets = indexes[distances < threshold][:, 1]
```

### Time Series Retrieval
Find the most similar series in a database:

```python
index = SimHashIndexANN(random_state=0).fit(time_series_database)
neighbours, distances = index.predict(query_series, k=10)
```

## Best Practices

1. **Window size**: Critical parameter for subsequence methods
   - Too small: captures noise
   - Too large: misses fine-grained patterns
   - Rule of thumb: roughly one period of the pattern you care about

2. **Normalization**: Set `normalize=True` for shape matching regardless of amplitude
   and offset; leave it off when absolute level matters.

3. **Distance metrics**: Euclidean (MASS) is fastest; DTW (`NaiveSubsequenceSearch`
   / `NaiveSeriesSearch` with `distance="dtw"`) tolerates temporal warping at much
   higher cost.

4. **Trivial matches**: when the query comes from the fitted data, its own position
   (and overlapping neighbours) will rank first — use the estimator's
   `exclusion_factor` / `allow_trivial_matches` options or discard overlapping hits.

5. **Performance**:
   - MASS is O(n log n) per series vs O(n·m) for the naive search
   - The ANN index trades exactness for speed on large collections
