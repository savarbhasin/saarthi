import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import Task, TaskStatus

ACTIVE = (TaskStatus.QUEUED, TaskStatus.RUNNING, TaskStatus.WAITING_USER)


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    goal: str,
    *,
    caller_waiting: bool = False,
    call_execution_id: str | None = None,
    follow_up_of: uuid.UUID | None = None,
) -> Task:
    task = Task(
        user_id=user_id,
        goal=goal.strip(),
        caller_waiting=caller_waiting,
        call_execution_id=call_execution_id,
        follow_up_of=follow_up_of,
    )
    session.add(task)
    await session.flush()
    return task


async def recent(session: AsyncSession, user_id: uuid.UUID, limit: int = 5) -> list[Task]:
    rows = await session.scalars(
        select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc()).limit(limit)
    )
    return list(rows)


async def find(session: AsyncSession, user_id: uuid.UUID, ref: str | None) -> Task | None:
    # `ref` is the short id the voice agent was given; without one, the latest task.
    for task in await recent(session, user_id, limit=20):
        if not ref or task.id.hex.startswith(ref.lower()):
            return task
    return None


async def unreported(session: AsyncSession, user_id: uuid.UUID) -> list[Task]:
    rows = await session.scalars(
        select(Task)
        .where(
            Task.user_id == user_id,
            Task.status.in_((TaskStatus.DONE, TaskStatus.FAILED)),
            Task.reported_at.is_(None),
        )
        .order_by(Task.created_at)
    )
    return list(rows)


async def by_callback(session: AsyncSession, execution_id: str) -> Task | None:
    return await session.scalar(select(Task).where(Task.callback_execution_id == execution_id))


def finish(task: Task, *, ok: bool, summary: str, result: str | None, cost_usd: float | None):
    task.status = TaskStatus.DONE if ok else TaskStatus.FAILED
    task.summary = summary
    task.result = result
    task.cost_usd = cost_usd


def mark_reported(tasks: list[Task]) -> None:
    now = datetime.now(UTC)
    for task in tasks:
        task.reported_at = now


def short_id(task: Task) -> str:
    return task.id.hex[:6]


def describe(task: Task) -> str:
    if task.status in ACTIVE:
        return f"[{short_id(task)}] still working on: {task.goal}"
    outcome = "done" if task.status is TaskStatus.DONE else "failed"
    return f"[{short_id(task)}] {outcome}: {task.goal} -> {task.summary or 'no summary'}"
