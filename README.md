# Axon API

> A multi-provider LLM API service with pluggable model backends (Groq, OpenAI, Anthropic) — document review, medical RAG, and more.

Built with **FastAPI**, **Python 3.12**, and **Docker**. Swap LLM providers with a single environment variable — no code changes needed.

**Production docs:** [View docs](https://api.axon.zonetechpark.com/docs)

---

## Features

- **Multi-provider LLM support** — Groq, OpenAI, and Anthropic out of the box; switch with one env var
- **Document Review** — upload PDF, DOCX, or plain text and get a structured placeholder validation back
- **Medical RAG** — query a Pinecone vector store with HuggingFace embeddings and get cited answers
- **Free tier** — 3 free requests per IP on the RAG endpoint; API key required after that
- **Structured JSON responses** — every endpoint returns typed, predictable output
- **API key authentication** — `X-API-Key` header on protected routes
- **Request logging** — method, path, status code, and latency on every request
- **Auto-generated docs** — Swagger UI at `/docs`, ReDoc at `/redoc`

---

## Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/health` | No | Service status, active model, environment |
| `GET` | `/api/models` | No | All available models grouped by provider |
| `GET` | `/api/models/active` | No | Currently configured model and provider |
| `POST` | `/api/review` | Yes | Validate DOCX template placeholders |
| `POST` | `/api/medical/query` | Free tier (3 req) / API key | RAG query against medical knowledge base |

---

## Quick Start

**1. Clone and configure**

```bash
git clone https://github.com/boscoseries/axon-api
cd axon-api
cp .env.example .env
```

Edit `.env`:

```env
app_env=development

# Active model — format: provider/model-name
llm_model=groq/llama-3.3-70b-versatile

# All models surfaced by GET /api/models
llm_available_models=groq/llama-3.3-70b-versatile,groq/llama-3.1-8b-instant,groq/mixtral-8x7b-32768,openai/gpt-4o,openai/gpt-4o-mini,anthropic/claude-sonnet-4-6,anthropic/claude-haiku-4-5-20251001

# Provider API keys — only the active provider's key is needed
groq_api_key=your_groq_key
openai_api_key=your_openai_key
anthropic_api_key=your_anthropic_key

# Your API's own auth key
api_key=your_secret_key

# Pinecone (RAG)
pinecone_api_key=your_pinecone_key
pinecone_index=your_index_name
pinecone_top_k=5

# HuggingFace (embeddings — get a free token at huggingface.co/settings/tokens)
hf_api_key=your_hf_token
hf_embedding_model=thenlper/gte-large

# Free tier
free_requests_limit=3

# AWS / DynamoDB (request logging)
aws_access_key_id=
aws_secret_access_key=
aws_region=us-east-1
```

**2. Run**

```bash
docker compose up --build
```

API is live at `http://localhost:8082`
Swagger docs at `http://localhost:8082/docs`

---

## API Reference

### `POST /api/review`

Validates Jinja-style placeholders (`{{variable}}`) in a DOCX template.

**Headers**
```
X-API-Key: <your key>
Content-Type: multipart/form-data
```

**Accepted file types:** PDF, DOCX, TXT, JSON

**Request**
```bash
curl -X POST http://localhost:8082/api/review \
  -H "X-API-Key: your_secret_key" \
  -F "file=@template.docx" \
  -F "allowed_keys=client_name,project_title,date"
```

**Response**
```json
{
  "has_issues": true,
  "issues": [
    {
      "type": "SINGLE_BRACE",
      "invalid variable": "{client_name}",
      "reason": "Uses single braces instead of double braces",
      "valid variable": "{{client_name}}"
    }
  ]
}
```

---

### `POST /api/medical/query`

Embeds the query using `thenlper/gte-large` via HuggingFace, retrieves the top-k most similar chunks from Pinecone, and returns a grounded answer.

First 3 requests per IP are free. Pass `X-API-Key` for unlimited access.

**Request**
```bash
curl -X POST http://localhost:8082/api/medical/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the symptoms of hypertension?", "top_k": 5}'
```

**Response**
```json
{
  "answer": "Hypertension is often asymptomatic, but severe cases may present with headaches, visual disturbances, and dizziness...",
  "sources": ["Merck"],
  "chunks_used": 5
}
```

**429 when free tier exceeded:**
```json
{
  "detail": "Free tier limit of 3 requests exceeded. Pass your API key in the X-API-Key header to continue."
}
```

---

### `GET /api/models`

Returns all available models grouped by provider (read from `llm_available_models` env var — no redeploy needed to add or remove models).

```bash
curl http://localhost:8082/api/models
```

```json
{
  "providers": {
    "groq": ["groq/llama-3.3-70b-versatile", "groq/llama-3.1-8b-instant", "groq/mixtral-8x7b-32768"],
    "openai": ["openai/gpt-4o", "openai/gpt-4o-mini"],
    "anthropic": ["anthropic/claude-sonnet-4-6", "anthropic/claude-haiku-4-5-20251001"]
  }
}
```

---

### `GET /api/models/active`

```bash
curl http://localhost:8082/api/models/active
```

```json
{
  "model": "groq/llama-3.3-70b-versatile",
  "provider": "groq"
}
```

---

### `GET /api/health`

```bash
curl http://localhost:8082/api/health
```

```json
{
  "status": "ok",
  "model": "groq/llama-3.3-70b-versatile",
  "environment": "production"
}
```

---

## Switching Providers

Change one environment variable — no code changes, no redeploy:

```env
# Groq (default)
llm_model=groq/llama-3.3-70b-versatile

# OpenAI
llm_model=openai/gpt-4o

# Anthropic
llm_model=anthropic/claude-sonnet-4-6
```

The `provider/model-name` format tells the client which SDK and API key to use automatically.

---

## Architecture

```
POST /api/review
      │
      ├── middlewares/auth.py      validates X-API-Key
      ├── services/extractor.py   PDF / DOCX / TXT → plain text
      ├── services/reviewer.py    builds prompt, parses LLM response
      └── services/llm_client.py  routes to Groq / OpenAI / Anthropic

POST /api/medical/query
      │
      ├── middlewares/auth.py      API key or free-tier (3 req/IP)
      ├── services/embedder.py    query → vector via HuggingFace API
      ├── services/retriever.py   Pinecone top-k similarity search
      └── services/llm_client.py  grounded answer from retrieved chunks
```

```
axon-api/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── poetry.lock
└── api/
    ├── main.py
    ├── config.py
    ├── routes/
    │   ├── health.py
    │   ├── review.py
    │   └── medical.py
    ├── services/
    │   ├── llm_client.py
    │   ├── extractor.py
    │   ├── reviewer.py
    │   ├── embedder.py
    │   └── retriever.py
    ├── middlewares/
    │   └── auth.py
    └── models/
        ├── schema/schemas.py
        └── db/
            ├── tables.py
            └── utils.py
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| LLM Providers | Groq, OpenAI, Anthropic |
| Embeddings | HuggingFace Inference API (`thenlper/gte-large`) |
| Vector Store | Pinecone |
| PDF Extraction | PyMuPDF |
| DOCX Extraction | python-docx |
| Request Tracking | AWS DynamoDB |
| Config | Pydantic Settings |
| Packaging | Poetry |
| Containerisation | Docker + Docker Compose |
| Hosting | DigitalOcean |

---

## Roadmap

- [x] Document review — DOCX placeholder validation
- [x] Multi-provider LLM support (Groq, OpenAI, Anthropic)
- [x] Medical RAG — Pinecone + HuggingFace embeddings
- [x] Free tier — 3 requests per IP before API key required
- [ ] Document summarisation endpoint
- [ ] Async job queue for large documents
- [ ] Per-client API key management
- [ ] Webhook callback on job completion

---

## Local Development

```bash
# Install dependencies
poetry install

# Run without Docker
cd api && uvicorn main:app --reload --port 8082

# Run with Docker
docker compose up --build
```

---

## Author

**Johnbosco Okoror** — [github.com/boscoseries](https://github.com/boscoseries) · [linkedin.com/in/johnbosco-okoror](https://linkedin.com/in/johnbosco-okoror)
