import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import hashlib
import uuid
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint,
            aws_access_key_id=settings.minio_root_user,
            aws_secret_access_key=settings.minio_root_password,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self.bucket = settings.s3_bucket_name
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")

    def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> dict:
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        extension = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        file_key = f"documents/{uuid.uuid4()}.{extension}"
        self.client.put_object(
            Bucket=self.bucket, Key=file_key, Body=file_bytes,
            ContentType=content_type, Metadata={"original_filename": filename, "sha256": file_hash},
        )
        return {"file_key": file_key, "file_hash": file_hash, "size_bytes": len(file_bytes)}

    def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": file_key}, ExpiresIn=expires_in,
        )

    def download_file(self, file_key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=file_key)
        return response["Body"].read()

    def delete_file(self, file_key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_key)
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {file_key}: {e}")
            return False


storage_service = StorageService()
