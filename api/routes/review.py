from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body
import logging, io, asyncio
from middlewares.auth import require_api_key
from services.extractor import extract_text
from services.reviewer import review_document
from models.schema.schemas import ReviewResponse
from config import settings

from models.db.utils import log_count, log_request

logger = logging.getLogger(__name__)
router = APIRouter()

def _track(endpoint: str, **kwargs):
    asyncio.create_task(asyncio.to_thread(log_count, endpoint))
    # asyncio.create_task(asyncio.to_thread(log_request, endpoint=endpoint, **kwargs))


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
    user: str = Body(None),
    _: str = Depends(require_api_key),
):
    
    # input validation
    if file and text_content:
        raise HTTPException(status_code=400, detail="Please upload a file or provide text content, but not both.")
    
    error_message = None
    result = None
    
    try:
        if file:
            # File size guard
            max_bytes = settings.max_file_size_mb * 1024 * 1024
            filename = file.filename
            contents = await file.read()
            if len(contents) > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB."
                )

            # Reset file pointer after size check so extractor can read it
            file.file = io.BytesIO(contents)
            text = await extract_text(file)

            logger.info(f"Review request received | file={filename} | size={len(contents)} bytes")
        elif text_content:
            text = text_content
            logger.info(f"Review request received | direct text input | length={len(text_content)} chars")
        else:
            raise HTTPException(status_code=400, detail="No input provided. Please upload a file or provide text content.")

        result = await review_document(text=text, allowed_keys=allowed_keys)
        logger.info(f"Review complete | issues={len(result.issues)}")

    except HTTPException as e:
        error_message = e.detail
        raise e
    
    finally:
        _track(
            endpoint="/api/review",
            provider=settings.llm_model,
            requester=user or "unknown",
            response=result,
            error=error_message,
        )

    return result