from fastapi import Security, HTTPException, status
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