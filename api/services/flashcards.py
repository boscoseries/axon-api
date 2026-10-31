from services.llm_client import chat
from models.schema.schemas import Flashcard, FlashcardsResponse
from fastapi import HTTPException
from config import settings
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
    You make flashcards for a learner from one lesson, using ONLY the lesson material you are given.

    Rules:
    - Every card must come from the material. Never add facts, examples or definitions that are not in it, and never use outside knowledge.
    - "front": one clear question or prompt (a term to define, a step to recall, a figure to remember). "back": the short answer, in one or two sentences, as the material gives it.
    - Cover the most important ideas of the lesson, spread across it from start to finish. No two cards about the same thing.
    - Plain words, in the same language as the material.
    - Make at most the requested number of cards. If the material only supports fewer, make fewer. If it supports none, return an empty list.
    - Output ONLY valid JSON, no markdown and no prose outside it.

    Output schema (MUST follow exactly):
    {"cards": [{"front": "...", "back": "..."}]}
    """.strip()


def _parse(raw: str) -> dict:
    clean = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse LLM response as JSON: {e}")


async def make_flashcards(material: str, title: str | None, count: int) -> FlashcardsResponse:
    limit = settings.summary_max_chars
    if len(material) > limit:
        logger.warning(f"Material truncated from {len(material)} to {limit} chars")
        material = material[:limit]
    header = f"Lesson title: {title}\n\n" if title else ""
    user_message = f"{header}Number of cards: {count}\n\nLESSON MATERIAL:\n{material}"
    raw = await chat(system_prompt=SYSTEM_PROMPT, user_message=user_message, max_tokens=2048)
    parsed = _parse(raw)
    cards = []
    for item in parsed.get("cards") or []:
        if isinstance(item, dict) and str(item.get("front") or "").strip() and str(item.get("back") or "").strip():
            cards.append(Flashcard(front=str(item["front"]).strip(), back=str(item["back"]).strip()))
    return FlashcardsResponse(cards=cards[:count])
