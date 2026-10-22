import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import OutreachCall, OutreachStatus, Task, User
from saarthi.domain.phone import InvalidPhone, normalize_phone

MAX_CALLS = 10
FINISHED = (OutreachStatus.DONE, OutreachStatus.NO_ANSWER, OutreachStatus.FAILED)

# Bolna's final execution statuses; anything else is still in flight.
BOLNA_FINAL = {
    "completed": OutreachStatus.DONE,
    "busy": OutreachStatus.NO_ANSWER,
    "no-answer": OutreachStatus.NO_ANSWER,
    "failed": OutreachStatus.FAILED,
    "canceled": OutreachStatus.FAILED,
    "error": OutreachStatus.FAILED,
    "stopped": OutreachStatus.FAILED,
    "balance-low": OutreachStatus.FAILED,
}

REPORT_LINES = {
    "hi": {
        "no_answer": "फ़ोन नहीं उठाया",
        "failed": "कॉल नहीं लग पाया",
        "unclear": "बात पूरी नहीं हुई",
    },
    "en": {
        "no_answer": "didn't pick up",
        "failed": "the call didn't go through",
        "unclear": "no clear answer",
    },
}


@dataclass(frozen=True)
class CallRequest:
    name: str
    phone: str
    purpose: str


class NothingToCall(ValueError):
    pass


async def create_calls(
    db: AsyncSession, user: User, task: Task, requests: list[CallRequest]
) -> tuple[list[OutreachCall], list[str]]:
    """Queue calls for a task, returning them and the names skipped.

    Skipped: bad or repeated numbers, the user's own number, and anyone past MAX_CALLS.
    """
    calls, skipped, seen = [], [], {user.phone}
    for request in requests[:MAX_CALLS]:
        try:
            phone = normalize_phone(request.phone)
        except InvalidPhone:
            phone = None
        if phone is None or phone in seen:
            skipped.append(request.name)
            continue
        seen.add(phone)
        calls.append(
            OutreachCall(
                task_id=task.id,
                user_id=user.id,
                contact_name=request.name.strip(),
                phone=phone,
                purpose=request.purpose.strip(),
            )
        )
    skipped += [r.name for r in requests[MAX_CALLS:]]
    if not calls:
        raise NothingToCall(", ".join(skipped))
    db.add_all(calls)
    await db.flush()
    return calls, skipped


async def calls_for(db: AsyncSession, task_id: uuid.UUID) -> list[OutreachCall]:
    rows = await db.scalars(
        select(OutreachCall)
        .where(OutreachCall.task_id == task_id)
        # Calls queued together share created_at (it is the transaction's time).
        .order_by(OutreachCall.created_at, OutreachCall.contact_name)
    )
    return list(rows)


async def by_token(db: AsyncSession, token: str) -> OutreachCall | None:
    return await db.scalar(select(OutreachCall).where(OutreachCall.session_token == token))


async def by_execution(db: AsyncSession, execution_id: str) -> OutreachCall | None:
    return await db.scalar(
        select(OutreachCall).where(OutreachCall.bolna_execution_id == execution_id)
    )


def finish(call: OutreachCall, status: OutreachStatus) -> None:
    if call.status in FINISHED:
        return
    call.status = status
    call.finished_at = datetime.now(UTC)


async def all_finished(db: AsyncSession, task_id: uuid.UUID) -> bool:
    # Lock the task so the last two calls finishing together can't both miss the report.
    await db.scalar(select(Task).where(Task.id == task_id).with_for_update())
    return all(c.status in FINISHED for c in await calls_for(db, task_id))


def report(calls: list[OutreachCall], language: str) -> str:
    lines = REPORT_LINES.get(language, REPORT_LINES["hi"])
    stop = "." if language == "en" else "।"
    parts = []
    for call in calls:
        if call.status is OutreachStatus.DONE:
            said = call.note or lines["unclear"]
        else:
            said = lines["no_answer" if call.status is OutreachStatus.NO_ANSWER else "failed"]
        parts.append(f"{call.contact_name}: {said.rstrip('.। ')}{stop}")
    return " ".join(parts)
