from tool import add, multiply, subtract,tools
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
            "content":"计算123+234的和乘以223"
    }
    ]
while True:
    response=client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )
    messages.append(response.choices[0].message)
    message=response.choices[0].message
    if message.tool_calls:
        tool_call=message.tool_calls[0]
        result=execute_tool(tool_call)
        messages.append({
                "role":"tool",
                "tool_call_id":tool_call.id,
                "content":str(result)
            })
            
    else:
        break

print(message.content)