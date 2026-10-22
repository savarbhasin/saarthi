from saarthi.api.tools import REGISTRY as TOOL_HANDLERS
from saarthi.config import Settings
from saarthi.voice.agents import REGISTRY, build_payload
from saarthi.voice.context import CONTEXT_KEYS
from saarthi.voice.tools import DO_TASK, MAIN_TOOLS, to_bolna_api_tools


def test_tools_are_all_required_and_templated():
    api_tools = to_bolna_api_tools([DO_TASK], "https://saarthi.example/", "s3cret")
    tool = api_tools["tools"][0]
    assert tool["key"] == "custom_task"
    assert set(tool["parameters"]["required"]) == {
        "session",
        "goal",
        "run_at",
        "repeat",
        "wait",
        "follow_up",
    }
    params = api_tools["tools_params"]["do_task"]
    assert params["url"] == "https://saarthi.example/tools/do_task"
    assert params["param"]["goal"] == "%(goal)s"
    assert params["api_token"] == "s3cret"


def test_main_agent_payload():
    settings = Settings(public_base_url="https://saarthi.example", bolna_tool_secret="s3cret")
    payload = build_payload(REGISTRY["saarthi-main"], settings)
    config = payload["agent_config"]
    assert config["ingest_source_config"]["source_url"] == "https://saarthi.example/bolna/lookup"
    assert config["webhook_url"].endswith("/webhooks/bolna?token=s3cret")
    tools_config = config["tasks"][0]["tools_config"]
    assert tools_config["transcriber"]["provider"] == "sarvam"
    assert {t["name"] for t in tools_config["api_tools"]["tools"]} == {t.name for t in MAIN_TOOLS}
    assert "{{session}}" in payload["agent_prompts"]["task_1"]["system_prompt"]


def test_openrouter_custom_llm_config():
    settings = Settings(_env_file=None)
    llm = build_payload(REGISTRY["saarthi-main"], settings)["agent_config"]["tasks"][0][
        "tools_config"
    ]["llm_agent"]["llm_config"]
    assert llm == {
        "provider": "custom",
        "model": "deepseek/deepseek-v4.1-flash",
        "base_url": "https://openrouter.ai/api/v1",
        "family": "deepseek",
        "extra_body": {
            "reasoning": {"effort": "none"},
            "provider": {"order": ["together", "crusoe/fp8"], "allow_fallbacks": True},
        },
        "max_tokens": 400,
        "temperature": 0.3,
    }


def test_native_provider_has_no_custom_fields():
    settings = Settings(_env_file=None, llm_provider="anthropic", llm_model="claude-sonnet-5")
    llm = build_payload(REGISTRY["saarthi-main"], settings)["agent_config"]["tasks"][0][
        "tools_config"
    ]["llm_agent"]["llm_config"]
    assert "base_url" not in llm and "extra_body" not in llm


def test_tool_params_do_not_collide_with_call_context():
    # Bolna overwrites a tool param with the call variable of the same name (seen live: the
    # model said the caller's name but onboard_user received the empty context "name").
    assert REGISTRY["saarthi-main"].context_keys == CONTEXT_KEYS
    for agent in REGISTRY.values():
        assert "session" in agent.context_keys
        for tool in agent.tools:
            clashes = (set(tool.properties) & agent.context_keys) - {"session"}
            assert not clashes, f"{agent.name}.{tool.name} reuses context keys {clashes}"


def test_every_tool_has_a_hindi_filler():
    for tool in MAIN_TOOLS:
        assert tool.pre_call_message and not tool.pre_call_message.isascii()


def test_every_voice_tool_has_a_backend_handler():
    for agent in REGISTRY.values():
        assert {t.name for t in agent.tools} <= set(TOOL_HANDLERS), agent.name


def test_messenger_agent_is_outbound_only_with_one_tool():
    settings = Settings(public_base_url="https://saarthi.example", bolna_tool_secret="s3cret")
    config = build_payload(REGISTRY["saarthi-messenger"], settings)["agent_config"]
    assert "ingest_source_config" not in config
    tools = config["tasks"][0]["tools_config"]["api_tools"]["tools"]
    assert [t["name"] for t in tools] == ["record_outcome"]


def test_stt_keywords_fit_bolnas_limit():
    # build_payload sends only the first 50, so pack keywords past that would be dropped.
    assert len(REGISTRY["saarthi-main"].stt_keywords) <= 50


def test_main_agent_has_builtin_web_search():
    def web_search(**overrides):
        settings = Settings(_env_file=None, **overrides)
        payload = build_payload(REGISTRY["saarthi-main"], settings)
        return payload["agent_config"]["tasks"][0]["tools_config"]["web_search"]

    keyless = web_search(web_search_provider="openai")
    assert keyless["enabled"] and "api_key" not in keyless
    assert not keyless["pre_call_message"].isascii()
    assert web_search(web_search_provider="exa", web_search_api_key="k")["api_key"] == "k"
