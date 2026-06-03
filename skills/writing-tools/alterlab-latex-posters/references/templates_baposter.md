# baposter Templates and Setup

baposter uses a box-based layout system with automatic spacing and positioning. Best for structured, professional multi-column layouts with consistent spacing.

A ready-to-use starting file lives at `assets/baposter_template.tex`. The blocks below are reference snippets for common tasks.

## Full-Page Document Setup

```latex
\documentclass[a0paper,portrait,fontscale=0.285]{baposter}

\begin{poster}{
  grid=false,
  columns=3,
  colspacing=1.5em,              % Space between columns
  eyecatcher=true,
  background=plain,
  bgColorOne=white,
  borderColor=blue!50,
  headerheight=0.12\textheight,  % 12% for header
  textborder=roundedleft,
  headerborder=closed,
  boxheaderheight=2em            % Consistent box header heights
}
% Content here
\end{poster}
```

## Header Boxes

```latex
\headerbox{Methods}{name=methods,column=0,row=0}{
  \centering
  \includegraphics[width=0.95\linewidth]{figures/methods_flowchart.png}
}

\headerbox{Results}{name=results,column=1,row=0}{
  \includegraphics[width=\linewidth]{figures/comparison_chart.png}
  \vspace{0.3em}

  Key finding: Our method achieves 92% accuracy.
}
```

## Theme / Color Selection

```latex
\begin{poster}{
  background=plain,
  bgColorOne=white,
  headerColorOne=blue!70,
  textborder=rounded
}
```

## Fixing Large White Margins

```latex
\documentclass[a0paper, margin=5mm]{baposter}
```

## Debugging Page Boundaries

When content extends beyond the page, verify the width calculation:

```latex
% For 3 columns with spacing:
% Total = 3×columnwidth + 2×colspace + 2×margins
% Ensure this equals \paperwidth

% Add a visible page boundary to debug
\usepackage{eso-pic}
\AddToShipoutPictureBG{
  \AtPageLowerLeft{
    \put(0,0){\framebox(\LenToUnit{\paperwidth},\LenToUnit{\paperheight}){}}
  }
}
```
