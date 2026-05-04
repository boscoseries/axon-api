from services.llm_client import chat
from models.schema.schemas import ReviewResponse
from fastapi import HTTPException
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
    You are a strict validator for DOCX template placeholders.

    You will receive the full extracted text of a DOCX template. The template is expected to use Jinja-style placeholders of the form:
    {{variable_name}}
    
    Input:
    - Template text
    - Allowed placeholder keys (comma-separated)

    Valid placeholders:
    - Any of the allowed keys wrapped in double curly braces, e.g. {{client_name}}, {{project_title}}.

    Your job:
    1) Determine whether the text contains any placeholder problems that would likely break Jinja/docxtpl rendering.
    2) Output ONLY valid JSON (no markdown, no prose outside JSON).
    3) If problems exist, list each problem with:
    - "type": 
        "SINGLE_BRACE": if a placeholder uses single braces, e.g. {client_name} instead of {{client_name}}.
        "MISSING_CLOSING_BRACES": if a placeholder starts with "{{" but does not end with "}}".
        "SPACE_IN_VARIABLE": if a placeholder contains spaces within the variable name.
        "MALFORMED_BRACES": if there are stray "}}" or other broken brace patterns.
        "OTHER": if a placeholder uses correct syntax but the variable name is not in the allowed keys.
    - "invalid variable": the exact placeholder substring as it appears in the text
    - "reason": a brief explanation of the issue. include the invalid variable in the reason for clarity.
    - "valid variable": the corrected placeholder string

    Output schema (MUST follow exactly):
    {
    "has_issues": true|false,
    "issues": [
        {
        "type": "...",
        "invalid variable": "...",
        "reason": "...",
        "valid variable": "...",
        }
    ]
    }

    Hard rules:
    - If the text is perfectly clean with no placeholder issues, return {"has_issues": false, "issues": []}.
    - If the text has no placeholders at all, return {"has_issues": false, "issues": []}.
    - "invalid variable" MUST be copied verbatim from the input text (exact substring).
    - Do not invent placeholders not present in the input's Allowed placeholder keys.
    - If has_issues is false, issues MUST be an empty array, [].
    - Do not include duplicates (same "invalid variable" + same "type").
    - If a placeholder is correct, do not list it.

    Report these problems:
    - SINGLE_BRACE: if a placeholder uses single braces, e.g. {client_name} instead of {{client_name}}.
    - MISSING_CLOSING_BRACES: if a placeholder starts with "{{" but does not end with "}}".
    - SPACE_IN_VARIABLE: if a placeholder contains spaces within the variable name.
    - MALFORMED_BRACES: if there are stray "}}" or other broken brace patterns.
    - OTHER: if a placeholder uses correct syntax but the variable name is not in the Allowed placeholder keys.
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response as JSON: {e}\nRaw: {raw[:500]}"
        )


async def review_document(text: str, allowed_keys: str = None) -> ReviewResponse:
    """
    Core review function.
    Takes extracted plain text, sends to LLM, returns structured ReviewResponse.
    """

    if allowed_keys:
        user_message = f"""
            Validate placeholders in the following DOCX template text.

            Template text:
            {text}

            Allowed placeholder keys:
            {allowed_keys}

            """.strip()
    else:
        user_message = f"""
            Validate placeholders in the following DOCX template text.

            Template text:
            {text}

            """.strip()

    raw_response = await chat(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
    )

    parsed = _parse_response(raw_response)
    return ReviewResponse(**parsed)