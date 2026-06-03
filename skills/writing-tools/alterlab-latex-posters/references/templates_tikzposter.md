# tikzposter Templates and Setup

tikzposter is a modern, flexible class with TikZ integration, built-in color themes, and layout templates. Best for colorful, modern designs with custom graphics.

A ready-to-use starting file lives at `assets/tikzposter_template.tex`. The blocks below are reference snippets for common tasks.

## Full-Page Document Setup

```latex
\documentclass[
  25pt,                      % Font scaling
  a0paper,                   % Paper size
  portrait,                  % Orientation
  margin=10mm,               % Outer margins (minimal)
  innermargin=15mm,          % Space inside blocks
  blockverticalspace=15mm,   % Space between blocks
  colspace=15mm,             % Space between columns
  subcolspace=8mm            % Space between subcolumns
]{tikzposter}
```

## Theme Selection

```latex
\usetheme{Rays}
\usecolorstyle{Denmark}
```

## Column and Block Layout

```latex
\documentclass[25pt, a0paper, portrait]{tikzposter}

\begin{document}
\maketitle

\begin{columns}
\column{0.5}

\block{Introduction}{
  \centering
  \includegraphics[width=0.85\linewidth]{figures/intro_visual.png}

  \vspace{0.5em}
  Brief context text here (2-3 sentences max).
}

\block{Methods}{
  \centering
  \includegraphics[width=0.9\linewidth]{figures/methods_flowchart.png}
}

\column{0.5}

\block{Results}{
  \begin{minipage}{0.48\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/result_1.png}
  \end{minipage}
  \hfill
  \begin{minipage}{0.48\linewidth}
    \centering
    \includegraphics[width=\linewidth]{figures/result_2.png}
  \end{minipage}

  \vspace{0.5em}
  Key findings in 3-4 bullet points.
}

\block{Conclusions}{
  \centering
  \includegraphics[width=0.8\linewidth]{figures/conclusions_graphic.png}
}

\end{columns}
\end{document}
```

## Figures with Captions

```latex
\block{Results}{
  \begin{tikzfigure}
    \includegraphics[width=0.9\linewidth]{results.png}
  \end{tikzfigure}
}
```

## Fixing Large White Margins

```latex
\documentclass[..., margin=5mm, innermargin=10mm]{tikzposter}
```

## Distributing Vertical Space

```latex
\block{Introduction}{...}
\vfill
\block{Methods}{...}
\vfill
\block{Results}{...}

% Or manually adjust spacing between specific blocks
\vspace{1cm}
```
