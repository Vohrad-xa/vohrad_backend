"""Attachment router."""

from __future__ import annotations
from api.attachment.schema import (
    AttachmentCreate,
    AttachmentFilterParams,
    AttachmentLinkRequest,
    AttachmentResponse,
    AttachmentUpdate,
    AttachmentUploadForm,
)
from api.attachment.service import attachment_service
from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.permission.dependencies import (
    RequireAttachmentCreate,
    RequireAttachmentDelete,
    RequireAttachmentRead,
    RequireAttachmentUpdate,
)
from constants.attachments import AttachmentTarget
from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from uuid import UUID
from web import (
    CreatedResponse,
    DeletedResponse,
    PaginatedResponse,
    PaginationParams,
    ResponseFactory,
    SuccessResponse,
    UpdatedResponse,
    pagination_params,
)

routes = APIRouter(
    prefix = "/attachments",
    tags   = ["attachments"],
)


@routes.post(
    "/",
    status_code    = status.HTTP_201_CREATED,
    response_model = CreatedResponse[AttachmentResponse],
)
async def create_attachment(
    form: AttachmentUploadForm = Depends(AttachmentUploadForm.as_form),
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireAttachmentCreate),
):
    """Upload a new attachment and link it to an entity."""
    current_user, tenant, db = context
    payload = AttachmentCreate.model_validate(form.model_dump(exclude={"file"}))

    tenant_identifier = getattr(tenant, "sub_domain", None) or tenant.tenant_schema_name
    attachment = await attachment_service.create_attachment(
        db                = db,
        payload           = payload,
        upload            = form.file,
        tenant_identifier = tenant_identifier,
        current_user      = current_user,
    )
    return ResponseFactory.created(attachment, response_model=AttachmentResponse)


@routes.get(
    "/",
    response_model = SuccessResponse[PaginatedResponse[AttachmentResponse]],
)
async def list_attachments(
    pagination: PaginationParams = Depends(pagination_params),
    filters: AttachmentFilterParams = Depends(AttachmentFilterParams.as_query),
    odata_filter: Optional[str] = Query(None, alias="$filter"),
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireAttachmentRead),
):
    """List attachments with filtering and pagination."""
    _, _, db = context
    result = await attachment_service.list_attachments(
        db           = db,
        filters      = filters,
        page         = pagination.page,
        size         = pagination.size,
        odata_filter = odata_filter,
    )
    return BaseRouterMixin.create_paginated_response(
        result.attachments,
        result.total,
        pagination,
        AttachmentResponse,
    )


@routes.get(
    "/{attachment_id}",
    response_model = SuccessResponse[AttachmentResponse],
)
async def get_attachment(
    attachment_id: UUID,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireAttachmentRead),
):
    """Retrieve attachment metadata."""
    _, _, db = context
    attachment = await attachment_service.get_attachment(db, attachment_id)
    return ResponseFactory.success(attachment, response_model=AttachmentResponse)


@routes.patch(
    "/{attachment_id}",
    response_model = UpdatedResponse[AttachmentResponse],
)
async def update_attachment(
    attachment_id: UUID,
    payload: AttachmentUpdate,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireAttachmentUpdate),
):
    """Update attachment metadata fields."""
    _, _, db = context
    attachment = await attachment_service.update_attachment(db, attachment_id, payload)
    return ResponseFactory.updated(attachment, response_model=AttachmentResponse)


@routes.delete(
    "/{attachment_id}",
    response_model = DeletedResponse,
)
async def delete_attachment(
    attachment_id: UUID,
    hard_delete: bool = Query(False, description="Also remove the physical file if true"),
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireAttachmentDelete),
):
    """Soft-delete an attachment and optionally remove the file."""
    _, _, db = context
    await attachment_service.soft_delete_attachment(db, attachment_id, remove_file=hard_delete)
    return ResponseFactory.deleted()


@routes.post(
    "/{attachment_id}/link",
    response_model = SuccessResponse[AttachmentResponse],
)
async def link_attachment(
    attachment_id: UUID,
    payload: AttachmentLinkRequest,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireAttachmentUpdate),
):
    """Link an existing attachment to another entity."""
    _, _, db = context
    attachment = await attachment_service.link_attachment(
        db            = db,
        attachment_id = attachment_id,
        target_type   = payload.target_type,
        target_id     = payload.target_id,
    )
    return ResponseFactory.success(attachment, response_model=AttachmentResponse)


@routes.delete(
    "/{attachment_id}/link",
    response_model = SuccessResponse[AttachmentResponse],
)
async def unlink_attachment(
    attachment_id: UUID,
    target_type: AttachmentTarget = Query(...),
    target_id: UUID = Query(...),
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireAttachmentUpdate),
):
    """Unlink an attachment from an entity."""
    _, _, db = context
    attachment = await attachment_service.unlink_attachment(
        db            = db,
        attachment_id = attachment_id,
        target_type   = target_type,
        target_id     = target_id,
    )
    return ResponseFactory.success(attachment, response_model=AttachmentResponse)


@routes.get(
    "/{attachment_id}/url",
    response_model = SuccessResponse[str],
)
async def get_attachment_url(
    attachment_id: UUID,
    expires_in: Optional[int] = Query(None, ge=60, le=86400),
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireAttachmentRead),
):
    """Generate a download URL for an attachment."""
    _, _, db = context
    attachment = await attachment_service.get_attachment(db, attachment_id)
    url = await attachment_service.get_presigned_url(attachment, expires_in)
    return ResponseFactory.success(url)
