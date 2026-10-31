from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from saarthi.api.deps import BolnaAuth, Db
from saarthi.db.models import BolnaAgent, Call, CallDirection
from saarthi.domain import login, outreach, tasks, users
from saarthi.domain.phone import InvalidPhone, normalize_phone
from saarthi.jobs.outreach import enqueue_report
from saarthi.voice.outbound import MESSENGER_AGENT

router = APIRouter(prefix="/webhooks", dependencies=[BolnaAuth])


class TelephonyData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    from_number: str | None = None
    to_number: str | None = None
    call_type: str | None = None


class ExecutionEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    agent_id: str | None = None
    status: str
    transcript: str | None = None
    extracted_data: dict[str, Any] | None = None
    conversation_duration: float | None = None
    answered_by_voice_mail: bool | None = None
    telephony_data: TelephonyData | None = None
    context_details: dict[str, Any] | None = None


def _counterpart_phone(event: ExecutionEvent) -> tuple[CallDirection | None, str | None]:
    telephony = event.telephony_data or TelephonyData()
    if telephony.call_type == "inbound":
        direction, raw = CallDirection.INBOUND, telephony.from_number
    elif telephony.call_type == "outbound":
        direction, raw = CallDirection.OUTBOUND, telephony.to_number
    else:
        return None, None
    if not raw:
        return direction, None
    try:
        return direction, normalize_phone(raw)
    except InvalidPhone:
        return direction, raw


def _person_answered(event: ExecutionEvent) -> bool:
    # Busy, no-answer and failed calls are final statuses of their own; only `completed`
    # means the call connected, and Bolna flags it when a voicemail picked up.
    return event.status == "completed" and not event.answered_by_voice_mail


@router.post("/bolna")
async def bolna_execution(request: Request, db: Db) -> dict[str, str]:
    event = ExecutionEvent.model_validate(await request.json())
    direction, phone = _counterpart_phone(event)
    agent_name = (
        await db.scalar(select(BolnaAgent.name).where(BolnaAgent.agent_id == event.agent_id))
        if event.agent_id
        else None
    )
    # A messenger call is with someone the user knows; never file it under any user's memory,
    # even if that person happens to use Saarthi too.
    is_messenger = agent_name == MESSENGER_AGENT
    # A call that read out a sign-in code is kept out of memory, history and the calls log.
    is_code_call = await login.is_code_call(db, event.id)
    private = is_messenger or is_code_call
    user = await users.get_by_phone(db, phone) if phone and not private else None

    values = {
        "bolna_execution_id": event.id,
        "user_id": user.id if user else None,
        "agent_name": agent_name,
        "direction": direction,
        "status": event.status,
        "transcript": None if is_code_call else event.transcript,
        "extracted": event.extracted_data,
        "duration_seconds": event.conversation_duration,
    }
    stmt = insert(Call).values(**values)
    # Events for one execution arrive several times as the status advances; later events
    # must not wipe fields an earlier one filled.
    updates = {k: stmt.excluded[k] for k, v in values.items() if v is not None}
    call_id = await db.scalar(
        stmt.on_conflict_do_update(
            index_elements=[Call.bolna_execution_id], set_=updates
        ).returning(Call.id)
    )
    if not is_messenger and _person_answered(event):
        task = await tasks.by_callback(db, event.id)
        if task is not None and task.reported_at is None:
            tasks.mark_reported([task])
    await db.commit()

    if is_messenger:
        await _track_outreach(request, db, event)
    elif event.status == "completed" and user is not None:
        await request.app.state.arq.enqueue_job(
            "ingest_call", str(call_id), _job_id=f"ingest:{event.id}"
        )
    return {"status": "ok"}


async def _track_outreach(request: Request, db, event: ExecutionEvent) -> None:
    final = outreach.BOLNA_FINAL.get(event.status)
    call = await outreach.by_execution(db, event.id) if final else None
    if call is None:
        return
    outreach.finish(call, final)
    done = await outreach.all_finished(db, call.task_id)
    await db.commit()
    if done:
        await enqueue_report(request.app.state.arq, call.task_id)
