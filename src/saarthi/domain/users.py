from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import User


async def get_by_phone(session: AsyncSession, phone: str) -> User | None:
    return await session.scalar(select(User).where(User.phone == phone))


async def onboard(
    session: AsyncSession,
    *,
    phone: str,
    name: str,
    occupation: str | None,
    language: str,
    pack: str,
    upi_id: str | None,
    consent: bool,
) -> User:
    user = await get_by_phone(session, phone)
    if user is None:
        user = User(phone=phone)
        session.add(user)
    user.name = name.strip()
    user.occupation = occupation
    user.language = language
    user.pack = pack
    user.upi_id = upi_id.strip().lower() if upi_id else None
    if consent and user.consent_at is None:
        user.consent_at = datetime.now(UTC)
    await session.flush()
    return user
