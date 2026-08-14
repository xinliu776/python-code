from tool import add, multiply, subtract,tools
from openai import OpenAI
import json
from tool_registry import tool_map

def execute_tool(tool_call):
    arguments=json.loads(tool_call.function.arguments)
    function_name=tool_call.function.name
    function=tool_map.get(function_name)
    if function is None:
        print("工具不存在")
        result="工具不存在"
        
    else:
        try:
            result=function(**arguments)
        except Exception as e:
            result=f"工具执行失败:{e}"

    return result