from openai import OpenAI
from tool import tools,add
import json
client = OpenAI(
    api_key="sk-d1f41205cf5e4c83b6aaa897d159c87c",
    base_url="https://api.deepseek.com"
)
messages=[
        {
            "role":"user",
            "content":"计算123+234"
    }
    ]
response=client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools
)
messages.append(response.choices[0].message)
tool_call=response.choices[0].message.tool_calls[0]
print(tool_call.function.arguments)
arguments = json.loads(
    tool_call.function.arguments
)
print(arguments)
result=add(arguments["a"],arguments["b"])
print(result)
messages.append({
    "role":"tool",
    "tool_call_id":tool_call.id,
    "content":str(result)
})
response=client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools
)
print(response.choices[0].message.content)