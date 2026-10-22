import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://saarthi:saarthi@localhost:5433/saarthi_test"
)
os.environ["BOLNA_TOOL_SECRET"] = "test-secret"
os.environ["SUPERMEMORY_API_KEY"] = ""

import asyncpg  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from saarthi.api.app import create_app  # noqa: E402
from saarthi.db.models import Base  # noqa: E402
from saarthi.db.session import engine  # noqa: E402

AUTH = {"Authorization": "Bearer test-secret"}


class FakeArq:
    def __init__(self):
        self.jobs: list[tuple] = []
        self.options: dict[str | None, dict] = {}

    async def enqueue_job(self, name, *args, _job_id=None, **kwargs):
        self.jobs.append((name, args, _job_id))
        self.options[_job_id] = kwargs


async def _ensure_database(url: str) -> None:
    dsn = url.replace("+asyncpg", "")
    admin_dsn, db_name = dsn.rsplit("/", 1)
    conn = await asyncpg.connect(f"{admin_dsn}/postgres")
    try:
        if not await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name):
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
async def database():
    await _ensure_database(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        # A full reset: tables removed from the models would otherwise block drop_all.
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables():
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture
def fake_arq() -> FakeArq:
    return FakeArq()


@pytest.fixture
async def client(fake_arq):
    app = create_app()
    app.state.arq = fake_arq
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", headers=AUTH) as c:
        yield c
