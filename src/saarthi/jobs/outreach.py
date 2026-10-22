import logging
import uuid
from datetime import UTC, datetime, time, timedelta

from arq import ArqRedis, Retry

from saarthi.db.models import OutreachCall, OutreachStatus, Task, User
from saarthi.db.session import session_scope
from saarthi.domain import outreach
from saarthi.domain.routines import USER_TZ
from saarthi.voice.context import CallReason
from saarthi.voice.outbound import call_for_user, call_phone

log = logging.getLogger(__name__)

# Space the calls out, and never ring anyone outside polite hours (India time).
CALL_GAP_SECONDS = 20
CALLING_FROM, CALLING_UNTIL = time(9, 0), time(21, 30)


async def start_calls(arq: ArqRedis, calls: list[OutreachCall]) -> None:
    for i, call in enumerate(calls):
        await arq.enqueue_job(
            "place_outreach_call",
            str(call.id),
            _job_id=f"outreach:{call.id}",
            _defer_by=i * CALL_GAP_SECONDS,
        )


def _seconds_until_calling_hours(now: datetime) -> int:
    local = now.astimezone(USER_TZ)
    if CALLING_FROM <= local.time() < CALLING_UNTIL:
        return 0
    start = datetime.combine(local.date(), CALLING_FROM, USER_TZ)
    if local.time() >= CALLING_UNTIL:
        start += timedelta(days=1)
    return int((start - local).total_seconds())


async def place_outreach_call(ctx: dict, call_id: str) -> None:
    if wait := _seconds_until_calling_hours(datetime.now(UTC)):
        raise Retry(defer=wait)

    async with session_scope() as session:
        call = await session.get(OutreachCall, uuid.UUID(call_id))
        if call is None or call.status is not OutreachStatus.QUEUED:
            return
        owner = await session.get(User, call.user_id)
        try:
            call.bolna_execution_id = await call_for_user(session, owner, call)
            call.status = OutreachStatus.CALLING
            log.info("calling %s for user %s", call.contact_name, owner.id)
            return
        except Exception:
            log.exception("could not place outreach call %s", call_id)
            outreach.finish(call, OutreachStatus.FAILED)
            done = await outreach.all_finished(session, call.task_id)
            task_id = call.task_id
    if done:
        await enqueue_report(ctx["redis"], task_id)


async def enqueue_report(arq: ArqRedis, task_id: uuid.UUID) -> None:
    await arq.enqueue_job("report_outreach", str(task_id), _job_id=f"outreach-report:{task_id}")


async def report_outreach(ctx: dict, task_id: str) -> None:
    async with session_scope() as session:
        task = await session.get(Task, uuid.UUID(task_id))
        user = await session.get(User, task.user_id)
        message = outreach.report(await outreach.calls_for(session, task.id), user.language)
        phone = user.phone
    if message:
        execution_id = await call_phone(phone, CallReason.CALLS_DONE, message)
        log.info("calls for task %s reported on call %s", task_id, execution_id)
