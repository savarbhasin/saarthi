from fastapi import APIRouter, Query

from saarthi.api.deps import BolnaAuth, Db
from saarthi.voice.context import build_call_context

router = APIRouter(dependencies=[BolnaAuth])


@router.get("/bolna/lookup")
async def caller_lookup(
    db: Db,
    contact_number: str = Query(...),
    agent_id: str | None = None,
    execution_id: str | None = None,
) -> dict[str, str]:
    return await build_call_context(db, contact_number, execution_id=execution_id)
