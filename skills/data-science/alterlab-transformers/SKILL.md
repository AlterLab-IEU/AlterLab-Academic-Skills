---
name: alterlab-transformers
description: Loads, runs, and fine-tunes pretrained models with Hugging Face Transformers v5 (PyTorch-only) — pipeline() inference for chat-model text generation, text classification, NER, zero-shot, speech recognition, image classification, object detection, and image-text-to-text VLMs; AutoModel/AutoTokenizer loading with dtype, device_map and bitsandbytes quantization; generate() decoding control; and Trainer fine-tuning with optional PEFT/LoRA. Use when running inference with a Hugging Face Hub checkpoint, fine-tuning BERT/ModernBERT/Qwen-style models on a custom labelled dataset, controlling generation (sampling, beam search, streaming, chat templates), or porting v4 code (torch_dtype, removed summarization/translation/QA pipelines, TF/Flax) to v5. Part of the AlterLab Academic Skills suite.
license: Apache-2.0
allowed-tools: Read Write Edit Bash(python:*) Bash(uv:*)
compatibility: No API key required for public models. Runs locally via `uv run python`; requires transformers >= 5.0 (current 5.17 as of 2026-09, Python >= 3.10) and PyTorch — v5 removed TensorFlow and Flax support. A Hugging Face token (HF_TOKEN) is needed only for gated/private models.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Transformers

## Overview

Hugging Face Transformers loads pretrained checkpoints from the Hub for NLP, vision, audio, and multimodal tasks, runs inference through `pipeline()` or the `Auto*` classes, and fine-tunes them with `Trainer`. This skill targets **transformers v5** (≥ 5.0; current 5.17.0 as of 2026-09). v5 is PyTorch-only and changes several v4 idioms, so check "v5 changes that break v4 code" below before reusing older snippets from papers, blogs, or model cards.

## When to Use This Skill

Use this skill when the user wants to:
- Run quick inference with a Hub checkpoint via `pipeline()` — text classification, NER, zero-shot classification, text generation with a chat model, speech recognition, image classification/detection, or image-text-to-text with a VLM.
- Load a model plus tokenizer/processor with explicit `dtype`, `device_map`, attention backend, or 4/8-bit quantization.
- Control decoding in `model.generate()` (greedy, sampling, beam search, streaming, chat templates).
- Fine-tune an encoder or decoder on a custom labelled dataset with `Trainer`, optionally with LoRA via `peft`.
- Port v4-era code (`torch_dtype=`, `load_in_8bit=`, removed pipelines, TF/Flax models) to v5.

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Classical ML on tabular features (random forests, preprocessing pipelines, CV grid search) | `alterlab-scikit-learn` |
| Structuring a custom PyTorch architecture's training loop, multi-GPU strategy, and checkpointing with a LightningModule | `alterlab-pytorch-lightning` |
| Topic models, embeddings, or text classifiers as a social-science measurement design (validity, BERTopic, dictionaries) | `alterlab-text-as-data` |
| Protein language models (ESM3 / ESM C embeddings, protein design) | `alterlab-esm` |
| Zero-shot time-series forecasting with a pretrained foundation model | `alterlab-timesfm` |

## Installation

```bash
uv pip install "transformers>=5" torch accelerate datasets
```

- Vision: add `pillow` and `torchvision` (the default image-processor backend; `timm` only for timm-backed models).
- Audio: add `librosa soundfile`.
- LoRA / quantization: `peft`, `bitsandbytes` (CUDA). Metrics: `evaluate` or plain scikit-learn metrics.

## Authentication

Gated or private models need a Hub token. Either log in once:

```python
from huggingface_hub import login
login()  # or run `hf auth login` in a shell (huggingface-cli is deprecated)
```

or export the variable the Hub client reads:

```bash
export HF_TOKEN="your_token_here"
```

Tokens: https://huggingface.co/settings/tokens. Pass `token=` (not the removed `use_auth_token=`) when you need it explicitly.

## Quick Start

```python
from transformers import pipeline

# Text generation with a small open chat model (CPU-friendly; add device_map="auto" on GPU)
generator = pipeline("text-generation", model="Qwen/Qwen3-0.6B")
messages = [{"role": "user", "content": "Explain p-hacking in two sentences."}]
out = generator(
    messages,
    max_new_tokens=128,
    tokenizer_encode_kwargs={"enable_thinking": False},  # Qwen3 chat-template switch; omit for other models
)
print(out[0]["generated_text"][-1]["content"])

# Text classification — pin the checkpoint; task defaults change between releases
classifier = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
classifier(["This movie was excellent!", "Terrible pacing."])

# Zero-shot classification
zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
zero_shot("The grant covers two postdoc salaries.", candidate_labels=["funding", "teaching", "ethics"])
```

Use `max_new_tokens` (tokens to generate) rather than `max_length` (prompt + output, and in the text-generation pipeline it also feeds tokenizer truncation). Summarization, translation, and question answering no longer have dedicated pipelines in v5 — prompt a chat model as above.

## v5 Changes That Break v4 Code

| v4 idiom | v5 replacement |
|----------|----------------|
| `torch_dtype=torch.float16` | `dtype=torch.float16` (`torch_dtype` only warns). Default is now `dtype="auto"` — the checkpoint's dtype, often bf16 — not float32 |
| `TFAutoModel…` / `FlaxAutoModel…`, `framework="tf"`, `return_tensors="tf"` | Removed; PyTorch only (`return_tensors` accepts `"pt"`, `"np"`, `"mlx"`) |
| `load_in_8bit=True` / `load_in_4bit=True` | `quantization_config=BitsAndBytesConfig(...)` |
| `pipeline("summarization" / "translation_xx_to_yy" / "text2text-generation" / "question-answering")` | Removed — `pipeline("text-generation")` with a chat model and an instruction prompt |
| `pipeline("image-to-text" / "visual-question-answering")` | `pipeline("image-text-to-text")` with a VLM, e.g. `Qwen/Qwen3-VL-2B-Instruct` |
| `AutoModelForVision2Seq`, `AutoModelWithLMHead` | `AutoModelForImageTextToText`; `AutoModelForCausalLM` / `AutoModelForMaskedLM` / `AutoModelForSeq2SeqLM` |
| `apply_chat_template(..., tokenize=True)` returned a tensor of ids | Returns a `BatchEncoding` (`input_ids`, `attention_mask`) → `model.generate(**inputs)` |
| Slow vs fast tokenizers, `use_fast=` | One tokenizer per model on the 🤗 tokenizers backend; `AutoTokenizer` ignores `use_fast` |
| `batch_decode`, `encode_plus`, `additional_special_tokens` | `decode` handles batches, `tokenizer(...)`, `extra_special_tokens` (old names kept for backward compatibility) |
| `penalty_alpha` (contrastive search), `force_words_ids` / `constraints`, group beam search, DoLa | Moved to Hub `custom_generate` repos — e.g. `custom_generate="transformers-community/contrastive-search", trust_remote_code=True` |
| `TrainingArguments(logging_dir=..., warmup_ratio=...)` | Both removed: set the `TENSORBOARD_LOGGING_DIR` env var; `warmup_steps=0.1` (a float < 1 is a ratio) |
| `Trainer(tokenizer=...)` | `Trainer(processing_class=...)`; `report_to` now defaults to `"none"` |
| `save_pretrained(safe_serialization=False)`, `use_auth_token=` | Always safetensors; `token=` |
| `TRANSFORMERS_CACHE`, `low_cpu_mem_usage=True` | `HF_HOME` / `HF_HUB_CACHE`; low-memory loading is always on (flag ignored) |

Source: the official [v5 migration guide](https://github.com/huggingface/transformers/blob/main/MIGRATION_GUIDE_V5.md), cross-checked against the 5.17.0 release.

## Core Capabilities

### 1. Pipelines for Quick Inference

One call covers tokenization, the forward pass, and post-processing for text classification, NER, zero-shot, fill-mask, text generation, ASR, audio classification, image classification/segmentation, object detection, depth estimation, and image-text-to-text. Use for prototyping and batch inference without custom preprocessing. See `references/pipelines.md`.

### 2. Model Loading and Management

`from_pretrained` with `dtype`, `device_map`, `attn_implementation` (SDPA by default), and `quantization_config`; saving, Hub upload, and ONNX export options. See `references/models.md`.

### 3. Text Generation

`generate()` with greedy, sampling (temperature/top-k/top-p), and beam search; chat templates, streaming, and static caches. See `references/generation.md`.

### 4. Training and Fine-Tuning

`Trainer` + `TrainingArguments` with mixed precision, gradient accumulation/checkpointing, callbacks, hyperparameter search, and LoRA via `peft`. See `references/training.md`.

### 5. Tokenization

Padding, truncation, special tokens, offsets, and chat templates. See `references/tokenizers.md`.

## Common Patterns

### Pattern 1: Simple Inference

```python
pipe = pipeline("task-name", model="org/model-id")
output = pipe(input_data)
```

### Pattern 2: Explicit Model + Tokenizer (chat model)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto", device_map="auto")

messages = [{"role": "user", "content": "State the central limit theorem in one sentence."}]
inputs = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    return_tensors="pt",
    enable_thinking=False,  # Qwen3-specific template variable
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=128)
new_tokens = outputs[0, inputs["input_ids"].shape[1]:]
print(tokenizer.decode(new_tokens, skip_special_tokens=True))
```

### Pattern 3: Fine-Tuning a Classifier

```python
from datasets import load_dataset
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          DataCollatorWithPadding, Trainer, TrainingArguments)

model_id = "google-bert/bert-base-uncased"  # or answerdotai/ModernBERT-base
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSequenceClassification.from_pretrained(model_id, num_labels=5)

ds = load_dataset("Yelp/yelp_review_full")
ds = ds.map(lambda b: tokenizer(b["text"], truncation=True), batched=True)

args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    eval_strategy="epoch",
    warmup_steps=0.1,          # ratio of total steps
    report_to="tensorboard",   # default is "none" in v5
)
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=ds["train"],
    eval_dataset=ds["test"],
    processing_class=tokenizer,
    data_collator=DataCollatorWithPadding(tokenizer),
)
trainer.train()
```

## Practical Notes

- Pin model IDs (and ideally `revision=`) in research code: pipeline defaults and Hub repos change, which silently changes results.
- Report the exact checkpoint, transformers version, decoding parameters, and seed (`transformers.set_seed`) when generated text or fine-tuned metrics appear in a paper.
- Check the model card's license and gating terms before redistributing weights or outputs.

## Reference Documentation

- `references/pipelines.md` — supported v5 tasks, parameters, batching, and removed pipelines
- `references/models.md` — loading, dtype/device/attention/quantization, saving, export
- `references/generation.md` — decoding strategies, chat templates, streaming, caches
- `references/training.md` — `Trainer` workflow, `TrainingArguments`, PEFT, tuning
- `references/tokenizers.md` — tokenization, special tokens, chat templates

Part of the AlterLab Academic Skills suite.
