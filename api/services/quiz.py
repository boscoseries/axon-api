from services.llm_client import chat
from models.schema.schemas import QuizQuestion, QuizResponse
from fastapi import HTTPException
from config import settings
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
    You write a practice quiz for a learner from one lesson, using ONLY the lesson material you are given.

    Rules:
    - Every question must be answerable from the material, and its correct answer must be stated in it. Never use outside knowledge.
    - Multiple choice, exactly 4 options per question, exactly one correct. Wrong options must be plausible but clearly wrong according to the material; never "all of the above" or "none of the above".
    - Test understanding of the important ideas across the whole lesson, not trivia. No two questions about the same thing.
    - Difficulty: the input says easy, medium or hard. Easy: direct recall of a clearly stated fact or term, with wrong options that are obviously off. Medium: understanding, such as why or how, or telling similar ideas apart. Hard: applying the lesson to a new situation, comparing or combining several points, with wrong options that are close and tempting. At every level the correct answer must still be supported by the material.
    - "answer_index" is the position (0 to 3) of the correct option.
    - "explanation": one short sentence saying why the answer is right, based on the material.
    - Plain words, in the same language as the material.
    - Write at most the requested number of questions. If the material supports fewer, write fewer. If it supports none, return an empty list.
    - Output ONLY valid JSON, no markdown and no prose outside it.

    Output schema (MUST follow exactly):
    {"questions": [{"question": "...", "options": ["...", "...", "...", "..."], "answer_index": 0, "explanation": "..."}]}
    """.strip()


def _parse(raw: str) -> dict:
    clean = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse LLM response as JSON: {e}")


async def make_quiz(material: str, title: str | None, count: int, difficulty: str = "medium") -> QuizResponse:
    limit = settings.summary_max_chars
    if len(material) > limit:
        logger.warning(f"Material truncated from {len(material)} to {limit} chars")
        material = material[:limit]
    header = f"Lesson title: {title}\n\n" if title else ""
    user_message = f"{header}Number of questions: {count}\nDifficulty: {difficulty}\n\nLESSON MATERIAL:\n{material}"
    raw = await chat(system_prompt=SYSTEM_PROMPT, user_message=user_message, max_tokens=3072)
    parsed = _parse(raw)
    questions = []
    for item in parsed.get("questions") or []:
        if not isinstance(item, dict):
            continue
        options = [str(o).strip() for o in (item.get("options") or []) if str(o).strip()]
        index = item.get("answer_index")
        text = str(item.get("question") or "").strip()
        # drop anything malformed rather than showing a broken question
        if not text or len(options) < 2 or not isinstance(index, int) or not 0 <= index < len(options):
            continue
        explanation = str(item.get("explanation") or "").strip() or None
        questions.append(QuizQuestion(question=text, options=options, answer_index=index, explanation=explanation))
    return QuizResponse(questions=questions[:count])
