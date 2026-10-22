import logging
import uuid
from collections.abc import Awaitable, Callable

from saarthi.db.models import Routine, RoutineKind, User
from saarthi.db.session import session_scope
from saarthi.domain import tasks
from saarthi.voice.context import CallReason
from saarthi.voice.outbound import call_phone

log = logging.getLogger(__name__)

RoutineRunner = Callable[[dict, Routine, User], Awaitable[None]]


async def _remind(ctx: dict, routine: Routine, user: User) -> None:
    await call_phone(user.phone, CallReason.REMINDER, routine.payload.get("message", ""))


async def _run_scheduled_task(ctx: dict, routine: Routine, user: User) -> None:
    async with session_scope() as session:
        task = await tasks.create(session, user.id, routine.payload["goal"])
    await ctx["redis"].enqueue_job("run_task", str(task.id), _job_id=f"task:{task.id}")


RUNNERS: dict[RoutineKind, RoutineRunner] = {
    RoutineKind.REMINDER: _remind,
    RoutineKind.TASK: _run_scheduled_task,
}


async def run_routine(ctx: dict, routine_id: str) -> None:
    async with session_scope() as session:
        routine = await session.get(Routine, uuid.UUID(routine_id))
        user = await session.get(User, routine.user_id) if routine else None
    if routine is None or user is None:
        return
    runner = RUNNERS.get(routine.kind)
    if runner is None:
        log.warning("no runner registered for routine kind %s (%s)", routine.kind, routine_id)
        return
    await runner(ctx, routine, user)
