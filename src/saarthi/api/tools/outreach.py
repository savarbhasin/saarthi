from saarthi.api.tools.base import Tool, ToolArgs, ToolContext, ToolFailure, ToolResult
from saarthi.domain import outreach


class RecordOutcomeArgs(ToolArgs):
    outcome: str
    note: str | None = None


async def record_outcome(ctx: ToolContext, args: RecordOutcomeArgs) -> ToolResult:
    # Called by saarthi-messenger: its session belongs to the outreach call, not to a user.
    call = await outreach.by_token(ctx.db, ctx.call_session.token)
    if call is None:
        raise ToolFailure("not_found")
    call.outcome = args.outcome
    call.note = args.note
    return {"status": "ok", "hint": "Thank them, say goodbye and stop talking."}


TOOLS = {
    "record_outcome": Tool(RecordOutcomeArgs, record_outcome),
}
