"""Attachment storage backends."""

from __future__ import annotations
import aiofiles  # type: ignore[import-untyped]
from config.settings import get_settings
import contextlib
from dataclasses import dataclass
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import AsyncIterator, Optional
from uuid import UUID

try:  # Optional import for S3 support
    import aioboto3
except ImportError:  # pragma: no cover - handled at runtime when selecting backend
    aioboto3 = None


@dataclass(slots=True)
class StorageResult:
    """Result data returned after saving an attachment."""

    relative_path: str
    size         : int
    content_type : str
    filename     : str


def _build_filename(original: str, attachment_id: UUID, preferred_filename: Optional[str]) -> str:
    chosen = preferred_filename or original
    name_part, dot, extension = chosen.rpartition(".")
    base = name_part or chosen
    sanitized_base = "_".join(base.split()) or attachment_id.hex
    suffix = f".{extension}" if dot else ""
    if preferred_filename:
        return f"{attachment_id.hex}_{sanitized_base}{suffix}"
    return f"{attachment_id.hex}{suffix}"


def _build_relative_key(tenant_identifier: str, attachment_id: UUID, filename: str) -> str:
    shard = attachment_id.hex[:2]
    posix_path = PurePosixPath(tenant_identifier.strip("/")) / shard / attachment_id.hex / filename
    return posix_path.as_posix()


def _posix_to_path(posix_key: str) -> Path:
    posix_parts = PurePosixPath(posix_key).parts
    return Path(*posix_parts)


class AttachmentStorage:
    """Abstract storage contract for attachment persistence."""

    async def save(
        self,
        upload: UploadFile,
        tenant_identifier: str,
        attachment_id: UUID,
        preferred_filename: Optional[str] = None,
    ) -> StorageResult:
        raise NotImplementedError

    async def delete(self, relative_path: str) -> None:
        raise NotImplementedError

    async def generate_presigned_url(self, relative_path: str, expires_in: int) -> str:
        raise NotImplementedError


class LocalAttachmentStorage(AttachmentStorage):
    """File-system based attachment storage."""

    def __init__(self, base_path: Path, chunk_size: int = 524_288):
        self.base_path = base_path
        self.chunk_size = chunk_size

    async def save(
        self,
        upload: UploadFile,
        tenant_identifier: str,
        attachment_id: UUID,
        preferred_filename: Optional[str] = None,
    ) -> StorageResult:
        original_name = upload.filename or "attachment"
        safe_name     = _build_filename(original_name, attachment_id, preferred_filename)
        relative_key  = _build_relative_key(tenant_identifier, attachment_id, safe_name)
        relative_path = _posix_to_path(relative_key)
        absolute_path = self.base_path.joinpath(relative_path)
        await run_in_threadpool(absolute_path.parent.mkdir, parents=True, exist_ok=True)

        size = 0
        content_type = upload.content_type or "application/octet-stream"

        async with aiofiles.open(absolute_path, "wb") as buffer:
            while chunk := await upload.read(self.chunk_size):
                size += len(chunk)
                await buffer.write(chunk)

        await upload.seek(0)
        return StorageResult(relative_path=relative_key, size=size, content_type=content_type, filename=safe_name)

    async def delete(self, relative_path: str) -> None:
        target = self.base_path.joinpath(_posix_to_path(relative_path))
        if not target.exists():
            return
        await run_in_threadpool(target.unlink)
        await self._cleanup_empty_parents(target.parent)

    async def generate_presigned_url(self, relative_path: str, expires_in: int) -> str:
        """Return a relative path that can be proxied by the API."""
        return f"/attachments/{relative_path}"

    async def _cleanup_empty_parents(self, start: Path) -> None:
        current = start
        while current != self.base_path and current.exists():
            try:
                await run_in_threadpool(current.rmdir)
            except OSError:
                break
            current = current.parent


class S3AttachmentStorage(AttachmentStorage):
    """S3-compatible object storage backend."""

    def __init__(self, bucket: str, region: Optional[str], endpoint_url: Optional[str], chunk_size: int = 524_288):
        if aioboto3 is None:  # pragma: no cover - runtime check
            raise RuntimeError("aioboto3 is required for the S3 attachment backend")

        self.bucket       = bucket
        self.region       = region
        self.endpoint_url = endpoint_url
        self.chunk_size   = chunk_size
        self._session     = aioboto3.Session()

    @contextlib.asynccontextmanager
    async def _client(self) -> AsyncIterator["aioboto3.client"]:
        async with self._session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
        ) as client:
            yield client

    async def save(
        self,
        upload: UploadFile,
        tenant_identifier: str,
        attachment_id: UUID,
        preferred_filename: Optional[str] = None,
    ) -> StorageResult:
        original_name = upload.filename or "attachment"
        filename      = _build_filename(original_name, attachment_id, preferred_filename)
        key           = _build_relative_key(tenant_identifier, attachment_id, filename)
        content_type  = upload.content_type or "application/octet-stream"

        await upload.seek(0)
        async with self._client() as client:
            await client.upload_fileobj(upload.file, self.bucket, key, ExtraArgs={"ContentType": content_type})

        size = await upload.seek(0, 2)  # position at end gives total size
        await upload.seek(0)
        return StorageResult(relative_path=key, size=size, content_type=content_type, filename=filename)

    async def delete(self, relative_path: str) -> None:
        async with self._client() as client:
            await client.delete_object(Bucket=self.bucket, Key=relative_path)

    async def generate_presigned_url(self, relative_path: str, expires_in: int) -> str:
        async with self._client() as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": relative_path},
                ExpiresIn=expires_in,
            )
        return url


@lru_cache
def get_attachment_storage() -> AttachmentStorage:
    """Return a configured attachment storage backend."""
    settings = get_settings()
    if settings.ATTACHMENT_STORAGE_BACKEND.lower() == "s3":
        if not settings.ATTACHMENT_STORAGE_S3_BUCKET:
            raise RuntimeError("ATTACHMENT_STORAGE_S3_BUCKET must be set for S3 backend")
        return S3AttachmentStorage(
            bucket       = settings.ATTACHMENT_STORAGE_S3_BUCKET,
            region       = settings.ATTACHMENT_STORAGE_S3_REGION,
            endpoint_url = settings.ATTACHMENT_STORAGE_S3_ENDPOINT,
            chunk_size   = settings.ATTACHMENT_STORAGE_CHUNK_SIZE,
        )

    base_path = Path(settings.ATTACHMENT_STORAGE_BASE_PATH).expanduser().resolve()
    base_path.mkdir(parents=True, exist_ok=True)
    return LocalAttachmentStorage(base_path=base_path, chunk_size=settings.ATTACHMENT_STORAGE_CHUNK_SIZE)
