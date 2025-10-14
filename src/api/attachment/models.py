"""Attachment models (tenant schemas)."""

from __future__ import annotations
from constants.attachments import SUPPORTED_ATTACHABLE_TYPES
from database import Base
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Index, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from uuid import UUID, uuid4


class Attachment(Base):
    """File attachments stored in tenant schemas with metadata only."""

    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint("size >= 0", name="ck_attachments_size_non_negative"),
        Index("idx_attachments_user_id", "user_id"),
        Index("idx_attachments_category", "category"),
        Index("idx_attachments_file_type", "file_type"),
        Index("idx_attachments_created_at", "created_at"),
        Index("idx_attachments_deleted_at", "deleted_at"),
    )

    id               : Mapped[UUID]           = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    filename         : Mapped[str]            = mapped_column(sa.String(255))
    original_filename: Mapped[str]            = mapped_column(sa.String(255))
    file_type        : Mapped[str]            = mapped_column(sa.String(100))
    extension        : Mapped[Optional[str]]  = mapped_column(sa.String(10))
    size             : Mapped[int]            = mapped_column(sa.BigInteger, default=0)
    file_path        : Mapped[str]            = mapped_column(sa.Text)
    description      : Mapped[Optional[str]]  = mapped_column(sa.Text)
    category         : Mapped[Optional[str]]  = mapped_column(sa.String(100))
    user_id          : Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        sa.ForeignKey("users.id",
        ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]]  = mapped_column(sa.DateTime(timezone=True))
    attachables: Mapped[List["Attachable"]] = relationship(
        back_populates = "attachment",
        cascade        = "all, delete-orphan",
        lazy           = "selectin",
    )


class Attachable(Base):
    """Polymorphic association table linking attachments to domain entities."""

    __tablename__ = "attachables"
    __table_args__ = (
        CheckConstraint(
            f"attachable_type IN ({', '.join(repr(value) for value in SUPPORTED_ATTACHABLE_TYPES)})",
            name="ck_attachables_type_supported",
        ),
        Index("idx_attachables_type_id", "attachable_type", "attachable_id"),
        Index("idx_attachables_attachment_id", "attachment_id"),
        sa.UniqueConstraint("attachment_id", "attachable_type", "attachable_id", name="attachables_unique"),
    )

    id           : Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    attachment_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        sa.ForeignKey("attachments.id",
        ondelete="CASCADE")
    )
    attachable_type: Mapped[str]      = mapped_column(sa.String(50))
    attachable_id  : Mapped[UUID]     = mapped_column(PostgresUUID(as_uuid=True))
    created_at     : Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    attachment: Mapped[Attachment] = relationship(back_populates="attachables", lazy="joined")
