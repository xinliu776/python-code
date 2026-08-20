from search import search

def add(a,b):
    return a+b


tools = [
    {
        "type":"function",
        "function":{
            "name":"search",
            "description":"搜索相关知识",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string"
                    }
                },
                "required":[
                    "query"
                ]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"retrieve",
            "description":"从知识库中访问相关知识",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string",
                        "description": "需要检索的问题或关键词"
                    }
                },
                "required":[
                    "query"
                ]
            }
        }
    },
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