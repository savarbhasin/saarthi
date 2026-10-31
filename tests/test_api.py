PHONE = "+919876543210"


async def _lookup(client, number=PHONE) -> dict:
    response = await client.get("/bolna/lookup", params={"contact_number": number})
    assert response.status_code == 200
    return response.json()


async def _onboarded_session(client, work: str = "फल बेचता हूँ") -> str:
    session = (await _lookup(client))["session"]
    result = await client.post(
        "/tools/onboard_user",
        json={
            "session": session,
            "caller_name": "रमेश",
            "caller_work": work,
            "caller_language": "hi",
            "consent": "yes",
        },
    )
    assert result.json()["status"] == "ok"
    return session


async def test_requires_bolna_secret(client):
    response = await client.get(
        "/bolna/lookup", params={"contact_number": PHONE}, headers={"Authorization": "nope"}
    )
    assert response.status_code == 401


async def test_unknown_caller_gets_new_context(client):
    context = await _lookup(client, "98765 43210")
    assert context["is_new"] == "yes"
    assert context["session"]
    assert all(isinstance(v, str) for v in context.values())


async def test_onboarding_then_lookup_recognises_caller(client):
    await _onboarded_session(client)
    context = await _lookup(client)
    assert context["is_new"] == "no"
    assert context["name"] == "रमेश"
    assert "रमेश" in context["greeting"]


async def test_tool_errors_are_spoken_not_raised(client):
    bad = await client.post("/tools/task_status", json={"session": "forged"})
    assert bad.status_code == 200
    assert bad.json()["status"] == "invalid_session"

    session = (await _lookup(client))["session"]
    not_yet = await client.post("/tools/task_status", json={"session": session})
    assert not_yet.json()["status"] == "not_onboarded"

    session = await _onboarded_session(client)
    missing = await client.post(
        "/tools/do_task",
        json={"session": session, "goal": "", "run_at": "", "repeat": "none", "wait": "no"},
    )
    body = missing.json()
    assert (body["status"], body["fields"]) == ("invalid_arguments", "goal")
    assert "Ask the caller" in body["hint"]


async def test_fruit_seller_gets_khata_instructions_for_both_agents(client):
    await _onboarded_session(client, work="फल बेचता हूँ")
    context = await _lookup(client)
    assert "do_task" in context["pack_prompt"] and "Khata" in context["pack_prompt"]

    from saarthi.packs import pack_for

    assert "~/files/khata.csv" in pack_for("phal_sabzi").worker_prompt


async def test_webhook_stores_call_and_enqueues_ingest(client, fake_arq):
    await _onboarded_session(client)
    event = {
        "id": "exec-1",
        "agent_id": "agent-1",
        "status": "in-progress",
        "telephony_data": {
            "from_number": PHONE,
            "to_number": "+918000000000",
            "call_type": "inbound",
        },
    }
    assert (await client.post("/webhooks/bolna", json=event)).status_code == 200
    assert fake_arq.jobs == []

    event |= {"status": "completed", "transcript": "user: Sharma ji ne 200 udhaar liye"}
    await client.post("/webhooks/bolna", json=event)
    name, args, job_id = fake_arq.jobs[0]
    assert (name, job_id) == ("ingest_call", "ingest:exec-1")
