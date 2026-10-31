from fastapi import APIRouter, Depends
import logging
from middlewares.auth import require_api_key
from services.quiz import make_quiz
from models.schema.schemas import QuizRequest, QuizResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/quiz",
    response_model=QuizResponse,
    summary="Make a practice quiz from given material",
    description="Makes multiple-choice questions using only the supplied lesson material.",
)
async def quiz(body: QuizRequest, _: str = Depends(require_api_key)):
    logger.info(f"Quiz request | material_chars={len(body.material)} | count={body.count} | difficulty={body.difficulty}")
    return await make_quiz(body.material, body.title, body.count, body.difficulty)
