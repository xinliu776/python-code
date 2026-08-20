import requests

response = requests.get(
    "https://httpbin.org/get",
    params={
        "query": "AI Agent"
    }
)

print("状态码:", response.status_code)

data = response.json()

print("返回数据:", data)