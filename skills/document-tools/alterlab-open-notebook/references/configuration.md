# Open Notebook Configuration Guide

## Docker Deployment

Open Notebook is deployed as a Docker Compose stack with two services: SurrealDB and the Open Notebook container (UI + API + background worker).

### docker-compose.yml (condensed from the official file, v1.x)

Always start from the upstream file (`curl -o docker-compose.yml https://raw.githubusercontent.com/lfnovo/open-notebook/main/docker-compose.yml`); the essentials are:

```yaml
services:
  surrealdb:
    image: surrealdb/surrealdb:v2
    command: ["start", "--log", "info", "--user", "${SURREAL_USER:-root}", "--pass", "${SURREAL_PASSWORD:-root}", "rocksdb:/mydata/mydatabase.db"]
    user: root
    ports:
      - "127.0.0.1:8000:8000"   # localhost only; the app reaches it over the compose network
    volumes:
      - ./surreal_data:/mydata
    restart: always

  open_notebook:
    image: lfnovo/open_notebook:v1-latest
    ports:
      - "8502:8502"   # Web UI
      - "5055:5055"   # REST API
    environment:
      - OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string   # REQUIRED: replace
      - SURREAL_URL=ws://surrealdb:8000/rpc
      - SURREAL_USER=${SURREAL_USER:-root}
      - SURREAL_PASSWORD=${SURREAL_PASSWORD:-root}
      - SURREAL_NAMESPACE=open_notebook
      - SURREAL_DATABASE=open_notebook
    volumes:
      - ./notebook_data:/app/data
    depends_on:
      - surrealdb
    restart: always
```

### Starting the Stack

```bash
# Replace the placeholder encryption key in the compose file (it is a literal value,
# so exporting OPEN_NOTEBOOK_ENCRYPTION_KEY in your shell does not change it)
sed -i.bak "s/change-me-to-a-secret-string/$(openssl rand -hex 32)/" docker-compose.yml

# Optional: database credentials for anything beyond local use
printf 'SURREAL_USER=notebook\nSURREAL_PASSWORD=%s\n' "$(openssl rand -hex 16)" > .env

# Start services
docker compose up -d

# View logs
docker compose logs -f open_notebook

# Stop services (data stays in ./notebook_data and ./surreal_data)
docker compose down
```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `OPEN_NOTEBOOK_ENCRYPTION_KEY` | Secret used to encrypt stored API credentials. Set before first launch and keep it stable; changing or losing it makes saved credentials unreadable. Docker secrets: `OPEN_NOTEBOOK_ENCRYPTION_KEY_FILE`. |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `SURREAL_URL` | `ws://surrealdb:8000/rpc` | SurrealDB WebSocket connection URL |
| `SURREAL_NAMESPACE` | `open_notebook` | SurrealDB namespace |
| `SURREAL_DATABASE` | `open_notebook` | SurrealDB database name |
| `SURREAL_USER` | `root` | SurrealDB username |
| `SURREAL_PASSWORD` | `root` | SurrealDB password |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `OPEN_NOTEBOOK_PASSWORD` | None | Optional password; the API then requires `Authorization: Bearer <password>` |
| `OPEN_NOTEBOOK_MAX_UPLOAD_SIZE_MB` | `100` | Largest request body the API accepts |
| `OPEN_NOTEBOOK_WORKER_MAX_TASKS` | `5` | Concurrent background jobs (use `1` for a single local GPU) |
| `API_URL` | auto-detected | URL where the frontend reaches the API (set it behind a reverse proxy) |
| `CORS_ORIGINS` | `*` | Allowed browser origins; set explicitly for production |
| `OPEN_NOTEBOOK_ENABLE_DOCLING` / `OPEN_NOTEBOOK_ENABLE_CRAWL4AI` | off | Install heavier extraction engines (Docling OCR, Crawl4AI) on first start |

See the upstream `docs/5-CONFIGURATION/environment-reference.md` for the complete list.

### AI Provider Keys (Legacy)

Provider keys can still be supplied as environment variables for backward compatibility (`POST /api/credentials/migrate-from-env` imports them). The preferred method is the credentials UI or API.

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `GOOGLE_API_KEY` | Google GenAI |
| `GROQ_API_KEY` | Groq |
| `MISTRAL_API_KEY` | Mistral |
| `ELEVENLABS_API_KEY` | ElevenLabs |

## AI Provider Configuration

### Via UI

1. Open **Models** and choose your provider
2. Click **+ Add Configuration**, paste the API key (and base URL if needed), and save
3. Click **Test** to verify the connection
4. Click **Sync Models** and select the models to include
5. Under **Default Model Assignments**, click **Auto-Assign Defaults** (or pick models per slot)

### Via API

```python
import os
import requests

BASE_URL = "http://localhost:5055/api"
HEADERS = {"Authorization": f"Bearer {os.environ['OPEN_NOTEBOOK_PASSWORD']}"} if os.environ.get("OPEN_NOTEBOOK_PASSWORD") else {}

# 1. Create credential
cred = requests.post(f"{BASE_URL}/credentials", headers=HEADERS, json={
    "provider": "anthropic",
    "name": "Anthropic Production",
    "api_key": os.environ["ANTHROPIC_API_KEY"],
}).json()

# 2. Test connection
print(requests.post(f"{BASE_URL}/credentials/{cred['id']}/test", headers=HEADERS).json())

# 3. Discover and register models
discovered = requests.post(
    f"{BASE_URL}/credentials/{cred['id']}/discover", headers=HEADERS
).json()["discovered"]

requests.post(
    f"{BASE_URL}/credentials/{cred['id']}/register-models",
    headers=HEADERS,
    json={"models": [
        {"name": m["name"], "provider": m["provider"], "model_type": m["model_type"]}
        for m in discovered if m.get("model_type")
    ]},
)

# 4. Auto-assign defaults (Anthropic has no embedding models: add an embedding
#    provider such as OpenAI, Google, Voyage, or Ollama for vector search)
requests.post(f"{BASE_URL}/models/auto-assign", headers=HEADERS)
```

### Using Ollama (Free Local Inference)

For free AI inference without API costs, use Ollama:

```yaml
# docker-compose-ollama.yml addition
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
```

Then configure Ollama as a provider with base URL `http://ollama:11434` (the upstream `examples/docker-compose-ollama.yml` wires this up). Ollama models default to an 8192-token context window in Open Notebook; raise it with the credential's `num_ctx` field for long sources.

## Security Configuration

### Password Protection

Set `OPEN_NOTEBOOK_PASSWORD` in the `open_notebook` service's `environment:` block (or `.env`) to require authentication; API clients then send `Authorization: Bearer <password>`. Treat this as basic protection only — for public deployments also use HTTPS, a reverse proxy, and restricted `CORS_ORIGINS`.

### Reverse Proxy (Nginx Example)

```nginx
server {
    listen 443 ssl;
    server_name notebook.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://localhost:8502;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://localhost:5055/api/;
        proxy_set_header Host $host;
    }
}
```

## Backup and Restore

### Backup SurrealDB Data

The simplest consistent backup is to stop the stack and copy the two bind-mounted folders:

```bash
docker compose down
tar czf open-notebook-backup-$(date +%F).tgz notebook_data surreal_data
docker compose up -d
```

For a logical dump instead, SurrealDB's own `surreal export` / `surreal import` CLI works against the running database (namespace `open_notebook`, database `open_notebook`, credentials from `SURREAL_USER` / `SURREAL_PASSWORD`); see the SurrealDB documentation for the invocation that matches your install.

### Backup Uploaded Files

Uploaded files and generated podcasts live under `./notebook_data` (mounted at `/app/data`); include that folder in your backups.

### Restore

```bash
# Restore folder backups
docker compose down
tar xzf open-notebook-backup-YYYY-MM-DD.tgz
docker compose up -d
```
