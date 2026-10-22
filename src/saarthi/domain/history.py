"""What the backend sends to a sandbox's ~/history (written by sandbox/agent_server/history.py).

Postgres stays the source of truth: task records are written by the sandbox itself as tasks
finish, and call transcripts are copied in just before the next task starts.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import Call, Task
from saarthi.domain import tasks
from saarthi.domain.routines import USER_TZ

SYNC_BATCH = 100
DETAILS_LIMIT = 3000


def call_ref(execution_id: str) -> str:
    # Same rule as the sandbox's history.short_ref.
    return execution_id.replace("-", "")[:6].lower()


async def unsynced_calls(session: AsyncSession, user_id: uuid.UUID) -> list[Call]:
    rows = await session.scalars(
        select(Call)
        .where(
            Call.user_id == user_id,
            Call.status == "completed",
            Call.transcript.is_not(None),
            Call.sandbox_synced_at.is_(None),
        )
        .order_by(Call.created_at)
        .limit(SYNC_BATCH)
    )
    return list(rows)


async def call_payloads(session: AsyncSession, calls: list[Call]) -> list[dict]:
    ids = [call.bolna_execution_id for call in calls]
    started = await session.scalars(
        select(Task).where(Task.call_execution_id.in_(ids)).order_by(Task.created_at)
    )
    refs: dict[str, list[str]] = {}
    for task in started:
        refs.setdefault(task.call_execution_id, []).append(tasks.short_id(task))
    return [
        {
            "execution_id": call.bolna_execution_id,
            "started": call.created_at.isoformat(),
            "transcript": call.transcript,
            "direction": call.direction.value if call.direction else "",
            "purpose": call.purpose or "",
            "duration_seconds": float(call.duration_seconds) if call.duration_seconds else None,
            "task_refs": refs.get(call.bolna_execution_id, []),
        }
        for call in calls
    ]


def mark_synced(calls: list[Call]) -> None:
    now = datetime.now(UTC)
    for call in calls:
        call.sandbox_synced_at = now


def follow_up_payload(earlier: Task) -> dict:
    return {
        "ref": tasks.short_id(earlier),
        "asked": earlier.created_at.astimezone(USER_TZ).strftime("%d %B %Y, %I:%M %p"),
        "goal": earlier.goal,
        "summary": earlier.summary or "",
        "details": (earlier.result or "")[:DETAILS_LIMIT],
    }
