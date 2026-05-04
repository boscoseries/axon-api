import logging, asyncio, uuid
from datetime import datetime, timezone
from .tables import _counts_table, _logs_table
from config import settings

logger = logging.getLogger(__name__)

from decimal import Decimal


def _serialize(value):
    """
    Recursively convert value to DynamoDB-safe types.
    Handles Pydantic models, lists, dicts, and primitives.
    DynamoDB only accepts: str, int, Decimal, bool, list, dict, set.
    float and Pydantic models will fail without this.
    """
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return _serialize(value.model_dump())
    if hasattr(value, "dict"):
        return _serialize(value.dict())
    if isinstance(value, list):
        return [_serialize(i) for i in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items() if v is not None}
    if isinstance(value, float):
        return Decimal(str(value))
    return value


def  log_count(endpoint: str) -> None:
    """
    Atomically increment the request counter for an endpoint on today's date.
    Creates the record if it doesn't exist yet.
    """

    if settings.app_env != "production":
        return
    
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        _counts_table.update_item(
            Key={
                "endpoint": endpoint,
                "date": today,
            },
            UpdateExpression="ADD #count :inc",
            ExpressionAttributeNames={"#count": "count"},
            ExpressionAttributeValues={":inc": 1},
        )

        # Increment all-time total
        _counts_table.update_item(
            Key={"endpoint": endpoint, "date": "ALL"},
            UpdateExpression="ADD #count :inc",
            ExpressionAttributeNames={"#count": "count"},
            ExpressionAttributeValues={":inc": 1},
        )

    except Exception as e:
        logger.error(f"DynamoDB count update failed | endpoint={endpoint} | error={e}")


def log_request(
    endpoint: str,
    provider: str = None,
    error: str = None,
    requester: str = None,
    response: dict = None,
) -> None:
    """
    Write a full request log to axon-request-logs.
    Optional fields are only written if they have values —
    DynamoDB does not accept None on typed attributes.
    Reusable across any endpoint, not tied to /api/review.
    """

    if settings.app_env != "production":
        return
    
    try:
        request_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            "request_id": request_id,
            "timestamp": timestamp,
            "endpoint": endpoint
        }

        if provider:        item["provider"] = provider
        if error:           item["error"] = error
        if requester:       item["requester"] = requester
        if response:        item["response"] = _serialize(response)

        _logs_table.put_item(Item=item)

    except Exception as e:
        logger.error(f"DynamoDB log write failed | error={e}")