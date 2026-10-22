import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sandbox"))

from agent_server.history import (  # noqa: E402
    IST,
    TRACE_LIMIT,
    CallRecord,
    History,
    TaskRecord,
    files_changed_since,
    render_trace,
    result_line,
    tool_line,
)

ASKED = datetime(2026, 10, 21, 14, 33, tzinfo=IST)
TASK_ID = "3f9a1c00-0000-4000-8000-000000000000"


def _task(**changes) -> TaskRecord:
    fields = {
        "task_id": TASK_ID,
        "goal": "Cheapest Delhi to Patna train on 2 Nov",
        "ok": True,
        "summary": "सबसे सस्ता टिकट ₹1,245 का है।",
        "details": "Sampoorna Kranti 3AC ₹1,245",
        "started": ASKED,
        "finished": ASKED.replace(minute=35),
        "call_ref": "7f3e2a",
        "turns": 41,
        "cost_usd": 0.38,
        "raw_log": "~/.claude/projects/-home-saarthi/abc.jsonl",
        "trace": ["Looking it up.", "→ WebSearch: query=delhi patna trains"],
    }
    return TaskRecord(**(fields | changes))


def test_trace_lines_keep_the_key_input_and_cut_results():
    assert tool_line("mcp__browser__browser_navigate", {"url": "https://irctc.co.in"}) == (
        "→ browser_navigate: url=https://irctc.co.in"
    )
    assert tool_line("Write", {"file_path": "/x.csv", "content": "a,b\n" * 500}) == (
        "→ Write: file_path=/x.csv"
    )
    assert tool_line("TodoWrite", {"todos": []}) == "→ TodoWrite"

    shot = result_line([{"type": "text", "text": "Saved"}, {"type": "image", "data": "..."}], False)
    assert shot == "  ← Saved [screenshot]"
    long = result_line("x" * 5000, True)
    assert long.startswith("  ✗ ") and len(long) < 410


def test_trace_is_capped_with_a_pointer_to_the_raw_log():
    trace = render_trace(["y" * 1000] * 100, "~/raw.jsonl")
    assert len(trace) < TRACE_LIMIT + 1100
    assert trace.rstrip().endswith("the full log is ~/raw.jsonl]")


async def test_task_and_call_records_are_indexed_newest_first(tmp_path):
    history = History(tmp_path)
    record = await history.add_task(_task())
    assert record == tmp_path / "2026-10-21" / "1433-task-3f9a1c.md"
    text = record.read_text()
    assert "on call 7f3e2a" in text and "41 steps, $0.38" in text
    assert "Sampoorna Kranti" in text and "1433-task-3f9a1c.trace.md" in text
    assert "→ WebSearch" in (tmp_path / "2026-10-21" / "1433-task-3f9a1c.trace.md").read_text()
    assert not os.access(record, os.W_OK)

    # Calls arrive later than the tasks they started, and may be copied in twice.
    call = CallRecord(
        execution_id="7f3e2a99-0000",
        started=ASKED.replace(minute=32),
        transcript="user: पटना की ट्रेन देखो",
        direction="inbound",
        duration_seconds=180,
        task_refs=["3f9a1c"],
    )
    await history.add_call(call)
    await history.add_call(call)
    await history.add_task(_task(task_id="aaaaaa00-0", started=ASKED.replace(day=22)))

    lines = history.recent()
    assert [line.split(" | ")[1] for line in lines] == ["task aaaaaa", "task 3f9a1c", "call 7f3e2a"]
    assert lines[2].endswith(
        "| inbound | 3 min | started task 3f9a1c | 2026-10-21/1432-call-inb-7f3e2a.md"
    )
    assert history.find_task("3f9a1c") == record


async def test_follow_up_points_at_the_earlier_record(tmp_path):
    history = History(tmp_path)
    await history.add_task(_task())
    later = await history.add_task(
        _task(task_id="bbbbbb00-0", started=ASKED.replace(day=22), follow_up_ref="3f9a1c")
    )
    assert "- Continues: task 3f9a1c (2026-10-21/1433-task-3f9a1c.md)" in later.read_text()


def test_only_files_changed_during_the_task_are_listed(tmp_path):
    files = tmp_path / "files"
    files.mkdir()
    old, new = files / "old.txt", files / "trains.csv"
    old.write_text("x")
    os.utime(old, (0, 0))
    new.write_text("y")
    assert files_changed_since(files, ASKED.replace(year=2020)) == ["~/files/trains.csv"]
