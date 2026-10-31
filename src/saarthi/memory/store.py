import uuid
from functools import lru_cache

from supermemory import AsyncSupermemory

from saarthi.config import get_settings
from saarthi.memory.transcript import for_memory


@lru_cache
def _client() -> AsyncSupermemory:
    return AsyncSupermemory(api_key=get_settings().supermemory_api_key)


def _namespace(user_id: uuid.UUID) -> str:
    return f"user_{user_id.hex}"


# Steers Supermemory's extraction so calls produce facts about the caller, not about the world.
CALL_CONTEXT = (
    "A phone call between a user and Saarthi, their AI assistant. Only remember facts about "
    "the user: who they are, their family and the people they deal with, their work, "
    "preferences, routines and plans. Do not remember general knowledge, news, prices, word "
    "meanings or anything Saarthi looked up, unless the user says it is about them."
)


async def add_transcript(user_id: uuid.UUID, execution_id: str, transcript: str) -> bool:
    content = for_memory(transcript)
    if not content:
        return False
    await _client().add(
        _namespace(user_id),
        content=content,
        id=f"call_{execution_id}",
        supporting_context=CALL_CONTEXT,
        metadata={"source": "call"},
    )
    return True


async def remember(user_id: uuid.UUID, fact: str) -> None:
    await _client().add(_namespace(user_id), content=fact, metadata={"source": "explicit"})


async def search(user_id: uuid.UUID, query: str, limit: int = 5) -> list[str]:
    response = await _client().search(_namespace(user_id), query=query, limit=limit)
    return [r.memory or r.chunk for r in response.results if r.memory or r.chunk]


async def facts(user_id: uuid.UUID) -> list[tuple[str, str]]:
    profile = (await _client().profile(_namespace(user_id))).profile
    return [(fact.id, fact.memory) for fact in [*profile.static, *profile.dynamic]]


def as_text(rows: list[tuple[str, str]]) -> str:
    return "\n".join(f"- {memory}" for _, memory in rows)


async def profile_text(user_id: uuid.UUID) -> str:
    return as_text(await facts(user_id))


async def forget_ids(user_id: uuid.UUID, ids: list[str]) -> int:
    return (await _client().memories.forget(_namespace(user_id), ids=ids)).count


async def forget(user_id: uuid.UUID, what: str) -> int:
    result = await _client().memories.forget_matching(
        _namespace(user_id), query=what, dry_run=False
    )
    return result.count
