"""
S3-Compatible Object Storage Client

Works with both AWS S3 (production) and MinIO (development)
transparently via environment variables.
"""

from __future__ import annotations

import io
from typing import Any

import boto3
import structlog
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import get_settings

logger = structlog.get_logger(__name__)


class StorageClient:
    """
    S3-compatible storage client.

    Abstracts file upload/download/delete operations.
    Uses MinIO locally and AWS S3 in production — the only
    difference is the endpoint_url environment variable.
    """

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazily initialize the S3 client."""
        if self._client is None:
            settings = get_settings()
            kwargs: dict[str, Any] = {
                "service_name": "s3",
                "region_name": settings.s3_region,
                "aws_access_key_id": settings.s3_access_key_id,
                "aws_secret_access_key": settings.s3_secret_access_key,
                "config": BotoConfig(
                    signature_version="s3v4",
                    retries={"max_attempts": 1, "mode": "standard"},
                    connect_timeout=2,
                    read_timeout=2,
                ),
            }
            # MinIO requires explicit endpoint_url; AWS S3 does not
            if settings.s3_endpoint_url:
                kwargs["endpoint_url"] = settings.s3_endpoint_url

            self._client = boto3.client(**kwargs)
        return self._client

    async def ensure_bucket(self) -> None:
        """Create the storage bucket if it doesn't exist."""
        settings = get_settings()
        client = self._get_client()
        try:
            client.head_bucket(Bucket=settings.s3_bucket_name)
            logger.info("s3_bucket_exists", bucket=settings.s3_bucket_name)
        except ClientError:
            try:
                client.create_bucket(
                    Bucket=settings.s3_bucket_name,
                    CreateBucketConfiguration={
                        "LocationConstraint": settings.s3_region,
                    }
                    if settings.s3_region != "us-east-1"
                    else {},
                )
                logger.info("s3_bucket_created", bucket=settings.s3_bucket_name)
            except ClientError as e:
                logger.error("s3_bucket_creation_failed", error=str(e))

    async def upload_file(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload a file to S3.

        Args:
            key: The S3 object key (path within bucket).
            data: File contents as bytes.
            content_type: MIME type.
            metadata: Optional metadata dictionary.

        Returns:
            The full S3 key of the uploaded object.
        """
        settings = get_settings()
        client = self._get_client()

        extra_args: dict[str, Any] = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata

        client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=data,
            **extra_args,
        )

        logger.info("s3_file_uploaded", key=key, size=len(data))
        return key

    async def download_file(self, key: str) -> bytes:
        """
        Download a file from S3.

        Returns:
            File contents as bytes.
        """
        settings = get_settings()
        client = self._get_client()

        response = client.get_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
        )

        data = response["Body"].read()
        logger.info("s3_file_downloaded", key=key, size=len(data))
        return data

    async def delete_file(self, key: str) -> None:
        """Delete a file from S3."""
        settings = get_settings()
        client = self._get_client()

        client.delete_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
        )
        logger.info("s3_file_deleted", key=key)

    async def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """
        Generate a presigned URL for temporary access.

        Args:
            key: S3 object key.
            expiration: URL expiration in seconds (default 1 hour).
            http_method: HTTP method the URL is valid for.

        Returns:
            Presigned URL string.
        """
        settings = get_settings()
        client = self._get_client()

        client_method = "get_object" if http_method == "GET" else "put_object"

        url = client.generate_presigned_url(
            ClientMethod=client_method,
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": key,
            },
            ExpiresIn=expiration,
        )
        return url

    async def list_files(self, prefix: str = "", max_keys: int = 1000) -> list[dict[str, Any]]:
        """List files in S3 with a given prefix."""
        settings = get_settings()
        client = self._get_client()

        response = client.list_objects_v2(
            Bucket=settings.s3_bucket_name,
            Prefix=prefix,
            MaxKeys=max_keys,
        )

        files = []
        for obj in response.get("Contents", []):
            files.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })
        return files

    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        settings = get_settings()
        client = self._get_client()
        try:
            client.head_object(Bucket=settings.s3_bucket_name, Key=key)
            return True
        except ClientError:
            return False


# Module-level singleton
storage_client = StorageClient()
