from groq import Groq
from openai import OpenAI
import anthropic as Anthropic
from config import settings
import logging

logger = logging.getLogger(__name__)

# Runtime active model — overrides settings.llm_model after an auto-switch.
# Persists for the process lifetime without a restart or redeployment.
_active_model: str | None = None

# Error substrings that mean the model itself is gone (not transient).
_FATAL_MODEL_ERRORS = (
    "model_decommissioned",
    "model_not_found",
    "model_does_not_exist",
    "decommissioned",
    "does not exist",
    "no such model",
)


def get_active_model() -> str:
    return _active_model or settings.llm_model


def set_active_model(model: str) -> None:
    global _active_model
    _active_model = model


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


def _is_fatal_model_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(code in msg for code in _FATAL_MODEL_ERRORS)


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


def _call_model(model_str: str, system_prompt: str, user_message: str) -> str:
    provider, model = parse_model(model_str)

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


async def chat(system_prompt: str, user_message: str) -> str:
    """
    Send a prompt to the configured LLM and return the response text.

    On a fatal model error (decommissioned / not found), automatically tries
    each model in LLM_FALLBACK_MODELS in order and promotes the first one
    that succeeds as the new active model — no restart required.
    """
    current = get_active_model()
    fallbacks = [
        m.strip()
        for m in settings.llm_available_models.split(",")
        if m.strip() and m.strip() != current
    ]
    models_to_try = [current] + fallbacks

    last_error: Exception | None = None
    for model_str in models_to_try:
        logger.info(f"Sending request | model={model_str}")
        try:
            result = _call_model(model_str, system_prompt, user_message)
            if model_str != current:
                logger.error(f"Auto-switched active model: {current} → {model_str}")
                set_active_model(model_str)
            return result
        except Exception as e:
            if _is_fatal_model_error(e):
                logger.error(f"Model '{model_str}' unavailable: {e}. Trying next fallback.")
                last_error = e
                continue
            raise

    raise last_error or RuntimeError("All configured models failed.")


def available_models(provider: str | None = None) -> list[str]:
    provider_map = get_provider_map()
    if provider:
        return provider_map.get(provider, [])
    return [m for models in provider_map.values() for m in models]
