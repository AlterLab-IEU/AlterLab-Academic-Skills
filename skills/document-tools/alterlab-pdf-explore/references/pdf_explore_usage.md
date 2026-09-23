# PDF Explore — Usage Reference

Deeper detail for `alterlab-pdf-explore`. Versions below were checked on PyPI in September 2026.

## Parser choice

- **PyMuPDF** (`pymupdf`, import `pymupdf`; `fitz` is the legacy alias) — fast text with fonts and
  bounding boxes, the document outline (`doc.get_toc()`), image lists, `page.find_tables()`, and
  Tesseract OCR through `page.get_textpage_ocr()`. Good default. License: AGPL-3.0 or a commercial
  license from Artifex — fine for local research use; check before bundling it into software you
  distribute.
- **pdfplumber** (MIT) — strong table extraction and word/character bounding boxes; slower.
- **pymupdf4llm** — Markdown per page (`pymupdf4llm.to_markdown(path, page_chunks=True)` returns one
  dict per page with `text`, `metadata`, `toc_items`), handy when you want Markdown with page numbers.
- **OCR** — scanned or image-only PDFs have no text layer. Either OCR pages with PyMuPDF
  (`page.get_textpage_ocr(language="eng", dpi=300, full=True)`, needs Tesseract installed) or add a
  text layer to the whole file once with `ocrmypdf scan.pdf searchable.pdf`, then parse normally.
  Cache the OCR result; do not re-OCR for every question.

```bash
uv pip install "pymupdf>=1.24" "pdfplumber>=0.11"   # current: 1.28.x and 0.11.x
```

## Parse once: section index + extract-every-instance

Parse the file a single time into line records (page, text, font size, bounding box), label each
line with the most recent heading, and answer later questions from that index. Tested with
PyMuPDF 1.28:

```python
import re
from collections import Counter

import pymupdf


def build_index(path):
    """Parse a PDF once: one record per text line with page, section, font size, and bbox."""
    doc = pymupdf.open(path)
    lines = []
    for pno, page in enumerate(doc, start=1):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if text:
                    size = max(span["size"] for span in line["spans"])
                    lines.append({"page": pno, "text": text, "size": size, "bbox": line["bbox"]})
    chars_by_size = Counter()
    for entry in lines:  # body text = the font size carrying the most characters
        chars_by_size[round(entry["size"])] += len(entry["text"])
    body_size = chars_by_size.most_common(1)[0][0]
    section = None
    for entry in lines:  # carry the most recent heading forward as the section label
        if entry["size"] >= body_size * 1.2:
            section = entry["text"]
        entry["section"] = section
    return {"toc": doc.get_toc(), "lines": lines, "n_pages": doc.page_count}


def find_all(index, pattern):
    """Every match with page + section, not just the first one."""
    rx = re.compile(pattern)
    return [
        {"page": e["page"], "section": e["section"], "match": m.group(0), "context": e["text"]}
        for e in index["lines"]
        for m in rx.finditer(e["text"])
    ]


index = build_index("paper.pdf")
p_values = find_all(index, r"\bp\s*[<=>]\s*0?\.\d+")
sample_sizes = find_all(index, r"\b[nN]\s*=\s*\d[\d,]*")
```

Prefer the PDF's own outline (`index["toc"]`) for section names when it exists; the font-size
heuristic is the fallback for PDFs without bookmarks. Values split across lines or hyphenated at a
line break can escape a line-level regex, so also search the page text (`page.get_text()`) when a
count looks low.

## Section / figure index

Record figure and table regions per page too: `page.get_images(full=True)` plus
`page.get_image_rects(xref)` locate embedded images, captions usually sit in the lines just below
("Figure 3", "Table 2"), and `page.find_tables()` returns table bounding boxes. Every answer should
carry a **page + section** citation so it is verifiable.

## Extract-every-instance

For "find all X", scan the full parsed text (not just the first match) and return a located
list — page, section, surrounding context — for each hit. Common patterns: p-values, sample
sizes (n=…), effect sizes/CIs, gene/protein mentions, dataset identifiers. Report the total count
and say which pages were OCR'd, since OCR errors ("0.O5", "p<O.001") hide matches.

## Reading figures and tables

- **Tables**: extract with `page.find_tables()` (PyMuPDF) or `pdfplumber`'s
  `page.extract_tables()`; verify column alignment and merged header cells against the rendered
  page.
- **Charts**: reading values off a rendered chart is approximate — render the region
  (`page.get_pixmap(clip=rect, dpi=200)`) and inspect it, report axis ranges and
  estimated series values, and flag that they should be confirmed against underlying data if
  available. Do not present chart-read numbers as exact.

## Choosing the document skill

| Goal | Skill |
|------|-------|
| Deep Q&A within ONE PDF (sections/figures/appendix) | `alterlab-pdf-explore` |
| Structured comparison table across MANY papers | `alterlab-pdf-extract` |
| Convert a document to clean Markdown | `alterlab-markitdown` |
| References / DOIs / BibTeX | `alterlab-pyzotero` |
| Chat across a library of sources (self-hosted NotebookLM) | `alterlab-open-notebook` |

## Pipeline

Located extractions feed `alterlab-paper-reviewer` and literature-review workflows; escalate to
`alterlab-pdf-extract` when the task becomes a multi-paper corpus table.
