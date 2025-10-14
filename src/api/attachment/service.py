"""Attachment service layer."""

from __future__ import annotations
from api.attachment.models import Attachable, Attachment
from api.attachment.schema import (
    AttachmentCreate,
    AttachmentFilterParams,
    AttachmentUpdate,
)
from api.attachment.storage import AttachmentStorage, get_attachment_storage
from api.common.base_service import BaseService
from config import get_settings
from constants.attachments import (
    MAX_UPLOAD_SIZE,
    SUPPORTED_ARCHIVE_EXTENSIONS,
    SUPPORTED_ARCHIVE_MIME_TYPES,
    SUPPORTED_DOCUMENT_EXTENSIONS,
    SUPPORTED_DOCUMENT_MIME_TYPES,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    SUPPORTED_VIDEO_MIME_TYPES,
    AttachmentKind,
    AttachmentTarget,
)
from database.constraint_handler import constraint_handler
from dataclasses import dataclass
from exceptions import ExceptionFactory
from fastapi import UploadFile
from security.jwt.tokens import AuthenticatedUser
from sqlalchemy import delete, func, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import true
from typing import Optional
from utils.odata_parser import ODataToSQLAlchemy
from uuid import UUID, uuid4
from web import PaginationUtil


@dataclass(slots=True)
class AttachmentListResult:
    """Container for paginated attachment data."""

    attachments: list[Attachment]
    total: int


class AttachmentService(BaseService[Attachment, AttachmentCreate, AttachmentUpdate]):
    """Domain service encapsulating attachment workflows."""

    def __init__(self, storage: AttachmentStorage):
        super().__init__(Attachment)
        self.storage = storage
        self.settings = get_settings()


    def get_search_fields(self) -> list[str]:
        return [
            "filename",
            "original_filename",
            "description",
            "category",
            "file_type",
        ]


    async def create_attachment(
        self,
        db: AsyncSession,
        payload: AttachmentCreate,
        upload: UploadFile,
        tenant_identifier: str,
        current_user: AuthenticatedUser,
    ) -> Attachment:
        """Persist metadata, store file, and create polymorphic link."""
        if upload is None:
            raise ExceptionFactory.validation_failed("file", "File upload is required")

        attachment_id = uuid4()
        storage_result = await self.storage.save(
            upload             = upload,
            tenant_identifier  = tenant_identifier,
            attachment_id      = attachment_id,
            preferred_filename = payload.filename,
        )

        original_name = payload.original_filename or upload.filename or storage_result.filename
        extension = self._infer_extension(payload.extension, original_name, storage_result.filename)
        size = storage_result.size
        if size > MAX_UPLOAD_SIZE:
            raise ExceptionFactory.validation_failed("file", "File exceeds maximum allowed size")

        attachment = Attachment(
            id                = attachment_id,
            filename          = storage_result.filename,
            original_filename = original_name,
            file_type         = payload.file_type or storage_result.content_type,
            extension         = extension,
            size              = size,
            file_path         = storage_result.relative_path,
            description       = payload.description,
            category          = payload.category,
            user_id           = payload.user_id or current_user.user_id,
        )

        attachable = Attachable(
            attachment_id   = attachment_id,
            attachable_type = payload.target_type.value,
            attachable_id   = payload.target_id,
        )

        try:
            db.add(attachment)
            db.add(attachable)
            await db.commit()
            await db.refresh(attachment)
            return attachment
        except IntegrityError as exc:
            await db.rollback()
            raise constraint_handler.handle_violation(
                exc,
                {
                    "operation"      : "create_attachment",
                    "attachment_id"  : str(attachment_id),
                    "attachable_type": payload.target_type.value,
                    "attachable_id"  : str(payload.target_id),
                },
            ) from exc


    async def list_attachments(
        self,
        db: AsyncSession,
        filters: AttachmentFilterParams,
        page: int,
        size: int,
        odata_filter: Optional[str] = None,
    ) -> AttachmentListResult:
        """Return paginated attachments applying typed and OData filters."""
        query = (
            select(Attachment)
            .options(selectinload(Attachment.attachables))
            .order_by(Attachment.created_at.desc())
        )
        count_query = select(func.count()).select_from(Attachment)

        conditions: list = []
        joins_attachable = False

        if not filters.include_deleted:
            conditions.append(Attachment.deleted_at.is_(None))

        if filters.category:
            conditions.append(Attachment.category == filters.category)

        if filters.file_type:
            conditions.append(Attachment.file_type.ilike(f"%{filters.file_type}%"))

        if filters.user_id:
            conditions.append(Attachment.user_id == filters.user_id)

        if filters.min_size is not None:
            conditions.append(Attachment.size >= filters.min_size)

        if filters.max_size is not None:
            conditions.append(Attachment.size <= filters.max_size)

        if filters.target_type is not None or filters.target_id is not None:
            query = query.join(Attachable, Attachment.id == Attachable.attachment_id)
            count_query = count_query.join(Attachable, Attachment.id == Attachable.attachment_id)
            joins_attachable = True
            if filters.target_type is not None:
                conditions.append(Attachable.attachable_type == filters.target_type.value)
            if filters.target_id is not None:
                conditions.append(Attachable.attachable_id == filters.target_id)

        if filters.kind is not None:
            conditions.append(self._build_kind_condition(filters.kind))

        for condition in conditions:
            query = query.where(condition)
            count_query = count_query.where(condition)

        if odata_filter:
            try:
                parser = ODataToSQLAlchemy(Attachment)
                odata_condition = parser.parse(odata_filter)
            except Exception as exc:
                raise ExceptionFactory.validation_failed("$filter", "Invalid OData expression") from exc
            if odata_condition is not None:
                query = query.where(odata_condition)
                count_query = count_query.where(odata_condition)

        if joins_attachable:
            query = query.distinct(Attachment.id)

        total       = await db.scalar(count_query) or 0
        offset      = PaginationUtil.get_offset(page, size)
        query       = query.offset(offset).limit(size)
        result      = await db.execute(query)
        attachments = result.scalars().unique().all()
        return AttachmentListResult(attachments=attachments, total=total)


    async def get_attachment(self, db: AsyncSession, attachment_id: UUID) -> Attachment:
        query = (
            select(Attachment)
            .where(Attachment.id == attachment_id)
            .options(selectinload(Attachment.attachables))
        )
        result = await db.execute(query)
        attachment = result.scalar_one_or_none()
        if not attachment:
            raise ExceptionFactory.not_found("Attachment", attachment_id)
        return attachment


    async def update_attachment(
        self,
        db: AsyncSession,
        attachment_id: UUID,
        payload: AttachmentUpdate,
    ) -> Attachment:
        attachment = await self.get_attachment(db, attachment_id)
        if attachment.deleted_at is not None:
            raise ExceptionFactory.validation_failed("attachment", "Cannot update a deleted attachment")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(attachment, key, value)

        try:
            await db.commit()
            await db.refresh(attachment)
            return attachment
        except IntegrityError as exc:
            await db.rollback()
            raise constraint_handler.handle_violation(
                exc,
                {
                    "operation"    : "update_attachment",
                    "attachment_id": str(attachment_id),
                },
            ) from exc


    async def link_attachment(
        self,
        db: AsyncSession,
        attachment_id: UUID,
        target_type: AttachmentTarget,
        target_id: UUID,
    ) -> Attachment:
        attachment = await self.get_attachment(db, attachment_id)
        if attachment.deleted_at is not None:
            raise ExceptionFactory.validation_failed("attachment", "Cannot link a deleted attachment")

        link = Attachable(
            attachment_id   = attachment_id,
            attachable_type = target_type.value,
            attachable_id   = target_id,
        )
        try:
            db.add(link)
            await db.commit()
            await db.refresh(attachment)
            return attachment
        except IntegrityError as exc:
            await db.rollback()
            raise constraint_handler.handle_violation(
                exc,
                {
                    "operation"      : "link_attachment",
                    "attachment_id"  : str(attachment_id),
                    "attachable_type": target_type.value,
                    "attachable_id"  : str(target_id),
                },
            ) from exc


    async def unlink_attachment(
        self,
        db: AsyncSession,
        attachment_id: UUID,
        target_type: AttachmentTarget,
        target_id: UUID,
    ) -> Attachment:
        attachment = await self.get_attachment(db, attachment_id)
        await db.execute(
            delete(Attachable).where(
                Attachable.attachment_id   == attachment_id,
                Attachable.attachable_type == target_type.value,
                Attachable.attachable_id   == target_id,
            )
        )
        await db.commit()
        await db.refresh(attachment)
        return attachment


    async def soft_delete_attachment(
        self,
        db: AsyncSession,
        attachment_id: UUID,
        *,
        remove_file: bool = False,
    ) -> None:
        attachment = await self.get_attachment(db, attachment_id)
        if attachment.deleted_at is not None:
            return

        await db.execute(delete(Attachable).where(Attachable.attachment_id == attachment_id))
        attachment.deleted_at = func.now()
        await db.commit()

        if remove_file:
            await self.storage.delete(attachment.file_path)


    async def get_presigned_url(
        self,
        attachment: Attachment,
        expires_in: Optional[int] = None,
    ) -> str:
        ttl = expires_in or self.settings.ATTACHMENT_PRESIGNED_TTL_SECONDS
        return await self.storage.generate_presigned_url(attachment.file_path, ttl)

    def _infer_extension(self, provided: Optional[str], *candidates: str) -> Optional[str]:
        if provided:
            return provided.lower().lstrip(".")
        for candidate in candidates:
            if not candidate:
                continue
            if "." in candidate:
                return candidate.rsplit(".", 1)[1].lower()
        return None


    def _build_kind_condition(self, kind: AttachmentKind):
        file_type_column = Attachment.file_type
        extension_column = Attachment.extension

        image_condition = or_(
            file_type_column.ilike("image/%"),
            extension_column.in_(tuple(SUPPORTED_IMAGE_EXTENSIONS)),
        )
        document_condition = or_(
            file_type_column.in_(tuple(SUPPORTED_DOCUMENT_MIME_TYPES)),
            extension_column.in_(tuple(SUPPORTED_DOCUMENT_EXTENSIONS)),
        )
        video_condition = or_(
            file_type_column.ilike("video/%"),
            file_type_column.in_(tuple(SUPPORTED_VIDEO_MIME_TYPES)),
            extension_column.in_(tuple(SUPPORTED_VIDEO_EXTENSIONS)),
        )
        archive_condition = or_(
            file_type_column.in_(tuple(SUPPORTED_ARCHIVE_MIME_TYPES)),
            extension_column.in_(tuple(SUPPORTED_ARCHIVE_EXTENSIONS)),
        )

        kind_map = {
            AttachmentKind.IMAGE: image_condition,
            AttachmentKind.DOCUMENT: document_condition,
            AttachmentKind.VIDEO: video_condition,
            AttachmentKind.ARCHIVE: archive_condition,
        }

        if kind == AttachmentKind.OTHER:
            non_other = or_(*kind_map.values())
            return not_(non_other)

        return kind_map.get(kind, true())


attachment_service = AttachmentService(get_attachment_storage())
