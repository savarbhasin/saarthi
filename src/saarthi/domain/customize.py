import re
import shlex
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import McpServer, McpTransport, UserSkill

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
# Server names become part of tool names (mcp__<name>__<tool>), and these are taken.
RESERVED_SERVERS = {"browser", "saarthi"}
MAX_SKILL_CHARS = 20_000


class InvalidInput(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


@dataclass(frozen=True)
class SkillForm:
    name: str
    description: str
    instructions: str


@dataclass(frozen=True)
class ServerForm:
    name: str
    transport: str
    url: str = ""
    headers: str = ""
    command: str = ""
    args: str = ""
    env: str = ""


def _slug(value: str, field: str) -> str:
    name = value.strip().lower().replace(" ", "-")
    if not SLUG.match(name):
        raise InvalidInput(field, "Use 1-40 lowercase letters, digits and dashes.")
    return name


def _pairs(text: str, separator: str, field: str) -> dict[str, str]:
    pairs = {}
    for line in filter(None, (line.strip() for line in text.splitlines())):
        key, sep, value = line.partition(separator)
        if not sep or not key.strip():
            raise InvalidInput(field, f"Write one per line as KEY{separator}value.")
        pairs[key.strip()] = value.strip()
    return pairs


def clean_skill(form: SkillForm) -> SkillForm:
    description = form.description.strip()
    instructions = form.instructions.strip()
    if not description:
        raise InvalidInput("description", "Say when the worker should use this skill.")
    if not instructions:
        raise InvalidInput("instructions", "Write the steps the worker should follow.")
    if len(instructions) > MAX_SKILL_CHARS:
        raise InvalidInput("instructions", f"Keep it under {MAX_SKILL_CHARS:,} characters.")
    return SkillForm(_slug(form.name, "name"), " ".join(description.split()), instructions)


def server_config(form: ServerForm) -> tuple[str, McpTransport, dict]:
    name = _slug(form.name, "name").replace("-", "_")
    if name in RESERVED_SERVERS:
        raise InvalidInput("name", "That name is taken by a built-in tool.")
    try:
        transport = McpTransport(form.transport)
    except ValueError as exc:
        raise InvalidInput("transport", "Pick stdio, http or sse.") from exc

    if transport is McpTransport.STDIO:
        if not form.command.strip():
            raise InvalidInput("command", "Give the command to run, e.g. npx.")
        try:
            args = shlex.split(form.args)
        except ValueError as exc:
            raise InvalidInput("args", "Check the quotes in the arguments.") from exc
        config = {
            "command": form.command.strip(),
            "args": args,
            "env": _pairs(form.env, "=", "env"),
        }
    else:
        url = form.url.strip()
        if not re.match(r"^https?://\S+$", url):
            raise InvalidInput("url", "Give the server's full http(s) URL.")
        config = {"url": url, "headers": _pairs(form.headers, ":", "headers")}
    return name, transport, config


async def skills(db: AsyncSession, user_id: uuid.UUID) -> list[UserSkill]:
    rows = await db.scalars(
        select(UserSkill).where(UserSkill.user_id == user_id).order_by(UserSkill.name)
    )
    return list(rows)


async def servers(db: AsyncSession, user_id: uuid.UUID) -> list[McpServer]:
    rows = await db.scalars(
        select(McpServer).where(McpServer.user_id == user_id).order_by(McpServer.name)
    )
    return list(rows)


async def save_skill(db: AsyncSession, user_id: uuid.UUID, form: SkillForm) -> UserSkill:
    form = clean_skill(form)
    skill = await db.scalar(
        select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.name == form.name)
    )
    if skill is None:
        skill = UserSkill(user_id=user_id, name=form.name)
        db.add(skill)
    skill.description, skill.instructions = form.description, form.instructions
    await db.flush()
    return skill


async def save_server(db: AsyncSession, user_id: uuid.UUID, form: ServerForm) -> McpServer:
    name, transport, config = server_config(form)
    server = await db.scalar(
        select(McpServer).where(McpServer.user_id == user_id, McpServer.name == name)
    )
    if server is None:
        server = McpServer(user_id=user_id, name=name)
        db.add(server)
    server.transport, server.config = transport, config
    await db.flush()
    return server


def skills_payload(rows: list[UserSkill]) -> list[dict]:
    return [
        {"name": s.name, "description": s.description, "instructions": s.instructions}
        for s in rows
        if s.enabled
    ]


def servers_payload(rows: list[McpServer]) -> dict[str, dict]:
    # The Agent SDK's mcp_servers shape: {"name": {"type": ..., ...config}}.
    return {s.name: {"type": s.transport.value, **s.config} for s in rows if s.enabled}
