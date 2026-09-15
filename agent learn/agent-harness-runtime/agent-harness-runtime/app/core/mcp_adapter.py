import re
from contextlib import AsyncExitStack

from mcp import (
    Client,
    StdioServerParameters
)

from app.core.tool_registry import (
    tool_registry
)


class MCPServerAdapter:

    def __init__(
        self,
        *,
        name: str,
        command: str,
        args: list[str],
        cwd=None,
        env=None
    ):
        self.name = name

        self.params = (
            StdioServerParameters(
                command=command,
                args=args,
                cwd=cwd,
                env=env
            )
        )

        self.stack = AsyncExitStack()

        self.client = None

        self.registered_tools = []

    def _local_tool_name(
        self,
        remote_name: str
    ):

        name = (
            f"mcp_{self.name}_{remote_name}"
        )

        return re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            name
        )

    async def connect(self):

        self.client = (
            await self.stack
            .enter_async_context(
                Client(self.params)
            )
        )

        result = (
            await self.client.list_tools()
        )

        for tool in result.tools:

            local_name = (
                self._local_tool_name(
                    tool.name
                )
            )

            handler = (
                self._create_handler(
                    tool.name
                )
            )

            tool_registry.register(
                name=local_name,

                description=(
                    tool.description
                    or
                    f"MCP tool: {tool.name}"
                ),

                parameters=
                    tool.input_schema,

                handler=handler,

                source=(
                    f"mcp:{self.name}"
                ),

                timeout_seconds=30,

                max_retries=1
            )

            self.registered_tools.append(
                local_name
            )

    def _create_handler(
        self,
        remote_name
    ):

        async def handler(**kwargs):

            result = (
                await self.client
                .call_tool(
                    remote_name,
                    kwargs
                )
            )

            if result.is_error:

                texts = []

                for item in result.content:

                    text = getattr(
                        item,
                        "text",
                        None
                    )

                    if text:
                        texts.append(text)

                raise RuntimeError(
                    "\n".join(texts)
                    or
                    f"MCP tool failed: "
                    f"{remote_name}"
                )

            if (
                result.structured_content
                is not None
            ):
                return (
                    result
                    .structured_content
                )

            output = []

            for item in result.content:

                if hasattr(
                    item,
                    "model_dump"
                ):
                    output.append(
                        item.model_dump(
                            mode="json"
                        )
                    )

                else:
                    output.append(
                        str(item)
                    )

            return output

        return handler

    async def close(self):

        for name in self.registered_tools:
            tool_registry.unregister(
                name
            )

        self.registered_tools.clear()

        await self.stack.aclose()