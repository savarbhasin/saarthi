import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from agent_server import history
from agent_server.calls import calls_server
from agent_server.prompt import LANGUAGE_NAMES, QUICK_NOTE, SYSTEM_PROMPT

HOME = Path.home()
# Built-in Claude Code tools the worker gets. The rest (worktrees, cron, notebooks, agents...)
# only bloat every request; the browser comes from the Playwright MCP server.
BUILTIN_TOOLS = [
    "Bash",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "TodoWrite",
]
SUMMARY_RE = re.compile(r"SUMMARY:\s*(?P<summary>.+?)\s*(?:DETAILS:\s*(?P<details>.*))?$", re.S)


@dataclass(frozen=True)
class Outcome:
    ok: bool
    summary: str
    details: str
    cost_usd: float | None
    session_id: str | None
    turns: int | None = None
    trace: list[str] = field(default_factory=list)

    @property
    def raw_log(self) -> str:
        # Where the SDK keeps the full transcript of a run: ~/.claude/projects/<cwd with - for />.
        if not self.session_id:
            return ""
        project = str(HOME).replace("/", "-")
        return f"~/.claude/projects/{project}/{self.session_id}.jsonl"


QUICK_MAX_TURNS = 12


def _options(
    *,
    name: str,
    profile: str,
    now: str,
    resume: str | None,
    quick: bool,
    language: str,
    pack_prompt: str,
    calls_url: str,
    context_note: str,
    extra_servers: dict[str, dict],
    skills: list[str],
) -> ClaudeAgentOptions:
    system_prompt = SYSTEM_PROMPT.format(
        name=name,
        profile=profile or "-",
        now=now,
        pack_prompt=pack_prompt,
        language_name=LANGUAGE_NAMES.get(language, "Hindi"),
    )
    if quick:
        system_prompt += QUICK_NOTE.format(name=name)
    system_prompt += context_note
    max_turns = int(os.environ.get("WORKER_MAX_TURNS", "60"))
    mcp_servers: dict = {**extra_servers, "browser": _browser_server()}
    if calls_url:
        mcp_servers["saarthi"] = calls_server(calls_url)
    # Skills the user wrote in the web app live in ~/.claude/skills (see customize.py).
    tools = [*BUILTIN_TOOLS, "Skill"] if skills else BUILTIN_TOOLS
    return ClaudeAgentOptions(
        model=os.environ["WORKER_MODEL"],
        system_prompt=system_prompt,
        cwd=str(HOME),
        permission_mode="bypassPermissions",
        mcp_servers=mcp_servers,
        tools=tools,
        allowed_tools=[*tools, *(f"mcp__{server}" for server in mcp_servers)],
        # A filter on what the model is shown: Claude Code's bundled skills stay hidden.
        skills=skills or None,
        max_turns=min(max_turns, QUICK_MAX_TURNS) if quick else max_turns,
        max_budget_usd=float(os.environ.get("WORKER_MAX_BUDGET_USD", "1.5")),
        resume=resume,
    )


def _browser_server() -> dict:
    return {
        "type": "stdio",
        "command": "playwright-mcp",
        "args": [
            "--browser",
            "chromium",
            "--user-data-dir",
            str(HOME / ".browser-profile"),
            "--output-dir",
            str(HOME / "files" / "browser"),
            "--viewport-size",
            "1280,800",
        ],
    }


def parse_final(text: str) -> tuple[str, str]:
    match = SUMMARY_RE.search(text.strip())
    if not match:
        return text.strip()[:300], text.strip()
    return match["summary"].strip(), (match["details"] or "").strip()


async def run(
    goal: str,
    *,
    name: str,
    profile: str,
    now: str,
    resume: str | None,
    quick: bool = False,
    language: str = "hi",
    pack_prompt: str = "",
    calls_url: str = "",
    context_note: str = "",
    extra_servers: dict[str, dict] | None = None,
    skills: list[str] | None = None,
) -> Outcome:
    final: ResultMessage | None = None
    trace: list[str] = []
    async for message in query(
        prompt=goal,
        options=_options(
            name=name,
            profile=profile,
            now=now,
            resume=resume,
            quick=quick,
            language=language,
            pack_prompt=pack_prompt,
            calls_url=calls_url,
            context_note=context_note,
            extra_servers=extra_servers or {},
            skills=skills or [],
        ),
    ):
        if isinstance(message, ResultMessage):
            final = message
        else:
            trace.extend(_trace_lines(message))
    if final is None or not final.result:
        return Outcome(
            False, "काम पूरा नहीं हो पाया।", "agent produced no result", None, None, trace=trace
        )
    summary, details = parse_final(final.result)
    return Outcome(
        not final.is_error,
        summary,
        details,
        final.total_cost_usd,
        final.session_id,
        turns=final.num_turns,
        trace=trace,
    )


def _trace_lines(message) -> list[str]:
    if not isinstance(message, AssistantMessage | UserMessage) or isinstance(message.content, str):
        return []
    lines = []
    for block in message.content:
        if isinstance(block, TextBlock) and isinstance(message, AssistantMessage):
            lines.append(block.text.strip())
        elif isinstance(block, ToolUseBlock):
            lines.append(history.tool_line(block.name, block.input))
        elif isinstance(block, ToolResultBlock):
            lines.append(history.result_line(block.content, bool(block.is_error)))
    return [line for line in lines if line]
