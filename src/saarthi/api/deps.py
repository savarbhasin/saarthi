import secrets
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.config import get_settings
from saarthi.db.session import session_scope


async def get_db() -> AsyncIterator[AsyncSession]:
    async with session_scope() as session:
        yield session


Db = Annotated[AsyncSession, Depends(get_db)]


def _strip_bearer(value: str) -> str:
    # We don't know whether Bolna prefixes "Bearer " to the api_token we configure, so accept
    # the raw secret as well as one or more "Bearer " prefixes.
    value = value.strip()
    while value.lower().startswith("bearer "):
        value = value[7:].strip()
    return value


def require_bolna_secret(
    authorization: Annotated[str | None, Header()] = None,
    token: Annotated[str | None, Query()] = None,
) -> None:
    supplied = _strip_bearer(authorization) if authorization else token
    if not supplied or not secrets.compare_digest(supplied, get_settings().bolna_tool_secret):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")


BolnaAuth = Depends(require_bolna_secret)


class ToolArgsError(ValueError):
    pass


async def parse_tool_args[M: BaseModel](request: Request, model: type[M]) -> M:
    data: dict = dict(request.query_params)
    if await request.body():
        try:
            body = await request.json()
        except ValueError:
            body = dict(await request.form())
        if isinstance(body, dict):
            data.update(body)
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        fields = ", ".join(str(err["loc"][0]) for err in exc.errors() if err["loc"])
        raise ToolArgsError(fields) from exc
