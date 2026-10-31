import hashlib
import hmac
import time
import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.config import get_settings
from saarthi.db.models import User

COOKIE = "saarthi_web"
SESSION_DAYS = 14


class LoginRequired(Exception):
    pass


def _sign(text: str) -> str:
    key = hashlib.sha256(f"web:{get_settings().bolna_tool_secret}".encode()).digest()
    return hmac.new(key, text.encode(), hashlib.sha256).hexdigest()


def session_cookie(user_id: uuid.UUID) -> str:
    payload = f"{user_id.hex}.{int(time.time()) + SESSION_DAYS * 86400}"
    return f"{payload}.{_sign(payload)}"


def user_id_from_cookie(value: str | None) -> uuid.UUID | None:
    if not value or value.count(".") != 2:
        return None
    payload, signature = value.rsplit(".", 1)
    user_hex, expires = payload.split(".")
    if not hmac.compare_digest(signature, _sign(payload)) or int(expires) < time.time():
        return None
    return uuid.UUID(hex=user_hex)


async def current_user(request: Request, db: AsyncSession) -> User:
    user_id = user_id_from_cookie(request.cookies.get(COOKIE))
    user = await db.get(User, user_id) if user_id else None
    if user is None:
        raise LoginRequired
    return user
