from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from arq import ArqRedis
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import CallSession, User

EMPTY_MARKERS = {"", "none", "null", "nil", "n/a", "na", "-"}

ToolResult = dict[str, object]


class ToolArgs(BaseModel):
    session: str

    @field_validator("*", mode="before")
    @classmethod
    def _blank_to_none(cls, value):
        # Every Bolna tool param is required, so the LLM sends "" (or "null") for "not given".
        if isinstance(value, str) and value.strip().lower() in EMPTY_MARKERS:
            return None
        return value.strip() if isinstance(value, str) else value


class ToolFailure(Exception):
    def __init__(self, status: str, **details):
        self.result: ToolResult = {"status": status, **details}


@dataclass
class ToolContext:
    db: AsyncSession
    call_session: CallSession
    arq: ArqRedis
    user: User | None

    def require_user(self) -> User:
        if self.user is None:
            raise ToolFailure("not_onboarded", hint="Onboard the caller with onboard_user first.")
        return self.user


@dataclass(frozen=True)
class Tool:
    args: type[ToolArgs]
    handler: Callable[[ToolContext, ToolArgs], Awaitable[ToolResult]]
