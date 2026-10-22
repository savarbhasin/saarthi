import asyncio
import time
from datetime import UTC, datetime
from typing import Literal

from saarthi.api.tools.base import Tool, ToolArgs, ToolContext, ToolFailure, ToolResult
from saarthi.config import get_settings
from saarthi.db.models import RoutineKind, TaskStatus
from saarthi.domain import routines, tasks

POLL_SECONDS = 1.0
DETAILS_LIMIT = 3000


class DoTaskArgs(ToolArgs):
    goal: str
    run_at: str | None = None
    repeat: Literal["none", "daily", "weekly"] | None = None
    wait: Literal["yes", "no"] | None = None


class WaitForTaskArgs(ToolArgs):
    task: str | None = None


class TaskStatusArgs(ToolArgs):
    pass


class TaskDetailsArgs(ToolArgs):
    task: str | None = None


async def do_task(ctx: ToolContext, args: DoTaskArgs) -> ToolResult:
    user = ctx.require_user()
    if args.run_at:
        try:
            when = routines.parse_local_time(args.run_at)
        except ValueError as exc:
            raise ToolFailure(
                "invalid_arguments", fields="run_at", hint="Use YYYY-MM-DD HH:MM"
            ) from exc
        routine = await routines.schedule(
            ctx.db,
            user_id=user.id,
            kind=RoutineKind.TASK,
            when=when,
            repeat=args.repeat or "none",
            payload={"goal": args.goal},
        )
        return {"status": "scheduled", "when": routines.describe(routine)}

    waiting = args.wait == "yes"
    task = await tasks.create(ctx.db, user.id, args.goal, caller_waiting=waiting)
    await ctx.db.commit()
    await ctx.arq.enqueue_job("run_task", str(task.id), _job_id=f"task:{task.id}")
    hint = (
        "Tell the caller you are working on it, then call wait_for_task with this task."
        if waiting
        else "Tell the caller you are on it and will call them back with the result."
    )
    return {"status": "started", "task": tasks.short_id(task), "hint": hint}


async def wait_for_task(ctx: ToolContext, args: WaitForTaskArgs) -> ToolResult:
    """Block briefly until a task the caller is holding for finishes.

    Bolna cannot push a result into a live call, so the voice agent pulls it: each call waits
    at most `task_wait_seconds` (kept under Bolna's custom-function timeout) and the agent
    says a filler between calls. A result heard here is marked reported, which turns the
    delayed callback for this task into a no-op.
    """
    user = ctx.require_user()
    task = await tasks.find(ctx.db, user.id, args.task)
    if task is None:
        raise ToolFailure("not_found", hint="No such task. Use task_status to see recent tasks.")

    deadline = time.monotonic() + get_settings().task_wait_seconds
    while task.status in tasks.ACTIVE and time.monotonic() < deadline:
        await asyncio.sleep(POLL_SECONDS)
        await ctx.db.refresh(task)

    if task.status in tasks.ACTIVE:
        return {
            "status": "still_working",
            "seconds_so_far": int((datetime.now(UTC) - task.created_at).total_seconds()),
            "hint": (
                "Say one short line that you are still on it, then call wait_for_task again. "
                "If it has been over a minute, offer to call them back instead."
            ),
        }
    tasks.mark_reported([task])
    return {
        "status": "done" if task.status is TaskStatus.DONE else "failed",
        "summary": task.summary or "",
        "details": (task.result or "")[:DETAILS_LIMIT],
    }


async def task_status(ctx: ToolContext, args: TaskStatusArgs) -> ToolResult:
    user = ctx.require_user()
    recent = await tasks.recent(ctx.db, user.id)
    return {"status": "ok", "tasks": [tasks.describe(t) for t in recent] or ["no tasks yet"]}


async def task_details(ctx: ToolContext, args: TaskDetailsArgs) -> ToolResult:
    user = ctx.require_user()
    task = await tasks.find(ctx.db, user.id, args.task)
    if task is None:
        raise ToolFailure("not_found", hint="No such task. Use task_status to see recent tasks.")
    if task.status in tasks.ACTIVE:
        return {"status": "still_working", "goal": task.goal}
    return {
        "status": "done" if task.status is TaskStatus.DONE else "failed",
        "goal": task.goal,
        "summary": task.summary or "",
        "details": (task.result or "")[:DETAILS_LIMIT],
        "hint": "Answer what they asked from these details, briefly, in your own spoken words.",
    }


TOOLS = {
    "do_task": Tool(DoTaskArgs, do_task),
    "wait_for_task": Tool(WaitForTaskArgs, wait_for_task),
    "task_status": Tool(TaskStatusArgs, task_status),
    "task_details": Tool(TaskDetailsArgs, task_details),
}
