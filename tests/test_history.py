import pytest
from sqlalchemy import select

from saarthi.db.models import Call, CallDirection, Task, TaskStatus, User
from saarthi.db.session import session_scope
from saarthi.domain import history
from saarthi.jobs import tasks as task_jobs
from saarthi.sandbox.manager import Sandbox

PHONE = "+919876543210"
EXECUTION = "1a2b3c4d-0000-4000-8000-000000000001"


async def _caller_session(client) -> str:
    context = (
        await client.get(
            "/bolna/lookup", params={"contact_number": PHONE, "execution_id": EXECUTION}
        )
    ).json()
    await client.post(
        "/tools/onboard_user",
        json={
            "session": context["session"],
            "caller_name": "Savar",
            "caller_work": "student",
            "caller_language": "hi",
            "consent": "yes",
        },
    )
    return context["session"]


async def _do_task(client, session: str, goal: str, follow_up: str = "") -> dict:
    body = {"session": session, "goal": goal, "run_at": "", "repeat": "none", "wait": "no"}
    return (await client.post("/tools/do_task", json=body | {"follow_up": follow_up})).json()


async def test_do_task_records_its_call_and_the_task_it_follows_up(client):
    session = await _caller_session(client)
    first = await _do_task(client, session, "Cheapest Delhi to Patna train on 2 Nov")
    second = await _do_task(client, session, "Book the cheaper train", follow_up=first["task"])
    assert second["status"] == "started"

    async with session_scope() as db:
        earlier, later = list(await db.scalars(select(Task).order_by(Task.created_at)))
    assert earlier.call_execution_id == later.call_execution_id == EXECUTION
    assert later.follow_up_of == earlier.id

    unknown = await _do_task(client, session, "Something", follow_up="ffffff")
    assert unknown["status"] == "not_found"


@pytest.fixture
def sandbox_calls(monkeypatch) -> dict[str, list]:
    seen: dict[str, list] = {"put_calls": [], "start_task": []}

    async def ensure(user_id):
        return Sandbox("saarthi-sbx-test", "http://sandbox", "token", None)

    async def put_calls(sandbox, calls):
        seen["put_calls"].append(calls)

    async def start_task(sandbox, payload):
        seen["start_task"].append(payload)

    monkeypatch.setattr(task_jobs.manager, "ensure", ensure)
    monkeypatch.setattr(task_jobs.manager, "put_calls", put_calls)
    monkeypatch.setattr(task_jobs.manager, "start_task", start_task)
    return seen


async def test_run_task_copies_new_calls_in_and_sends_the_earlier_task(
    client, fake_arq, sandbox_calls
):
    session = await _caller_session(client)
    first = await _do_task(client, session, "Cheapest Delhi to Patna train on 2 Nov")
    async with session_scope() as db:
        user = await db.scalar(select(User))
        earlier = await db.scalar(select(Task))
        earlier.status, earlier.summary = TaskStatus.DONE, "सबसे सस्ता टिकट ₹1,245 का है।"
        earlier.result = "Sampoorna Kranti 3AC ₹1,245, departs 17:20"
        db.add_all(
            [
                Call(
                    bolna_execution_id=EXECUTION,
                    user_id=user.id,
                    direction=CallDirection.INBOUND,
                    status="completed",
                    transcript="user: पटना की ट्रेन देखो",
                    duration_seconds=180,
                ),
                Call(bolna_execution_id="in-flight", user_id=user.id, status="in-progress"),
            ]
        )
    await _do_task(client, session, "Book the cheaper train", follow_up=first["task"])
    async with session_scope() as db:
        later = await db.scalar(select(Task).where(Task.follow_up_of.is_not(None)))

    await task_jobs.run_task({"redis": fake_arq}, str(later.id))

    [copied] = sandbox_calls["put_calls"]
    assert [c["execution_id"] for c in copied] == [EXECUTION]
    assert copied[0]["task_refs"] == [first["task"], later.id.hex[:6]]
    [payload] = sandbox_calls["start_task"]
    assert payload["call_ref"] == history.call_ref(EXECUTION) == "1a2b3c"
    assert payload["follow_up"]["ref"] == first["task"]
    assert payload["follow_up"]["details"].startswith("Sampoorna Kranti")

    async with session_scope() as db:
        call = await db.scalar(select(Call).where(Call.bolna_execution_id == EXECUTION))
        assert call.sandbox_synced_at is not None
        another = await db.scalar(select(Task).where(Task.id == earlier.id))
        another.status = TaskStatus.QUEUED
    await task_jobs.run_task({"redis": fake_arq}, str(earlier.id))
    assert len(sandbox_calls["put_calls"]) == 1
