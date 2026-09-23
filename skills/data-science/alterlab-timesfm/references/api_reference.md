# TimesFM API Reference

The `timesfm` package (>= 2.0 on PyPI; current 3.0.2 as of 2026-09) ships two APIs:
TimesFM 2.5 (`timesfm.TimesFM_2p5_200M_torch`, below) and TimesFM 3.0 (`timesfm3`, see
"TimesFM 3.0 API" at the end). The 1.x/2.0 `TimesFmHparams` / `TimesFmCheckpoint` /
`TimesFm(...)` API and the `freq=` argument exist only in `timesfm==1.3.0`.

## Model Classes

### `timesfm.TimesFM_2p5_200M_torch`

The primary model class for TimesFM 2.5 (200M parameters, PyTorch backend).

#### `from_pretrained()`

```python
model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
    "google/timesfm-2.5-200m-pytorch",
    cache_dir=None,          # Optional: custom cache directory
    force_download=False,    # True re-downloads the ~0.9 GB weights even if cached
)
```

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `model_id` | str | `"google/timesfm-2.5-200m-pytorch"` | Hugging Face model ID |
| `revision` | str \| None | None | Specific model revision |
| `cache_dir` | str \| Path \| None | None | Custom cache directory |
| `force_download` | bool | False | Force re-download of weights |

**Returns**: Initialized `TimesFM_2p5_200M_torch` instance (not yet compiled).

#### `compile()`

Compiles the model with the given forecast configuration. **Must be called before `forecast()`.**

```python
model.compile(
    timesfm.ForecastConfig(
        max_context=1024,
        max_horizon=256,
        normalize_inputs=True,
        per_core_batch_size=32,
        use_continuous_quantile_head=True,
        force_flip_invariance=True,
        infer_is_positive=True,
        fix_quantile_crossing=True,
    )
)
```

`compile()` rounds `max_context` up to a multiple of the 32-step input patch and `max_horizon`
up to a multiple of the 128-step output patch. It raises `ValueError` if
`max_context + max_horizon > 16384`, or if `use_continuous_quantile_head=True` with
`max_horizon > 1024`. `forecast()` raises `RuntimeError` if the model is not compiled and
`ValueError` if `horizon > max_horizon`.

#### `forecast()`

Run inference on one or more time series.

```python
point_forecast, quantile_forecast = model.forecast(
    horizon=24,
    inputs=[array1, array2, ...],
)
```

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `horizon` | int | Number of future steps to forecast |
| `inputs` | list[np.ndarray] | List of 1-D numpy arrays (each is a time series) |

**Returns**: `tuple[np.ndarray, np.ndarray]`

- `point_forecast`: shape `(batch_size, horizon)` — median (0.5 quantile)
- `quantile_forecast`: shape `(batch_size, horizon, 10)` — [mean, q10, q20, ..., q90]

**Raises**: `RuntimeError` if model is not compiled.

**Key behaviors**:

- Leading NaN values are stripped automatically
- Internal NaN values are linearly interpolated
- Series longer than `max_context` are truncated (last `max_context` points used)
- Series shorter than `max_context` are padded

#### `forecast_with_covariates()`

Run inference with exogenous variables (requires `timesfm[xreg]`, which pulls in JAX and
scikit-learn). The model must be compiled with `return_backcast=True`, otherwise the call
raises `ValueError`.

```python
model.compile(timesfm.ForecastConfig(
    max_context=512, max_horizon=128, normalize_inputs=True,
    use_continuous_quantile_head=True, fix_quantile_crossing=True,
    return_backcast=True,  # required for forecast_with_covariates
))

point, quantiles = model.forecast_with_covariates(
    inputs=inputs,
    dynamic_numerical_covariates={"temp": [temp_array1, temp_array2]},
    dynamic_categorical_covariates={"dow": [dow_array1, dow_array2]},
    static_categorical_covariates={"region": ["east", "west"]},
    xreg_mode="xreg + timesfm",
)
# point / quantiles are LISTS with one array per series: (horizon,) and (horizon, 10)
```

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `inputs` | list[np.ndarray] | Target time series |
| `dynamic_numerical_covariates` | dict[str, list[np.ndarray]] | Time-varying numeric features |
| `dynamic_categorical_covariates` | dict[str, list[np.ndarray]] | Time-varying categorical features |
| `static_categorical_covariates` | dict[str, list[str]] | Fixed categorical features per series |
| `static_numerical_covariates` | dict[str, list[float]] | Fixed numeric features per series |
| `xreg_mode` | str | `"xreg + timesfm"` (default): fit a linear model on the target, TimesFM forecasts its residuals. `"timesfm + xreg"`: TimesFM forecasts first, a linear model fits its residuals |
| `ridge` | float | Ridge penalty for the in-context linear model (default 0.0) |

**Note**: Dynamic covariates must have length `context + horizon` for each series; the
forecast horizon is inferred from them and must not exceed `max_horizon`.

---

## `timesfm.ForecastConfig`

Immutable dataclass controlling all forecast behavior.

```python
@dataclasses.dataclass(frozen=True)
class ForecastConfig:
    max_context: int = 0
    max_horizon: int = 0
    normalize_inputs: bool = False
    window_size: int = 0            # reserved for decomposed forecasting (not yet implemented)
    per_core_batch_size: int = 1
    use_continuous_quantile_head: bool = False
    force_flip_invariance: bool = True
    infer_is_positive: bool = True
    fix_quantile_crossing: bool = False
    return_backcast: bool = False
```

The quantile levels (0.1–0.9) and the median index (5) are fixed by the TimesFM 2.5 model
definition, not by `ForecastConfig`.

### Parameter Details

#### `max_context` (int, default=0)

Maximum number of historical time points to use as context.

- **N**: Truncate series to the last N points (rounded up to a multiple of 32); shorter series are left-padded and masked
- **Limit**: `max_context + max_horizon` must be ≤ 16,384 for v2.5
- **Best practice**: Set it explicitly to cover your longest series (or 512–2048 for speed); do not rely on the default of 0

#### `max_horizon` (int, default=0)

Maximum forecast horizon.

- **N**: Forecasts up to N steps (rounded up to a multiple of 128; call `forecast(horizon=M)` with M ≤ N)
- **Best practice**: Set it explicitly to your expected maximum forecast length

#### `normalize_inputs` (bool, default=False)

Whether to z-normalize each series before feeding to the model.

- **True** (RECOMMENDED): Normalizes each series to zero mean, unit variance
- **False**: Raw values are passed directly
- **When False is OK**: Only if your series are already normalized or very close to scale 1.0

#### `per_core_batch_size` (int, default=1)

Number of series processed per device in each batch.

- Increase for throughput, decrease if OOM
- See `references/system_requirements.md` for recommended values by hardware

#### `use_continuous_quantile_head` (bool, default=False)

Use the 30M-parameter continuous quantile head for better interval calibration.

- **True** (recommended): More accurate prediction intervals, especially for longer horizons; only valid for `max_horizon ≤ 1024`
- **False**: Uses fixed quantile buckets (faster but less accurate intervals)

#### `force_flip_invariance` (bool, default=True)

Ensures the model satisfies `f(-x) = -f(x)`.

- **True** (RECOMMENDED): Mathematical consistency — forecasts are invariant to sign flip
- **False**: Slightly faster but may produce asymmetric forecasts

#### `infer_is_positive` (bool, default=True)

Automatically detect if all input values are positive and clamp forecasts ≥ 0.

- **True**: Safe for sales, demand, counts, prices, volumes
- **False**: Required for temperature, returns, PnL, any series that can be negative

#### `fix_quantile_crossing` (bool, default=False)

Post-process quantiles to ensure monotonicity (q10 ≤ q20 ≤ ... ≤ q90).

- **True** (RECOMMENDED): Guarantees well-ordered quantiles
- **False**: Slightly faster but quantiles may occasionally cross

#### `return_backcast` (bool, default=False)

Return the model's reconstruction of the input (backcast) in addition to forecast.

- **True**: Required by `forecast_with_covariates()`; plain `forecast()` outputs then include the backcast steps before the horizon
- **False**: Only return forecast

---

## Available Model Checkpoints

| Model ID | Version | Params | Backend | Context |
| -------- | ------- | ------ | ------- | ------- |
| `google/timesfm-3.0-pytorch` | 3.0 (non-commercial weights) | ~330M | PyTorch / MLX (`timesfm3`) | 15,360 |
| `google/timesfm-2.5-200m-pytorch` | 2.5 | 200M | PyTorch | 16,384 |
| `google/timesfm-2.5-200m-flax` | 2.5 | 200M | JAX/Flax | 16,384 |
| `google/timesfm-2.5-200m-transformers` | 2.5 | 200M | 🤗 Transformers (`TimesFm2_5ModelForPrediction`) | 16,384 |
| `google/timesfm-2.0-500m-pytorch` | 2.0 | 500M | PyTorch | 2,048 |
| `google/timesfm-2.0-500m-jax` | 2.0 | 500M | JAX | 2,048 |
| `google/timesfm-1.0-200m-pytorch` | 1.0 | 200M | PyTorch | 2,048 |
| `google/timesfm-1.0-200m` | 1.0 | 200M | JAX | 2,048 |

---

## Output Shape Reference

| Output | Shape | Description |
| ------ | ----- | ----------- |
| `point_forecast` | `(B, H)` | Median forecast for B series, H steps |
| `quantile_forecast` | `(B, H, 10)` | Full quantile distribution |
| `quantile_forecast[:,:,0]` | `(B, H)` | Mean |
| `quantile_forecast[:,:,1]` | `(B, H)` | 10th percentile |
| `quantile_forecast[:,:,5]` | `(B, H)` | 50th percentile (= point_forecast) |
| `quantile_forecast[:,:,9]` | `(B, H)` | 90th percentile |

Where `B` = batch size (number of input series), `H` = forecast horizon.

---

## Error Handling

| Error | Cause | Fix |
| ----- | ----- | --- |
| `RuntimeError: Model is not compiled` | Called `forecast()` before `compile()` | Call `model.compile(ForecastConfig(...))` first |
| `torch.cuda.OutOfMemoryError` | Batch too large for GPU | Reduce `per_core_batch_size` |
| `ValueError: inputs must be list` | Passed array instead of list | Wrap in list: `[array]` |
| `HfHubHTTPError` | Download failed | Check internet, set `HF_HOME` to writable dir |
| `ValueError: ... return_backcast must be set to True` | `forecast_with_covariates()` on a model compiled without it | Recompile with `ForecastConfig(..., return_backcast=True)` |
| `AttributeError: module 'timesfm' has no attribute 'TimesFmHparams'` | 1.x-era code with timesfm ≥ 2.0 | Port to `TimesFM_2p5_200M_torch` (or pin `timesfm==1.3.0` for old checkpoints) |

---

## TimesFM 3.0 API (`timesfm3`)

Installed with `timesfm>=3.0` (`uv pip install "timesfm[torch]"`, or `timesfm[mlx]` for the
MLX backend on Apple silicon). The pretrained weights (`google/timesfm-3.0-pytorch`) are
distributed under `timesfm-non-commercial-license-v1.0`: non-commercial, non-production use
only. The source code stays Apache-2.0.

```python
import numpy as np
from timesfm3 import TimesFM3Forecaster   # PyTorch backend; timesfm3.mlx has the same interface

forecaster = TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device="cuda")  # or "cpu"

# Univariate
out = forecaster.predict(np.asarray(series, dtype=np.float32), horizon=24, return_quantiles=True)
out.forecast   # (24,)    median forecast
out.quantiles  # (24, 9)  deciles q10..q90 — index 4 is the median; there is NO mean column

# Batch of series with different lengths (returns a generator of ForecastOutput)
outs = list(forecaster.predict_batch([s1, s2], horizon=12, return_quantiles=True))

# Multivariate target (num_variates, context) with covariates
out = forecaster.predict(
    target,                                   # (V, T)
    horizon=32,
    past_only_covariates=past_only,           # (C1, T)
    past_future_covariates=past_future,       # (C2, T + horizon) — known future values
    return_quantiles=True,
)
out.forecast   # (V, 32);  out.quantiles  # (V, 32, 9)
```

| Parameter | Default | Meaning |
| --------- | ------- | ------- |
| `horizon` | — | Steps to forecast (longer horizons are stitched from 64-step output patches) |
| `return_quantiles` | False | Also return the 9 deciles |
| `make_positive` | False | Clamp forecasts at zero for non-negative series |
| `use_symmetric_averaging` | False | Average with the sign-flipped forecast |
| `use_znorm` | False | Z-normalise inputs before decoding |
| `padding_mode` | `"none"` | `"none"` or `"edge"` |

Contexts longer than 15,360 steps are truncated to the most recent points.
`TimesFM3Evaluator(ModelConfig(checkpoint_path=..., per_core_batch_size=..., device=...))`
exposes the same `predict_batch` for benchmark-style evaluation.
