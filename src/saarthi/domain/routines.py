import uuid
from datetime import UTC, datetime
from typing import Literal
from zoneinfo import ZoneInfo

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import Routine, RoutineKind

# Users say "subah 7 baje" in Indian time, so schedules are written and read in IST.
USER_TZ = ZoneInfo("Asia/Kolkata")

Repeat = Literal["none", "daily", "weekly"]


def parse_local_time(text: str) -> datetime:
    when = datetime.fromisoformat(text.strip().replace(" ", "T"))
    if when.tzinfo is None:
        when = when.replace(tzinfo=USER_TZ)
    return when.astimezone(UTC)


def cron_for(when: datetime, repeat: Repeat) -> str | None:
    local = when.astimezone(USER_TZ)
    if repeat == "daily":
        return f"{local.minute} {local.hour} * * *"
    if repeat == "weekly":
        return f"{local.minute} {local.hour} * * {local.isoweekday() % 7}"
    return None


def next_cron_run(cron: str, after: datetime) -> datetime:
    return croniter(cron, after.astimezone(USER_TZ)).get_next(datetime).astimezone(UTC)


async def schedule(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    kind: RoutineKind,
    when: datetime,
    repeat: Repeat,
    payload: dict,
) -> Routine:
    routine = Routine(
        user_id=user_id,
        kind=kind,
        cron=cron_for(when, repeat),
        run_at=when,
        next_run_at=when,
        payload=payload,
    )
    session.add(routine)
    await session.flush()
    return routine


async def upcoming(session: AsyncSession, user_id: uuid.UUID, limit: int = 10) -> list[Routine]:
    rows = await session.scalars(
        select(Routine)
        .where(Routine.user_id == user_id, Routine.active.is_(True))
        .order_by(Routine.next_run_at)
        .limit(limit)
    )
    return list(rows)


def describe(routine: Routine) -> str:
    when = routine.next_run_at.astimezone(USER_TZ).strftime("%d %b %I:%M %p")
    repeat = {None: "", "daily": " (daily)"}.get(_repeat_label(routine.cron), " (weekly)")
    what = routine.payload.get("message") or routine.payload.get("goal") or ""
    return f"{when}{repeat}: {routine.kind.value} - {what}"


def _repeat_label(cron: str | None) -> str | None:
    if cron is None:
        return None
    return "daily" if cron.endswith("* * *") else "weekly"
