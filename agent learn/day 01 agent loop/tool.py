def add(a,b):
    return a+b
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
    }
]