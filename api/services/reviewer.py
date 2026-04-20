from services.llm_client import chat
from schema.schemas import ReviewResponse, Issue, IssueType, IssueSeverity
from config import settings
from fastapi import HTTPException
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a professional document reviewer. Your job is to analyse documents for two things only:
1. Completeness — are expected sections, fields, or content areas missing?
2. Grammar & language errors — spelling mistakes, grammatical errors, unclear phrasing.

You must respond ONLY with a valid JSON object. No preamble, no explanation outside the JSON.

The JSON must follow this exact structure:
{
  "score": <integer 0-100, overall document quality>,
  "summary": "<one paragraph summary of the document quality>",
  "issues": [
    {
      "type": "<grammar | completeness>",
      "severity": "<low | medium | high>",
      "detail": "<specific description of the issue>",
      "location": "<where in the document, e.g. Paragraph 2, Section: Introduction>"
    }
  ]
}

Severity guide:
- high: significantly impacts document usability or meaning
- medium: noticeable issue that should be fixed
- low: minor issue, stylistic or trivial

If the document has no issues, return an empty issues array and a score of 100.
Do not invent issues. Only report what you actually find.
""".strip()


def _truncate(text: str, max_chars: int = 12000) -> str:
    """
    Groq's context window is large but we truncate very long documents
    to stay within token limits and keep costs predictable.
    """
    if len(text) <= max_chars:
        return text
    logger.warning(f"Document truncated from {len(text)} to {max_chars} chars")
    return text[:max_chars] + "\n\n[Document truncated for review]"


def _parse_response(raw: str) -> dict:
    """
    Extract and parse the JSON block from the LLM response.
    LLMs sometimes wrap JSON in markdown code fences — we strip those.
    """
    # Strip markdown code fences if present
    clean = re.sub(r"```json|```", "", raw).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}\nRaw: {raw[:500]}")
        raise HTTPException(
            status_code=500,
            detail="The review model returned an unexpected response format. Please try again."
        )


async def review_document(text: str, filename: str) -> ReviewResponse:
    """
    Core review function.
    Takes extracted plain text, sends to LLM, returns structured ReviewResponse.
    """
    truncated_text = _truncate(text)
    word_count = len(text.split())

    user_message = f"Please review the following document:\n\n{truncated_text}"

    raw_response = await chat(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
    )

    parsed = _parse_response(raw_response)

    # Validate and coerce issues into our schema
    issues = []
    for item in parsed.get("issues", []):
        try:
            issues.append(Issue(
                type=IssueType(item["type"]),
                severity=IssueSeverity(item["severity"]),
                detail=item["detail"],
                location=item.get("location", "Unspecified"),
            ))
        except (KeyError, ValueError) as e:
            logger.warning(f"Skipping malformed issue from LLM: {item} | error: {e}")
            continue

    return ReviewResponse(
        score=int(parsed.get("score", 0)),
        summary=parsed.get("summary", "No summary provided."),
        issues=issues,
        model_used=settings.llm_model,
        document_name=filename,
        word_count=word_count,
    )