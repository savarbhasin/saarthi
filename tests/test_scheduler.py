from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from saarthi.db.models import Routine, RoutineKind, User
from saarthi.db.session import session_scope
from saarthi.domain.routines import next_cron_run
from saarthi.scheduler import tick


def test_cron_is_evaluated_in_ist():
    # 06:00 UTC is 11:30 IST, so the next "7 am daily" is tomorrow 07:00 IST = 01:30 UTC.
    after = datetime(2026, 10, 20, 6, 0, tzinfo=UTC)
    assert next_cron_run("0 7 * * *", after) == datetime(2026, 10, 21, 1, 30, tzinfo=UTC)


async def test_tick_fires_due_routines_once(fake_arq):
    now = datetime(2026, 10, 20, 6, 0, tzinfo=UTC)
    async with session_scope() as session:
        user = User(phone="+919876543210", name="Ramesh")
        session.add(user)
        await session.flush()
        session.add_all(
            [
                Routine(
                    user_id=user.id,
                    kind=RoutineKind.REMINDER,
                    run_at=now,
                    next_run_at=now - timedelta(minutes=1),
                ),
                Routine(
                    user_id=user.id,
                    kind=RoutineKind.BRIEF,
                    cron="0 7 * * *",
                    next_run_at=now - timedelta(seconds=5),
                ),
                Routine(
                    user_id=user.id,
                    kind=RoutineKind.BRIEF,
                    cron="0 20 * * *",
                    next_run_at=now + timedelta(hours=1),
                ),
            ]
        )

    assert await tick(fake_arq, now) == 2
    assert await tick(fake_arq, now) == 0
    assert len(fake_arq.jobs) == 2

    async with session_scope() as session:
        fired = list(await session.scalars(select(Routine).where(Routine.last_run_at.is_not(None))))
    one_off = next(r for r in fired if r.kind is RoutineKind.REMINDER)
    daily = next(r for r in fired if r.kind is RoutineKind.BRIEF)
    assert one_off.active is False and one_off.next_run_at is None
    assert daily.next_run_at == datetime(2026, 10, 21, 1, 30, tzinfo=UTC)
