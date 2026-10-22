import asyncio
import dataclasses
import hashlib
import hmac
import uuid
from dataclasses import dataclass

import docker
import httpx
from docker.errors import NotFound
from docker.models.containers import Container

from saarthi.config import get_settings

AGENT_PORT = 8700
VNC_PORT = 6080
HEALTH_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class Sandbox:
    name: str
    url: str
    token: str
    vnc_host_port: int | None


def sandbox_token(user_id: uuid.UUID) -> str:
    # Derived rather than stored: the API can verify a sandbox's callback from the task's
    # user alone, and rotating BOLNA_TOOL_SECRET rotates every sandbox token.
    secret = get_settings().bolna_tool_secret.encode()
    return hmac.new(secret, f"sandbox:{user_id}".encode(), hashlib.sha256).hexdigest()


def _names(user_id: uuid.UUID) -> tuple[str, str]:
    short = user_id.hex[:12]
    return f"saarthi-sbx-{short}", f"saarthi-home-{short}"


def _environment(token: str) -> dict[str, str]:
    settings = get_settings()
    return {
        "SANDBOX_TOKEN": token,
        "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
        "ANTHROPIC_AUTH_TOKEN": settings.openrouter_api_key,
        "ANTHROPIC_API_KEY": "",
        "WORKER_MODEL": settings.worker_model,
        "ANTHROPIC_DEFAULT_SONNET_MODEL": settings.worker_model,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": settings.worker_fast_model,
        "WORKER_MAX_BUDGET_USD": str(settings.worker_max_budget_usd),
    }


def _vnc_port(container: Container) -> int | None:
    bindings = (container.attrs["NetworkSettings"]["Ports"] or {}).get(f"{VNC_PORT}/tcp")
    return int(bindings[0]["HostPort"]) if bindings else None


def _vnc_port_by_name(name: str) -> int | None:
    return _vnc_port(docker.from_env().containers.get(name))


def _ensure_sync(user_id: uuid.UUID) -> Sandbox:
    settings = get_settings()
    client = docker.from_env()
    name, volume = _names(user_id)
    token = sandbox_token(user_id)
    try:
        container = client.containers.get(name)
        if container.status != "running":
            container.start()
    except NotFound:
        container = client.containers.run(
            settings.sandbox_image,
            name=name,
            detach=True,
            environment=_environment(token),
            volumes={volume: {"bind": "/home/saarthi", "mode": "rw"}},
            network=settings.sandbox_network,
            ports={f"{VNC_PORT}/tcp": ("127.0.0.1", None)},
            mem_limit=settings.sandbox_memory,
            nano_cpus=int(settings.sandbox_cpus * 1e9),
            pids_limit=1024,
            shm_size="1g",
            labels={"saarthi.user_id": str(user_id)},
            restart_policy={"Name": "unless-stopped"},
        )
    container.reload()
    return Sandbox(name, f"http://{name}:{AGENT_PORT}", token, _vnc_port(container))


async def _wait_healthy(sandbox: Sandbox) -> None:
    async with httpx.AsyncClient(timeout=5) as http:
        for _ in range(HEALTH_TIMEOUT_SECONDS):
            try:
                if (await http.get(f"{sandbox.url}/health")).is_success:
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1)
    raise TimeoutError(f"sandbox {sandbox.name} did not become healthy")


async def ensure(user_id: uuid.UUID) -> Sandbox:
    sandbox = await asyncio.to_thread(_ensure_sync, user_id)
    await _wait_healthy(sandbox)
    # A just-created container has no host port bound until it is running, so read it again.
    port = await asyncio.to_thread(_vnc_port_by_name, sandbox.name)
    return dataclasses.replace(sandbox, vnc_host_port=port)


async def start_task(sandbox: Sandbox, payload: dict) -> None:
    async with httpx.AsyncClient(timeout=15) as http:
        response = await http.post(
            f"{sandbox.url}/tasks",
            json=payload,
            headers={"Authorization": f"Bearer {sandbox.token}"},
        )
        response.raise_for_status()
