import re
from typing import Literal

from pydantic import field_validator

from saarthi.api.tools.base import Tool, ToolArgs, ToolContext, ToolResult
from saarthi.config import get_settings
from saarthi.domain import users
from saarthi.packs import pick_pack

SUPPORTED_LANGUAGES = {"hi", "en", "bn", "ta", "te", "mr", "gu", "kn", "pa", "ml", "od"}


class OnboardArgs(ToolArgs):
    caller_name: str
    caller_work: str | None = None
    caller_upi_id: str | None = None
    caller_language: str | None = None
    consent: Literal["yes", "no"] | None = None

    @field_validator("caller_upi_id")
    @classmethod
    def _upi(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.replace(" ", "").lower()
        if not re.fullmatch(r"[a-z0-9.\-_]{2,256}@[a-z]{2,64}", value):
            raise ValueError("UPI ID must look like name@bank in English letters")
        return value


async def onboard(ctx: ToolContext, args: OnboardArgs) -> ToolResult:
    language = args.caller_language if args.caller_language in SUPPORTED_LANGUAGES else None
    pack = pick_pack(args.caller_work)
    user = await users.onboard(
        ctx.db,
        phone=ctx.call_session.phone,
        name=args.caller_name,
        occupation=args.caller_work,
        language=language or get_settings().default_language,
        pack=pack.name,
        upi_id=args.caller_upi_id,
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
