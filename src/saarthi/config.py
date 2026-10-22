from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://saarthi:saarthi@localhost:5433/saarthi"
    redis_url: str = "redis://localhost:6380/0"

    # Public HTTPS URL Bolna uses to reach us (cloudflared tunnel in dev).
    public_base_url: str = "http://localhost:8000"

    bolna_api_key: str = ""
    bolna_base_url: str = "https://api.bolna.ai"
    # Shared secret Bolna sends as a bearer token on lookup and tool calls.
    bolna_tool_secret: str = "change-me"
    bolna_phone_number_id: str = ""
    telephony_provider: Literal["plivo", "exotel", "twilio"] = "plivo"

    # OpenRouter is wired through Bolna's "custom" (OpenAI-compatible) LLM provider.
    llm_provider: str = "custom"
    llm_model: str = "deepseek/deepseek-v4.1-flash"
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_family: str = "deepseek"
    llm_api_key: str = ""
    # DeepSeek V4 reasons by default, which adds dead air before every spoken reply. Upstream
    # providers differ a lot in time to first token for streamed tool calls (0.9s for Together
    # vs 2-3s for others, measured Oct 19 from India), so pin the fastest and keep fallbacks.
    llm_extra_body: dict = {
        "reasoning": {"effort": "none"},
        "provider": {"order": ["together", "crusoe/fp8"], "allow_fallbacks": True},
    }
    llm_max_tokens: int = 400
    llm_temperature: float = 0.3

    tts_model: str = "bulbul:v4-flash"
    tts_voice: str = "Aparna (Customer)"
    tts_voice_id: str = "aparna_hi_customer"
    stt_model: str = "saaras:v4"
    default_language: str = "hi"

    supermemory_api_key: str = ""

    # Bolna's built-in in-call web search: openai (no key needed), exa, firecrawl or parallel.
    web_search_provider: Literal["openai", "exa", "firecrawl", "parallel"] = "openai"
    web_search_api_key: str = Field(
        "", validation_alias=AliasChoices("web_search_api_key", "exa_api_key")
    )
    web_search_max_results: int = 3

    # Per-user sandbox computers (see saarthi.sandbox). The worker agent inside is the Claude
    # Agent SDK pointed at OpenRouter's Anthropic-compatible endpoint, driving any OpenRouter
    # model (DeepSeek by default).
    openrouter_api_key: str = ""
    sandbox_image: str = "saarthi-sandbox:latest"
    sandbox_network: str = "saarthi-net"
    # How sandboxes reach the API to report results (service name on sandbox_network).
    sandbox_api_url: str = "http://api:8000"
    sandbox_memory: str = "2g"
    sandbox_cpus: float = 1.0
    worker_model: str = "deepseek/deepseek-v4.1-flash"
    worker_fast_model: str = "deepseek/deepseek-v4.1-flash"
    worker_max_budget_usd: float = 1.5
    # Hold-on pattern: each wait_for_task call blocks at most this long (must stay under
    # Bolna's custom-function timeout; its own web search uses 8s), and a held task's
    # callback is delayed this long so it only fires if the caller hung up before hearing it.
    task_wait_seconds: float = 6.0
    held_callback_delay_seconds: int = 90

    default_region: str = "IN"
    call_session_ttl_minutes: int = 120
    scheduler_tick_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
