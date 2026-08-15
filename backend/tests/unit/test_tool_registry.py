import pytest

from app.tools.base import Tool, ToolDefinition
from app.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_tool_registry_invokes_registered_tool():
    registry = ToolRegistry()

    async def handler(arguments):
        return {"ok": arguments["value"]}

    registry.register(
        Tool(
            ToolDefinition(name="example", description="Example tool", input_schema={}),
            handler,
        )
    )

    result = await registry.invoke("example", {"value": True})

    assert result == {"ok": True}

