from saarthi.api.tools.base import Tool, ToolArgs, ToolContext, ToolFailure, ToolResult
from saarthi.config import get_settings
from saarthi.memory import store


class RememberArgs(ToolArgs):
    fact: str


class RecallArgs(ToolArgs):
    query: str


class ForgetArgs(ToolArgs):
    what: str


def _require_memory() -> None:
    if not get_settings().supermemory_api_key:
        raise ToolFailure("unavailable", hint="Memory is switched off right now.")


async def remember(ctx: ToolContext, args: RememberArgs) -> ToolResult:
    _require_memory()
    await store.remember(ctx.require_user().id, args.fact)
    return {"status": "ok"}


async def recall(ctx: ToolContext, args: RecallArgs) -> ToolResult:
    _require_memory()
    found = await store.search(ctx.require_user().id, args.query)
    return {"status": "ok", "memories": found or ["nothing found"]}


async def forget(ctx: ToolContext, args: ForgetArgs) -> ToolResult:
    _require_memory()
    removed = await store.forget(ctx.require_user().id, args.what)
    return {"status": "ok", "forgotten": removed}


TOOLS = {
    "remember": Tool(RememberArgs, remember),
    "recall": Tool(RecallArgs, recall),
    "forget": Tool(ForgetArgs, forget),
}
