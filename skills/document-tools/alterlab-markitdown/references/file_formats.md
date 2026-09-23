# File Format Support

This document provides detailed information about each file format supported by MarkItDown.

## Document Formats

### PDF (.pdf)

**Capabilities**:
- Text-layer extraction (pdfminer.six / pdfplumber)
- Table detection
- Metadata extraction
- OCR for scanned pages only through the `markitdown-ocr` plugin or Azure Document Intelligence

**Dependencies**:
```bash
uv pip install 'markitdown[pdf]'
```

**Best For**:
- Scientific papers
- Reports
- Books
- Forms

**Limitations**:
- Complex layouts may not preserve perfect formatting
- Scanned PDFs have no text layer: use `markitdown-ocr`, Document Intelligence, or pre-process with `ocrmypdf`
- Some PDF features (annotations, forms) may not convert

**Example**:
```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("research_paper.pdf")
print(result.markdown)
```

**Enhanced with Azure Document Intelligence**:
```python
md = MarkItDown(docintel_endpoint="https://YOUR-ENDPOINT.cognitiveservices.azure.com/")
result = md.convert("complex_layout.pdf")
```

---

### Microsoft Word (.docx)

**Capabilities**:
- Text extraction
- Table conversion
- Heading hierarchy
- List formatting
- Basic text formatting (bold, italic)

**Dependencies**:
```bash
uv pip install 'markitdown[docx]'
```

**Best For**:
- Research papers
- Reports
- Documentation
- Manuscripts

**Preserved Elements**:
- Headings (converted to Markdown headers)
- Tables (converted to Markdown tables)
- Lists (bulleted and numbered)
- Basic formatting (bold, italic)
- Paragraphs

**Example**:
```python
result = md.convert("manuscript.docx")
```

---

### PowerPoint (.pptx)

**Capabilities**:
- Slide content extraction
- Speaker notes
- Table extraction
- Image descriptions (with AI)

**Dependencies**:
```bash
uv pip install 'markitdown[pptx]'
```

**Best For**:
- Presentations
- Lecture slides
- Conference talks

**Output Format**:
```markdown
# Slide 1: Title

Content from slide 1...

**Notes**: Speaker notes appear here

---

# Slide 2: Next Topic

...
```

**With AI Image Descriptions** (via OpenRouter; model follows the `ALTERLAB_MODEL` convention, see skills/core/shared/model_env.md):
```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
md = MarkItDown(llm_client=client, llm_model=os.environ.get("ALTERLAB_MODEL") or "anthropic/claude-opus-4-8")
result = md.convert("presentation.pptx")
```

---

### Excel (.xlsx, .xls)

**Capabilities**:
- Sheet extraction
- Table formatting
- Data preservation
- Formula values (calculated)

**Dependencies**:
```bash
uv pip install 'markitdown[xlsx]'  # Modern Excel
uv pip install 'markitdown[xls]'   # Legacy Excel
```

**Best For**:
- Data tables
- Research data
- Statistical results
- Experimental data

**Output Format**:
```markdown
# Sheet: Results

| Sample | Control | Treatment | P-value |
|--------|---------|-----------|---------|
| 1      | 10.2    | 12.5      | 0.023   |
| 2      | 9.8     | 11.9      | 0.031   |
```

**Example**:
```python
result = md.convert("experimental_data.xlsx")
```

---

## Image Formats

### Images (.jpg, .jpeg, .png)

**Capabilities**:
- EXIF metadata extraction (requires the `exiftool` binary)
- AI-powered image descriptions when `llm_client` / `llm_model` are set (the model can also transcribe visible text)
- No local OCR engine; other image types (GIF, WebP, TIFF) are not handled by the built-in image converter

**Dependencies**:
```bash
uv pip install markitdown   # core only; install exiftool separately (e.g. apt/brew)
```

**Best For**:
- Scanned documents
- Charts and graphs
- Scientific diagrams
- Photographs with text

**Output Without AI**:
```markdown
![Image](image.jpg)

**EXIF Data**:
- Camera: Canon EOS 5D
- Date: 2024-01-15
- Resolution: 4000x3000
```

**Output With AI** (via OpenRouter; model follows the `ALTERLAB_MODEL` convention):
```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
md = MarkItDown(
    llm_client=client,
    llm_model=os.environ.get("ALTERLAB_MODEL") or "anthropic/claude-opus-4-8",
    llm_prompt="Describe this scientific diagram in detail"
)
result = md.convert("graph.png")
```

**OCR for Text Extraction**:
MarkItDown does not call Tesseract. For images embedded in PDF/DOCX/PPTX/XLSX, install the `markitdown-ocr` plugin and pass an LLM client (`MarkItDown(enable_plugins=True, llm_client=..., llm_model=...)`); for standalone images, the LLM description above with a transcription-oriented `llm_prompt` is the built-in route, or use Azure Document Intelligence.

---

## Audio Formats

### Audio (.wav, .mp3, .m4a, .mp4)

**Capabilities**:
- Metadata extraction (via `exiftool`)
- Speech-to-text transcription through the `speech_recognition` package's Google Web Speech backend (audio leaves your machine; check ethics approvals before transcribing participant recordings)
- Duration and technical info

**Dependencies**:
```bash
uv pip install 'markitdown[audio-transcription]'
```

**Best For**:
- Lecture recordings
- Interviews
- Podcasts
- Meeting recordings

**Output Format**:
```markdown
# Audio: interview.mp3

**Metadata**:
- Duration: 45:32
- Bitrate: 320kbps
- Sample Rate: 44100Hz

**Transcription**:
[Transcribed text appears here...]
```

**Example**:
```python
result = md.convert("lecture.mp3")
```

---

## Web Formats

### HTML (.html, .htm)

**Capabilities**:
- Clean HTML to Markdown conversion
- Link preservation
- Table conversion
- List formatting

**Best For**:
- Web pages
- Documentation
- Blog posts
- Online articles

**Output Format**: Clean Markdown with preserved links and structure

**Example**:
```python
result = md.convert("webpage.html")
```

---

### YouTube URLs

**Capabilities**:
- Fetch video transcriptions
- Extract video metadata
- Caption download

**Dependencies**:
```bash
uv pip install 'markitdown[youtube-transcription]'
```

**Best For**:
- Educational videos
- Lectures
- Talks
- Tutorials

**Example**:
```python
result = md.convert("https://www.youtube.com/watch?v=VIDEO_ID")
```

---

## Data Formats

### CSV (.csv)

**Capabilities**:
- Automatic table conversion
- Delimiter detection
- Header preservation

**Output Format**: Markdown tables

**Example**:
```python
result = md.convert("data.csv")
```

**Output**:
```markdown
| Column1 | Column2 | Column3 |
|---------|---------|---------|
| Value1  | Value2  | Value3  |
```

---

### JSON (.json)

**Capabilities**:
- Structured representation
- Pretty formatting
- Nested data visualization

**Best For**:
- API responses
- Configuration files
- Data exports

**Example**:
```python
result = md.convert("data.json")
```

---

### XML (.xml)

**Capabilities**:
- Structure preservation
- Attribute extraction
- Formatted output

**Best For**:
- Configuration files
- Data interchange
- Structured documents

**Example**:
```python
result = md.convert("config.xml")
```

---

## Archive Formats

### ZIP (.zip)

**Capabilities**:
- Iterates through archive contents
- Converts each file individually
- Maintains directory structure in output

**Best For**:
- Document collections
- Project archives
- Batch conversions

**Output Format**:
```markdown
# Archive: documents.zip

## File: document1.pdf
[Content from document1.pdf...]

---

## File: document2.docx
[Content from document2.docx...]
```

**Example**:
```python
result = md.convert("archive.zip")
```

---

## E-book Formats

### EPUB (.epub)

**Capabilities**:
- Full text extraction
- Chapter structure
- Metadata extraction

**Best For**:
- E-books
- Digital publications
- Long-form content

**Output Format**: Markdown with preserved chapter structure

**Example**:
```python
result = md.convert("book.epub")
```

---

## Other Formats

### Outlook Messages (.msg)

**Capabilities**:
- Email content extraction
- Attachment listing
- Metadata (from, to, subject, date)

**Dependencies**:
```bash
uv pip install 'markitdown[outlook]'
```

**Best For**:
- Email archives
- Communication records

**Example**:
```python
result = md.convert("message.msg")
```

---

## Format-Specific Tips

### PDF Best Practices

1. **Use Azure Document Intelligence for complex layouts**:
   ```python
   md = MarkItDown(docintel_endpoint="endpoint_url")
   ```

2. **For scanned PDFs, add OCR**:
   ```bash
   uv pip install markitdown-ocr openai   # LLM-vision OCR plugin
   # or add a text layer locally first: ocrmypdf scan.pdf searchable.pdf
   ```

3. **Split very large PDFs before conversion** for better performance

### PowerPoint Best Practices

1. **Use AI for visual content** (model via the `ALTERLAB_MODEL` convention):
   ```python
   md = MarkItDown(llm_client=client, llm_model=os.environ.get("ALTERLAB_MODEL") or "anthropic/claude-opus-4-8")
   ```

2. **Check speaker notes** - they're included in output

3. **Complex animations won't be captured** - static content only

### Excel Best Practices

1. **Large spreadsheets** may take time to convert

2. **Formulas are converted to their calculated values**

3. **Multiple sheets** are all included in output

4. **Charts and embedded images are not converted** — only cell values; the `markitdown-ocr` plugin can OCR embedded images

### Image Best Practices

1. **Use AI for meaningful descriptions** (model via the `ALTERLAB_MODEL` convention):
   ```python
   md = MarkItDown(
       llm_client=client,
       llm_model=os.environ.get("ALTERLAB_MODEL") or "anthropic/claude-opus-4-8",
       llm_prompt="Describe this scientific figure in detail"
   )
   ```

2. **For text-heavy images**, use a transcription-oriented `llm_prompt` or Azure Document Intelligence (there is no local OCR)

3. **High-resolution images** may take longer to process

### Audio Best Practices

1. **Clear audio** produces better transcriptions

2. **Long recordings** may take significant time

3. **Consider splitting long audio files** for faster processing

---

## Unsupported Formats

If you need to convert an unsupported format:

1. **Create a custom converter** (see `api_reference.md`)
2. **Look for plugins** on GitHub (#markitdown-plugin)
3. **Pre-convert to supported format** (e.g., convert .rtf to .docx)

---

## Format Detection

MarkItDown combines several signals to pick a converter:

1. **File extension** and **MIME type** (from the path, URL, HTTP headers, or your `StreamInfo`)
2. **Content sniffing** with Google's Magika model, so files without a useful extension still route correctly

**Override detection** with a `StreamInfo` hint (the older `file_extension=` keyword is deprecated):
```python
from markitdown import StreamInfo

# Force specific format
result = md.convert("file_without_extension", stream_info=StreamInfo(extension=".pdf"))

# With streams
with open("file", "rb") as f:
    result = md.convert_stream(f, stream_info=StreamInfo(extension=".pdf"))
```

