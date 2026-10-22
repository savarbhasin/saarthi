import logging
import uuid
from datetime import UTC, datetime

from saarthi.config import get_settings
from saarthi.db.models import Task, TaskStatus, User
from saarthi.db.session import session_scope
from saarthi.domain import history, tasks
from saarthi.domain.routines import USER_TZ
from saarthi.memory import profile_cache
from saarthi.packs import pack_for
from saarthi.sandbox import manager
from saarthi.voice.context import CallReason
from saarthi.voice.outbound import call_phone

log = logging.getLogger(__name__)

START_FAILED = "माफ़ कीजिए, आपका काम शुरू नहीं हो पाया। थोड़ी देर बाद फिर से कहिए।"


async def run_task(ctx: dict, task_id: str) -> None:
    async with session_scope() as session:
        task = await session.get(Task, uuid.UUID(task_id))
        if task is None or task.status is not TaskStatus.QUEUED:
            return
        user = await session.get(User, task.user_id)
        task.status = TaskStatus.RUNNING
        profile = await profile_cache.get(session, user.id)
        earlier = await session.get(Task, task.follow_up_of) if task.follow_up_of else None
        task_url = f"{get_settings().sandbox_api_url}/sandbox/tasks/{task_id}"
        payload = {
            "task_id": task_id,
            "goal": task.goal,
            "name": user.name or "the user",
            "profile": "\n".join(p for p in (user.occupation, profile) if p),
            "now": datetime.now(UTC).astimezone(USER_TZ).strftime("%A %d %B %Y, %I:%M %p"),
            "callback_url": f"{task_url}/result",
            "calls_url": f"{task_url}/calls",
            "quick": task.caller_waiting,
            "language": user.language,
            "pack_prompt": pack_for(user.pack).worker_prompt,
            "call_ref": history.call_ref(task.call_execution_id) if task.call_execution_id else "",
            "follow_up": history.follow_up_payload(earlier) if earlier else None,
        }

    try:
        sandbox = await manager.ensure(user.id)
        await _sync_calls(sandbox, user.id)
        await manager.start_task(sandbox, payload)
        log.info(
            "task %s running in %s (vnc port %s)", task_id, sandbox.name, sandbox.vnc_host_port
        )
    except Exception:
        log.exception("could not start task %s", task_id)
        async with session_scope() as session:
            task = await session.get(Task, uuid.UUID(task_id))
            tasks.finish(task, ok=False, summary=START_FAILED, result=None, cost_usd=None)
        await ctx["redis"].enqueue_job("report_task", task_id, _job_id=f"report:{task_id}")


async def _sync_calls(sandbox: manager.Sandbox, user_id: uuid.UUID) -> None:
    # Done here rather than after each call so a sandbox never starts just to store a call.
    # A failure only costs the worker some context, so it never stops the task.
    try:
        async with session_scope() as session:
            calls = await history.unsynced_calls(session, user_id)
            if not calls:
                return
            await manager.put_calls(sandbox, await history.call_payloads(session, calls))
            history.mark_synced(calls)
    except Exception:
        log.exception("could not copy calls into %s", sandbox.name)


async def report_task(ctx: dict, task_id: str) -> None:
    async with session_scope() as session:
        task = await session.get(Task, uuid.UUID(task_id))
        if task is None or task.reported_at is not None or task.callback_execution_id:
            return
        user = await session.get(User, task.user_id)
        phone, summary = user.phone, task.summary or ""

    try:
        execution_id = await call_phone(phone, CallReason.TASK_RESULT, summary)
    except Exception:
        # Left unreported: the next time they call in, the greeting tells them instead.
        log.exception("callback for task %s failed", task_id)
        return
    # Not marked heard yet: the execution webhook does that once a person picks up. On
    # voicemail or no answer it stays unheard and the next greeting tells them.
    async with session_scope() as session:
        task = await session.get(Task, uuid.UUID(task_id))
        task.callback_execution_id = execution_id
    log.info("task %s callback placed on call %s", task_id, execution_id)
