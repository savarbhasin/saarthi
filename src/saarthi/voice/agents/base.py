from dataclasses import dataclass, field
from pathlib import Path

from saarthi.config import Settings
from saarthi.voice.tools import ToolSpec, to_bolna_api_tools

PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass(frozen=True)
class AgentSpec:
    name: str
    prompt_file: str
    welcome_message: str
    tools: list[ToolSpec] = field(default_factory=list)
    inbound: bool = False
    stt_keywords: list[str] = field(default_factory=list)
    stt_context: str = ""
    hangup_after_silence: int = 15
    max_call_seconds: int = 600
    still_there_message: str = "हैलो? क्या आप मुझे सुन पा रहे हैं?"
    hangup_message: str = "ठीक है जी, नमस्ते!"
    web_search: bool = False
    # Call variables this agent is given; tool params must not reuse them (Bolna overwrites).
    context_keys: frozenset[str] = frozenset()

    def prompt(self) -> str:
        return (PROMPTS_DIR / self.prompt_file).read_text()


def llm_config(settings: Settings) -> dict:
    config = {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "max_tokens": settings.llm_max_tokens,
        "temperature": settings.llm_temperature,
    }
    if settings.llm_provider == "custom":
        config |= {"base_url": settings.llm_base_url.rstrip("/"), "family": settings.llm_family}
        if settings.llm_extra_body:
            config["extra_body"] = settings.llm_extra_body
    return config


def web_search_config(settings: Settings) -> dict:
    config = {
        "enabled": True,
        "provider": settings.web_search_provider,
        "max_results": settings.web_search_max_results,
        "description": (
            "Search the web for live facts the caller wants right now: today's prices and "
            "rates, news, scores, weather, opening hours, train or flight timings."
        ),
        "pre_call_message": "एक सेकंड, देखता हूँ।",
    }
    # Bolna supplies its own key for OpenAI search; the other providers need ours.
    if settings.web_search_provider != "openai":
        config["api_key"] = settings.web_search_api_key
    return config


def build_payload(spec: AgentSpec, settings: Settings) -> dict:
    base_url = settings.public_base_url.rstrip("/")
    secret = settings.bolna_tool_secret
    telephony = {"provider": settings.telephony_provider, "format": "wav"}

    agent_config: dict = {
        "agent_name": spec.name,
        "agent_welcome_message": spec.welcome_message,
        "webhook_url": f"{base_url}/webhooks/bolna?token={secret}",
        "agent_type": "other",
        "tasks": [
            {
                "task_type": "conversation",
                "tools_config": {
                    "llm_agent": {
                        "agent_type": "simple_llm_agent",
                        "agent_flow_type": "streaming",
                        "llm_config": llm_config(settings),
                    },
                    "synthesizer": {
                        "provider": "sarvam",
                        "provider_config": {
                            "voice": settings.tts_voice,
                            "voice_id": settings.tts_voice_id,
                            "model": settings.tts_model,
                            "language": settings.default_language,
                            "speed": 1.0,
                        },
                        "stream": True,
                        "buffer_size": 150,
                    },
                    "transcriber": {
                        "provider": "sarvam",
                        "model": settings.stt_model,
                        "language": settings.default_language,
                        "stream": True,
                        "endpointing": 500,
                        "keywords": ", ".join(spec.stt_keywords[:50]),
                        "context": spec.stt_context,
                    },
                    "input": telephony,
                    "output": telephony,
                    "api_tools": (
                        to_bolna_api_tools(spec.tools, base_url, secret) if spec.tools else None
                    ),
                    **({"web_search": web_search_config(settings)} if spec.web_search else {}),
                },
                "toolchain": {
                    "execution": "parallel",
                    "pipelines": [["transcriber", "llm", "synthesizer"]],
                },
                "task_config": {
                    "hangup_after_silence": spec.hangup_after_silence,
                    "call_terminate": spec.max_call_seconds,
                    "check_if_user_online": True,
                    "check_user_online_message": spec.still_there_message,
                    "call_hangup_message": spec.hangup_message,
                },
            }
        ],
    }
    if spec.inbound:
        agent_config["ingest_source_config"] = {
            "source_type": "api",
            "source_url": f"{base_url}/bolna/lookup",
            "source_auth_token": secret,
        }

    return {
        "agent_config": agent_config,
        "agent_prompts": {"task_1": {"system_prompt": spec.prompt()}},
    }
