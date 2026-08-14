def add(a,b):
    return a+b


def multiply(a,b):
    return a*b


def subtract(a,b):
    return a-b

def get_time():
    return "2026-08-12 18:20"
tools = [
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "计算两个数字的和",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number"
                    },
                    "b": {
                        "type": "number"
                    }
                },
                "required": [
                    "a",
                    "b"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "计算两个数字的积",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number"
                    },
                    "b": {
                        "type": "number"
                    }
                },
                "required": [
                    "a",
                    "b"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "subtract",
            "description": "计算两个数字的差",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number"
                    },
                    "b": {
                        "type": "number"
                    }
                },
                "required": [
                    "a",
                    "b"
                ]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "获取当前日期和时间",
        "parameters": {
            "type": "object",
            "properties": {},  # 没有参数
            "required": []      # 没有必需参数
        }
    }
}
]