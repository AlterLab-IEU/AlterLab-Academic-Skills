# CLI Reference, Refinement Workflow, Configuration & Troubleshooting

Full command-line options, the smart iterative-refinement loop and review criteria,
research integration detail, configuration, prompt-engineering tips, and troubleshooting.

## Smart Iterative Refinement

### How It Works

```
┌─────────────────────────────────────────────────────┐
│  1. Generate infographic with Nano Banana Pro       │
│                    ↓                                │
│  2. Review quality with Gemini 3 Pro                │
│                    ↓                                │
│  3. Score >= threshold?                             │
│       YES → DONE! (early stop)                      │
│       NO  → Improve prompt, go to step 1            │
│                    ↓                                │
│  4. Repeat until quality met OR max iterations      │
└─────────────────────────────────────────────────────┘
```

### Quality Review Criteria

Gemini 3 Pro evaluates each infographic on:

1. **Visual Hierarchy & Layout** (0-2 points) — clear hierarchy, logical reading flow, balanced composition
2. **Typography & Readability** (0-2 points) — readable text, bold headlines, no overlapping
3. **Data Visualization** (0-2 points) — prominent numbers, clear charts/icons, proper labels
4. **Color & Accessibility** (0-2 points) — professional colors, sufficient contrast, colorblind-friendly
5. **Overall Impact** (0-2 points) — professional appearance, free of visual bugs, achieves communication goal

### Review Log

Each generation produces a JSON review log:
```json
{
  "user_prompt": "5 benefits of exercise...",
  "infographic_type": "list",
  "style": "healthcare",
  "doc_type": "marketing",
  "quality_threshold": 8.5,
  "iterations": [
    {
      "iteration": 1,
      "image_path": "figures/exercise_v1.png",
      "score": 8.7,
      "needs_improvement": false,
      "critique": "SCORE: 8.7\nSTRENGTHS:..."
    }
  ],
  "final_score": 8.7,
  "early_stop": true,
  "early_stop_reason": "Quality score 8.7 meets threshold 8.5"
}
```

## Research Integration

### Automatic Data Gathering (`--research`)

When creating infographics that require accurate, up-to-date data, use the `--research` flag to automatically gather facts and statistics using **Perplexity Sonar Pro**.

```bash
# Research and generate statistical infographic
python scripts/generate_infographic.py \
  "Global renewable energy adoption rates by country" \
  -o figures/renewable_energy.png --type statistical --research

# Research for timeline infographic
python scripts/generate_infographic.py \
  "History of artificial intelligence breakthroughs" \
  -o figures/ai_history.png --type timeline --research

# Research for comparison infographic
python scripts/generate_infographic.py \
  "Electric vehicles vs hydrogen vehicles comparison" \
  -o figures/ev_hydrogen.png --type comparison --research
```

### What Research Provides

1. **Gathers Key Facts**: 5-8 relevant facts and statistics about the topic
2. **Provides Context**: Background information for accurate representation
3. **Finds Data Points**: Specific numbers, percentages, and dates
4. **Cites Sources**: Mentions major studies or sources
5. **Prioritizes Recency**: Focuses on 2023-2026 information

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
- Topics where you provide all the data in the prompt
- Speed-critical generation

### Research Output

When research is enabled, additional files are created:
- `{name}_research.json` - Raw research data and sources
- Research content is automatically incorporated into the infographic prompt

## Command-Line Reference

```bash
python scripts/generate_infographic.py [OPTIONS] PROMPT

Arguments:
  PROMPT                    Description of the infographic content

Options:
  -o, --output PATH         Output file path (required)
  -t, --type TYPE           Infographic type preset
  -s, --style STYLE         Industry style preset
  -p, --palette PALETTE     Colorblind-safe palette
  -b, --background COLOR    Background color (default: white)
  --doc-type TYPE           Document type for quality threshold
  --iterations N            Maximum refinement iterations (default: 3)
  --api-key KEY             OpenRouter API key
  -v, --verbose             Verbose output
  --list-options            List all available options
```

### List All Options

```bash
python scripts/generate_infographic.py --list-options
```

## Configuration

### API Key Setup

Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY='your_api_key_here'
```

Get an API key at: https://openrouter.ai/keys

### Data & Privacy

This skill sends your prompts and research/infographic content to a third-party API (OpenRouter) for generation and quality review. Avoid sending confidential, clinical, or unpublished material. The OpenRouter API key is read from the environment (`OPENROUTER_API_KEY`).

## Prompt Engineering Tips

### Be Specific About Content

✓ **Good prompts** (specific, detailed):
```
"5 benefits of meditation: reduces stress, improves focus,
better sleep, lower blood pressure, emotional balance"
```

✗ **Avoid vague prompts**:
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

### Specify Visual Elements

✓ **Good**:
```
"Timeline showing 5 milestones with icons for each event"
```

## Troubleshooting

**Problem**: Text in infographic is unreadable
- **Solution**: Reduce text content; use --type to specify layout type

**Problem**: Colors clash or are inaccessible
- **Solution**: Use `--palette wong` for colorblind-safe colors

**Problem**: Quality score too low
- **Solution**: Increase iterations with `--iterations 3`; use more specific prompt

**Problem**: Wrong infographic type generated
- **Solution**: Always specify `--type` flag for consistent results

## Integration with Other Skills

- **alterlab-scientific-schematics**: technical diagrams, flowcharts, CONSORT/PRISMA, pathways
- **alterlab-generate-image**: non-infographic visual content (illustrations, photos, hero images)
- **alterlab-market-research**: infographics embedded in business reports
- **alterlab-scientific-slides**: infographic elements for presentations

## Quick Reference Checklist

Before generating:
- [ ] Clear, specific content description
- [ ] Infographic type selected (`--type`)
- [ ] Style appropriate for audience (`--style`)
- [ ] Output path specified (`-o`)
- [ ] API key configured

After generating:
- [ ] Review the generated image
- [ ] Check the review log for scores
- [ ] Regenerate with more specific prompt if needed
