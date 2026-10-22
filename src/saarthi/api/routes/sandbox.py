import secrets
import uuid

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from saarthi.api.deps import Db
from saarthi.config import get_settings
from saarthi.db.models import Task, User
from saarthi.domain import outreach, tasks
from saarthi.jobs.outreach import start_calls
from saarthi.sandbox.manager import sandbox_token
from saarthi.voice.speech import speakable

router = APIRouter(prefix="/sandbox")


class TaskResult(BaseModel):
    ok: bool
    summary: str
    details: str = ""
    cost_usd: float | None = None
    session_id: str | None = None


class CallRequestBody(BaseModel):
    name: str
    phone: str
    purpose: str


class CallsRequest(BaseModel):
    calls: list[CallRequestBody]


async def _authorized_task(db: Db, task_id: uuid.UUID, authorization: str | None) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(404, "unknown task")
    expected = f"Bearer {sandbox_token(task.user_id)}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(401, "invalid token")
    return task


@router.post("/tasks/{task_id}/calls")
async def request_calls(
    task_id: uuid.UUID,
    body: CallsRequest,
    request: Request,
    db: Db,
    authorization: str | None = Header(None),
) -> dict[str, object]:
    task = await _authorized_task(db, task_id, authorization)
    user = await db.get(User, task.user_id)
    requests = [outreach.CallRequest(c.name, c.phone, c.purpose) for c in body.calls]
    try:
        calls, skipped = await outreach.create_calls(db, user, task, requests)
    except outreach.NothingToCall:
        return {"status": "rejected", "reason": "none of the phone numbers are valid"}
    await db.commit()
    await start_calls(request.app.state.arq, calls)
    return {
        "status": "calling",
        "calling": [c.contact_name for c in calls],
        "skipped": skipped,
        "next": "In your SUMMARY, say who is being called; Saarthi reports back what they said.",
    }


@router.post("/tasks/{task_id}/result")
async def task_result(
    task_id: uuid.UUID,
    body: TaskResult,
    request: Request,
    db: Db,
    authorization: str | None = Header(None),
) -> dict[str, str]:
    task = await _authorized_task(db, task_id, authorization)
    if task.status not in tasks.ACTIVE:
        return {"status": "already_recorded"}

    tasks.finish(
        task,
        ok=body.ok,
        summary=speakable(body.summary),
        result=body.details,
        cost_usd=body.cost_usd,
    )
    task.sdk_session_id = body.session_id
    await db.commit()
    # If the caller is holding for it, give wait_for_task the chance to deliver it on the call;
    # the delayed callback only rings if they hung up first (it skips reported tasks).
    delay = get_settings().held_callback_delay_seconds if task.caller_waiting else 0
    await request.app.state.arq.enqueue_job(
        "report_task", str(task_id), _job_id=f"report:{task_id}", _defer_by=delay
    )
    return {"status": "ok"}
