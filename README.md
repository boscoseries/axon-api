# Axon API

> A multi-provider LLM API service with pluggable model backends (Groq, OpenAI, xAI) — document review, and more coming.

Built with **FastAPI**, **Python 3.12**, and **Docker**. Swap LLM providers with a single environment variable — no code changes needed.

---

## Features

- **Multi-provider LLM support** — Groq, OpenAI, and xAI (Grok) out of the box
- **Document Review** — upload PDF, DOCX, or plain text and get a structured analysis back
- **Structured JSON responses** — every endpoint returns typed, predictable output
- **API key authentication** — `X-API-Key` header on all protected routes
- **Request logging** — method, path, status code, and latency on every request
- **Auto-generated docs** — Swagger UI at `/docs`, ReDoc at `/redoc`
- **RAG-ready architecture** — designed to plug in a vector store in v2

---

## Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/health` | No | Service status and active model |
| `GET` | `/api/models` | Yes | Available models for current provider |
| `POST` | `/api/review` | Yes | Review a document for completeness and grammar |

---

## Quick Start

**1. Clone and configure**

```bash
git clone https://github.com/boscoseries/axon-api
cd axon-api
cp .env.example .env
```

Edit `.env`:

```bash
# Provider: groq | openai | xai
LLM_PROVIDER=groq
LLM_MODEL=llama3-8b-8192

# Provider API keys — only the active provider's key is required
GROQ_API_KEY=your_groq_key        # free at console.groq.com
OPENAI_API_KEY=your_openai_key
XAI_API_KEY=your_xai_key

# Your API's own auth key — generate with:
# python -c "import secrets; print(secrets.token_hex(32))"
API_KEY=your_secret_key
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

Upload a document and receive a structured review covering completeness and grammar.

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
  -F "file=@contract.pdf"
```

**Response**
```json
{
  "score": 74,
  "summary": "The document is mostly well-written but is missing a conclusion section and contains several grammar issues in the opening paragraphs.",
  "issues": [
    {
      "type": "completeness",
      "severity": "high",
      "detail": "Missing 'Conclusion' section",
      "location": "End of document"
    },
    {
      "type": "grammar",
      "severity": "low",
      "detail": "Subject-verb agreement error: 'The results was consistent'",
      "location": "Paragraph 3"
    }
  ],
  "model_used": "llama3-8b-8192",
  "document_name": "contract.pdf",
  "word_count": 842
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
  "model": "llama3-8b-8192",
  "environment": "production"
}
```

---

### `GET /api/models`

```bash
curl http://localhost:8082/api/models \
  -H "X-API-Key: your_secret_key"
```

```json
{
  "provider": "groq",
  "models": [
    "llama3-8b-8192",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma-7b-it"
  ]
}
```

---

## Switching Providers

Change two environment variables — no code changes:

```bash
# Use OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Use xAI (Grok)
LLM_PROVIDER=xai
LLM_MODEL=grok-3-mini

# Use Groq (default)
LLM_PROVIDER=groq
LLM_MODEL=llama3-8b-8192
```

All three providers implement the OpenAI-compatible chat completions interface, so the same internal call works across all of them.

---

## Architecture

```
POST /api/review
      │
      ├── middleware/auth.py       validates X-API-Key header
      ├── services/extractor.py    PDF / DOCX / TXT → plain text
      ├── services/reviewer.py     builds prompt, parses LLM response into schema
      ├── services/llm_client.py   routes to Groq, OpenAI, or xAI based on env
      └── models/schemas.py        Pydantic response shapes
```

```
axon-api/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── poetry.lock
├── Dockerfile
└── api/
    ├── main.py
    ├── config.py
    ├── routes/
    │   ├── review.py
    │   └── health.py
    ├── services/
    │   ├── llm_client.py
    │   ├── extractor.py
    │   └── reviewer.py
    ├── middleware/
    │   └── auth.py
    └── models/
        └── schemas.py
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| LLM Providers | Groq, OpenAI, xAI |
| PDF Extraction | PyMuPDF |
| DOCX Extraction | python-docx |
| Config | Pydantic Settings |
| Packaging | Poetry |
| Containerisation | Docker + Docker Compose |
| Hosting | DigitalOcean |

---

## Roadmap

- [x] Document review — completeness and grammar
- [x] Multi-provider LLM support (Groq, OpenAI, xAI)
- [ ] RAG — review documents against a reference template using vector search
- [ ] Document summarisation endpoint
- [ ] Async job queue for large documents (Celery + Redis)
- [ ] Per-client API key management
- [ ] Rate limiting per client
- [ ] Webhook callback on job completion

---

## Local Development

```bash
# Install dependencies
poetry install

# Run without Docker
uvicorn api.main:app --reload --port 8082

# Run with Docker
docker compose up --build
```

---

## Author

**Johnbosco Okoror** — [github.com/boscoseries](https://github.com/boscoseries) · [linkedin.com/in/johnbosco-okoror](https://linkedin.com/in/johnbosco-okoror)
