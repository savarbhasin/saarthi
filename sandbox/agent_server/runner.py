import os
import re
from dataclasses import dataclass
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

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
    max_turns = int(os.environ.get("WORKER_MAX_TURNS", "60"))
    mcp_servers: dict = {"browser": _browser_server()}
    if calls_url:
        mcp_servers["saarthi"] = calls_server(calls_url)
    return ClaudeAgentOptions(
        model=os.environ["WORKER_MODEL"],
        system_prompt=system_prompt,
        cwd=str(HOME),
        permission_mode="bypassPermissions",
        mcp_servers=mcp_servers,
        tools=BUILTIN_TOOLS,
        allowed_tools=[*BUILTIN_TOOLS, *(f"mcp__{name}" for name in mcp_servers)],
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
) -> Outcome:
    final: ResultMessage | None = None
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
        ),
    ):
        if isinstance(message, ResultMessage):
            final = message
    if final is None or not final.result:
        return Outcome(False, "काम पूरा नहीं हो पाया।", "agent produced no result", None, None)
    summary, details = parse_final(final.result)
    return Outcome(not final.is_error, summary, details, final.total_cost_usd, final.session_id)
