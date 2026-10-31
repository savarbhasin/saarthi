import sys
import uuid
from pathlib import Path

import httpx
from sqlalchemy import select

from saarthi.config import get_settings
from saarthi.db.models import Call, CallDirection, McpServer, User, UserSkill
from saarthi.db.session import session_scope
from saarthi.domain import customize, login
from saarthi.memory import profile_cache, store

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sandbox"))

from agent_server import customize as sandbox_customize  # noqa: E402

PHONE = "+919876543210"


async def _onboard(client, phone: str = PHONE) -> None:
    session = (await client.get("/bolna/lookup", params={"contact_number": phone})).json()[
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


def _browser(client) -> httpx.AsyncClient:
    # The web app has no Bolna token; it is a separate client sharing the same app.
    return httpx.AsyncClient(transport=client._transport, base_url="http://test/api/web")


async def _signed_in(client, fake_arq, phone: str = PHONE) -> httpx.AsyncClient:
    await _onboard(client, phone)
    web = _browser(client)
    sent = await web.post("/login", json={"phone": phone})
    assert sent.json() == {"phone": phone}  # no code in the response outside dev mode
    name, args, _ = fake_arq.jobs[-1]
    assert name == "send_login_code"
    signed_in = await web.post("/login/verify", json={"phone": phone, "code": args[2]})
    assert signed_in.json() == {"ok": True}
    return web


async def test_api_needs_sign_in(client):
    web = _browser(client)
    assert (await web.get("/skills")).status_code == 401
    web.cookies.set("saarthi_web", "abc.123.def")
    assert (await web.get("/me")).status_code == 401


async def test_only_known_callers_get_a_code(client, fake_arq):
    response = await _browser(client).post("/login", json={"phone": "98111 22233"})
    assert response.status_code == 422 and response.json()["field"] == "phone"
    assert fake_arq.jobs == []


async def test_wrong_codes_are_refused_and_codes_are_single_use(client, fake_arq):
    await _onboard(client)
    web = _browser(client)
    await web.post("/login", json={"phone": PHONE})
    code = fake_arq.jobs[-1][1][2]
    wrong = "000000" if code != "000000" else "111111"
    refused = await web.post("/login/verify", json={"phone": PHONE, "code": wrong})
    assert refused.status_code == 422 and refused.json()["field"] == "code"
    assert (await web.post("/login/verify", json={"phone": PHONE, "code": code})).is_success
    again = await web.post("/login/verify", json={"phone": PHONE, "code": code})
    assert again.status_code == 422


async def test_profile_and_instructions_reach_the_voice_agent(client, fake_arq):
    web = await _signed_in(client, fake_arq)
    form = {
        "name": "रमेश",
        "language": "en",
        "pack": "kirana",
        "occupation": "kirana store",
        "custom_instructions": "My UPI ID is ramesh@okaxis. Always quote Azadpur mandi prices.",
    }
    assert (await web.put("/me", json=form)).json() == {"ok": True}
    unnamed = await web.put("/me", json=form | {"name": " "})
    assert unnamed.status_code == 422 and unnamed.json()["field"] == "name"
    me = (await web.get("/me")).json()
    assert me["pack"] == "kirana" and me["options"]["packs"]["kirana"] == "Kirana store"
    assert "upi_id" not in me

    context = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()
    assert "ramesh@okaxis" in context["custom_instructions"]
    assert context["language"] == "en"
    assert "kirana" in context["pack_prompt"]


async def test_home_shows_activity_memory_and_examples(client, fake_arq):
    web = await _signed_in(client, fake_arq)
    async with session_scope() as db:
        user = await db.scalar(select(User).where(User.phone == PHONE))
        profile = "- Sells mangoes at Azadpur\n- [2026-10-19] Daughter is Priya"
        await profile_cache.put(db, user.id, profile)
        db.add(
            Call(
                bolna_execution_id="exec-home",
                user_id=user.id,
                direction=CallDirection.INBOUND,
                status="completed",
                duration_seconds=125,
            )
        )
    home = (await web.get("/home")).json()
    assert home["pack"] == "Fruit & vegetable seller"
    # Without Supermemory it falls back to the cached profile, which has no ids to delete by.
    assert (await web.get("/memory")).json() == [
        {"id": None, "text": "Sells mangoes at Azadpur"},
        {"id": None, "text": "Daughter is Priya"},
    ]
    assert home["stats"]["minutes_talked"] == 2 and home["stats"]["calls_this_week"] == 1
    assert home["calls"][0] == home["calls"][0] | {"inbound": True, "seconds": 125}


async def test_memory_can_be_added_and_forgotten(client, fake_arq, monkeypatch):
    web = await _signed_in(client, fake_arq)
    facts = [("m1", "Sells mangoes at Azadpur"), ("m2", "[2026-10-19] SpaceX shares for kids")]
    forgotten = []

    async def fake_facts(user_id):
        return [f for f in facts if f[0] not in forgotten]

    async def fake_forget(user_id, ids):
        forgotten.extend(ids)
        return len(ids)

    async def fake_text(user_id):
        return store.as_text(await fake_facts(user_id))

    monkeypatch.setattr(get_settings(), "supermemory_api_key", "k")
    monkeypatch.setattr(store, "facts", fake_facts)
    monkeypatch.setattr(store, "forget_ids", fake_forget)
    monkeypatch.setattr(store, "profile_text", fake_text)

    remembered = []

    async def fake_remember(user_id, fact):
        remembered.append(fact)

    monkeypatch.setattr(store, "remember", fake_remember)
    assert (await web.post("/memory", json={"text": " Daughter is Priya "})).json() == {"ok": True}
    assert remembered == ["Daughter is Priya"]
    assert (await web.post("/memory", json={"text": " "})).status_code == 422

    memory = (await web.get("/memory")).json()
    assert memory[1] == {"id": "m2", "text": "SpaceX shares for kids"}
    assert (await web.delete("/memory/m2")).json() == {"ok": True}
    assert [m["id"] for m in (await web.get("/memory")).json()] == ["m1"]
    # The voice agent's cached profile no longer has it either.
    context = (await client.get("/bolna/lookup", params={"contact_number": PHONE})).json()
    assert "SpaceX" not in context["profile"]


async def test_guide_shows_what_everyone_gets_and_what_the_profile_adds(client, fake_arq):
    web = await _signed_in(client, fake_arq)
    guide = (await web.get("/guide")).json()
    assert guide["pack_label"] == "Fruit & vegetable seller"
    assert "Calls people for you" in [a["title"] for a in guide["everyone"]]
    assert "Keeps your khata" in [a["title"] for a in guide["profile"]]
    assert all(a["examples"] for a in guide["everyone"] + guide["profile"])


async def test_skills_are_saved_listed_and_scoped_to_their_owner(client, fake_arq):
    web = await _signed_in(client, fake_arq)
    skill = {
        "name": "Weekly Report",
        "description": "When they ask for the weekly sales report",
        "instructions": "1. Read ~/files/khata.csv\n2. Total the week",
    }
    saved = (await web.post("/skills", json=skill)).json()
    assert saved["name"] == "weekly-report" and saved["enabled"]
    invalid = await web.post("/skills", json=skill | {"name": "no/slashes"})
    assert invalid.status_code == 422 and "lowercase letters" in invalid.json()["message"]
    assert [s["name"] for s in (await web.get("/skills")).json()] == ["weekly-report"]

    async with session_scope() as db:
        row = await db.scalar(select(UserSkill))
        payload = customize.skills_payload(await customize.skills(db, row.user_id))
    assert payload == [
        {
            "name": "weekly-report",
            "description": "When they ask for the weekly sales report",
            "instructions": "1. Read ~/files/khata.csv\n2. Total the week",
        }
    ]

    other = await _signed_in(client, fake_arq, phone="+919822233344")
    assert (await other.delete(f"/skills/{row.id}")).status_code == 404
    async with session_scope() as db:
        assert await db.get(UserSkill, row.id) is not None

    await web.patch(f"/skills/{row.id}", json={"enabled": False})
    async with session_scope() as db:
        assert customize.skills_payload(await customize.skills(db, row.user_id)) == []


async def test_connectors_become_agent_sdk_mcp_servers(client, fake_arq):
    web = await _signed_in(client, fake_arq)
    await web.post(
        "/connectors",
        json={
            "name": "memory",
            "transport": "stdio",
            "command": "npx",
            "args": "-y @modelcontextprotocol/server-memory",
            "env": "MEMORY_FILE=/home/saarthi/files/memory.json",
        },
    )
    await web.post(
        "/connectors",
        json={
            "name": "my-crm",
            "transport": "http",
            "url": "https://crm.example.com/mcp",
            "headers": "Authorization: Bearer s3cret",
        },
    )
    taken = await web.post(
        "/connectors", json={"name": "browser", "transport": "http", "url": "https://x.y"}
    )
    assert "taken by a built-in tool" in taken.json()["message"]
    listed = (await web.get("/connectors")).text
    assert "Authorization" in listed and "s3cret" not in listed

    async with session_scope() as db:
        user_id = (await db.scalar(select(McpServer))).user_id
        servers = customize.servers_payload(await customize.servers(db, user_id))
    assert servers == {
        "memory": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
            "env": {"MEMORY_FILE": "/home/saarthi/files/memory.json"},
        },
        "my_crm": {
            "type": "http",
            "url": "https://crm.example.com/mcp",
            "headers": {"Authorization": "Bearer s3cret"},
        },
    }


async def test_code_calls_stay_out_of_memory(client, fake_arq):
    await _onboard(client)
    await _browser(client).post("/login", json={"phone": PHONE})
    login_id = fake_arq.jobs[-1][1][0]
    async with session_scope() as db:
        await login.record_call(db, uuid.UUID(login_id), "exec-code")
    event = {
        "id": "exec-code",
        "status": "completed",
        "transcript": "assistant: आपका लॉगिन कोड है 4 7 2, 9 1 3",
        "telephony_data": {"to_number": PHONE, "call_type": "outbound"},
    }
    await client.post("/webhooks/bolna", json=event)
    assert not [job for job in fake_arq.jobs if job[0] == "ingest_call"]
    async with session_scope() as db:
        call = await db.scalar(select(Call).where(Call.bolna_execution_id == "exec-code"))
        user = await db.scalar(select(User))
    assert call.transcript is None and call.user_id is None and user is not None


def test_sandbox_installs_and_removes_managed_skills(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox_customize, "SKILLS_DIR", tmp_path)
    (tmp_path / "workers-own").mkdir()
    sandbox_customize.install_skills(
        [{"name": "weekly-report", "description": 'Use: "weekly"\nreport', "instructions": "1."}]
    )
    text = (tmp_path / "weekly-report" / "SKILL.md").read_text()
    assert text.startswith('---\nname: weekly-report\ndescription: "Use: \\"weekly\\"\\nreport"')

    sandbox_customize.install_skills([])
    assert not (tmp_path / "weekly-report").exists()
    assert (tmp_path / "workers-own").exists()
    assert sandbox_customize.user_servers({"browser": {}, "crm": {}}) == {"crm": {}}


async def test_spa_routes_fall_back_to_the_app(client, monkeypatch, tmp_path):
    from saarthi.web import spa

    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<div id=root></div>")
    (tmp_path / "landing.html").write_text("<h1>Saarthi</h1>")
    (tmp_path / "deck.html").write_text("<h1>Deck</h1>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    monkeypatch.setattr(spa, "DIST", tmp_path)
    assert (await client.get("/")).text == "<h1>Saarthi</h1>"
    assert (await client.get("/deck")).text == "<h1>Deck</h1>"
    assert (await client.get("/app/skills")).text == "<div id=root></div>"
    assert (await client.get("/app/assets/app.js")).text == "console.log(1)"
    # An encoded ../ reaches the handler intact and must not escape the build folder.
    escape = await client.get("/app/..%2F..%2F..%2Fetc%2Fhosts")
    assert escape.text == "<div id=root></div>"
