import uuid

from saarthi.db.session import session_scope
from saarthi.domain import login
from saarthi.voice.context import CallReason
from saarthi.voice.outbound import call_phone


async def send_login_code(ctx: dict, login_id: str, phone: str, code: str) -> None:
    # Spaced out so it is read digit by digit: "4 7 2, 9 1 3".
    spoken = f"{' '.join(code[:3])}, {' '.join(code[3:])}"
    execution_id = await call_phone(phone, CallReason.LOGIN_CODE, spoken)
    async with session_scope() as session:
        await login.record_call(session, uuid.UUID(login_id), execution_id)
