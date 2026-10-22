import json
import time
from dataclasses import dataclass

import httpx

from saarthi.config import Settings

REASONING_FIELDS = ("reasoning", "reasoning_content", "reasoning_details")

PROBE_MESSAGES = [
    {"role": "system", "content": "You are a phone assistant. Reply in one short Hindi sentence."},
    {"role": "user", "content": "शर्मा जी ने दो सौ उधार लिए, लिख लो।"},
]


@dataclass(frozen=True)
class LlmCheck:
    first_token_seconds: float | None
    total_seconds: float
    reply: str
    reasoning_chars: int


async def probe(settings: Settings) -> LlmCheck:
    """Stream one turn straight from the endpoint, with the same params Bolna will send.

    We measure time to the first *spoken* token: reasoning deltas (`reasoning`,
    `reasoning_content` or `reasoning_details`, depending on the gateway) are silence for the
    caller, so they count as latency, not output.
    """
    body = {
        "model": settings.llm_model,
        "messages": PROBE_MESSAGES,
        "max_tokens": settings.llm_max_tokens,
        "temperature": settings.llm_temperature,
        "stream": True,
        **settings.llm_extra_body,
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"

    start = time.perf_counter()
    first_token: float | None = None
    reply, reasoning = [], 0
    async with (
        httpx.AsyncClient(timeout=60) as http,
        http.stream("POST", url, json=body, headers=headers) as response,
    ):
        if response.is_error:
            await response.aread()
            raise RuntimeError(f"LLM endpoint {response.status_code}: {response.text}")
        async for line in response.aiter_lines():
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            choices = json.loads(line[6:]).get("choices") or [{}]
            delta = choices[0].get("delta", {})
            reasoning += sum(len(str(delta.get(k) or "")) for k in REASONING_FIELDS)
            if content := delta.get("content"):
                first_token = first_token or time.perf_counter() - start
                reply.append(content)
    return LlmCheck(first_token, time.perf_counter() - start, "".join(reply), reasoning)
