# Infographic Type Catalog (10 Types)

Each of the ten `--type` presets with its best use, key visual elements, and a runnable
`generate_infographic.py` example. The SKILL.md body lists the types; this is the full catalog.

## 1. Statistical/Data-Driven (`--type statistical`)

Best for: Presenting numbers, percentages, survey results, and quantitative data.

**Key Elements:** Charts (bar, pie, line, donut), large numerical callouts, data comparisons, trend indicators.

```bash
python scripts/generate_infographic.py \
  "Global internet usage 2025: 5.5 billion users (68% of population), \
   Asia Pacific 53%, Europe 15%, Americas 20%, Africa 12%" \
  -o figures/internet_stats.png --type statistical --style technology
```

## 2. Timeline (`--type timeline`)

Best for: Historical events, project milestones, company history, evolution of concepts.

**Key Elements:** Chronological flow, date markers, event nodes, connecting lines.

```bash
python scripts/generate_infographic.py \
  "History of AI: 1950 Turing Test, 1956 Dartmouth Conference, \
   1997 Deep Blue, 2016 AlphaGo, 2022 ChatGPT" \
  -o figures/ai_history.png --type timeline --style technology
```

## 3. Process/How-To (`--type process`)

Best for: Step-by-step instructions, workflows, procedures, tutorials.

**Key Elements:** Numbered steps, directional arrows, action icons, clear flow.

```bash
python scripts/generate_infographic.py \
  "How to start a podcast: 1. Choose your niche, 2. Plan content, \
   3. Set up equipment, 4. Record episodes, 5. Publish and promote" \
  -o figures/podcast_process.png --type process --style marketing
```

## 4. Comparison (`--type comparison`)

Best for: Product comparisons, pros/cons, before/after, option evaluation.

**Key Elements:** Side-by-side layout, matching categories, check/cross indicators.

```bash
python scripts/generate_infographic.py \
  "Electric vs Gas Cars: Fuel cost (lower vs higher), \
   Maintenance (less vs more), Range (improving vs established)" \
  -o figures/ev_comparison.png --type comparison --style nature
```

## 5. List/Informational (`--type list`)

Best for: Tips, facts, key points, summaries, quick reference guides.

**Key Elements:** Numbered or bulleted points, icons, clear hierarchy.

```bash
python scripts/generate_infographic.py \
  "7 Habits of Highly Effective People: Be Proactive, \
   Begin with End in Mind, Put First Things First, Think Win-Win, \
   Seek First to Understand, Synergize, Sharpen the Saw" \
  -o figures/habits.png --type list --style corporate
```

## 6. Geographic (`--type geographic`)

Best for: Regional data, demographics, location-based statistics, global trends.

**Key Elements:** Map visualization, color coding, data overlays, legend.

```bash
python scripts/generate_infographic.py \
  "Renewable energy adoption by region: Iceland 100%, Norway 98%, \
   Germany 50%, USA 22%, India 20%" \
  -o figures/renewable_map.png --type geographic --style nature
```

## 7. Hierarchical/Pyramid (`--type hierarchical`)

Best for: Organizational structures, priority levels, importance ranking.

**Key Elements:** Pyramid or tree structure, distinct levels, size progression.

```bash
python scripts/generate_infographic.py \
  "Maslow's Hierarchy: Physiological, Safety, Love/Belonging, \
   Esteem, Self-Actualization" \
  -o figures/maslow.png --type hierarchical --style education
```

## 8. Anatomical/Visual Metaphor (`--type anatomical`)

Best for: Explaining complex systems using familiar visual metaphors.

**Key Elements:** Central metaphor image, labeled parts, connection lines.

```bash
python scripts/generate_infographic.py \
  "Business as a human body: Brain=Leadership, Heart=Culture, \
   Arms=Sales, Legs=Operations, Skeleton=Systems" \
  -o figures/business_body.png --type anatomical --style corporate
```

## 9. Resume/Professional (`--type resume`)

Best for: Personal branding, CVs, portfolio highlights, professional achievements.

**Key Elements:** Photo area, skills visualization, timeline, contact info.

```bash
python scripts/generate_infographic.py \
  "UX Designer resume: Skills - User Research 95%, Wireframing 90%, \
   Prototyping 85%. Experience - 2020-2022 Junior, 2022-2025 Senior" \
  -o figures/resume.png --type resume --style technology
```

## 10. Social Media (`--type social`)

Best for: Instagram, LinkedIn, Twitter/X posts, shareable graphics.

**Key Elements:** Bold headline, minimal text, maximum impact, vibrant colors.

```bash
python scripts/generate_infographic.py \
  "Save Water, Save Life: 2.2 billion people lack safe drinking water. \
   Tips: shorter showers, fix leaks, full loads only" \
  -o figures/water_social.png --type social --style marketing
```

## Style Presets (`--style`)

| Style | Colors | Best For |
|-------|--------|----------|
| `corporate` | Navy, steel blue, gold | Business reports, finance |
| `healthcare` | Medical blue, cyan, light cyan | Medical, wellness |
| `technology` | Tech blue, slate, violet | Software, data, AI |
| `nature` | Forest green, mint, earth brown | Environmental, organic |
| `education` | Academic blue, light blue, coral | Learning, academic |
| `marketing` | Coral, teal, yellow | Social media, campaigns |
| `finance` | Navy, gold, green/red | Investment, banking |
| `nonprofit` | Warm orange, sage, sand | Social causes, charities |

```bash
# Corporate style
python scripts/generate_infographic.py \
  "Q4 Results" -o q4.png --type statistical --style corporate

# Healthcare style
python scripts/generate_infographic.py \
  "Patient Journey" -o journey.png --type process --style healthcare
```

## Colorblind-Safe Palettes (`--palette`)

| Palette | Colors | Description |
|---------|--------|-------------|
| `wong` | Orange, sky blue, green, blue, vermillion | Most widely recommended |
| `ibm` | Ultramarine, indigo, magenta, orange, gold | IBM's accessible palette |
| `tol` | Indigo, cyan, teal, green, sand, rose | Paul Tol qualitative; for many categories |

```bash
# Wong's colorblind-safe palette
python scripts/generate_infographic.py \
  "Survey results by category" -o survey.png --type statistical --palette wong
```
