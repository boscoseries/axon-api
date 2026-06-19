import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from services.notifier import SMTPErrorHandler
from middlewares.requests import RequestLoggingMiddleware
from routes import health, review, medical
from models.db.tables import create_tables_if_not_exist
from config import settings
import logging, time





# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(SMTPErrorHandler())

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AXON API",
    description=(
        "A multi-provider AI API platform with pluggable model backends (Groq, OpenAI, Anthropic). "
        "Exposes document review for DOCX template validation and a medical RAG pipeline — "
        "query a Pinecone knowledge base with semantic search and get grounded, source-attributed answers. "
        "First 3 requests on the RAG endpoint are free per IP; API key required beyond that."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc", 
)

@app.on_event("startup")
async def startup():
    create_tables_if_not_exist()

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware ────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(review.router, prefix="/api", tags=["Review"])
app.include_router(medical.router, prefix="/api", tags=["Medical"])


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/home", include_in_schema=False)
async def root():
    return {
        "service": "AXON API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }