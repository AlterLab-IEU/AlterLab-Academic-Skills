# Compilation, Output, and Quality Control

This reference covers compiling a poster, preventing content overflow, and the pre-print quality checklist. A helper script lives at `scripts/review_poster.sh`.

## Compilation

```bash
# Basic compilation
pdflatex poster.tex

# With bibliography
pdflatex poster.tex
bibtex poster
pdflatex poster.tex
pdflatex poster.tex

# Better font support for beamer-based posters
lualatex poster.tex
xelatex poster.tex   # Unicode and modern fonts
```

Full-page setup for each class is documented in the per-package template references
(`templates_beamerposter.md`, `templates_tikzposter.md`, `templates_baposter.md`).

## Preventing Content Overflow

Text or graphics running off the page edge is the most common poster defect. Prevent it up front:

- **Limit sections.** Around 5-6 content blocks for an A0 (e.g. Title, Introduction, Methods, Results, Conclusions). More than that tends to crowd the page.
- **Keep word count down.** Roughly 300-800 words total for an A0, 50-100 per section. If you have more, cut it or make a handout.
- **Set safe margins.** Give the document class generous outer margins (see the per-package references).
- **Never size figures at full width.** Use `width=0.85\linewidth` rather than `1.0\linewidth`.

## Overflow Check After Compilation

Check the log for overflow warnings — these mean content is cut off or extending past a boundary:

```bash
grep -i "overfull\|underfull\|badbox" poster.log
```

What they mean:

- `Overfull \hbox (15.2pt too wide)` — text/graphic is wider than its column.
- `Overfull \vbox (23.5pt too high)` — content is taller than the available space.
- `Badbox` — LaTeX is struggling to fit content within boundaries.

Then open the PDF at 100% zoom and inspect all four edges plus the gaps between columns: title and authors fully visible at the top; references, acknowledgments, and contact info intact at the bottom; no text or graphics bleeding off the left or right; and nothing crossing from one column into the next.

If you find overflow, fix it in this order:

1. **Simplify graphics** — too complex, tiny text, or too many of them.
2. **Reduce sections** — combine or drop blocks (e.g. merge Discussion into Conclusions).
3. **Cut text** — trim toward 300-500 words total.
4. **Shrink figures** — `width=\linewidth` → `width=0.85\linewidth`.
5. **Increase margins** as a last resort.

## Page-Size Verification

```bash
pdfinfo poster.pdf | grep "Page size"

# Expected:
# A0:     2384 x 3370 points (841 x 1189 mm)
# A1:     1684 x 2384 points (594 x 841 mm)
# 36x48": 2592 x 3456 points
```

## Visual Inspection Checklist (100% zoom)

**Layout and spacing**
- [ ] Content fills the page (no large empty margins)
- [ ] Consistent spacing between columns and blocks
- [ ] Elements aligned; nothing overlapping
- [ ] White space evenly distributed

**Typography**
- [ ] Title large and clearly visible (72pt+)
- [ ] Section headers readable (48-72pt)
- [ ] Body text readable (24-36pt minimum)
- [ ] No text cut off; consistent fonts; special characters render

**Visual elements**
- [ ] All figures display, none pixelated or blurry
- [ ] Captions present and readable
- [ ] Colors render correctly; logos and QR codes clear

**Content completeness**
- [ ] Title, authors, all sections, references, contact info present
- [ ] No placeholder text (Lorem ipsum, TODO)
- [ ] Citations resolved (no [?] marks); cross-references working

## Reduced-Scale Print Test

Print at ~25% of final size (an A0 fits on A4 at ~24.7%; a 36×48" fits on letter at ~25%). This simulates viewing the full poster from 8-10 feet:

- [ ] Title readable from 6 feet
- [ ] Section headers readable from 4 feet
- [ ] Body text readable from 2 feet
- [ ] Figures clear; colors accurate

## Digital Quality Checks

```bash
# Confirm all fonts are embedded (every row should show "yes")
pdffonts poster.pdf

# Check image resolution (aim for 300 DPI at final print size)
pdfimages -list poster.pdf

# Compress for email/web if the file is large (keep the original for print)
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=poster_compressed.pdf poster.pdf
```

## Accessibility

- Text/background contrast ratio ≥ 4.5:1 (WCAG AA); ≥ 7:1 for key elements (AAA). Test at https://webaim.org/resources/contrastchecker/.
- Avoid red-green combinations; add patterns or shapes alongside color.
- View through a color-blindness simulator (e.g. Coblis) to confirm no information is lost.

## Common Warnings and Fixes

```latex
% Overfull hbox (text too wide)
\usepackage{microtype}   % Better spacing
\sloppy                  % Allow slightly looser spacing
\hyphenation{long-word}  % Manual hyphenation

% Font encoding
\usepackage[T1]{fontenc}

% Image not found — set search paths
\graphicspath{{./figures/}{./images/}}
```

| Issue | Cause | Fix |
|-------|-------|-----|
| Large white margins | Margin settings | Reduce margin in documentclass |
| Content cut off | Exceeds page bounds | Recheck width/height calculations |
| Blurry images | < 300 DPI | Replace with higher-resolution images |
| Missing fonts | Not embedded | Recompile with font embedding |
| Wrong page size | Wrong paper option | Verify documentclass paper size |
| Colors look wrong | RGB vs CMYK mismatch | Convert color space for print |
| File too large | Uncompressed images | Optimize images or compress PDF |

## Print Preparation

- Export PDF/X-1a for professional printing; embed all fonts.
- Convert colors to CMYK if the printer requires it (RGB is fine for screen).
- Confirm all images are at least 300 DPI and the page size matches the spec exactly.
- Add a 3-5 mm bleed if the printer requires one.
- Use clear file naming, e.g. `LastName_Conference_Poster.pdf`, and keep a backup.
