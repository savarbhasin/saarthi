from fastapi import APIRouter
from sqlalchemy import text

from saarthi.api.deps import Db

router = APIRouter()


@router.get("/health")
async def health(db: Db) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}
