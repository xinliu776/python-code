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

def compress_webpage(content, question, url):

    if not isinstance(content, str):
        content = json.dumps(
            content,
            ensure_ascii=False
        )

    response = llm_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": """
你是研究资料压缩器。

你的任务不是回答用户问题，
而是从网页中提取对研究问题有用的证据。

只保留：
1. 核心观点
2. 关键事实或数据
3. 与研究问题直接相关的信息
4. 来源URL

删除广告、导航、重复内容和无关信息。

控制在500字以内。
"""
            },
            {
                "role": "user",
                "content": f"""
研究问题：
{question}

来源：
{url}

网页内容：
{content}
"""
            }
        ]
    )

    return response.choices[0].message.content

def generate_report(question, evidence_list):

    evidence_text = json.dumps(
        evidence_list,
        ensure_ascii=False,
        indent=2
    )

    response = llm_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": """
你是一名研究报告撰写者。

只能根据提供的研究证据生成报告。

要求：
1. 总结不同来源的共同观点。
2. 指出不同来源之间的差异。
3. 不要编造证据中不存在的数据。
4. 给出5个最值得关注的趋势。
5. 最后列出来源URL。
"""
            },
            {
                "role": "user",
                "content": f"""
研究问题：
{question}

研究证据：
{evidence_text}
"""
            }
        ]
    )

    return response.choices[0].message.content
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
                            
                            user_question = "研究一下2026年AI Agent的发展趋势"

                            messages = [{
                                    "role": "system",
                                    "content": """
                                你是一个研究型 AI Agent。
                                工具使用原则：
                                1. 本地知识库问题优先使用 retrieve。
                                2. 最新、实时、近期信息使用 web_search。
                                3. web_search 只用于发现资料，不能把搜索摘要当作完整原文。
                                4. 进行研究类任务时：
                                - 先使用 web_search 搜索资料；
                                研究任务最多进行2次网络搜索。
                                从搜索结果中选择3个高质量且不同的来源阅读。
                                阅读3个来源后必须停止继续搜索和阅读，开始综合分析。
                                不要重复读取同一个URL。
                                - 分别调用 read_webpage 阅读正文；
                                - 优先选择官方机构、大学、主流媒体、知名技术公司的资料；
                                - 不要只依赖一个来源。
                                5. 如果不同来源说法冲突，要明确指出。
                                6. 最终回答必须列出实际阅读过的来源标题和 URL。
                                7. 数学计算使用计算工具。
                                8. 可以连续调用多个工具完成复杂任务。
                                """
                                },
                                {
                                    "role": "user",
                                    "content":user_question
                                }
                            ]
                            MAX_SEARCH_CALLS = 2
                            MAX_READ_CALLS = 3
                            MAX_AGENT_STEPS = 15
                            agent_steps = 0
                            search_calls = 0
                            read_calls = 0
                            visited_urls = set()
                            evidence_list = []
                            while True:
                                agent_steps += 1

                                if agent_steps > MAX_AGENT_STEPS:
                                    print("Agent达到最大执行轮数，强制停止")
                                    break
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
                                        arguments = json.loads(tool_call.function.arguments)

                                        print("调用工具：", tool_name)

                                        # 搜索次数限制
                                        if tool_name == "web_search":
                                            if search_calls >= MAX_SEARCH_CALLS:
                                                tool_result = {
                                                    "error": "搜索次数已达到上限，请根据已有资料继续分析。"
                                                }
                                            else:
                                                search_calls += 1

                                                target_session = tool_session_map[tool_name]

                                                result = await target_session.call_tool(
                                                    tool_name,
                                                    arguments
                                                )

                                                tool_result = get_mcp_result(result)

                                        # 网页阅读限制

                                        elif tool_name == "read_webpage":
                                            url = arguments["url"]

                                            if url in visited_urls:
                                                tool_result = {
                                                    "error": "这个网页已经成功读取过，请不要重复读取。"
                                                }

                                            elif read_calls >= MAX_READ_CALLS:
                                                tool_result = {
                                                    "error": "已经成功阅读3个来源，请停止继续读取并开始综合分析。"
                                                }

                                            else:
                                                target_session = tool_session_map[tool_name]

                                                result = await target_session.call_tool(
                                                    tool_name,
                                                    arguments
                                                )

                                                raw_result = get_mcp_result(result)

                                                # 先判断读取是否成功
                                                if result.is_error:
                                                    tool_result = {
                                                        "error": "网页读取失败",
                                                        "detail": str(raw_result)
                                                    }

                                                else:
                                                    # 如果 MCP 返回的是 JSON 字符串，先转成 Python 对象
                                                    if isinstance(raw_result, str):
                                                        try:
                                                            parsed_result = json.loads(raw_result)
                                                        except json.JSONDecodeError:
                                                            parsed_result = None
                                                    else:
                                                        parsed_result = raw_result

                                                    # read_webpage 自己捕获异常时，
                                                    # MCP本身可能 is_error=False，但返回 {"error": "..."}
                                                    if (
                                                        isinstance(parsed_result, dict)
                                                        and parsed_result.get("error")
                                                    ):
                                                        tool_result = parsed_result

                                                    else:
                                                        # 到这里才算真正读取成功
                                                        read_calls += 1
                                                        visited_urls.add(url)

                                                        tool_result = compress_webpage(
                                                            raw_result,
                                                            user_question,
                                                            url
                                                        )

                                                        evidence_list.append({
                                                            "url": url,
                                                            "evidence": tool_result
                                                        })
                                                        
                                                        print(
                                                            f"成功阅读：{read_calls}/{MAX_READ_CALLS}"
                                                        )
                                                        print("压缩后的网页证据：")
                                                        print(tool_result)

                                        

                                        # 其他工具正常执行
                                        else:
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
                                    report = generate_report(
                                        user_question,
                                        evidence_list
                                    )

                                    print("\n===== 最终研究报告 =====\n")
                                    print(report)

                                    break

asyncio.run(main())