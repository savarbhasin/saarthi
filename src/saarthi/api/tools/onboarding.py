from typing import Literal

from saarthi.api.tools.base import Tool, ToolArgs, ToolContext, ToolResult
from saarthi.config import get_settings
from saarthi.domain import users
from saarthi.packs import pick_pack


class OnboardArgs(ToolArgs):
    caller_name: str
    caller_work: str | None = None
    caller_language: str | None = None
    consent: Literal["yes", "no"] | None = None


async def onboard(ctx: ToolContext, args: OnboardArgs) -> ToolResult:
    language = args.caller_language if args.caller_language in users.SUPPORTED_LANGUAGES else None
    pack = pick_pack(args.caller_work)
    user = await users.onboard(
        ctx.db,
        phone=ctx.call_session.phone,
        name=args.caller_name,
        occupation=args.caller_work,
        language=language or get_settings().default_language,
        pack=pack.name,
        consent=args.consent == "yes",
    )
    ctx.call_session.user_id = user.id
    return {
        "status": "ok",
        "name": user.name,
        "profile": pack.name,
        "extra_instructions": pack.voice_prompt or "none",
    }


TOOLS = {"onboard_user": Tool(OnboardArgs, onboard)}
