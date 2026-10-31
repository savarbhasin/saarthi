import logging

from arq.connections import RedisSettings

from saarthi.config import get_settings
from saarthi.jobs.ingest import ingest_call
from saarthi.jobs.outreach import place_outreach_call, report_outreach
from saarthi.jobs.routines import run_routine
from saarthi.jobs.tasks import report_task, run_task
from saarthi.jobs.web import send_login_code


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


async def _startup(ctx: dict) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


class WorkerSettings:
    functions = [
        ingest_call,
        run_routine,
        run_task,
        report_task,
        place_outreach_call,
        report_outreach,
        send_login_code,
    ]
    on_startup = _startup
    redis_settings = redis_settings()
    max_jobs = 20
    job_timeout = 600
