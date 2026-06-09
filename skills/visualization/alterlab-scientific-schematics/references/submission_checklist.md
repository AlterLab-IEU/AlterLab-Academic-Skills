# Quick Reference Checklist

Before submitting diagrams, verify each item.

## Visual Quality
- [ ] High-quality image format (PNG from AI generation)
- [ ] No overlapping elements (visually confirm in the output)
- [ ] Adequate spacing between all components
- [ ] Clean, professional alignment
- [ ] All arrows connect properly to intended targets

## Accessibility
- [ ] Colorblind-safe palette (Okabe-Ito) used
- [ ] Works in grayscale (test: `magick diagram.png -colorspace gray gray.png`)
- [ ] Sufficient contrast between elements
- [ ] Redundant encoding where appropriate (shapes + colors)
- [ ] Checked with a colorblind simulator (e.g. Color Oracle) if color is load-bearing

## Typography and Readability
- [ ] Text minimum 7-8 pt at final size
- [ ] All elements labeled clearly and completely
- [ ] Consistent font family and sizing
- [ ] No text overlaps or cutoffs
- [ ] Units included where applicable

## Publication Standards
- [ ] Consistent styling with other figures in manuscript
- [ ] Comprehensive caption written with all abbreviations defined
- [ ] Referenced appropriately in manuscript text
- [ ] Meets journal-specific dimension requirements
- [ ] Exported in required format for journal (PDF/EPS/TIFF)

## Quality Verification
- [ ] Reviewed the `*_review_log.json` and confirmed the final score met the document-type threshold
- [ ] Visually confirmed no overlapping or cut-off elements
- [ ] Confirmed legibility in grayscale and adequate contrast
- [ ] Resolution adequate at target size (300+ DPI for print)
- [ ] Final image and review log saved together

## Documentation and Version Control
- [ ] Generation prompt and `--doc-type` recorded for future regeneration
- [ ] Review log (`*_review_log.json`) kept alongside the figure
- [ ] Git commit includes the prompt/command, the output image, and the review log
- [ ] README or comments explain how to regenerate the figure

## Final Integration Check
- [ ] Figure displays correctly in compiled manuscript
- [ ] Cross-references work (`\ref{}` points to correct figure)
- [ ] Figure number matches text citations
- [ ] Caption appears on correct page relative to figure
- [ ] No compilation warnings or errors related to figure

## Best Practices Summary

### Design Principles
1. **Clarity over complexity** - Simplify, remove unnecessary elements
2. **Consistent styling** - Use templates and style files
3. **Colorblind accessibility** - Use Okabe-Ito palette, redundant encoding
4. **Appropriate typography** - Sans-serif fonts, minimum 7-8 pt
5. **Vector format** - Always use PDF/SVG for publication

### Technical Requirements
1. **Resolution** - Vector preferred, or 300+ DPI for raster
2. **File format** - PDF for LaTeX, SVG for web, PNG as fallback
3. **Color space** - RGB for digital, CMYK for print (convert if needed)
4. **Line weights** - Minimum 0.5 pt, typical 1-2 pt
5. **Text size** - 7-8 pt minimum at final size

### Integration Guidelines
1. **Include in LaTeX** - Use `\includegraphics{}` for generated images
2. **Caption thoroughly** - Describe all elements and abbreviations
3. **Reference in text** - Explain diagram in narrative flow
4. **Maintain consistency** - Same style across all figures in paper
5. **Version control** - Keep prompts and generated images in repository
