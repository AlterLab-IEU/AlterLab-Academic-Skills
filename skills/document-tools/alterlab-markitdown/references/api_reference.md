# MarkItDown API Reference

## Core Classes

### MarkItDown

The main class for converting files to Markdown (markitdown 0.1.x).

```python
from markitdown import MarkItDown

md = MarkItDown(
    enable_plugins=False,      # load third-party plugins
    llm_client=None,           # OpenAI-compatible client for image descriptions / OCR plugin
    llm_model=None,
    llm_prompt=None,
    docintel_endpoint=None,    # Azure Document Intelligence
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_plugins` | bool | `False` | Load converters from installed plugins (entry point group `markitdown.plugin`) |
| `enable_builtins` | bool | `True` | Register the built-in converters |
| `llm_client` | OpenAI client | `None` | OpenAI-compatible client for AI image descriptions (image files and PPTX pictures) |
| `llm_model` | str | `None` | Model name for image descriptions; use the `ALTERLAB_MODEL` convention (dated default `anthropic/claude-opus-4-8`, see skills/core/shared/model_env.md) |
| `llm_prompt` | str | `None` | Custom prompt for image description |
| `docintel_endpoint` | str | `None` | Azure Document Intelligence endpoint (`docintel_credential`, `docintel_file_types`, `docintel_api_version` refine it) |
| `cu_endpoint` | str | `None` | Azure Content Understanding endpoint (`cu_credential`, analyzer options) |
| `exiftool_path` | str | `None` | Path to `exiftool` for image/audio metadata (falls back to `EXIFTOOL_PATH` or a search of common locations) |
| `style_map` | str | `None` | Mammoth style map for DOCX conversion |
| `requests_session` | `requests.Session` | new session | Session used for URL fetches |

All keyword arguments are also forwarded to plugins' `register_converters()`.

#### Methods

##### convert()

Convert a local path, URL (`http:`, `https:`, `file:`, `data:`), `requests.Response`, or binary stream.

```python
result = md.convert(source, stream_info=None)
```

**Parameters**:
- `source`: path, URI string, `pathlib.Path`, `requests.Response`, or binary file-like object
- `stream_info` (`StreamInfo`, optional): hints such as `extension`, `mimetype`, `charset`, `filename`, `url`

`convert()` is intentionally permissive (it will fetch URLs). For untrusted input, call the narrowest method instead: `convert_local(path)`, `convert_stream(stream)`, or `convert_response(response)` on a response you fetched yourself.

**Example**:
```python
result = md.convert("document.pdf")
print(result.markdown)
```

##### convert_stream()

Convert from a binary file-like object.

```python
from markitdown import StreamInfo

with open("document.pdf", "rb") as f:
    result = md.convert_stream(f, stream_info=StreamInfo(extension=".pdf"))
    print(result.markdown)
```

The stream must be opened in binary mode (`"rb"`). The older `file_extension=".pdf"` keyword still works but is deprecated in favor of `stream_info`.

## Result Object

### DocumentConverterResult

The result of a conversion operation.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `markdown` | str | The converted Markdown text |
| `title` | str or None | Document title (if available) |
| `text_content` | str | Soft-deprecated alias for `markdown` |

`str(result)` also returns the Markdown.

#### Example

```python
result = md.convert("paper.pdf")

content = result.markdown
title = result.title
```

## Custom Converters

A converter subclasses `DocumentConverter` and implements two methods that receive a binary stream plus a `StreamInfo` (0.1.x interface; the pre-0.1 `convert(stream, file_extension)` signature no longer works):

```python
from typing import Any, BinaryIO
from markitdown import MarkItDown, DocumentConverter, DocumentConverterResult, StreamInfo


class CustomFormatConverter(DocumentConverter):
    def accepts(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> bool:
        # Decide from the metadata; if you peek at bytes, restore the stream position
        return (stream_info.extension or "").lower() == ".custom"

    def convert(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> DocumentConverterResult:
        text = file_stream.read().decode(stream_info.charset or "utf-8")
        return DocumentConverterResult(markdown=f"# Custom Format\n\n{text}", title="Custom Document")


md = MarkItDown()
md.register_converter(CustomFormatConverter())   # optional: priority=PRIORITY_SPECIFIC_FILE_FORMAT
result = md.convert("myfile.custom")
```

Lower `priority` values are tried first; built-in format converters use `PRIORITY_SPECIFIC_FILE_FORMAT` (0.0) and the generic text/HTML/ZIP converters use `PRIORITY_GENERIC_FILE_FORMAT` (10.0).

## Plugin System

### Finding Plugins

Search GitHub for the `#markitdown-plugin` tag. Microsoft's own `markitdown-ocr` plugin adds LLM-vision OCR for PDF, DOCX, PPTX, and XLSX (see SKILL.md).

### Using Plugins

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)   # CLI: markitdown --use-plugins file.pdf
result = md.convert("document.pdf")
```

### Creating Plugins

A plugin is a package that exposes a module through the `markitdown.plugin` entry-point group. The module defines `__plugin_interface_version__ = 1` and a `register_converters(markitdown, **kwargs)` function (see `packages/markitdown-sample-plugin` upstream):

**pyproject.toml**:
```toml
[project]
name = "markitdown-my-plugin"
version = "0.1.0"
dependencies = ["markitdown>=0.1,<0.2"]

[project.entry-points."markitdown.plugin"]
my_plugin = "my_plugin"
```

**my_plugin/__init__.py**:
```python
from markitdown import MarkItDown
from .converter import MyConverter   # a DocumentConverter subclass as above

__plugin_interface_version__ = 1


def register_converters(markitdown: MarkItDown, **kwargs):
    # kwargs carries the MarkItDown(...) keyword arguments (e.g. llm_client)
    markitdown.register_converter(MyConverter())
```

## AI-Enhanced Conversions

### Using OpenRouter for Image Descriptions

```python
from markitdown import MarkItDown
from openai import OpenAI

# Model ID via the ALTERLAB_MODEL convention (skills/core/shared/model_env.md):
# $ALTERLAB_MODEL, else the dated default (reviewed 2026-06-06), with OpenRouter prefix.
import os
model = os.environ.get("ALTERLAB_MODEL") or "anthropic/claude-opus-4-8"

# Initialize OpenRouter client (OpenAI-compatible API)
client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

# Create MarkItDown with AI support
md = MarkItDown(
    llm_client=client,
    llm_model=model,  # recommended for scientific vision
    llm_prompt="Describe this image in detail for scientific documentation"
)

# Convert files with images
result = md.convert("presentation.pptx")
```

### Available Models via OpenRouter

Popular models with vision support:
- `anthropic/claude-opus-4-8` - **Recommended for scientific vision** (the dated default behind `ALTERLAB_MODEL`)
- A current Google Gemini Pro Vision model - alternative vision backend

Prefer the `ALTERLAB_MODEL` env-var convention (skills/core/shared/model_env.md) over
hardcoding any of these. See https://openrouter.ai/models for the complete list.

### Custom Prompts

```python
# For scientific diagrams
scientific_prompt = """
Analyze this scientific diagram or chart. Describe:
1. The type of visualization (graph, chart, diagram, etc.)
2. Key data points or trends
3. Labels and axes
4. Scientific significance
Be precise and technical.
"""

md = MarkItDown(
    llm_client=client,
    llm_model=os.environ.get("ALTERLAB_MODEL") or "anthropic/claude-opus-4-8",
    llm_prompt=scientific_prompt
)
```

## Azure Document Intelligence

### Setup

1. Create Azure Document Intelligence resource
2. Get endpoint URL
3. Set authentication

### Usage

```python
from markitdown import MarkItDown

md = MarkItDown(
    docintel_endpoint="https://YOUR-RESOURCE.cognitiveservices.azure.com/"
)

result = md.convert("complex_document.pdf")
```

### Authentication

If `AZURE_API_KEY` is set, it is used as an `AzureKeyCredential`; otherwise MarkItDown falls back to `DefaultAzureCredential` (Azure CLI login, managed identity, environment service principal):
```bash
export AZURE_API_KEY="your-key"
export MARKITDOWN_DOCINTEL_ENDPOINT="https://YOUR-RESOURCE.cognitiveservices.azure.com/"  # CLI: then `markitdown file.pdf -d`
```

Or pass a credential object: `MarkItDown(docintel_endpoint=..., docintel_credential=AzureKeyCredential("..."))`.

## Error Handling

```python
from markitdown import MarkItDown

md = MarkItDown()

from markitdown import FileConversionException, MissingDependencyException, UnsupportedFormatException

try:
    result = md.convert_local("document.pdf")
    print(result.markdown)
except FileNotFoundError:
    print("File not found")
except MissingDependencyException as e:
    print(f"Install the matching extra, e.g. 'markitdown[pdf]': {e}")
except UnsupportedFormatException:
    print("No converter accepted this file")
except FileConversionException as e:
    print(f"Conversion error: {e}")
```

## Performance Tips

### 1. Reuse MarkItDown Instance

```python
# Good: Create once, use many times
md = MarkItDown()

for file in files:
    result = md.convert(file)
    process(result)
```

### 2. Convert from Streams When You Already Have Bytes

`convert_stream()` avoids a temporary file when the data is already in memory or comes from another API; it does not reduce peak memory (the converters still read the whole document).

```python
with open("large_file.pdf", "rb") as f:
    result = md.convert_stream(f, stream_info=StreamInfo(extension=".pdf"))
```

### 3. Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor

md = MarkItDown()

def convert_file(filepath):
    return md.convert(filepath)

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(convert_file, file_list)
```

## Breaking Changes (v0.0.1 to v0.1.0)

1. **Dependencies**: Now organized into optional feature groups
   ```bash
   # Old
   pip install markitdown
   
   # New
   pip install 'markitdown[all]'
   ```

2. **convert_stream()**: Now requires binary file-like object
   ```python
   # Old (also accepted text)
   with open("file.pdf", "r") as f:  # text mode
       result = md.convert_stream(f)
   
   # New (binary only)
   with open("file.pdf", "rb") as f:  # binary mode
       result = md.convert_stream(f, stream_info=StreamInfo(extension=".pdf"))
   ```

3. **DocumentConverter Interface**: Converters now implement `accepts(file_stream, stream_info, **kwargs)` and `convert(file_stream, stream_info, **kwargs)` and return `DocumentConverterResult(markdown=..., title=...)`
   - No temporary files created
   - Plugins written for 0.0.x need updating

4. **Result attribute**: `result.markdown` is the primary field; `result.text_content` remains as a soft-deprecated alias

## Version Compatibility

- **Python**: 3.10–3.14 (markitdown 0.1.8)
- **Dependencies**: Declared in `packages/markitdown/pyproject.toml`; format support comes from the optional extras
- **OpenAI**: Compatible with OpenAI Python SDK v1.0+

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for image descriptions | `sk-or-v1-...` |
| `AZURE_API_KEY` | Azure Document Intelligence / Content Understanding key (else `DefaultAzureCredential`) | `key123...` |
| `MARKITDOWN_DOCINTEL_ENDPOINT` | Default Document Intelligence endpoint for the CLI `-d` flag | `https://...` |
| `MARKITDOWN_CU_ENDPOINT` | Default Content Understanding endpoint for `--use-cu` | `https://...` |
| `EXIFTOOL_PATH` | Location of `exiftool` for image/audio metadata | `/usr/bin/exiftool` |
| `MARKITDOWN_ENABLE_PLUGINS` | `markitdown-mcp` only: load installed plugins | `true` |

