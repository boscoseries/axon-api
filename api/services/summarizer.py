from services.llm_client import chat
from models.schema.schemas import SummarizeResponse
from fastapi import HTTPException
from config import settings
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
    You summarise teaching material for learners.

    You will receive the text of a lesson (usually a transcript of narration or a video) and optionally its title.

    Rules:
    - Use only what the text says. Do not add facts, examples or advice that are not in it.
    - "summary": a clear summary of the whole lesson, from start to finish. Make it as long as it needs to be to cover everything important; do not cut it short and do not pad it.
    - "key_points": the main points of the lesson, in the order they appear, each a complete, self-contained sentence a learner could read on its own. Group related details into one point instead of listing each detail separately: for example, the rules, steps or parts of one idea become a single point that names them, not one line per rule. Usually 6 to 12 points; use more only if the lesson really makes that many separate main points. Do not leave out an important idea, and do not split one idea across several points.
    - Write in the same language as the text, in plain words.
    - If the text is too short or empty of content to summarise, return an empty summary and an empty key_points list.
    - Output ONLY valid JSON, no markdown and no prose outside it.

    Output schema (MUST follow exactly):
    {"summary": "...", "key_points": ["...", "..."]}
    """.strip()

def _truncate(text: str) -> str:
    limit = settings.summary_max_chars
    if len(text) <= limit:
        return text
    logger.warning(f"Text truncated from {len(text)} to {limit} chars")
    return text[:limit]


def _parse_response(raw: str) -> dict:
    clean = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse LLM response as JSON: {e}")


async def summarize_text(text: str, title: str | None = None, max_points: int | None = None) -> SummarizeResponse:
    header = f"Title: {title}\n\n" if title else ""
    limit_note = f"Give at most {max_points} key points.\n\n" if max_points else ""
    user_message = f"{header}{limit_note}Text:\n{_truncate(text)}"
    # a full set of key points needs more room than the default reply size
    raw = await chat(system_prompt=SYSTEM_PROMPT, user_message=user_message, max_tokens=4096)
    parsed = _parse_response(raw)
    points = [str(p).strip() for p in (parsed.get("key_points") or []) if str(p).strip()]
    return SummarizeResponse(summary=str(parsed.get("summary") or "").strip(), key_points=points[:max_points] if max_points else points)
