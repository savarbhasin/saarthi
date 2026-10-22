import asyncio
import logging
import os
import secrets
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from agent_server import runner
from agent_server.history import IST, CallRecord, History, TaskRecord, files_changed_since
from agent_server.prompt import FOLLOW_UP_NOTE, RECENT_NOTE

log = logging.getLogger("agent_server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TOKEN = os.environ["SANDBOX_TOKEN"]
MAX_PARALLEL = int(os.environ.get("WORKER_MAX_PARALLEL", "2"))

app = FastAPI(title="Saarthi sandbox agent")
_slots = asyncio.Semaphore(MAX_PARALLEL)
_running: set[asyncio.Task] = set()
history = History(Path.home() / "history")


class FollowUp(BaseModel):
    ref: str
    asked: str
    goal: str
    summary: str = ""
    details: str = ""


class TaskRequest(BaseModel):
    task_id: str
    goal: str
    name: str
    profile: str = ""
    now: str
    callback_url: str
    resume_session_id: str | None = None
    quick: bool = False
    language: str = "hi"
    pack_prompt: str = ""
    calls_url: str = ""
    call_ref: str = ""
    follow_up: FollowUp | None = None


class CallIn(BaseModel):
    execution_id: str
    started: datetime
    transcript: str
    direction: str = ""
    purpose: str = ""
    duration_seconds: float | None = None
    task_refs: list[str] = []


class CallsIn(BaseModel):
    calls: list[CallIn]


def _check(authorization: str | None) -> None:
    if not authorization or not secrets.compare_digest(authorization, f"Bearer {TOKEN}"):
        raise HTTPException(401, "invalid token")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "running": len(_running)}


@app.post("/tasks", status_code=202)
async def start_task(req: TaskRequest, authorization: str | None = Header(None)) -> dict:
    _check(authorization)
    job = asyncio.create_task(_execute(req))
    _running.add(job)
    job.add_done_callback(_running.discard)
    return {"accepted": req.task_id}


@app.post("/history/calls")
async def store_calls(body: CallsIn, authorization: str | None = Header(None)) -> dict:
    _check(authorization)
    for call in body.calls:
        await history.add_call(CallRecord(**call.model_dump()))
    return {"stored": len(body.calls)}


def _context_note(req: TaskRequest) -> str:
    note = ""
    if recent := history.recent():
        note += RECENT_NOTE.format(lines="\n".join(recent))
    if req.follow_up:
        record = history.find_task(req.follow_up.ref)
        where = (
            f"Read its record ~/history/{record.relative_to(history.root)} and the .trace.md "
            "next to it before you start."
            if record
            else "It ran before ~/history was kept, so this is all there is:"
        )
        earlier = req.follow_up
        note += FOLLOW_UP_NOTE.format(
            name=req.name,
            ref=earlier.ref,
            asked=earlier.asked,
            where=where,
            goal=earlier.goal,
            summary=earlier.summary or "-",
            details=earlier.details or "-",
        )
    return note


async def _execute(req: TaskRequest) -> None:
    async with _slots:
        log.info("task %s started: %s", req.task_id, req.goal)
        started = datetime.now(IST)
        outcome = None
        try:
            outcome = await runner.run(
                req.goal,
                name=req.name,
                profile=req.profile,
                now=req.now,
                resume=req.resume_session_id,
                quick=req.quick,
                language=req.language,
                pack_prompt=req.pack_prompt,
                calls_url=req.calls_url,
                context_note=_context_note(req),
            )
            body = {
                "ok": outcome.ok,
                "summary": outcome.summary,
                "details": outcome.details,
                "cost_usd": outcome.cost_usd,
                "session_id": outcome.session_id,
            }
        except Exception as exc:
            log.exception("task %s crashed", req.task_id)
            body = {"ok": False, "summary": "काम में दिक्कत आ गई।", "details": repr(exc)}
        log.info("task %s finished ok=%s", req.task_id, body["ok"])
        await _record(req, body, outcome, started)
        await _report(req.callback_url, body)


async def _record(
    req: TaskRequest, body: dict, outcome: runner.Outcome | None, started: datetime
) -> None:
    # The history is a convenience for later tasks; it must never stop the result reaching
    # the user.
    try:
        await history.add_task(
            TaskRecord(
                task_id=req.task_id,
                goal=req.goal,
                ok=body["ok"],
                summary=body["summary"],
                details=body["details"],
                started=started,
                finished=datetime.now(IST),
                caller_waiting=req.quick,
                call_ref=req.call_ref,
                follow_up_ref=req.follow_up.ref if req.follow_up else "",
                turns=outcome.turns if outcome else None,
                cost_usd=outcome.cost_usd if outcome else None,
                raw_log=outcome.raw_log if outcome else "",
                files=files_changed_since(Path.home() / "files", started),
                trace=outcome.trace if outcome else [],
            )
        )
    except Exception:
        log.exception("could not write history for task %s", req.task_id)


async def _report(url: str, body: dict) -> None:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with httpx.AsyncClient(timeout=30) as http:
        for attempt in range(5):
            try:
                (await http.post(url, json=body, headers=headers)).raise_for_status()
                return
            except httpx.HTTPError:
                log.warning("result callback failed (attempt %d)", attempt + 1)
                await asyncio.sleep(2**attempt)
