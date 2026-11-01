from fastapi import APIRouter, Depends
import logging
from middlewares.auth import require_api_key
from services.course_copy import make_course_copy
from models.schema.schemas import CourseCopyRequest, CourseCopyResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/course-copy",
    response_model=CourseCopyResponse,
    summary="Write a course description and summary",
    description="Writes the catalogue description (HTML paragraphs) and a one-line summary from a course's outline.",
)
async def course_copy(body: CourseCopyRequest, _: str = Depends(require_api_key)):
    logger.info(f"Course copy request | outline_chars={len(body.outline)} | tone={body.tone}")
    return await make_course_copy(body.title, body.outline, body.level, body.category, body.current_description, body.current_summary, body.tone)
