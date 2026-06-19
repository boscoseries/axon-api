import asyncio
from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependency injected into any route that requires authentication.
    Clients must send:  X-API-Key: <your key>  in the request header.
    """
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Pass your key in the X-API-Key header.",
        )
    return api_key


async def require_api_key_or_free_tier(
    request: Request,
    api_key: str = Security(api_key_header),
) -> str | None:
    """
    Allows requests with a valid API key unconditionally.
    Without a key, grants up to FREE_REQUESTS_LIMIT free requests per IP,
    then returns 429.
    """
    if api_key and api_key == settings.api_key:
        return api_key

    from models.db.utils import check_and_increment_free_tier
    from services.notifier import send_notification_email

    ip = request.client.host
    allowed = await asyncio.to_thread(
        check_and_increment_free_tier, ip, settings.free_requests_limit
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Free tier limit of {settings.free_requests_limit} requests exceeded. "
                   "Pass your API key in the X-API-Key header to continue.",
        )

    try:
        body = await request.json()
        query = body.get("query", "(no query)")
    except Exception:
        query = "(could not parse body)"

    asyncio.create_task(asyncio.to_thread(
        send_notification_email,
        subject="Free Tier Request",
        body=f"IP Address: {ip}\nQuery:      {query}",
    ))

    return None