import asyncio
from pathlib import Path
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

llm_client = OpenAI(
    api_key="sk-d1f41205cf5e4c83b6aaa897d159c87c",
    base_url="https://api.deepseek.com"
)
async def main():

    base_dir = Path(__file__).parent

    calculator_path = (
        base_dir / "calculator_server.py"
    ).resolve()

    knowledge_path = (
        base_dir / "knowledge_server.py"
    ).resolve()


    calculator_params = StdioServerParameters(
        command="mcp",
        args=["run", str(calculator_path)]
    )

    knowledge_params = StdioServerParameters(
        command="mcp",
        args=["run", str(knowledge_path)]
    )


    async with stdio_client(calculator_params) as (calc_read, calc_write):

        async with ClientSession(calc_read, calc_write) as calc_session:

            await calc_session.initialize()

            calc_tools = await calc_session.list_tools()

            print("计算服务器：")
            print(calc_tools)


            async with stdio_client(knowledge_params) as (kb_read, kb_write):

                async with ClientSession(kb_read, kb_write) as kb_session:

                    await kb_session.initialize()
                    
                    kb_tools = await kb_session.list_tools()

                    print("知识库服务器：")
                    print(kb_tools)

                    llm_tools = []
                    tool_session_map = {}
                    for tool in calc_tools.tools:

                        llm_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description or "",
                                "parameters": tool.input_schema
                            }
                        })

                        tool_session_map[tool.name] = calc_session

                    for tool in kb_tools.tools:
                        llm_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description or "",
                                "parameters": tool.input_schema
                            }
                        })

                        tool_session_map[tool.name] = kb_session
                    for tool in llm_tools:
                        print(tool["function"]["name"])

                    messages = [
                        {
                            "role": "user",
                            "content": "根据知识库告诉我MCP是什么，然后计算(100-25)×4。"
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

                                # 关键：自动找到这个工具属于哪个 MCP Server
                                target_session = tool_session_map[tool_name]

                                result = await target_session.call_tool(
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