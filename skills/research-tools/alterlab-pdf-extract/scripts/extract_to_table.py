#!/usr/bin/env python3
"""
extract_to_table.py — the free Elicit-columns analog.

Ingest N PDFs (or any MarkItDown-supported document), convert each to Markdown,
then build a per-paper evidence table with USER-DEFINED columns. One row per
document; one column per question/attribute you want pulled from every paper.
Output as CSV and/or a GitHub-flavored Markdown table.

Conversion is routed through Microsoft MarkItDown (see the
alterlab-markitdown skill) so every input format is normalized to clean,
token-efficient Markdown before any column is extracted.

Two extraction backends:
  * heuristic (default, no API, fully offline): for each column, locate the most
    relevant Markdown section/sentences by LITERAL keyword overlap with the column
    spec and emit a short evidence snippet. Deterministic and free — good for a
    first pass, screening, and for reproducible tests. Matching is lexical, not
    semantic: phrase columns as 'Label:question' using the words the papers
    actually use (a bare label like "Sample size" won't match "240 participants").
  * llm (optional): hand the converted Markdown + the column questions to a model
    via an OpenAI-compatible endpoint (e.g. OpenRouter) for a precise structured
    answer per column. The model ID follows the ALTERLAB_MODEL convention
    (skills/core/shared/model_env.md): $ALTERLAB_MODEL or the dated default.

The script is import-light: MarkItDown and the OpenAI client are imported lazily
so the file compiles and `--help` works without them installed.

Examples
--------
  # Heuristic backend — phrase columns so the question carries paper vocabulary:
  uv run python extract_to_table.py papers/*.pdf \
      --column "Sample size:how many participants were enrolled" \
      --column "Main finding:primary result reported" \
      --format md -o evidence.md

  # Columns with explicit extraction questions, CSV out:
  uv run python extract_to_table.py a.pdf b.pdf \
      --column "n=:how many participants" \
      --column "effect:what was the main reported effect" \
      --format csv -o table.csv

  # LLM-backed precise extraction (needs OPENROUTER_API_KEY):
  uv run python extract_to_table.py lit/*.pdf \
      --columns "Population" "Intervention" "Outcome" --backend llm
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Optional

# AlterLab model convention — default reviewed 2026-06-06; override via ALTERLAB_MODEL.
# See skills/core/shared/model_env.md before changing the default. OpenRouter needs
# the "provider/" prefix, so the default is the dated Anthropic ID with that prefix.
DEFAULT_MODEL = "anthropic/claude-opus-4-8"


def alterlab_model() -> str:
    """Return the model ID: $ALTERLAB_MODEL if set/non-empty, else the dated default."""
    return os.environ.get("ALTERLAB_MODEL") or DEFAULT_MODEL


_STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "is", "are", "was", "were", "for",
    "and", "or", "what", "how", "many", "much", "did", "do", "this", "that",
    "with", "on", "as", "by", "be", "it", "from", "at", "which", "main",
}


@dataclass
class Column:
    """A user-defined table column: a label plus the question that drives extraction."""

    label: str
    question: str
    keywords: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, spec: str) -> "Column":
        """Parse a 'label:question' spec. If no ':' present, label == question."""
        if ":" in spec:
            label, question = spec.split(":", 1)
            label, question = label.strip(), question.strip()
        else:
            label = question = spec.strip()
        if not label:
            raise ValueError(f"Empty column label in spec: {spec!r}")
        if not question:
            question = label
        return cls(label=label, question=question, keywords=_tokens(label + " " + question))


def _tokens(text: str) -> list[str]:
    """Lowercase content tokens (>=3 chars, not stopwords) for keyword overlap."""
    words = re.findall(r"[A-Za-z0-9%][A-Za-z0-9%\-]+", text.lower())
    return [w for w in words if len(w) >= 3 and w not in _STOPWORDS]


def convert_to_markdown(path: Path) -> str:
    """Route a document through MarkItDown to clean Markdown text.

    Imported lazily so the module compiles without markitdown installed.
    """
    try:
        from markitdown import MarkItDown
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "markitdown is required for conversion. Install it with:\n"
            "  uv pip install 'markitdown[all]'\n"
            "(See the alterlab-markitdown skill for details.)"
        ) from exc

    md = MarkItDown()
    result = md.convert(str(path))
    return result.text_content or ""


def _split_sentences(markdown: str) -> list[str]:
    """Crude sentence/line splitter that keeps Markdown headings as boundaries."""
    chunks: list[str] = []
    for line in markdown.splitlines():
        line = line.strip()
        if not line:
            continue
        # Split prose lines into sentences; keep headings/bullets whole.
        if line.startswith("#") or line.startswith(("-", "*", "|")):
            chunks.append(line.lstrip("#-*| ").strip())
        else:
            chunks.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())
    return [c for c in chunks if c]


def extract_heuristic(markdown: str, column: Column, max_chars: int = 240) -> str:
    """Pick the sentence with the highest keyword overlap with the column spec.

    Deterministic, offline, free. Returns a trimmed evidence snippet or "" if no
    sentence shares any keyword with the column.
    """
    if not column.keywords:
        return ""
    sentences = _split_sentences(markdown)
    kw = set(column.keywords)
    best_score = 0
    best: str = ""
    for sent in sentences:
        toks = set(_tokens(sent))
        score = len(kw & toks)
        # Light bonus for numeric content when the question is quantitative.
        if score and re.search(r"\d", sent) and any(c.isdigit() or c == "%" for c in column.question):
            score += 1
        if score > best_score:
            best_score, best = score, sent
    if not best:
        return ""
    snippet = re.sub(r"\s+", " ", best).strip()
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 1].rstrip() + "…"
    return snippet


def extract_llm(markdown: str, columns: list[Column], *, model: str, source: str) -> dict[str, str]:
    """Ask an LLM (OpenAI-compatible endpoint) to fill every column at once.

    Imported lazily. Requires OPENROUTER_API_KEY (or OPENAI_API_KEY + OPENAI_BASE_URL).
    Returns {label: answer}. Falls back to "" for any column the model omits.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "The llm backend needs the openai client: uv pip install openai"
        ) from exc

    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "The llm backend needs OPENROUTER_API_KEY (or OPENAI_API_KEY) in the environment."
        )
    base_url = os.environ.get("OPENAI_BASE_URL") or "https://openrouter.ai/api/v1"

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Cap context so a long paper does not blow the prompt budget.
    body = markdown[:24000]
    questions = "\n".join(f"- {c.label}: {c.question}" for c in columns)
    prompt = (
        "You are extracting a structured evidence table from one paper. "
        "For each requested column, answer ONLY from the paper text below, concisely "
        '(a phrase, number, or one sentence). If the paper does not say, answer "N/A". '
        "Reply as 'Label: answer' lines, one per column, nothing else.\n\n"
        f"Columns:\n{questions}\n\nPaper ({source}):\n{body}"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    text = resp.choices[0].message.content or ""
    return _parse_llm_answers(text, columns)


def _parse_llm_answers(text: str, columns: list[Column]) -> dict[str, str]:
    """Parse 'Label: answer' lines back into a {label: answer} dict."""
    answers = {c.label: "" for c in columns}
    label_lower = {c.label.lower(): c.label for c in columns}
    for line in text.splitlines():
        if ":" not in line:
            continue
        raw_label, value = line.split(":", 1)
        key = raw_label.strip().lstrip("-*# ").strip().lower()
        if key in label_lower:
            answers[label_lower[key]] = value.strip()
    return answers


def build_rows(
    paths: list[Path], columns: list[Column], *, backend: str, model: str, verbose: bool
) -> list[dict[str, str]]:
    """Convert each document and extract every column. One row dict per document."""
    rows: list[dict[str, str]] = []
    for path in paths:
        if verbose:
            print(f"Converting & extracting: {path}", file=sys.stderr)
        try:
            markdown = convert_to_markdown(path)
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001 - surface per-file failure, keep going
            print(f"  ! failed to convert {path}: {exc}", file=sys.stderr)
            row = {"Source": path.name}
            row.update({c.label: "ERROR" for c in columns})
            rows.append(row)
            continue

        row: dict[str, str] = {"Source": path.name}
        if backend == "llm":
            answers = extract_llm(markdown, columns, model=model, source=path.name)
            for c in columns:
                row[c.label] = answers.get(c.label, "")
        else:
            for c in columns:
                row[c.label] = extract_heuristic(markdown, c)
        rows.append(row)
    return rows


def _md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(rows: list[dict[str, str]], columns: list[Column]) -> str:
    """Render rows as a GitHub-flavored Markdown table."""
    headers = ["Source"] + [c.label for c in columns]
    out = StringIO()
    out.write("| " + " | ".join(headers) + " |\n")
    out.write("| " + " | ".join("---" for _ in headers) + " |\n")
    for row in rows:
        cells = [_md_escape(str(row.get(h, ""))) for h in headers]
        out.write("| " + " | ".join(cells) + " |\n")
    return out.getvalue()


def render_csv(rows: list[dict[str, str]], columns: list[Column]) -> str:
    """Render rows as CSV text."""
    headers = ["Source"] + [c.label for c in columns]
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({h: row.get(h, "") for h in headers})
    return out.getvalue()


def parse_columns(args: argparse.Namespace) -> list[Column]:
    """Collect columns from both --columns and repeated --column flags."""
    specs: list[str] = []
    if args.columns:
        specs.extend(args.columns)
    if args.column:
        specs.extend(args.column)
    if not specs:
        raise SystemExit("No columns given. Use --columns or --column (see --help).")
    columns = [Column.parse(s) for s in specs]
    seen: set[str] = set()
    for c in columns:
        if c.label in seen:
            raise SystemExit(f"Duplicate column label: {c.label!r}")
        seen.add(c.label)
    return columns


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a user-defined evidence table from N PDFs (Elicit-columns analog).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pdfs", nargs="+", type=Path, help="Input documents (PDF or any MarkItDown format).")
    parser.add_argument(
        "--columns", nargs="+",
        help="Column specs, each 'Label' or 'Label:question'. Space-separated list.",
    )
    parser.add_argument(
        "--column", action="append",
        help="A single column spec 'Label:question'. Repeatable; combines with --columns.",
    )
    parser.add_argument(
        "--backend", choices=["heuristic", "llm"], default="heuristic",
        help="heuristic (offline, free, default) or llm (precise, needs API key).",
    )
    parser.add_argument(
        "--format", choices=["md", "csv"], default="md",
        help="Output format: Markdown table (md) or CSV (csv).",
    )
    parser.add_argument("-o", "--output", type=Path, help="Write to this file instead of stdout.")
    parser.add_argument(
        "--model", default=None,
        help="Override the LLM model ID (else $ALTERLAB_MODEL or the dated default).",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Progress to stderr.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    columns = parse_columns(args)
    model = args.model or alterlab_model()

    missing = [p for p in args.pdfs if not p.exists()]
    if missing:
        raise SystemExit("Input(s) not found: " + ", ".join(str(p) for p in missing))

    rows = build_rows(
        args.pdfs, columns, backend=args.backend, model=model, verbose=args.verbose
    )

    text = render_csv(rows, columns) if args.format == "csv" else render_markdown(rows, columns)

    if args.output:
        args.output.write_text(text, encoding="utf-8")
        if args.verbose:
            print(f"Wrote {len(rows)} row(s) x {len(columns)} column(s) -> {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
