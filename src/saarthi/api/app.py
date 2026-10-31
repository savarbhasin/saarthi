import logging
from contextlib import asynccontextmanager

from arq import create_pool
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from saarthi.api.routes import health, lookup, sandbox, tools, webhooks
from saarthi.jobs.worker import redis_settings
from saarthi.web import auth, spa
from saarthi.web import routes as web


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
    for module in (health, lookup, tools, webhooks, sandbox, web, spa):
        app.include_router(module.router)

    @app.exception_handler(auth.LoginRequired)
    async def _signed_out(request: Request, exc: auth.LoginRequired) -> JSONResponse:
        return JSONResponse({"detail": "sign in required"}, status_code=401)

    return app


app = create_app()
