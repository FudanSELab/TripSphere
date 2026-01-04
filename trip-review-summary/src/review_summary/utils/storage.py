from typing import Any

from review_summary.config.settings import get_settings


def get_storage_options() -> dict[str, Any]:
    """Get S3 storage options for connecting to MinIO."""
    minio_settings = get_settings().minio
    return {
        "endpoint_url": minio_settings.endpoint,
        "aws_access_key_id": minio_settings.access_key,
        "aws_secret_access_key": minio_settings.secret_key.get_secret_value(),
    }
