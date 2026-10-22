import os

import httpx
from claude_agent_sdk import create_sdk_mcp_server, tool

MAX_CALLS = 10

CALLS_SCHEMA = {
    "type": "object",
    "properties": {
        "calls": {
            "type": "array",
            "maxItems": MAX_CALLS,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Who to call, as the user says it"},
                    "phone": {"type": "string", "description": "Their phone number"},
                    "purpose": {
                        "type": "string",
                        "description": "What the caller should say and ask, with any amount",
                    },
                },
                "required": ["name", "phone", "purpose"],
            },
        }
    },
    "required": ["calls"],
}


def calls_server(calls_url: str):
    @tool(
        "request_calls",
        "Have Saarthi phone these people on the user's behalf, starting right away. Send "
        "everyone in one request; Saarthi calls the user back with what each person said.",
        CALLS_SCHEMA,
    )
    async def request_calls(args: dict) -> dict:
        headers = {"Authorization": f"Bearer {os.environ['SANDBOX_TOKEN']}"}
        async with httpx.AsyncClient(timeout=30) as http:
            response = await http.post(calls_url, json=args, headers=headers)
        return {
            "content": [{"type": "text", "text": response.text}],
            "is_error": not response.is_success,
        }

    return create_sdk_mcp_server("saarthi", tools=[request_calls])
