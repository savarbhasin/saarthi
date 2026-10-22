from saarthi.voice.agents.base import AgentSpec, build_payload
from saarthi.voice.agents.main import MAIN
from saarthi.voice.agents.messenger import MESSENGER

REGISTRY: dict[str, AgentSpec] = {spec.name: spec for spec in [MAIN, MESSENGER]}

__all__ = ["REGISTRY", "AgentSpec", "build_payload"]
