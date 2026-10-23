#!/usr/bin/env python3
"""
Project scaffold for the keyless Denario-style pipeline (Claude does every agent role).

Creates the same layout the denario package uses, so a project can later be handed to the
package unchanged, and compiles the paper with a local LaTeX install. No API key, standard
library only.

  <dir>/input_files/data_description.md   stage 0: what data and tools exist
  <dir>/input_files/idea.md               stage 1: idea (after maker/critic rounds)
  <dir>/input_files/methods.md            stage 2: methodology
  <dir>/input_files/results.md            stage 3: results written from the analysis run
  <dir>/input_files/plots/                figures produced by the analysis code
  <dir>/analysis/                         analysis scripts (run with uv run / python)
  <dir>/paper/paper.tex                   stage 4: journal-formatted LaTeX

Usage:
  python research_project.py init ./my_research --journal aps [--data-description notes.md]
  python research_project.py status ./my_research
  python research_project.py compile ./my_research
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

STAGES = ["data_description.md", "idea.md", "methods.md", "results.md"]
TODO = "<!-- TODO -->"

PREAMBLES = {
    # revtex4-2 (APS) ships with TeX Live
    "none": "\\documentclass[11pt]{article}\n\\usepackage{graphicx,amsmath,hyperref}\n",
    "aps": "\\documentclass[aps,prd,twocolumn,superscriptaddress]{revtex4-2}\n\\usepackage{graphicx,amsmath,hyperref}\n",
}
# These need the venue's own class/style file; paper.tex starts as plain article
VENUE_FILES = {"aas": "AASTeX (aastex631.cls plus epsf.sty, journals.aas.org)",
               "jhep": "jheppub.sty from the JHEP author instructions", "icml": "icml20xx.sty from the ICML site",
               "neurips": "neurips_20xx.sty from the NeurIPS site", "pasj": "pasj01.cls from PASJ"}

BODY = r"""
\begin{document}

\title{%(title)s}
%(author)s
%(abstract_open)s
%% Written from input_files/idea.md, methods.md and results.md.
TODO abstract.
%(abstract_close)s
%(maketitle)s

\section{Introduction}
TODO

\section{Data}
TODO %% from input_files/data_description.md

\section{Methods}
TODO %% from input_files/methods.md

\section{Results}
TODO %% from input_files/results.md; figures from input_files/plots/

\section{Discussion and limitations}
TODO

\section*{AI assistance}
The idea, methodology, analysis code and draft text were produced with an AI assistant
following a Denario-style pipeline and were checked by the authors, who take responsibility
for the content.

\bibliographystyle{%(bst)s}
%% \bibliography{references}
\end{document}
"""


def init(d: Path, journal: str, desc: Path | None) -> None:
    inp = d / "input_files"
    (inp / "plots").mkdir(parents=True, exist_ok=True)
    (d / "analysis").mkdir(exist_ok=True)
    (d / "paper").mkdir(exist_ok=True)
    texts = {
        "data_description.md": desc.read_text() if desc else f"{TODO}\n# Data description\n",
        "idea.md": f"{TODO}\n# Idea\n\n## Candidate ideas and critique rounds\n\n## Selected idea\n",
        "methods.md": f"{TODO}\n# Methods\n",
        "results.md": f"{TODO}\n# Results\n",
    }
    for name, text in texts.items():
        p = inp / name
        if not p.exists():
            p.write_text(text)
    key = journal if journal in PREAMBLES else "none"
    if journal in VENUE_FILES:
        print(f"note: {journal} needs {VENUE_FILES[journal]}; paper.tex uses plain article until "
              "that file sits next to it", file=sys.stderr)
    aps = key == "aps"
    tex = PREAMBLES[key] + BODY % {
        "title": "TODO title",
        "author": "\\author{TODO author}\n\\affiliation{TODO affiliation}" if aps else "\\author{TODO author}",
        # revtex takes the abstract before \maketitle; article needs \maketitle first
        "abstract_open": "\\begin{abstract}" if aps else "\\maketitle\n\\begin{abstract}",
        "abstract_close": "\\end{abstract}",
        "maketitle": "\\maketitle" if aps else "",
        "bst": "apsrev4-2" if aps else "unsrt",
    }
    paper = d / "paper" / "paper.tex"
    if not paper.exists():
        paper.write_text(tex)
    print(f"initialised {d} (journal: {journal})")


def status(d: Path) -> int:
    missing = 0
    for name in STAGES:
        p = d / "input_files" / name
        state = "missing" if not p.exists() else ("todo" if TODO in p.read_text() else "done")
        missing += state != "done"
        print(f"{name:22} {state}")
    plots = list((d / "input_files" / "plots").glob("*"))
    print(f"{'plots/':22} {len(plots)} file(s)")
    tex = d / "paper" / "paper.tex"
    print(f"{'paper/paper.tex':22} {'todo' if not tex.exists() or 'TODO' in tex.read_text() else 'done'}")
    return 0 if missing == 0 else 2


def compile_paper(d: Path) -> int:
    engine = shutil.which("pdflatex") or shutil.which("xelatex")
    if not engine:
        print("error: no pdflatex/xelatex on PATH; the .tex source is still the deliverable", file=sys.stderr)
        return 1
    paper = d / "paper"
    cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", "paper.tex"]
    for i in range(2):
        r = subprocess.run(cmd, cwd=paper, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], file=sys.stderr)
            print("error: LaTeX failed (log above)", file=sys.stderr)
            return 1
        if i == 0 and (paper / "references.bib").exists() and shutil.which("bibtex"):
            subprocess.run(["bibtex", "paper"], cwd=paper, capture_output=True)
    print(f"wrote {paper / 'paper.pdf'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Scaffold and compile a keyless Denario-style research project")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("dir")
    p.add_argument("--journal", default="none", choices=["none", "aps", "aas", "jhep", "icml", "neurips", "pasj"])
    p.add_argument("--data-description", type=Path)
    sub.add_parser("status").add_argument("dir")
    sub.add_parser("compile").add_argument("dir")
    a = ap.parse_args(argv)
    d = Path(a.dir)
    if a.cmd == "init":
        init(d, a.journal, a.data_description)
        return 0
    if a.cmd == "status":
        return status(d)
    return compile_paper(d)


if __name__ == "__main__":
    sys.exit(main())
