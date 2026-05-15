from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics_context.audit.application.queries import AuditQueryService
from src.analytics_context.audit.infrastructure.repository import AuditEntryRepository
from src.core.database import get_session


async def get_audit_entry_repository(db: AsyncSession = Depends(get_session)) -> AuditEntryRepository:
    return AuditEntryRepository(db)


async def get_audit_query_service(
    repo: AuditEntryRepository = Depends(get_audit_entry_repository),
) -> AuditQueryService:
    return AuditQueryService(repo)
