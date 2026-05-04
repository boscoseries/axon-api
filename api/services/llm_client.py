from groq import Groq
from config import settings
from fastapi import HTTPException
import logging, json

logger = logging.getLogger(__name__)

# Initialise once at startup — not per request
_client = Groq(api_key=settings.groq_api_key)


async def chat(system_prompt: str, user_message: str) -> str:
    """
    Send a prompt to the configured LLM and return the response text.

    Provider: Groq (llama3 / mixtral)
    Swap this function's internals to switch to OpenAI, Anthropic, or Ollama
    without touching any other part of the codebase.
    """
    try:
        logger.info(f"Sending request to Groq | model={settings.llm_model}")

        response = _client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,      # low temp = consistent, deterministic output
            max_tokens=2048,
        )

        result = response.choices[0].message.content
        logger.info(f"Groq response received | tokens_used={response.usage.total_tokens}")
        return result

    except Exception as e:
        logger.error(f"LLM provider error in chat function: {str(e)}")    
        return json.dumps({
            "has_issues": False,
            "issues": []
        })


def available_models() -> list[str]:
    """
    Return the models available on this provider.
    Extend this if you add dynamic model listing.
    """
    return [
        "llama3-8b-8192",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
    ]