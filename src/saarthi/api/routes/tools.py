import logging

from fastapi import APIRouter, Request

from saarthi.api.deps import BolnaAuth, Db, ToolArgsError, parse_tool_args
from saarthi.api.tools import REGISTRY
from saarthi.api.tools.base import ToolContext, ToolFailure, ToolResult
from saarthi.db.models import User
from saarthi.domain import call_sessions

log = logging.getLogger("saarthi.tools")
router = APIRouter(prefix="/tools", dependencies=[BolnaAuth])

ASK_INSTEAD = (
    "You do not have these details yet. Do not call this tool again until the caller has "
    "told you them. Ask the caller for them now, in one short question."
)


async def _invoke(name: str, request: Request, db) -> ToolResult:
    tool = REGISTRY.get(name)
    if tool is None:
        raise ToolFailure("unknown_tool")
    try:
        args = await parse_tool_args(request, tool.args)
    except ToolArgsError as exc:
        raise ToolFailure("invalid_arguments", fields=str(exc), hint=ASK_INSTEAD) from exc

    call_session = await call_sessions.resolve(db, args.session)
    if call_session is None:
        raise ToolFailure("invalid_session", hint="Session expired. Apologise and end the call.")
    user = await db.get(User, call_session.user_id) if call_session.user_id else None
    ctx = ToolContext(db=db, call_session=call_session, arq=request.app.state.arq, user=user)
    return await tool.handler(ctx, args)


@router.post("/{name}")
async def call_tool(name: str, request: Request, db: Db) -> ToolResult:
    try:
        result = await _invoke(name, request, db)
    except ToolFailure as failure:
        result = failure.result
    log.info(
        "tool %s raw=%s -> %s", name, (await request.body()).decode(errors="replace")[:500], result
    )
    return result
