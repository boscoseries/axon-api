from services.llm_client import chat
from models.schema.schemas import CourseCopyResponse
from fastapi import HTTPException
from config import settings
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
    You write the marketing copy of an online course for its catalogue page: a description and a short summary.

    You receive the course title, optionally its level and category, its outline (modules and lessons, with what the lessons say) and, sometimes, the copy it has now.

    Rules:
    - Use only what the outline tells you about the course. Never invent topics, outcomes, certificates, prices, durations, instructors or claims that the outline does not support.
    - If current copy is given, keep what is accurate in it and improve the rest; do not contradict the outline.
    - "description": 2 or 3 short paragraphs as simple HTML, each wrapped in <p>...</p>. Say what the course is about, what the learner will cover (you may add one <ul> of 3 to 6 <li> points drawn from the modules), and who it suits only if the outline makes that clear. No headings, no markdown, no other tags.
    - "summary": plain text, one or two sentences (at most 280 characters), no HTML. It must read well on its own as the one-line pitch.
    - Write in the same language as the title and outline, in the requested tone (professional, friendly or concise), in plain words, with no hype.
    - Output ONLY valid JSON, no markdown fences and no prose outside it.

    Output schema (MUST follow exactly):
    {"description": "<p>...</p>", "summary": "..."}
    """.strip()


def _parse(raw: str) -> dict:
    clean = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse LLM response as JSON: {e}")


async def make_course_copy(title, outline, level, category, current_description, current_summary, tone) -> CourseCopyResponse:
    limit = settings.summary_max_chars
    if len(outline) > limit:
        outline = outline[:limit]
    lines = [f"Course title: {title}"]
    if level:
        lines.append(f"Level: {level}")
    if category:
        lines.append(f"Category: {category}")
    lines.append(f"Tone: {tone}")
    if current_description:
        lines.append(f"\nCURRENT DESCRIPTION:\n{current_description[:3000]}")
    if current_summary:
        lines.append(f"\nCURRENT SUMMARY:\n{current_summary[:1000]}")
    lines.append(f"\nOUTLINE:\n{outline}")
    raw = await chat(system_prompt=SYSTEM_PROMPT, user_message="\n".join(lines), max_tokens=1500)
    parsed = _parse(raw)
    description = str(parsed.get("description") or "").strip()
    summary = re.sub(r"<[^>]+>", "", str(parsed.get("summary") or "")).strip()
    if not description or not summary:
        raise HTTPException(status_code=502, detail="The model returned no copy.")
    return CourseCopyResponse(description=description, summary=summary[:300])
