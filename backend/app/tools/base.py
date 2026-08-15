from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class Tool:
    def __init__(
        self,
        definition: ToolDefinition,
        handler: Callable[[dict[str, Any]], Awaitable[Any]],
    ):
        self.definition = definition
        self.handler = handler

    async def invoke(self, arguments: dict[str, Any]) -> Any:
        return await self.handler(arguments)

