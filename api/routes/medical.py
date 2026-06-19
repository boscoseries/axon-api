from fastapi import APIRouter, Depends
from middlewares.auth import require_api_key_or_free_tier
from services.retriever import retrieve
from services.llm_client import chat
from models.schema.schemas import MedicalQueryRequest, MedicalQueryResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

_SYSTEM_PROMPT = """
You are a medical information assistant. Answer the user's question using ONLY the context provided below.
Do not mention or cite any source names in your answer — sources are returned separately.
If the context does not contain enough information to answer, say so — do not guess or use outside knowledge.
""".strip()


@router.post(
    "/medical/query",
    response_model=MedicalQueryResponse,
    summary="Medical RAG query",
    description="Embeds the query, retrieves the most relevant chunks from Pinecone, and returns a cited answer.",
    dependencies=[Depends(require_api_key_or_free_tier)],
)
async def medical_query(body: MedicalQueryRequest):
    matches = await retrieve(body.query, top_k=body.top_k)

    def _format_source(raw: str) -> str:
        import os
        return os.path.splitext(raw)[0].replace("-", " ").replace("_", " ").title()

    context_parts = []
    for m in matches:
        raw_source = m.metadata.get("source", "Unknown")
        source = _format_source(raw_source)
        text = m.metadata.get("text", m.metadata.get("content", ""))
        context_parts.append(f"[Source: {source}]\n{text}")

    context = "\n\n".join(context_parts)
    sources = list(dict.fromkeys(
        _format_source(m.metadata.get("source", "Unknown")) for m in matches
    ))

    logger.info(f"RAG query | chunks={len(matches)} | sources={sources}")

    answer = await chat(
        system_prompt=_SYSTEM_PROMPT,
        user_message=f"Context:\n{context}\n\nQuestion: {body.query}",
    )

    return MedicalQueryResponse(
        answer=answer,
        sources=sources,
        chunks_used=len(matches),
    )
