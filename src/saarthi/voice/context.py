from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from saarthi.db.models import OutreachCall, User
from saarthi.domain import call_sessions, tasks, users
from saarthi.domain.phone import InvalidPhone, normalize_phone
from saarthi.domain.routines import USER_TZ
from saarthi.memory import profile_cache
from saarthi.packs import pack_for

# We don't know a new caller's language yet, so the first line invites any.
NEW_CALLER_GREETING = (
    "नमस्ते! मैं सारथी हूँ, आपका अपना सहायक। आप किसी भी भाषा में बात कर सकते हैं। आपका नाम क्या है?"
)

# Opening lines per language a returning caller last used; anything else falls back to Hindi
# and the agent switches as soon as they speak.
GREETINGS = {
    "hi": {
        "hello": "नमस्ते {name} जी",
        "task_result": "{hello}, सारथी बोल रहा हूँ। आपके काम का अपडेट है: {message}",
        "reminder": "{hello}, सारथी बोल रहा हूँ। आपने याद दिलाने को कहा था: {message}",
        "calls_done": "{hello}, सारथी बोल रहा हूँ। आपके कहने पर मैंने सबको कॉल कर लिया। {message}",
        "login_code": "{hello}, सारथी बोल रहा हूँ। आपका लॉगिन कोड है: {message}। फिर से: {message}।",
        "unheard": "{hello}! आपके काम का अपडेट: {message} और बताइए, क्या करना है?",
        "inbound": "{hello}! बताइए, क्या करना है?",
    },
    "en": {
        "hello": "Hi {name}",
        "task_result": "{hello}, this is Saarthi with an update on your task: {message}",
        "reminder": "{hello}, this is Saarthi. You asked me to remind you: {message}",
        "calls_done": "{hello}, this is Saarthi. I made the calls you asked for. {message}",
        "login_code": "{hello}, this is Saarthi. Your sign-in code is {message}. Again: {message}.",
        "unheard": "{hello}! An update on your task: {message} What else can I do for you?",
        "inbound": "{hello}! What can I do for you?",
    },
}

# Every key build_call_context returns. Bolna merges these into tool params with the same
# name, so tool parameters must not reuse them (except `session`, which we want injected).
CONTEXT_KEYS = frozenset(
    {
        "session",
        "is_new",
        "greeting",
        "name",
        "language",
        "now",
        "profile",
        "pack_prompt",
        "custom_instructions",
        "task_updates",
        "call_reason",
    }
)

# The same, for saarthi-messenger calls to someone on a user's behalf.
MESSENGER_CONTEXT_KEYS = frozenset(
    {"session", "greeting", "contact_name", "owner_name", "purpose", "language", "now"}
)

MESSENGER_GREETINGS = {
    "hi": "नमस्ते, क्या मेरी बात {contact} से हो रही है? मैं सारथी हूँ, {owner} जी का AI सहायक।",
    "en": "Hello, am I speaking with {contact}? This is Saarthi, {owner}'s AI assistant.",
}


class CallReason(StrEnum):
    INBOUND = "inbound"
    TASK_RESULT = "task_result"
    REMINDER = "reminder"
    CALLS_DONE = "calls_done"
    LOGIN_CODE = "login_code"


async def build_call_context(
    db: AsyncSession,
    raw_phone: str,
    *,
    execution_id: str | None = None,
    reason: CallReason = CallReason.INBOUND,
    message: str = "",
) -> dict[str, str]:
    """Prompt variables for saarthi-main, used by inbound lookup and outbound calls alike.

    Only touches Postgres: inbound lookup must answer Bolna within 3 seconds, so the memory
    profile comes from the cache the post-call ingest job keeps fresh. Finished tasks the
    caller has not heard about yet are folded into the greeting (so they are spoken without
    waiting on the LLM) and marked reported.
    """
    try:
        phone = normalize_phone(raw_phone)
    except InvalidPhone:
        phone = raw_phone.strip()

    user = await users.get_by_phone(db, phone)
    session = await call_sessions.issue(
        db, phone=phone, user_id=user.id if user else None, execution_id=execution_id
    )
    base = {"session": session.token, "now": _now(), "call_reason": reason.value}
    if user is None:
        return base | {
            "is_new": "yes",
            "greeting": NEW_CALLER_GREETING,
            "name": "",
            "language": "unknown",
            "profile": "",
            "pack_prompt": "",
            "custom_instructions": "none",
            "task_updates": "none",
        }

    unheard = await tasks.unreported(db, user.id) if reason is CallReason.INBOUND else []
    tasks.mark_reported(unheard)
    recent = await tasks.recent(db, user.id)
    return base | {
        "is_new": "no",
        "greeting": _greeting(user, reason, message, [t.summary or "" for t in unheard]),
        "name": user.name or "",
        "language": user.language,
        "profile": await profile_cache.get(db, user.id) or "(nothing yet)",
        "pack_prompt": pack_for(user.pack).voice_prompt,
        "custom_instructions": user.custom_instructions or "none",
        "task_updates": "\n".join(tasks.describe(t) for t in recent) or "none",
    }


async def build_messenger_context(
    db: AsyncSession, owner: User, call: OutreachCall
) -> dict[str, str]:
    # No user on this session: the person we call must not reach the owner's tools or data.
    session = await call_sessions.issue(db, phone=call.phone, user_id=None)
    call.session_token = session.token
    greeting = MESSENGER_GREETINGS.get(owner.language, MESSENGER_GREETINGS["hi"])
    return {
        "session": session.token,
        "greeting": greeting.format(contact=call.contact_name, owner=owner.name),
        "contact_name": call.contact_name,
        "owner_name": owner.name or "",
        "purpose": call.purpose,
        "language": owner.language,
        "now": _now(),
    }


def _now() -> str:
    return datetime.now(UTC).astimezone(USER_TZ).strftime("%A %d %B %Y, %I:%M %p")


def _greeting(user: User, reason: CallReason, message: str, unheard: list[str]) -> str:
    lines = GREETINGS.get(user.language, GREETINGS["hi"])
    hello = lines["hello"].format(name=user.name)
    if reason is not CallReason.INBOUND:
        return lines[reason.value].format(hello=hello, message=message)
    if unheard:
        return lines["unheard"].format(hello=hello, message=" ".join(unheard))
    return lines["inbound"].format(hello=hello)
