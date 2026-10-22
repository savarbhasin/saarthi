from datetime import datetime
from typing import Any, Self

import httpx

from saarthi.config import get_settings


class BolnaError(RuntimeError):
    def __init__(self, status: int, body: Any):
        super().__init__(f"Bolna API {status}: {body}")
        self.status = status
        self.body = body


class BolnaClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self._http = httpx.AsyncClient(
            base_url=base_url or settings.bolna_base_url,
            headers={"Authorization": f"Bearer {api_key or settings.bolna_api_key}"},
            timeout=30,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_) -> None:
        await self._http.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        response = await self._http.request(method, path, **kwargs)
        if response.is_error:
            try:
                body = response.json()
            except ValueError:
                body = response.text
            raise BolnaError(response.status_code, body)
        return response.json() if response.content else None

    async def create_agent(self, payload: dict) -> str:
        return (await self._request("POST", "/v2/agent", json=payload))["agent_id"]

    async def update_agent(self, agent_id: str, payload: dict) -> None:
        await self._request("PUT", f"/v2/agent/{agent_id}", json=payload)

    async def get_agent(self, agent_id: str) -> dict:
        return await self._request("GET", f"/v2/agent/{agent_id}")

    async def add_custom_model(
        self, *, name: str, base_url: str, api_key: str, family: str, languages: str
    ) -> None:
        await self._request(
            "POST",
            "/user/model/custom",
            json={
                "custom_model_name": name,
                "custom_model_url": base_url,
                "custom_model_key": api_key,
                "custom_model_family": family,
                "custom_model_languages": languages,
            },
        )

    async def setup_inbound(self, agent_id: str, phone_number_id: str) -> dict:
        return await self._request(
            "POST",
            "/inbound/setup",
            json={"agent_id": agent_id, "phone_number_id": phone_number_id},
        )

    async def list_phone_numbers(self) -> list[dict]:
        return await self._request("GET", "/phone-numbers/all")

    async def make_call(
        self,
        *,
        agent_id: str,
        to: str,
        user_data: dict[str, str] | None = None,
        from_number: str | None = None,
        scheduled_at: datetime | None = None,
    ) -> str:
        body: dict[str, Any] = {"agent_id": agent_id, "recipient_phone_number": to}
        if user_data:
            body["user_data"] = user_data
        if from_number:
            body["from_phone_number"] = from_number
        if scheduled_at:
            # Bolna rejects a trailing "Z"; isoformat() on an aware datetime gives "+00:00".
            body["scheduled_at"] = scheduled_at.isoformat()
        return (await self._request("POST", "/call", json=body))["execution_id"]

    async def get_execution(self, execution_id: str) -> dict:
        return await self._request("GET", f"/executions/{execution_id}")
