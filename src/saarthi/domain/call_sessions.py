import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.config import get_settings
from saarthi.db.models import CallSession


async def issue(
    session: AsyncSession,
    *,
    phone: str,
    user_id: uuid.UUID | None,
    execution_id: str | None = None,
) -> CallSession:
    ttl = timedelta(minutes=get_settings().call_session_ttl_minutes)
    call_session = CallSession(
        token=secrets.token_urlsafe(16),
        phone=phone,
        user_id=user_id,
        bolna_execution_id=execution_id,
        expires_at=datetime.now(UTC) + ttl,
    )
    session.add(call_session)
    await session.flush()
    return call_session


async def resolve(session: AsyncSession, token: str) -> CallSession | None:
    call_session = await session.scalar(select(CallSession).where(CallSession.token == token))
    if call_session is None or call_session.expires_at < datetime.now(UTC):
        return None
    return call_session
