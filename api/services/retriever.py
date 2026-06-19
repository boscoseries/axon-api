from pinecone import Pinecone
from config import settings
from services.embedder import embed
import logging

logger = logging.getLogger(__name__)

_pc: Pinecone | None = None
_index = None


def _get_index():
    global _pc, _index
    if _index is None:
        _pc = Pinecone(api_key=settings.pinecone_api_key)
        _index = _pc.Index(settings.pinecone_index)
    return _index


async def retrieve(query: str, top_k: int | None = None) -> list:
    k = top_k or settings.pinecone_top_k
    vector = await embed(query)
    index = _get_index()

    results = index.query(vector=vector, top_k=k, include_metadata=True)
    logger.info(f"Pinecone query | top_k={k} | matches={len(results.matches)}")
    return results.matches
