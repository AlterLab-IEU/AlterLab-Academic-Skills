---
name: alterlab-markitdown
description: Converts files and Office documents to clean, LLM-friendly Markdown with Microsoft MarkItDown (markitdown CLI, Python API, and markitdown-mcp server), supporting PDF, DOCX, PPTX, XLSX/XLS, images (EXIF metadata, LLM descriptions), audio (transcription), HTML, CSV, JSON, XML, ZIP archives, EPUB e-books, Outlook MSG, Jupyter notebooks, and YouTube transcript URLs, with OCR through the markitdown-ocr plugin or Azure Document Intelligence. Use when converting a document, PDF, slide deck, spreadsheet, scanned image, audio file, web page, or e-book into Markdown text for ingestion or LLM processing, extracting text from scans via OCR, transcribing audio, or batch-converting mixed file formats to token-efficient Markdown. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: "markitdown >= 0.1.8 (Python 3.10-3.14; uv pip install 'markitdown[all]'); format extras gate support (pdf, docx, pptx, audio, etc.); AI image descriptions and the markitdown-ocr plugin need an OpenAI-compatible LLM client and key (OPENAI_API_KEY or OPENROUTER_API_KEY); Azure Document Intelligence / Content Understanding need an Azure endpoint."
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# MarkItDown - File to Markdown Conversion

## Overview

MarkItDown is Microsoft's Python package and CLI for converting documents, media, and web content to Markdown for LLM and text-analysis pipelines. It preserves structure that matters to models (headings, lists, tables, links) and is not meant for high-fidelity, human-facing document conversion. This skill targets **markitdown 0.1.x** (current release 0.1.8, Sept 2026; Python 3.10–3.14).

## When to Use This Skill

Use this skill when the user wants to:
- Convert a PDF, Word, PowerPoint, Excel, EPUB, HTML, or Outlook file into Markdown for an LLM prompt, RAG index, or text analysis
- Batch-convert a folder of mixed document formats
- Get a YouTube transcript or audio transcription as Markdown
- Add LLM-written image descriptions, or OCR text from scans and embedded images
- Expose file conversion to an agent through the `markitdown-mcp` server

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Ingesting many sources into a self-hosted notebook with chat, search, or podcasts | `alterlab-open-notebook` |
| Answering questions across the sections, figures, and tables of one PDF | `alterlab-pdf-explore` |
| Building a one-row-per-paper evidence table from many PDFs | `alterlab-pdf-extract` |
| Managing references, DOIs, or BibTeX libraries | `alterlab-pyzotero` |

## Supported Formats

| Format | Description | Notes |
|--------|-------------|-------|
| **PDF** | Portable Document Format | Text-layer extraction (`[pdf]`); scans need OCR (see below) |
| **DOCX** | Microsoft Word | Headings, lists, tables (`[docx]`) |
| **PPTX** | PowerPoint | Slide text, tables, notes; optional LLM image descriptions (`[pptx]`) |
| **XLSX / XLS** | Excel spreadsheets | One Markdown table per sheet (`[xlsx]`, `[xls]`) |
| **Images** | JPEG, PNG | EXIF metadata (needs `exiftool`) and an LLM description when `llm_client` is set |
| **Audio** | WAV, MP3, M4A, MP4 | Metadata + speech transcription (`[audio-transcription]`) |
| **HTML** | Web pages | Clean conversion; Wikipedia and Bing result pages get dedicated handling |
| **CSV / JSON / XML** | Text-based data | CSV becomes a table; JSON, JSONL, and XML pass through as text; RSS/Atom feeds are parsed |
| **ZIP** | Archive files | Iterates contents |
| **EPUB** | E-books | Full text extraction |
| **Outlook MSG** | Email messages | Headers and body (`[outlook]`) |
| **Jupyter** | `.ipynb` notebooks | Markdown and code cells |
| **YouTube** | Video URLs | Fetches transcripts (`[youtube-transcription]`) |

## Quick Start

### Installation

```bash
# Install with all features (uv-first; uv pip works inside an active venv)
uv pip install 'markitdown[all]'

# Or run the CLI ad hoc without installing into the project env
uvx --from 'markitdown[all]' markitdown document.pdf -o output.md

# Or from source
git clone https://github.com/microsoft/markitdown.git
cd markitdown
uv pip install -e 'packages/markitdown[all]'
```

### Command-Line Usage

```bash
# Basic conversion
markitdown document.pdf > output.md

# Specify output file
markitdown document.pdf -o output.md

# Pipe content (give a type hint when reading from stdin)
cat document.pdf | markitdown -x pdf > output.md

# Keep embedded images as data URIs instead of truncating them
markitdown slides.pptx --keep-data-uris -o slides.md

# Plugins
markitdown --list-plugins          # list installed plugins
markitdown --use-plugins document.pdf -o output.md
```

### Python API

```python
from markitdown import MarkItDown, StreamInfo

md = MarkItDown()
result = md.convert("document.pdf")
print(result.markdown)            # result.text_content is a soft-deprecated alias
print(result.title)               # may be None

# Local files only (narrower than convert(), which also fetches URIs)
result = md.convert_local("document.pdf")

# From a binary stream; stream_info replaces the deprecated file_extension= keyword
with open("document.pdf", "rb") as f:
    result = md.convert_stream(f, stream_info=StreamInfo(extension=".pdf"))
```

## Advanced Features

### 1. AI-Enhanced Image Descriptions

Use an LLM via OpenRouter to describe images (built-in support covers image files and pictures inside PPTX):

```python
import os
from markitdown import MarkItDown
from openai import OpenAI

# OpenRouter takes the dotted slug of an Anthropic model ID (claude-opus-5-5 -> anthropic/claude-opus-5.5);
# scripts/convert_with_ai.py derives it from $ALTERLAB_MODEL (skills/core/shared/model_env.md).
model = "anthropic/claude-opus-5.5"

# Initialize OpenRouter client (OpenAI-compatible API)
client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

md = MarkItDown(
    llm_client=client,
    llm_model=model,  # recommended for scientific vision
    llm_prompt="Describe this image in detail for scientific documentation"
)

result = md.convert("presentation.pptx")
print(result.markdown)
```

### 2. OCR for Scans and Embedded Images

MarkItDown has no local OCR engine; the converters read existing text layers. Two supported routes add OCR:

- **`markitdown-ocr` plugin** (Microsoft, 0.1.x): LLM-vision OCR for images inside PDF, DOCX, PPTX, and XLSX, with full-page OCR for scanned PDFs. It reuses the same `llm_client` / `llm_model` as image descriptions; without a client it silently falls back to the normal converters.

  ```bash
  uv pip install markitdown-ocr openai
  ```

  ```python
  md_ocr = MarkItDown(enable_plugins=True, llm_client=client, llm_model=model)  # client/model as above
  result = md_ocr.convert("scanned_paper.pdf")
  ```

- **Azure Document Intelligence** (cloud OCR and layout analysis) — see the next section.

For fully local OCR, add a text layer first (e.g. `ocrmypdf scan.pdf searchable.pdf`, which uses Tesseract) and then convert the result.

### 3. Azure Document Intelligence and Content Understanding

```bash
# Document Intelligence (endpoint on the command line or in MARKITDOWN_DOCINTEL_ENDPOINT)
markitdown document.pdf -o output.md -d -e "<document_intelligence_endpoint>"

# Content Understanding (documents, images, audio, video; needs the [az-content-understanding] extra)
markitdown recording.mp4 --use-cu --cu-endpoint "<content_understanding_endpoint>"
```

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
result = md.convert("complex_document.pdf")
print(result.markdown)
```

Authentication uses the `AZURE_API_KEY` environment variable if set, otherwise `DefaultAzureCredential` (Azure CLI login, managed identity, etc.); pass `docintel_credential=` to supply one explicitly. Both services send the document to Azure, so check that this is allowed for the data you are converting.

### 4. Plugin System

Plugins are disabled by default. Enable them with `--use-plugins` on the CLI or `MarkItDown(enable_plugins=True)` in Python. Find third-party plugins with the GitHub hashtag `#markitdown-plugin`; see `references/api_reference.md` for writing one.

### 5. MCP Server

`markitdown-mcp` (0.0.1 alpha series) exposes one tool, `convert_to_markdown(uri)`, for `http:`, `https:`, `file:`, and `data:` URIs.

```bash
uv pip install markitdown-mcp
markitdown-mcp                                   # STDIO transport (default)
markitdown-mcp --http --host 127.0.0.1 --port 3001  # Streamable HTTP + SSE on localhost

# Register with Claude Code
claude mcp add markitdown -- uvx markitdown-mcp
```

Set `MARKITDOWN_ENABLE_PLUGINS=true` in the server environment to use installed plugins. The server has no authentication and can read any file its user can, so keep it on localhost (upstream recommends the Docker image for Claude Desktop).

## Optional Dependencies

Control which file formats you support:

```bash
# Install specific formats (no spaces inside the bracket — pip parses 'pdf, docx' as bad names)
uv pip install 'markitdown[pdf,docx,pptx]'

# All available options:
# [all]                       - All optional dependencies
# [pptx]                      - PowerPoint files
# [docx]                      - Word documents
# [xlsx]                      - Excel spreadsheets
# [xls]                       - Older Excel files
# [pdf]                       - PDF documents
# [outlook]                   - Outlook messages
# [az-doc-intel]              - Azure Document Intelligence
# [az-content-understanding]  - Azure Content Understanding
# [audio-transcription]       - WAV and MP3 transcription
# [youtube-transcription]     - YouTube video transcription
```

## Common Use Cases

### 1. Convert a Folder of Papers

```python
from pathlib import Path
from markitdown import MarkItDown

md = MarkItDown()
pdf_dir, output_dir = Path("papers/"), Path("markdown_output/")
output_dir.mkdir(exist_ok=True)

for pdf_file in pdf_dir.glob("*.pdf"):
    try:
        result = md.convert_local(pdf_file)
    except Exception as e:  # keep going; report failures at the end
        print(f"✗ {pdf_file.name}: {e}")
        continue
    (output_dir / f"{pdf_file.stem}.md").write_text(result.markdown)
```

For larger jobs with logging and parallelism, use `scripts/batch_convert.py`.

### 2. Extract Data from Excel for Analysis

```python
from markitdown import MarkItDown

result = MarkItDown().convert("data.xlsx")
print(result.markdown)  # one Markdown table per sheet
```

### 3. Convert PowerPoint with AI Descriptions

```python
import os
from markitdown import MarkItDown
from openai import OpenAI

# OpenRouter takes the dotted slug of an Anthropic model ID (claude-opus-5-5 -> anthropic/claude-opus-5.5);
# scripts/convert_with_ai.py derives it from $ALTERLAB_MODEL (skills/core/shared/model_env.md).
model = "anthropic/claude-opus-5.5"

# Use OpenRouter for access to multiple AI models
client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

md = MarkItDown(
    llm_client=client,
    llm_model=model,  # recommended for presentations
    llm_prompt="Describe this slide image in detail, focusing on key visual elements and data"
)

result = md.convert("presentation.pptx")
with open("presentation.md", "w") as f:
    f.write(result.markdown)
```

### 4. Extract YouTube Video Transcription

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("https://www.youtube.com/watch?v=VIDEO_ID")
print(result.markdown)
```

## Docker Usage

```bash
# Build image (from the repository root)
docker build -t markitdown:latest .

# Run conversion
docker run --rm -i markitdown:latest < ~/document.pdf > output.md
```

## Best Practices

### 1. Choose the Right Conversion Method

- **Simple documents**: Use basic `MarkItDown()`
- **Complex layouts or scanned PDFs**: Azure Document Intelligence, or the `markitdown-ocr` plugin
- **Visual content**: Enable AI image descriptions
- **Untrusted inputs**: Use `convert_local()` or `convert_stream()` rather than `convert()`

### 2. Handle Errors Gracefully

```python
from markitdown import MarkItDown, FileConversionException, UnsupportedFormatException

md = MarkItDown()

try:
    result = md.convert_local("document.pdf")
    print(result.markdown)
except FileNotFoundError:
    print("File not found")
except UnsupportedFormatException:
    print("No converter for this format (is the matching extra installed?)")
except FileConversionException as e:
    print(f"Conversion error: {e}")
```

### 3. Optimize for Token Efficiency

Markdown output is already token-efficient, but you can collapse blank lines and strip metadata you do not need:

```python
import re

clean_text = re.sub(r"\n{3,}", "\n\n", result.markdown).strip()
```

## Integration with Scientific Workflows

### Convert Literature for Review

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()

# Convert all papers in literature folder
papers_dir = Path("literature/pdfs")
output_dir = Path("literature/markdown")
output_dir.mkdir(exist_ok=True)

for paper in papers_dir.glob("*.pdf"):
    result = md.convert(str(paper))
    
    # Save with metadata
    output_file = output_dir / f"{paper.stem}.md"
    content = f"# {paper.stem}\n\n"
    content += f"**Source**: {paper.name}\n\n"
    content += "---\n\n"
    content += result.markdown
    
    output_file.write_text(content)

# For AI-enhanced conversion with figures
import os
from openai import OpenAI

# Model ID via the ALTERLAB_MODEL convention (skills/core/shared/model_env.md).
model = "anthropic/claude-opus-5.5"  # OpenRouter slug of the ALTERLAB_MODEL default (skills/core/shared/model_env.md)

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

md_ai = MarkItDown(
    llm_client=client,
    llm_model=model,
    llm_prompt="Describe scientific figures with technical precision"
)
```

## Security

MarkItDown reads files and fetches URLs with the privileges of the current process. When any part of the input comes from an untrusted user (hosted tools, agents acting on web content), validate paths and URLs first, block private and metadata-service addresses, and call the narrowest method (`convert_local()`, `convert_stream()`, or `convert_response()` on a response you fetched yourself) instead of `convert()`.

## Troubleshooting

### Common Issues

1. **Missing dependencies** (`MissingDependencyException`): install the feature extra
   ```bash
   uv pip install 'markitdown[pdf]'  # For PDF support
   ```

2. **Binary file errors**: `convert_stream()` requires a binary stream
   ```python
   with open("file.pdf", "rb") as f:  # Note the "rb"
       result = md.convert_stream(f, stream_info=StreamInfo(extension=".pdf"))
   ```

3. **Empty output from a scanned PDF or image**: MarkItDown found no text layer. Use the `markitdown-ocr` plugin, Azure Document Intelligence, or add a text layer locally with `ocrmypdf` before converting. Installing Tesseract alone does not enable OCR in MarkItDown.

4. **No EXIF metadata for images or audio**: install `exiftool` (or point `EXIFTOOL_PATH` at it).

## Performance Considerations

- **PDF files**: Large PDFs take time; there is no page-range option, so split very large files first if needed
- **Reuse one `MarkItDown()` instance** across files; creating it loads the file-type detector
- **Audio transcription**: Sends the audio to Google's Web Speech API via the `speech_recognition` package (network required, slow for long files); don't use it on confidential research recordings such as participant interviews unless your ethics approval allows third-party processing
- **AI image descriptions / OCR plugin**: One API call per image (costs and rate limits apply)

## Next Steps

- See `references/api_reference.md` for complete API documentation, custom converters, and plugins
- Check `references/file_formats.md` for format-specific details
- Review `scripts/batch_convert.py` for automation examples
- Explore `scripts/convert_with_ai.py` for AI-enhanced conversions

## Resources

- **MarkItDown GitHub**: https://github.com/microsoft/markitdown
- **PyPI**: https://pypi.org/project/markitdown/ (also `markitdown-ocr`, `markitdown-mcp`)
- **OpenRouter**: https://openrouter.ai (for AI-enhanced conversions)
- **OpenRouter API Keys**: https://openrouter.ai/keys
- **OpenRouter Models**: https://openrouter.ai/models
- **Plugin Development**: See `packages/markitdown-sample-plugin` in the MarkItDown repository

Part of the AlterLab Academic Skills suite.
