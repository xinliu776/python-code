from app.core.tool_registry import tool_registry
import asyncio

def calculator(
    a: float,
    b: float,
    operation: str
):

    if operation == "add":
        return a + b

    if operation == "subtract":
        return a - b

    if operation == "multiply":
        return a * b

    if operation == "divide":

        if b == 0:
            raise ValueError(
                "Cannot divide by zero"
            )

        return a / b

    raise ValueError(
        f"Unsupported operation: {operation}"
    )


tool_registry.register(
    name="calculator",

    description="执行基础数学计算",

    parameters={
        "type": "object",
        "properties": {

            "a": {
                "type": "number"
            },

            "b": {
                "type": "number"
            },

            "operation": {
                "type": "string",
                "enum": [
                    "add",
                    "subtract",
                    "multiply",
                    "divide"
                ]
            }
        },

        "required": [
            "a",
            "b",
            "operation"
        ]
    },

    handler=calculator
)

async def wait_seconds(
    seconds: int
):

    if seconds < 1:
        raise ValueError(
            "seconds must be >= 1"
        )

    if seconds > 60:
        raise ValueError(
            "seconds must be <= 60"
        )

    await asyncio.sleep(
        seconds
    )

    return {
        "waited_seconds":
            seconds
    }


tool_registry.register(
    name="wait_seconds",

    description=(
        "等待指定秒数，"
        "用于需要延迟执行的任务"
    ),

    parameters={
        "type": "object",

        "properties": {
            "seconds": {
                "type": "integer",
                "minimum": 1,
                "maximum": 60
            }
        },

        "required": [
            "seconds"
        ]
    },

    handler=wait_seconds,

    timeout_seconds=65,

    max_retries=0
)