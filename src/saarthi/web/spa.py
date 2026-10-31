from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

# The Vite build of frontend/; `npm run build` writes it, the Docker image copies it in.
DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"

router = APIRouter()


def _built() -> None:
    if not DIST.is_dir():
        raise HTTPException(503, "Web app not built: run `npm run build` in frontend/")


@router.get("/", include_in_schema=False)
async def landing() -> FileResponse:
    _built()
    return FileResponse(DIST / "landing.html")


@router.get("/deck", include_in_schema=False)
async def deck() -> FileResponse:
    _built()
    return FileResponse(DIST / "deck.html")


@router.get("/app")
@router.get("/app/{path:path}")
async def spa(path: str = "") -> FileResponse:
    _built()
    asset = (DIST / path).resolve()
    if path and asset.is_file() and asset.is_relative_to(DIST):
        return FileResponse(asset)
    # Everything else is a client-side route.
    return FileResponse(DIST / "index.html")
