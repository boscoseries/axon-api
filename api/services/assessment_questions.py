from services.llm_client import chat
from models.schema.schemas import AssessmentOption, AssessmentQuestion, AssessmentQuestionsResponse
from fastapi import HTTPException
from config import settings
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
    You write graded quiz questions for a course, using ONLY the course material you are given.

    The input says how many questions to write, the difficulty (easy, medium or hard) and the question type (single, multiple or mixed).

    Rules:
    - Every question must be answerable from the material, and its correct answer(s) must be stated in it. Never use outside knowledge and never write a question the material does not settle.
    - Question types:
        "single": exactly 4 options and exactly ONE correct.
        "multiple": exactly 5 options and TWO OR THREE correct; the question must say it has more than one answer (for example "Select all that apply").
      For type "mixed", write about a third "multiple" and the rest "single". Otherwise every question has the requested type.
    - Wrong options must be plausible but clearly wrong according to the material. Never "all of the above" or "none of the above".
    - Difficulty: easy is direct recall of a clearly stated fact or term; medium is understanding (why or how, telling similar ideas apart); hard is applying the material to a new situation or combining several points, with close, tempting wrong options.
    - Cover the important ideas across the whole material, in the order they appear, with no two questions about the same thing. When the material is made of several lessons, spread the questions across them.
    - "explanation": one short sentence saying why the answer is right, based on the material.
    - Plain words, in the same language as the material.
    - Write at most the requested number of questions. If the material supports fewer, write fewer. If it supports none, return an empty list.
    - Output ONLY valid JSON, no markdown and no prose outside it.

    Output schema (MUST follow exactly):
    {"questions": [{"question": "...", "question_type": "single"|"multiple", "options": [{"value": "...", "is_correct": true|false}], "explanation": "..."}]}
    """.strip()


def _parse(raw: str) -> dict:
    clean = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse LLM response as JSON: {e}")


async def make_assessment_questions(material: str, title: str | None, count: int, difficulty: str, question_type: str) -> AssessmentQuestionsResponse:
    limit = settings.summary_max_chars
    if len(material) > limit:
        logger.warning(f"Material truncated from {len(material)} to {limit} chars")
        material = material[:limit]
    header = f"Title: {title}\n\n" if title else ""
    user_message = (
        f"{header}Number of questions: {count}\nDifficulty: {difficulty}\nQuestion type: {question_type}\n\n"
        f"MATERIAL:\n{material}"
    )
    raw = await chat(system_prompt=SYSTEM_PROMPT, user_message=user_message, max_tokens=4096)
    parsed = _parse(raw)
    questions = []
    for item in parsed.get("questions") or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("question") or "").strip()
        options = []
        for option in item.get("options") or []:
            if isinstance(option, dict) and str(option.get("value") or "").strip():
                options.append(AssessmentOption(value=str(option["value"]).strip(), is_correct=bool(option.get("is_correct"))))
        right = sum(1 for o in options if o.is_correct)
        kind = "multiple" if item.get("question_type") == "multiple" else "single"
        # drop anything malformed rather than letting a broken question into a graded quiz
        if not text or len(options) < 3 or right < 1 or (kind == "single" and right != 1) or (kind == "multiple" and right < 2):
            continue
        explanation = str(item.get("explanation") or "").strip() or None
        questions.append(AssessmentQuestion(question=text, question_type=kind, options=options, explanation=explanation))
    return AssessmentQuestionsResponse(questions=questions[:count])
