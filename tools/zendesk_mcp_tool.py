import os
from typing import Any


ZENDESK_MCP_URL = os.getenv("ZENDESK_MCP_URL")
ZENDESK_MCP_AUTH_TOKEN = os.getenv("ZENDESK_MCP_AUTH_TOKEN")
ZENDESK_TICKET_COMPLETION_STATUS = os.getenv(
    "ZENDESK_TICKET_COMPLETION_STATUS",
    "solved",
)
ZENDESK_MCP_UPDATE_TICKET_TOOL = os.getenv(
    "ZENDESK_MCP_UPDATE_TICKET_TOOL",
    "update_ticket",
)


def _content_to_dict(content) -> dict[str, Any]:
    if hasattr(content, "model_dump"):
        return content.model_dump()
    if hasattr(content, "dict"):
        return content.dict()
    return {"value": str(content)}


def _tool_result_to_dict(result) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return {
            "status": "success",
            "structured_content": structured,
        }

    return {
        "status": "success",
        "content": [
            _content_to_dict(content)
            for content in getattr(result, "content", [])
        ],
    }


async def update_ticket_status_via_mcp(
    *,
    ticket_id: int,
    status: str | None = None,
    comment: str | None = None,
    workflow_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Update a Zendesk ticket through a remote MCP Streamable HTTP server.
    """
    target_status = status or ZENDESK_TICKET_COMPLETION_STATUS
    payload = {
        "ticket_id": ticket_id,
        "status": target_status,
        "comment": comment,
    }
    if workflow_result:
        payload["workflow_summary"] = {
            "triage": workflow_result.get("triage"),
            "resolution": workflow_result.get("resolution"),
            "actions_taken": workflow_result.get("actions_taken", []),
        }

    if not ZENDESK_MCP_URL:
        return {
            "status": "skipped",
            "reason": "ZENDESK_MCP_URL is not configured",
            "mcp_tool": ZENDESK_MCP_UPDATE_TICKET_TOOL,
            "payload": payload,
        }

    try:
        import httpx
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Missing MCP client dependency: {e}",
            "install_hint": "Install dependencies from requirements.txt, including mcp.",
            "mcp_url": ZENDESK_MCP_URL,
            "mcp_tool": ZENDESK_MCP_UPDATE_TICKET_TOOL,
            "payload": payload,
        }

    headers = {}
    if ZENDESK_MCP_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {ZENDESK_MCP_AUTH_TOKEN}"

    try:
        async with httpx.AsyncClient(headers=headers or None, follow_redirects=True) as http_client:
            async with streamable_http_client(
                ZENDESK_MCP_URL,
                http_client=http_client,
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        ZENDESK_MCP_UPDATE_TICKET_TOOL,
                        arguments=payload,
                    )

        parsed = _tool_result_to_dict(result)
        parsed.update({
            "mcp_url": ZENDESK_MCP_URL,
            "mcp_tool": ZENDESK_MCP_UPDATE_TICKET_TOOL,
            "payload": payload,
        })
        return parsed
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "mcp_url": ZENDESK_MCP_URL,
            "mcp_tool": ZENDESK_MCP_UPDATE_TICKET_TOOL,
            "payload": payload,
        }
