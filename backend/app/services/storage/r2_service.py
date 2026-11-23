import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Optional, BinaryIO
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()


class R2StorageService:
    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._enabled = bool(
            self.settings.R2_ACCOUNT_ID
            and self.settings.R2_ACCESS_KEY_ID
            and self.settings.R2_SECRET_ACCESS_KEY
            and self.settings.R2_BUCKET_NAME
        )

    @property
    def client(self):
        if self._client is None and self._enabled:
            self._client = boto3.client(
                "s3",
                endpoint_url=f"https://{self.settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                aws_access_key_id=self.settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=self.settings.R2_SECRET_ACCESS_KEY,
                region_name="auto",
            )
        return self._client

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def upload_file(
        self,
        file_content: bytes,
        object_key: str,
        content_type: str = "application/octet-stream",
    ) -> bool:
        if not self._enabled:
            logger.warning("R2 storage not configured, skipping upload")
            return False

        try:
            self.client.put_object(
                Bucket=self.settings.R2_BUCKET_NAME,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
            )
            logger.info("File uploaded to R2", object_key=object_key)
            return True
        except ClientError as e:
            logger.error("R2 upload failed", object_key=object_key, error=str(e))
            return False

    def download_file(self, object_key: str) -> Optional[bytes]:
        if not self._enabled:
            return None

        try:
            response = self.client.get_object(
                Bucket=self.settings.R2_BUCKET_NAME,
                Key=object_key,
            )
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning("File not found in R2", object_key=object_key)
            else:
                logger.error("R2 download failed", object_key=object_key, error=str(e))
            return None

    def delete_file(self, object_key: str) -> bool:
        if not self._enabled:
            return False

        try:
            self.client.delete_object(
                Bucket=self.settings.R2_BUCKET_NAME,
                Key=object_key,
            )
            logger.info("File deleted from R2", object_key=object_key)
            return True
        except ClientError as e:
            logger.error("R2 delete failed", object_key=object_key, error=str(e))
            return False

    def file_exists(self, object_key: str) -> bool:
        if not self._enabled:
            return False

        try:
            self.client.head_object(
                Bucket=self.settings.R2_BUCKET_NAME,
                Key=object_key,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error("R2 head_object failed", object_key=object_key, error=str(e))
            return False

    def generate_presigned_url(
        self, object_key: str, expiration: int = 3600
    ) -> Optional[str]:
        if not self._enabled:
            return None

        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.settings.R2_BUCKET_NAME, "Key": object_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logger.error("Presigned URL generation failed", object_key=object_key, error=str(e))
            return None

    def get_public_url(self, object_key: str) -> Optional[str]:
        if not self._enabled or not self.settings.R2_PUBLIC_URL:
            return None
        return f"{self.settings.R2_PUBLIC_URL.rstrip('/')}/{object_key}"


r2_storage_service = R2StorageService()