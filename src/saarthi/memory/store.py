import uuid
from functools import lru_cache

from supermemory import AsyncSupermemory

from saarthi.config import get_settings


@lru_cache
def _client() -> AsyncSupermemory:
    return AsyncSupermemory(api_key=get_settings().supermemory_api_key)


def _namespace(user_id: uuid.UUID) -> str:
    return f"user_{user_id.hex}"


async def add_transcript(user_id: uuid.UUID, execution_id: str, transcript: str) -> None:
    await _client().add(
        _namespace(user_id),
        content=transcript,
        id=f"call_{execution_id}",
        metadata={"source": "call"},
    )


async def remember(user_id: uuid.UUID, fact: str) -> None:
    await _client().add(_namespace(user_id), content=fact, metadata={"source": "explicit"})


async def search(user_id: uuid.UUID, query: str, limit: int = 5) -> list[str]:
    response = await _client().search(_namespace(user_id), query=query, limit=limit)
    return [r.memory or r.chunk for r in response.results if r.memory or r.chunk]


async def profile_text(user_id: uuid.UUID) -> str:
    profile = (await _client().profile(_namespace(user_id))).profile
    lines = [f"- {fact.memory}" for fact in [*profile.static, *profile.dynamic]]
    return "\n".join(lines)


async def forget(user_id: uuid.UUID, what: str) -> int:
    result = await _client().memories.forget_matching(
        _namespace(user_id), query=what, dry_run=False
    )
    return result.count
