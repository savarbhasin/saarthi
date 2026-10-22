import logging
import uuid
from datetime import UTC, datetime

from arq import Retry

from saarthi.config import get_settings
from saarthi.db.models import Call
from saarthi.db.session import session_scope
from saarthi.memory import profile_cache, store

log = logging.getLogger(__name__)

MAX_TRIES = 4


async def ingest_call(ctx: dict, call_id: str) -> None:
    if not get_settings().supermemory_api_key:
        log.warning("SUPERMEMORY_API_KEY not set; skipping ingest of call %s", call_id)
        return

    async with session_scope() as session:
        call = await session.get(Call, uuid.UUID(call_id))
        if call is None or call.user_id is None or call.ingested_at or not call.transcript:
            return
        user_id, execution_id, transcript = call.user_id, call.bolna_execution_id, call.transcript

    try:
        await store.add_transcript(user_id, execution_id, transcript)
        profile = await store.profile_text(user_id)
    except Exception:
        # Supermemory occasionally returns a spurious 401/5xx; the same request succeeds
        # seconds later, so back off and retry rather than lose the call's memory.
        if ctx.get("job_try", 1) >= MAX_TRIES:
            raise
        log.warning("memory ingest of %s failed, retrying", execution_id, exc_info=True)
        raise Retry(defer=15 * ctx.get("job_try", 1)) from None

    async with session_scope() as session:
        await profile_cache.put(session, user_id, profile)
        call = await session.get(Call, uuid.UUID(call_id))
        call.ingested_at = datetime.now(UTC)
    log.info("ingested call %s for user %s", execution_id, user_id)
