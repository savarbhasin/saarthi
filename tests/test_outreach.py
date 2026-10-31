from datetime import datetime

from sqlalchemy import select

from saarthi.db.models import BolnaAgent, Call, OutreachStatus, Task, User
from saarthi.db.session import session_scope
from saarthi.domain import outreach
from saarthi.domain.routines import USER_TZ
from saarthi.jobs.outreach import _seconds_until_calling_hours
from saarthi.sandbox.manager import sandbox_token
from saarthi.voice.context import build_messenger_context
from saarthi.voice.speech import speakable

PHONE = "+919876543210"
SHARMA, GUPTA = "+919811122233", "+919822233344"


async def _owner_with_task(client) -> tuple[str, Task, User]:
    session = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()[
        "session"
    ]
    await client.post(
        "/tools/onboard_user",
        json={
            "session": session,
            "caller_name": "रमेश",
            "caller_work": "फल बेचता हूँ",
            "caller_language": "hi",
            "consent": "yes",
        },
    )
    await client.post(
        "/tools/do_task",
        json={
            "session": session,
            "goal": "Khata: call everyone who owes money and ask them to pay",
            "run_at": "",
            "repeat": "none",
            "wait": "yes",
        },
    )
    async with session_scope() as db:
        return session, await db.scalar(select(Task)), await db.scalar(select(User))


async def _stage_calls(client, task: Task, user: User) -> dict:
    calls = [
        {"name": "Sharma ji", "phone": "98111 22233", "purpose": "Owes ₹200 for mangoes"},
        {"name": "Gupta ji", "phone": GUPTA, "purpose": "Owes ₹450"},
        {"name": "Verma ji", "phone": "12345", "purpose": "Owes ₹100"},
        {"name": "Ramesh", "phone": PHONE, "purpose": "Owes ₹1"},
    ]
    response = await client.post(
        f"/sandbox/tasks/{task.id}/calls",
        json={"calls": calls},
        headers={"Authorization": f"Bearer {sandbox_token(user.id)}"},
    )
    return response.json()


async def test_calls_the_worker_asks_for_start_right_away(client, fake_arq):
    session, task, user = await _owner_with_task(client)
    forged = await client.post(
        f"/sandbox/tasks/{task.id}/calls",
        json={"calls": []},
        headers={"Authorization": "Bearer nope"},
    )
    assert forged.status_code == 401

    staged = await _stage_calls(client, task, user)
    assert staged["status"] == "calling"
    assert staged["calling"] == ["Sharma ji", "Gupta ji"]
    assert staged["skipped"] == ["Verma ji", "Ramesh"]  # bad number, and the owner's own

    placed = [job for job in fake_arq.jobs if job[0] == "place_outreach_call"]
    assert [fake_arq.options[job[2]]["_defer_by"] for job in placed] == [0, 20]


async def test_outcomes_are_recorded_and_reported_when_every_call_ends(client, fake_arq):
    session, task, user = await _owner_with_task(client)
    await _stage_calls(client, task, user)

    async with session_scope() as db:
        db.add(BolnaAgent(name="saarthi-messenger", agent_id="messenger-agent"))
        owner = await db.get(User, user.id)
        gupta, sharma = await outreach.calls_for(db, task.id)
        context = await build_messenger_context(db, owner, sharma)
        for call, execution in ((sharma, "exec-sharma"), (gupta, "exec-gupta")):
            call.status, call.bolna_execution_id = OutreachStatus.CALLING, execution
    assert "Sharma ji" in context["greeting"] and "upi_id" not in context

    # The person called can't reach the owner's tools with their session.
    leaked = await client.post("/tools/task_status", json={"session": context["session"]})
    assert leaked.json()["status"] == "not_onboarded"

    recorded = await client.post(
        "/tools/record_outcome",
        json={"session": context["session"], "outcome": "agreed", "note": "शुक्रवार तक देंगे"},
    )
    assert recorded.json()["status"] == "ok"

    def event(execution: str, status: str, to: str) -> dict:
        return {
            "id": execution,
            "agent_id": "messenger-agent",
            "status": status,
            "transcript": "assistant: नमस्ते",
            "telephony_data": {"to_number": to, "call_type": "outbound"},
        }

    await client.post("/webhooks/bolna", json=event("exec-sharma", "completed", SHARMA))
    assert not [job for job in fake_arq.jobs if job[0] == "report_outreach"]
    await client.post("/webhooks/bolna", json=event("exec-gupta", "no-answer", GUPTA))
    assert [job for job in fake_arq.jobs if job[0] == "report_outreach"]
    assert not [job for job in fake_arq.jobs if job[0] == "ingest_call"]

    async with session_scope() as db:
        calls = await outreach.calls_for(db, task.id)
        assert all(c.user_id is None for c in await db.scalars(select(Call)))
    assert outreach.report(calls, "hi") == ("Gupta ji: फ़ोन नहीं उठाया। Sharma ji: शुक्रवार तक देंगे।")


async def test_task_details_gives_the_full_result(client):
    session, task, user = await _owner_with_task(client)
    await client.post(
        f"/sandbox/tasks/{task.id}/result",
        json={"ok": True, "summary": "**सोना** आज महँगा है", "details": "24k ₹7,900/g (IBJA)"},
        headers={"Authorization": f"Bearer {sandbox_token(user.id)}"},
    )
    details = await client.post("/tools/task_details", json={"session": session, "task": ""})
    body = details.json()
    assert body["status"] == "done" and "IBJA" in body["details"]
    assert body["summary"] == "सोना आज महँगा है।"


def test_summaries_are_cleaned_for_speech():
    text = "**Gold** price:\n- 24k: ₹7,900\n- 22k: ₹7,250\nSource: [IBJA](https://ibja.co)"
    assert speakable(text) == "Gold price. 24k: ₹7,900. 22k: ₹7,250. Source: IBJA."
    assert speakable("## आज का भाव\n1. आम 80 रुपये") == "आज का भाव। आम 80 रुपये।"


def test_calls_wait_for_polite_hours():
    def at(hour: int) -> int:
        return _seconds_until_calling_hours(datetime(2026, 10, 22, hour, tzinfo=USER_TZ))

    assert at(12) == 0
    assert at(8) == 3600
    assert at(21) == 0  # a 9 pm job still goes out the same night
    assert at(22) == 11 * 3600
