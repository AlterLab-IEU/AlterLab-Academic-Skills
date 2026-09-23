# Installation and Configuration

## System Requirements

### Hardware Requirements
- **GPU**: NVIDIA A6000 (48GB minimum) required for video generation with talking-head features
- **CPU**: Multi-core processor recommended for PDF processing and document conversion
- **RAM**: 16GB minimum, 32GB recommended for large papers

### Software Requirements
- **Python**: 3.11 or higher
- **Conda**: Environment manager for dependency isolation
- **LibreOffice**: Required for document format conversion (PDF to PPTX, etc.)
- **Poppler utilities**: Required for PDF processing and manipulation

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/YuhangChen1/Paper2All.git
cd Paper2All
```

### 2. Create Conda Environment
```bash
conda create -n p2w python=3.11
conda activate p2w
```

The website/poster/PR modules run in this `p2w` environment. Paper2Video uses a separate `p2v` environment (Python 3.10), and the optional talking-head module a third `hallo` environment (Python 3.10).

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install libreoffice poppler-utils
```

**macOS:**
```bash
brew install libreoffice poppler
```

**Windows:**
- Download and install LibreOffice from https://www.libreoffice.org/
- Download and install Poppler from https://github.com/oschwartz10612/poppler-windows

## API Configuration

`pipeline_all.py` (website, poster, PR materials) does not read `.env`: it requires `OPENROUTER_API_KEY` exported in the shell and exits if it is missing:

```bash
export OPENROUTER_API_KEY=sk-or-your-openrouter-key-here
```

The sub-modules and Paper2Video read a `.env` file in the project root with the following credentials (the AutoPR component uses its own `AutoPR/.env`, copied from `AutoPR/.env.example`):

### Required API Keys

**Option 1: OpenAI API**
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
```

**Option 2: OpenRouter API** (upstream-recommended — reuses the same variable names, just repoint the base URL)
```
OPENAI_API_KEY=sk-or-your-openrouter-key-here
OPENAI_API_BASE=https://openrouter.ai/api/v1
```

### Optional API Keys

**Google Search API** (for automatic logo discovery)
```
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

## Model Configuration

### Model Selection

- For `pipeline_all.py` (website/poster/PR): there is no model flag. The website agent and the poster module use models hard-coded upstream and routed through OpenRouter (Qwen3/Qwen2.5-VL for the website agent, GPT-4o for Paper2Poster at the time of writing). The `--model-choice` flag selects the **output component(s)** (1=website, 2=poster, 3=PR materials), not the model.
- For the video pipelines (`pipeline_light.py` / `pipeline.py`): pass models via `--model_name_t` (text/script) and `--model_name_v` (visual/slides). Both default to `gpt-4.1`; the values are Paper2Video aliases (`gpt-4.1`, `gpt-4.1-mini`, `4o`, `o3`, `gpt-5`, …) mapped in `wei_utils.get_agent_config`, and OpenAI-platform aliases use `OPENAI_API_KEY`.

## Verification

Test the installation:

```bash
python pipeline_all.py --help
```

If successful, you should see the help menu with all available options.

## Troubleshooting

### Common Issues

**1. LibreOffice not found**
- Ensure LibreOffice is installed and in your system PATH
- Try running `libreoffice --version` to verify

**2. Poppler utilities not found**
- Verify installation with `pdftoppm -v`
- Add Poppler bin directory to PATH if needed

**3. GPU/CUDA errors for video generation**
- Ensure NVIDIA drivers are up to date
- Verify CUDA toolkit is installed
- Check GPU memory with `nvidia-smi`

**4. API key errors**
- Verify `.env` file is in the project root
- Check that API keys are valid and have sufficient credits
- Ensure no extra spaces or quotes around keys in `.env`

## Directory Structure

After installation, organize your workspace:

```
Paper2All/
├── .env                  # API credentials
├── input/               # Place your paper files here
│   └── paper_name/      # Each paper in its own directory
│       └── main.tex     # LaTeX source or PDF
├── output/              # Generated outputs
│   └── paper_name/
│       ├── website/     # Generated website files
│       ├── video/       # Generated video files
│       └── poster/      # Generated poster files
└── ...
```
