import asyncio
import logging
from datetime import UTC, datetime

from arq import ArqRedis, create_pool
from sqlalchemy import select

from saarthi.config import get_settings
from saarthi.db.models import Routine
from saarthi.db.session import session_scope
from saarthi.domain.routines import next_cron_run
from saarthi.jobs.worker import redis_settings

log = logging.getLogger(__name__)

BATCH_SIZE = 100


async def tick(arq: ArqRedis, now: datetime | None = None) -> int:
    """Enqueue every due routine once and advance its schedule.

    Rows are claimed with FOR UPDATE SKIP LOCKED so several schedulers can run without
    double-firing. The arq job id is derived from (routine, scheduled time), so if the
    enqueue succeeds but the commit fails, the retry on the next tick is deduplicated by arq
    instead of placing the same call twice.
    """
    now = now or datetime.now(UTC)
    async with session_scope() as session:
        due = await session.scalars(
            select(Routine)
            .where(Routine.active.is_(True), Routine.next_run_at <= now)
            .order_by(Routine.next_run_at)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        fired = 0
        for routine in due:
            scheduled_for = routine.next_run_at
            await arq.enqueue_job(
                "run_routine",
                str(routine.id),
                _job_id=f"routine:{routine.id}:{scheduled_for.isoformat()}",
            )
            routine.last_run_at = now
            if routine.cron:
                routine.next_run_at = next_cron_run(routine.cron, now)
            else:
                routine.active = False
                routine.next_run_at = None
            fired += 1
    return fired


async def run_forever() -> None:
    interval = get_settings().scheduler_tick_seconds
    arq = await create_pool(redis_settings())
    log.info("scheduler started, tick every %ss", interval)
    try:
        while True:
            try:
                fired = await tick(arq)
                if fired:
                    log.info("enqueued %d routines", fired)
            except Exception:
                log.exception("scheduler tick failed")
            await asyncio.sleep(interval)
    finally:
        await arq.aclose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run_forever())


if __name__ == "__main__":
    main()
