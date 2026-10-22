import argparse
import asyncio
import json

from saarthi.config import Settings, get_settings
from saarthi.db.models import BolnaAgent
from saarthi.db.session import session_scope
from saarthi.voice import llm_check
from saarthi.voice.agents import REGISTRY, build_payload
from saarthi.voice.bolna import BolnaClient, BolnaError

CUSTOM_MODEL_LANGUAGES = "hi,en,bn,ta,te,mr,gu,kn,pa,ml"


async def ensure_custom_model(bolna: BolnaClient, settings: Settings) -> None:
    if settings.llm_provider != "custom":
        return
    if not settings.llm_api_key:
        raise SystemExit("LLM_API_KEY is required to register the custom model with Bolna")
    try:
        await bolna.add_custom_model(
            name=settings.llm_model,
            base_url=settings.llm_base_url.rstrip("/"),
            api_key=settings.llm_api_key,
            family=settings.llm_family,
            languages=CUSTOM_MODEL_LANGUAGES,
        )
        print(f"registered custom model {settings.llm_model}")
    except BolnaError as exc:
        if exc.status != 409:
            raise
        print(f"custom model {settings.llm_model} already registered")


async def sync_agents(names: list[str] | None = None) -> dict[str, str]:
    settings = get_settings()
    specs = [REGISTRY[n] for n in names] if names else list(REGISTRY.values())
    synced: dict[str, str] = {}

    async with BolnaClient() as bolna, session_scope() as session:
        await ensure_custom_model(bolna, settings)
        for spec in specs:
            payload = build_payload(spec, settings)
            row = await session.get(BolnaAgent, spec.name)
            if row:
                await bolna.update_agent(row.agent_id, payload)
                print(f"updated {spec.name} ({row.agent_id})")
            else:
                row = BolnaAgent(name=spec.name, agent_id=await bolna.create_agent(payload))
                session.add(row)
                print(f"created {spec.name} ({row.agent_id})")
            synced[spec.name] = row.agent_id

            if spec.inbound and settings.bolna_phone_number_id:
                await bolna.setup_inbound(row.agent_id, settings.bolna_phone_number_id)
                print(f"  inbound number {settings.bolna_phone_number_id} -> {spec.name}")
    return synced


async def _list_numbers() -> None:
    async with BolnaClient() as bolna:
        for number in await bolna.list_phone_numbers():
            print(f"{number['id']}  {number['phone_number']}  {number['telephony_provider']}")


async def _check_llm() -> None:
    result = await llm_check.probe(get_settings())
    first = f"{result.first_token_seconds:.2f}s" if result.first_token_seconds else "never"
    print(f"first spoken token: {first}   total: {result.total_seconds:.2f}s")
    print(f"reasoning chars: {result.reasoning_chars}   reply: {result.reply!r}")
    if result.reasoning_chars:
        print("WARNING: the model is still thinking; adjust LLM_EXTRA_BODY")
    if result.first_token_seconds and result.first_token_seconds > 1.0:
        print("WARNING: over ~1s to first token, callers will hear a pause")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Saarthi's Bolna agents from code")
    parser.add_argument("agents", nargs="*", help=f"subset of: {', '.join(REGISTRY)}")
    parser.add_argument("--dry-run", action="store_true", help="print payloads, call nothing")
    parser.add_argument("--numbers", action="store_true", help="list Bolna phone numbers")
    parser.add_argument("--check-llm", action="store_true", help="probe LLM latency/thinking")
    args = parser.parse_args()

    if args.numbers:
        asyncio.run(_list_numbers())
    elif args.check_llm:
        asyncio.run(_check_llm())
    elif args.dry_run:
        for name in args.agents or REGISTRY:
            print(json.dumps(build_payload(REGISTRY[name], get_settings()), indent=2))
    else:
        asyncio.run(sync_agents(args.agents or None))


if __name__ == "__main__":
    main()
