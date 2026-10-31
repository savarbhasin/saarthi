import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.config import get_settings
from saarthi.db.models import LoginCode

CODE_TTL = timedelta(minutes=10)
MAX_CODES_PER_WINDOW = 3
CODE_WINDOW = timedelta(minutes=15)
MAX_ATTEMPTS = 5


class TooManyCodes(Exception):
    pass


def _hash_code(phone: str, code: str) -> str:
    key = hashlib.sha256(f"login:{get_settings().bolna_tool_secret}".encode()).digest()
    return hmac.new(key, f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


async def issue_code(db: AsyncSession, phone: str) -> tuple[LoginCode, str]:
    since = datetime.now(UTC) - CODE_WINDOW
    recent = await db.scalar(
        select(func.count())
        .select_from(LoginCode)
        .where(LoginCode.phone == phone, LoginCode.created_at > since)
    )
    if recent >= MAX_CODES_PER_WINDOW:
        raise TooManyCodes
    code = f"{secrets.randbelow(1_000_000):06d}"
    login = LoginCode(
        phone=phone, code_hash=_hash_code(phone, code), expires_at=datetime.now(UTC) + CODE_TTL
    )
    db.add(login)
    await db.flush()
    return login, code


async def check_code(db: AsyncSession, phone: str, code: str) -> bool:
    login = await db.scalar(
        select(LoginCode)
        .where(
            LoginCode.phone == phone,
            LoginCode.used_at.is_(None),
            LoginCode.expires_at > datetime.now(UTC),
        )
        .order_by(LoginCode.created_at.desc())
        .limit(1)
        .with_for_update()
    )
    if login is None or login.attempts >= MAX_ATTEMPTS:
        return False
    login.attempts += 1
    if not hmac.compare_digest(login.code_hash, _hash_code(phone, code.strip())):
        return False
    login.used_at = datetime.now(UTC)
    return True


async def record_call(db: AsyncSession, login_id: uuid.UUID, execution_id: str) -> None:
    login = await db.get(LoginCode, login_id)
    login.call_execution_id = execution_id


async def is_code_call(db: AsyncSession, execution_id: str) -> bool:
    # A call that read out a sign-in code must never reach memory or the sandbox history.
    found = await db.scalar(select(LoginCode.id).where(LoginCode.call_execution_id == execution_id))
    return found is not None
