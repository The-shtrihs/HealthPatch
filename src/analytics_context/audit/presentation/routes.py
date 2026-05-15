from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.analytics_context.audit.application.queries import AuditQueryService
from src.analytics_context.audit.domain.models import AuditChannel
from src.analytics_context.audit.presentation.dependencies import get_audit_query_service
from src.analytics_context.audit.presentation.schemas import AuditEntryResponse
from src.core_context.auth.contracts.dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/analytics/audit", tags=["analytics"])


@router.get("", response_model=list[AuditEntryResponse])
async def list_audit_entries(
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    user_id: int | None = Query(default=None),
    channel: AuditChannel | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    service: AuditQueryService = Depends(get_audit_query_service),
) -> list[AuditEntryResponse]:
    entries = await service.list(user_id=user_id, channel=channel, since=since, limit=limit)
    return [AuditEntryResponse.from_domain(e) for e in entries]
