import logging
from contextlib import asynccontextmanager

from arq import create_pool
from fastapi import FastAPI

from saarthi.api.routes import health, lookup, sandbox, tools, webhooks
from saarthi.jobs.worker import redis_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq = await create_pool(redis_settings())
    yield
    await app.state.arq.aclose()


def create_app() -> FastAPI:
    logging.getLogger("saarthi").setLevel(logging.INFO)
    if not logging.getLogger().handlers:
        logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(title="Saarthi", lifespan=lifespan)
    for module in (health, lookup, tools, webhooks, sandbox):
        app.include_router(module.router)
    return app


app = create_app()
