from services.llm_client import chat
from models.schema.schemas import ReviewResponse
from fastapi import HTTPException
import json
import logging
import re

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
    You are a strict validator for DOCX template placeholders.

    You will receive the full extracted text of a DOCX template. The template uses Jinja-style placeholders of the form {{variable_name}}.

    Input:
    - Template text
    - Allowed placeholder keys: a comma-separated list of bare variable names, e.g. client_name, project_title

    How to check a placeholder against the allowed keys:
    - Strip the {{ and }} from the placeholder to get the bare variable name.
    - That bare name must appear exactly (case-sensitive) in the allowed keys list.
    - Example: {{start_date}} is VALID if start_date is in the allowed keys list.
    - A placeholder appearing multiple times in the text is NOT an issue — repeated use of a valid placeholder is fine.

    Your job:
    1) Determine whether the text contains any placeholder problems that would break Jinja/docxtpl rendering.
    2) Output ONLY valid JSON (no markdown, no prose outside JSON).
    3) If problems exist, list each unique problem with:
    - "type":
        "SINGLE_BRACE": placeholder uses single braces, e.g. {client_name} instead of {{client_name}}.
        "MISSING_CLOSING_BRACES": placeholder starts with "{{" but does not end with "}}".
        "SPACE_IN_VARIABLE": placeholder contains spaces within the variable name, e.g. {{client name}}.
        "MALFORMED_BRACES": stray "}}" or other broken brace patterns with no matching "{{".
        "OTHER": placeholder has correct {{ }} syntax but the bare variable name is NOT in the allowed keys list.
    - "invalid variable": the exact placeholder substring as it appears in the text.
    - "reason": brief explanation. Include the invalid variable and what is wrong.
    - "valid variable": the corrected form as a string (never null):
        - SINGLE_BRACE → add outer braces: {client_name} → {{client_name}}
        - MISSING_CLOSING_BRACES → append missing "}}"
        - SPACE_IN_VARIABLE → replace spaces with underscores
        - MALFORMED_BRACES → "" if the stray braces should be removed; otherwise the fully corrected form
        - OTHER → the closest matching allowed key wrapped in {{ }}, or "" if no close match exists

    Output schema (MUST follow exactly):
    {
    "has_issues": true|false,
    "issues": [
        {
        "type": "...",
        "invalid variable": "...",
        "reason": "...",
        "valid variable": "..."
        }
    ]
    }

    Hard rules:
    - Return {"has_issues": false, "issues": []} if the text is clean or has no placeholders.
    - "invalid variable" MUST be copied verbatim from the input text.
    - Only report each unique ("invalid variable" + "type") pair once — no duplicates.
    - NEVER report a placeholder as an issue if its bare variable name is in the allowed keys list, regardless of how many times it appears.
    - If has_issues is false, issues MUST be an empty array [].
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

    # Strip false OTHER reports where the bare variable name is actually allowed.
    # This catches model hallucinations that slip through despite the prompt rules.
    if allowed_keys and parsed.get("issues"):
        allowed_set = {k.strip() for k in allowed_keys.split(",")}
        parsed["issues"] = [
            issue for issue in parsed["issues"]
            if not (
                issue.get("type") == "OTHER"
                and re.search(r"\{\{(\w+)\}\}", issue.get("invalid variable", ""))
                and re.search(r"\{\{(\w+)\}\}", issue.get("invalid variable", "")).group(1) in allowed_set
            )
        ]
        if not parsed["issues"]:
            parsed["has_issues"] = False

    return ReviewResponse(**parsed)