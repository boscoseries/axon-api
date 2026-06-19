import httpx
import math
from config import settings
import logging

logger = logging.getLogger(__name__)

_HF_URL = "https://router.huggingface.co/hf-inference/models/{model}/pipeline/feature-extraction"


def _normalize(v: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in v))
    return [x / norm for x in v] if norm else v


def _mean_pool(token_embeddings: list[list[float]]) -> list[float]:
    n = len(token_embeddings)
    dim = len(token_embeddings[0])
    return [sum(token_embeddings[j][i] for j in range(n)) / n for i in range(dim)]


async def embed(text: str) -> list[float]:
    url = _HF_URL.format(model=settings.hf_embedding_model)
    headers = {"Authorization": f"Bearer {settings.hf_api_key}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json={"inputs": text})
    response.raise_for_status()
    result = response.json()

    # New HF router returns a flat 1-D list for sentence-transformer models.
    # Keep mean-pool fallback for models that return token-level embeddings.
    if isinstance(result[0], list):
        if isinstance(result[0][0], list):
            vector = _mean_pool(result[0])   # 3-D [batch, tokens, dim]
        else:
            vector = _mean_pool(result)      # 2-D [tokens, dim]
    else:
        vector = result                      # 1-D [dim] — already sentence embedding

    vector = _normalize(vector)
    logger.info(f"HF embed | model={settings.hf_embedding_model} | dim={len(vector)}")
    return vector
