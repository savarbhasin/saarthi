import logging
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select

from saarthi.api.deps import Db
from saarthi.config import get_settings
from saarthi.db.models import (
    Call,
    CallDirection,
    McpServer,
    OutreachCall,
    Routine,
    Task,
    TaskStatus,
    User,
    UserSkill,
)
from saarthi.domain import customize, login, routines, tasks, users
from saarthi.domain.phone import InvalidPhone, normalize_phone
from saarthi.memory import profile_cache, store
from saarthi.packs import PACKS, pack_for
from saarthi.packs.base import EVERYONE, Ability
from saarthi.web import auth

log = logging.getLogger(__name__)
# The tasks page searches and filters in the browser, over this many of the latest.
TASKS_LIMIT = 200
DATED = re.compile(r"^\[\d{4}-\d{2}-\d{2}\]\s*")
router = APIRouter(prefix="/api/web")

LANGUAGES = {
    "hi": "हिन्दी",
    "en": "English",
    "bn": "বাংলা",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "mr": "मराठी",
    "gu": "ગુજરાતી",
    "kn": "ಕನ್ನಡ",
    "pa": "ਪੰਜਾਬੀ",
    "ml": "മലയാളം",
    "od": "ଓଡ଼ିଆ",
}


async def web_user(request: Request, db: Db) -> User:
    return await auth.current_user(request, db)


CurrentUser = Annotated[User, Depends(web_user)]


def invalid(field: str, message: str) -> JSONResponse:
    return JSONResponse({"field": field, "message": message}, status_code=422)


async def _owned(db: Db, model, item_id: uuid.UUID, user: User):
    item = await db.get(model, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(404, "not found")
    return item


# Sign in: Saarthi phones the user and reads out a code.


class PhoneIn(BaseModel):
    phone: str


class CodeIn(BaseModel):
    phone: str
    code: str


@router.post("/login")
async def login_send(body: PhoneIn, request: Request, db: Db):
    try:
        phone = normalize_phone(body.phone)
    except InvalidPhone:
        return invalid("phone", "That doesn't look like a phone number.")
    if await users.get_by_phone(db, phone) is None:
        return invalid("phone", "Call Saarthi once first to set up your account, then sign in.")
    try:
        code_row, code = await login.issue_code(db, phone)
    except login.TooManyCodes:
        return invalid("phone", "Too many codes. Try again in a while.")
    await db.commit()
    if get_settings().web_login_delivery == "log":
        # Local dev only: no call is made, so hand the code back instead of reading it out.
        log.warning("login code for %s: %s", phone, code)
        return {"phone": phone, "dev_code": code}
    await request.app.state.arq.enqueue_job("send_login_code", str(code_row.id), phone, code)
    return {"phone": phone}


@router.post("/login/verify")
async def login_verify(body: CodeIn, request: Request, response: Response, db: Db):
    if not await login.check_code(db, body.phone, body.code):
        await db.commit()
        return invalid("code", "Wrong or expired code.")
    user = await users.get_by_phone(db, body.phone)
    response.set_cookie(
        auth.COOKIE,
        auth.session_cookie(user.id),
        max_age=auth.SESSION_DAYS * 86400,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(auth.COOKIE)
    return {"ok": True}


# Home: what Saarthi is doing, has done and knows.


async def _recent(db: Db, model, user: User, limit: int):
    query = (
        select(model).where(model.user_id == user.id).order_by(model.created_at.desc()).limit(limit)
    )
    return list(await db.scalars(query))


def _task_card(task: Task) -> dict:
    return {
        "id": str(task.id),
        "goal": task.goal,
        "summary": task.summary or "",
        "state": _task_state(task),
        "created_at": task.created_at.isoformat(),
    }


async def _memory(db: Db, user: User) -> list[dict]:
    """Facts Saarthi remembers, with Supermemory ids so each can be deleted.

    Falls back to the cached profile (no ids, so not deletable) when Supermemory is
    unreachable, so the home page never fails because of it.
    """
    if get_settings().supermemory_api_key:
        try:
            rows = await store.facts(user.id)
            return [{"id": fact_id, "text": DATED.sub("", text)} for fact_id, text in rows]
        except Exception:
            log.warning("could not load memory for %s", user.id, exc_info=True)
    cached = await profile_cache.get(db, user.id)
    lines = (line.strip().lstrip("- ") for line in cached.splitlines())
    return [{"id": None, "text": DATED.sub("", line)} for line in lines if line]


@router.get("/home")
async def home(db: Db, user: CurrentUser):
    week_ago = datetime.now(UTC) - timedelta(days=7)
    seconds = await db.scalar(
        select(func.coalesce(func.sum(Call.duration_seconds), 0)).where(Call.user_id == user.id)
    )
    recent_tasks = await tasks.recent(db, user.id, limit=8)
    pack = pack_for(user.pack)
    return {
        "name": user.name or "",
        "pack": pack.label,
        "stats": {
            "tasks_done": await _count(db, Task, user, Task.status == TaskStatus.DONE),
            "calls_this_week": await _count(db, Call, user, Call.created_at > week_ago),
            "minutes_talked": round(float(seconds) / 60),
            "people_called": await _count(db, OutreachCall, user),
        },
        "working": [_task_card(t) for t in recent_tasks if t.status in tasks.ACTIVE],
        "recent_tasks": [_task_card(t) for t in recent_tasks if t.status not in tasks.ACTIVE][:3],
        "upcoming": [
            {"id": str(r.id), "text": routines.describe(r)}
            for r in await routines.upcoming(db, user.id, limit=4)
        ],
        "calls": [
            {
                "id": str(c.id),
                "inbound": c.direction is CallDirection.INBOUND,
                "seconds": round(float(c.duration_seconds or 0)),
                "created_at": c.created_at.isoformat(),
            }
            for c in await _recent(db, Call, user, 5)
        ],
        "outreach": [
            {
                "id": str(o.id),
                "name": o.contact_name,
                "status": o.status.value,
                "note": o.note or "",
                "created_at": o.created_at.isoformat(),
            }
            for o in await _recent(db, OutreachCall, user, 5)
        ],
    }


class FactIn(BaseModel):
    text: str


@router.get("/memory")
async def memory_list(db: Db, user: CurrentUser):
    return await _memory(db, user)


@router.post("/memory")
async def memory_add(body: FactIn, user: CurrentUser):
    text = body.text.strip()
    if not text:
        return invalid("text", "Write what Saarthi should remember.")
    if not get_settings().supermemory_api_key:
        raise HTTPException(503, "memory is not set up")
    await store.remember(user.id, text[:500])
    return {"ok": True}


@router.delete("/memory/{fact_id}")
async def memory_forget(fact_id: str, db: Db, user: CurrentUser):
    if not get_settings().supermemory_api_key:
        raise HTTPException(503, "memory is not set up")
    # Forgetting is scoped to the user's own namespace, so another user's id does nothing.
    await store.forget_ids(user.id, [fact_id])
    # Refresh what the voice agent is given at the start of each call.
    await profile_cache.put(db, user.id, await store.profile_text(user.id))
    return {"ok": True}


# Guide: what Saarthi can do, for everyone and for this user's kind of work.


def _abilities(abilities: tuple[Ability, ...]) -> list[dict]:
    return [{"title": a.title, "detail": a.detail, "examples": list(a.examples)} for a in abilities]


@router.get("/guide")
async def guide(user: CurrentUser):
    pack = pack_for(user.pack)
    return {
        "pack": pack.name,
        "pack_label": pack.label,
        "everyone": _abilities(EVERYONE),
        "profile": _abilities(pack.abilities),
    }


# Profile and standing instructions.


class ProfileIn(BaseModel):
    name: str
    language: str
    pack: str
    occupation: str = ""
    custom_instructions: str = ""


async def _count(db: Db, model, user: User, *conditions) -> int:
    query = select(func.count()).select_from(model).where(model.user_id == user.id, *conditions)
    return await db.scalar(query)


@router.get("/me")
async def me(user: CurrentUser):
    return {
        "phone": user.phone,
        "name": user.name or "",
        "language": user.language,
        "pack": user.pack,
        "occupation": user.occupation or "",
        "custom_instructions": user.custom_instructions or "",
        "options": {
            "languages": LANGUAGES,
            "packs": {name: pack.label for name, pack in PACKS.items()},
        },
    }


@router.put("/me")
async def me_save(body: ProfileIn, user: CurrentUser):
    if not body.name.strip():
        return invalid("name", "Your name can't be empty.")
    user.name = body.name.strip()
    user.language = body.language if body.language in users.SUPPORTED_LANGUAGES else user.language
    user.pack = body.pack if body.pack in PACKS else user.pack
    user.occupation = body.occupation.strip() or None
    user.custom_instructions = body.custom_instructions.strip()[:4000] or None
    return {"ok": True}


# Skills: instructions the worker loads when a task matches their description.


class SkillIn(BaseModel):
    name: str
    description: str
    instructions: str


class ToggleIn(BaseModel):
    enabled: bool


def _skill(skill: UserSkill) -> dict:
    return {
        "id": str(skill.id),
        "name": skill.name,
        "description": skill.description,
        "instructions": skill.instructions,
        "enabled": skill.enabled,
    }


@router.get("/skills")
async def skills_list(db: Db, user: CurrentUser):
    return [_skill(s) for s in await customize.skills(db, user.id)]


@router.post("/skills")
async def skills_save(body: SkillIn, db: Db, user: CurrentUser):
    form = customize.SkillForm(body.name, body.description, body.instructions)
    try:
        skill = await customize.save_skill(db, user.id, form)
    except customize.InvalidInput as exc:
        return invalid(exc.field, str(exc))
    return _skill(skill)


@router.patch("/skills/{skill_id}")
async def skills_toggle(skill_id: uuid.UUID, body: ToggleIn, db: Db, user: CurrentUser):
    skill = await _owned(db, UserSkill, skill_id, user)
    skill.enabled = body.enabled
    return _skill(skill)


@router.delete("/skills/{skill_id}")
async def skills_delete(skill_id: uuid.UUID, db: Db, user: CurrentUser):
    await db.delete(await _owned(db, UserSkill, skill_id, user))
    return {"ok": True}


# Connectors: MCP servers the worker can use.


class ServerIn(BaseModel):
    name: str
    transport: str
    url: str = ""
    headers: str = ""
    command: str = ""
    args: str = ""
    env: str = ""


def _server(server: McpServer) -> dict:
    config = server.config
    # Header and env values are often secrets; only their names go back to the browser.
    return {
        "id": str(server.id),
        "name": server.name,
        "transport": server.transport.value,
        "enabled": server.enabled,
        "url": config.get("url", ""),
        "command": " ".join([config.get("command", ""), *config.get("args", [])]).strip(),
        "secret_names": sorted([*config.get("headers", {}), *config.get("env", {})]),
    }


@router.get("/connectors")
async def connectors_list(db: Db, user: CurrentUser):
    return [_server(s) for s in await customize.servers(db, user.id)]


@router.post("/connectors")
async def connectors_save(body: ServerIn, db: Db, user: CurrentUser):
    form = customize.ServerForm(**body.model_dump())
    try:
        server = await customize.save_server(db, user.id, form)
    except customize.InvalidInput as exc:
        return invalid(exc.field, str(exc))
    return _server(server)


@router.patch("/connectors/{server_id}")
async def connectors_toggle(server_id: uuid.UUID, body: ToggleIn, db: Db, user: CurrentUser):
    server = await _owned(db, McpServer, server_id, user)
    server.enabled = body.enabled
    return _server(server)


@router.delete("/connectors/{server_id}")
async def connectors_delete(server_id: uuid.UUID, db: Db, user: CurrentUser):
    await db.delete(await _owned(db, McpServer, server_id, user))
    return {"ok": True}


# What Saarthi has done and will do.


def _task_state(task: Task) -> str:
    if task.status in tasks.ACTIVE:
        return "working"
    return "done" if task.status is TaskStatus.DONE else "failed"


@router.get("/tasks")
async def tasks_list(db: Db, user: CurrentUser):
    return [
        {
            "id": str(t.id),
            "goal": t.goal,
            "summary": t.summary or "",
            "result": t.result or "",
            "state": _task_state(t),
            "created_at": t.created_at.isoformat(),
        }
        for t in await tasks.recent(db, user.id, limit=TASKS_LIMIT)
    ]


@router.get("/schedule")
async def schedule_list(db: Db, user: CurrentUser):
    rows = await routines.upcoming(db, user.id, limit=50)
    return [{"id": str(r.id), "text": routines.describe(r)} for r in rows]


@router.delete("/schedule/{routine_id}")
async def schedule_delete(routine_id: uuid.UUID, db: Db, user: CurrentUser):
    routine = await _owned(db, Routine, routine_id, user)
    routine.active = False
    return {"ok": True}
