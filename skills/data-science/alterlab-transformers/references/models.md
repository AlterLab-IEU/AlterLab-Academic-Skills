# Model Loading and Management (transformers v5)

## Overview

`from_pretrained` detects the architecture from the checkpoint's config, downloads weights (safetensors) from the Hub or reads them from disk, and places them on devices according to `device_map`. v5 is PyTorch-only.

## Loading Models

### AutoModel Classes

```python
from transformers import (AutoModel, AutoModelForCausalLM, AutoModelForMaskedLM,
                          AutoModelForSeq2SeqLM, AutoModelForSequenceClassification)

# Base model (no task head) — hidden states / embeddings
model = AutoModel.from_pretrained("google-bert/bert-base-uncased")

# Sequence classification (the head is newly initialized unless the checkpoint has one)
model = AutoModelForSequenceClassification.from_pretrained("distilbert/distilbert-base-uncased", num_labels=2)

# Causal language modeling (decoder-only LLMs)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B")

# Masked language modeling (BERT-style)
model = AutoModelForMaskedLM.from_pretrained("answerdotai/ModernBERT-base")

# Sequence-to-sequence (T5/BART-style encoder-decoders)
model = AutoModelForSeq2SeqLM.from_pretrained("google-t5/t5-small")
```

### Common AutoModel Classes

**NLP:**
- `AutoModelForSequenceClassification`: text classification, sentiment
- `AutoModelForTokenClassification`: NER, POS tagging
- `AutoModelForQuestionAnswering`: extractive QA heads (the QA *pipeline* was removed in v5, the model class was not)
- `AutoModelForCausalLM`: text generation (Qwen, Llama, Gemma, SmolLM, …)
- `AutoModelForMaskedLM`: masked language modeling (BERT, ModernBERT)
- `AutoModelForSeq2SeqLM`: encoder-decoder translation/summarization (T5, BART)

**Vision:**
- `AutoModelForImageClassification`, `AutoModelForObjectDetection`, `AutoModelForImageSegmentation`

**Audio:**
- `AutoModelForAudioClassification`, `AutoModelForSpeechSeq2Seq` (Whisper), `AutoModelForCTC`

**Multimodal:**
- `AutoModelForImageTextToText`: vision-language chat models (replaces the removed `AutoModelForVision2Seq`)
- `AutoProcessor`: loads the matching tokenizer + image/audio processor bundle

## Loading Parameters

### Basic Parameters

**pretrained_model_name_or_path**: Hub ID or local directory
```python
model = AutoModel.from_pretrained("google-bert/bert-base-uncased")  # from the Hub
model = AutoModel.from_pretrained("./local/model/path")             # from disk
```

**revision**: pin a branch, tag, or commit for reproducibility
```python
model = AutoModel.from_pretrained("org/model-id", revision="a1b2c3d")
```

**num_labels**: output size of a new classification head
```python
model = AutoModelForSequenceClassification.from_pretrained("google-bert/bert-base-uncased", num_labels=3)
```

**cache_dir**: custom cache location for this call (globally, set `HF_HOME` or `HF_HUB_CACHE`)
```python
model = AutoModel.from_pretrained("org/model-id", cache_dir="./my_cache")
```

**token**: Hub token for gated/private repos (the old `use_auth_token=` was removed)

### Device Management

**device_map**: automatic placement for large models (requires `accelerate`)
```python
# Spread across available GPUs, then CPU
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-8B", device_map="auto")

# Fill devices in order
model = AutoModelForCausalLM.from_pretrained("org/model-id", device_map="sequential")

# Custom map (module names depend on the architecture — inspect print(model) first)
device_map = {
    "model.embed_tokens": 0,
    "model.layers.0": 0,
    "model.layers.1": 1,
    "lm_head": "cpu",
}
model = AutoModelForCausalLM.from_pretrained("org/model-id", device_map=device_map)
```

Manual placement:
```python
import torch
model = AutoModel.from_pretrained("org/model-id")
model.to("cuda" if torch.cuda.is_available() else "cpu")
```

### Precision Control

**dtype** (the old `torch_dtype=` keyword still works but warns). In v5 the default is `dtype="auto"`, i.e. the dtype stored in the checkpoint (bf16 for most recent LLMs) rather than float32.
```python
import torch

model = AutoModel.from_pretrained("org/model-id", dtype=torch.bfloat16)  # better range than fp16
model = AutoModel.from_pretrained("org/model-id", dtype=torch.float16)
model = AutoModel.from_pretrained("org/model-id", dtype=torch.float32)  # force full precision (e.g. CPU numerics)
```

### Attention Implementation

**attn_implementation**: PyTorch SDPA is used by default where the architecture supports it, falling back to eager.
```python
# Flash Attention 2 (CUDA; requires the flash-attn package and fp16/bf16 weights)
model = AutoModel.from_pretrained("org/model-id", attn_implementation="flash_attention_2", dtype=torch.bfloat16)

# Eager — required to return attention weights (SDPA does not support output_attentions=True)
model = AutoModel.from_pretrained("org/model-id", attn_implementation="eager")
```

### Memory Optimization

Low-memory loading is the only loading path in v5, so the old `low_cpu_mem_usage=True` flag is silently ignored.

**Quantization** (bitsandbytes, CUDA): pass a `BitsAndBytesConfig` via `quantization_config`. The direct `load_in_8bit=` / `load_in_4bit=` keyword arguments were removed in v5.

8-bit:
```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

model = AutoModelForCausalLM.from_pretrained(
    "org/model-id",
    quantization_config=BitsAndBytesConfig(load_in_8bit=True),
    device_map="auto",
)
```

4-bit (NF4 + double quantization):
```python
import torch
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
model = AutoModelForCausalLM.from_pretrained(
    "org/model-id",
    quantization_config=quantization_config,
    device_map="auto",
)
```

Pre-quantized checkpoints (GPTQ, AWQ, FP8, …) load with plain `from_pretrained`; their config carries the quantization settings.

## Model Configuration

### Loading with Custom Config

```python
from transformers import AutoConfig, AutoModel

config = AutoConfig.from_pretrained("google-bert/bert-base-uncased")
config.hidden_dropout_prob = 0.2
config.attention_probs_dropout_prob = 0.2

model = AutoModel.from_pretrained("google-bert/bert-base-uncased", config=config)
```

Or override attributes inline: `AutoModel.from_pretrained("org/model-id", hidden_dropout_prob=0.2)`.

v5 config notes: RoPE settings live in `config.rope_parameters` (not `config.rope_theta`); vision-language configs are nested (`config.text_config.vocab_size`); generation settings live in `model.generation_config`, not the model config.

### Initializing from Config Only

```python
from transformers import AutoConfig, AutoModelForCausalLM

config = AutoConfig.from_pretrained("Qwen/Qwen3-0.6B")
model = AutoModelForCausalLM.from_config(config)  # random weights — for pre-training from scratch
```

## Model Modes

`from_pretrained` returns the model in **evaluation mode** (`model.training == False`, dropout off). Switch explicitly when writing your own loop:

```python
model = AutoModel.from_pretrained("org/model-id")
print(model.training)  # False

model.train()  # enable dropout for fine-tuning in a custom loop
model.eval()   # back to deterministic inference
```

`Trainer` toggles modes for you. For inference, also wrap forward passes in `torch.inference_mode()` (or `torch.no_grad()`) to skip gradient tracking. Models built with `from_config` start in training mode, like any fresh `nn.Module`.

## Saving Models

### Save Locally

```python
model.save_pretrained("./my_model")
tokenizer.save_pretrained("./my_model")  # keep tokenizer/processor with the weights
```

This writes `config.json`, `generation_config.json` (generative models), and `model.safetensors` (sharded above the 50 GB default `max_shard_size`). v5 always saves safetensors; the `safe_serialization` argument was removed.

### Save to the Hugging Face Hub

```python
model.push_to_hub("username/model-name")
model.push_to_hub("username/model-name", commit_message="Update model", private=True)
```

In v5, `push_to_hub` arguments other than `repo_id` are keyword-only.

## Model Inspection

```python
total_params = model.num_parameters()
trainable_params = model.num_parameters(only_trainable=True)
print(f"Total: {total_params:,}  Trainable: {trainable_params:,}")

memory_mb = model.get_memory_footprint() / 1024**2
print(f"Memory: {memory_mb:.2f} MB")

print(model)          # module tree
print(model.config)   # architecture hyperparameters
```

## Forward Pass

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilbert/distilbert-base-uncased-finetuned-sst-2-english")
model = AutoModelForSequenceClassification.from_pretrained("distilbert/distilbert-base-uncased-finetuned-sst-2-english")

inputs = tokenizer("Sample text", return_tensors="pt")
with torch.inference_mode():
    logits = model(**inputs).logits
predictions = logits.argmax(dim=-1)
labels = [model.config.id2label[i] for i in predictions.tolist()]
```

## Export

### ONNX

- **Optimum**: `optimum-onnx` (0.1.0, the current release as of 2026-09) still pins `transformers<4.58`, so it cannot share an environment with transformers v5. Use a separate v4 environment if you need `ORTModelFor…` classes.
- **In-library (v5)**: recent v5 releases ship `transformers.exporters` with an `OnnxExporter` built on `torch.export` + `torch.onnx` (needs `onnx` and `onnxscript`):

```python
from transformers.exporters.exporter_onnx import OnnxConfig, OnnxExporter

inputs = tokenizer("Sample text", return_tensors="pt")
exporter = OnnxExporter()
exporter.export(model, inputs, config=OnnxConfig(output_path="model.onnx"))
```

This module is new; check the installed version's docstrings before relying on it in a pipeline. `torch.onnx.export(..., dynamo=True)` is the lower-level fallback.

## Best Practices

1. **Use Auto classes** for architecture detection.
2. **Pin `revision=`** for any result you will publish.
3. **Set `dtype` deliberately**: bf16/fp16 on GPU; float32 when you need CPU numerical parity.
4. **Use `device_map="auto"`** for models larger than one device.
5. **Consider quantization** for memory-constrained inference (validate accuracy afterwards).
6. **Keep tokenizer/processor with the weights** when saving.
7. **Cache location**: set `HF_HOME` (the `TRANSFORMERS_CACHE` variable was removed in v5).

## Common Issues

**CUDA out of memory:**
```python
import torch
from transformers import AutoModel, BitsAndBytesConfig

model = AutoModel.from_pretrained("org/model-id", dtype=torch.bfloat16)          # lower precision
model = AutoModel.from_pretrained(                                               # or quantize
    "org/model-id",
    quantization_config=BitsAndBytesConfig(load_in_8bit=True),
    device_map="auto",
)
model = AutoModel.from_pretrained("org/model-id", device_map="cpu")              # or stay on CPU
```

**Unexpected dtype after upgrading to v5:** the default changed from float32 to `"auto"`; pass `dtype=torch.float32` to restore v4 behaviour.

**Model not found / 401:**
```python
# Verify the model ID on https://huggingface.co and accept the license on gated repos
from huggingface_hub import login
login()
```
