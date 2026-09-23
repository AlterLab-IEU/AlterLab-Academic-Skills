# Text Generation (transformers v5)

## Overview

Generate text with `model.generate()`. Decoding strategy and parameters (length, temperature, top-k/top-p, beams, repetition controls) shape output quality and diversity. Examples use `Qwen/Qwen3-0.6B`, a small open chat model that runs on CPU; swap in any `AutoModelForCausalLM` checkpoint.

## Basic Generation

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto", device_map="auto")

inputs = tokenizer("Once upon a time", return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=50)

# Decode only the newly generated tokens
text = tokenizer.decode(outputs[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(text)
```

Pass `**inputs` (not just `input_ids`) so the attention mask reaches `generate()`.

## Generation Strategies

### Greedy Decoding

Highest-probability token at each step (deterministic):

```python
outputs = model.generate(**inputs, max_new_tokens=50, do_sample=False)
```

**Use for**: extraction, short factual answers, reproducible runs. Note that many chat checkpoints ship a `generation_config.json` that turns sampling on by default, so pass `do_sample=False` explicitly when you need determinism. Some reasoning models (e.g. Qwen3 in thinking mode) degrade or loop under greedy decoding — follow the model card's recommended settings.

### Sampling

```python
outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    do_sample=True,
    temperature=0.7,
    top_k=50,
    top_p=0.95,
)
```

**Use for**: open-ended or diverse outputs. `min_p` (e.g. `min_p=0.05`) is an alternative truncation rule.

### Beam Search

```python
outputs = model.generate(**inputs, max_new_tokens=50, num_beams=5, early_stopping=True)
```

**Use for**: translation/summarization with encoder-decoder models, where a high-likelihood output matters.

### Strategies Moved to the Hub in v5

Contrastive search (`penalty_alpha`), constrained beam search (`force_words_ids`, `constraints`), group/diverse beam search (`num_beam_groups`), and DoLa now live in Hub `custom_generate` repositories. Calling them the v4 way raises an error unless you opt in to running the repository's code:

```python
outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    penalty_alpha=0.6,
    top_k=4,
    custom_generate="transformers-community/contrastive-search",
    trust_remote_code=True,  # executes custom_generate/generate.py from that repo — read it first
)
```

Other repos: `transformers-community/constrained-beam-search`, `transformers-community/group-beam-search`, `transformers-community/dola`.

## Key Parameters

### Length Control

- `max_new_tokens`: maximum tokens to generate — prefer this.
- `max_length`: maximum total length (prompt + output); easy to exhaust with long prompts.
- `min_new_tokens`: force at least N new tokens.

### Temperature

Only applies with `do_sample=True`:

```python
temperature=1.0   # model distribution unchanged
temperature=0.7   # more focused
temperature=1.3   # more random
```

### Top-K / Top-P

```python
do_sample=True
top_k=50     # sample from the 50 most likely tokens
top_p=0.95   # sample from the smallest set with ≥95% cumulative probability
```

### Repetition Controls

```python
repetition_penalty=1.2   # 1.0 = none; >1 discourages repeats
no_repeat_ngram_size=3   # forbid repeating any 3-gram
```

### Output Control

```python
outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    do_sample=True,
    num_return_sequences=3,  # three samples per prompt
)
```

- `pad_token_id=tokenizer.eos_token_id` — silences the warning for models without a pad token.
- `eos_token_id` — stop on a specific token (or a list of ids); `stop_strings=["\n\n"]` (with `tokenizer=tokenizer`) stops on text.

## Advanced Features

### Batch Generation

Decoder-only models must be **left-padded** for batched generation; right padding corrupts the continuation.

```python
tokenizer = AutoTokenizer.from_pretrained(model_id, padding_side="left")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

prompts = ["Hello, my name is", "Once upon a time"]
inputs = tokenizer(prompts, return_tensors="pt", padding=True).to(model.device)
outputs = model.generate(**inputs, max_new_tokens=50)

texts = tokenizer.decode(outputs[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)  # v5: decode handles batches
for i, text in enumerate(texts):
    print(f"Prompt {i}: {text}\n")
```

### Streaming Generation

```python
from threading import Thread
from transformers import TextIteratorStreamer

streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
generation_kwargs = dict(**inputs, streamer=streamer, max_new_tokens=100)

thread = Thread(target=model.generate, kwargs=generation_kwargs)
thread.start()
for text in streamer:
    print(text, end="", flush=True)
thread.join()
```

For simple console output, `TextStreamer(tokenizer, skip_prompt=True)` passed as `streamer=` needs no thread.

### Blocking Tokens

```python
bad_words_ids = tokenizer(["offensive", "inappropriate"], add_special_tokens=False).input_ids
outputs = model.generate(**inputs, max_new_tokens=50, bad_words_ids=bad_words_ids)
```

To *force* words into the output, use the `transformers-community/constrained-beam-search` repo shown above.

### Generation Config

```python
from transformers import GenerationConfig

generation_config = GenerationConfig(
    max_new_tokens=100,
    do_sample=True,
    temperature=0.7,
    top_k=50,
    top_p=0.95,
)
generation_config.save_pretrained("./my_generation_config")

generation_config = GenerationConfig.from_pretrained("./my_generation_config")
outputs = model.generate(**inputs, generation_config=generation_config)
```

The model's defaults live in `model.generation_config` (in v5 they are no longer read from `model.config`). Inspect it to see what a checkpoint does by default.

## Model-Specific Generation

### Chat Models

In v5 `apply_chat_template` returns a `BatchEncoding` (`input_ids` + `attention_mask`) by default, so unpack it into `generate()`:

```python
messages = [
    {"role": "system", "content": "You are a concise research assistant."},
    {"role": "user", "content": "What is the capital of France?"},
]

inputs = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,  # append the assistant header so the model answers
    return_tensors="pt",
    enable_thinking=False,       # Qwen3 template variable; omit for other models
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=100)
response = tokenizer.decode(outputs[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
```

Use `tokenize=False` to inspect the rendered prompt string. Extra keyword arguments (like `enable_thinking`) are passed to the model's chat template, so they are model-specific.

### Encoder-Decoder Models

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

model = AutoModelForSeq2SeqLM.from_pretrained("google-t5/t5-small")
tokenizer = AutoTokenizer.from_pretrained("google-t5/t5-small")

# T5 uses task prefixes
inputs = tokenizer("translate English to French: Hello, how are you?", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=50, num_beams=4)
translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## Optimization

### KV Cache

Caching is on by default (`use_cache=True`); in v5 the default cache class is chosen by the model.

### Static Cache

A fixed-size cache enables `torch.compile` speedups for repeated generation:

```python
outputs = model.generate(**inputs, max_new_tokens=100, cache_implementation="static")
```

Or build one explicitly: `StaticCache(config=model.config, max_cache_len=1024)` passed as `past_key_values=`.

### Attention Implementation

SDPA is the default; Flash Attention 2 can be faster on supported CUDA GPUs:

```python
model = AutoModelForCausalLM.from_pretrained(
    "org/model-id", attn_implementation="flash_attention_2", dtype=torch.bfloat16
)
```

### Assisted (Speculative) Decoding

A small draft model sharing the tokenizer can speed up a large one:

```python
assistant = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B", dtype="auto", device_map="auto")
outputs = model.generate(**inputs, assistant_model=assistant, max_new_tokens=100)
```

## Generation Recipes

### Creative Writing

```python
outputs = model.generate(
    **inputs, max_new_tokens=200, do_sample=True,
    temperature=0.8, top_k=50, top_p=0.95, repetition_penalty=1.2,
)
```

### Factual / Reproducible Generation

```python
outputs = model.generate(**inputs, max_new_tokens=100, do_sample=False, repetition_penalty=1.1)
```

### Several Diverse Candidates

```python
outputs = model.generate(
    **inputs, max_new_tokens=100, do_sample=True,
    temperature=1.0, top_p=0.95, num_return_sequences=5,
)
```

### Translation / Summarization (encoder-decoder)

```python
outputs = model.generate(
    **inputs, max_new_tokens=100, num_beams=5, early_stopping=True, no_repeat_ngram_size=3,
)
```

## Common Issues

**Repetitive output:** raise `repetition_penalty` (1.1–1.3), set `no_repeat_ngram_size` (2–3), or switch from greedy to sampling.

**Poor quality:** use a larger or instruction-tuned checkpoint, apply its chat template, and follow the model card's recommended decoding settings.

**Too deterministic:** set `do_sample=True` and raise `temperature` (0.7–1.0).

**Garbled batched outputs:** left-pad (`padding_side="left"`) and pass the attention mask.

**Slow generation:** use a GPU with `dtype=torch.bfloat16`, a static cache, Flash Attention, assisted decoding, or fewer `max_new_tokens`.

## Best Practices

1. **Start from the checkpoint's `generation_config`**, then tune.
2. **Greedy/beam for extraction and scoring, sampling for open-ended text.**
3. **Always set `max_new_tokens`.**
4. **Seed sampled runs** with `transformers.set_seed(42)` and report decoding parameters with results.
5. **Validate generated text** against a labelled sample before using an LLM as a research instrument (coding, classification, summarization).
6. **Monitor memory**: beams and `num_return_sequences` multiply memory use.
