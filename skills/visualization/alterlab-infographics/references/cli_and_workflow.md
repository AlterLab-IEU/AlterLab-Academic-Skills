# CLI Reference, Refinement Workflow, Configuration & Troubleshooting

Full command-line options, the keyless iterative-refinement loop and review criteria, research
detail, the optional AI backend, prompt and layout tips, and troubleshooting.

## Smart Iterative Refinement (keyless)

### How It Works

```
┌──────────────────────────────────────────────────────────────┐
│  0. (--research) web search -> <name>_research.json          │
│  1. Brief: generate_infographic.py "topic" --type ... -o X   │
│  2. Claude writes X.svg from the data / research file        │
│  3. Render + lint: generate_infographic.py X.svg -o X_vN.png │
│  4. Claude Reads X_vN.png, checks every number, scores it    │
│  5. figure_tools.py score -> DONE (>= threshold, early stop) │
│                           -> REVISE (fix X.svg, go to 3)     │
│                           -> STOP (3 iterations used)        │
└──────────────────────────────────────────────────────────────┘
```

No image model and no API key are used. The render step (cairosvg) reports the smallest label at
print size, text that probably overflows its box, the colours used, and whether the image is blank;
`--gray` writes a grayscale preview for the accessibility check.

### Quality Review Criteria

The reviewer — Claude from the rendered PNG on the keyless path, Gemini 3.1 Pro
(`google/gemini-3.1-pro-preview`, override with `ALTERLAB_REVIEW_MODEL`) on the AI path — scores:

1. **Visual Hierarchy & Layout** (0-2 points) — clear hierarchy, logical reading flow, balanced composition
2. **Typography & Readability** (0-2 points) — readable text, bold headlines, no overlapping
3. **Data Visualization** (0-2 points) — prominent numbers, clear charts/icons, proper labels
4. **Color & Accessibility** (0-2 points) — professional colors, sufficient contrast, colorblind-friendly
5. **Overall Impact** (0-2 points) — professional appearance, free of visual bugs, achieves communication goal

On the keyless path every number, date and name is first checked against the user's data or the
research file; a mismatch is fixed before scoring, never traded against design points.

### Review Log

`figure_tools.py score` writes the same JSON shape the AI path writes:
```json
{
  "kind": "infographic",
  "user_prompt": "5 benefits of exercise...",
  "doc_type": "marketing",
  "quality_threshold": 8.5,
  "reviewer": "Claude, from the rendered image (keyless; no review model)",
  "iterations": [
    {
      "iteration": 1,
      "image_path": "figures/exercise_v1.png",
      "source_path": "figures/exercise.svg",
      "score": 8.7,
      "needs_improvement": false,
      "critique": "Clear hierarchy; icons consistent; all five benefits verbatim"
    }
  ],
  "final_score": 8.7,
  "early_stop": true,
  "early_stop_reason": "score 8.7 meets threshold 8.5 for marketing"
}
```

## Research Integration

### Sourcing the numbers (`--research`)

When an infographic needs accurate, up-to-date data, add `--research`. On the keyless path the
brief then includes the research protocol, and Claude carries it out with web search before
drawing:

```bash
python scripts/generate_infographic.py \
  "Global renewable energy adoption rates by country" \
  -o figures/renewable_energy.png --type statistical --research
```

1. **Find 5-8 key facts** with specific numbers, percentages and dates, preferring 2023-2026
   primary sources (statistics offices, agencies, peer-reviewed papers, the original report).
2. **Record each one** in `{name}_research.json`: claim, value, unit, year, source title, URL,
   and the retrieval date.
3. **Handle disagreement**: market-size and forecast figures differ between firms; show the
   range or attribute the figure on the graphic instead of picking one silently.
4. **Use only recorded numbers** on the infographic, with a source line naming them.

### When to Use Research

**Enable research (`--research`) for:**
- Statistical infographics requiring accurate numbers
- Market data, industry statistics, or trends
- Scientific or medical information
- Current events or recent developments
- Any topic where accuracy is critical

**Skip research for:**
- Simple conceptual infographics
- Internal process documentation
- Topics where the user provides all the data

## Command-Line Reference

```bash
python scripts/generate_infographic.py [OPTIONS] PROMPT_OR_SOURCE

Arguments:
  PROMPT_OR_SOURCE          A .svg/.tex source to render, or a description (prints the brief;
                            with --backend ai, generates)

Options:
  -o, --output PATH         Output file path (.png, .pdf or .svg)
  -t, --type TYPE           Infographic type preset
  -s, --style STYLE         Industry style preset
  -p, --palette PALETTE     Colorblind-safe palette
  -b, --background COLOR    Background color (default: white)
  --doc-type TYPE           Document type for quality threshold
  --backend {code,ai}       code (default, keyless) or ai (OpenRouter, needs a key)
  --brief                   Print the design brief and exit
  --width-in INCHES         Printed width, for the font-size check
  --dpi N                   PNG resolution (default 300)
  --gray                    Also write a grayscale preview
  --iterations N            Maximum refinement iterations for --backend ai (default: 3)
  -r, --research            Keyless: add the web-search research protocol to the brief;
                            ai: gather facts with Perplexity sonar-pro first
  --api-key KEY             OpenRouter API key (--backend ai only)
  -v, --verbose             Verbose output (--backend ai)
  --list-options            List all available options

python scripts/figure_tools.py score LOG --kind infographic --doc-type T --image PNG \
    --score S --critique TEXT [--source SVG] [--prompt TEXT]
python scripts/figure_tools.py render SOURCE -o OUT [--width-in W] [--gray] [--transparent]
```

### List All Options

```bash
python scripts/generate_infographic.py --list-options
```

## Optional AI Backend (OpenRouter)

`--backend ai` sends the description to Nano Banana Pro (`google/gemini-3-pro-image`) for
generation and Gemini 3.1 Pro for review, regenerating until the threshold is met (max 3
iterations); `--research` first asks Perplexity `sonar-pro` for facts and writes
`{name}_research.json` with the cited URLs. Set the key first:

```bash
export OPENROUTER_API_KEY='your_api_key_here'   # https://openrouter.ai/keys
python scripts/generate_infographic.py "Global AI market size" -o figures/ai_market.png \
  --type statistical --research --backend ai
```

Without a key (`--api-key`, the environment, or a `.env` file) `--backend ai` exits 2 and names
the keyless route. The image model draws every number itself and can alter digits; check each
against the research sources.

### Data & Privacy

The keyless path keeps everything local except Claude's own web searches. The AI backend sends
prompts and research/infographic content to OpenRouter for generation and review, so keep
confidential, clinical, or unpublished material out of it. The key is passed to the generator
through the environment rather than the command line.

## Layout and Prompt Tips

### Be Specific About Content

✓ **Good** (specific, detailed):
```
"5 benefits of meditation: reduces stress, improves focus,
better sleep, lower blood pressure, emotional balance"
```

✗ **Avoid vague requests**:
```
"meditation infographic"
```

### Include Data Points

✓ **Good**:
```
"Market growth from $10B (2020) to $45B (2025), CAGR 35%"
```

✗ **Vague**:
```
"market is growing"
```

### Draw charts from the values

Compute bar lengths, donut angles and icon counts from the numbers (or render the chart panel
with matplotlib and place it as a local image), and print each value next to its mark so the
graphic stays exact.

## Troubleshooting

**Problem**: Text in the infographic is unreadable
- **Solution**: Cut words, raise `font-size`, and re-render; the lint reports the smallest label

**Problem**: Text runs out of its box
- **Solution**: Split it into two `<text>` lines or widen the box (the render step flags it)

**Problem**: Colors clash or are inaccessible
- **Solution**: Use `--palette wong` for data colours and check the `--gray` preview

**Problem**: Quality score stays below threshold
- **Solution**: Fix the specific critique items; after 3 iterations deliver the best version and
  list what is still short rather than lowering `--doc-type`

**Problem**: `no SVG renderer: cairosvg unavailable`
- **Solution**: Run through `uv run --with cairosvg`; install the Cairo library if it is missing

## Integration with Other Skills

- **alterlab-scientific-schematics**: technical diagrams, flowcharts, CONSORT/PRISMA, pathways
- **alterlab-generate-image**: non-infographic visual content (illustrations, photos, hero images)
- **alterlab-market-research**: infographics embedded in business reports
- **alterlab-scientific-slides**: infographic elements for presentations

## Quick Reference Checklist

Before drawing:
- [ ] Content collected from the user (or researched and recorded with sources)
- [ ] Infographic type selected (`--type`)
- [ ] Style appropriate for audience (`--style`) and a colorblind-safe palette
- [ ] Document type set for the threshold (`--doc-type`)

After rendering:
- [ ] Every number and name matches the data or research file
- [ ] No lint warnings; grayscale preview still readable
- [ ] Review recorded with `figure_tools.py score`; final score >= threshold or gaps listed
- [ ] PNG, vector copy, SVG source, research file and review log saved together
