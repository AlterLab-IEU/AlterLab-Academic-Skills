# Figures and Visual Elements for Posters

Posters are read from several feet away, so visual elements must be simple, high-contrast, and readable at a distance. This guide covers planning, generating, sizing, and integrating figures.

## Generating Figures

If a diagram or figure would aid comprehension, invoke the **alterlab-scientific-schematics** skill (diagrams/schematics) or the **alterlab-generate-image** skill (images). Figures are optional — add them only where they improve clarity.

A useful target is a roughly even balance of visuals and text (40-50% visual area). Let the content drive how many figures you need; do not pad a poster with figures for their own sake.

## Keep Each Graphic Simple

The most common failure mode for poster graphics is cramming too much into one image, which forces text to shrink below readable size. Each graphic should carry **one message**. Practical defaults:

- 3-4 key elements per graphic is plenty; split a complex diagram into several simple ones.
- Minimal text — single-word labels and big numbers read far better than sentences.
- Generous white space (aim for around half the graphic empty).
- Large fonts inside the graphic: key numbers/metrics at the largest size, labels clearly smaller but still bold.

Patterns that tend to fail and their fixes:

| Instead of | Do this |
|------------|---------|
| A 7-stage workflow | 3 high-level stages |
| A timeline with annual milestones | 3-4 key years |
| A comparison of 6 methods | Top 3, or "ours vs. best baseline" |
| Several case studies in one image | One case (or one metric) per image |
| An architecture with every layer | 3-4 high-level components |

## Reviewing a Generated Graphic

Open each figure at roughly 25% zoom (simulating viewing distance) and confirm:

- All text is legible.
- It reads as one clear idea in a couple of seconds.
- It has comfortable white space and isn't crowded.

If a graphic fails, simplify and regenerate (fewer elements, larger text, more white space) rather than shrinking it in the layout.

## Font-Size Reference (text inside graphics)

| Element | Suggested minimum | Prompt keywords |
|---------|-------------------|-----------------|
| Main numbers/metrics | 72pt+ | "huge", "very large", "poster-size" |
| Section titles | 60pt+ | "large bold", "prominent" |
| Labels/captions | 36pt+ | "readable from 6 feet", "clear labels" |
| Body text | 24pt+ | "poster-readable", "large text" |

When describing a graphic for generation, it helps to state the poster context ("for an A0 poster, readable from 6 feet"), the exact text that should appear, high contrast, and generous margins so nothing sits near the edges.

## Integrating Figures in LaTeX

```latex
\usepackage{graphicx}

% Leave margins around figures — avoid full \linewidth
\includegraphics[width=0.85\linewidth]{figure.pdf}

% Multiple subfigures for comparisons
\usepackage{subcaption}
\begin{figure}
  \begin{subfigure}{0.48\linewidth}
    \includegraphics[width=\linewidth]{fig1.pdf}
    \caption{Condition A}
  \end{subfigure}
  \begin{subfigure}{0.48\linewidth}
    \includegraphics[width=\linewidth]{fig2.pdf}
    \caption{Condition B}
  \end{subfigure}
\end{figure}
```

Figure best practices:

- Prefer vector graphics (PDF, SVG) for scalability; raster images at 300 DPI minimum at final print size.
- Keep figure styling (borders, captions, sizes) consistent across the poster.
- Group related figures together and center them within blocks.
- Never use 100% width — leave a margin so figures don't bleed to the edge.

## QR Codes

```latex
\usepackage{qrcode}

\qrcode[height=2cm]{https://github.com/username/project}

\begin{center}
  \qrcode[height=3cm]{https://doi.org/10.1234/paper}\\
  \small Scan for full paper
\end{center}
```

Use QR codes to link to the full paper, code repository, demos, or supplementary data. Keep them at least 2×2 cm and high contrast so they scan reliably.
