import logging, time, asyncio

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from services.notifier import send_error_email

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start = time.time()

        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = round((time.time() - start) * 1000)
            body = (
                f"Method:   {request.method}\n"
                f"Path:     {request.url.path}\n"
                f"Error:    {str(e)}\n"
                f"Duration: {duration_ms}ms\n"
                f"Client:   {request.client.host if request.client else 'unknown'}\n"
            )
            asyncio.create_task(
                asyncio.to_thread(send_error_email, subject=f"Unhandled exception on {request.url.path}", body=body)
            )
            raise

        duration_ms = round((time.time() - start) * 1000)

        logger.info(
            f"{request.method} {request.url.path} "
            f"| status={response.status_code} "
            f"| duration={duration_ms}ms"
        )

        if response.status_code >= 500:
            body = (
                f"Method:   {request.method}\n"
                f"Path:     {request.url.path}\n"
                f"Status:   {response.status_code}\n"
                f"Duration: {duration_ms}ms\n"
                f"Client:   {request.client.host if request.client else 'unknown'}\n"
            )
            asyncio.create_task(
                asyncio.to_thread(send_error_email, subject=f"{response.status_code} on {request.url.path}", body=body)
            )

        return response