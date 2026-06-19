from groq import Groq
from openai import OpenAI
import anthropic as Anthropic
from config import settings
import logging

logger = logging.getLogger(__name__)


def parse_model(model_str: str) -> tuple[str, str]:
    """Split 'provider/model-name' into (provider, model). Defaults to groq if no prefix."""
    if "/" in model_str:
        provider, model = model_str.split("/", 1)
        return provider.lower(), model
    return "groq", model_str


def get_provider_map() -> dict[str, list[str]]:
    """Build provider → [models] from the LLM_AVAILABLE_MODELS env var at call time."""
    result: dict[str, list[str]] = {}
    for entry in settings.llm_available_models.split(","):
        entry = entry.strip()
        if not entry:
            continue
        provider, _ = parse_model(entry)
        result.setdefault(provider, []).append(entry)
    return result


def _openai_compat_chat(client, model: str, system_prompt: str, user_message: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.5,
        max_tokens=2048,
    )
    logger.info(f"Response received | tokens_used={response.usage.total_tokens}")
    return response.choices[0].message.content


async def chat(system_prompt: str, user_message: str) -> str:
    """
    Send a prompt to the configured LLM and return the response text.

    Provider is determined by the prefix in settings.llm_model:
      - groq/...       → Groq
      - openai/...     → OpenAI
      - anthropic/...  → Anthropic
    Change only the LLM_MODEL env var to switch providers at runtime.
    """
    provider, model = parse_model(settings.llm_model)
    logger.info(f"Sending request | provider={provider} | model={model}")

    try:
        if provider == "groq":
            client = Groq(api_key=settings.groq_api_key)
            return _openai_compat_chat(client, model, system_prompt, user_message)

        elif provider == "openai":
            client = OpenAI(api_key=settings.openai_api_key)
            return _openai_compat_chat(client, model, system_prompt, user_message)

        elif provider == "anthropic":
            client = Anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            logger.info(f"Response received | tokens_used={response.usage.input_tokens + response.usage.output_tokens}")
            return response.content[0].text

        else:
            raise ValueError(f"Unknown provider '{provider}'. Use groq/, openai/, or anthropic/ prefix in LLM_MODEL.")

    except Exception as e:
        logger.error(f"LLM provider error: {str(e)}")
        raise


def available_models(provider: str | None = None) -> list[str]:
    provider_map = get_provider_map()
    if provider:
        return provider_map.get(provider, [])
    return [m for models in provider_map.values() for m in models]
