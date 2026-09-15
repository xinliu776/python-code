import asyncio
import inspect
import json


class ToolRegistry:

    def __init__(self):
        self._tools = {}

    def register(
        self,
        *,
        name,
        description,
        parameters,
        handler,
        source="builtin",
        timeout_seconds=20,
        max_retries=1
    ):
        if name in self._tools:
            raise ValueError(
                f"Tool already registered: {name}"
            )

        self._tools[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            },
            "handler": handler,
            "source": source,
            "timeout_seconds": timeout_seconds,
            "max_retries": max_retries
        }

    def unregister(self, name: str):
        self._tools.pop(name, None)

    def schemas(self):
        return [
            tool["schema"]
            for tool in self._tools.values()
        ]

    def list_tools(self):
        return [
            {
                "name": name,
                "source": tool["source"]
            }
            for name, tool in self._tools.items()
        ]

    async def execute(
        self,
        name: str,
        arguments: str
    ):
        if name not in self._tools:
            return {
                "success": False,
                "error": f"Tool not found: {name}",
                "attempts": 0
            }

        tool = self._tools[name]

        try:
            args = json.loads(arguments)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid tool arguments: {e}",
                "attempts": 0
            }

        handler = tool["handler"]
        timeout = tool["timeout_seconds"]
        max_retries = tool["max_retries"]

        last_error = None

        for attempt in range(
            1,
            max_retries + 2
        ):
            try:

                if inspect.iscoroutinefunction(
                    handler
                ):
                    task = handler(**args)

                else:
                    task = asyncio.to_thread(
                        handler,
                        **args
                    )

                result = await asyncio.wait_for(
                    task,
                    timeout=timeout
                )

                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt
                }

            except asyncio.TimeoutError:
                last_error = (
                    f"Tool timeout after "
                    f"{timeout} seconds"
                )

            except Exception as e:
                last_error = str(e)

            if attempt <= max_retries:
                await asyncio.sleep(
                    min(2 ** (attempt - 1), 4)
                )

        return {
            "success": False,
            "error": last_error,
            "attempts": max_retries + 1
        }


tool_registry = ToolRegistry()