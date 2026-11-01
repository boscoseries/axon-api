from fastapi import APIRouter, Depends, UploadFile, File
import logging
from middlewares.auth import require_api_key
from services.extractor import extract_text
from services.assessment_questions import make_assessment_questions
from models.schema.schemas import AssessmentQuestionsRequest, AssessmentQuestionsResponse, ExtractResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/assessment-questions",
    response_model=AssessmentQuestionsResponse,
    summary="Write graded quiz questions from given material",
    description="Single and multiple choice questions with their correct options, using only the supplied material.",
)
async def assessment_questions(body: AssessmentQuestionsRequest, _: str = Depends(require_api_key)):
    logger.info(f"Assessment questions request | material_chars={len(body.material)} | count={body.count} | {body.difficulty} | {body.question_type}")
    return await make_assessment_questions(body.material, body.title, body.count, body.difficulty, body.question_type)


@router.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Read the text of a document",
    description="Upload a PDF, DOCX or plain text file and receive its text.",
)
async def extract(file: UploadFile = File(...), _: str = Depends(require_api_key)):
    return ExtractResponse(text=await extract_text(file))
