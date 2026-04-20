from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from middlewares.auth import require_api_key
from services.extractor import extract_text
from services.reviewer import review_document
from schema.schemas import ReviewResponse
from config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/review",
    response_model=ReviewResponse,
    summary="Review a document",
    description="Upload a PDF, DOCX, or plain text file and receive a structured review covering completeness and grammar issues.",
)
async def review(
    file: UploadFile = File(..., description="The document to review (PDF, DOCX, TXT, JSON)"),
    _: str = Depends(require_api_key),
):
    # File size guard
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB."
        )

    # Reset file pointer after size check so extractor can read it
    import io
    file.file = io.BytesIO(contents)

    logger.info(f"Review request received | file={file.filename} | size={len(contents)} bytes")

    text = await extract_text(file)
    result = await review_document(text=text, filename=file.filename or "unnamed")

    logger.info(f"Review complete | file={file.filename} | score={result.score} | issues={len(result.issues)}")
    return result