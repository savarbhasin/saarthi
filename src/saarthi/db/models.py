import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    MetaData,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Fetch server defaults (created_at etc.) on INSERT; lazy refresh would fail under asyncio.
    __mapper_args__ = {"eager_defaults": True}


def _enum(cls: type[StrEnum]) -> Enum:
    return Enum(cls, native_enum=False, length=32, values_callable=lambda e: [m.value for m in e])


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


def _user_fk() -> Mapped[uuid.UUID]:
    return mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    DONE = "done"
    FAILED = "failed"


class QuestionStatus(StrEnum):
    OPEN = "open"
    ANSWERED = "answered"
    EXPIRED = "expired"


class RoutineKind(StrEnum):
    REMINDER = "reminder"
    BRIEF = "brief"
    TASK = "task"
    SKILL = "skill"


class ActionStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class OutreachStatus(StrEnum):
    QUEUED = "queued"
    CALLING = "calling"
    DONE = "done"
    NO_ANSWER = "no_answer"
    FAILED = "failed"


class CallDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _pk()
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str | None] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(8), default="hi")
    pack: Mapped[str] = mapped_column(String(32), default="general")
    occupation: Mapped[str | None] = mapped_column(String(200))
    upi_id: Mapped[str | None] = mapped_column(String(120))
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    goal: Mapped[str] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(_enum(TaskStatus), default=TaskStatus.QUEUED)
    sdk_session_id: Mapped[str | None] = mapped_column(String(120))
    # `summary` is the short spoken version; `result` the full detail kept for follow-ups.
    summary: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(Text)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 4))
    # The caller is holding the line for this result (see api.tools.tasks.wait_for_task).
    caller_waiting: Mapped[bool] = mapped_column(default=False, server_default="false")
    # The call that rang them with the result. The result only counts as heard once that call
    # completes with a person on the line (see api.routes.webhooks).
    callback_execution_id: Mapped[str | None] = mapped_column(String(64), index=True)
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TaskQuestion(Base):
    __tablename__ = "task_questions"

    id: Mapped[uuid.UUID] = _pk()
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)
    status: Mapped[QuestionStatus] = mapped_column(
        _enum(QuestionStatus), default=QuestionStatus.OPEN
    )
    created_at: Mapped[datetime] = _created_at()


class Routine(Base):
    __tablename__ = "routines"
    __table_args__ = (
        CheckConstraint("cron IS NOT NULL OR run_at IS NOT NULL", name="has_schedule"),
        Index("ix_routines_due", "active", "next_run_at"),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    kind: Mapped[RoutineKind] = mapped_column(_enum(RoutineKind))
    cron: Mapped[str | None] = mapped_column(String(64))
    run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = _created_at()


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    action: Mapped[str] = mapped_column(String(64))
    args: Mapped[dict] = mapped_column(JSONB, default=dict)
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[ActionStatus] = mapped_column(_enum(ActionStatus), default=ActionStatus.PENDING)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()


class OutreachCall(Base):
    """One person Saarthi phones on a user's behalf; the task that asked for it is the batch."""

    __tablename__ = "outreach_calls"

    id: Mapped[uuid.UUID] = _pk()
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = _user_fk()
    contact_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    purpose: Mapped[str] = mapped_column(Text)
    status: Mapped[OutreachStatus] = mapped_column(
        _enum(OutreachStatus), default=OutreachStatus.QUEUED
    )
    # What the person said, written by the messenger agent in the user's language.
    outcome: Mapped[str | None] = mapped_column(String(32))
    note: Mapped[str | None] = mapped_column(Text)
    session_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    bolna_execution_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = _created_at()
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = _pk()
    bolna_execution_id: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    agent_name: Mapped[str | None] = mapped_column(String(64))
    direction: Mapped[CallDirection | None] = mapped_column(_enum(CallDirection))
    purpose: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    transcript: Mapped[str | None] = mapped_column(Text)
    extracted: Mapped[dict | None] = mapped_column(JSONB)
    duration_seconds: Mapped[float | None] = mapped_column(Numeric(10, 2))
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()


class CallSession(Base):
    """Opaque per-call token handed to the voice LLM; tools resolve the caller from it."""

    __tablename__ = "call_sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    phone: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    bolna_execution_id: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()


class ProfileCache(Base):
    __tablename__ = "profile_cache"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    profile_text: Mapped[str] = mapped_column(Text, default="")
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BolnaAgent(Base):
    __tablename__ = "bolna_agents"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64))
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
