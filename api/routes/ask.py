from fastapi import APIRouter, Depends
import logging
from middlewares.auth import require_api_key
from services.asker import answer_question
from models.schema.schemas import AskRequest, AskResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Answer a question from given material only",
    description="Answers a question using only the supplied lesson material. Anything the material does not cover comes back as found=false.",
)
async def ask(body: AskRequest, _: str = Depends(require_api_key)):
    logger.info(f"Ask request | material_chars={len(body.material)} | history={len(body.history)}")
    return await answer_question(body.question, body.material, body.title, body.history)
