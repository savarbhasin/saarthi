from saarthi.db.models import BolnaAgent, OutreachCall, User
from saarthi.db.session import session_scope
from saarthi.voice.bolna import BolnaClient
from saarthi.voice.context import CallReason, build_call_context, build_messenger_context

MAIN_AGENT = "saarthi-main"
MESSENGER_AGENT = "saarthi-messenger"


async def _agent_id(session, name: str) -> str:
    agent = await session.get(BolnaAgent, name)
    if agent is None:
        raise RuntimeError(f"{name} is not synced yet; run saarthi-sync first")
    return agent.agent_id


async def call_phone(phone: str, reason: CallReason = CallReason.INBOUND, message: str = "") -> str:
    async with session_scope() as session:
        agent_id = await _agent_id(session, MAIN_AGENT)
        context = await build_call_context(session, phone, reason=reason, message=message)
    async with BolnaClient() as bolna:
        return await bolna.make_call(agent_id=agent_id, to=phone, user_data=context)


async def call_for_user(session, owner: User, call: OutreachCall) -> str:
    # Runs inside the caller's transaction, so the session token is saved with the call.
    agent_id = await _agent_id(session, MESSENGER_AGENT)
    context = await build_messenger_context(session, owner, call)
    async with BolnaClient() as bolna:
        return await bolna.make_call(agent_id=agent_id, to=call.phone, user_data=context)
