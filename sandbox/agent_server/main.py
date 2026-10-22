import asyncio
import logging
import os
import secrets

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from agent_server import runner

log = logging.getLogger("agent_server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TOKEN = os.environ["SANDBOX_TOKEN"]
MAX_PARALLEL = int(os.environ.get("WORKER_MAX_PARALLEL", "2"))

app = FastAPI(title="Saarthi sandbox agent")
_slots = asyncio.Semaphore(MAX_PARALLEL)
_running: set[asyncio.Task] = set()


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


async def _execute(req: TaskRequest) -> None:
    async with _slots:
        log.info("task %s started: %s", req.task_id, req.goal)
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
        await _report(req.callback_url, body)


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
