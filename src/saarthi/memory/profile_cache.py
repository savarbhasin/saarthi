import uuid

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import ProfileCache


async def get(session: AsyncSession, user_id: uuid.UUID) -> str:
    cached = await session.get(ProfileCache, user_id)
    return cached.profile_text if cached else ""


async def put(session: AsyncSession, user_id: uuid.UUID, profile_text: str) -> None:
    stmt = insert(ProfileCache).values(user_id=user_id, profile_text=profile_text)
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[ProfileCache.user_id],
            set_={"profile_text": stmt.excluded.profile_text, "refreshed_at": func.now()},
        )
    )
