import pytest

from saarthi.db.models import Task, TaskStatus, User
from saarthi.db.session import session_scope
from saarthi.jobs import tasks as task_jobs

PHONE = "+919876543210"
SUMMARY = "सबसे सस्ता टिकट ₹1,245 का है।"


@pytest.fixture
def placed_calls(monkeypatch) -> list[str]:
    placed: list[str] = []

    async def fake_call_phone(phone, reason, message):
        placed.append(message)
        return "exec-callback"

    monkeypatch.setattr(task_jobs, "call_phone", fake_call_phone)
    return placed


async def _done_task() -> Task:
    async with session_scope() as db:
        user = User(phone=PHONE, name="Savar")
        db.add(user)
        await db.flush()
        task = Task(user_id=user.id, goal="Cheapest train", status=TaskStatus.DONE, summary=SUMMARY)
        db.add(task)
    return task


def _event(status: str, voicemail: bool | None = None) -> dict:
    return {
        "id": "exec-callback",
        "status": status,
        "answered_by_voice_mail": voicemail,
        "transcript": f"assistant: नमस्ते Savar जी, सारथी बोल रहा हूँ। {SUMMARY}",
        "telephony_data": {"to_number": PHONE, "call_type": "outbound"},
    }


@pytest.mark.parametrize(
    ("status", "voicemail", "heard"),
    [
        ("completed", False, True),
        ("completed", None, True),
        ("completed", True, False),
        ("no-answer", None, False),
        ("busy", None, False),
        ("failed", None, False),
    ],
)
async def test_callback_counts_as_heard_only_when_a_person_answers(
    client, placed_calls, status, voicemail, heard
):
    task = await _done_task()
    await task_jobs.report_task({}, str(task.id))
    assert placed_calls == [SUMMARY]
    async with session_scope() as db:
        assert (await db.get(Task, task.id)).reported_at is None

    await client.post("/webhooks/bolna", json=_event(status, voicemail))

    async with session_scope() as db:
        assert ((await db.get(Task, task.id)).reported_at is not None) is heard
    greeting = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()
    assert (SUMMARY in greeting["greeting"]) is not heard


async def test_callback_is_placed_once(client, placed_calls):
    task = await _done_task()
    await task_jobs.report_task({}, str(task.id))
    await task_jobs.report_task({}, str(task.id))
    assert len(placed_calls) == 1
