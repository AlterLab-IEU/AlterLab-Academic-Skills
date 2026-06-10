# Scientific Schematics - Nano Banana 2

**Generate any scientific diagram by describing it in natural language.**

Nano Banana 2 creates publication-quality diagrams automatically - no coding, no templates, no manual drawing required.

## Quick Start

### Generate Any Diagram

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY='your_api_key_here'

# Generate any scientific diagram
python scripts/generate_schematic.py "CONSORT participant flow diagram" -o figures/consort.png

# Neural network architecture
python scripts/generate_schematic.py "Transformer encoder-decoder architecture" -o figures/transformer.png

# Biological pathway
python scripts/generate_schematic.py "MAPK signaling pathway" -o figures/pathway.png
```

### What You Get

- **Up to two iterations** (v1, v2) with progressive refinement
- **Automatic quality review** after each iteration
- **Detailed review log** with scores and critiques (JSON format)
- **Publication-ready images** following scientific standards

## Features

### Smart Iterative Refinement Process

1. **Generation 1**: Create initial diagram from your description
2. **Review 1**: Gemini 3.1 Pro Preview evaluates clarity, labels, accuracy, accessibility
3. **Stop early** if the score meets the document-type threshold (no extra API calls)
4. **Generation 2** (only if below threshold): Improve based on critique
5. **Review 2**: Second evaluation; this is the final version (max 2 iterations)

### Automatic Quality Standards

All diagrams automatically follow:
- Clean white/light background
- High contrast for readability
- Clear labels (minimum 10pt font)
- Professional typography
- Colorblind-friendly colors
- Proper spacing between elements
- Scale bars, legends, axes where appropriate

## Installation

### For AI Generation

```bash
# Get OpenRouter API key
# Visit: https://openrouter.ai/keys

# Set environment variable
export OPENROUTER_API_KEY='sk-or-v1-...'

# Or add to .env file
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env

# Install Python dependencies (if not already installed)
pip install requests
```

## Usage Examples

### Example 1: CONSORT Flowchart

```bash
python scripts/generate_schematic.py \
  "CONSORT participant flow diagram for RCT. \
   Assessed for eligibility (n=500). \
   Excluded (n=150): age<18 (n=80), declined (n=50), other (n=20). \
   Randomized (n=350) into Treatment (n=175) and Control (n=175). \
   Lost to follow-up: 15 and 10 respectively. \
   Final analysis: 160 and 165." \
  -o figures/consort.png
```

**Output:**
- `figures/consort_v1.png` - Initial generation
- `figures/consort_v2.png` - After first review (only if v1 was below threshold)
- `figures/consort.png` - Copy of the final accepted version
- `figures/consort_review_log.json` - Detailed review log

### Example 2: Neural Network Architecture

```bash
python scripts/generate_schematic.py \
  "Transformer architecture with encoder on left (input embedding, \
   positional encoding, multi-head attention, feed-forward) and \
   decoder on right (masked attention, cross-attention, feed-forward). \
   Show cross-attention connection from encoder to decoder." \
  -o figures/transformer.png \
  --iterations 2
```

### Example 3: Biological Pathway

```bash
python scripts/generate_schematic.py \
  "MAPK signaling pathway: EGFR receptor → RAS → RAF → MEK → ERK → nucleus. \
   Label each step with phosphorylation. Use different colors for each kinase." \
  -o figures/mapk.png
```

### Example 4: System Architecture

```bash
python scripts/generate_schematic.py \
  "IoT system block diagram: sensors (bottom) → microcontroller → \
   WiFi module and display (middle) → cloud server → mobile app (top). \
   Label all connections with protocols." \
  -o figures/iot_system.png
```

## Command-Line Options

```bash
python scripts/generate_schematic.py [OPTIONS] "description" -o output.png

Options:
  --iterations N          Number of AI refinement iterations (default: 2, max: 2)
  --api-key KEY          OpenRouter API key (or use env var)
  -v, --verbose          Verbose output
  -h, --help             Show help message
```

## Python API

```python
from scripts.generate_schematic_ai import ScientificSchematicGenerator

# Initialize
generator = ScientificSchematicGenerator(
    api_key="your_key",
    verbose=True
)

# Generate with iterative refinement
results = generator.generate_iterative(
    user_prompt="CONSORT flowchart",
    output_path="figures/consort.png",
    iterations=2
)

# Access results
print(f"Final score: {results['final_score']}/10")
print(f"Final image: {results['final_image']}")

# Review iterations
for iteration in results['iterations']:
    print(f"Iteration {iteration['iteration']}: {iteration['score']}/10")
    print(f"Critique: {iteration['critique']}")
```

## Prompt Engineering Tips

### Be Specific About Layout
✓ "Flowchart with vertical flow, top to bottom"  
✓ "Architecture diagram with encoder on left, decoder on right"  
✗ "Make a diagram" (too vague)

### Include Quantitative Details
✓ "Neural network: input (784), hidden (128), output (10)"  
✓ "Flowchart: n=500 screened, n=150 excluded, n=350 randomized"  
✗ "Some numbers" (not specific)

### Specify Visual Style
✓ "Minimalist block diagram with clean lines"  
✓ "Detailed biological pathway with protein structures"  
✓ "Technical schematic with engineering notation"

### Request Specific Labels
✓ "Label all arrows with activation/inhibition"  
✓ "Include layer dimensions in each box"  
✓ "Show time progression with timestamps"

### Mention Color Requirements
✓ "Use colorblind-friendly colors"  
✓ "Grayscale-compatible design"  
✓ "Color-code by function: blue=input, green=processing, red=output"

## Review Log Format

Each generation produces a JSON review log:

```json
{
  "user_prompt": "CONSORT participant flow diagram...",
  "doc_type": "journal",
  "quality_threshold": 8.5,
  "iterations": [
    {
      "iteration": 1,
      "image_path": "figures/consort_v1.png",
      "prompt": "Full generation prompt...",
      "critique": "SCORE: 7.5. Issues: font too small...",
      "score": 7.5,
      "needs_improvement": true,
      "success": true
    },
    {
      "iteration": 2,
      "image_path": "figures/consort_v2.png",
      "score": 8.5,
      "needs_improvement": false,
      "critique": "Much improved. Publication ready."
    }
  ],
  "final_image": "figures/consort_v2.png",
  "final_score": 8.5,
  "success": true,
  "early_stop": false
}
```

## Why Use Nano Banana 2

**Simply describe what you want - Nano Banana 2 creates it:**

- ✓ **Fast**: Results in minutes
- ✓ **Easy**: Natural language descriptions (no coding)
- ✓ **Quality**: Automatic review and refinement
- ✓ **Universal**: Works for all diagram types
- ✓ **Publication-ready**: High-quality output immediately

**Just describe your diagram, and it's generated automatically.**

## Troubleshooting

### API Key Issues

```bash
# Check if key is set
echo $OPENROUTER_API_KEY

# Set temporarily
export OPENROUTER_API_KEY='your_key'

# Set permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENROUTER_API_KEY="your_key"' >> ~/.bashrc
```

### Import Errors

```bash
# Install the only runtime dependency
pip install requests

# Optional: python-dotenv enables loading OPENROUTER_API_KEY from a .env file
pip install python-dotenv
```

### Generation Fails

```bash
# Use verbose mode to see detailed errors
python scripts/generate_schematic.py "diagram" -o out.png -v

# Check API status
curl https://openrouter.ai/api/v1/models
```

### Low Quality Scores

If iterations consistently score below 7/10:
1. Make your prompt more specific
2. Include more details about layout and labels
3. Specify visual requirements explicitly
4. Increase iterations: `--iterations 2`

## Cost Considerations

Each run makes one image-generation call per iteration plus one review call per iteration, billed
through OpenRouter at the current per-token rates for the image and review models. Smart iteration
keeps cost down: if the first generation meets the document-type threshold it stops after a single
generate-and-review pair (1 iteration) instead of the maximum of 2. Check live pricing for the
configured models on https://openrouter.ai/models before estimating a budget.

## Examples Gallery

See the full SKILL.md for extensive examples including:
- CONSORT flowcharts
- Neural network architectures (Transformers, CNNs, RNNs)
- Biological pathways
- Circuit diagrams
- System architectures
- Block diagrams

## Support

For issues or questions:
1. Check SKILL.md for detailed documentation
2. Use verbose mode (-v) to see detailed errors and API responses
3. Review the `*_review_log.json` for per-iteration quality feedback
4. See `references/troubleshooting.md` for common fixes

