import boto3
import logging
from config import settings

logger = logging.getLogger(__name__)

# Initialise once at startup — not per request
_dynamodb = boto3.resource(
    "dynamodb",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)

_counts_table = _dynamodb.Table(settings.dynamo_counts_table)
_logs_table = _dynamodb.Table(settings.dynamo_logs_table)


def create_tables_if_not_exist() -> None:
    """
    Creates DynamoDB tables if they don't already exist.
    Safe to run on every startup — skips creation if tables are present.
    """
    existing = [t.name for t in _dynamodb.tables.all()]

    if settings.dynamo_counts_table not in existing:
        logger.info(f"Creating table: {settings.dynamo_counts_table}")
        _dynamodb.create_table(
            TableName=settings.dynamo_counts_table,
            KeySchema=[
                {"AttributeName": "endpoint", "KeyType": "HASH"},
                {"AttributeName": "date", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "endpoint", "AttributeType": "S"},
                {"AttributeName": "date", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        logger.info(f"Table created: {settings.dynamo_counts_table}")
    else:
        logger.info(f"Table already exists: {settings.dynamo_counts_table}")

    if settings.dynamo_logs_table not in existing:
        logger.info(f"Creating table: {settings.dynamo_logs_table}")
        _dynamodb.create_table(
            TableName=settings.dynamo_logs_table,
            KeySchema=[
                {"AttributeName": "request_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "request_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        logger.info(f"Table created: {settings.dynamo_logs_table}")
    else:
        logger.info(f"Table already exists: {settings.dynamo_logs_table}")