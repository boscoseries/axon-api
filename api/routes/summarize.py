from fastapi import APIRouter, Depends, File, Form, UploadFile
from services.extractor import extract_text
import logging
from middlewares.auth import require_api_key
from services.summarizer import summarize_text
from models.schema.schemas import SummarizeRequest, SummarizeResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarise a text",
    description="Send plain text (for example a lesson transcript) and receive a short summary with key points.",
)
async def summarize(body: SummarizeRequest, _: str = Depends(require_api_key)):
    logger.info(f"Summarize request | chars={len(body.text)}")
    return await summarize_text(body.text, body.title, body.max_points)


@router.post(
    "/summarize/file",
    response_model=SummarizeResponse,
    summary="Summarise a document",
    description="Upload a PDF, DOCX or plain text file and receive a short summary with key points.",
)
async def summarize_file(
    file: UploadFile = File(..., description="The document (PDF, DOCX, TXT)"),
    title: str = Form(None),
    max_points: int = Form(None),
    _: str = Depends(require_api_key),
):
    text = await extract_text(file)
    logger.info(f"Summarize file request | file={file.filename} | chars={len(text)}")
    return await summarize_text(text, title, max(1, min(max_points, 50)) if max_points else None)
