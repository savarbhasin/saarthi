from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from saarthi.db.models import Routine, RoutineKind, Task, TaskStatus, User
from saarthi.db.session import session_scope
from saarthi.domain.routines import cron_for, parse_local_time
from saarthi.packs import PACKS, pick_pack
from saarthi.sandbox.manager import sandbox_token

PHONE = "+919876543210"


async def _new_user_session(client, work="software engineer") -> str:
    session = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()[
        "session"
    ]
    await client.post(
        "/tools/onboard_user",
        json={
            "session": session,
            "caller_name": "Savar",
            "caller_work": work,
            "caller_language": "hi",
            "consent": "yes",
        },
    )
    return session


@pytest.mark.parametrize(
    ("work", "pack"),
    [
        ("मैं फल बेचता हूँ", "phal_sabzi"),
        ("sabzi ka thela", "phal_sabzi"),
        ("सब्जियां बेचता हूँ", "phal_sabzi"),
        ("kheti karta hoon, mandi mein bechta hoon", "kisan"),
        ("मैं किसान हूँ", "kisan"),
        ("किराने की दुकान है", "kirana"),
        ("general store chalata hoon", "kirana"),
        ("plumber hoon", "service_pro"),
        ("मैं दर्जी हूँ", "service_pro"),
        ("Ola aur Uber chalata hoon", "gig_driver"),
        ("Swiggy delivery", "gig_driver"),
        ("ऑटो चलाता हूँ", "gig_driver"),
        ("retired teacher", "elder_care"),
        ("पेंशन पर हूँ", "elder_care"),
        ("software engineer", "general"),
        ("chocolate banata hoon", "general"),
        (None, "general"),
    ],
)
def test_pack_is_picked_from_what_the_caller_does(work, pack):
    assert pick_pack(work).name == pack


def test_every_pack_instructs_both_agents():
    for pack in PACKS.values():
        if pack.name != "general":
            assert pack.voice_prompt and "~/files/" in pack.worker_prompt, pack.name


def test_local_times_are_ist_and_repeat_becomes_cron():
    when = parse_local_time("2026-10-21 07:00")
    assert when == datetime(2026, 10, 21, 1, 30, tzinfo=UTC)
    assert cron_for(when, "daily") == "0 7 * * *"
    assert cron_for(when, "weekly") == "0 7 * * 3"
    assert cron_for(when, "none") is None


async def test_general_user_gets_no_pack_prompt(client):
    await _new_user_session(client)
    context = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()
    assert context["pack_prompt"] == ""
    assert context["call_reason"] == "inbound"
    assert context["now"]


async def test_do_task_now_queues_sandbox_work(client, fake_arq):
    session = await _new_user_session(client)
    result = (
        await client.post(
            "/tools/do_task",
            json={
                "session": session,
                "goal": "Find tomorrow's Delhi to Agra trains",
                "run_at": "",
                "repeat": "none",
            },
        )
    ).json()
    assert result["status"] == "started"
    name, args, job_id = fake_arq.jobs[-1]
    assert name == "run_task" and job_id == f"task:{args[0]}"

    status = (await client.post("/tools/task_status", json={"session": session})).json()
    assert "still working on: Find tomorrow's Delhi to Agra trains" in status["tasks"][0]


async def test_do_task_later_and_reminders_become_routines(client):
    session = await _new_user_session(client)
    later = (
        await client.post(
            "/tools/do_task",
            json={
                "session": session,
                "goal": "Mandi rates for bananas",
                "run_at": "2026-10-21 07:00",
                "repeat": "daily",
            },
        )
    ).json()
    assert later["status"] == "scheduled"
    reminder = (
        await client.post(
            "/tools/set_reminder",
            json={
                "session": session,
                "message": "दवाई लेनी है",
                "remind_at": "2026-10-20 21:00",
                "repeat": "none",
            },
        )
    ).json()
    assert reminder["status"] == "ok"
    bad = (
        await client.post(
            "/tools/set_reminder",
            json={"session": session, "message": "x", "remind_at": "kal subah", "repeat": "none"},
        )
    ).json()
    assert bad["status"] == "invalid_arguments"

    async with session_scope() as db:
        rows = {r.kind: r for r in await db.scalars(select(Routine))}
    assert rows[RoutineKind.TASK].cron == "0 7 * * *"
    assert rows[RoutineKind.REMINDER].cron is None
    listing = (await client.post("/tools/list_schedule", json={"session": session})).json()
    assert len(listing["upcoming"]) == 2


async def test_sandbox_result_is_authenticated_and_reported(client, fake_arq):
    session = await _new_user_session(client)
    await client.post(
        "/tools/do_task",
        json={"session": session, "goal": "Weather in Delhi", "run_at": "", "repeat": "none"},
    )
    async with session_scope() as db:
        task = await db.scalar(select(Task))
        user = await db.scalar(select(User))
    url = f"/sandbox/tasks/{task.id}/result"
    body = {"ok": True, "summary": "दिल्ली में कल धूप रहेगी।", "details": "32C, sunny", "cost_usd": 0.12}

    forged = await client.post(url, json=body, headers={"Authorization": "Bearer nope"})
    assert forged.status_code == 401

    ok = await client.post(
        url, json=body, headers={"Authorization": f"Bearer {sandbox_token(user.id)}"}
    )
    assert ok.json() == {"status": "ok"}
    assert fake_arq.jobs[-1][0] == "report_task"
    async with session_scope() as db:
        task = await db.get(Task, task.id)
    assert task.status is TaskStatus.DONE and task.summary.startswith("दिल्ली")


async def test_unheard_results_are_spoken_in_the_next_greeting(client):
    session = await _new_user_session(client)
    await client.post(
        "/tools/do_task",
        json={"session": session, "goal": "Weather in Delhi", "run_at": "", "repeat": "none"},
    )
    async with session_scope() as db:
        task = await db.scalar(select(Task))
        task.status, task.summary = TaskStatus.DONE, "कल धूप रहेगी।"

    first = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()
    assert "कल धूप रहेगी।" in first["greeting"]
    again = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()
    assert "कल धूप रहेगी।" not in again["greeting"]


async def _start_held_task(client, session) -> dict:
    return (
        await client.post(
            "/tools/do_task",
            json={
                "session": session,
                "goal": "Gold rate in Delhi today",
                "run_at": "",
                "repeat": "none",
                "wait": "yes",
            },
        )
    ).json()


async def test_wait_for_task_returns_result_and_suppresses_callback(client, fake_arq):
    session = await _new_user_session(client)
    started = await _start_held_task(client, session)
    assert "wait_for_task" in started["hint"]

    async with session_scope() as db:
        task = await db.scalar(select(Task))
        user = await db.scalar(select(User))
    assert task.caller_waiting
    await client.post(
        f"/sandbox/tasks/{task.id}/result",
        json={"ok": True, "summary": "आज सोना ₹7,900 प्रति ग्राम है।", "details": "24k"},
        headers={"Authorization": f"Bearer {sandbox_token(user.id)}"},
    )
    assert fake_arq.options[f"report:{task.id}"]["_defer_by"] > 0

    result = (
        await client.post(
            "/tools/wait_for_task", json={"session": session, "task": started["task"]}
        )
    ).json()
    assert result["status"] == "done" and result["summary"].startswith("आज सोना")
    async with session_scope() as db:
        assert (await db.get(Task, task.id)).reported_at is not None


async def test_wait_for_task_times_out_with_still_working(client, monkeypatch):
    from saarthi.config import get_settings

    monkeypatch.setattr(get_settings(), "task_wait_seconds", 0.2)
    session = await _new_user_session(client)
    started = await _start_held_task(client, session)
    result = (
        await client.post("/tools/wait_for_task", json={"session": session, "task": ""})
    ).json()
    assert result["status"] == "still_working" and "call wait_for_task again" in result["hint"]
    assert started["task"]


async def test_returning_caller_is_greeted_in_their_language(client):
    session = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()[
        "session"
    ]
    await client.post(
        "/tools/onboard_user",
        json={
            "session": session,
            "caller_name": "Shreyas",
            "caller_work": "engineer",
            "caller_language": "en",
            "consent": "yes",
        },
    )
    context = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()
    assert context["greeting"] == "Hi Shreyas! What can I do for you?"
    assert context["language"] == "en"
