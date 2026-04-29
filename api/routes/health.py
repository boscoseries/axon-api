from fastapi import APIRouter, Depends
from middlewares.auth import require_api_key
from services.llm_client import available_models
from schema.schemas import HealthResponse, ModelsResponse
from config import settings

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns API status and current model in use. No auth required.",
)
async def health():
    return HealthResponse(
        status="ok",
        model=settings.llm_model,
        environment=settings.app_env,
    )


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="List available models",
    description="Returns the models available on the current LLM provider.",
    # dependencies=[Depends(require_api_key)],
)
async def models():
    return ModelsResponse(
        provider="groq",
        models=available_models(),
    )