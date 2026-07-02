# Python API Usage

Programmatic control of HypoGeniC generation and inference — the real init/update loop and inference registry, verified against the library's `examples/` scripts.

For programmatic control, copy and adapt the scripts under `examples/`. The library is **not** a one-call fluent API — generation runs as an explicit init/update loop over the algorithm classes, and inference runs through the inference registry. The real building blocks (verified against `examples/generation.py` and `examples/inference.py`):

```python
from hypogenic.tasks import BaseTask
from hypogenic.prompt import BasePrompt
from hypogenic.LLM_wrapper import llm_wrapper_register
from hypogenic.extract_label import extract_label_register
from hypogenic.algorithm.generation import DefaultGeneration
from hypogenic.algorithm.inference import DefaultInference, inference_register
from hypogenic.algorithm.replace import DefaultReplace
from hypogenic.algorithm.update import DefaultUpdate

# 1. Task: pass a custom extract_label, or reuse a registered one
#    (e.g. "shoe", "hotel_reviews", "retweet", "headline_binary").
task = BaseTask(
    "./data/your_task/config.yaml",
    extract_label=my_extract_label,         # or None + from_register=...
    from_register=extract_label_register,
)

# 2. Build the LLM backend via the registry (API or local model)
api = llm_wrapper_register.build(model_type)(model=model_name, path_name=model_path)
prompt_class = BasePrompt(task)

# 3. Generation pipeline: inference -> generation -> update loop
inference_class  = DefaultInference(api, prompt_class, train_data, task)
generation_class = DefaultGeneration(api, prompt_class, inference_class, task)
update_class     = DefaultUpdate(
    generation_class, inference_class, DefaultReplace(max_num_hypotheses), save_path
)
hypotheses_bank = update_class.update(
    current_epoch=epoch, hypotheses_bank=hyp_bank,
    current_seed=seed, cache_seed=cache_seed,
)
```

For **HypoRefine / Union** methods (literature + data), adapt `examples/union_generation.py` instead — it produces three banks: HypoRefine (integrated), literature-only, and Literature ∪ HypoRefine.

### Inference

```python
# Load a saved hypothesis bank, then run inference through the registry
inference_class = inference_register.build(inference_type)(
    api, prompt_class, train_data, task
)
pred_list, label_list = inference_class.run_inference_final(test_data, hyp_bank)
# evaluate with get_results(pred_list, label_list)  -> accuracy / F1
```

`inference_type` selects the strategy, e.g. `default`, `one_step_adaptive`, `filter_and_weight`, `two_step_adaptive`, `upperbound` (see `examples/multi_hyp_inference.py` for multi-hypothesis runs).

### Custom Label Extraction

The `extract_label()` function is critical for parsing LLM outputs. Implement it based on your task:

```python
def extract_label(llm_output: str) -> str:
    """Extract predicted label from LLM inference text.
    
    Default behavior: searches for 'final answer:\s+(.*)' pattern.
    Customize for your domain-specific output format.
    """
    import re
    match = re.search(r'final answer:\s+(.*)', llm_output, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return llm_output.strip()
```

**Important:** Extracted labels must match the format of `label` values in your dataset for correct accuracy calculation.
