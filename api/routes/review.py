from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body
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
    file: UploadFile = File(None, description="The document to review (PDF, DOCX, TXT, JSON)"),
    text_content: str = Body(None),  # Optional direct text input instead of file upload,
    allowed_keys: str = Body(None, description="Optional comma separated string of allowed placeholder keysfor DOCX template validation."),
    _: str = Depends(require_api_key),
):
    
    # input validation
    if file and text_content:
        raise HTTPException(status_code=400, detail="Please upload a file or provide text content, but not both.")
    
    if file:
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
        text = await extract_text(file)

        logger.info(f"Review request received | file={file.filename} | size={len(contents)} bytes")
    elif text_content:
        text = text_content
        logger.info(f"Review request received | direct text input | length={len(text_content)} chars")
    else:
        raise HTTPException(status_code=400, detail="No input provided. Please upload a file or provide text content.")

    result = await review_document(text=text, allowed_keys=allowed_keys)

    logger.info(f"Review complete | issues={len(result.issues)}")
    return result