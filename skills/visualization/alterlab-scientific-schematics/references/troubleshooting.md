# Troubleshooting Common Issues

Fixes for AI generation, quality, and accessibility problems. All controls are prompt-based plus the
`--iterations` and `--doc-type` flags; there is no separate quality-check toolkit to run.

## API and Setup Issues

**Problem**: `OPENROUTER_API_KEY not found`
- Set it: `export OPENROUTER_API_KEY='sk-or-v1-...'`, or pass `--api-key`, or put it in a `.env`
  file (requires `pip install python-dotenv`).
- Verify it is exported in the same shell: `echo $OPENROUTER_API_KEY`.

**Problem**: `requests library not found`
- Install it: `pip install requests`.

**Problem**: "No image data in API response" / generation returns nothing
- Re-run with `-v` to print the raw API response structure.
- Confirm the configured image model actually supports image output. The default is
  `google/gemini-3.1-flash-image` (Nano Banana 2); set `ALTERLAB_IMAGE_MODEL` to use another
  image-capable model. A "model not found" error usually means a retired ID — check
  https://openrouter.ai/models.

**Problem**: "Quality review skipped" / log shows `"review_skipped": true` and `"final_score": null`
- The review call to `ALTERLAB_REVIEW_MODEL` (default `google/gemini-3.1-pro-preview`) failed, so
  the image was kept without a score. Re-run with `-v` to see the error, then inspect the image
  yourself or re-run once the review model responds.

## AI Generation Issues

**Problem**: Overlapping text or elements, or elements not connecting properly
- Make the prompt more specific about layout, connection points, and spacing
  (e.g. "vertical top-to-bottom flow, generous spacing, no overlapping boxes").
- Raise `--iterations 2` so the review feedback drives a second, corrected generation.

**Problem**: Quality score never reaches the threshold (stuck NEEDS_IMPROVEMENT)
- Lower the bar to match the real venue with `--doc-type` (e.g. `poster` = 7.0 vs `journal` = 8.5).
- Add the missing detail the critique calls out (labels, counts, direction) to the prompt.

## Accessibility Problems

The guidelines prompt already requests an Okabe-Ito palette, redundant encoding, and grayscale
compatibility. If the result still falls short:

**Problem**: Colors indistinguishable in grayscale
- Add explicit redundant encoding to the prompt: distinct shapes, line styles, or fill patterns
  per category, not color alone.
- Ask for higher contrast between adjacent elements.

**Problem**: Text too small when printed
- Request larger, consistent label sizes and design for the final print size.
- Re-generate at a higher target size; the guidelines ask for >=10 pt labels by default.
