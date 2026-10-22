from typing import Literal

from saarthi.api.tools.base import Tool, ToolArgs, ToolContext, ToolFailure, ToolResult
from saarthi.db.models import RoutineKind
from saarthi.domain import routines


class SetReminderArgs(ToolArgs):
    message: str
    remind_at: str
    repeat: Literal["none", "daily", "weekly"] | None = None


class ListScheduleArgs(ToolArgs):
    pass


async def set_reminder(ctx: ToolContext, args: SetReminderArgs) -> ToolResult:
    user = ctx.require_user()
    try:
        when = routines.parse_local_time(args.remind_at)
    except ValueError as exc:
        raise ToolFailure(
            "invalid_arguments", fields="remind_at", hint="Use YYYY-MM-DD HH:MM"
        ) from exc
    routine = await routines.schedule(
        ctx.db,
        user_id=user.id,
        kind=RoutineKind.REMINDER,
        when=when,
        repeat=args.repeat or "none",
        payload={"message": args.message},
    )
    return {"status": "ok", "scheduled": routines.describe(routine)}


async def list_schedule(ctx: ToolContext, args: ListScheduleArgs) -> ToolResult:
    upcoming = await routines.upcoming(ctx.db, ctx.require_user().id)
    return {"status": "ok", "upcoming": [routines.describe(r) for r in upcoming] or ["nothing"]}


TOOLS = {
    "set_reminder": Tool(SetReminderArgs, set_reminder),
    "list_schedule": Tool(ListScheduleArgs, list_schedule),
}
