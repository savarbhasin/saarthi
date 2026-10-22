"""The record of past calls and tasks in ~/history, written by code and never by the model.

Postgres is the source of truth; this is the user's own mirror of it, laid out by India date
so the worker can find "yesterday's" work with ls, grep and Read. Standard library only.
"""

import asyncio
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30), "IST")
INDEX_HEADER = (
    "# History, newest first\n"
    "When (India) | what and id | outcome or direction | goal or length | result or tasks | file\n"
    "\n"
)
RECENT_LINES = 10
TRACE_LIMIT = 40_000
CLIP_INPUT = 200
CLIP_RESULT = 400
CLIP_INDEX = 100
MAX_FILES_LISTED = 20
# Tool inputs worth showing on a trace line, in this order. Bulky ones (file contents,
# todo lists) are left out on purpose.
KEY_INPUTS = ("command", "url", "query", "file_path", "pattern", "element", "text", "prompt")
TOOL_PREFIXES = ("mcp__browser__", "mcp__saarthi__")
_SPACE = re.compile(r"\s+")


def clip(text: str, limit: int) -> str:
    text = _SPACE.sub(" ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def short_ref(identifier: str) -> str:
    # Same rule as the backend's refs (saarthi.domain.tasks.short_id, domain.history.call_ref).
    return identifier.replace("-", "")[:6].lower()


def tool_line(name: str, args: dict) -> str:
    for prefix in TOOL_PREFIXES:
        name = name.removeprefix(prefix)
    shown = [f"{key}={clip(str(args[key]), CLIP_INPUT)}" for key in KEY_INPUTS if args.get(key)]
    return f"→ {name}: {' '.join(shown)}" if shown else f"→ {name}"


def result_line(content: str | list | None, is_error: bool) -> str:
    if isinstance(content, list):
        text = " ".join(
            "[screenshot]" if part.get("type") == "image" else str(part.get("text", ""))
            for part in content
        )
    else:
        text = str(content or "")
    return f"  {'✗' if is_error else '←'} {clip(text, CLIP_RESULT)}"


def render_trace(lines: list[str], raw_log: str) -> str:
    kept, size = [], 0
    for line in lines:
        if size + len(line) > TRACE_LIMIT:
            kept.append(f"[trace cut here; the full log is {raw_log}]")
            break
        kept.append(line)
        size += len(line) + 1
    return "\n".join(kept) + "\n"


def files_changed_since(folder: Path, since: datetime) -> list[str]:
    if not folder.is_dir():
        return []
    cutoff = since.timestamp()
    changed = sorted(
        f"~/{path.relative_to(folder.parent)}"
        for path in folder.rglob("*")
        if path.is_file() and path.stat().st_mtime >= cutoff
    )
    if len(changed) > MAX_FILES_LISTED:
        return [*changed[:MAX_FILES_LISTED], f"and {len(changed) - MAX_FILES_LISTED} more"]
    return changed


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    goal: str
    ok: bool
    summary: str
    details: str
    started: datetime
    finished: datetime
    caller_waiting: bool = False
    call_ref: str = ""
    follow_up_ref: str = ""
    turns: int | None = None
    cost_usd: float | None = None
    raw_log: str = ""
    files: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    @property
    def ref(self) -> str:
        return short_ref(self.task_id)


@dataclass(frozen=True)
class CallRecord:
    execution_id: str
    started: datetime
    transcript: str
    direction: str = ""
    purpose: str = ""
    duration_seconds: float | None = None
    task_refs: list[str] = field(default_factory=list)

    @property
    def ref(self) -> str:
        return short_ref(self.execution_id)


def _stamp(when: datetime) -> str:
    return when.astimezone(IST).strftime("%Y-%m-%d %H:%M")


def _length(seconds: float | None) -> str:
    if not seconds:
        return "length unknown"
    return f"{round(seconds / 60)} min" if seconds >= 60 else "under 1 min"


class History:
    def __init__(self, root: Path):
        self.root = root
        self._index_lock = asyncio.Lock()

    @property
    def index(self) -> Path:
        return self.root / "INDEX.md"

    def recent(self, count: int = RECENT_LINES) -> list[str]:
        return self._entries()[:count]

    def _entries(self) -> list[str]:
        if not self.index.exists():
            return []
        lines = self.index.read_text().splitlines()[INDEX_HEADER.count("\n") :]
        return [line for line in lines if line.strip()]

    def find_task(self, ref: str) -> Path | None:
        return next(iter(sorted(self.root.glob(f"*/*-task-{ref}.md"))), None)

    async def add_task(self, task: TaskRecord) -> Path:
        base = self._base(task.started, f"task-{task.ref}")
        record, trace = base.with_name(f"{base.name}.md"), base.with_name(f"{base.name}.trace.md")
        _write(record, self._task_markdown(task, trace.name))
        _write(trace, render_trace(task.trace, task.raw_log or "not kept"))
        outcome = "done" if task.ok else "failed"
        await self._index(
            f"{_stamp(task.started)} | task {task.ref} | {outcome} | {clip(task.goal, CLIP_INDEX)}"
            f" | {clip(task.summary, CLIP_INDEX)} | {self._rel(record)}"
        )
        return record

    async def add_call(self, call: CallRecord) -> Path:
        direction = call.direction or "call"
        base = self._base(call.started, f"call-{direction[:3]}-{call.ref}")
        record = base.with_name(f"{base.name}.md")
        _write(record, self._call_markdown(call))
        tasks = f"started task {', '.join(call.task_refs)}" if call.task_refs else "no task"
        await self._index(
            f"{_stamp(call.started)} | call {call.ref} | {direction} | "
            f"{_length(call.duration_seconds)} | {tasks} | {self._rel(record)}"
        )
        return record

    def _base(self, when: datetime, name: str) -> Path:
        local = when.astimezone(IST)
        return self.root / local.strftime("%Y-%m-%d") / f"{local.strftime('%H%M')}-{name}"

    def _rel(self, path: Path) -> str:
        return str(path.relative_to(self.root))

    async def _index(self, line: str) -> None:
        # Entries arrive out of order (calls are copied in later), so keep INDEX sorted by
        # time, and replace any earlier line for the same file so rewrites stay idempotent.
        target = line.rsplit(" | ", 1)[1]
        async with self._index_lock:
            lines = [old for old in self._entries() if not old.endswith(f" | {target}")]
            lines.append(line)
            lines.sort(key=lambda entry: entry[:16], reverse=True)
            _write(self.index, INDEX_HEADER + "\n".join(lines) + "\n")

    def _task_markdown(self, task: TaskRecord, trace_name: str) -> str:
        asked = f"- Asked: {_stamp(task.started)} IST"
        if task.call_ref:
            asked += f", on call {task.call_ref}"
        if task.caller_waiting:
            asked += ", caller held the line"
        finished = f"- Finished: {task.finished.astimezone(IST).strftime('%H:%M')}"
        if task.turns is not None:
            finished += f", {task.turns} steps"
        if task.cost_usd is not None:
            finished += f", ${task.cost_usd:.2f}"
        facts = [asked, finished]
        if task.follow_up_ref:
            earlier = self.find_task(task.follow_up_ref)
            where = f" ({self._rel(earlier)})" if earlier else ""
            facts.append(f"- Continues: task {task.follow_up_ref}{where}")
        if task.files:
            facts.append(f"- Files changed: {', '.join(task.files)}")
        facts.append(f"- Step by step: {trace_name}")
        if task.raw_log:
            facts.append(f"- Raw log: {task.raw_log}")
        outcome = "done" if task.ok else "failed"
        return (
            f"# Task {task.ref}: {outcome}\n"
            + "\n".join(facts)
            + f"\n\n## Goal\n{task.goal}\n\n## Spoken summary\n{task.summary}\n\n"
            + f"## Details\n{task.details or '-'}\n"
        )

    def _call_markdown(self, call: CallRecord) -> str:
        facts = [f"- When: {_stamp(call.started)} IST, {_length(call.duration_seconds)}"]
        if call.purpose:
            facts.append(f"- Why: {call.purpose}")
        if call.task_refs:
            facts.append(f"- Tasks started on this call: {', '.join(call.task_refs)}")
        return (
            f"# Call {call.ref}: {call.direction or 'call'}\n"
            + "\n".join(facts)
            + f"\n\n## Transcript\n{call.transcript.strip()}\n"
        )


def _write(path: Path, text: str) -> None:
    # Atomic, and read-only so the worker doesn't edit its own record by accident. It runs as
    # the same user, so this guards against slips, not against a determined model.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
    os.chmod(tmp, 0o444)
    os.replace(tmp, path)
