# Pipeline API Reference (transformers v5)

## Overview

Pipelines are the simplest way to run pretrained models for inference. They wrap tokenization/pre-processing, the forward pass, and post-processing behind one call. v5 pipelines are PyTorch-only and the task list was trimmed (see "Removed in v5" below).

## Basic Usage

```python
from transformers import pipeline

# Auto-selects the task's default checkpoint (and warns) — fine for a demo
pipe = pipeline("text-classification")
result = pipe("This is great!")

# Pin the checkpoint for anything you will report or rerun
pipe = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
```

`transformers.pipelines.get_supported_tasks()` lists the tasks your installed version supports.

## Supported Tasks

### Natural Language Processing

**text-generation** (plain prompt or chat messages):
```python
generator = pipeline("text-generation", model="Qwen/Qwen3-0.6B")

# Chat input: returns the conversation with the assistant turn appended
messages = [{"role": "user", "content": "Give three uses of bootstrapping in statistics."}]
out = generator(messages, max_new_tokens=200,
                tokenizer_encode_kwargs={"enable_thinking": False})  # Qwen3-only switch
print(out[0]["generated_text"][-1]["content"])

# Plain-text continuation
generator("Once upon a time", max_new_tokens=50, do_sample=True, num_return_sequences=2)
```
When no model is given, v5 defaults to `HuggingFaceTB/SmolLM3-3B` for this task.

**Summarization, translation, question answering** — no dedicated pipeline in v5; prompt a chat model:
```python
summarizer = pipeline("text-generation", model="Qwen/Qwen3-0.6B")
prompt = [{"role": "user", "content": f"Summarize in 3 bullet points:\n\n{article}"}]
summary = summarizer(prompt, max_new_tokens=200,
                     tokenizer_encode_kwargs={"enable_thinking": False})[0]["generated_text"][-1]["content"]
```
Swap the instruction for "Translate to French: …" or "Answer using only this context: …". Larger instruct models (e.g. `Qwen/Qwen3-4B-Instruct-2507`) give noticeably better summaries than sub-1B models.

**text-classification** (alias `sentiment-analysis`):
```python
classifier = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
result = classifier("I love this product!")  # [{'label': 'POSITIVE', 'score': ...}]
```

**token-classification** (alias `ner`):
```python
ner = pipeline("token-classification", model="dslim/bert-base-NER", aggregation_strategy="simple")
entities = ner("Hugging Face is based in New York City")
```

**fill-mask**:
```python
unmasker = pipeline("fill-mask", model="google-bert/bert-base-uncased")
result = unmasker("Paris is the [MASK] of France.")
```

**zero-shot-classification**:
```python
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
result = classifier(
    "This is a course about Python programming",
    candidate_labels=["education", "politics", "business"],
)
```

**feature-extraction** (token embeddings; pool them yourself):
```python
extractor = pipeline("feature-extraction", model="google-bert/bert-base-uncased")
embeddings = extractor("Some text", return_tensors=True)  # shape (1, seq_len, hidden)
```
For sentence embeddings as a measurement instrument in social-science text analysis, see `alterlab-text-as-data` (sentence-transformers).

**table-question-answering** and **document-question-answering** (`impira/layoutlm-document-qa`, needs `pytesseract` for OCR) are still available.

### Computer Vision

**image-classification**:
```python
from PIL import Image

classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
result = classifier("path/to/image.jpg")         # path, URL, PIL image, or list of them
result = classifier(Image.open("image.jpg"))
```

**object-detection**:
```python
detector = pipeline("object-detection", model="facebook/detr-resnet-50")
results = detector("image.jpg")  # [{'score', 'label', 'box': {xmin, ymin, xmax, ymax}}, ...]
```

**image-segmentation**:
```python
segmenter = pipeline("image-segmentation", model="facebook/detr-resnet-50-panoptic")
segments = segmenter("image.jpg")
```

**depth-estimation**:
```python
depth = pipeline("depth-estimation", model="Intel/dpt-large")
result = depth("image.jpg")
```

**zero-shot-image-classification**:
```python
classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
result = classifier("image.jpg", candidate_labels=["cat", "dog", "bird"])
```

Also available: `zero-shot-object-detection`, `image-feature-extraction`, `mask-generation` (SAM), `video-classification`, `keypoint-matching`.

### Audio

**automatic-speech-recognition**:
```python
asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo")
text = asr("audio.mp3", return_timestamps=True)  # timestamps needed for audio > 30 s with Whisper
```
`openai/whisper-base` is a lighter CPU option.

**audio-classification**:
```python
classifier = pipeline("audio-classification", model="MIT/ast-finetuned-audioset-10-10-0.4593")
result = classifier("audio.wav")
```

**text-to-audio** (alias `text-to-speech`):
```python
tts = pipeline("text-to-audio", model="suno/bark-small")
speech = tts("Hello, this is a test")  # {'audio': np.ndarray, 'sampling_rate': int}
```
Some TTS models need extra inputs (e.g. SpeechT5 requires `forward_params={"speaker_embeddings": ...}`); check the model card.

### Multimodal

**image-text-to-text** (captioning, visual question answering, chart/figure reading with a VLM):
```python
vlm = pipeline("image-text-to-text", model="Qwen/Qwen3-VL-2B-Instruct")
messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": "https://example.com/figure.png"},
        {"type": "text", "text": "Describe the trend shown in this figure."},
    ],
}]
out = vlm(text=messages, max_new_tokens=200)
print(out[0]["generated_text"][-1]["content"])
```
In v5 images must be embedded in the chat `content`; passing `images=` alongside a chat is no longer accepted.

`any-to-any` covers omni models (e.g. text + audio + image in, text out).

### Removed in v5

| Removed task | Use instead |
|--------------|-------------|
| `summarization`, `translation_xx_to_yy`, `text2text-generation`, `question-answering` | `text-generation` with a chat model and an instruction prompt |
| `image-to-text`, `visual-question-answering` | `image-text-to-text` with a VLM |
| `image-to-image` | 🤗 Diffusers |

## Pipeline Parameters

**model**: Hub ID or local path
```python
pipe = pipeline("task", model="org/model-id", revision="main")  # pin revision= for reproducibility
```

**device**: GPU index, device string, or -1 for CPU
```python
pipe = pipeline("task", model="org/model-id", device=0)        # first CUDA GPU
pipe = pipeline("task", model="org/model-id", device="mps")    # Apple silicon
```

**device_map**: automatic placement for large models (requires `accelerate`)
```python
pipe = pipeline("task", model="org/large-model", device_map="auto")
```

**dtype**: precision (defaults to `"auto"` = checkpoint dtype in v5)
```python
import torch
pipe = pipeline("task", model="org/model-id", dtype=torch.bfloat16)
```
`torch_dtype=` still works but logs a deprecation warning — use `dtype=`.

**batch_size**: process several inputs per forward pass
```python
pipe = pipeline("task", model="org/model-id", batch_size=8)
results = pipe(["text1", "text2", "text3"])
```

There is no `framework=` argument any more: v5 is PyTorch-only.

## Batch Processing

```python
classifier = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
results = classifier(["Great product!", "Terrible experience", "Just okay"])
```

For large datasets, stream from a `datasets.Dataset` with `KeyDataset` so the pipeline can batch and prefetch:

```python
from datasets import load_dataset
from transformers.pipelines.pt_utils import KeyDataset

dataset = load_dataset("stanfordnlp/imdb", split="test")
pipe = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
                device=0, batch_size=32)

for output in pipe(KeyDataset(dataset, "text"), truncation=True):
    print(output)
```

## Performance Optimization

- **GPU**: pass `device=0` (or `device_map="auto"` for models that do not fit on one GPU).
- **Precision**: `dtype=torch.bfloat16` (Ampere+ GPUs) or `torch.float16` roughly halves memory versus float32.
- **Batching**: helps on GPU with similar-length inputs; usually not on CPU, and it adds latency for real-time use.

```python
pipe = pipeline("task", model="org/model-id", batch_size=32, device=0)
results = pipe(list_of_texts)
```

### Streaming Output

```python
from transformers import TextStreamer

generator = pipeline("text-generation", model="Qwen/Qwen3-0.6B")
streamer = TextStreamer(generator.tokenizer, skip_prompt=True)
# Pass the streamer at call time, not to the pipeline constructor
generator("The future of open science is", max_new_tokens=100, streamer=streamer)
```

## Custom Pipeline Configuration

Pass pre-loaded components:

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("org/model-id")
model = AutoModelForSequenceClassification.from_pretrained("org/model-id")
pipe = pipeline("text-classification", model=model, tokenizer=tokenizer)
```

Subclass a pipeline to customize a stage:

```python
from transformers import TextClassificationPipeline

class CustomPipeline(TextClassificationPipeline):
    def postprocess(self, model_outputs, **kwargs):
        # Custom post-processing
        return super().postprocess(model_outputs, **kwargs)

pipe = pipeline("text-classification", model="org/model-id", pipeline_class=CustomPipeline)
```

## Input Formats

- **Text tasks**: a string or a list of strings; `text-generation` also accepts chat message lists.
- **Image tasks**: URLs, file paths, PIL images, or lists of them.
- **Audio tasks**: file paths, NumPy arrays, or `{"raw": array, "sampling_rate": sr}` dicts.

## Error Handling

```python
import torch

try:
    result = pipe(input_data)
except torch.cuda.OutOfMemoryError:
    # Reduce batch_size, lower precision, or fall back to CPU
    pipe = pipeline("task", model="org/model-id", device=-1)
except OSError as e:
    # Raised for unknown/misspelled model IDs or gated repos without a token
    print(f"Check the model ID and your HF_TOKEN: {e}")
```

## Best Practices

1. **Use pipelines for prototyping** and straightforward batch inference.
2. **Pin model IDs (and revisions)**: task defaults change between releases.
3. **Enable GPU and reduced precision** when available.
4. **Batch for throughput** on GPU; skip batching for latency-sensitive use.
5. **Prefer a chat model** for summarization, translation, and QA in v5 — and validate its output on a labelled sample before using it as a research instrument.
6. **Cache models locally**: set `HF_HOME` (not the removed `TRANSFORMERS_CACHE`) to control the cache location.
