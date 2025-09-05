"""Role model for both shared and tenant schemas."""

from constants import ValidationConstraints
from constants.enums import RoleScope, RoleType
from database import Base
import sqlalchemy as sa
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from uuid import uuid4


class Role(Base):
    """role model"""
    __tablename__  = "roles"
    __table_args__ = (
        sa.Index("idx_roles_is_active", "is_active"),
        sa.Index("idx_roles_name", "name", unique=True),
        sa.Index("idx_roles_active_name", "is_active", "name"),
    )

    id                  = sa.Column(sa.UUID, primary_key=True, default=uuid4, nullable=False)
    name                = sa.Column(sa.String(ValidationConstraints.MAX_ROLE_LENGTH), nullable=False, unique=True)
    description         = sa.Column(sa.Text, nullable=True)
    is_active           = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    role_type           = sa.Column(sa.Enum(
                            RoleType,
                            name="role_type_enum"),
                            nullable=False,
                            default=RoleType.PREDEFINED
                        )
    role_scope          = sa.Column(sa.Enum(
                            RoleScope,
                            name="role_scope_enum"),
                            nullable=False,
                            default=RoleScope.TENANT
                        )
    is_mutable          = sa.Column(sa.Boolean, nullable=False, default=False)
    permissions_mutable = sa.Column(sa.Boolean, nullable=False, default=False)
    managed_by          = sa.Column(sa.String(ValidationConstraints.MAX_ROLE_LENGTH), nullable=True)
    is_deletable        = sa.Column(sa.Boolean, nullable=False, default=False)
    etag                = sa.Column(sa.String(50), nullable=False, default=lambda: str(uuid4())[:8])
    created_at          = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at          = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())

    """ORM Relationships."""
    permissions = relationship("Permission", back_populates="role", lazy="selectin")

    @validates('role_type')
    def validate_mutability(self, key, role_type):
        """Set mutability and etag based on role type."""
        if role_type in [RoleType.BASIC, RoleType.PREDEFINED]:
            self.is_mutable = False
            self.permissions_mutable = False
            self.is_deletable = False
            self.etag = "AA=="
        else:
            # Custom roles get unique etag
            self.etag = str(uuid4())[:8]
        return role_type

    def update_etag(self):
        """Update etag when role is modified (for custom roles only)."""
        if hasattr(self, 'role_type') and self.role_type == RoleType.CUSTOM:
            self.etag = str(uuid4())[:8]
