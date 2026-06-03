# beamerposter Templates and Setup

beamerposter extends the Beamer presentation class for large-format posters. Best for traditional academic posters and institutional branding when you already know Beamer.

A ready-to-use starting file lives at `assets/beamerposter_template.tex`. The blocks below are reference snippets for common tasks.

## Full-Page Document Setup

```latex
\documentclass[final,t]{beamer}
\usepackage[size=a0,scale=1.4,orientation=portrait]{beamerposter}

% Remove default beamer margins
\setbeamersize{text margin left=0mm, text margin right=0mm}

% Use geometry for precise control
\usepackage[margin=10mm]{geometry}  % 10mm margins all around

% Remove navigation symbols
\setbeamertemplate{navigation symbols}{}

% Remove footline and headline if not needed
\setbeamertemplate{footline}{}
\setbeamertemplate{headline}{}
```

## Theme Selection

```latex
\usetheme{Berlin}
\usecolortheme{beaver}
```

## Typography

```latex
% Sans-serif fonts recommended for posters
\usepackage{helvet}      % Helvetica
\usepackage{avant}       % Avant Garde
\usepackage{sfmath}      % Sans-serif math fonts
\renewcommand{\familydefault}{\sfdefault}

% Hierarchy sizing
\setbeamerfont{title}{size=\VeryHuge}
\setbeamerfont{author}{size=\Large}
\setbeamerfont{institute}{size=\normalsize}
```

## Fixing Large White Margins

```latex
\setbeamersize{text margin left=5mm, text margin right=5mm}
```

## Compilation

```bash
pdflatex poster.tex
# Better font support:
lualatex poster.tex
xelatex poster.tex   # Unicode and modern fonts
```
