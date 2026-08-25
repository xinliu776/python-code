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
def get_mcp_result(result):
    if result.structured_content is not None:
        return result.structured_content

    texts = []

    for item in result.content:
        if hasattr(item, "text"):
            texts.append(item.text)

    return "\n".join(texts)
async def main():

    base_dir = Path(__file__).parent

    calculator_path = (
        base_dir /"mcp_servers"/ "calculator_server.py"
    ).resolve()

    knowledge_path = (
        base_dir /"mcp_servers"/ "knowledge_server.py"
    ).resolve()

    search_path = (
        base_dir / "mcp_servers" / "search_server.py"
    ).resolve()

    calculator_params = StdioServerParameters(
        command="mcp",
        args=["run", str(calculator_path)]
    )

    knowledge_params = StdioServerParameters(
        command="mcp",
        args=["run", str(knowledge_path)]
    )

    search_params = StdioServerParameters(
        command="mcp",
        args=["run", str(search_path)]
    )

    async with stdio_client(calculator_params) as (calc_read, calc_write):

        async with ClientSession(calc_read, calc_write) as calc_session:

            await calc_session.initialize()

            calc_tools = await calc_session.list_tools()



            async with stdio_client(knowledge_params) as (kb_read, kb_write):

                async with ClientSession(kb_read, kb_write) as kb_session:

                    await kb_session.initialize()
                    
                    kb_tools = await kb_session.list_tools()

                    async with stdio_client(search_params) as (search_read, search_write):
                        async with ClientSession(search_read, search_write) as search_session:

                            await search_session.initialize()

                            search_tools = await search_session.list_tools()

                            print("搜索服务器：")
                            print(search_tools)                    


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

                            for tool in search_tools.tools:
                                llm_tools.append({
                                    "type": "function",
                                    "function": {
                                        "name": tool.name,
                                        "description": tool.description or "",
                                        "parameters": tool.input_schema
                                    }
                                })

                                tool_session_map[tool.name] = search_session

                            for tool in llm_tools:
                                print(tool["function"]["name"])

                            messages = [{
                                    "role": "system",
                                    "content": """
                                你是一个研究型AI Agent。

                                工具使用原则：
                                1. 本地知识库已有的基础知识，优先使用 retrieve。
                                2. 涉及最新、近期、实时、2026年动态等信息，优先使用 web_search。
                                3. 涉及数学计算，使用计算工具。
                                4. 如果需要，可以连续调用多个工具。
                                5. 不要假装已经搜索或检索，只有实际调用工具后才能引用工具结果。
                                """
                                },
                                {
                                    "role": "user",
                                    "content": "AI Agent trends 2026"
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

                                        tool_result = get_mcp_result(result)

                                        print("MCP结果：", tool_result)

                                        messages.append({
                                            "role": "tool",
                                            "tool_call_id": tool_call.id,
                                            "content": (
                                                json.dumps(tool_result, ensure_ascii=False)
                                                if not isinstance(tool_result, str)
                                                else tool_result
                                            )
                                        })

                                else:
                                    print("最终回答：", message.content)
                                    break

asyncio.run(main())