# LLM API Configuration

## Overview

On init, `Denario` constructs a `KeyManager` and calls `get_keys_from_env()`, which reads provider keys straight from environment variables. There is **no** model/config argument on the `Denario` constructor — keys come from the environment, and per-stage model choices are passed as method arguments (see `research_pipeline.md`).

## Environment variables (what KeyManager actually reads)

| Variable | Provider | Status |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI | **Required** — the analysis/results module needs it; OpenAI models are the cmbagent-mode defaults |
| `GOOGLE_API_KEY` | Gemini (Google AI Studio key) | Optional — default LLM for the `mode="fast"` path |
| `ANTHROPIC_API_KEY` | Anthropic Claude | Optional |
| `PERPLEXITY_API_KEY` | Perplexity | Optional — only for citation search |
| `SEMANTIC_SCHOLAR_KEY` | Semantic Scholar | Optional — only for fast Semantic Scholar lookups |

> `GOOGLE_API_KEY` is a plain **Gemini** API key from Google AI Studio — not a Vertex AI service-account JSON. Use Vertex AI only via the dedicated backend setup below.

## Obtaining keys

- **OpenAI**: create a key at [platform.openai.com](https://platform.openai.com/) → API Keys → "Create new secret key".
- **Gemini**: create a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
- **Anthropic**: create a key in the [Anthropic Console](https://console.anthropic.com/).

## Storing keys

### Method 1: Environment variables

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."       # optional, Gemini
export ANTHROPIC_API_KEY="..."    # optional, Claude
```

Add to `~/.zshrc` (or your shell profile) for persistence.

**Windows (PowerShell):**
```powershell
setx OPENAI_API_KEY "sk-..."
```

### Method 2: .env file

Create a `.env` in your project directory:

```env
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-gemini-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
PERPLEXITY_API_KEY=your-perplexity-key-here   # only if using citation search
```

Load it before importing `denario` (so the env is populated when `KeyManager` runs):

```python
from dotenv import load_dotenv
load_dotenv()

from denario import Denario
den = Denario(project_dir="./project")
```

### Method 3: Docker Environment Files

For Docker deployments, pass environment variables:

```bash
# Using --env-file flag
docker run -p 8501:8501 --env-file .env --rm pablovd/denario:latest

# Using -e flag for individual variables
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-... \
  -e GOOGLE_API_KEY=... \
  --rm pablovd/denario:latest
```

## Vertex AI Detailed Setup (alternative Google backend)

Use this only if you want to route Gemini through Google Cloud Vertex AI instead of a plain `GOOGLE_API_KEY`. It requires a Google Cloud project and service account.

### Prerequisites
- Google Cloud account with billing enabled
- gcloud CLI installed (optional but recommended)

### Step-by-Step Configuration

1. **Install Google Cloud SDK (if not using Docker)**

   Follow the official instructions at https://cloud.google.com/sdk/docs/install
   and prefer a package manager or the versioned installer archive over piping a
   remote script to your shell:

   ```bash
   # macOS (Homebrew)
   brew install --cask google-cloud-sdk

   # Debian/Ubuntu (APT repository) — see the install page for the full steps
   sudo apt-get install google-cloud-cli

   # Then initialize
   gcloud init
   ```

   > **Caution:** Avoid `curl https://sdk.cloud.google.com | bash` — piping a
   > remote script straight into a shell executes unreviewed code. Use a package
   > manager or the downloaded installer so you can verify what runs.

2. **Authenticate gcloud**
   ```bash
   gcloud auth application-default login
   ```

3. **Set project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

4. **Enable required APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable compute.googleapis.com
   ```

5. **Create service account (alternative to gcloud auth)**
   ```bash
   gcloud iam service-accounts create denario-service-account \
     --display-name="Denario AI Service Account"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:denario-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"

   gcloud iam service-accounts keys create credentials.json \
     --iam-account=denario-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

6. **Configure denario to use Vertex AI**
   ```python
   import os
   os.environ['GOOGLE_CLOUD_PROJECT'] = 'YOUR_PROJECT_ID'
   os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/credentials.json'

   from denario import Denario
   den = Denario(project_dir="./research")
   ```

## Model Selection

Models are chosen **per stage**, as method arguments — not on the `Denario` constructor. Each `get_*` method exposes per-agent model parameters (model names are strings/`LLM` objects from `denario`'s model registry). Verified defaults from the source:

```python
# Fast path uses a single LLM (defaults to gemini-2.0-flash):
den.get_idea(mode="fast", llm="gemini-2.0-flash")

# cmbagent path configures each agent (defaults shown):
den.get_idea(
    mode="cmbagent",
    idea_maker_model="gpt-4o",
    idea_hater_model="o3-mini",
    planner_model="gpt-4o",
    plan_reviewer_model="o3-mini",
    orchestration_model="gpt-4.1",
    formatter_model="o3-mini",
)

# Results stage agents:
den.get_results(
    engineer_model="gpt-4.1",
    researcher_model="o3-mini",
)
```

Available model names depend on the installed `denario` version; consult `denario.llm.models` for the current registry.

## Cost Management

### Monitoring Costs

- **OpenAI**: Track usage at [platform.openai.com/usage](https://platform.openai.com/usage)
- **Google Cloud**: Monitor in Cloud Console → Billing
- Set up billing alerts to avoid unexpected charges

### Cost Optimization Tips

1. **Use appropriate model tiers**
   - The faster `mode="fast"` path (default LLM `gemini-2.0-flash`) is cheaper for idea/method generation
   - Reserve the heavier cmbagent defaults (`gpt-4o`, `gpt-4.1`, `o3-mini`) for the runs that need reliability

2. **Batch operations**
   - Process multiple research tasks in single sessions

3. **Cache results**
   - Reuse generated ideas, methods, and results when possible

4. **Set token limits**
   - Configure maximum token usage for cost control

## Security Best Practices

### Do NOT commit API keys to version control

Add to `.gitignore`:
```gitignore
.env
*.json  # If storing credentials
credentials.json
service-account-key.json
```

### Rotate keys regularly
- Generate new API keys periodically
- Revoke old keys after rotation

### Use least privilege access
- Grant only necessary permissions to service accounts
- Use separate keys for development and production

### Encrypt sensitive files
- Store credential files in encrypted volumes
- Use cloud secret management services for production

## Troubleshooting

### "API key not found" errors
- Verify environment variables are set: `echo $OPENAI_API_KEY`
- Check `.env` file is in correct directory
- Ensure `load_dotenv()` is called before importing denario

### Vertex AI authentication failures
- Verify `GOOGLE_APPLICATION_CREDENTIALS` points to valid JSON file
- Check service account has required permissions
- Ensure APIs are enabled in Google Cloud project

### Rate limiting issues
- Implement exponential backoff
- Reduce concurrent requests
- Upgrade API plan if needed

### Docker environment variable issues
- Use `docker run --env-file .env` to pass environment
- Mount credential files with `-v` flag
- Check environment inside container: `docker exec <container> env`
