from fastapi import APIRouter, Depends
import logging
from middlewares.auth import require_api_key
from services.flashcards import make_flashcards
from models.schema.schemas import FlashcardsRequest, FlashcardsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/flashcards",
    response_model=FlashcardsResponse,
    summary="Make flashcards from given material",
    description="Makes question-and-answer cards using only the supplied lesson material.",
)
async def flashcards(body: FlashcardsRequest, _: str = Depends(require_api_key)):
    logger.info(f"Flashcards request | material_chars={len(body.material)} | count={body.count}")
    return await make_flashcards(body.material, body.title, body.count)
