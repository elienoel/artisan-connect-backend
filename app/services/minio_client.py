import io
import json
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)

_PUBLIC_READ_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{settings.MINIO_BUCKET}/*"],
        }
    ],
}


def ensure_bucket() -> None:
    if not _client.bucket_exists(settings.MINIO_BUCKET):
        _client.make_bucket(settings.MINIO_BUCKET)
    _client.set_bucket_policy(settings.MINIO_BUCKET, json.dumps(_PUBLIC_READ_POLICY))


def upload_file(data: bytes, content_type: str, folder: str = "uploads") -> tuple[str, str]:
    """Uploads bytes to MinIO. Returns (object_key, public_url)."""
    ext = content_type.split("/")[-1] if "/" in content_type else "bin"
    object_key = f"{folder}/{uuid.uuid4()}.{ext}"

    _client.put_object(
        settings.MINIO_BUCKET,
        object_key,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET}/{object_key}"
    return object_key, url


def presigned_url(object_key: str, expires_minutes: int = 60) -> str:
    try:
        return _client.presigned_get_object(
            settings.MINIO_BUCKET, object_key, expires=timedelta(minutes=expires_minutes)
        )
    except S3Error:
        return ""
