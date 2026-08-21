import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
import json
server_path = Path(__file__).with_name("server.py").resolve()

print("MCP Server路径：", server_path)

llm_client = OpenAI(
    api_key="sk-d1f41205cf5e4c83b6aaa897d159c87c",
    base_url="https://api.deepseek.com"
)
async def main():
    server_params = StdioServerParameters(
    command="mcp",
    args=["run", str(server_path)]
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            tools_result = await session.list_tools()
            print(tools_result)
            mcp_tools=tools_result.tools
            llm_tools=[]
            for tool in mcp_tools:
                llm_tools.append(
                    {"type":"function",
                     "function":{
                         "name":tool.name,
                         "description":tool.description or "",
                         "parameters":tool.input_schema
                     }}
                )

            messages = [
                {
                    "role": "user",
                    "content": "计算 (100 - 25) × 4"
                }
            ]

            while True:
                response = llm_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    tools=llm_tools
                )

                message = response.choices[0].message
                messages.append(message)

                if message.tool_calls:

                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        arguments = json.loads(
                            tool_call.function.arguments
                        )

                        print("调用工具：", tool_name)
                        print("参数：", arguments)

                        result = await session.call_tool(
                            tool_name,
                            arguments
                        )

                        print("MCP结果：", result.structured_content)

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(
                                result.structured_content,
                                ensure_ascii=False
                            )
                        })

                else:
                    print("最终回答：", message.content)
                    break
asyncio.run(main())