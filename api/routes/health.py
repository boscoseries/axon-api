from fastapi import APIRouter, Depends
from middlewares.auth import require_api_key
from services.llm_client import available_models
from models.schema.schemas import HealthResponse, ModelsResponse
from config import settings

import logging
logger = logging.getLogger(__name__)

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


@router.get("/test-email", include_in_schema=False)
async def test_email():
    # Test 1: direct send — bypasses logging entirely
    from services.notifier import send_error_email
    try:
        send_error_email(subject="Direct test", body="This is a direct call to send_error_email()")
        direct = "sent"
    except Exception as e:
        direct = str(e)

    # Test 2: via logger — goes through SMTPErrorHandler
    logger.error("Test error via logger.error()")
    
    # Test 3: check if handler is actually registered
    root_logger = logging.getLogger()
    handlers = [type(h).__name__ for h in root_logger.handlers]

    return {
        "direct_email": direct,
        "root_logger_handlers": handlers,
        "smtp_config": {
            "host": settings.smtp_host,
            "port": settings.smtp_port,
            "user": settings.smtp_user,
            "from": settings.smtp_from,
            "to": settings.admin_emails.split(",")[0],
        }
    }