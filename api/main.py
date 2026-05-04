import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from services.notifier import SMTPErrorHandler, send_error_email
from middlewares.requests import RequestLoggingMiddleware
from routes import health, review
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
    title="Document Review API",
    description=(
        "A production-grade API that uses an LLM to review documents for "
        "completeness and grammar issues. Accepts PDF, DOCX, and plain text."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc", 
)

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


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/home", include_in_schema=False)
async def root():
    return {
        "service": "Document Review API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }