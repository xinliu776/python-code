from tools import tools
from openai import OpenAI
import json
from tool_registry import tool_map
from executor import execute_tool


client = OpenAI(
    api_key="sk-d1f41205cf5e4c83b6aaa897d159c87c",
    base_url="https://api.deepseek.com"
)
messages=[
        
        {
            "role":"user",
            "content":"AI模型怎样连接外部工具？不要调用search"
    }
    ]
while True:
    response=client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )
    message=response.choices[0].message
    if message.tool_calls:
        messages.append(message)
        for tool_call in message.tool_calls:
            print("模型请求调用工具：", tool_call.function.name)
            print("参数：", tool_call.function.arguments)
            result = execute_tool(tool_call)
            print(result)
            messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
            })
        
    else:
        break

print(message.content)